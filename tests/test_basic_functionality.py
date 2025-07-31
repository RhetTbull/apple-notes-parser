"""
Basic pytest tests for apple-notes-parser functionality.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser import AppleNotesParser
from apple_notes_parser.database import AppleNotesDatabase
from apple_notes_parser.exceptions import AppleNotesParserError, DatabaseError
from apple_notes_parser.models import Account, Folder


class TestBasicFunctionality:
    """Test basic functionality of the apple-notes-parser."""

    def test_parser_initialization_with_nonexistent_file(self):
        """Test that parser raises error for nonexistent database file."""
        with pytest.raises(AppleNotesParserError, match="Database file not found"):
            AppleNotesParser("nonexistent.sqlite")

    def test_database_initialization_with_valid_file(self, real_database):
        """Test database initialization with valid file."""
        db = AppleNotesDatabase(real_database)
        assert db.database_path.exists()

    def test_account_loading(self, real_database):
        """Test loading accounts from database."""
        with AppleNotesDatabase(real_database) as db:
            accounts = db.get_accounts()
            assert len(accounts) >= 1
            # Find the "On My Mac" account
            on_my_mac = next((acc for acc in accounts if acc.name == "On My Mac"), None)
            assert on_my_mac is not None

    def test_folder_loading(self, real_database):
        """Test loading folders from database directly."""
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

    def test_ios_version_detection(self, real_database):
        """Test iOS version detection based on database schema."""
        with AppleNotesDatabase(real_database) as db:
            ios_version = db.get_ios_version()
            # Real macOS 15 database should detect as iOS 18
            assert ios_version == 18

    def test_z_uuid_extraction(self, real_database):
        """Test Z_UUID extraction from metadata table."""
        with AppleNotesDatabase(real_database) as db:
            z_uuid = db.get_z_uuid()
            assert z_uuid == "09FBEB4A-5B24-424E-814B-4AE8E757FB83"

    def test_folders_dict_property(self, real_database):
        """Test folders_dict property provides correct mapping."""
        with AppleNotesDatabase(real_database) as db:
            accounts_list = db.get_accounts()
            accounts_dict = {acc.id: acc for acc in accounts_list}
            folders_list = db.get_folders(accounts_dict)
            folders_dict = {folder.id: folder for folder in folders_list}

            assert len(folders_dict) == 6

            # Check that all folder IDs are mapped correctly
            for folder in folders_list:
                assert folder.id in folders_dict
                assert folders_dict[folder.id] == folder

    def test_export_structure(self, real_database):
        """Test that basic database structure can be read."""
        with AppleNotesDatabase(real_database) as db:
            accounts_list = db.get_accounts()
            folders_list = db.get_folders({acc.id: acc for acc in accounts_list})

            # Check accounts structure
            assert len(accounts_list) == 1
            account = accounts_list[0]
            assert hasattr(account, "id")
            assert hasattr(account, "name")
            assert hasattr(account, "identifier")

            # Check folders structure
            assert len(folders_list) == 6
            folder = folders_list[0]
            assert hasattr(folder, "id")
            assert hasattr(folder, "name")
            assert hasattr(folder, "parent_id")

            # Test folder path functionality
            folders_dict = {f.id: f for f in folders_list}
            paths = [f.get_path(folders_dict) for f in folders_list]
            assert len(paths) == 6
            assert any(
                "/" in path for path in paths
            )  # Some paths should have hierarchy

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


class TestErrorHandling:
    """Test error handling in the parser."""

    def test_database_error_propagation(self):
        """Test that database errors are properly propagated."""
        with pytest.raises((AppleNotesParserError, DatabaseError)):
            AppleNotesParser("/nonexistent/path/database.sqlite")

    def test_context_manager_cleanup(self, real_database):
        """Test that database context manager properly cleans up."""
        db = AppleNotesDatabase(real_database)

        # Should work in context manager
        with db:
            accounts = db.get_accounts()
            assert len(accounts) > 0

        # Connection should be closed after context manager
        assert db.connection is None
