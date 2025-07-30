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

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This library builds upon the excellent work from:

- [threeplanetssoftware/apple_cloud_notes_parser](https://github.com/threeplanetssoftware/apple_cloud_notes_parser) - Ruby implementation and protobuf definitions
- [HamburgChimps/apple-notes-liberator](https://github.com/HamburgChimps/apple-notes-liberator) - Java implementation
- [Ciofeca Forensics](https://ciofecaforensics.com/) - Technical research on Apple Notes storage format

## Disclaimer

This library is for educational and personal use only. Always respect privacy and obtain proper authorization before accessing someone else's data.