"""Tests for media extraction functionality from GroupContainers test data."""

import tempfile
from pathlib import Path

import pytest

from apple_notes_parser.database import AppleNotesDatabase


@pytest.fixture
def sequoia_container_path():
    """Path to the macOS 15 Sequoia GroupContainer test data."""
    return (
        Path(__file__).parent
        / "data"
        / "GroupContainers"
        / "macOS15-Sequioa"
        / "group.com.apple.notes"
    )


@pytest.fixture
def tahoe_container_path():
    """Path to the macOS 26 Tahoe GroupContainer test data."""
    return (
        Path(__file__).parent
        / "data"
        / "GroupContainers"
        / "macOS26-Tahoe"
        / "group.com.apple.notes"
    )


@pytest.fixture
def original_bitcoin_pdf():
    """Path to the original bitcoin.pdf file for comparison."""
    return Path(__file__).parent / "data" / "bitcoin.pdf"


def test_sequoia_media_extraction(sequoia_container_path, original_bitcoin_pdf):
    """Test media extraction from macOS 15 Sequoia test data."""
    database_path = sequoia_container_path / "NoteStore.sqlite"
    assert database_path.exists(), f"Database not found: {database_path}"
    assert original_bitcoin_pdf.exists(), (
        f"Original PDF not found: {original_bitcoin_pdf}"
    )

    with AppleNotesDatabase(str(database_path)) as db:
        # Verify this is macOS 15
        assert db.get_macos_version() == 15

        # Get all notes
        accounts = {account.id: account for account in db.get_accounts()}
        assert len(accounts) > 0, "No accounts found"

        folders = {folder.id: folder for folder in db.get_folders(accounts)}
        assert len(folders) > 0, "No folders found"

        notes = db.get_notes(accounts, folders)
        assert len(notes) > 0, "No notes found"

        # Find note with bitcoin.pdf attachment
        bitcoin_note = None
        bitcoin_attachment = None

        for note in notes:
            for attachment in note.attachments:
                if attachment.filename == "bitcoin.pdf":
                    bitcoin_note = note
                    bitcoin_attachment = attachment
                    break
            if bitcoin_attachment:
                break

        assert bitcoin_note is not None, "Note with bitcoin.pdf not found"
        assert bitcoin_attachment is not None, "bitcoin.pdf attachment not found"

        # Verify attachment properties
        assert bitcoin_attachment.filename == "bitcoin.pdf"
        assert bitcoin_attachment.type_uti == "com.adobe.pdf"
        assert bitcoin_attachment.is_document is True
        assert bitcoin_attachment.file_extension == "pdf"

        # Test media file path discovery
        media_path = bitcoin_attachment.get_media_file_path(sequoia_container_path)
        assert media_path is not None, "Media file path not found"
        assert media_path.exists(), f"Media file does not exist: {media_path}"
        assert media_path.name == "bitcoin.pdf"

        # The media file should be in the expected location structure
        assert "Accounts/LocalAccount/Media" in str(media_path)

        # Test media file availability
        assert bitcoin_attachment.has_media_file(sequoia_container_path) is True

        # Extract and compare with original
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "extracted_bitcoin.pdf"

            # Test save_attachment method (prefers media file)
            success = bitcoin_attachment.save_attachment(
                output_path, sequoia_container_path
            )
            assert success is True, "Failed to save attachment"
            assert output_path.exists(), "Output file was not created"

            # Compare with original
            original_data = original_bitcoin_pdf.read_bytes()
            extracted_data = output_path.read_bytes()
            assert extracted_data == original_data, (
                "Extracted PDF does not match original"
            )

            # Test copy_media_file method directly
            copy_path = Path(temp_dir) / "copied_bitcoin.pdf"
            copy_success = bitcoin_attachment.copy_media_file(
                copy_path, sequoia_container_path
            )
            assert copy_success is True, "Failed to copy media file"
            assert copy_path.exists(), "Copied file was not created"

            # Verify copied file matches original
            copied_data = copy_path.read_bytes()
            assert copied_data == original_data, "Copied PDF does not match original"

            # Test get_attachment_data method
            attachment_data = bitcoin_attachment.get_attachment_data(
                sequoia_container_path
            )
            assert attachment_data is not None, "Failed to get attachment data"
            assert attachment_data == original_data, (
                "Attachment data does not match original"
            )


def test_tahoe_media_extraction(tahoe_container_path, original_bitcoin_pdf):
    """Test media extraction from macOS 26 Tahoe test data."""
    database_path = tahoe_container_path / "NoteStore.sqlite"
    assert database_path.exists(), f"Database not found: {database_path}"
    assert original_bitcoin_pdf.exists(), (
        f"Original PDF not found: {original_bitcoin_pdf}"
    )

    with AppleNotesDatabase(str(database_path)) as db:
        # Verify this is macOS 26
        assert db.get_macos_version() == 26

        # Get all notes
        accounts = {account.id: account for account in db.get_accounts()}
        assert len(accounts) > 0, "No accounts found"

        folders = {folder.id: folder for folder in db.get_folders(accounts)}
        assert len(folders) > 0, "No folders found"

        notes = db.get_notes(accounts, folders)
        assert len(notes) > 0, "No notes found"

        # Find note with bitcoin.pdf attachment
        bitcoin_note = None
        bitcoin_attachment = None

        for note in notes:
            for attachment in note.attachments:
                if attachment.filename == "bitcoin.pdf":
                    bitcoin_note = note
                    bitcoin_attachment = attachment
                    break
            if bitcoin_attachment:
                break

        assert bitcoin_note is not None, "Note with bitcoin.pdf not found"
        assert bitcoin_attachment is not None, "bitcoin.pdf attachment not found"

        # Verify attachment properties
        assert bitcoin_attachment.filename == "bitcoin.pdf"
        assert bitcoin_attachment.type_uti == "com.adobe.pdf"
        assert bitcoin_attachment.is_document is True
        assert bitcoin_attachment.file_extension == "pdf"

        # Test media file path discovery
        media_path = bitcoin_attachment.get_media_file_path(tahoe_container_path)
        assert media_path is not None, "Media file path not found"
        assert media_path.exists(), f"Media file does not exist: {media_path}"
        assert media_path.name == "bitcoin.pdf"

        # The media file should be in the expected location structure
        assert "Accounts/LocalAccount/Media" in str(media_path)

        # Test media file availability
        assert bitcoin_attachment.has_media_file(tahoe_container_path) is True

        # Extract and compare with original
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "extracted_bitcoin_tahoe.pdf"

            # Test save_attachment method (prefers media file)
            success = bitcoin_attachment.save_attachment(
                output_path, tahoe_container_path
            )
            assert success is True, "Failed to save attachment"
            assert output_path.exists(), "Output file was not created"

            # Compare with original
            original_data = original_bitcoin_pdf.read_bytes()
            extracted_data = output_path.read_bytes()
            assert extracted_data == original_data, (
                "Extracted PDF does not match original"
            )


def test_both_versions_consistency(sequoia_container_path, tahoe_container_path):
    """Test that both database versions can extract the same attachment consistently."""
    sequoia_db_path = sequoia_container_path / "NoteStore.sqlite"
    tahoe_db_path = tahoe_container_path / "NoteStore.sqlite"

    # Extract data from both versions
    sequoia_data = None
    tahoe_data = None

    with AppleNotesDatabase(str(sequoia_db_path)) as db:
        accounts = {account.id: account for account in db.get_accounts()}
        folders = {folder.id: folder for folder in db.get_folders(accounts)}
        notes = db.get_notes(accounts, folders)

        for note in notes:
            for attachment in note.attachments:
                if attachment.filename == "bitcoin.pdf":
                    sequoia_data = attachment.get_attachment_data(
                        sequoia_container_path
                    )
                    break
            if sequoia_data:
                break

    with AppleNotesDatabase(str(tahoe_db_path)) as db:
        accounts = {account.id: account for account in db.get_accounts()}
        folders = {folder.id: folder for folder in db.get_folders(accounts)}
        notes = db.get_notes(accounts, folders)

        for note in notes:
            for attachment in note.attachments:
                if attachment.filename == "bitcoin.pdf":
                    tahoe_data = attachment.get_attachment_data(tahoe_container_path)
                    break
            if tahoe_data:
                break

    assert sequoia_data is not None, "Failed to extract data from Sequoia database"
    assert tahoe_data is not None, "Failed to extract data from Tahoe database"
    assert sequoia_data == tahoe_data, "Data from both versions should be identical"


def test_media_path_without_container_path_fails(sequoia_container_path):
    """Test that media file operations fail when container path is not provided."""
    database_path = sequoia_container_path / "NoteStore.sqlite"

    with AppleNotesDatabase(str(database_path)) as db:
        accounts = {account.id: account for account in db.get_accounts()}
        folders = {folder.id: folder for folder in db.get_folders(accounts)}
        notes = db.get_notes(accounts, folders)

        # Find bitcoin attachment
        bitcoin_attachment = None
        for note in notes:
            for attachment in note.attachments:
                if attachment.filename == "bitcoin.pdf":
                    bitcoin_attachment = attachment
                    break
            if bitcoin_attachment:
                break

        assert bitcoin_attachment is not None

        # These operations should fail without container path since we're not on macOS
        # with the default Notes location
        assert bitcoin_attachment.get_media_file_path() is None
        assert bitcoin_attachment.has_media_file() is False

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "should_fail.pdf"
            success = bitcoin_attachment.copy_media_file(output_path)
            assert success is False


def test_nonexistent_attachment_uuid(sequoia_container_path):
    """Test behavior with non-existent attachment UUID."""
    database_path = sequoia_container_path / "NoteStore.sqlite"

    with AppleNotesDatabase(str(database_path)) as db:
        accounts = {account.id: account for account in db.get_accounts()}
        folders = {folder.id: folder for folder in db.get_folders(accounts)}
        notes = db.get_notes(accounts, folders)

        # Find any attachment and modify its UUID
        test_attachment = None
        for note in notes:
            if note.attachments:
                test_attachment = note.attachments[0]
                break

        assert test_attachment is not None

        # Create a copy with a fake UUID
        from apple_notes_parser.models import Attachment

        fake_attachment = Attachment(
            id=test_attachment.id,
            filename=test_attachment.filename,
            file_size=test_attachment.file_size,
            type_uti=test_attachment.type_uti,
            note_id=test_attachment.note_id,
            uuid="FAKE-UUID-DOES-NOT-EXIST",
        )

        # Operations should fail gracefully
        assert fake_attachment.get_media_file_path(sequoia_container_path) is None
        assert fake_attachment.has_media_file(sequoia_container_path) is False

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "should_not_exist.pdf"
            success = fake_attachment.copy_media_file(
                output_path, sequoia_container_path
            )
            assert success is False
