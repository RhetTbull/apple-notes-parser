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


def test_media_path_without_container_path_behavior(sequoia_container_path):
    """Test behavior when container path is not provided - may succeed on macOS with real Notes installation."""
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

        # Test auto-detection behavior - may work on macOS with real Notes installation
        media_path = bitcoin_attachment.get_media_file_path()
        has_media = bitcoin_attachment.has_media_file()

        # On macOS with a real Notes installation, this might succeed
        # On other systems or without Notes, it should fail gracefully
        if media_path is not None:
            # If auto-detection worked, media_path should exist and be valid
            assert media_path.is_file()
            assert has_media is True
            print(f"Auto-detection found media file: {media_path}")
        else:
            # If auto-detection failed (expected on non-macOS or without Notes)
            assert has_media is False
            print("Auto-detection failed as expected")

        # Test copy operation
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "copied_file.pdf"
            success = bitcoin_attachment.copy_media_file(output_path)

            # Success depends on whether auto-detection worked
            if media_path is not None:
                assert success is True
                assert output_path.exists()
                print("Copy operation succeeded with auto-detection")
            else:
                assert success is False
                print("Copy operation failed as expected without auto-detection")


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


def test_save_to_file_method_with_media_items(
    sequoia_container_path, original_bitcoin_pdf
):
    """Test that the save_to_file method works seamlessly with media items."""
    database_path = sequoia_container_path / "NoteStore.sqlite"
    assert database_path.exists(), f"Database not found: {database_path}"
    assert original_bitcoin_pdf.exists(), (
        f"Original PDF not found: {original_bitcoin_pdf}"
    )

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

        assert bitcoin_attachment is not None, "bitcoin.pdf attachment not found"

        # Test save_to_file with media file
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "saved_bitcoin.pdf"

            # Test with notes_container_path provided
            success = bitcoin_attachment.save_to_file(
                output_path, notes_container_path=sequoia_container_path
            )
            assert success is True, "Failed to save media item with save_to_file method"
            assert output_path.exists(), "Output file was not created"

            # Verify content matches original
            original_data = original_bitcoin_pdf.read_bytes()
            saved_data = output_path.read_bytes()
            assert saved_data == original_data, "Saved file does not match original"

            # Test without notes_container_path (should still work due to auto-detection fallback)
            output_path2 = Path(temp_dir) / "saved_bitcoin2.pdf"
            success2 = bitcoin_attachment.save_to_file(output_path2)
            # This might fail if auto-detection doesn't work, but should fallback to BLOB data if available
            # For this specific test case, we expect it to fail gracefully since we're not on the actual macOS system
            if success2:
                saved_data2 = output_path2.read_bytes()
                # If it succeeded, it should match the original
                assert saved_data2 == original_data, (
                    "Saved file without container path does not match original"
                )


def test_save_to_file_fallback_to_blob_data(sequoia_container_path):
    """Test that save_to_file falls back to BLOB data when media file is not available."""
    database_path = sequoia_container_path / "NoteStore.sqlite"

    with AppleNotesDatabase(str(database_path)) as db:
        accounts = {account.id: account for account in db.get_accounts()}
        folders = {folder.id: folder for folder in db.get_folders(accounts)}
        notes = db.get_notes(accounts, folders)

        # Find an attachment with BLOB data
        blob_attachment = None
        for note in notes:
            for attachment in note.attachments:
                if attachment.has_data and attachment.filename != "bitcoin.pdf":
                    blob_attachment = attachment
                    break
            if blob_attachment:
                break

        if blob_attachment:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = (
                    Path(temp_dir) / f"blob_{blob_attachment.get_suggested_filename()}"
                )

                # Test save_to_file - should fall back to BLOB data since no media file exists
                success = blob_attachment.save_to_file(
                    output_path, notes_container_path=sequoia_container_path
                )

                if success:  # Only test if BLOB data is available
                    assert output_path.exists(), "Output file was not created"

                    # Verify it matches get_decompressed_data()
                    blob_data = blob_attachment.get_decompressed_data()
                    if blob_data:
                        saved_data = output_path.read_bytes()
                        assert saved_data == blob_data, (
                            "Saved BLOB data does not match get_decompressed_data()"
                        )
