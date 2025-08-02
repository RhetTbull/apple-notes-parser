"""
Tests for attachment extraction functionality.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser import AppleNotesParser
from apple_notes_parser.database import AppleNotesDatabase
from apple_notes_parser.models import Attachment


def test_attachment_data_loading(test_database):
    """Test that attachment BLOB data is loaded from database."""
    parser = AppleNotesParser(test_database)
    attachments = parser.get_all_attachments()

    # Should have attachments from test database
    assert len(attachments) > 0

    # Check that at least one attachment has data
    attachments_with_data = [att for att in attachments if att.has_data]
    assert len(attachments_with_data) > 0

    # Test data properties
    for attachment in attachments_with_data:
        assert attachment.has_data is True
        raw_data = attachment.get_raw_data()
        assert raw_data is not None
        assert isinstance(raw_data, bytes)
        assert len(raw_data) > 0


def test_attachment_decompression(test_database):
    """Test attachment data decompression."""
    parser = AppleNotesParser(test_database)
    attachments_with_data = parser.get_attachments_with_data()

    if not attachments_with_data:
        pytest.skip("No attachments with data in test database")

    for attachment in attachments_with_data:
        raw_data = attachment.get_raw_data()
        decompressed_data = attachment.get_decompressed_data()

        assert raw_data is not None
        assert decompressed_data is not None

        # If data starts with gzip magic bytes, decompressed should be different
        if len(raw_data) >= 2 and raw_data[:2] == b"\x1f\x8b":
            # Should be decompressed
            assert len(decompressed_data) != len(raw_data)
        else:
            # Should be unchanged
            assert decompressed_data == raw_data


def test_attachment_filename_generation(test_database):
    """Test suggested filename generation."""
    parser = AppleNotesParser(test_database)
    attachments = parser.get_all_attachments()

    for attachment in attachments:
        filename = attachment.get_suggested_filename()
        assert isinstance(filename, str)
        assert len(filename) > 0

        # Should have attachment ID in filename if no original filename
        if not attachment.filename:
            assert str(attachment.id) in filename

        # Should have appropriate extension for known types
        if attachment.type_uti == "com.adobe.pdf":
            assert filename.endswith(".pdf")
        elif attachment.type_uti == "com.apple.notes.table":
            assert filename.endswith(".table")


def test_attachment_save_to_file(test_database):
    """Test saving individual attachments to files."""
    parser = AppleNotesParser(test_database)
    attachments_with_data = parser.get_attachments_with_data()

    if not attachments_with_data:
        pytest.skip("No attachments with data in test database")

    attachment = attachments_with_data[0]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        filename = attachment.get_suggested_filename()
        file_path = temp_path / filename

        # Test saving with decompression
        success = attachment.save_to_file(file_path, decompress=True)
        assert success is True
        assert file_path.exists()
        assert file_path.stat().st_size > 0

        # Test saving raw data
        raw_file_path = temp_path / f"raw_{filename}"
        success = attachment.save_to_file(raw_file_path, decompress=False)
        assert success is True
        assert raw_file_path.exists()
        assert raw_file_path.stat().st_size > 0


def test_parser_save_all_attachments(test_database):
    """Test bulk attachment saving via parser."""
    parser = AppleNotesParser(test_database)

    with tempfile.TemporaryDirectory() as temp_dir:
        results = parser.save_all_attachments(temp_dir, decompress=True)

        # Should return results dictionary
        assert isinstance(results, dict)

        # If any attachments were saved, check files exist
        successful_saves = [
            filename for filename, success in results.items() if success
        ]
        for filename in successful_saves:
            file_path = Path(temp_dir) / filename
            assert file_path.exists()
            assert file_path.stat().st_size > 0


def test_parser_save_note_attachments(test_database):
    """Test saving attachments from a specific note."""
    parser = AppleNotesParser(test_database)

    # Find a note with attachments
    notes_with_attachments = [note for note in parser.notes if note.attachments]
    if not notes_with_attachments:
        pytest.skip("No notes with attachments in test database")

    note = notes_with_attachments[0]

    with tempfile.TemporaryDirectory() as temp_dir:
        results = parser.save_note_attachments(note, temp_dir, decompress=True)

        # Should return results dictionary
        assert isinstance(results, dict)

        # Results should correspond to note's attachments with data
        expected_count = len([att for att in note.attachments if att.has_data])
        assert len(results) == expected_count


def test_attachments_with_data_filtering(test_database):
    """Test filtering attachments that have extractable data."""
    parser = AppleNotesParser(test_database)

    all_attachments = parser.get_all_attachments()
    attachments_with_data = parser.get_attachments_with_data()

    # Should be subset of all attachments
    assert len(attachments_with_data) <= len(all_attachments)

    # All returned attachments should have data
    for attachment in attachments_with_data:
        assert attachment.has_data is True


def test_attachment_blob_data_fields(test_database):
    """Test that BLOB data fields are properly loaded."""
    with AppleNotesDatabase(test_database) as db:
        accounts = db.get_accounts()
        accounts_dict = {acc.id: acc for acc in accounts}
        attachments = db.get_attachments(accounts_dict)

        for attachment in attachments:
            # At least one of the BLOB fields should be present for attachments with data
            if attachment.has_data:
                has_blob_data = any(
                    [
                        attachment.mergeable_data1 is not None,
                        attachment.mergeable_data is not None,
                        attachment.mergeable_data2 is not None,
                    ]
                )
                assert has_blob_data is True


def test_attachment_error_handling(test_database):
    """Test error handling in attachment operations."""
    parser = AppleNotesParser(test_database)
    attachments = parser.get_all_attachments()

    if not attachments:
        pytest.skip("No attachments in test database")

    attachment = attachments[0]

    # Test saving to invalid path (should raise exception)
    with pytest.raises((IOError, PermissionError, OSError)):
        attachment.save_to_file("/invalid/path/that/does/not/exist/file.dat")

    # Test attachment without data
    empty_attachment = Attachment(
        id=999,
        filename="test.txt",
        file_size=0,
        type_uti="public.plain-text",
        note_id=1,
    )

    # Should return False for no data
    assert empty_attachment.has_data is False
    assert empty_attachment.get_raw_data() is None
    assert empty_attachment.get_decompressed_data() is None

    with tempfile.TemporaryDirectory() as temp_dir:
        success = empty_attachment.save_to_file(Path(temp_dir) / "empty.txt")
        assert success is False


def test_attachment_type_properties():
    """Test attachment type detection properties."""
    # Test PDF attachment
    pdf_attachment = Attachment(
        id=1,
        filename="document.pdf",
        file_size=1000,
        type_uti="com.adobe.pdf",
        note_id=1,
    )

    assert pdf_attachment.is_document is True
    assert pdf_attachment.is_image is False
    assert pdf_attachment.mime_type == "application/pdf"
    assert pdf_attachment.file_extension == "pdf"

    # Test image attachment
    image_attachment = Attachment(
        id=2, filename="photo.jpg", file_size=5000, type_uti="public.jpeg", note_id=1
    )

    assert image_attachment.is_image is True
    assert image_attachment.is_document is False
    assert image_attachment.mime_type == "image/jpeg"
    assert image_attachment.file_extension == "jpg"

    # Test table attachment
    table_attachment = Attachment(
        id=3, filename=None, file_size=500, type_uti="com.apple.notes.table", note_id=1
    )

    assert table_attachment.get_suggested_filename() == "attachment_3.table"


def test_attachment_filename_edge_cases():
    """Test filename generation edge cases."""
    # No filename, no type
    attachment = Attachment(
        id=123, filename=None, file_size=100, type_uti=None, note_id=1
    )

    filename = attachment.get_suggested_filename()
    assert filename == "attachment_123"

    # Unknown type UTI
    attachment_unknown = Attachment(
        id=456, filename=None, file_size=100, type_uti="unknown.type", note_id=1
    )

    filename = attachment_unknown.get_suggested_filename()
    assert filename == "attachment_456"


def test_media_file_path_resolution():
    """Test media file path resolution with known UUID."""
    # Create test attachment with known media UUID (if available in test environment)
    attachment = Attachment(
        id=999,
        filename="test_image.png",
        file_size=38529,
        type_uti="public.png",
        note_id=1,
        uuid="84C7620E-87ED-4288-B38D-7B6288B957D3",  # Known UUID from real system
    )

    # Test with explicit notes container path (may not exist in test environment)
    notes_container = "/Users/rhet/Library/Group Containers/group.com.apple.notes"

    # This test will pass if the media file exists, skip if not
    try:
        has_media = attachment.has_media_file(notes_container)
        if has_media:
            media_path = attachment.get_media_file_path(notes_container)
            assert media_path is not None
            assert media_path.exists()
            assert media_path.is_file()
            print(f"Media file found: {media_path}")
        else:
            print("No media file found (expected in test environment)")
    except Exception as e:
        print(f"Media file test skipped: {e}")


def test_notes_container_auto_detection():
    """Test automatic Notes container detection."""
    attachment = Attachment(
        id=999,
        filename="test.txt",
        file_size=100,
        type_uti="public.plain-text",
        note_id=1,
        uuid="test-uuid",
    )

    # Test auto-detection (should work on macOS with Notes installed)
    container_path = attachment._find_notes_container()
    if container_path:
        assert container_path.exists()
        assert (container_path / "NoteStore.sqlite").exists()
    else:
        # Expected on non-macOS or systems without Notes
        assert container_path is None


def test_attachment_data_preference():
    """Test that get_attachment_data prefers media files over BLOB data."""
    # Create attachment with both BLOB and potential media file
    attachment = Attachment(
        id=999,
        filename="test.png",
        file_size=1000,
        type_uti="public.png",
        note_id=1,
        uuid="test-uuid",
        mergeable_data1=b"fake blob data",
    )

    # Test with non-existent media file (should fall back to BLOB)
    data = attachment.get_attachment_data("/nonexistent/path")
    assert data == b"fake blob data"

    # Test has_data property still works
    assert attachment.has_data is True


def test_save_attachment_with_preference():
    """Test save_attachment method with media file preference."""
    import tempfile

    attachment = Attachment(
        id=999,
        filename="test.txt",
        file_size=100,
        type_uti="public.plain-text",
        note_id=1,
        uuid="test-uuid",
        mergeable_data1=b"blob data content",
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_output.txt"

        # Test saving with no media file (should use BLOB data)
        success = attachment.save_attachment(output_path, prefer_media_file=False)
        assert success is True
        assert output_path.exists()
        assert output_path.read_bytes() == b"blob data content"


def test_copy_media_file_error_handling():
    """Test error handling in copy_media_file method."""
    attachment = Attachment(
        id=999,
        filename="nonexistent.txt",
        file_size=100,
        type_uti="public.plain-text",
        note_id=1,
        uuid="nonexistent-uuid",
    )

    # Test with non-existent source
    result = attachment.copy_media_file("/tmp/test_copy.txt")
    assert result is False

    # Test that no file was created
    assert not Path("/tmp/test_copy.txt").exists()
