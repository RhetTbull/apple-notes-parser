# Apple Notes Parser

A Python library for reading and parsing Apple Notes SQLite databases. This library extracts data from Apple Notes SQLite stores, including support for reading tags on notes and finding notes that have specific tags.

This is a python implementation of some of the functionality found in [Apple Cloud Notes Parser](https://github.com/threeplanetssoftware/apple_cloud_notes_parser). If you can use Ruby and need a more full featured solution, I recommend trying Apple Cloud Notes Parser.

See also my companion project [macnotesapp](https://github.com/rhettbull/macnotesapp) which uses AppleScript to interact with the Notes app including creating and modifying notes. Apple Notes Parser only supports reading and parsing Apple Notes databases.

## Features

- **Full Database Parsing**: Read all accounts, folders, and notes from Apple Notes databases
- **Protobuf Support**: Parse compressed note data using Protocol Buffers
- **Tag Extraction**: Automatically extract hashtags from note content
- **Tag Filtering**: Find notes by specific tags or combinations of tags
- **Mention Support**: Extract and search for @mentions in notes
- **Link Extraction**: Find and filter notes containing URLs
- **Attachment Support**: Extract attachment metadata and filter notes by attachment type
- **Multi-Version Support**: Works with macOS 10.11+ Notes databases
- **Search Functionality**: Full-text search across note content
- **Export Capabilities**: Export data to JSON format
- **Metadata Access**: Access creation dates, modification dates, pinned status, etc.

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
parser = AppleNotesParser()

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

```
~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite
```

## Command Line Interface (CLI)

The package includes a simpl command-line interface for working with Apple Notes databases without writing any code. The CLI provides access to all major functionality including listing notes, searching, exporting data, and analyzing attachments.

### Installation and Access

After installing the package, the CLI is available as `apple-notes-parser`:

```bash
# Install from PyPI
pip install apple-notes-parser

# Use the CLI
apple-notes-parser --help
```

### CLI Commands Overview

The CLI provides several commands for different use cases:

- **`list`** - List and filter notes
- **`search`** - Search notes by text content
- **`export`** - Export notes to JSON format
- **`stats`** - Show database statistics and summary
- **`attachments`** - List and extract attachments
- **`tags`** - Analyze and list hashtags

### Global Options

All commands support these global options:

```bash
apple-notes-parser [--database PATH] [--version] COMMAND [OPTIONS]
```

- `--database`, `-d` - Path to NoteStore.sqlite file (auto-detected if not specified)
- `--version` - Show version information
- `--help` - Show help message

### CLI Usage Examples

**Quick Database Overview:**
```bash
apple-notes-parser stats --verbose
```

**Find Work-Related Notes:**
```bash
apple-notes-parser list --folder "Work" --tag "urgent"
```

**Find Notes About Specific Topic:**
```bash
apple-notes-parser search "budget meeting" --content
```

**Custom Database Path:**
```bash
# Use specific database file
apple-notes-parser --database /path/to/custom/NoteStore.sqlite stats
```

## API Reference

### Main Parser Class

#### `AppleNotesParser(database_path: str)`

Main parser class for Apple Notes databases.

**Methods:**

- `load_data()` - Load all data from the database
- `notes` - Get all notes (list[Note])
- `folders` - Get all folders (list[Folder])
- `accounts` - Get all accounts (list[Account])

### Tag and Content Filtering

- `get_notes_by_tag(tag: str)` - Get notes with a specific tag
- `get_notes_by_tags(tags: list[str], match_all: bool = False)` - Get notes with multiple tags
- `get_all_tags()` - Get all unique hashtags
- `get_tag_counts()` - Get usage count for each tag

### Search and Filter

- `search_notes(query: str, case_sensitive: bool = False)` - Full-text search
- `get_notes_by_folder(folder_name: str)` - Get notes in specific folder
- `get_notes_by_account(account_name: str)` - Get notes in specific account
- `get_note_by_applescript_id(applescript_id: str)` - Get note by AppleScript ID (e.g. "x-coredata://5A2C18B7-767B-41A9-BF71-E4E966775D32/ICNote/p4884")
- `get_pinned_notes()` - Get all pinned notes
- `get_protected_notes()` - Get password-protected notes
- `filter_notes(filter_func: Callable[[Note], bool])` - Custom filtering

### Mentions and Links

- `get_notes_with_mentions()` - Get notes containing @mentions
- `get_notes_by_mention(mention: str)` - Get notes mentioning specific user
- `get_notes_with_links()` - Get notes containing URLs
- `get_notes_by_link_domain(domain: str)` - Get notes with links to specific domain

### Attachments

- `get_notes_with_attachments()` - Get notes that have attachments
- `get_notes_by_attachment_type(attachment_type: str)` - Get notes with specific attachment types (image, video, audio, document)
- `get_all_attachments()` - Get all attachments across all notes

### Export

- `export_notes_to_dict(include_content: bool = True)` - Export to dictionary/JSON

### Data Models

#### Note
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
- `applescript_id: str` - AppleScript ID of the note (this is the unique identifier used by AppleScript to interact with the note)
- `tags: list[str]` - Hashtags found in note
- `mentions: list[str]` - @mentions found in note
- `links: list[str]` - URLs found in note
- `attachments: list[Attachment]` - File attachments in note
- `get_folder_path(): str` - Returns the path of the folder the note is in
- `get_attachments_by_extension(extension: str) -> list[Attachment]` - Returns a list of attachments with the specified extension
- `get_attachments_by_type(attachment_type: str) -> list[Attachment]` - Returns a list of attachments with the specified type

#### Folder
- `name: str` - Folder name
- `account: Account` - Owning account
- `uuid: str` - Unique identifier
- `parent_id: int` - Parent folder ID (for nested folders)
- `get_path(): str` - Returns the path of the folder
- `get_parent(): Folder` - Returns the parent folder
- `is_root(): bool` - Returns whether the folder is the root folder

#### Attachment
- `id: int` - Database primary key
- `filename: str` - Attachment filename (e.g., "document.pdf")
- `file_size: int` - File size in bytes
- `type_uti: str` - Uniform Type Identifier (e.g., "com.adobe.pdf")
- `note_id: int` - Parent note ID
- `creation_date: datetime` - When attachment was created
- `modification_date: datetime` - When attachment was last modified
- `uuid: str` - Unique identifier
- `is_remote: bool` - Whether attachment is stored remotely
- `remote_url: str` - Remote URL if applicable

##### Attachment Properties
- `file_extension: str` - File extension (e.g., "pdf", "jpg")
- `mime_type: str` - MIME type (e.g., "application/pdf", "image/jpeg")
- `is_image: bool` - Whether attachment is an image
- `is_video: bool` - Whether attachment is a video
- `is_audio: bool` - Whether attachment is audio
- `is_document: bool` - Whether attachment is a document

#### Account
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

# Find notes with attachments
notes_with_attachments = parser.get_notes_with_attachments()
print(f"Found {len(notes_with_attachments)} notes with attachments")

# Find notes with specific attachment types
image_notes = parser.get_notes_by_attachment_type("image")
document_notes = parser.get_notes_by_attachment_type("document")
video_notes = parser.get_notes_by_attachment_type("video")
audio_notes = parser.get_notes_by_attachment_type("audio")
```

### Working with Attachments

```python
# Get all notes that have attachments
notes_with_attachments = parser.get_notes_with_attachments()
print(f"Found {len(notes_with_attachments)} notes with attachments")

# Filter by attachment type
image_notes = parser.get_notes_by_attachment_type("image")
document_notes = parser.get_notes_by_attachment_type("document")
video_notes = parser.get_notes_by_attachment_type("video")
audio_notes = parser.get_notes_by_attachment_type("audio")

# Get all attachments across all notes
all_attachments = parser.get_all_attachments()
for attachment in all_attachments:
    print(f"{attachment.filename} ({attachment.file_size} bytes) - {attachment.mime_type}")

# Work with individual note attachments
for note in notes_with_attachments:
    print(f"Note: {note.title}")
    for attachment in note.attachments:
        print(f"  - {attachment.filename}")
        print(f"    Size: {attachment.file_size} bytes")
        print(f"    Type: {attachment.type_uti}")
        print(f"    MIME: {attachment.mime_type}")
        print(f"    Is Image: {attachment.is_image}")
        print(f"    Is Document: {attachment.is_document}")

        # Filter by file extension
        if attachment.file_extension == "pdf":
            print(f"    Found PDF: {attachment.filename}")
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

The library uses Protocol Buffers to parse compressed note data. See [Revisiting Apple Notes (6): The Protobuf](https://ciofecaforensics.com/2020/09/18/apple-notes-revisited-protobuf/) for more details about how Apple Notes stores data.

## Limitations

- **Encrypted Notes**: Password-protected notes cannot be decrypted without the password
- **Rich Formatting**: Complex formatting information is not fully preserved in plain text output

## Development and Building

### Prerequisites

For using the library (end users), you only need:
- Python 3.11+
- Dependencies are automatically installed via `uv`:

For development and building, you need:
- Python 3.11+
- `uv` package manager (recommended)
- Development dependencies including `grpcio-tools` (for protobuf code generation, if needed)

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone <this-repository>
   cd apple-notes-parser
   ```

2. **Install in development mode with uv (recommended):**
   ```bash
   uv sync --all-extras
   ```

### Running Tests

The project includes a comprehensive test suite with 54+ tests:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_real_database.py

# Run tests with coverage
uv run pytest --cov=apple_notes_parser
```

### Code Quality and Linting

The project uses modern Python tooling for code quality assurance:

#### Running Ruff (Linting and Formatting)

[Ruff](https://docs.astral.sh/ruff/) is used for fast linting and import sorting:

```bash
# Check for linting issues
uv run ruff check src/

# Automatically fix linting issues (safe fixes only)
uv run ruff check --fix src/

# Apply formatting
uv run ruff format src/

# Check imports are properly sorted
uv run ruff check --select I src/
```

The script `./check` in the project root directory is a convenient wrapper for running all linting and formatting checks and automatically fixing safe issues:

```bash
uv run ./check --verbose
```

#### Running MyPy (Type Checking)

[MyPy](https://mypy.readthedocs.io/) is used for static type checking:

```bash
# Run type checking on the entire codebase
uv run mypy src/apple_notes_parser/

# Run type checking with verbose output
uv run mypy --verbose src/apple_notes_parser/

# Check specific file
uv run mypy src/apple_notes_parser/parser.py
```

#### Pre-commit Workflow

Before submitting code, run the complete quality check using our automated scripts:

```bash
./check
```

### Protobuf Code Generation

**Important:** The protobuf Python files (`notestore_pb2.py`) are pre-generated and included in the repository. You typically don't need to regenerate them unless:

- You're modifying the `notestore.proto` file
- You're updating to a newer protobuf version
- You encounter protobuf version compatibility warnings

#### How to Regenerate Protobuf Files

1. **Ensure you have the required development tools:**
   ```bash
   uv sync --all-extras  # Install development dependencies including grpcio-tools
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

### Adding Support for New Database Versions

The library is designed to be extensible for future macOS versions:

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
   def get_macos_version(self) -> int:
       # Add detection logic for new version
       if "NEW_COLUMN_NAME" in columns:
           self._macos_version = 26  # New version number
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

- **Development dependencies** (for contributors):
  - `pytest>=8.0.0` - Testing framework
  - `pytest-cov>=4.0.0` - Coverage reporting
  - `ruff>=0.8.0` - Fast Python linter and formatter
  - `mypy>=1.13.0` - Static type checker
  - `grpcio-tools>=1.74.0` - Protocol buffer compiler for code generation
  - `types-protobuf>=6.30.2.20250703` - Type stubs for protobuf

### Troubleshooting

**Protobuf version warnings:**
- Regenerate protobuf files using the steps above
- Ensure `protobuf` and `grpcio-tools` are at compatible versions (install dev dependencies with `uv sync --dev`)

**Test failures:**
- Ensure you have the real test database in `tests/data/`
- Check that your Python version is 3.11+
- Try running `uv sync --all-extras` to refresh dependencies

**Import errors:**
- Verify installation with `uv run python -c "import apple_notes_parser; print('OK')"`
- Check that you're in the correct virtual environment

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

### Contribution Guidelines

1. **Fork the repository** and create a feature branch
2. **Write tests** for any new functionality
3. **Run quality checks** before submitting:
  ```bash
  uv run ./check
  ```
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
