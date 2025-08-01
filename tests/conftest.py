"""
Pytest fixtures for Apple Notes Parser tests.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser.database import AppleNotesDatabase


@pytest.fixture
def test_database():
    """Fixture providing path to the test macOS 15 NoteStore database."""
    database_path = Path(__file__).parent / "data" / "NoteStore-macOS-15-Seqoia.sqlite"
    if not database_path.exists():
        pytest.skip(f"Real database not found at {database_path}")
    return str(database_path)


@pytest.fixture
def database_with_connection(test_database):
    """Fixture providing a connected AppleNotesDatabase instance."""
    with AppleNotesDatabase(test_database) as db:
        yield db


@pytest.fixture
def sample_notes_data():
    """Fixture providing expected note data from the real database."""
    return {
        # Note with tags
        "tagged_note": {
            "title": "This note has tags",
            "folder": "Notes",
            "tags": ["travel", "vacation"],
            "password_protected": False,
            "applescript_id": "x-coredata://09FBEB4A-5B24-424E-814B-4AE8E757FB83/ICNote/p6",
        },
        # Note with attachment
        "attachment_note": {
            "title": "This note has an attachment",
            "folder": "Notes",
            "password_protected": False,
            "applescript_id": "x-coredata://09FBEB4A-5B24-424E-814B-4AE8E757FB83/ICNote/p13",
        },
        # Password protected note
        "protected_note": {
            "title": "This note is password protected",
            "folder": "Notes",
            "password_protected": True,
            "applescript_id": "x-coredata://09FBEB4A-5B24-424E-814B-4AE8E757FB83/ICNote/p24",
        },
        # Note with formatting
        "formatted_note": {
            "title": "This note has special formatting",
            "folder": "Notes",
            "password_protected": False,
            "applescript_id": "x-coredata://09FBEB4A-5B24-424E-814B-4AE8E757FB83/ICNote/p11",
        },
        # Note in subfolder
        "subfolder_note": {
            "title": "This note is in a subfolder",
            "folder": "Subfolder",
            "password_protected": False,
            "applescript_id": "x-coredata://09FBEB4A-5B24-424E-814B-4AE8E757FB83/ICNote/p29",
        },
        # Note in deep subfolder
        "deep_subfolder_note": {
            "title": "This note is deeply buried",
            "folder": "Subsubfolder",
            "password_protected": False,
            "applescript_id": "x-coredata://09FBEB4A-5B24-424E-814B-4AE8E757FB83/ICNote/p31",
        },
        # Note in top-level folder
        "folder_note": {
            "title": "This note is in Folder",
            "folder": "Folder",
            "password_protected": False,
            "applescript_id": "x-coredata://09FBEB4A-5B24-424E-814B-4AE8E757FB83/ICNote/p26",
        },
        # Simple note in root
        "simple_note": {
            "title": "This is a note",
            "folder": "Notes",
            "password_protected": False,
            "applescript_id": "x-coredata://09FBEB4A-5B24-424E-814B-4AE8E757FB83/ICNote/p5",
        },
    }


@pytest.fixture
def sample_folders_data():
    """Fixture providing expected folder hierarchy from the real database."""
    return {
        "expected_folders": [
            {"name": "Notes", "parent": None, "path": "Notes"},
            {"name": "Recently Deleted", "parent": None, "path": "Recently Deleted"},
            {"name": "Folder", "parent": None, "path": "Folder"},
            {"name": "Folder2", "parent": None, "path": "Folder2"},
            {"name": "Subfolder", "parent": "Folder2", "path": "Folder2/Subfolder"},
            {
                "name": "Subsubfolder",
                "parent": "Subfolder",
                "path": "Folder2/Subfolder/Subsubfolder",
            },
        ],
        "total_count": 6,
    }


@pytest.fixture
def database_metadata():
    """Fixture providing expected database metadata."""
    return {
        "z_uuid": "09FBEB4A-5B24-424E-814B-4AE8E757FB83",
        "macos_version": 15,  # macOS 15 (Sequoia)
        "total_notes": 9,
        "total_folders": 6,
        "account_name": "On My Mac",
    }


@pytest.fixture
def macos_12_database():
    """Fixture providing path to the macOS 12 NoteStore database."""
    database_path = Path(__file__).parent / "data" / "NoteStore-macOS-12-Monterey.sqlite"
    if not database_path.exists():
        pytest.skip(f"macOS 12 database not found at {database_path}")
    return str(database_path)


@pytest.fixture
def macos_13_database():
    """Fixture providing path to the macOS 13 NoteStore database."""
    database_path = Path(__file__).parent / "data" / "NoteStore-macOS-13-Ventura.sqlite"
    if not database_path.exists():
        pytest.skip(f"macOS 13 database not found at {database_path}")
    return str(database_path)


@pytest.fixture
def macos_15_database():
    """Fixture providing path to the macOS 15 NoteStore database."""
    return test_database()


@pytest.fixture(params=["macos_12_monterey", "macos_13_ventura", "macos_15_sequoia", "macos_26_tahoe"])
def versioned_database(request):
    """Parameterized fixture for testing across different database versions."""
    if request.param == "macos_12_monterey":
        database_path = (
            Path(__file__).parent / "data" / "NoteStore-macOS-12-Monterey.sqlite"
        )
        if not database_path.exists():
            pytest.skip(f"macOS 12 (Monterey) database not found at {database_path}")
        return str(database_path)
    elif request.param == "macos_13_ventura":
        database_path = (
            Path(__file__).parent / "data" / "NoteStore-macOS-13-Ventura.sqlite"
        )
        if not database_path.exists():
            pytest.skip(f"macOS 13 (Ventura) database not found at {database_path}")
        return str(database_path)
    elif request.param == "macos_15_sequoia":
        database_path = (
            Path(__file__).parent / "data" / "NoteStore-macOS-15-Seqoia.sqlite"
        )
        if not database_path.exists():
            pytest.skip(f"macOS 15 (Sequoia) database not found at {database_path}")
        return str(database_path)
    elif request.param == "macos_26_tahoe":
        database_path = (
            Path(__file__).parent / "data" / "NoteStore-macOS-26-Tahoe.sqlite"
        )
        if not database_path.exists():
            pytest.skip(f"macOS 26 (Tahoe) database not found at {database_path}")
        return str(database_path)
    else:
        pytest.skip(f"Database version {request.param} not available")


@pytest.fixture
def version_metadata(versioned_database):
    """Fixture providing version-specific metadata for the current database."""
    # Determine version from database path
    db_path = Path(versioned_database)

    if "macOS-12" in db_path.name:
        return {
            "version": "macOS 12 (Monterey)",
            "macos_version": 11,  # Database version detection returns 11 for macOS 12
            "z_uuid": "FABDAB03-8EF2-41B9-9944-193D67BE0365",
            "total_notes": 7,
            "total_folders": 6,
            "account_name": "On My Mac",
            "expected_folders": {
                "Notes": {"parent": None, "path": "Notes"},
                "Recently Deleted": {"parent": None, "path": "Recently Deleted"},
                "Folder": {"parent": None, "path": "Folder"},  # Top-level folder
                "Folder2": {"parent": None, "path": "Folder2"},  # Top-level folder
                "Subfolder": {"parent": "Folder2", "path": "Folder2/Subfolder"},
                "Subsubfolder": {
                    "parent": "Subfolder",
                    "path": "Folder2/Subfolder/Subsubfolder",
                },
            },
            "tagged_notes": [],  # No tags in macOS 12
            "protected_notes": ["This note is password protected"],
            "attachment_notes": [],  # No attachments in this sample
            "formatted_notes": ["This note has special formatting"],
            "deleted_notes": ["This note is deleted"],  # macOS 12 has deleted notes
        }
    elif "macOS-13" in db_path.name:
        return {
            "version": "macOS 13 (Ventura)",
            "macos_version": 12,  # Database version detection returns 12 for macOS 13
            "z_uuid": "B1676C6D-218E-4208-9F99-0EE88571CFD4",
            "total_notes": 8,
            "total_folders": 6,
            "account_name": "On My Mac",
            "expected_folders": {
                "Notes": {"parent": None, "path": "Notes"},
                "Recently Deleted": {"parent": None, "path": "Recently Deleted"},
                "Folder": {"parent": None, "path": "Folder"},  # Top-level folder
                "Folder2": {"parent": None, "path": "Folder2"},  # Top-level folder
                "Subfolder": {"parent": "Folder2", "path": "Folder2/Subfolder"},
                "Subsubfolder": {
                    "parent": "Subfolder",
                    "path": "Folder2/Subfolder/Subsubfolder",
                },
            },
            "tagged_notes": ["This note has tags"],  # macOS 13 supports tags
            "protected_notes": ["This note is password protected"],
            "attachment_notes": [],  # No attachments in this sample
            "formatted_notes": ["This note has special formatting"],
            "deleted_notes": [],  # No notes currently in deleted folder
        }
    elif "macOS-15" in db_path.name:
        return {
            "version": "macOS 15 (Sequoia)",
            "macos_version": 15,  # macOS 15 (Sequoia)
            "z_uuid": "09FBEB4A-5B24-424E-814B-4AE8E757FB83",
            "total_notes": 9,
            "total_folders": 6,
            "account_name": "On My Mac",
            "expected_folders": {
                "Notes": {"parent": None, "path": "Notes"},
                "Recently Deleted": {"parent": None, "path": "Recently Deleted"},
                "Folder": {"parent": None, "path": "Folder"},  # Top-level folder
                "Folder2": {"parent": None, "path": "Folder2"},  # Top-level folder
                "Subfolder": {"parent": "Folder2", "path": "Folder2/Subfolder"},
                "Subsubfolder": {
                    "parent": "Subfolder",
                    "path": "Folder2/Subfolder/Subsubfolder",
                },
            },
            "tagged_notes": ["This note has tags"],
            "protected_notes": ["This note is password protected"],
            "attachment_notes": ["This note has an attachment"],
            "formatted_notes": ["This note has special formatting"],
        }
    elif "macOS-26" in db_path.name:
        return {
            "version": "macOS 26 (Tahoe)",
            "macos_version": 26,  # macOS 26 (Tahoe)
            "z_uuid": "9B3F80E8-BEEE-4921-BE3B-57B7D6FFAF2E",
            "total_notes": 8,
            "total_folders": 6,
            "account_name": "On My Mac",
            "expected_folders": {
                "Notes": {"parent": None, "path": "Notes"},
                "Recently Deleted": {"parent": None, "path": "Recently Deleted"},
                "Folder": {"parent": None, "path": "Folder"},  # Top-level folder
                "Folder2": {"parent": None, "path": "Folder2"},  # Top-level folder
                "Subfolder": {"parent": "Folder2", "path": "Folder2/Subfolder"},
                "Subsubfolder": {
                    "parent": "Subfolder",
                    "path": "Folder2/Subfolder/Subsubfolder",
                },
            },
            "tagged_notes": ["This note has tags"],
            "protected_notes": ["This note is password protected"],
            "attachment_notes": [],  # No attachments in this sample
            "formatted_notes": ["This note has special formatting"],
        }
    else:
        # Future database versions can be added here
        return {}


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent
