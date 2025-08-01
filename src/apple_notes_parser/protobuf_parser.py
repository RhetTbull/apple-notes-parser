"""Protobuf parsing utilities for Apple Notes data."""

from __future__ import annotations

import gzip
import re
from typing import Any

from google.protobuf.message import DecodeError

from .exceptions import ProtobufError
from .notestore_pb2 import NoteStoreProto


class ProtobufParser:
    """Handles parsing of Apple Notes protobuf data."""

    @staticmethod
    def extract_note_text(zdata: bytes) -> str | None:
        """Extract plain text from compressed note data.

        Processes gzipped protobuf data from Apple Notes database to extract
        readable text content. Falls back to manual text extraction if
        protobuf parsing fails.

        Args:
            zdata: Raw bytes from the ZDATA column in the database.

        Returns:
            str | None: Extracted plain text content or None if extraction fails.

        Raises:
            ProtobufError: If critical errors occur during protobuf processing.
        """
        if not zdata:
            return None

        try:
            # Check if data is gzipped
            if len(zdata) > 2 and zdata[0:2] == b"\x1f\x8b":
                # Decompress gzipped data
                decompressed = gzip.decompress(zdata)

                # Parse as protobuf
                try:
                    note_store = NoteStoreProto()
                    note_store.ParseFromString(decompressed)

                    if note_store.HasField("document") and note_store.document.HasField(
                        "note"
                    ):
                        return note_store.document.note.note_text

                except DecodeError:
                    # If protobuf parsing fails, try to extract text manually
                    return ProtobufParser._extract_text_fallback(decompressed)
            else:
                # Try to decode as plain text (legacy format)
                try:
                    return zdata.decode("utf-8", errors="ignore")
                except (UnicodeDecodeError, ValueError):
                    return None

        except Exception as e:
            raise ProtobufError(f"Failed to extract note text: {e}")

        return None

    @staticmethod
    def _extract_text_fallback(data: bytes) -> str | None:
        """Fallback method to extract text when protobuf parsing fails.

        Attempts to find readable text in binary data by decoding as UTF-8
        and cleaning up non-printable characters.

        Args:
            data: Decompressed binary data from note.

        Returns:
            str | None: Cleaned text content or None if no readable text found.
        """
        try:
            # Try to find readable text in the binary data
            text = data.decode("utf-8", errors="ignore")
            # Clean up the text by removing non-printable characters
            text = re.sub(r"[^\x20-\x7E\n\r\t]", "", text)
            # Remove excessive whitespace
            text = re.sub(r"\s+", " ", text).strip()
            return text if text else None
        except (UnicodeDecodeError, ValueError, re.error):
            return None

    @staticmethod
    def extract_hashtags(text: str) -> list[str]:
        """Extract hashtags from note text.

        Uses regex pattern to find hashtag patterns (#word) in the text.

        Args:
            text: Note text content to search.

        Returns:
            list[str]: List of unique hashtags found (without # symbol).
        """
        if not text:
            return []

        # Pattern to match hashtags
        hashtag_pattern = r"#(\w+)"
        matches = re.findall(hashtag_pattern, text)
        return list(set(matches))  # Remove duplicates

    @staticmethod
    def extract_mentions(text: str) -> list[str]:
        """Extract @mentions from note text.

        Uses regex pattern to find mention patterns (@username) in the text.

        Args:
            text: Note text content to search.

        Returns:
            list[str]: List of unique mentions found (without @ symbol).
        """
        if not text:
            return []

        # Pattern to match @mentions
        mention_pattern = r"@(\w+)"
        matches = re.findall(mention_pattern, text)
        return list(set(matches))  # Remove duplicates

    @staticmethod
    def extract_links(text: str) -> list[str]:
        """Extract URLs from note text.

        Uses regex pattern to find HTTP/HTTPS URLs in the text.

        Args:
            text: Note text content to search.

        Returns:
            list[str]: List of unique URLs found.
        """
        if not text:
            return []

        # Pattern to match URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,!?;:)]'
        matches = re.findall(url_pattern, text)
        return list(set(matches))  # Remove duplicates

    @staticmethod
    def parse_note_structure(zdata: bytes) -> dict[str, Any]:
        """Parse note structure and extract metadata.

        Parses the protobuf structure of a note to extract text content,
        formatting information, embedded objects, and attachment references.

        Args:
            zdata: Raw bytes from the ZDATA column in the database.

        Returns:
            dict[str, Any]: Dictionary containing:
                - 'has_document': Whether note has document structure
                - 'text': Extracted text content
                - 'attribute_runs': List of formatting information
                - 'attachments': List of attachment references
                - 'hashtags': List of hashtags found in text
                - 'mentions': List of mentions found in text
                - 'links': List of URLs found in text

        Raises:
            ProtobufError: If critical errors occur during protobuf processing.
        """
        if not zdata:
            return {}

        try:
            # Check if data is gzipped
            if len(zdata) > 2 and zdata[0:2] == b"\x1f\x8b":
                decompressed = gzip.decompress(zdata)

                try:
                    note_store = NoteStoreProto()
                    note_store.ParseFromString(decompressed)

                    result = {
                        "has_document": note_store.HasField("document"),
                        "text": None,
                        "attribute_runs": [],
                        "attachments": [],
                        "hashtags": [],
                        "mentions": [],
                        "links": [],
                    }

                    if note_store.HasField("document") and note_store.document.HasField(
                        "note"
                    ):
                        note = note_store.document.note
                        result["text"] = note.note_text

                        # Extract hashtags, mentions, and links
                        if note.note_text:
                            result["hashtags"] = ProtobufParser.extract_hashtags(
                                note.note_text
                            )
                            result["mentions"] = ProtobufParser.extract_mentions(
                                note.note_text
                            )
                            result["links"] = ProtobufParser.extract_links(
                                note.note_text
                            )

                        # Process attribute runs (formatting information)
                        for i, attr_run in enumerate(note.attribute_run):
                            run_info = {
                                "index": i,
                                "length": (
                                    attr_run.length
                                    if attr_run.HasField("length")
                                    else 0
                                ),
                                "has_attachment": attr_run.HasField("attachment_info"),
                                "has_link": attr_run.HasField("link"),
                                "has_font": attr_run.HasField("font"),
                                "has_paragraph_style": attr_run.HasField(
                                    "paragraph_style"
                                ),
                            }

                            if attr_run.HasField("attachment_info"):
                                attachment = {
                                    "identifier": attr_run.attachment_info.attachment_identifier,
                                    "type_uti": attr_run.attachment_info.type_uti,
                                }
                                result["attachments"].append(attachment)

                            result["attribute_runs"].append(run_info)

                    return result

                except DecodeError:
                    # If protobuf parsing fails, return basic structure
                    text = ProtobufParser._extract_text_fallback(decompressed)
                    return {
                        "has_document": False,
                        "text": text,
                        "attribute_runs": [],
                        "attachments": [],
                        "hashtags": (
                            ProtobufParser.extract_hashtags(text) if text else []
                        ),
                        "mentions": (
                            ProtobufParser.extract_mentions(text) if text else []
                        ),
                        "links": ProtobufParser.extract_links(text) if text else [],
                    }
            else:
                # Legacy format
                try:
                    text = zdata.decode("utf-8", errors="ignore")
                    return {
                        "has_document": False,
                        "text": text,
                        "attribute_runs": [],
                        "attachments": [],
                        "hashtags": ProtobufParser.extract_hashtags(text),
                        "mentions": ProtobufParser.extract_mentions(text),
                        "links": ProtobufParser.extract_links(text),
                    }
                except (UnicodeDecodeError, ValueError):
                    return {}

        except Exception as e:
            raise ProtobufError(f"Failed to parse note structure: {e}")

    @staticmethod
    def is_gzipped(data: bytes) -> bool:
        """Check if data is gzip compressed.

        Checks for the gzip magic number (0x1f, 0x8b) at the start of the data.

        Args:
            data: Binary data to check.

        Returns:
            bool: True if data appears to be gzip compressed, False otherwise.
        """
        return len(data) > 2 and data[0:2] == b"\x1f\x8b"
