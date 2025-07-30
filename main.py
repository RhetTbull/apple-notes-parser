#!/usr/bin/env python3
"""
Example usage of the Apple Notes Parser library.
"""

import json
from pathlib import Path
from src.apple_notes_parser import AppleNotesParser, AppleNotesParserError


def main():
    """Main example function."""
    # Example database path - adjust this to your actual Notes database
    # On macOS, this is typically:
    # ~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite

    database_path = Path("~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite").expanduser()

    if not database_path.exists():
        print(f"Notes database not found at: {database_path}")
        print("Please provide the correct path to your NoteStore.sqlite file")
        return

    try:
        # Initialize the parser
        parser = AppleNotesParser(str(database_path))

        # Load all data
        print("Loading Apple Notes data...")
        parser.load_data()

        # Basic statistics
        print(f"\nFound {len(parser.accounts)} accounts")
        print(f"Found {len(parser.folders)} folders")
        print(f"Found {len(parser.notes)} notes")

        # Show accounts
        print("\nAccounts:")
        for account in parser.accounts:
            print(f"  - {account.name} (ID: {account.id})")

        # Show folders
        print("\nFolders:")
        for folder in parser.folders:
            print(f"  - {folder.name} in {folder.account.name}")

        # Show notes with tags
        tagged_notes = [note for note in parser.notes if note.tags]
        if tagged_notes:
            print(f"\nNotes with tags ({len(tagged_notes)}):")
            for note in tagged_notes[:5]:  # Show first 5
                print(f"  - '{note.title}' has tags: {', '.join(note.tags)}")

        # Show all unique tags
        all_tags = parser.get_all_tags()
        if all_tags:
            print(f"\nAll tags found: {', '.join(all_tags)}")

        # Example: Find notes with a specific tag
        if all_tags:
            sample_tag = all_tags[0]
            tagged_notes = parser.get_notes_by_tag(sample_tag)
            print(f"\nNotes with tag '{sample_tag}': {len(tagged_notes)}")

        # Show pinned notes
        pinned_notes = parser.get_pinned_notes()
        print(f"\nPinned notes: {len(pinned_notes)}")

        # Show notes with mentions
        notes_with_mentions = parser.get_notes_with_mentions()
        print(f"Notes with mentions: {len(notes_with_mentions)}")

        # Show notes with links
        notes_with_links = parser.get_notes_with_links()
        print(f"Notes with links: {len(notes_with_links)}")

        # Example search
        search_results = parser.search_notes("totry")
        print(f"\nNotes containing 'totry': {len(search_results)}")

        # Tag counts
        tag_counts = parser.get_tag_counts()
        if tag_counts:
            print("\nTag usage counts:")
            for tag, count in list(tag_counts.items())[:5]:
                print(f"  #{tag}: {count} notes")

        # Folder counts
        folder_counts = parser.get_folder_counts()
        print("\nNotes per folder:")
        for folder, count in list(folder_counts.items())[:5]:
            print(f"  {folder}: {count} notes")

        # Export example
        print("\nExporting data to JSON...")
        export_data = parser.export_notes_to_dict(include_content=True)

        with open("notes_export.json", "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print("Data exported to notes_export.json")

    except AppleNotesParserError as e:
        print(f"Error parsing Notes database: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
