# Apple Notes Parser

A Python library for reading and parsing Apple Notes SQLite databases. This library can extract all data from Notes SQLite stores, including support for reading tags on notes and finding notes that have specific tags.

## Features

-  **Full Database Parsing**: Read all accounts, folders, and notes from Apple Notes databases
-  **Protobuf Support**: Parse compressed note data using Protocol Buffers
-  **Tag Extraction**: Automatically extract hashtags from note content
-  **Tag Filtering**: Find notes by specific tags or combinations of tags
-  **Mention Support**: Extract and search for @mentions in notes
-  **Link Extraction**: Find and filter notes containing URLs
-  **Multi-Version Support**: Works with iOS 9+ and macOS Notes databases
-  **Search Functionality**: Full-text search across note content
-  **Export Capabilities**: Export data to JSON format
-  **Metadata Access**: Access creation dates, modification dates, pinned status, etc.

## Installation

### Using uv (recommended)

```bash
git clone <this-repository>
cd apple-notes-parser
uv sync
```

### Using pip

```bash
git clone <this-repository>
cd apple-notes-parser
pip install -e .
```

## Quick Start

```python
from apple_notes_parser import AppleNotesParser

# Initialize parser with your Notes database
parser = AppleNotesParser("/path/to/NoteStore.sqlite")

# Load all data
parser.load_data()

# Get basic statistics
print(f"Found {len(parser.notes)} notes in {len(parser.folders)} folders")

# Find notes with specific tags
work_notes = parser.get_notes_by_tag("work")
print(f"Found {len(work_notes)} notes tagged with #work")

# Search for notes containing text
important_notes = parser.search_notes("important")

# Get all unique tags
all_tags = parser.get_all_tags()
print(f"All tags: {', '.join(all_tags)}")
```

## Database Location

The Apple Notes database is typically located at:

**macOS:**
```
~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite
```

**iOS (from backup):**
```
# iTunes Backup
~/Library/Application Support/MobileSync/Backup/<device-id>/4f/4f98687d8ab0d6d1a371110e6b7300f6e465bef2

# Physical/SSH access
/private/var/mobile/Library/Notes/NoteStore.sqlite
```

## API Reference

### Main Parser Class

#### `AppleNotesParser(database_path: str)`

Main parser class for Apple Notes databases.

**Methods:**

- `load_data()` - Load all data from the database
- `notes` - Get all notes (List[Note])
- `folders` - Get all folders (List[Folder])
- `accounts` - Get all accounts (List[Account])

### Tag and Content Filtering

- `get_notes_by_tag(tag: str)` - Get notes with a specific tag
- `get_notes_by_tags(tags: List[str], match_all: bool = False)` - Get notes with multiple tags
- `get_all_tags()` - Get all unique hashtags
- `get_tag_counts()` - Get usage count for each tag

### Search and Filter

- `search_notes(query: str, case_sensitive: bool = False)` - Full-text search
- `get_notes_by_folder(folder_name: str)` - Get notes in specific folder
- `get_notes_by_account(account_name: str)` - Get notes in specific account
- `get_pinned_notes()` - Get all pinned notes
- `get_protected_notes()` - Get password-protected notes
- `filter_notes(filter_func: Callable[[Note], bool])` - Custom filtering

### Mentions and Links

- `get_notes_with_mentions()` - Get notes containing @mentions
- `get_notes_by_mention(mention: str)` - Get notes mentioning specific user
- `get_notes_with_links()` - Get notes containing URLs
- `get_notes_by_link_domain(domain: str)` - Get notes with links to specific domain

### Export

- `export_notes_to_dict(include_content: bool = True)` - Export to dictionary/JSON

### Data Models

#### `Note`
- `id: int` - Database primary key
- `note_id: int` - Note identifier
- `title: str` - Note title
- `content: str` - Note text content
- `creation_date: datetime` - When note was created
- `modification_date: datetime` - When note was last modified
- `account: Account` - Owning account
- `folder: Folder` - Containing folder
- `is_pinned: bool` - Whether note is pinned
- `is_password_protected: bool` - Whether note is encrypted
- `uuid: str` - Unique identifier
- `tags: List[str]` - Hashtags found in note
- `mentions: List[str]` - @mentions found in note
- `links: List[str]` - URLs found in note

#### `Folder`
- `id: int` - Database primary key
- `name: str` - Folder name
- `account: Account` - Owning account
- `uuid: str` - Unique identifier
- `parent_id: int` - Parent folder ID (for nested folders)

#### `Account`
- `id: int` - Database primary key
- `name: str` - Account name (e.g., "iCloud", "On My Mac")
- `identifier: str` - Account identifier
- `user_record_name: str` - CloudKit user record name

## Examples

### Find Notes by Tags

```python
# Find notes with specific tag
work_notes = parser.get_notes_by_tag("work")

# Find notes with multiple tags (OR logic)
important_or_urgent = parser.get_notes_by_tags(["important", "urgent"], match_all=False)

# Find notes with multiple tags (AND logic)
work_and_important = parser.get_notes_by_tags(["work", "important"], match_all=True)

# Get tag statistics
tag_counts = parser.get_tag_counts()
for tag, count in tag_counts.items():
    print(f"#{tag}: {count} notes")
```

### Search and Filter

```python
# Full-text search
meeting_notes = parser.search_notes("meeting")

# Custom filtering
recent_notes = parser.filter_notes(
    lambda note: note.modification_date and 
                 note.modification_date > datetime.now() - timedelta(days=7)
)

# Find notes with attachments (based on content)
notes_with_images = parser.filter_notes(
    lambda note: note.content and "image" in note.content.lower()
)
```

### Export Data

```python
# Export all data to JSON
data = parser.export_notes_to_dict()
with open("notes_backup.json", "w") as f:
    json.dump(data, f, indent=2)

# Export without content (for privacy)
metadata_only = parser.export_notes_to_dict(include_content=False)
```

## Technical Details

### Protobuf Parsing

The library uses Protocol Buffers to parse compressed note data. It can handle:

- Modern Notes format (iOS 9+) with gzipped protobuf data
- Legacy Notes format (pre-iOS 9) with plain text
- Automatic fallback when protobuf parsing fails

### Database Schema Detection

Automatically detects iOS/macOS version based on database schema:

- iOS 18: `ZUNAPPLIEDENCRYPTEDRECORDDATA` column
- iOS 17: `ZGENERATION` column  
- iOS 16: `ZACCOUNT6` column
- iOS 15: `ZACCOUNT5` column
- iOS 14: `ZLASTOPENEDDATE` column
- iOS 13: `ZACCOUNT4` column
- iOS 12: `ZSERVERRECORDDATA` column
- iOS 11: `Z_11NOTES` table
- Legacy: Different table structure

### Tag Extraction

Tags are extracted from note content using regex patterns:

- Hashtags: `#(\w+)` - matches #work, #important, etc.
- Mentions: `@(\w+)` - matches @john, @team, etc.
- Links: Full URL pattern matching

## Limitations

- **Encrypted Notes**: Password-protected notes cannot be decrypted without the password
- **Attachments**: Binary attachments are not extracted, only referenced
- **Rich Formatting**: Complex formatting information is not fully preserved in plain text output
- **Deleted Notes**: Notes in trash/recently deleted are not accessible through this library

## Development and Building

### Prerequisites

For using the library (end users), you only need:
- Python 3.11+
- Dependencies are automatically installed via `uv` or `pip`

For development and building, you need:
- Python 3.11+  
- `uv` package manager (recommended) or `pip`
- `grpcio-tools` (for protobuf code generation, if needed)

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone <this-repository>
   cd apple-notes-parser
   ```

2. **Install in development mode with uv (recommended):**
   ```bash
   uv sync --dev
   ```

3. **Or install with pip:**
   ```bash
   pip install -e ".[dev]"
   ```

### Running Tests

The project includes a comprehensive test suite with 54+ tests:

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_real_database.py

# Run tests with coverage
uv run pytest --cov=apple_notes_parser
```

### Protobuf Code Generation

**Important:** The protobuf Python files (`notestore_pb2.py`) are pre-generated and included in the repository. You typically don't need to regenerate them unless:

- You're modifying the `notestore.proto` file
- You're updating to a newer protobuf version
- You encounter protobuf version compatibility warnings

#### When to Regenerate Protobuf Files

If you see warnings like:
```
UserWarning: Protobuf gencode version X.X.X is exactly one major version older than the runtime version Y.Y.Y
```

#### How to Regenerate Protobuf Files

1. **Ensure you have the required tools:**
   ```bash
   uv add grpcio-tools  # Should already be installed as a dependency
   ```

2. **Navigate to the protobuf source directory:**
   ```bash
   cd src/apple_notes_parser
   ```

3. **Regenerate the Python protobuf files using the automated script:**
   ```bash
   python scripts/regenerate_protobuf.py
   ```

   Or manually:
   ```bash
   cd src/apple_notes_parser
   python -m grpc_tools.protoc --proto_path=. --python_out=. notestore.proto
   cd ../..  # Back to project root
   uv run pytest  # Verify everything works
   ```

The automated script will:
- Regenerate the protobuf files
- Verify the version was updated correctly
- Run the test suite to ensure compatibility

### Package Structure

```
apple-notes-parser/
├── src/apple_notes_parser/
│   ├── __init__.py              # Main package exports
│   ├── parser.py                # Main AppleNotesParser class  
│   ├── database.py              # SQLite database operations
│   ├── models.py                # Data models (Note, Folder, Account)
│   ├── protobuf_parser.py       # Protobuf parsing logic
│   ├── embedded_objects.py      # Hashtag/mention extraction
│   ├── exceptions.py            # Custom exceptions
│   ├── notestore.proto          # Protocol buffer schema (source)
│   └── notestore_pb2.py         # Generated protobuf Python code
├── tests/                       # Comprehensive test suite
│   ├── conftest.py              # Pytest fixtures and configuration
│   ├── data/                    # Test databases
│   │   ├── NoteStore-macOS-15-Seqoia.sqlite  # Real test database
│   │   └── Notes-macOS-15-Seqoia.txt         # Database content dump
│   ├── test_real_database.py    # Tests using real database
│   ├── test_version_agnostic.py # Cross-version compatibility tests
│   └── test_*.py                # Additional test modules
├── scripts/                     # Development and build scripts
│   └── regenerate_protobuf.py   # Automated protobuf regeneration
├── pyproject.toml               # Project configuration and dependencies
├── README.md                    # This file
└── pytest.ini                  # Test configuration
```

### Adding Support for New Database Versions

The library is designed to be extensible for future macOS/iOS versions:

1. **Add new test database:**
   ```bash
   # Place new database in tests/data/
   cp /path/to/NoteStore-macOS-16.sqlite tests/data/
   ```

2. **Update test fixtures in `tests/conftest.py`:**
   ```python
   @pytest.fixture(params=["macos_15", "macos_16"])  # Add new version
   def versioned_database(request):
       if request.param == "macos_16":
           database_path = Path(__file__).parent / "data" / "NoteStore-macOS-16.sqlite"
           # ... handle new version
   ```

3. **Update version detection in `src/apple_notes_parser/database.py`:**
   ```python
   def get_ios_version(self) -> int:
       # Add detection logic for new version
       if "NEW_COLUMN_NAME" in columns:
           self._ios_version = 19  # New version number
   ```

4. **Run tests to ensure compatibility:**
   ```bash
   uv run pytest tests/test_version_agnostic.py
   ```

### Building and Distribution

To build the package for distribution:

```bash
# Install build tools
uv add --dev build

# Build the package
uv run python -m build

# This creates:
# dist/apple_notes_parser-0.1.0-py3-none-any.whl
# dist/apple_notes_parser-0.1.0.tar.gz
```

### Dependency Management

The project uses these key dependencies:

- **Runtime dependencies** (required for end users):
  - `protobuf>=6.31.1` - Protocol buffer runtime for parsing compressed note data
  - `grpcio-tools>=1.74.0` - Includes protobuf compiler for code generation

- **Development dependencies** (for contributors):
  - `pytest>=8.0.0` - Testing framework
  - `pytest-cov>=4.0.0` - Coverage reporting

### Troubleshooting

**Protobuf version warnings:**
- Regenerate protobuf files using the steps above
- Ensure `protobuf` and `grpcio-tools` are at compatible versions

**Test failures:**
- Ensure you have the real test database in `tests/data/`
- Check that your Python version is 3.11+
- Try running `uv sync --dev` to refresh dependencies

**Import errors:**
- Verify installation with `uv run python -c "import apple_notes_parser; print('OK')"`
- Check that you're in the correct virtual environment

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

### Contribution Guidelines

1. **Fork the repository** and create a feature branch
2. **Write tests** for any new functionality
3. **Ensure all tests pass** with `uv run pytest`
4. **Follow existing code style** and patterns
5. **Update documentation** for user-facing changes
6. **Submit a pull request** with a clear description

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This library builds upon the excellent work from:

- [threeplanetssoftware/apple_cloud_notes_parser](https://github.com/threeplanetssoftware/apple_cloud_notes_parser) - Ruby implementation and protobuf definitions
- [HamburgChimps/apple-notes-liberator](https://github.com/HamburgChimps/apple-notes-liberator) - Java implementation
- [Ciofeca Forensics](https://ciofecaforensics.com/) - Technical research on Apple Notes storage format

## Disclaimer

This library is for educational and personal use only. Always respect privacy and obtain proper authorization before accessing someone else's data.