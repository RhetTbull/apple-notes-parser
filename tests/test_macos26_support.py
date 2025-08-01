"""
Tests for iOS 19 / macOS 26 Tahoe database support.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser import AppleNotesParser
from apple_notes_parser.database import AppleNotesDatabase


@pytest.fixture
def macos26_database():
    """Fixture providing path to the macOS 26 database."""
    database_path = (
        Path(__file__).parent / "data" / "NoteStore-macOS-26-Tahoe.sqlite"
    )
    if not database_path.exists():
        pytest.skip(f"macOS 26 database not found at {database_path}")
    return str(database_path)


@pytest.fixture
def macos26_db_connection(macos26_database):
    """Fixture providing a connected AppleNotesDatabase instance for macOS 26."""
    with AppleNotesDatabase(macos26_database) as db:
        yield db

def test_macos26_version_detection(macos26_db_connection):
    """Test that macOS 26 database is correctly identified."""
    version = macos26_db_connection.get_macos_version()
    assert version == 26, f"Expected macOS 26, got {version}"


def test_macos26_z_uuid_extraction(macos26_db_connection):
    """Test Z_UUID extraction from macOS 26 database."""
    z_uuid = macos26_db_connection.get_z_uuid()
    assert z_uuid == "9B3F80E8-BEEE-4921-BE3B-57B7D6FFAF2E"


def test_macos26_basic_data_extraction(macos26_db_connection):
    """Test basic data extraction from macOS 26 database."""
    # Test accounts
    accounts = macos26_db_connection.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].name == "On My Mac"

    # Test folders
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos26_db_connection.get_folders(accounts_dict)
    assert len(folders) == 6

    # Test notes
    folders_dict = {f.id: f for f in folders}
    notes = macos26_db_connection.get_notes(accounts_dict, folders_dict)
    assert len(notes) == 8

def test_macos26_folder_structure(macos26_db_connection):
    """Test folder hierarchy in macOS 26 database."""
    accounts = macos26_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos26_db_connection.get_folders(accounts_dict)
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
    assert folders_by_name["Folder"].is_root()
    assert folders_by_name["Folder2"].is_root()

    # Test nested folders
    subfolder = folders_by_name["Subfolder"]
    assert not subfolder.is_root()
    assert subfolder.get_parent().name == "Folder2"

    subsubfolder = folders_by_name["Subsubfolder"]
    assert not subsubfolder.is_root()
    assert subsubfolder.get_parent().name == "Subfolder"

def test_macos26_notes_content(macos26_db_connection):
    """Test note content extraction from macOS 26 database."""
    accounts = macos26_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos26_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos26_db_connection.get_notes(accounts_dict, folders_dict)

    # Find specific notes by title
    notes_by_title = {n.title: n for n in notes if n.title}

    # Test tagged note
    tagged_note = notes_by_title.get("This note has tags")
    assert tagged_note is not None
    assert "travel" in tagged_note.tags
    assert "vacation" in tagged_note.tags

    # Test password protected note
    protected_note = notes_by_title.get("This note is password protected")
    assert protected_note is not None
    assert protected_note.is_password_protected

    # Test formatted note
    formatted_note = notes_by_title.get("This note has special formatting")
    assert formatted_note is not None
    assert not formatted_note.is_password_protected

def test_macos26_applescript_ids(macos26_db_connection):
    """Test AppleScript ID construction for macOS 26 database."""
    accounts = macos26_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos26_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos26_db_connection.get_notes(accounts_dict, folders_dict)

    # All notes should have AppleScript IDs
    for note in notes:
        assert note.applescript_id is not None
        assert note.applescript_id.startswith("x-coredata://")
        assert "/ICNote/p" in note.applescript_id

def test_macos26_parser_integration(macos26_database):
    """Test AppleNotesParser integration with macOS 26 database."""
    parser = AppleNotesParser(macos26_database)

    # Basic functionality
    assert len(parser.notes) == 8
    assert len(parser.folders) == 6
    assert len(parser.accounts) == 1

    # Search functionality
    search_results = parser.search_notes("note")
    assert len(search_results) > 0

    # Tag functionality
    all_tags = parser.get_all_tags()
    assert "travel" in all_tags
    assert "vacation" in all_tags

    # Folder functionality
    folders_dict = parser.folders_dict
    for folder in parser.folders:
        path = folder.get_path()
        assert isinstance(path, str)
        assert len(path) > 0

def test_macos26_export_functionality(macos26_database):
    """Test export functionality with macOS 26 database."""
    parser = AppleNotesParser(macos26_database)

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

    # Verify note data
    note_titles = [n["title"] for n in export_data["notes"] if n["title"]]
    assert "This note has tags" in note_titles
    assert "This note is password protected" in note_titles

def test_macos26_deleted_folder_exclusion(macos26_db_connection):
    """Test that deleted folders are properly excluded in macOS 26 database."""
    accounts = macos26_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos26_db_connection.get_folders(accounts_dict)

    # Query database directly to verify filtering
    cursor = macos26_db_connection.connection.cursor()

    # Count all folders (including deleted)
    cursor.execute("""
        SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTITLE2 IS NOT NULL
    """)
    # Count non-deleted folders (what our method should return)
    cursor.execute("""
        SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTITLE2 IS NOT NULL AND ZMARKEDFORDELETION = 0
    """)
    non_deleted_folders = cursor.fetchone()[0]

    # Our method should return the same count as non-deleted folders
    assert len(folders) == non_deleted_folders

def test_macos26_schema_features(macos26_db_connection):
    """Test macOS 26 specific schema features."""
    cursor = macos26_db_connection.connection.cursor()

    # Check for macOS 26 specific column
    cursor.execute("PRAGMA table_info(ZICCLOUDSYNCINGOBJECT)")
    columns = [row[1] for row in cursor.fetchall()]

    # macOS 26 should have the new column
    assert "ZNEEDSTOFETCHUSERSPECIFICRECORDASSETS" in columns

    # macOS 26 should also retain earlier columns
    assert "ZUNAPPLIEDENCRYPTEDRECORDDATA" in columns

    # Check for new table
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='ZICASSETSIGNATURE'
    """)
    result = cursor.fetchone()
    assert result is not None, "ZICASSETSIGNATURE table should exist in macOS 26"


def test_version_detection_difference():
    """Test that macOS 15 and macOS 26 databases are correctly distinguished."""
    # Test macOS 15 (Sequoia) database
    with AppleNotesDatabase("tests/data/NoteStore-macOS-15-Seqoia.sqlite") as db15:
        version15 = db15.get_macos_version()
        assert version15 == 15

    # Test macOS 26 (Tahoe) database
    with AppleNotesDatabase("tests/data/NoteStore-macOS-26-Tahoe.sqlite") as db26:
        version26 = db26.get_macos_version()
        assert version26 == 26


def test_backward_compatibility():
    """Test that existing functionality works with both versions."""
    # Test both databases with same operations
    for db_path, _expected_version in [
        ("tests/data/NoteStore-macOS-15-Seqoia.sqlite", 15),
        ("tests/data/NoteStore-macOS-26-Tahoe.sqlite", 26),
    ]:
        parser = AppleNotesParser(db_path)

        # Basic functionality should work with both
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
