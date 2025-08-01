"""
Version-agnostic tests that work across different database versions.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser import AppleNotesParser
from apple_notes_parser.database import AppleNotesDatabase


def test_database_version_detection(versioned_database, version_metadata):
    """Test that database version is correctly detected."""
    with AppleNotesDatabase(versioned_database) as db:
        macos_version = db.get_macos_version()
        assert macos_version == version_metadata["macos_version"]


def test_z_uuid_extraction(versioned_database, version_metadata):
    """Test Z_UUID extraction works for all versions."""
    with AppleNotesDatabase(versioned_database) as db:
        z_uuid = db.get_z_uuid()
        assert z_uuid == version_metadata["z_uuid"]


def test_basic_data_loading(versioned_database, version_metadata):
    """Test basic data loading works for all versions."""
    with AppleNotesDatabase(versioned_database) as db:
        # Load accounts
        accounts = db.get_accounts()
        assert len(accounts) >= 1

        # Find expected account
        expected_account = next(
            (
                acc
                for acc in accounts
                if acc.name == version_metadata["account_name"]
            ),
            None,
        )
        assert expected_account is not None

        # Load folders
        accounts_dict = {acc.id: acc for acc in accounts}
        folders = db.get_folders(accounts_dict)
        assert len(folders) == version_metadata["total_folders"]

        # Load notes
        folders_dict = {folder.id: folder for folder in folders}
        notes = db.get_notes(accounts_dict, folders_dict)
        assert len(notes) == version_metadata["total_notes"]

def test_folder_hierarchy_structure(versioned_database, version_metadata):
    """Test folder hierarchy structure is correctly parsed."""
    with AppleNotesDatabase(versioned_database) as db:
        accounts_list = db.get_accounts()
        accounts_dict = {acc.id: acc for acc in accounts_list}
        folders_list = db.get_folders(accounts_dict)
        folders_dict = {folder.id: folder for folder in folders_list}

        folders_by_name = {f.name: f for f in folders_list}

        # Test expected folder structure
        expected_folders = version_metadata["expected_folders"]
        for folder_name, folder_info in expected_folders.items():
            folder = folders_by_name.get(folder_name)
            assert folder is not None, f"Folder '{folder_name}' not found"

            # Check path construction
            actual_path = folder.get_path()
            expected_path = folder_info["path"]
            assert actual_path == expected_path, (
                f"Expected path '{expected_path}', got '{actual_path}'"
            )

            # Check parent relationship
            if folder_info["parent"] is None:
                assert folder.is_root()
                assert folder.parent_id is None
            else:
                assert not folder.is_root()
                parent_folder = folder.get_parent()
                assert parent_folder is not None
                assert parent_folder.name == folder_info["parent"]

def test_applescript_id_construction(versioned_database, version_metadata):
    """Test AppleScript ID construction works for all versions."""
    with AppleNotesDatabase(versioned_database) as db:
        accounts_list = db.get_accounts()
        accounts_dict = {acc.id: acc for acc in accounts_list}
        folders_list = db.get_folders(accounts_dict)
        folders_dict = {folder.id: folder for folder in folders_list}
        notes_list = db.get_notes(accounts_dict, folders_dict)

        # All notes should have AppleScript IDs
        for note in notes_list:
            assert note.applescript_id is not None
            assert version_metadata["z_uuid"] in note.applescript_id
            assert note.applescript_id.startswith("x-coredata://")
            assert "/ICNote/p" in note.applescript_id

def test_password_protection_detection(versioned_database, version_metadata):
    """Test password protection detection works across versions."""
    parser = AppleNotesParser(versioned_database)

    protected_notes = parser.get_protected_notes()
    assert isinstance(protected_notes, list)

    # Check expected protected notes
    expected_protected = version_metadata.get("protected_notes", [])
    if expected_protected:
        protected_titles = [note.title for note in protected_notes]
        for expected_title in expected_protected:
            assert expected_title in protected_titles

def test_export_functionality(versioned_database, version_metadata):
    """Test data export works across versions."""
    parser = AppleNotesParser(versioned_database)

    export_data = parser.export_notes_to_dict(include_content=True)

    # Verify basic structure
    assert "accounts" in export_data
    assert "folders" in export_data
    assert "notes" in export_data

    # Verify counts match expectations
    assert len(export_data["accounts"]) >= 1
    assert len(export_data["folders"]) == version_metadata["total_folders"]
    assert len(export_data["notes"]) == version_metadata["total_notes"]

    # Verify all notes have AppleScript IDs
    for note_data in export_data["notes"]:
        assert "applescript_id" in note_data
        assert note_data["applescript_id"] is not None
        assert version_metadata["z_uuid"] in note_data["applescript_id"]

    # Verify all folders have paths
    for folder_data in export_data["folders"]:
        assert "path" in folder_data
        assert folder_data["path"] is not None


def test_version_fixture_extensibility():
    """Demonstrate how version metadata can be extended for new versions."""
    # Future macOS/iOS versions would add entries like:
    example_future_metadata = {
        "version": "macOS 16",
        "ios_version": 18,
        "z_uuid": "EXAMPLE-UUID-FOR-FUTURE-VERSION",
        "total_notes": 10,
        "total_folders": 8,
        "account_name": "On My Mac",
        "expected_folders": {
            "Notes": {"parent": None, "path": "Notes"},
            # ... additional folders for new version
        },
        "new_features": {
            "supports_ai_summaries": True,
            "supports_advanced_search": True,
        },
    }

    # Test that the structure is extensible
    assert "version" in example_future_metadata
    assert "ios_version" in example_future_metadata
    assert "expected_folders" in example_future_metadata

    # Future tests could check new features
    if example_future_metadata.get("new_features", {}).get("supports_ai_summaries"):
        # Test AI summary functionality
        pass


def test_parameter_expansion_example():
    """Show how versioned_database fixture can be expanded."""
    # The versioned_database fixture in conftest.py can be updated like:
    # @pytest.fixture(params=["macos_15", "macos_16", "ios_17"])
    # def versioned_database(request):
    #     if request.param == "macos_15":
    #         return path_to_macos_15_db
    #     elif request.param == "macos_16":
    #         return path_to_macos_16_db
    #     elif request.param == "ios_17":
    #         return path_to_ios_17_db

    # This ensures all version-agnostic tests run against all versions
    assert True  # Placeholder for documentation
