"""Main parser class for Apple Notes databases."""

from typing import List, Dict, Optional, Callable
from pathlib import Path

from .database import AppleNotesDatabase
from .models import Account, Folder, Note
from .exceptions import AppleNotesParserError


class AppleNotesParser:
    """Main parser for Apple Notes SQLite databases."""
    
    def __init__(self, database_path: str):
        """Initialize parser with path to Notes SQLite database."""
        self.database_path = Path(database_path)
        if not self.database_path.exists():
            raise AppleNotesParserError(f"Database file not found: {database_path}")
        
        self._accounts: Optional[List[Account]] = None
        self._folders: Optional[List[Folder]] = None
        self._notes: Optional[List[Note]] = None
    
    def load_data(self) -> None:
        """Load all data from the database."""
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
    def accounts(self) -> List[Account]:
        """Get all accounts."""
        if self._accounts is None:
            self.load_data()
        return self._accounts or []
    
    @property
    def folders(self) -> List[Folder]:
        """Get all folders."""
        if self._folders is None:
            self.load_data()
        return self._folders or []
    
    @property
    def notes(self) -> List[Note]:
        """Get all notes."""
        if self._notes is None:
            self.load_data()
        return self._notes or []
    
    @property
    def folders_dict(self) -> Dict[int, Folder]:
        """Get folders as a dictionary for easy lookup by ID."""
        return {folder.id: folder for folder in self.folders}
    
    def get_notes_by_tag(self, tag: str) -> List[Note]:
        """Get all notes that have a specific tag."""
        return [note for note in self.notes if note.has_tag(tag)]
    
    def get_notes_by_tags(self, tags: List[str], match_all: bool = False) -> List[Note]:
        """
        Get notes that have specific tags.
        
        Args:
            tags: List of tags to search for
            match_all: If True, note must have ALL tags. If False, note must have ANY tag.
        """
        if match_all:
            return [
                note for note in self.notes 
                if all(note.has_tag(tag) for tag in tags)
            ]
        else:
            return [
                note for note in self.notes 
                if any(note.has_tag(tag) for tag in tags)
            ]
    
    def get_notes_by_folder(self, folder_name: str) -> List[Note]:
        """Get all notes in a specific folder."""
        return [note for note in self.notes if note.folder.name.lower() == folder_name.lower()]
    
    def get_notes_by_account(self, account_name: str) -> List[Note]:
        """Get all notes in a specific account."""
        return [note for note in self.notes if note.account.name.lower() == account_name.lower()]
    
    def get_notes_with_mentions(self) -> List[Note]:
        """Get all notes that contain mentions."""
        return [note for note in self.notes if note.mentions]
    
    def get_notes_by_mention(self, mention: str) -> List[Note]:
        """Get all notes that mention a specific user."""
        return [note for note in self.notes if note.has_mention(mention)]
    
    def get_notes_with_links(self) -> List[Note]:
        """Get all notes that contain links."""
        return [note for note in self.notes if note.links]
    
    def get_notes_by_link_domain(self, domain: str) -> List[Note]:
        """Get all notes that contain links to a specific domain."""
        return [
            note for note in self.notes 
            if any(domain.lower() in link.lower() for link in note.links)
        ]
    
    def get_pinned_notes(self) -> List[Note]:
        """Get all pinned notes."""
        return [note for note in self.notes if note.is_pinned]
    
    def get_protected_notes(self) -> List[Note]:
        """Get all password-protected notes."""
        return [note for note in self.notes if note.is_password_protected]
    
    def search_notes(self, query: str, case_sensitive: bool = False) -> List[Note]:
        """Search for notes containing specific text."""
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
    
    def filter_notes(self, filter_func: Callable[[Note], bool]) -> List[Note]:
        """Filter notes using a custom function."""
        return [note for note in self.notes if filter_func(note)]
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags across all notes."""
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
        return sorted(list(all_tags))
    
    def get_all_mentions(self) -> List[str]:
        """Get all unique mentions across all notes."""
        all_mentions = set()
        for note in self.notes:
            all_mentions.update(note.mentions)
        return sorted(list(all_mentions))
    
    def get_tag_counts(self) -> Dict[str, int]:
        """Get count of notes for each tag."""
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
        tag_counts = {}
        for note in self.notes:
            for tag in note.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return dict(sorted(tag_counts.items()))
    
    def get_folder_counts(self) -> Dict[str, int]:
        """Get count of notes for each folder."""
        folder_counts = {}
        for note in self.notes:
            folder_name = note.folder.name
            folder_counts[folder_name] = folder_counts.get(folder_name, 0) + 1
        return dict(sorted(folder_counts.items()))
    
    def get_account_counts(self) -> Dict[str, int]:
        """Get count of notes for each account."""
        account_counts = {}
        for note in self.notes:
            account_name = note.account.name
            account_counts[account_name] = account_counts.get(account_name, 0) + 1
        return dict(sorted(account_counts.items()))
    
    def export_notes_to_dict(self, include_content: bool = True) -> Dict:
        """Export all notes to a dictionary structure."""
        folders_dict = self.folders_dict
        
        return {
            'accounts': [
                {
                    'id': account.id,
                    'name': account.name,
                    'identifier': account.identifier,
                    'user_record_name': account.user_record_name
                }
                for account in self.accounts
            ],
            'folders': [
                {
                    'id': folder.id,
                    'name': folder.name,
                    'account_name': folder.account.name,
                    'uuid': folder.uuid,
                    'parent_id': folder.parent_id,
                    'path': folder.get_path(folders_dict)
                }
                for folder in self.folders
            ],
            'notes': [
                {
                    'id': note.id,
                    'note_id': note.note_id,
                    'title': note.title,
                    'content': note.content if include_content else None,
                    'creation_date': note.creation_date.isoformat() if note.creation_date else None,
                    'modification_date': note.modification_date.isoformat() if note.modification_date else None,
                    'account_name': note.account.name,
                    'folder_name': note.folder.name,
                    'folder_path': note.get_folder_path(folders_dict),
                    'is_pinned': note.is_pinned,
                    'is_password_protected': note.is_password_protected,
                    'uuid': note.uuid,
                    'applescript_id': note.applescript_id,
                    'tags': note.tags,
                    'mentions': note.mentions,
                    'links': note.links
                }
                for note in self.notes
            ]
        }