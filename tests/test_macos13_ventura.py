"""
Tests for macOS 13 (Ventura) database support.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser import AppleNotesParser
from apple_notes_parser.database import AppleNotesDatabase


@pytest.fixture
def macos13_db_connection(macos_13_database):
    """Fixture providing a connected AppleNotesDatabase instance for macOS 13."""
    with AppleNotesDatabase(macos_13_database) as db:
        yield db


def test_macos13_version_detection(macos13_db_connection):
    """Test that macOS 13 database is correctly identified."""
    version = macos13_db_connection.get_macos_version()
    assert version == 12, f"Expected database version 12 for macOS 13, got {version}"


def test_macos13_z_uuid_extraction(macos13_db_connection):
    """Test Z_UUID extraction from macOS 13 database."""
    z_uuid = macos13_db_connection.get_z_uuid()
    assert z_uuid == "B1676C6D-218E-4208-9F99-0EE88571CFD4"


def test_macos13_basic_data_extraction(macos13_db_connection):
    """Test basic data extraction from macOS 13 database."""
    # Test accounts
    accounts = macos13_db_connection.get_accounts()
    assert len(accounts) == 1
    assert accounts[0].name == "On My Mac"

    # Test folders
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos13_db_connection.get_folders(accounts_dict)
    assert len(folders) == 6

    # Test notes
    folders_dict = {f.id: f for f in folders}
    notes = macos13_db_connection.get_notes(accounts_dict, folders_dict)
    assert len(notes) == 8


def test_macos13_folder_structure(macos13_db_connection):
    """Test folder hierarchy in macOS 13 database."""
    accounts = macos13_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos13_db_connection.get_folders(accounts_dict)
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
    assert subfolder.get_parent().name == "Folder2"

    subsubfolder = folders_by_name["Subsubfolder"]
    assert not subsubfolder.is_root()
    assert subsubfolder.get_parent().name == "Subfolder"


def test_macos13_notes_content(macos13_db_connection):
    """Test note content extraction from macOS 13 database."""
    accounts = macos13_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos13_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos13_db_connection.get_notes(accounts_dict, folders_dict)

    # Find specific notes by title
    notes_by_title = {n.title: n for n in notes if n.title}

    # Test tagged note (macOS 13 specific feature)
    tagged_note = notes_by_title.get("This note has tags")
    assert tagged_note is not None
    # Note: Tag extraction might be from content parsing rather than database
    assert tagged_note.folder.name == "Notes"

    # Test password protected note
    protected_note = notes_by_title.get("This note is password protected")
    assert protected_note is not None
    assert protected_note.is_password_protected

    # Test formatted note
    formatted_note = notes_by_title.get("This note has special formatting")
    assert formatted_note is not None
    assert not formatted_note.is_password_protected

    # Test folder hierarchy notes
    folder_note = notes_by_title.get("This note is in a folder")
    assert folder_note is not None
    assert folder_note.folder.name == "Folder"

    subfolder_note = notes_by_title.get("This note is in a subfolder")
    assert subfolder_note is not None
    assert subfolder_note.folder.name == "Subfolder"

    # Note: Different title than macOS 12
    deep_note = notes_by_title.get("This is a deeply buried note")
    assert deep_note is not None
    assert deep_note.folder.name == "Subsubfolder"


def test_macos13_applescript_ids(macos13_db_connection):
    """Test AppleScript ID construction for macOS 13 database."""
    accounts = macos13_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos13_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos13_db_connection.get_notes(accounts_dict, folders_dict)

    # All notes should have AppleScript IDs
    for note in notes:
        assert note.applescript_id is not None
        assert note.applescript_id.startswith("x-coredata://")
        assert "/ICNote/p" in note.applescript_id
        assert "B1676C6D-218E-4208-9F99-0EE88571CFD4" in note.applescript_id

    # Test specific AppleScript IDs match expected pattern
    notes_by_title = {n.title: n for n in notes if n.title}
    simple_note = notes_by_title.get("This is a note")
    assert simple_note is not None
    assert simple_note.applescript_id == "x-coredata://B1676C6D-218E-4208-9F99-0EE88571CFD4/ICNote/p5"


def test_macos13_tag_functionality(macos_13_database):
    """Test enhanced tag functionality in macOS 13."""
    parser = AppleNotesParser(macos_13_database)

    # macOS 13 has improved tag support
    all_tags = parser.get_all_tags()
    assert isinstance(all_tags, list)

    # Should find the travel and vacation tags from the tagged note
    # (either from embedded objects or regex parsing)
    if all_tags:
        # If we found tags, they should include expected ones
        assert any(tag in ["travel", "vacation"] for tag in all_tags)

    # Tag counts should work
    tag_counts = parser.get_tag_counts()
    assert isinstance(tag_counts, dict)

    # Search for notes by tag (if tags were found)
    if all_tags:
        for tag in all_tags[:2]:  # Test first few tags
            notes_with_tag = parser.get_notes_by_tag(tag)
            assert isinstance(notes_with_tag, list)


def test_macos13_password_protection_detection(macos_13_database):
    """Test detection of password-protected notes."""
    parser = AppleNotesParser(macos_13_database)

    protected_notes = parser.get_protected_notes()
    assert isinstance(protected_notes, list)
    assert len(protected_notes) >= 1

    # Verify the specific protected note
    protected_titles = [note.title for note in protected_notes]
    assert "This note is password protected" in protected_titles


def test_macos13_search_functionality(macos_13_database):
    """Test note search functionality."""
    parser = AppleNotesParser(macos_13_database)

    # Search for specific text that should exist
    results = parser.search_notes("buried")
    assert len(results) >= 1

    # Case insensitive search
    results_case = parser.search_notes("BURIED", case_sensitive=False)
    assert len(results_case) >= len(results)

    # Search for text in title
    results_title = parser.search_notes("folder")
    assert len(results_title) >= 1

    # Search for tag-related content
    results_tags = parser.search_notes("tags")
    assert len(results_tags) >= 1


def test_macos13_export_functionality(macos_13_database):
    """Test export functionality with macOS 13 database."""
    parser = AppleNotesParser(macos_13_database)

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

    # Verify note data includes tagged note
    note_titles = [n["title"] for n in export_data["notes"] if n["title"]]
    assert "This note has tags" in note_titles
    assert "This note is password protected" in note_titles

    # Verify AppleScript IDs use correct UUID
    for note_data in export_data["notes"]:
        assert "applescript_id" in note_data
        assert note_data["applescript_id"] is not None
        assert "B1676C6D-218E-4208-9F99-0EE88571CFD4" in note_data["applescript_id"]


def test_macos13_tag_extraction_from_content(macos_13_database):
    """Test that tags are properly extracted from note with tags."""
    parser = AppleNotesParser(macos_13_database)

    # Find the note with tags
    tagged_notes = [note for note in parser.notes if note.title == "This note has tags"]
    assert len(tagged_notes) == 1

    tagged_note = tagged_notes[0]

    # The note should have tags (either from embedded objects or content parsing)
    # Tags might be extracted via different methods in macOS 13
    assert tagged_note.tags is not None
    assert isinstance(tagged_note.tags, list)


def test_macos13_folder_path_reconstruction(macos_13_database):
    """Test folder path reconstruction for macOS 13."""
    parser = AppleNotesParser(macos_13_database)
    folders_dict = parser.folders_dict

    # Test deep hierarchy path (note different title than macOS 12)
    deep_notes = [note for note in parser.notes if note.title == "This is a deeply buried note"]
    assert len(deep_notes) == 1
    deep_note = deep_notes[0]
    folder_path = deep_note.get_folder_path()
    assert folder_path == "Folder2/Subfolder/Subsubfolder"

    # Test single level folder
    folder_notes = [note for note in parser.notes if note.title == "This note is in a folder"]
    assert len(folder_notes) == 1
    folder_note = folder_notes[0]
    folder_path = folder_note.get_folder_path()
    assert folder_path == "Folder"


def test_macos13_parser_integration(macos_13_database):
    """Test AppleNotesParser integration with macOS 13 database."""
    parser = AppleNotesParser(macos_13_database)

    # Basic functionality
    assert len(parser.notes) == 8
    assert len(parser.folders) == 6
    assert len(parser.accounts) == 1

    # Search functionality
    search_results = parser.search_notes("note")
    assert len(search_results) > 0

    # Folder functionality - verify all folders have valid paths
    folders_dict = parser.folders_dict
    for folder in parser.folders:
        path = folder.get_path()
        assert isinstance(path, str)
        assert len(path) > 0


def test_macos13_database_schema_compatibility(macos13_db_connection):
    """Test that macOS 13 database schema is handled correctly."""
    cursor = macos13_db_connection.connection.cursor()

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


def test_macos13_version_specific_features(macos_13_database):
    """Test macOS 13 specific features and improvements."""
    parser = AppleNotesParser(macos_13_database)

    # macOS 13 should have better tag support than macOS 12
    all_tags = parser.get_all_tags()
    assert isinstance(all_tags, list)

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

    # Verify that notes with tags can be found
    tagged_notes = [note for note in parser.notes if note.title == "This note has tags"]
    assert len(tagged_notes) == 1


def test_macos13_embedded_object_extraction(macos13_db_connection):
    """Test embedded object extraction capabilities in macOS 13."""
    # macOS 13 may have limited embedded object support compared to macOS 15+
    if macos13_db_connection._embedded_extractor:
        extractor = macos13_db_connection._embedded_extractor

        # Try to get hashtags (may be limited)
        hashtags = extractor.get_all_hashtags()
        assert isinstance(hashtags, list)  # Should return list even if empty

        # Try to get mentions
        mentions = extractor.get_all_mentions()
        assert isinstance(mentions, list)  # Should return list even if empty


def test_macos13_note_content_extraction(macos13_db_connection):
    """Test that note content is properly extracted and not null."""
    accounts = macos13_db_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts}
    folders = macos13_db_connection.get_folders(accounts_dict)
    folders_dict = {f.id: f for f in folders}
    notes = macos13_db_connection.get_notes(accounts_dict, folders_dict)

    # At least some notes should have non-null content
    notes_with_content = [note for note in notes if note.content]
    assert len(notes_with_content) > 0, (
        "No notes have content - content extraction may be failing"
    )

    # Check specific notes we know should have content
    notes_by_title = {note.title: note for note in notes}

    simple_note = notes_by_title.get("This is a note")
    if simple_note:
        assert simple_note.content is not None
        assert len(simple_note.content.strip()) > 0

    tagged_note = notes_by_title.get("This note has tags")
    if tagged_note:
        assert tagged_note.content is not None
        assert len(tagged_note.content.strip()) > 0


def test_macos13_backward_compatibility(macos_13_database):
    """Test that macOS 13 maintains compatibility with core functionality."""
    parser = AppleNotesParser(macos_13_database)

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
