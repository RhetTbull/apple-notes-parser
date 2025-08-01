"""
Tests for macOS 12 (Monterey) database support.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser import AppleNotesParser
from apple_notes_parser.database import AppleNotesDatabase


@pytest.fixture
def macos12_db_connection(macos_12_database):
    """Fixture providing a connected AppleNotesDatabase instance for macOS 12."""
    with AppleNotesDatabase(macos_12_database) as db:
        yield db


def test_macos12_version_detection(macos12_db_connection):
    """Test that macOS 12 database is correctly identified."""
    version = macos12_db_connection.get_macos_version()
    assert version == 11, f"Expected database version 11 for macOS 12, got {version}"


def test_macos12_z_uuid_extraction(macos12_db_connection):
    """Test Z_UUID extraction from macOS 12 database."""
    z_uuid = macos12_db_connection.get_z_uuid()
    assert z_uuid == "FABDAB03-8EF2-41B9-9944-193D67BE0365"


def test_macos12_basic_data_extraction(macos12_db_connection):
    """Test basic data extraction from macOS 12 database."""
    # Test accounts
    accounts = macos12_db_connection.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].name == "On My Mac"

    # Test folders
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos12_db_connection.get_folders(accounts_dict)
    assert len(folders) == 6

    # Test notes
    folders_dict = {f.id: f for f in folders}
    notes = macos12_db_connection.get_notes(accounts_dict, folders_dict)
    assert len(notes) == 7


def test_macos12_folder_structure(macos12_db_connection):
    """Test folder hierarchy in macOS 12 database."""
    accounts = macos12_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos12_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}

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
    assert subfolder.get_parent(folders_dict).name == "Folder2"

    subsubfolder = folders_by_name["Subsubfolder"]
    assert not subsubfolder.is_root()
    assert subsubfolder.get_parent(folders_dict).name == "Subfolder"


def test_macos12_notes_content(macos12_db_connection):
    """Test note content extraction from macOS 12 database."""
    accounts = macos12_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos12_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos12_db_connection.get_notes(accounts_dict, folders_dict)

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

    # Test deleted note (macOS 12 specific)
    deleted_note = notes_by_title.get("This note is deleted")
    assert deleted_note is not None
    assert deleted_note.folder.name == "Recently Deleted"
    assert not deleted_note.is_password_protected

    # Test folder hierarchy notes
    folder_note = notes_by_title.get("This note is in a folder")
    assert folder_note is not None
    assert folder_note.folder.name == "Folder"

    subfolder_note = notes_by_title.get("This note is in a subfolder")
    assert subfolder_note is not None
    assert subfolder_note.folder.name == "Subfolder"

    deep_note = notes_by_title.get("This note is deeply buried")
    assert deep_note is not None
    assert deep_note.folder.name == "Subsubfolder"


def test_macos12_applescript_ids(macos12_db_connection):
    """Test AppleScript ID construction for macOS 12 database."""
    accounts = macos12_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos12_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos12_db_connection.get_notes(accounts_dict, folders_dict)

    # All notes should have AppleScript IDs
    for note in notes:
        assert note.applescript_id is not None
        assert note.applescript_id.startswith("x-coredata://")
        assert "/ICNote/p" in note.applescript_id
        assert "FABDAB03-8EF2-41B9-9944-193D67BE0365" in note.applescript_id

    # Test specific AppleScript IDs match expected pattern
    notes_by_title = {n.title: n for n in notes if n.title}
    simple_note = notes_by_title.get("This is a note")
    assert simple_note is not None
    assert simple_note.applescript_id == "x-coredata://FABDAB03-8EF2-41B9-9944-193D67BE0365/ICNote/p5"


def test_macos12_tag_functionality(macos_12_database):
    """Test tag functionality (should be limited in macOS 12)."""
    parser = AppleNotesParser(macos_12_database)

    # macOS 12 has limited tag support - most tags come from regex parsing
    all_tags = parser.get_all_tags()
    # Should return a list (may be empty)
    assert isinstance(all_tags, list)

    # Tag counts should work
    tag_counts = parser.get_tag_counts()
    assert isinstance(tag_counts, dict)


def test_macos12_password_protection_detection(macos_12_database):
    """Test detection of password-protected notes."""
    parser = AppleNotesParser(macos_12_database)

    protected_notes = parser.get_protected_notes()
    assert isinstance(protected_notes, list)
    assert len(protected_notes) >= 1

    # Verify the specific protected note
    protected_titles = [note.title for note in protected_notes]
    assert "This note is password protected" in protected_titles


def test_macos12_search_functionality(macos_12_database):
    """Test note search functionality."""
    parser = AppleNotesParser(macos_12_database)

    # Search for specific text that should exist
    results = parser.search_notes("buried")
    assert len(results) >= 1

    # Case insensitive search
    results_case = parser.search_notes("BURIED", case_sensitive=False)
    assert len(results_case) >= len(results)

    # Search for text in title
    results_title = parser.search_notes("folder")
    assert len(results_title) >= 1


def test_macos12_export_functionality(macos_12_database):
    """Test export functionality with macOS 12 database."""
    parser = AppleNotesParser(macos_12_database)

    # Test export to dict
    export_data = parser.export_notes_to_dict(include_content=True)

    assert "accounts" in export_data
    assert "folders" in export_data
    assert "notes" in export_data

    assert len(export_data["accounts"]) == 1
    assert len(export_data["folders"]) == 6
    assert len(export_data["notes"]) == 7

    # Verify account data
    account = export_data["accounts"][0]
    assert account["name"] == "On My Mac"

    # Verify folder data includes "Recently Deleted"
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

    # Verify note data includes deleted note
    note_titles = [n["title"] for n in export_data["notes"] if n["title"]]
    assert "This note is deleted" in note_titles
    assert "This note is password protected" in note_titles

    # Verify AppleScript IDs use correct UUID
    for note_data in export_data["notes"]:
        assert "applescript_id" in note_data
        assert note_data["applescript_id"] is not None
        assert "FABDAB03-8EF2-41B9-9944-193D67BE0365" in note_data["applescript_id"]


def test_macos12_deleted_notes_support(macos_12_database):
    """Test that macOS 12 properly handles deleted notes."""
    parser = AppleNotesParser(macos_12_database)

    # Find the recently deleted folder
    recently_deleted_folder = None
    for folder in parser.folders:
        if folder.name == "Recently Deleted":
            recently_deleted_folder = folder
            break

    assert recently_deleted_folder is not None, "Recently Deleted folder should exist in macOS 12"

    # Find notes in recently deleted folder
    deleted_notes = [note for note in parser.notes if note.folder.name == "Recently Deleted"]
    assert len(deleted_notes) >= 1, "Should have at least one deleted note"

    # Verify deleted note properties
    deleted_note = deleted_notes[0]
    assert deleted_note.title == "This note is deleted"
    assert not deleted_note.is_password_protected


def test_macos12_folder_path_reconstruction(macos_12_database):
    """Test folder path reconstruction for macOS 12."""
    parser = AppleNotesParser(macos_12_database)
    folders_dict = parser.folders_dict

    # Test deep hierarchy path
    deep_notes = [note for note in parser.notes if note.title == "This note is deeply buried"]
    assert len(deep_notes) == 1
    deep_note = deep_notes[0]
    folder_path = deep_note.get_folder_path(folders_dict)
    assert folder_path == "Folder2/Subfolder/Subsubfolder"

    # Test single level folder
    folder_notes = [note for note in parser.notes if note.title == "This note is in a folder"]
    assert len(folder_notes) == 1
    folder_note = folder_notes[0]
    folder_path = folder_note.get_folder_path(folders_dict)
    assert folder_path == "Folder"


def test_macos12_parser_integration(macos_12_database):
    """Test AppleNotesParser integration with macOS 12 database."""
    parser = AppleNotesParser(macos_12_database)

    # Basic functionality
    assert len(parser.notes) == 7
    assert len(parser.folders) == 6
    assert len(parser.accounts) == 1

    # Search functionality
    search_results = parser.search_notes("note")
    assert len(search_results) > 0

    # Folder functionality - verify all folders have valid paths
    folders_dict = parser.folders_dict
    for folder in parser.folders:
        path = folder.get_path(folders_dict)
        assert isinstance(path, str)
        assert len(path) > 0


def test_macos12_database_schema_compatibility(macos12_db_connection):
    """Test that macOS 12 database schema is handled correctly."""
    cursor = macos12_db_connection.connection.cursor()

    # Check that we can query basic tables
    cursor.execute("SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT WHERE ZTITLE2 IS NOT NULL")
    folder_count = cursor.fetchone()[0]
    assert folder_count >= 6

    cursor.execute("SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT WHERE ZTITLE1 IS NOT NULL")
    note_count = cursor.fetchone()[0]
    assert note_count >= 7

    # Verify database structure
    cursor.execute("PRAGMA table_info(ZICCLOUDSYNCINGOBJECT)")
    columns = [row[1] for row in cursor.fetchall()]

    # Basic columns should exist
    assert "ZTITLE1" in columns   # Note titles
    assert "ZTITLE2" in columns   # Folder titles
    assert "ZNOTEDATA" in columns # Note content


def test_macos12_version_specific_features(macos_12_database):
    """Test macOS 12 specific features and limitations."""
    parser = AppleNotesParser(macos_12_database)

    # macOS 12 has basic functionality but limited embedded object support
    # Tags are mainly extracted via regex from note content
    all_tags = parser.get_all_tags()
    assert isinstance(all_tags, list)  # Should work but may be empty

    # Password protection should work
    protected_notes = parser.get_protected_notes()
    assert len(protected_notes) >= 1

    # Recently deleted folder should be available
    folder_names = {folder.name for folder in parser.folders}
    assert "Recently Deleted" in folder_names

    # All basic parser operations should work
    export_data = parser.export_notes_to_dict()
    assert len(export_data["notes"]) == 7
    assert len(export_data["folders"]) == 6
    assert len(export_data["accounts"]) == 1
