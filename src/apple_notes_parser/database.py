"""SQLite database operations for Apple Notes."""

import sqlite3
import gzip
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .exceptions import DatabaseError
from .models import Account, Folder, Note
from .protobuf_parser import ProtobufParser
from .embedded_objects import EmbeddedObjectExtractor


class AppleNotesDatabase:
    """Handles SQLite database operations for Apple Notes."""

    def __init__(self, database_path: Optional[str] = None):
        """Initialize with path to Notes SQLite database.
        
        Args:
            database_path: Path to NoteStore.sqlite. If None, tries to find the default
                          macOS location in ~/Library/Group Containers/
        """
        if database_path is None:
            database_path = self._find_default_database_path()
        
        self.database_path = Path(database_path)
        if not self.database_path.exists():
            raise DatabaseError(f"Database file not found: {database_path}")

        self.connection: Optional[sqlite3.Connection] = None
        self._ios_version: Optional[int] = None
        self._embedded_extractor: Optional[EmbeddedObjectExtractor] = None
    
    def _find_default_database_path(self) -> str:
        """Find the default Apple Notes database path on macOS."""
        home = Path.home()
        
        # Common macOS Notes database locations
        possible_paths = [
            # Modern macOS (10.15+)
            home / "Library" / "Group Containers" / "group.com.apple.notes" / "NoteStore.sqlite",
            # Alternative location
            home / "Library" / "Containers" / "com.apple.Notes" / "Data" / "Library" / "Notes" / "NotesV7.storedata",
            # Older locations (for completeness)
            home / "Library" / "Containers" / "com.apple.Notes" / "Data" / "Library" / "CoreData" / "ExternalRecords" / "NoteStore.sqlite",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # If no default found, raise an error with helpful message
        raise DatabaseError(
            "Could not find Apple Notes database. Please provide the path explicitly. "
            f"Searched locations: {[str(p) for p in possible_paths]}"
        )

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.connection = sqlite3.connect(str(self.database_path))
            self.connection.row_factory = sqlite3.Row

            # Initialize embedded object extractor once we have connection and version
            ios_version = self.get_ios_version()
            self._embedded_extractor = EmbeddedObjectExtractor(self.connection, ios_version)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def _ensure_connected(self):
        """Ensure database connection exists."""
        if not self.connection:
            self.connect()

    def get_z_uuid(self) -> Optional[str]:
        """Get the Z_UUID from Z_METADATA table for constructing AppleScript IDs."""
        self._ensure_connected()
        cursor = self.connection.cursor()

        try:
            cursor.execute("SELECT Z_UUID FROM Z_METADATA LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error:
            # Z_METADATA table may not exist in older versions
            return None

    def get_ios_version(self) -> int:
        """Detect iOS version based on database schema."""
        if self._ios_version is not None:
            return self._ios_version

        self._ensure_connected()
        cursor = self.connection.cursor()

        try:
            # Check for columns that appeared in different iOS versions
            cursor.execute("PRAGMA table_info(ZICCLOUDSYNCINGOBJECT)")
            columns = [row[1] for row in cursor.fetchall()]

            if "ZUNAPPLIEDENCRYPTEDRECORDDATA" in columns:
                self._ios_version = 18
            elif "ZGENERATION" in columns:
                self._ios_version = 17
            elif "ZACCOUNT6" in columns:
                self._ios_version = 16
            elif "ZACCOUNT5" in columns:
                self._ios_version = 15
            elif "ZLASTOPENEDDATE" in columns:
                self._ios_version = 14
            elif "ZACCOUNT4" in columns:
                self._ios_version = 13
            elif "ZSERVERRECORDDATA" in columns:
                self._ios_version = 12
            else:
                # Check for iOS 11 specific table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Z_11NOTES'")
                if cursor.fetchone():
                    self._ios_version = 11
                else:
                    self._ios_version = 10  # Default fallback

            return self._ios_version

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to detect iOS version: {e}")

    def get_accounts(self) -> List[Account]:
        """Get all accounts from the database."""
        self._ensure_connected()
        cursor = self.connection.cursor()

        try:
            # Query varies by iOS version
            ios_version = self.get_ios_version()

            if ios_version >= 9:
                query = """
                SELECT Z_PK, ZNAME, ZIDENTIFIER, ZUSERRECORDNAME
                FROM ZICCLOUDSYNCINGOBJECT
                WHERE ZNAME IS NOT NULL
                """
            else:
                query = """
                SELECT Z_PK, ZNAME, ZACCOUNTIDENTIFIER as ZIDENTIFIER, NULL as ZUSERRECORDNAME
                FROM ZACCOUNT
                """

            cursor.execute(query)
            accounts = []

            for row in cursor.fetchall():
                account = Account(
                    id=row[0],
                    name=row[1] or "Unknown",
                    identifier=row[2] or "",
                    user_record_name=row[3] if len(row) > 3 else None
                )
                accounts.append(account)

            return accounts

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get accounts: {e}")

    def get_folders(self, accounts: Dict[int, Account]) -> List[Folder]:
        """Get all folders from the database."""
        self._ensure_connected()
        cursor = self.connection.cursor()

        try:
            ios_version = self.get_ios_version()

            if ios_version >= 9:
                query = """
                SELECT Z_PK, ZTITLE2, ZOWNER, ZIDENTIFIER, ZPARENT
                FROM ZICCLOUDSYNCINGOBJECT
                WHERE ZTITLE2 IS NOT NULL
                """
            else:
                query = """
                SELECT Z_PK, ZNAME as ZTITLE2, ZACCOUNT as ZOWNER, '' as ZIDENTIFIER, NULL as ZPARENT
                FROM ZSTORE
                """

            cursor.execute(query)
            folders = []

            for row in cursor.fetchall():
                account_id = row[2]
                if account_id in accounts:
                    folder = Folder(
                        id=row[0],
                        name=row[1] or "Untitled Folder",
                        account=accounts[account_id],
                        uuid=row[3] if row[3] else None,
                        parent_id=row[4] if len(row) > 4 and row[4] else None
                    )
                    folders.append(folder)

            return folders

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get folders: {e}")

    def get_notes(self, accounts: Dict[int, Account], folders: Dict[int, Folder]) -> List[Note]:
        """Get all notes from the database."""
        self._ensure_connected()
        cursor = self.connection.cursor()

        try:
            ios_version = self.get_ios_version()
            z_uuid = self.get_z_uuid()  # Get Z_UUID for AppleScript ID construction

            # Build query based on iOS version
            if ios_version >= 16:
                account_field = "ZACCOUNT7"
                creation_field = "ZCREATIONDATE3"
            elif ios_version == 15:
                account_field = "ZACCOUNT4"
                creation_field = "ZCREATIONDATE3"
            elif ios_version >= 13:
                account_field = "ZACCOUNT3"
                creation_field = "ZCREATIONDATE1"
            elif ios_version == 12:
                account_field = "ZACCOUNT2"
                creation_field = "ZCREATIONDATE1"
            elif ios_version == 11:
                account_field = "ZACCOUNT2"
                creation_field = "ZCREATIONDATE1"
            else:
                # Legacy version
                return self._get_legacy_notes(accounts, folders)

            query = f"""
            SELECT
                nd.Z_PK,
                nd.ZNOTE,
                obj.ZTITLE1,
                nd.ZDATA,
                obj.{creation_field},
                obj.ZMODIFICATIONDATE1,
                obj.{account_field},
                obj.ZFOLDER,
                obj.ZISPINNED,
                obj.ZIDENTIFIER,
                obj.ZISPASSWORDPROTECTED
            FROM ZICNOTEDATA nd
            JOIN ZICCLOUDSYNCINGOBJECT obj ON nd.ZNOTE = obj.Z_PK
            WHERE nd.ZDATA IS NOT NULL
            """

            cursor.execute(query)
            notes = []

            for row in cursor.fetchall():
                account_id = row[6]
                folder_id = row[7]

                if account_id in accounts and folder_id in folders:
                    # Decompress and parse content using protobuf parser
                    content = ProtobufParser.extract_note_text(row[3])
                    structure = ProtobufParser.parse_note_structure(row[3])

                    # Extract embedded objects (hashtags, mentions, links) from database
                    embedded_objects = self._embedded_extractor.get_embedded_objects_for_note(row[1])

                    # Combine hashtags from both protobuf content and embedded objects
                    # Embedded objects are more reliable for iOS 15+
                    hashtags = embedded_objects.get('hashtags', [])
                    if not hashtags:
                        # Fallback to regex extraction for older versions or when embedded objects aren't found
                        hashtags = structure.get('hashtags', [])

                    mentions = embedded_objects.get('mentions', [])
                    if not mentions:
                        mentions = structure.get('mentions', [])

                    links = embedded_objects.get('links', [])
                    if not links:
                        links = structure.get('links', [])

                    # Convert Core Data timestamps to datetime
                    creation_date = self._convert_core_time(row[4]) if row[4] else None
                    modification_date = self._convert_core_time(row[5]) if row[5] else None

                    # Construct AppleScript ID: x-coredata://{Z_UUID}/ICNote/p{Z_PK}
                    applescript_id = None
                    if z_uuid:
                        applescript_id = f"x-coredata://{z_uuid}/ICNote/p{row[1]}"

                    note = Note(
                        id=row[0],
                        note_id=row[1],
                        title=row[2],
                        content=content,
                        creation_date=creation_date,
                        modification_date=modification_date,
                        account=accounts[account_id],
                        folder=folders[folder_id],
                        is_pinned=bool(row[8]) if row[8] is not None else False,
                        uuid=row[9],
                        applescript_id=applescript_id,
                        is_password_protected=bool(row[10]) if row[10] is not None else False,
                        tags=hashtags,
                        mentions=mentions,
                        links=links
                    )
                    notes.append(note)

            return notes

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get notes: {e}")

    def _get_legacy_notes(self, accounts: Dict[int, Account], folders: Dict[int, Folder]) -> List[Note]:
        """Get notes from legacy (pre-iOS 9) database format."""
        cursor = self.connection.cursor()
        z_uuid = self.get_z_uuid()  # Get Z_UUID for AppleScript ID construction

        query = """
        SELECT
            n.Z_PK,
            n.Z_PK as ZNOTE,
            n.ZTITLE,
            nb.ZCONTENT,
            n.ZCREATIONDATE,
            n.ZMODIFICATIONDATE,
            s.ZACCOUNT,
            s.Z_PK as ZFOLDER,
            0 as ZISPINNED,
            '' as ZIDENTIFIER,
            0 as ZISPASSWORDPROTECTED
        FROM ZNOTE n
        JOIN ZNOTEBODY nb ON n.ZBODY = nb.Z_PK
        JOIN ZSTORE s ON n.ZSTORE = s.Z_PK
        """

        cursor.execute(query)
        notes = []

        for row in cursor.fetchall():
            account_id = row[6]
            folder_id = row[7]

            if account_id in accounts and folder_id in folders:
                creation_date = self._convert_core_time(row[4]) if row[4] else None
                modification_date = self._convert_core_time(row[5]) if row[5] else None

                # Construct AppleScript ID for legacy notes
                applescript_id = None
                if z_uuid:
                    applescript_id = f"x-coredata://{z_uuid}/ICNote/p{row[1]}"

                note = Note(
                    id=row[0],
                    note_id=row[1],
                    title=row[2],
                    content=row[3],  # Legacy notes store plain text
                    creation_date=creation_date,
                    modification_date=modification_date,
                    account=accounts[account_id],
                    folder=folders[folder_id],
                    is_pinned=False,
                    uuid=row[9] if row[9] else None,
                    applescript_id=applescript_id,
                    is_password_protected=False
                )
                notes.append(note)

        return notes

    def _extract_note_content(self, zdata: bytes) -> Optional[str]:
        """Extract plain text content from compressed note data."""
        if not zdata:
            return None

        try:
            # Check if data is gzipped
            if len(zdata) > 2 and zdata[0:2] == b'\x1f\x8b':
                # Decompress gzipped data
                decompressed = gzip.decompress(zdata)
                # For now, return a placeholder - we'll implement protobuf parsing later
                return f"[Compressed note data - {len(decompressed)} bytes]"
            else:
                # Try to decode as plain text
                try:
                    return zdata.decode('utf-8', errors='ignore')
                except:
                    return f"[Binary note data - {len(zdata)} bytes]"
        except Exception:
            return None

    def _convert_core_time(self, core_time: float) -> datetime:
        """Convert Core Data timestamp to Python datetime."""
        # Core Data timestamps are seconds since January 1, 2001 00:00:00 UTC
        # Unix timestamps are seconds since January 1, 1970 00:00:00 UTC
        # The difference is 978307200 seconds (31 years)
        unix_timestamp = core_time + 978307200
        return datetime.fromtimestamp(unix_timestamp)
