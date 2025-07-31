"""
Pytest tests for folder hierarchy functionality without notes.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser.database import AppleNotesDatabase
from apple_notes_parser.models import Account, Folder


class TestFolderOnly:
    """Test folder functionality without requiring notes."""

    def test_account_loading(self, real_database):
        """Test loading accounts from database."""
        with AppleNotesDatabase(real_database) as db:
            accounts = db.get_accounts()
            assert len(accounts) == 1
            # Find the "On My Mac" account
            on_my_mac = next((acc for acc in accounts if acc.name == "On My Mac"), None)
            assert on_my_mac is not None

    def test_folder_loading(self, real_database):
        """Test loading folders from database."""
        with AppleNotesDatabase(real_database) as db:
            accounts_list = db.get_accounts()
            accounts_dict = {acc.id: acc for acc in accounts_list}
            folders_list = db.get_folders(accounts_dict)

            assert len(folders_list) == 6
            folder_names = {f.name for f in folders_list}
            expected_names = {
                "Notes",
                "Recently Deleted",
                "Folder",
                "Folder2",
                "Subfolder",
                "Subsubfolder",
            }
            assert folder_names == expected_names

    def test_folder_parent_extraction(self, real_database):
        """Test that folder parent IDs are extracted correctly."""
        with AppleNotesDatabase(real_database) as db:
            accounts_list = db.get_accounts()
            accounts_dict = {acc.id: acc for acc in accounts_list}
            folders_list = db.get_folders(accounts_dict)

            folders_by_name = {f.name: f for f in folders_list}

            # Root folder should have no parent
            assert folders_by_name["Notes"].parent_id is None
            assert folders_by_name["Notes"].is_root()

            # Folder2 should be a root folder (no parent)
            assert folders_by_name["Folder2"].parent_id is None
            assert folders_by_name["Folder2"].is_root()

            # Subfolder should have Folder2 as parent
            assert (
                folders_by_name["Subfolder"].parent_id == folders_by_name["Folder2"].id
            )
            assert not folders_by_name["Subfolder"].is_root()

    def test_folder_path_construction(self, real_database):
        """Test that folder paths are constructed correctly."""
        with AppleNotesDatabase(real_database) as db:
            accounts_list = db.get_accounts()
            accounts_dict = {acc.id: acc for acc in accounts_list}
            folders_list = db.get_folders(accounts_dict)
            folders_dict = {folder.id: folder for folder in folders_list}

            folders_by_name = {f.name: f for f in folders_list}

            # Test specific paths
            expected_paths = {
                "Notes": "Notes",
                "Folder": "Folder",
                "Folder2": "Folder2",
                "Subfolder": "Folder2/Subfolder",
                "Subsubfolder": "Folder2/Subfolder/Subsubfolder",
            }

            for name, expected_path in expected_paths.items():
                actual_path = folders_by_name[name].get_path(folders_dict)
                assert actual_path == expected_path, (
                    f"Expected {expected_path}, got {actual_path}"
                )

    def test_folder_parent_navigation(self, real_database):
        """Test folder parent navigation methods."""
        with AppleNotesDatabase(real_database) as db:
            accounts_list = db.get_accounts()
            accounts_dict = {acc.id: acc for acc in accounts_list}
            folders_list = db.get_folders(accounts_dict)
            folders_dict = {folder.id: folder for folder in folders_list}

            folders_by_name = {f.name: f for f in folders_list}

            # Test parent navigation with real folder hierarchy
            subsubfolder = folders_by_name["Subsubfolder"]
            subfolder = subsubfolder.get_parent(folders_dict)
            assert subfolder.name == "Subfolder"

            folder2 = subfolder.get_parent(folders_dict)
            assert folder2.name == "Folder2"

            # Folder2 is a root folder, should have no parent
            assert folder2.get_parent(folders_dict) is None

    def test_macos_version_detection(self, real_database):
        """Test macOS version detection based on database schema."""
        with AppleNotesDatabase(real_database) as db:
            macos_version = db.get_macos_version()
            # Real macOS 15 database should detect as macOS 15
            assert macos_version == 15

    def test_z_uuid_extraction(self, real_database):
        """Test Z_UUID extraction from metadata table."""
        with AppleNotesDatabase(real_database) as db:
            z_uuid = db.get_z_uuid()
            assert z_uuid == "09FBEB4A-5B24-424E-814B-4AE8E757FB83"

    def test_folder_path_without_dict(self, real_database):
        """Test folder path fallback when no folders_dict is provided."""
        with AppleNotesDatabase(real_database) as db:
            accounts_list = db.get_accounts()
            accounts_dict = {acc.id: acc for acc in accounts_list}
            folders_list = db.get_folders(accounts_dict)

            folders_by_name = {f.name: f for f in folders_list}

            # Without folders_dict, should just return the folder name
            assert folders_by_name["Subsubfolder"].get_path(None) == "Subsubfolder"
            assert folders_by_name["Folder2"].get_path(None) == "Folder2"

    def test_root_folder_detection(self, real_database):
        """Test detection of root folders."""
        with AppleNotesDatabase(real_database) as db:
            accounts_list = db.get_accounts()
            accounts_dict = {acc.id: acc for acc in accounts_list}
            folders_list = db.get_folders(accounts_dict)

            root_folders = [f for f in folders_list if f.is_root()]
            # Should have multiple root folders: Notes, Recently Deleted, Folder, Folder2
            assert len(root_folders) == 4
            root_names = {f.name for f in root_folders}
            expected_root_names = {"Notes", "Recently Deleted", "Folder", "Folder2"}
            assert root_names == expected_root_names

    def test_folder_model_methods(self):
        """Test Folder model methods."""
        # Create mock account
        account = Account(id=1, name="Test", identifier="test")

        # Create test folders
        root_folder = Folder(id=1, name="Root", account=account, parent_id=None)
        child_folder = Folder(id=2, name="Child", account=account, parent_id=1)

        # Test is_root method
        assert root_folder.is_root()
        assert not child_folder.is_root()

        # Test get_parent method
        folders_dict = {1: root_folder, 2: child_folder}
        assert child_folder.get_parent(folders_dict) == root_folder
        assert root_folder.get_parent(folders_dict) is None

        # Test get_path method
        assert root_folder.get_path(folders_dict) == "Root"
        assert child_folder.get_path(folders_dict) == "Root/Child"

    def test_cycle_prevention(self, real_database):
        """Test that cycle detection prevents infinite loops."""
        with AppleNotesDatabase(real_database) as db:
            accounts_list = db.get_accounts()
            accounts_dict = {acc.id: acc for acc in accounts_list}
            folders_list = db.get_folders(accounts_dict)
            folders_dict = {folder.id: folder for folder in folders_list}

            # Artificially create a cycle by making Notes point to itself
            notes_folder = next(f for f in folders_list if f.name == "Notes")
            notes_folder.parent_id = notes_folder.id  # Create cycle

            # Should not cause infinite loop, just return the folder name
            path = notes_folder.get_path(folders_dict)
            assert path == "Notes"


class TestErrorHandling:
    """Test error handling."""

    def real_database_initialization_with_valid_file(self, real_database):
        """Test database initialization with valid file."""
        db = AppleNotesDatabase(real_database)
        assert db.database_path.exists()

    def test_context_manager_cleanup(self, real_database):
        """Test that database context manager properly cleans up."""
        db = AppleNotesDatabase(real_database)

        # Should work in context manager
        with db:
            accounts = db.get_accounts()
            assert len(accounts) > 0

        # Connection should be closed after context manager
        assert db.connection is None
