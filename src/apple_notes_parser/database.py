"""SQLite database operations for Apple Notes."""

from __future__ import annotations

import gzip
import sqlite3
from datetime import datetime
from pathlib import Path

from .embedded_objects import EmbeddedObjectExtractor
from .exceptions import DatabaseError
from .models import Account, Attachment, Folder, Note
from .protobuf_parser import ProtobufParser


class AppleNotesDatabase:
    """Handles SQLite database operations for Apple Notes."""

    def __init__(self, database_path: str | None = None):
        """Initialize with path to Notes SQLite database.

        Args:
            database_path: Path to NoteStore.sqlite. If None, tries to find the default
                          macOS location in ~/Library/Group Containers/.

        Raises:
            DatabaseError: If the database file is not found.
        """
        if database_path is None:
            database_path = self._find_default_database_path()

        self.database_path = Path(database_path)
        if not self.database_path.exists():
            raise DatabaseError(f"Database file not found: {database_path}")

        self.connection: sqlite3.Connection | None = None
        self._ios_version: int | None = None
        self._embedded_extractor: EmbeddedObjectExtractor | None = None

    def _find_default_database_path(self) -> str:
        """Find the default Apple Notes database path on macOS.

        Searches common macOS Notes database locations in order of preference.

        Returns:
            str: Path to the found database file.

        Raises:
            DatabaseError: If no database file is found in any of the searched locations.
        """
        home = Path.home()

        # Common macOS Notes database locations
        possible_paths = [
            # Modern macOS (10.15+)
            home
            / "Library"
            / "Group Containers"
            / "group.com.apple.notes"
            / "NoteStore.sqlite",
            # Alternative location
            home
            / "Library"
            / "Containers"
            / "com.apple.Notes"
            / "Data"
            / "Library"
            / "Notes"
            / "NotesV7.storedata",
            # Older locations (for completeness)
            home
            / "Library"
            / "Containers"
            / "com.apple.Notes"
            / "Data"
            / "Library"
            / "CoreData"
            / "ExternalRecords"
            / "NoteStore.sqlite",
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        # If no default found, raise an error with helpful message
        raise DatabaseError(
            "Could not find Apple Notes database. Please provide the path explicitly. "
            f"Searched locations: {[str(p) for p in possible_paths]}"
        )

    def __enter__(self) -> AppleNotesDatabase:
        """Context manager entry.

        Returns:
            AppleNotesDatabase: Self instance for use in with statement.
        """
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        self.close()

    def connect(self) -> None:
        """Connect to the SQLite database.

        Establishes connection and initializes embedded object extractor.

        Raises:
            DatabaseError: If connection to the database fails.
        """
        try:
            self.connection = sqlite3.connect(str(self.database_path))
            self.connection.row_factory = sqlite3.Row

            # Initialize embedded object extractor once we have connection and version
            ios_version = self.get_ios_version()
            self._embedded_extractor = EmbeddedObjectExtractor(
                self.connection, ios_version
            )
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")

    def close(self) -> None:
        """Close database connection.

        Safely closes the SQLite connection if it exists.
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    def _ensure_connected(self) -> None:
        """Ensure database connection exists.

        Creates a new connection if one doesn't already exist.
        """
        if not self.connection:
            self.connect()

    def get_z_uuid(self) -> str | None:
        """Get the Z_UUID from Z_METADATA table for constructing AppleScript IDs.

        Returns:
            str | None: The Z_UUID string if found, None if the table doesn't exist
                       or no UUID is found.
        """
        self._ensure_connected()
        assert self.connection is not None
        cursor = self.connection.cursor()

        try:
            cursor.execute("SELECT Z_UUID FROM Z_METADATA LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error:
            # Z_METADATA table may not exist in older versions
            return None

    def get_ios_version(self) -> int:
        """Detect iOS version based on database schema.

        Analyzes the database schema to determine which iOS/macOS version
        created the database by checking for version-specific columns.

        Returns:
            int: Detected iOS/macOS version number (e.g., 15, 16, 17, 18).

        Raises:
            DatabaseError: If version detection fails due to database access issues.
        """
        if self._ios_version is not None:
            return self._ios_version

        self._ensure_connected()
        assert self.connection is not None
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
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='Z_11NOTES'"
                )
                if cursor.fetchone():
                    self._ios_version = 11
                else:
                    self._ios_version = 10  # Default fallback

            return self._ios_version

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to detect iOS version: {e}")

    def get_accounts(self) -> list[Account]:
        """Get all accounts from the database.

        Retrieves all Apple Notes accounts (e.g., iCloud, On My Mac) from the database.
        The query structure varies based on the detected iOS version.

        Returns:
            list[Account]: List of Account objects representing all accounts in the database.

        Raises:
            DatabaseError: If account retrieval fails due to database access issues.
        """
        self._ensure_connected()
        assert self.connection is not None
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
                    user_record_name=row[3] if len(row) > 3 else None,
                )
                accounts.append(account)

            return accounts

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get accounts: {e}")

    def get_folders(self, accounts: dict[int, Account]) -> list[Folder]:
        """Get all folders from the database.

        Retrieves all Apple Notes folders and constructs their hierarchy relationships.
        Only folders belonging to the provided accounts are included.

        Args:
            accounts: Dictionary mapping account IDs to Account objects.
                     Only folders belonging to these accounts will be returned.

        Returns:
            list[Folder]: List of Folder objects representing all folders in the database.

        Raises:
            DatabaseError: If folder retrieval fails due to database access issues.
        """
        self._ensure_connected()
        assert self.connection is not None
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
                        parent_id=row[4] if len(row) > 4 and row[4] else None,
                    )
                    folders.append(folder)

            return folders

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get folders: {e}")

    def get_attachments(self, accounts: dict[int, Account]) -> list[Attachment]:
        """Get all attachments from the database.

        Retrieves all file attachments associated with notes in the database.
        Attachments are stored as ZICCLOUDSYNCINGOBJECT records with ZNOTE
        pointing to the parent note.

        Args:
            accounts: Dictionary mapping account IDs to Account objects.
                     Used for consistency with other methods (attachments are note-scoped).

        Returns:
            list[Attachment]: List of Attachment objects representing all attachments.

        Raises:
            DatabaseError: If attachment retrieval fails due to database access issues.
        """
        self._ensure_connected()
        assert self.connection is not None
        cursor = self.connection.cursor()

        try:
            self.get_ios_version()
            self.get_z_uuid()

            # Query for attachment records
            # Attachments are stored as ZICCLOUDSYNCINGOBJECT records with ZNOTE pointing to the parent note
            query = """
            SELECT
                obj.Z_PK,
                COALESCE(obj.ZFILENAME, obj.ZTITLE) as filename,
                obj.ZFILESIZE,
                obj.ZTYPEUTI,
                obj.ZNOTE,
                obj.ZCREATIONDATE,
                obj.ZMODIFICATIONDATE,
                obj.ZIDENTIFIER,
                obj.ZREMOTEFILEURLSTRING
            FROM ZICCLOUDSYNCINGOBJECT obj
            WHERE obj.ZNOTE IS NOT NULL
                AND (obj.ZFILENAME IS NOT NULL OR obj.ZTITLE IS NOT NULL OR obj.ZFILESIZE > 0 OR obj.ZTYPEUTI IS NOT NULL)
                AND obj.ZTITLE1 IS NULL
                AND (obj.ZTYPEUTI IS NOT NULL AND obj.ZTYPEUTI != '')
            """

            cursor.execute(query)
            attachments = []

            for row in cursor.fetchall():
                # Convert Core Data timestamps to datetime
                creation_date = self._convert_core_time(row[5]) if row[5] else None
                modification_date = self._convert_core_time(row[6]) if row[6] else None

                attachment = Attachment(
                    id=row[0],
                    filename=row[1],
                    file_size=row[2] if row[2] and row[2] > 0 else None,
                    type_uti=row[3],
                    note_id=row[4],
                    creation_date=creation_date,
                    modification_date=modification_date,
                    uuid=row[7],
                    is_remote=row[8] is not None,
                    remote_url=row[8],
                )
                attachments.append(attachment)

            return attachments

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get attachments: {e}")

    def get_notes(
        self, accounts: dict[int, Account], folders: dict[int, Folder]
    ) -> list[Note]:
        """Get all notes from the database.

        Retrieves all Apple Notes from the database, including their content,
        metadata, embedded objects (hashtags, mentions, links), and attachments.
        Only notes belonging to the provided accounts and folders are included.

        Args:
            accounts: Dictionary mapping account IDs to Account objects.
                     Only notes belonging to these accounts will be returned.
            folders: Dictionary mapping folder IDs to Folder objects.
                    Only notes in these folders will be returned.

        Returns:
            list[Note]: List of Note objects representing all notes in the database.

        Raises:
            DatabaseError: If note retrieval fails due to database access issues.
        """
        self._ensure_connected()
        assert self.connection is not None
        cursor = self.connection.cursor()

        try:
            ios_version = self.get_ios_version()
            z_uuid = self.get_z_uuid()  # Get Z_UUID for AppleScript ID construction

            # Get all attachments first and organize by note_id
            attachments_list = self.get_attachments(accounts)
            attachments_by_note: dict[int, list[Attachment]] = {}
            for attachment in attachments_list:
                if attachment.note_id not in attachments_by_note:
                    attachments_by_note[attachment.note_id] = []
                attachments_by_note[attachment.note_id].append(attachment)

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
                    embedded_objects = (
                        self._embedded_extractor.get_embedded_objects_for_note(row[1])
                        if self._embedded_extractor
                        else {}
                    )

                    # Combine hashtags from both protobuf content and embedded objects
                    # Embedded objects are more reliable for iOS 15+
                    hashtags = embedded_objects.get("hashtags", [])
                    if not hashtags:
                        # Fallback to regex extraction for older versions or when embedded objects aren't found
                        hashtags = structure.get("hashtags", [])

                    mentions = embedded_objects.get("mentions", [])
                    if not mentions:
                        mentions = structure.get("mentions", [])

                    links = embedded_objects.get("links", [])
                    if not links:
                        links = structure.get("links", [])

                    # Convert Core Data timestamps to datetime
                    creation_date = self._convert_core_time(row[4]) if row[4] else None
                    modification_date = (
                        self._convert_core_time(row[5]) if row[5] else None
                    )

                    # Construct AppleScript ID: x-coredata://{Z_UUID}/ICNote/p{Z_PK}
                    applescript_id = None
                    if z_uuid:
                        applescript_id = f"x-coredata://{z_uuid}/ICNote/p{row[1]}"

                    # Get attachments for this note
                    note_attachments = attachments_by_note.get(row[1], [])

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
                        is_password_protected=(
                            bool(row[10]) if row[10] is not None else False
                        ),
                        tags=hashtags,
                        mentions=mentions,
                        links=links,
                        attachments=note_attachments,
                    )
                    notes.append(note)

            return notes

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get notes: {e}")

    def _get_legacy_notes(
        self, accounts: dict[int, Account], folders: dict[int, Folder]
    ) -> list[Note]:
        """Get notes from legacy (pre-iOS 9) database format.

        Handles the older database schema used in iOS 8 and earlier versions
        where notes were stored in ZNOTE/ZNOTEBODY tables instead of the
        modern ZICCLOUDSYNCINGOBJECT structure.

        Args:
            accounts: Dictionary mapping account IDs to Account objects.
            folders: Dictionary mapping folder IDs to Folder objects.

        Returns:
            list[Note]: List of Note objects from the legacy database format.
        """
        self._ensure_connected()
        assert self.connection is not None
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
                    is_password_protected=False,
                )
                notes.append(note)

        return notes

    def _extract_note_content(self, zdata: bytes) -> str | None:
        """Extract plain text content from compressed note data.

        Legacy method for extracting note content. Modern note parsing
        is handled by the ProtobufParser class.

        Args:
            zdata: Raw bytes from the ZDATA column in the database.

        Returns:
            str | None: Extracted text content or None if extraction fails.
        """
        if not zdata:
            return None

        try:
            # Check if data is gzipped
            if len(zdata) > 2 and zdata[0:2] == b"\x1f\x8b":
                # Decompress gzipped data
                decompressed = gzip.decompress(zdata)
                # For now, return a placeholder - we'll implement protobuf parsing later
                return f"[Compressed note data - {len(decompressed)} bytes]"
            else:
                # Try to decode as plain text
                try:
                    return zdata.decode("utf-8", errors="ignore")
                except:
                    return f"[Binary note data - {len(zdata)} bytes]"
        except Exception:
            return None

    def _convert_core_time(self, core_time: float) -> datetime | None:
        """Convert Core Data timestamp to Python datetime.

        Core Data timestamps are seconds since January 1, 2001 00:00:00 UTC.
        Unix timestamps are seconds since January 1, 1970 00:00:00 UTC.
        The difference is 978307200 seconds (31 years).

        Args:
            core_time: Core Data timestamp as a float.

        Returns:
            datetime | None: Converted datetime object in local timezone, or None if invalid.
        """
        try:
            # Core Data timestamps are seconds since January 1, 2001 00:00:00 UTC
            # Unix timestamps are seconds since January 1, 1970 00:00:00 UTC
            # The difference is 978307200 seconds (31 years)

            # Skip invalid timestamps (0, negative, or extremely large values)
            if core_time <= 0 or core_time > 2147483647:  # Max 32-bit timestamp
                return None

            unix_timestamp = core_time + 978307200

            # Additional validation for reasonable date range (1970-2100)
            if unix_timestamp < 0 or unix_timestamp > 4102444800:  # Year 2100
                return None

            return datetime.fromtimestamp(unix_timestamp)
        except (ValueError, OSError, OverflowError):
            # Handle invalid timestamps gracefully
            return None
