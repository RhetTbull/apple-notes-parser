"""Data models for Apple Notes entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import re


@dataclass
class Account:
    """Represents an Apple Notes account."""
    id: int
    name: str
    identifier: str
    user_record_name: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Account(id={self.id}, name='{self.name}')"


@dataclass
class Folder:
    """Represents an Apple Notes folder."""
    id: int
    name: str
    account: Account
    uuid: Optional[str] = None
    parent_id: Optional[int] = None
    
    def __str__(self) -> str:
        return f"Folder(id={self.id}, name='{self.name}', account='{self.account.name}')"


@dataclass
class Note:
    """Represents an Apple Notes note."""
    id: int
    note_id: int
    title: Optional[str]
    content: Optional[str]
    creation_date: Optional[datetime]
    modification_date: Optional[datetime]
    account: Account
    folder: Folder
    is_pinned: bool = False
    is_password_protected: bool = False
    uuid: Optional[str] = None
    applescript_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    
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
    
    def __str__(self) -> str:
        return f"Note(id={self.id}, title='{self.title}', folder='{self.folder.name}')"