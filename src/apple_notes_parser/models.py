"""Data models for Apple Notes entities."""

from __future__ import annotations

import gzip
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Account:
    """Represents an Apple Notes account."""

    id: int
    name: str
    identifier: str
    user_record_name: str | None = None

    def __str__(self) -> str:
        """Return string representation of Account.

        Returns:
            str: Formatted string containing account ID and name.
        """
        return f"Account(id={self.id}, name='{self.name}')"


@dataclass
class Folder:
    """Represents an Apple Notes folder."""

    id: int
    name: str
    account: Account
    uuid: str | None = None
    parent_id: int | None = None
    parent: Folder | None = field(default=None, init=False)  # Will be set after loading

    def get_path(self) -> str:
        """Get the full path of this folder (e.g., 'Notes/Cocktails/Classic').

        Returns:
            str: Full folder path from root to this folder, separated by '/'.
        """
        path_parts = []
        current_folder = self
        visited = set()  # Prevent infinite loops

        while current_folder and current_folder.id not in visited:
            visited.add(current_folder.id)
            path_parts.append(current_folder.name)

            if current_folder.parent:
                current_folder = current_folder.parent
            else:
                break

        # Reverse to get root-to-leaf order
        path_parts.reverse()
        return "/".join(path_parts)

    def get_parent(self) -> Folder | None:
        """Get the parent folder object.

        Returns:
            Folder | None: Parent folder object if exists, None otherwise.
        """
        return self.parent

    def is_root(self) -> bool:
        """Check if this is a root folder (no parent).

        Returns:
            bool: True if this folder has no parent, False otherwise.
        """
        return self.parent_id is None

    def __str__(self) -> str:
        """Return string representation of Folder.

        Returns:
            str: Formatted string containing folder ID, name, and account name.
        """
        return (
            f"Folder(id={self.id}, name='{self.name}', account='{self.account.name}')"
        )


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
    mergeable_data1: bytes | None = None  # Primary BLOB data storage
    mergeable_data: bytes | None = None  # Alternative BLOB data storage
    mergeable_data2: bytes | None = None  # Additional BLOB data storage

    @property
    def file_extension(self) -> str | None:
        """Get file extension from filename.

        Returns:
            str | None: File extension in lowercase (e.g., 'pdf', 'jpg') or None if no extension.
        """
        if self.filename and "." in self.filename:
            return self.filename.split(".")[-1].lower()
        return None

    @property
    def mime_type(self) -> str | None:
        """Get MIME type from UTI.

        Returns:
            str | None: MIME type string (e.g., 'application/pdf', 'image/jpeg') or None if unknown.
        """
        uti_to_mime = {
            "com.adobe.pdf": "application/pdf",
            "public.jpeg": "image/jpeg",
            "public.png": "image/png",
            "public.tiff": "image/tiff",
            "public.heic": "image/heic",
            "public.mp4": "video/mp4",
            "public.mov": "video/quicktime",
            "public.mp3": "audio/mpeg",
            "public.m4a": "audio/mp4",
            "public.plain-text": "text/plain",
            "public.rtf": "text/rtf",
            "com.microsoft.word.doc": "application/msword",
            "org.openxmlformats.wordprocessingml.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return uti_to_mime.get(self.type_uti) if self.type_uti else None

    @property
    def is_image(self) -> bool:
        """Check if attachment is an image.

        Returns:
            bool: True if attachment is an image file (jpeg, png, tiff, heic, gif), False otherwise.
        """
        if self.type_uti:
            return self.type_uti.startswith("public.") and any(
                img_type in self.type_uti
                for img_type in ["jpeg", "png", "tiff", "heic", "gif"]
            )
        return False

    @property
    def is_video(self) -> bool:
        """Check if attachment is a video.

        Returns:
            bool: True if attachment is a video file (mp4, mov, avi, quicktime), False otherwise.
        """
        if self.type_uti:
            return any(
                vid_type in self.type_uti
                for vid_type in ["mp4", "mov", "avi", "quicktime"]
            )
        return False

    @property
    def is_audio(self) -> bool:
        """Check if attachment is audio.

        Returns:
            bool: True if attachment is an audio file (mp3, m4a, wav, aiff), False otherwise.
        """
        if self.type_uti:
            return any(
                aud_type in self.type_uti for aud_type in ["mp3", "m4a", "wav", "aiff"]
            )
        return False

    @property
    def is_document(self) -> bool:
        """Check if attachment is a document.

        Returns:
            bool: True if attachment is a document file (pdf, doc, docx, rtf, txt, pages), False otherwise.
        """
        if self.type_uti:
            return any(
                doc_type in self.type_uti
                for doc_type in ["pdf", "doc", "docx", "rtf", "txt", "pages"]
            )
        return False

    @property
    def has_data(self) -> bool:
        """Check if attachment has extractable data.

        Returns:
            bool: True if attachment has data in any BLOB field, False otherwise.
        """
        return any([self.mergeable_data1, self.mergeable_data, self.mergeable_data2])

    def get_raw_data(self) -> bytes | None:
        """Get raw BLOB data from the attachment.

        Returns:
            bytes | None: Raw BLOB data from the first available source, or None if no data.
        """
        # Try each data field in order of preference
        for data_field in [
            self.mergeable_data1,
            self.mergeable_data,
            self.mergeable_data2,
        ]:
            if data_field:
                return data_field
        return None

    def get_decompressed_data(self) -> bytes | None:
        """Get decompressed attachment data.

        If the raw data is gzipped (detected by magic bytes), decompresses it.
        Otherwise returns the raw data unchanged.

        Returns:
            bytes | None: Decompressed attachment data, or None if no data available.
        """
        raw_data = self.get_raw_data()
        if not raw_data:
            return None

        # Check for gzip magic bytes (1F 8B)
        if len(raw_data) >= 2 and raw_data[:2] == b"\x1f\x8b":
            try:
                return gzip.decompress(raw_data)
            except gzip.BadGzipFile:
                # If gzip decompression fails, return raw data
                return raw_data

        return raw_data

    def save_to_file(
        self,
        output_path: str | Path,
        decompress: bool = True,
        notes_container_path: str | Path | None = None,
    ) -> bool:
        """Save attachment data to a file.

        Attempts to save media file data first (if available), then falls back to BLOB data.
        This method now seamlessly handles both media items stored on disk and BLOB data
        stored in the database.

        Args:
            output_path: Path where the attachment should be saved.
            decompress: If True, automatically decompress gzipped data. Defaults to True.
            notes_container_path: Path to Apple Notes container. If None, attempts to find automatically.

        Returns:
            bool: True if save was successful, False if no data available.

        Raises:
            IOError: If file writing fails.
            PermissionError: If insufficient permissions to write file.
        """
        output_path = Path(output_path)

        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # First try to copy from media file (more efficient for large files)
        media_path = self.get_media_file_path(notes_container_path)
        if media_path and media_path.exists():
            try:
                import shutil

                shutil.copy2(media_path, output_path)
                return True
            except OSError:
                # Fall through to BLOB data if media file copy fails
                pass

        # Fall back to BLOB data
        if decompress:
            data = self.get_decompressed_data()
        else:
            data = self.get_raw_data()

        if not data:
            return False

        # Write data to file
        with open(output_path, "wb") as f:
            f.write(data)

        return True

    def get_suggested_filename(self) -> str:
        """Get a suggested filename for saving the attachment.

        Returns:
            str: Suggested filename based on attachment metadata.
        """
        # Use existing filename if available
        if self.filename:
            return self.filename

        # Generate filename based on ID and type
        extension = ""
        if self.type_uti:
            # Map common UTIs to extensions
            uti_to_ext = {
                "com.adobe.pdf": ".pdf",
                "public.jpeg": ".jpg",
                "public.png": ".png",
                "public.tiff": ".tiff",
                "public.heic": ".heic",
                "public.mp4": ".mp4",
                "public.mov": ".mov",
                "public.mp3": ".mp3",
                "public.m4a": ".m4a",
                "public.plain-text": ".txt",
                "public.rtf": ".rtf",
                "com.microsoft.word.doc": ".doc",
                "com.apple.notes.table": ".table",
                "com.apple.drawing.2": ".drawing",
            }
            extension = uti_to_ext.get(self.type_uti, "")

        return f"attachment_{self.id}{extension}"

    def get_media_file_path(
        self, notes_container_path: str | Path | None = None
    ) -> Path | None:
        """Get the path to the attachment file in the Media folder.

        Args:
            notes_container_path: Path to Apple Notes container. If None, attempts to find automatically.

        Returns:
            Path | None: Path to the attachment file, or None if not found.
        """
        if not self.uuid:
            return None

        # Try to find the Notes container automatically if not provided
        if notes_container_path is None:
            notes_container_path = self._find_notes_container()
            if not notes_container_path:
                return None

        container_path = Path(notes_container_path)

        # Find the account folder in the container
        accounts_path = container_path / "Accounts"
        if not accounts_path.exists():
            return None

        # Look for account folders - typically only one for local accounts
        account_folders = [d for d in accounts_path.iterdir() if d.is_dir()]

        for account_folder in account_folders:
            media_path = account_folder / "Media" / self.uuid
            if media_path.exists():
                # Look for the actual file in subdirectories
                for item in media_path.rglob("*"):
                    if item.is_file() and not item.name.startswith("."):
                        return item

        # If UUID-based search failed and we have a filename, search by filename
        if self.filename:
            # Extract just the basename to avoid issues with path separators in rglob
            filename_basename = Path(self.filename).name
            for account_folder in account_folders:
                media_base = account_folder / "Media"
                if media_base.exists():
                    # Search all media directories for the filename
                    for item in media_base.rglob(filename_basename):
                        if item.is_file():
                            return item

        return None

    def _find_notes_container(self) -> Path | None:
        """Attempt to find the Apple Notes container automatically.

        Returns:
            Path | None: Path to the Notes container, or None if not found.
        """
        # Common paths for Apple Notes container
        possible_paths = [
            Path.home() / "Library" / "Group Containers" / "group.com.apple.notes",
            Path.home()
            / "Library"
            / "Containers"
            / "com.apple.Notes"
            / "Data"
            / "Library"
            / "Notes",
        ]

        for path in possible_paths:
            if path.exists() and (path / "NoteStore.sqlite").exists():
                return path

        return None

    def has_media_file(self, notes_container_path: str | Path | None = None) -> bool:
        """Check if the attachment has a media file available.

        Args:
            notes_container_path: Path to Apple Notes container. If None, attempts to find automatically.

        Returns:
            bool: True if media file exists, False otherwise.
        """
        return self.get_media_file_path(notes_container_path) is not None

    def copy_media_file(
        self, destination: str | Path, notes_container_path: str | Path | None = None
    ) -> bool:
        """Copy the attachment's media file to a destination.

        Args:
            destination: Path where the file should be copied.
            notes_container_path: Path to Apple Notes container. If None, attempts to find automatically.

        Returns:
            bool: True if copy was successful, False otherwise.

        Raises:
            IOError: If file copying fails.
        """
        source_path = self.get_media_file_path(notes_container_path)
        if not source_path:
            return False

        dest_path = Path(destination)

        # Create parent directories if they don't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import shutil

            shutil.copy2(source_path, dest_path)
            return True
        except OSError:
            return False

    def get_attachment_data(
        self, notes_container_path: str | Path | None = None
    ) -> bytes | None:
        """Get attachment data, preferring media files over BLOB data.

        Args:
            notes_container_path: Path to Apple Notes container. If None, attempts to find automatically.

        Returns:
            bytes | None: Attachment data from media file or BLOB, or None if not available.
        """
        # First try to get data from media file
        media_path = self.get_media_file_path(notes_container_path)
        if media_path and media_path.exists():
            try:
                return media_path.read_bytes()
            except OSError:
                pass

        # Fall back to BLOB data
        return self.get_decompressed_data()

    def save_attachment(
        self,
        output_path: str | Path,
        notes_container_path: str | Path | None = None,
        prefer_media_file: bool = True,
    ) -> bool:
        """Save attachment data to a file, preferring media files over BLOB data.

        Args:
            output_path: Path where the attachment should be saved.
            notes_container_path: Path to Apple Notes container. If None, attempts to find automatically.
            prefer_media_file: If True, prefer media file over BLOB data. Defaults to True.

        Returns:
            bool: True if save was successful, False if no data available.

        Raises:
            IOError: If file writing fails.
        """
        data = None

        if prefer_media_file:
            # Try media file first
            media_path = self.get_media_file_path(notes_container_path)
            if media_path and media_path.exists():
                # Direct copy is more efficient for large files
                return self.copy_media_file(output_path, notes_container_path)

            # Fall back to BLOB data
            data = self.get_decompressed_data()
        else:
            # Try BLOB data first, then media file
            data = self.get_decompressed_data()
            if not data:
                media_path = self.get_media_file_path(notes_container_path)
                if media_path and media_path.exists():
                    return self.copy_media_file(output_path, notes_container_path)

        if not data:
            return False

        output_path = Path(output_path)

        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write data to file
        with open(output_path, "wb") as f:
            f.write(data)

        return True

    def __str__(self) -> str:
        """Return string representation of Attachment.

        Returns:
            str: Formatted string containing attachment ID, filename, and optional file size.
        """
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

    def __post_init__(self) -> None:
        """Extract tags from content after initialization.

        This method is called automatically after dataclass initialization
        to perform additional setup tasks.
        """
        if self.content:
            self._extract_tags()

    def _extract_tags(self) -> None:
        """Extract hashtags from note content.

        Note:
            This method is kept for compatibility but tags are now set
            by the parser using protobuf data for better accuracy.
        """
        # Tags will be set by the parser using protobuf data
        # This method is kept for compatibility
        pass

    def has_tag(self, tag: str) -> bool:
        """Check if the note has a specific tag.

        Args:
            tag: Tag to search for (case-insensitive).

        Returns:
            bool: True if the note contains the specified tag, False otherwise.
        """
        return tag.lower() in [t.lower() for t in self.tags]

    def has_mention(self, mention: str) -> bool:
        """Check if the note has a specific mention.

        Args:
            mention: Mention to search for (case-insensitive).

        Returns:
            bool: True if the note contains the specified mention, False otherwise.
        """
        return mention.lower() in [m.lower() for m in self.mentions]

    def has_link(self, link: str) -> bool:
        """Check if the note contains a specific link.

        Args:
            link: URL to search for.

        Returns:
            bool: True if the note contains the specified link, False otherwise.
        """
        return link in self.links

    def has_attachments(self) -> bool:
        """Check if the note has any attachments.

        Returns:
            bool: True if the note has one or more attachments, False otherwise.
        """
        return len(self.attachments) > 0

    def get_attachments_by_type(self, attachment_type: str) -> list[Attachment]:
        """Get attachments of a specific type.

        Args:
            attachment_type: Type of attachments to retrieve. Must be one of:
                           'image', 'video', 'audio', or 'document'.

        Returns:
            list[Attachment]: List of attachments matching the specified type.
        """
        type_filters = {
            "image": lambda a: a.is_image,
            "video": lambda a: a.is_video,
            "audio": lambda a: a.is_audio,
            "document": lambda a: a.is_document,
        }

        if attachment_type.lower() in type_filters:
            return [
                att
                for att in self.attachments
                if type_filters[attachment_type.lower()](att)
            ]
        return []

    def get_attachments_by_extension(self, extension: str) -> list[Attachment]:
        """Get attachments with a specific file extension.

        Args:
            extension: File extension to search for (case-insensitive).
                      Can include or omit the leading dot (e.g., 'pdf' or '.pdf').

        Returns:
            list[Attachment]: List of attachments with the specified file extension.
        """
        ext = extension.lower().lstrip(".")
        return [att for att in self.attachments if att.file_extension == ext]

    def get_folder_path(self) -> str:
        """Get the full folder path for this note.

        Returns:
            str: Full folder path from root to containing folder, separated by '/'.
                Example: 'Notes/Cocktails/Classic'
        """
        return self.folder.get_path()

    def __str__(self) -> str:
        """Return string representation of Note.

        Returns:
            str: Formatted string containing note ID, title, and folder name.
        """
        return f"Note(id={self.id}, title='{self.title}', folder='{self.folder.name}')"
