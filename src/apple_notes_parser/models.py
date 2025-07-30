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
class Attachment:
    """Represents an Apple Notes attachment."""
    id: int
    filename: str | None
    file_size: int | None
    type_uti: str | None  # Uniform Type Identifier (e.g., com.adobe.pdf)
    note_id: int
    creation_date: datetime | None = None
    modification_date: datetime | None = None
    uuid: str | None = None
    is_remote: bool = False
    remote_url: str | None = None
    
    @property
    def file_extension(self) -> str | None:
        """Get file extension from filename."""
        if self.filename and '.' in self.filename:
            return self.filename.split('.')[-1].lower()
        return None
    
    @property
    def mime_type(self) -> str | None:
        """Get MIME type from UTI."""
        uti_to_mime = {
            'com.adobe.pdf': 'application/pdf',
            'public.jpeg': 'image/jpeg',
            'public.png': 'image/png',
            'public.tiff': 'image/tiff', 
            'public.heic': 'image/heic',
            'public.mp4': 'video/mp4',
            'public.mov': 'video/quicktime',
            'public.mp3': 'audio/mpeg',
            'public.m4a': 'audio/mp4',
            'public.plain-text': 'text/plain',
            'public.rtf': 'text/rtf',
            'com.microsoft.word.doc': 'application/msword',
            'org.openxmlformats.wordprocessingml.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        return uti_to_mime.get(self.type_uti) if self.type_uti else None
    
    @property
    def is_image(self) -> bool:
        """Check if attachment is an image."""
        if self.type_uti:
            return self.type_uti.startswith('public.') and any(img_type in self.type_uti for img_type in ['jpeg', 'png', 'tiff', 'heic', 'gif'])
        return False
    
    @property
    def is_video(self) -> bool:
        """Check if attachment is a video."""
        if self.type_uti:
            return any(vid_type in self.type_uti for vid_type in ['mp4', 'mov', 'avi', 'quicktime'])
        return False
    
    @property
    def is_audio(self) -> bool:
        """Check if attachment is audio."""
        if self.type_uti:
            return any(aud_type in self.type_uti for aud_type in ['mp3', 'm4a', 'wav', 'aiff'])
        return False
    
    @property  
    def is_document(self) -> bool:
        """Check if attachment is a document."""
        if self.type_uti:
            return any(doc_type in self.type_uti for doc_type in ['pdf', 'doc', 'docx', 'rtf', 'txt', 'pages'])
        return False
    
    def __str__(self) -> str:
        size_str = f", {self.file_size} bytes" if self.file_size else ""
        return f"Attachment(id={self.id}, filename='{self.filename}'{size_str})"


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
    attachments: list[Attachment] = field(default_factory=list)
    
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
    
    def has_attachments(self) -> bool:
        """Check if the note has any attachments."""
        return len(self.attachments) > 0
    
    def get_attachments_by_type(self, attachment_type: str) -> list[Attachment]:
        """Get attachments of a specific type (image, video, audio, document)."""
        type_filters = {
            'image': lambda a: a.is_image,
            'video': lambda a: a.is_video, 
            'audio': lambda a: a.is_audio,
            'document': lambda a: a.is_document
        }
        
        if attachment_type.lower() in type_filters:
            return [att for att in self.attachments if type_filters[attachment_type.lower()](att)]
        return []
    
    def get_attachments_by_extension(self, extension: str) -> list[Attachment]:
        """Get attachments with a specific file extension."""
        ext = extension.lower().lstrip('.')
        return [att for att in self.attachments if att.file_extension == ext]
    
    def get_folder_path(self, folders_dict: dict[int, Folder] | None = None) -> str:
        """Get the full folder path for this note (e.g., 'Notes/Cocktails/Classic')."""
        if folders_dict:
            return self.folder.get_path(folders_dict)
        return self.folder.name
    
    def __str__(self) -> str:
        return f"Note(id={self.id}, title='{self.title}', folder='{self.folder.name}')"