"""Data models for Apple Notes entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass
class Account:
    """Represents an Apple Notes account."""
    id: int
    name: str
    identifier: str
    user_record_name: str | None = None
    
    def __str__(self) -> str:
        return f"Account(id={self.id}, name='{self.name}')"


@dataclass
class Folder:
    """Represents an Apple Notes folder."""
    id: int
    name: str
    account: Account
    uuid: str | None = None
    parent_id: int | None = None
    
    def get_path(self, folders_dict: dict[int, Folder] | None = None) -> str:
        """Get the full path of this folder (e.g., 'Notes/Cocktails/Classic')."""
        if not folders_dict:
            return self.name
        
        path_parts = []
        current_folder = self
        visited = set()  # Prevent infinite loops
        
        while current_folder and current_folder.id not in visited:
            visited.add(current_folder.id)
            path_parts.append(current_folder.name)
            
            if current_folder.parent_id and current_folder.parent_id in folders_dict:
                current_folder = folders_dict[current_folder.parent_id]
            else:
                break
        
        # Reverse to get root-to-leaf order
        path_parts.reverse()
        return "/".join(path_parts)
    
    def get_parent(self, folders_dict: dict[int, Folder]) -> Folder | None:
        """Get the parent folder object."""
        if self.parent_id and self.parent_id in folders_dict:
            return folders_dict[self.parent_id]
        return None
    
    def is_root(self) -> bool:
        """Check if this is a root folder (no parent)."""
        return self.parent_id is None
    
    def __str__(self) -> str:
        return f"Folder(id={self.id}, name='{self.name}', account='{self.account.name}')"


@dataclass
class Note:
    """Represents an Apple Notes note."""
    id: int
    note_id: int
    title: str | None
    content: str | None
    creation_date: datetime | None
    modification_date: datetime | None
    account: Account
    folder: Folder
    is_pinned: bool = False
    is_password_protected: bool = False
    uuid: str | None = None
    applescript_id: str | None = None
    tags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Extract tags from content after initialization."""
        if self.content:
            self._extract_tags()
    
    def _extract_tags(self):
        """Extract hashtags from note content."""
        # Tags will be set by the parser using protobuf data
        # This method is kept for compatibility
        pass
    
    def has_tag(self, tag: str) -> bool:
        """Check if the note has a specific tag."""
        return tag.lower() in [t.lower() for t in self.tags]
    
    def has_mention(self, mention: str) -> bool:
        """Check if the note has a specific mention."""
        return mention.lower() in [m.lower() for m in self.mentions]
    
    def has_link(self, link: str) -> bool:
        """Check if the note contains a specific link."""
        return link in self.links
    
    def get_folder_path(self, folders_dict: dict[int, Folder] | None = None) -> str:
        """Get the full folder path for this note (e.g., 'Notes/Cocktails/Classic')."""
        if folders_dict:
            return self.folder.get_path(folders_dict)
        return self.folder.name
    
    def __str__(self) -> str:
        return f"Note(id={self.id}, title='{self.title}', folder='{self.folder.name}')"