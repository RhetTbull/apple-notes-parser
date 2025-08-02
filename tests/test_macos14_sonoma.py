"""
Tests for macOS 14 (Sonoma) database support.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser import AppleNotesParser
from apple_notes_parser.database import AppleNotesDatabase


@pytest.fixture
def macos14_db_connection(macos_14_database):
    """Fixture providing a connected AppleNotesDatabase instance for macOS 14."""
    with AppleNotesDatabase(macos_14_database) as db:
        yield db


def test_macos14_version_detection(macos14_db_connection):
    """Test that macOS 14 database is correctly identified."""
    version = macos14_db_connection.get_macos_version()
    assert version == 14, f"Expected database version 14 for macOS 14, got {version}"


def test_macos14_z_uuid_extraction(macos14_db_connection):
    """Test Z_UUID extraction from macOS 14 database."""
    z_uuid = macos14_db_connection.get_z_uuid()
    assert z_uuid == "96FBBB9A-C1A9-4216-ACA4-1BE22EC8E9B4"


def test_macos14_basic_data_extraction(macos14_db_connection):
    """Test basic data extraction from macOS 14 database."""
    # Test accounts
    accounts = macos14_db_connection.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].name == "On My Mac"

    # Test folders
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos14_db_connection.get_folders(accounts_dict)
    assert len(folders) == 6

    # Test notes
    folders_dict = {f.id: f for f in folders}
    notes = macos14_db_connection.get_notes(accounts_dict, folders_dict)
    assert len(notes) == 8


def test_macos14_folder_structure(macos14_db_connection):
    """Test folder hierarchy in macOS 14 database."""
    accounts = macos14_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos14_db_connection.get_folders(accounts_dict)

    # Verify expected folders exist
    folder_names = {f.name for f in folders}
    expected_folders = {
        "Recently Deleted",
        "Notes",
        "Folder",
        "Folder2",
        "Subfolder",
        "Subsubfolder",
    }
    assert folder_names == expected_folders

    # Test folder hierarchy
    folders_by_name = {f.name: f for f in folders}

    # Test root folders
    assert folders_by_name["Notes"].is_root()
    assert folders_by_name["Recently Deleted"].is_root()
    assert folders_by_name["Folder"].is_root()
    assert folders_by_name["Folder2"].is_root()

    # Test nested folders
    subfolder = folders_by_name["Subfolder"]
    assert not subfolder.is_root()
    assert subfolder.get_parent().name == "Folder2"

    subsubfolder = folders_by_name["Subsubfolder"]
    assert not subsubfolder.is_root()
    assert subsubfolder.get_parent().name == "Subfolder"


def test_macos14_notes_content(macos14_db_connection):
    """Test note content extraction from macOS 14 database."""
    accounts = macos14_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos14_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos14_db_connection.get_notes(accounts_dict, folders_dict)

    # Find specific notes by title
    notes_by_title = {n.title: n for n in notes if n.title}

    # Test password protected note
    protected_note = notes_by_title.get("This note is password protected")
    assert protected_note is not None
    assert protected_note.is_password_protected

    # Test formatted note
    formatted_note = notes_by_title.get("This note has special formatting")
    assert formatted_note is not None
    assert not formatted_note.is_password_protected

    # Test attachment note (macOS 14 specific feature)
    attachment_note = notes_by_title.get("This note has an attachment")
    assert attachment_note is not None
    assert not attachment_note.is_password_protected
    assert attachment_note.folder.name == "Notes"

    # Test deleted note (macOS 14 specific)
    deleted_note = notes_by_title.get("This is a deleted note")
    assert deleted_note is not None
    assert deleted_note.folder.name == "Recently Deleted"
    assert not deleted_note.is_password_protected

    # Test folder hierarchy notes
    folder_note = notes_by_title.get("This note is in a folder")
    assert folder_note is not None
    assert folder_note.folder.name == "Folder"

    # Test deeply nested note
    deep_note = notes_by_title.get("This note is deeply buried")
    assert deep_note is not None
    assert deep_note.folder.name == "Subsubfolder"

    # Test plain note
    plain_note = notes_by_title.get("This is a plain note")
    assert plain_note is not None
    assert plain_note.folder.name == "Notes"


def test_macos14_applescript_ids(macos14_db_connection):
    """Test AppleScript ID construction for macOS 14 database."""
    accounts = macos14_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos14_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos14_db_connection.get_notes(accounts_dict, folders_dict)

    # All notes should have AppleScript IDs
    for note in notes:
        assert note.applescript_id is not None
        assert note.applescript_id.startswith("x-coredata://")
        assert "/ICNote/p" in note.applescript_id
        assert "96FBBB9A-C1A9-4216-ACA4-1BE22EC8E9B4" in note.applescript_id

    # Test specific AppleScript IDs match expected pattern
    notes_by_title = {n.title: n for n in notes if n.title}
    plain_note = notes_by_title.get("This is a plain note")
    assert plain_note is not None
    assert (
        plain_note.applescript_id
        == "x-coredata://96FBBB9A-C1A9-4216-ACA4-1BE22EC8E9B4/ICNote/p13"
    )


def test_macos14_attachment_functionality(macos_14_database):
    """Test attachment functionality in macOS 14."""
    parser = AppleNotesParser(macos_14_database)

    # macOS 14 has good attachment support
    notes_with_attachments = parser.get_notes_with_attachments()
    assert len(notes_with_attachments) >= 1

    # Find the specific attachment note
    attachment_notes = [
        note for note in parser.notes if note.title == "This note has an attachment"
    ]
    assert len(attachment_notes) == 1

    attachment_note = attachment_notes[0]
    assert len(attachment_note.attachments) >= 1

    # Test attachment properties
    attachment = attachment_note.attachments[0]
    assert attachment.filename is not None
    assert "bitcoin.pdf" in attachment.filename or attachment.filename.endswith(".pdf")


def test_macos14_password_protection_detection(macos_14_database):
    """Test detection of password-protected notes."""
    parser = AppleNotesParser(macos_14_database)

    protected_notes = parser.get_protected_notes()
    assert isinstance(protected_notes, list)
    assert len(protected_notes) >= 1

    # Verify the specific protected note
    protected_titles = [note.title for note in protected_notes]
    assert "This note is password protected" in protected_titles


def test_macos14_deleted_notes_support(macos_14_database):
    """Test that macOS 14 properly handles deleted notes."""
    parser = AppleNotesParser(macos_14_database)

    # Find the recently deleted folder
    recently_deleted_folder = None
    for folder in parser.folders:
        if folder.name == "Recently Deleted":
            recently_deleted_folder = folder
            break

    assert recently_deleted_folder is not None, (
        "Recently Deleted folder should exist in macOS 14"
    )

    # Find notes in recently deleted folder
    deleted_notes = [
        note for note in parser.notes if note.folder.name == "Recently Deleted"
    ]
    assert len(deleted_notes) >= 1, "Should have at least one deleted note"

    # Verify deleted note properties
    deleted_note = deleted_notes[0]
    assert deleted_note.title == "This is a deleted note"
    assert not deleted_note.is_password_protected


def test_macos14_search_functionality(macos_14_database):
    """Test note search functionality."""
    parser = AppleNotesParser(macos_14_database)

    # Search for specific text that should exist
    results = parser.search_notes("buried")
    assert len(results) >= 1

    # Case insensitive search
    results_case = parser.search_notes("BURIED", case_sensitive=False)
    assert len(results_case) >= len(results)

    # Search for text in title
    results_title = parser.search_notes("folder")
    assert len(results_title) >= 1

    # Search for attachment-related content
    results_attachment = parser.search_notes("attachment")
    assert len(results_attachment) >= 1


def test_macos14_export_functionality(macos_14_database):
    """Test export functionality with macOS 14 database."""
    parser = AppleNotesParser(macos_14_database)

    # Test export to dict
    export_data = parser.export_notes_to_dict(include_content=True)

    assert "accounts" in export_data
    assert "folders" in export_data
    assert "notes" in export_data

    assert len(export_data["accounts"]) == 1
    assert len(export_data["folders"]) == 6
    assert len(export_data["notes"]) == 8

    # Verify account data
    account = export_data["accounts"][0]
    assert account["name"] == "On My Mac"

    # Verify folder data
    folder_names = {f["name"] for f in export_data["folders"]}
    expected_folders = {
        "Recently Deleted",
        "Notes",
        "Folder",
        "Folder2",
        "Subfolder",
        "Subsubfolder",
    }
    assert folder_names == expected_folders

    # Verify note data includes specific notes
    note_titles = [n["title"] for n in export_data["notes"] if n["title"]]
    assert "This note has an attachment" in note_titles
    assert "This note is password protected" in note_titles
    assert "This is a deleted note" in note_titles

    # Verify AppleScript IDs use correct UUID
    for note_data in export_data["notes"]:
        assert "applescript_id" in note_data
        assert note_data["applescript_id"] is not None
        assert "96FBBB9A-C1A9-4216-ACA4-1BE22EC8E9B4" in note_data["applescript_id"]


def test_macos14_folder_path_reconstruction(macos_14_database):
    """Test folder path reconstruction for macOS 14."""
    parser = AppleNotesParser(macos_14_database)

    # Test deep hierarchy path
    deep_notes = [
        note for note in parser.notes if note.title == "This note is deeply buried"
    ]
    assert len(deep_notes) == 1
    deep_note = deep_notes[0]
    folder_path = deep_note.get_folder_path()
    assert folder_path == "Folder2/Subfolder/Subsubfolder"

    # Test single level folder
    folder_notes = [
        note for note in parser.notes if note.title == "This note is in a folder"
    ]
    assert len(folder_notes) == 1
    folder_note = folder_notes[0]
    folder_path = folder_note.get_folder_path()
    assert folder_path == "Folder"


def test_macos14_parser_integration(macos_14_database):
    """Test AppleNotesParser integration with macOS 14 database."""
    parser = AppleNotesParser(macos_14_database)

    # Basic functionality
    assert len(parser.notes) == 8
    assert len(parser.folders) == 6
    assert len(parser.accounts) == 1

    # Search functionality
    search_results = parser.search_notes("note")
    assert len(search_results) > 0

    # Folder functionality - verify all folders have valid paths
    for folder in parser.folders:
        path = folder.get_path()
        assert isinstance(path, str)
        assert len(path) > 0


def test_macos14_database_schema_compatibility(macos14_db_connection):
    """Test that macOS 14 database schema is handled correctly."""
    cursor = macos14_db_connection.connection.cursor()

    # Check that we can query basic tables
    cursor.execute(
        "SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT WHERE ZTITLE2 IS NOT NULL"
    )
    folder_count = cursor.fetchone()[0]
    assert folder_count >= 6

    cursor.execute(
        "SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT WHERE ZTITLE1 IS NOT NULL"
    )
    note_count = cursor.fetchone()[0]
    assert note_count >= 7

    # Verify database structure
    cursor.execute("PRAGMA table_info(ZICCLOUDSYNCINGOBJECT)")
    columns = [row[1] for row in cursor.fetchall()]

    # Basic columns should exist
    assert "ZTITLE1" in columns  # Note titles
    assert "ZTITLE2" in columns  # Folder titles
    assert "ZNOTEDATA" in columns  # Note content


def test_macos14_version_specific_features(macos_14_database):
    """Test macOS 14 specific features and improvements."""
    parser = AppleNotesParser(macos_14_database)

    # macOS 14 should have good attachment support
    notes_with_attachments = parser.get_notes_with_attachments()
    assert len(notes_with_attachments) >= 1

    # Password protection should work
    protected_notes = parser.get_protected_notes()
    assert len(protected_notes) >= 1

    # Recently deleted folder should be available
    folder_names = {folder.name for folder in parser.folders}
    assert "Recently Deleted" in folder_names

    # All basic parser operations should work
    export_data = parser.export_notes_to_dict()
    assert len(export_data["notes"]) == 8
    assert len(export_data["folders"]) == 6
    assert len(export_data["accounts"]) == 1

    # Verify that notes with attachments can be found
    attachment_notes = [
        note for note in parser.notes if note.title == "This note has an attachment"
    ]
    assert len(attachment_notes) == 1


def test_macos14_attachment_extraction(macos14_db_connection):
    """Test attachment extraction capabilities in macOS 14."""
    accounts = macos14_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos14_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos14_db_connection.get_notes(accounts_dict, folders_dict)

    # Find notes with attachments
    notes_with_attachments = [note for note in notes if note.attachments]
    assert len(notes_with_attachments) >= 1

    # Test the specific attachment note
    attachment_note = None
    for note in notes:
        if note.title == "This note has an attachment":
            attachment_note = note
            break

    assert attachment_note is not None
    assert len(attachment_note.attachments) >= 1

    # Test attachment properties
    attachment = attachment_note.attachments[0]
    assert attachment.filename is not None
    assert attachment.uuid is not None


def test_macos14_note_content_extraction(macos14_db_connection):
    """Test that note content is properly extracted and not null."""
    accounts = macos14_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos14_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos14_db_connection.get_notes(accounts_dict, folders_dict)

    # At least some notes should have non-null content
    notes_with_content = [note for note in notes if note.content]
    assert len(notes_with_content) > 0, (
        "No notes have content - content extraction may be failing"
    )

    # Check specific notes we know should have content
    notes_by_title = {note.title: note for note in notes}

    plain_note = notes_by_title.get("This is a plain note")
    if plain_note:
        assert plain_note.content is not None
        assert len(plain_note.content.strip()) > 0

    attachment_note = notes_by_title.get("This note has an attachment")
    if attachment_note:
        assert attachment_note.content is not None
        assert len(attachment_note.content.strip()) > 0


def test_macos14_backward_compatibility(macos_14_database):
    """Test that macOS 14 maintains compatibility with core functionality."""
    parser = AppleNotesParser(macos_14_database)

    # All core functionality should work regardless of version
    assert len(parser.accounts) >= 1
    assert len(parser.folders) >= 1
    assert len(parser.notes) >= 1

    # Search should work
    search_results = parser.search_notes("note")
    assert isinstance(search_results, list)

    # Export should work
    export_data = parser.export_notes_to_dict()
    assert "accounts" in export_data
    assert "folders" in export_data
    assert "notes" in export_data

    # Password protection detection should work
    protected_notes = parser.get_protected_notes()
    assert isinstance(protected_notes, list)

    # Attachment detection should work
    notes_with_attachments = parser.get_notes_with_attachments()
    assert isinstance(notes_with_attachments, list)


def test_macos14_enhanced_features(macos_14_database):
    """Test macOS 14 enhanced features compared to earlier versions."""
    parser = AppleNotesParser(macos_14_database)

    # macOS 14 has better attachment support than earlier versions
    all_attachments = parser.get_all_attachments()
    assert isinstance(all_attachments, list)
    assert len(all_attachments) >= 1

    # Should be able to filter by attachment type
    document_notes = parser.get_notes_by_attachment_type("document")
    assert isinstance(document_notes, list)

    # All attachments should have proper metadata
    for attachment in all_attachments:
        assert attachment.uuid is not None
        assert hasattr(attachment, "filename")
        assert hasattr(attachment, "file_size")
