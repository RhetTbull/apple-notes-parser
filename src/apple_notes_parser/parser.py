"""Main parser class for Apple Notes databases."""

from __future__ import annotations

from collections.abc import Callable

from .database import AppleNotesDatabase
from .exceptions import AppleNotesParserError, DatabaseError
from .models import Account, Attachment, Folder, Note


class AppleNotesParser:
    """Main parser for Apple Notes SQLite databases."""

    def __init__(self, database_path: str | None = None):
        """Initialize parser with path to Notes SQLite database.

        Args:
            database_path: Path to NoteStore.sqlite. If None, tries to find the default
                          macOS location in ~/Library/Group Containers/.

        Raises:
            AppleNotesParserError: If the database cannot be accessed or is invalid.
        """
        # Let AppleNotesDatabase handle the path resolution
        try:
            self.database = AppleNotesDatabase(database_path)
            self.database_path = self.database.database_path
        except DatabaseError as e:
            raise AppleNotesParserError(str(e))

        self._accounts: list[Account] | None = None
        self._folders: list[Folder] | None = None
        self._notes: list[Note] | None = None

    def load_data(self) -> None:
        """Load all data from the database.

        Loads accounts, folders, and notes from the database into memory.
        This method must be called before accessing the data properties.

        Raises:
            AppleNotesParserError: If data loading fails due to database issues.
        """
        with AppleNotesDatabase(str(self.database_path)) as db:
            # Load accounts
            accounts_list = db.get_accounts()
            accounts_dict = {account.id: account for account in accounts_list}

            # Load folders
            folders_list = db.get_folders(accounts_dict)
            folders_dict = {folder.id: folder for folder in folders_list}

            # Load notes
            notes_list = db.get_notes(accounts_dict, folders_dict)

            # Store the data
            self._accounts = accounts_list
            self._folders = folders_list
            self._notes = notes_list

    @property
    def accounts(self) -> list[Account]:
        """Get all accounts.

        Automatically loads data if not already loaded.

        Returns:
            list[Account]: List of all accounts in the database.
        """
        if self._accounts is None:
            self.load_data()
        return self._accounts or []

    @property
    def folders(self) -> list[Folder]:
        """Get all folders.

        Automatically loads data if not already loaded.

        Returns:
            list[Folder]: List of all folders in the database.
        """
        if self._folders is None:
            self.load_data()
        return self._folders or []

    @property
    def notes(self) -> list[Note]:
        """Get all notes.

        Automatically loads data if not already loaded.

        Returns:
            list[Note]: List of all notes in the database.
        """
        if self._notes is None:
            self.load_data()
        return self._notes or []

    @property
    def folders_dict(self) -> dict[int, Folder]:
        """Get folders as a dictionary for easy lookup by ID.

        Returns:
            dict[int, Folder]: Dictionary mapping folder IDs to Folder objects.
        """
        return {folder.id: folder for folder in self.folders}

    def get_notes_by_tag(self, tag: str) -> list[Note]:
        """Get all notes that have a specific tag.

        Args:
            tag: Tag to search for (case-insensitive).

        Returns:
            list[Note]: List of notes containing the specified tag.
        """
        return [note for note in self.notes if note.has_tag(tag)]

    def get_notes_by_tags(self, tags: list[str], match_all: bool = False) -> list[Note]:
        """Get notes that have specific tags.

        Args:
            tags: List of tags to search for (case-insensitive).
            match_all: If True, note must have ALL tags. If False, note must have ANY tag.
                      Defaults to False.

        Returns:
            list[Note]: List of notes matching the tag criteria.
        """
        if match_all:
            return [
                note for note in self.notes if all(note.has_tag(tag) for tag in tags)
            ]
        else:
            return [
                note for note in self.notes if any(note.has_tag(tag) for tag in tags)
            ]

    def get_notes_by_folder(self, folder_name: str) -> list[Note]:
        """Get all notes in a specific folder.

        Args:
            folder_name: Name of the folder to search in (case-insensitive).

        Returns:
            list[Note]: List of notes in the specified folder.
        """
        return [
            note
            for note in self.notes
            if note.folder.name.lower() == folder_name.lower()
        ]

    def get_notes_by_account(self, account_name: str) -> list[Note]:
        """Get all notes in a specific account.

        Args:
            account_name: Name of the account to search in (case-insensitive).
                         Common account names: 'iCloud', 'On My Mac'.

        Returns:
            list[Note]: List of notes in the specified account.
        """
        return [
            note
            for note in self.notes
            if note.account.name.lower() == account_name.lower()
        ]

    def get_notes_with_mentions(self) -> list[Note]:
        """Get all notes that contain mentions.

        Returns:
            list[Note]: List of notes containing one or more @mentions.
        """
        return [note for note in self.notes if note.mentions]

    def get_notes_by_mention(self, mention: str) -> list[Note]:
        """Get all notes that mention a specific user.

        Args:
            mention: Username to search for (case-insensitive, without @ symbol).

        Returns:
            list[Note]: List of notes containing the specified mention.
        """
        return [note for note in self.notes if note.has_mention(mention)]

    def get_notes_with_links(self) -> list[Note]:
        """Get all notes that contain links.

        Returns:
            list[Note]: List of notes containing one or more URLs.
        """
        return [note for note in self.notes if note.links]

    def get_notes_by_link_domain(self, domain: str) -> list[Note]:
        """Get all notes that contain links to a specific domain.

        Args:
            domain: Domain name to search for (case-insensitive).
                   Example: 'github.com', 'apple.com'.

        Returns:
            list[Note]: List of notes containing links to the specified domain.
        """
        return [
            note
            for note in self.notes
            if any(domain.lower() in link.lower() for link in note.links)
        ]

    def get_pinned_notes(self) -> list[Note]:
        """Get all pinned notes.

        Returns:
            list[Note]: List of notes that are marked as pinned.
        """
        return [note for note in self.notes if note.is_pinned]

    def get_protected_notes(self) -> list[Note]:
        """Get all password-protected notes.

        Returns:
            list[Note]: List of notes that are password-protected (encrypted).
                       Note: The content of these notes cannot be decrypted without the password.
        """
        return [note for note in self.notes if note.is_password_protected]

    def get_note_by_applescript_id(self, applescript_id: str) -> Note | None:
        """Get a note by its AppleScript ID.

        Args:
            applescript_id: The AppleScript ID to search for.
                          Format: x-coredata://UUID/ICNote/pID

        Returns:
            Note | None: The note with the specified AppleScript ID, or None if not found.
        """
        for note in self.notes:
            if note.applescript_id == applescript_id:
                return note
        return None

    def get_notes_with_attachments(self) -> list[Note]:
        """Get all notes that have attachments.

        Returns:
            list[Note]: List of notes containing one or more file attachments.
        """
        return [note for note in self.notes if note.has_attachments()]

    def get_notes_by_attachment_type(self, attachment_type: str) -> list[Note]:
        """Get notes that have attachments of a specific type.

        Args:
            attachment_type: Type of attachments to filter by. Must be one of:
                           'image', 'video', 'audio', or 'document'.

        Returns:
            list[Note]: List of notes containing attachments of the specified type.
        """
        return [
            note for note in self.notes if note.get_attachments_by_type(attachment_type)
        ]

    def get_all_attachments(self) -> list[Attachment]:
        """Get all attachments across all notes.

        Returns:
            list[Attachment]: List of all attachments from all notes in the database.
        """
        attachments = []
        for note in self.notes:
            attachments.extend(note.attachments)
        return attachments

    def search_notes(self, query: str, case_sensitive: bool = False) -> list[Note]:
        """Search for notes containing specific text.

        Searches both note titles and content for the specified query string.

        Args:
            query: Text to search for.
            case_sensitive: Whether to perform case-sensitive search. Defaults to False.

        Returns:
            list[Note]: List of notes containing the search query in title or content.
        """
        if not case_sensitive:
            query = query.lower()

        results = []
        for note in self.notes:
            content = note.content or ""
            title = note.title or ""

            if not case_sensitive:
                content = content.lower()
                title = title.lower()

            if query in content or query in title:
                results.append(note)

        return results

    def filter_notes(self, filter_func: Callable[[Note], bool]) -> list[Note]:
        """Filter notes using a custom function.

        Args:
            filter_func: Function that takes a Note object and returns True
                        if the note should be included in the results.

        Returns:
            list[Note]: List of notes for which filter_func returned True.
        """
        return [note for note in self.notes if filter_func(note)]

    def get_all_tags(self) -> list[str]:
        """Get all unique tags across all notes.

        Attempts to retrieve tags from the database embedded objects first
        (more accurate for iOS 15+), then falls back to note-based extraction.

        Returns:
            list[str]: Sorted list of all unique hashtags found in the database.
        """
        # Try to get tags from database first (more accurate for iOS 15+)
        try:
            with AppleNotesDatabase(str(self.database_path)) as db:
                if db._embedded_extractor:
                    db_tags = db._embedded_extractor.get_all_hashtags()
                    if db_tags:
                        return db_tags
        except:
            pass  # Fall back to note-based extraction

        # Fallback: extract from loaded notes
        all_tags = set()
        for note in self.notes:
            all_tags.update(note.tags)
        return sorted(all_tags)

    def get_all_mentions(self) -> list[str]:
        """Get all unique mentions across all notes.

        Returns:
            list[str]: Sorted list of all unique @mentions found in the database.
        """
        all_mentions = set()
        for note in self.notes:
            all_mentions.update(note.mentions)
        return sorted(all_mentions)

    def get_tag_counts(self) -> dict[str, int]:
        """Get count of notes for each tag.

        Attempts to retrieve counts from the database embedded objects first
        (more accurate for iOS 15+), then falls back to note-based counting.

        Returns:
            dict[str, int]: Dictionary mapping tag names to the number of notes
                          containing each tag, sorted by tag name.
        """
        # Try to get counts from database first (more accurate for iOS 15+)
        try:
            with AppleNotesDatabase(str(self.database_path)) as db:
                if db._embedded_extractor:
                    db_counts = db._embedded_extractor.get_hashtag_counts()
                    if db_counts:
                        return db_counts
        except:
            pass  # Fall back to note-based counting

        # Fallback: count from loaded notes
        tag_counts: dict[str, int] = {}
        for note in self.notes:
            for tag in note.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return dict(sorted(tag_counts.items()))

    def get_folder_counts(self) -> dict[str, int]:
        """Get count of notes for each folder.

        Returns:
            dict[str, int]: Dictionary mapping folder names to the number of notes
                          in each folder, sorted by folder name.
        """
        folder_counts: dict[str, int] = {}
        for note in self.notes:
            folder_name = note.folder.name
            folder_counts[folder_name] = folder_counts.get(folder_name, 0) + 1
        return dict(sorted(folder_counts.items()))

    def get_account_counts(self) -> dict[str, int]:
        """Get count of notes for each account.

        Returns:
            dict[str, int]: Dictionary mapping account names to the number of notes
                          in each account, sorted by account name.
        """
        account_counts: dict[str, int] = {}
        for note in self.notes:
            account_name = note.account.name
            account_counts[account_name] = account_counts.get(account_name, 0) + 1
        return dict(sorted(account_counts.items()))

    def export_notes_to_dict(self, include_content: bool = True) -> dict:
        """Export all notes to a dictionary structure.

        Creates a comprehensive dictionary containing all accounts, folders,
        and notes with their metadata. Suitable for JSON serialization.

        Args:
            include_content: Whether to include note content in the export.
                           Set to False for privacy or to reduce export size.
                           Defaults to True.

        Returns:
            dict: Dictionary with 'accounts', 'folders', and 'notes' keys,
                 each containing lists of dictionaries with object data.
                 All dates are converted to ISO format strings.
        """
        folders_dict = self.folders_dict

        return {
            "accounts": [
                {
                    "id": account.id,
                    "name": account.name,
                    "identifier": account.identifier,
                    "user_record_name": account.user_record_name,
                }
                for account in self.accounts
            ],
            "folders": [
                {
                    "id": folder.id,
                    "name": folder.name,
                    "account_name": folder.account.name,
                    "uuid": folder.uuid,
                    "parent_id": folder.parent_id,
                    "path": folder.get_path(folders_dict),
                }
                for folder in self.folders
            ],
            "notes": [
                {
                    "id": note.id,
                    "note_id": note.note_id,
                    "title": note.title,
                    "content": note.content if include_content else None,
                    "creation_date": (
                        note.creation_date.isoformat() if note.creation_date else None
                    ),
                    "modification_date": (
                        note.modification_date.isoformat()
                        if note.modification_date
                        else None
                    ),
                    "account_name": note.account.name,
                    "folder_name": note.folder.name,
                    "folder_path": note.get_folder_path(folders_dict),
                    "is_pinned": note.is_pinned,
                    "is_password_protected": note.is_password_protected,
                    "uuid": note.uuid,
                    "applescript_id": note.applescript_id,
                    "tags": note.tags,
                    "mentions": note.mentions,
                    "links": note.links,
                    "attachments": [
                        {
                            "id": attachment.id,
                            "filename": attachment.filename,
                            "file_size": attachment.file_size,
                            "type_uti": attachment.type_uti,
                            "file_extension": attachment.file_extension,
                            "mime_type": attachment.mime_type,
                            "is_image": attachment.is_image,
                            "is_video": attachment.is_video,
                            "is_audio": attachment.is_audio,
                            "is_document": attachment.is_document,
                            "creation_date": (
                                attachment.creation_date.isoformat()
                                if attachment.creation_date
                                else None
                            ),
                            "modification_date": (
                                attachment.modification_date.isoformat()
                                if attachment.modification_date
                                else None
                            ),
                            "uuid": attachment.uuid,
                            "is_remote": attachment.is_remote,
                            "remote_url": attachment.remote_url,
                        }
                        for attachment in note.attachments
                    ],
                }
                for note in self.notes
            ],
        }
