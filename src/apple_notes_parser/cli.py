"""Command-line interface for Apple Notes Parser."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from . import AppleNotesParser, __version__
from .exceptions import AppleNotesParserError


def handle_parser_error(e: AppleNotesParserError) -> None:
    """Handle parser errors with helpful messages."""
    if "Could not find Apple Notes database" in str(e):
        print(f"Error: {e}", file=sys.stderr)
        print("\nTip: Specify a database path with --database or -d", file=sys.stderr)
        print("Example: apple-notes-parser --database /path/to/NoteStore.sqlite list", file=sys.stderr)
    else:
        print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)


def format_size(size_bytes: int | None) -> str:
    """Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        str: Formatted size string (e.g., '1.2 MB', '345 KB').
    """
    if size_bytes is None:
        return "Unknown"
    
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            if unit == 'B':
                return f"{size_bytes} {unit}"
            else:
                return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_date(date: datetime | None) -> str:
    """Format datetime for display.
    
    Args:
        date: Datetime object to format.
        
    Returns:
        str: Formatted date string.
    """
    if date is None:
        return "Unknown"
    return date.strftime("%Y-%m-%d %H:%M:%S")


def print_note(note, include_content: bool = False, include_attachments: bool = False) -> None:
    """Print note information in a formatted way.
    
    Args:
        note: Note object to print.
        include_content: Whether to include note content.
        include_attachments: Whether to include attachment details.
    """
    print(f"📝 {note.title or 'Untitled'}")
    print(f"   ID: {note.note_id}")
    print(f"   Folder: {note.folder.name}")
    print(f"   Account: {note.account.name}")
    print(f"   Created: {format_date(note.creation_date)}")
    print(f"   Modified: {format_date(note.modification_date)}")
    
    if note.is_pinned:
        print("   📌 Pinned")
    if note.is_password_protected:
        print("   🔒 Password Protected")
    
    if note.tags:
        print(f"   Tags: {', '.join('#' + tag for tag in note.tags)}")
    if note.mentions:
        print(f"   Mentions: {', '.join('@' + mention for mention in note.mentions)}")
    if note.links:
        print(f"   Links: {len(note.links)} URL(s)")
    
    if note.has_attachments():
        print(f"   📎 Attachments: {len(note.attachments)}")
        if include_attachments:
            for i, attachment in enumerate(note.attachments, 1):
                print(f"      {i}. {attachment.filename or '[No filename]'}")
                print(f"         Size: {format_size(attachment.file_size)}")
                print(f"         Type: {attachment.type_uti or 'Unknown'}")
                if attachment.mime_type:
                    print(f"         MIME: {attachment.mime_type}")
    
    if include_content and note.content:
        print("\n   Content:")
        # Truncate very long content
        content = note.content[:500]
        if len(note.content) > 500:
            content += "... (truncated)"
        # Indent each line
        for line in content.split('\n'):
            print(f"   {line}")
    
    print()


def cmd_list(args) -> None:
    """List all notes with optional filtering."""
    try:
        parser = AppleNotesParser(args.database)
        
        notes = parser.notes
        
        # Apply filters
        if args.folder:
            notes = [n for n in notes if n.folder.name.lower() == args.folder.lower()]
        
        if args.account:
            notes = [n for n in notes if n.account.name.lower() == args.account.lower()]
        
        if args.tag:
            notes = [n for n in notes if n.has_tag(args.tag)]
        
        if args.attachments:
            notes = [n for n in notes if n.has_attachments()]
        
        if args.pinned:
            notes = [n for n in notes if n.is_pinned]
        
        if args.protected:
            notes = [n for n in notes if n.is_password_protected]
        
        print(f"Found {len(notes)} note(s)")
        print()
        
        for note in notes:
            print_note(note, include_content=args.content, include_attachments=args.show_attachments)
            
    except AppleNotesParserError as e:
        handle_parser_error(e)


def cmd_search(args) -> None:
    """Search notes by text content."""
    try:
        parser = AppleNotesParser(args.database)
        
        notes = parser.search_notes(args.query, case_sensitive=args.case_sensitive)
        
        print(f"Found {len(notes)} note(s) matching '{args.query}'")
        print()
        
        for note in notes:
            print_note(note, include_content=args.content, include_attachments=args.show_attachments)
            
    except AppleNotesParserError as e:
        handle_parser_error(e)


def cmd_export(args) -> None:
    """Export notes to JSON file."""
    try:
        parser = AppleNotesParser(args.database)
        
        # Apply filters if specified
        notes_to_export = parser.notes
        
        if args.folder:
            notes_to_export = [n for n in notes_to_export if n.folder.name.lower() == args.folder.lower()]
        
        if args.account:
            notes_to_export = [n for n in notes_to_export if n.account.name.lower() == args.account.lower()]
        
        if args.tag:
            notes_to_export = [n for n in notes_to_export if n.has_tag(args.tag)]
        
        # Create a filtered export
        if len(notes_to_export) != len(parser.notes):
            # Create custom export with filtered notes
            folders_dict = parser.folders_dict
            export_data = {
                'accounts': [
                    {
                        'id': account.id,
                        'name': account.name,
                        'identifier': account.identifier,
                        'user_record_name': account.user_record_name
                    }
                    for account in parser.accounts
                ],
                'folders': [
                    {
                        'id': folder.id,
                        'name': folder.name,
                        'account_name': folder.account.name,
                        'uuid': folder.uuid,
                        'parent_id': folder.parent_id,
                        'path': folder.get_path(folders_dict)
                    }
                    for folder in parser.folders
                ],
                'notes': [
                    {
                        'id': note.id,
                        'note_id': note.note_id,
                        'title': note.title,
                        'content': note.content if args.include_content else None,
                        'creation_date': note.creation_date.isoformat() if note.creation_date else None,
                        'modification_date': note.modification_date.isoformat() if note.modification_date else None,
                        'account_name': note.account.name,
                        'folder_name': note.folder.name,
                        'folder_path': note.get_folder_path(folders_dict),
                        'is_pinned': note.is_pinned,
                        'is_password_protected': note.is_password_protected,
                        'uuid': note.uuid,
                        'applescript_id': note.applescript_id,
                        'tags': note.tags,
                        'mentions': note.mentions,
                        'links': note.links,
                        'attachments': [
                            {
                                'id': attachment.id,
                                'filename': attachment.filename,
                                'file_size': attachment.file_size,
                                'type_uti': attachment.type_uti,
                                'file_extension': attachment.file_extension,
                                'mime_type': attachment.mime_type,
                                'is_image': attachment.is_image,
                                'is_video': attachment.is_video,
                                'is_audio': attachment.is_audio,
                                'is_document': attachment.is_document,
                                'creation_date': attachment.creation_date.isoformat() if attachment.creation_date else None,
                                'modification_date': attachment.modification_date.isoformat() if attachment.modification_date else None,
                                'uuid': attachment.uuid,
                                'is_remote': attachment.is_remote,
                                'remote_url': attachment.remote_url
                            }
                            for attachment in note.attachments
                        ]
                    }
                    for note in notes_to_export
                ]
            }
        else:
            # Export all data
            export_data = parser.export_notes_to_dict(include_content=args.include_content)
        
        # Write to file
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(notes_to_export)} note(s) to {output_path}")
        
    except AppleNotesParserError as e:
        handle_parser_error(e)
    except IOError as e:
        print(f"Error writing to file: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args) -> None:
    """Show database statistics."""
    try:
        parser = AppleNotesParser(args.database)
        
        print("📊 Apple Notes Database Statistics")
        print("=" * 40)
        
        # Basic counts
        print(f"Total Notes: {len(parser.notes)}")
        print(f"Total Folders: {len(parser.folders)}")
        print(f"Total Accounts: {len(parser.accounts)}")
        
        # Account breakdown
        print("\n📁 Notes by Account:")
        account_counts = parser.get_account_counts()
        for account, count in account_counts.items():
            print(f"   {account}: {count} notes")
        
        # Folder breakdown
        print("\n📂 Notes by Folder:")
        folder_counts = parser.get_folder_counts()
        for folder, count in folder_counts.items():
            print(f"   {folder}: {count} notes")
        
        # Tags
        tag_counts = parser.get_tag_counts()
        if tag_counts:
            print(f"\n🏷️  Tags: {len(tag_counts)} unique tags")
            if args.verbose:
                print("   Top tags:")
                sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                for tag, count in sorted_tags[:10]:
                    print(f"      #{tag}: {count} notes")
        else:
            print("\n🏷️  No tags found")
        
        # Mentions
        all_mentions = parser.get_all_mentions()
        if all_mentions:
            print(f"\n👥 Mentions: {len(all_mentions)} unique mentions")
            if args.verbose:
                print("   Mentions:")
                for mention in all_mentions[:10]:
                    print(f"      @{mention}")
        else:
            print("\n👥 No mentions found")
        
        # Attachments
        all_attachments = parser.get_all_attachments()
        if all_attachments:
            print(f"\n📎 Attachments: {len(all_attachments)} total attachments")
            
            # Attachment type breakdown
            image_count = len([a for a in all_attachments if a.is_image])
            video_count = len([a for a in all_attachments if a.is_video])
            audio_count = len([a for a in all_attachments if a.is_audio])
            document_count = len([a for a in all_attachments if a.is_document])
            other_count = len(all_attachments) - image_count - video_count - audio_count - document_count
            
            if image_count:
                print(f"   Images: {image_count}")
            if video_count:
                print(f"   Videos: {video_count}")
            if audio_count:
                print(f"   Audio: {audio_count}")
            if document_count:
                print(f"   Documents: {document_count}")
            if other_count:
                print(f"   Other: {other_count}")
                
            # Total size
            total_size = sum(a.file_size for a in all_attachments if a.file_size)
            if total_size:
                print(f"   Total Size: {format_size(total_size)}")
        else:
            print("\n📎 No attachments found")
        
        # Special notes
        pinned_notes = parser.get_pinned_notes()
        protected_notes = parser.get_protected_notes()
        notes_with_links = parser.get_notes_with_links()
        
        print(f"\n📌 Pinned Notes: {len(pinned_notes)}")
        print(f"🔒 Password Protected: {len(protected_notes)}")
        print(f"🔗 Notes with Links: {len(notes_with_links)}")
        
    except AppleNotesParserError as e:
        handle_parser_error(e)


def cmd_attachments(args) -> None:
    """List and manage attachments."""
    try:
        parser = AppleNotesParser(args.database)
        
        if args.type:
            notes = parser.get_notes_by_attachment_type(args.type)
            attachments = [att for note in notes for att in note.get_attachments_by_type(args.type)]
        else:
            attachments = parser.get_all_attachments()
        
        print(f"Found {len(attachments)} attachment(s)")
        print()
        
        total_size = 0
        for attachment in attachments:
            print(f"📎 {attachment.filename or '[No filename]'}")
            print(f"   ID: {attachment.id}")
            print(f"   Size: {format_size(attachment.file_size)}")
            print(f"   Type: {attachment.type_uti or 'Unknown'}")
            if attachment.mime_type:
                print(f"   MIME: {attachment.mime_type}")
            print(f"   Created: {format_date(attachment.creation_date)}")
            print(f"   Modified: {format_date(attachment.modification_date)}")
            
            # Find parent note
            parent_notes = [n for n in parser.notes if attachment in n.attachments]
            if parent_notes:
                parent_note = parent_notes[0]
                print(f"   Note: {parent_note.title or 'Untitled'}")
                print(f"   Folder: {parent_note.folder.name}")
            
            print(f"   Categories: ", end="")
            categories = []
            if attachment.is_image:
                categories.append("Image")
            if attachment.is_video:
                categories.append("Video")
            if attachment.is_audio:
                categories.append("Audio")
            if attachment.is_document:
                categories.append("Document")
            print(", ".join(categories) if categories else "Other")
            
            if attachment.file_size:
                total_size += attachment.file_size
            
            print()
        
        if attachments:
            print(f"Total size: {format_size(total_size)}")
        
    except AppleNotesParserError as e:
        handle_parser_error(e)


def cmd_tags(args) -> None:
    """List and analyze tags."""
    try:
        parser = AppleNotesParser(args.database)
        
        tag_counts = parser.get_tag_counts()
        
        if not tag_counts:
            print("No tags found in the database.")
            return
        
        print(f"Found {len(tag_counts)} unique tag(s)")
        print()
        
        # Sort by count (descending) or alphabetically
        if args.sort_by_count:
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        else:
            sorted_tags = sorted(tag_counts.items())
        
        for tag, count in sorted_tags:
            print(f"#{tag}: {count} note(s)")
            
            if args.show_notes:
                notes = parser.get_notes_by_tag(tag)
                for note in notes[:5]:  # Show first 5 notes
                    print(f"   - {note.title or 'Untitled'}")
                if len(notes) > 5:
                    print(f"   ... and {len(notes) - 5} more")
                print()
        
    except AppleNotesParserError as e:
        handle_parser_error(e)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog='apple-notes-parser',
        description='Parse and analyze Apple Notes databases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  apple-notes-parser list                              # List all notes
  apple-notes-parser list --folder "Work"              # List notes in Work folder
  apple-notes-parser list --tag "important"            # List notes with #important tag
  apple-notes-parser search "meeting notes"            # Search for specific text
  apple-notes-parser export notes.json                 # Export all notes to JSON
  apple-notes-parser export --folder "Work" work.json  # Export only Work folder
  apple-notes-parser stats                             # Show database statistics
  apple-notes-parser attachments --type image          # List image attachments
  apple-notes-parser tags --sort-by-count              # List tags sorted by usage
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'apple-notes-parser {__version__}'
    )
    
    parser.add_argument(
        '--database', '-d',
        help='Path to NoteStore.sqlite file (auto-detected if not specified)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List notes with optional filtering')
    list_parser.add_argument('--folder', help='Filter by folder name')
    list_parser.add_argument('--account', help='Filter by account name')
    list_parser.add_argument('--tag', help='Filter by tag')
    list_parser.add_argument('--attachments', action='store_true', help='Show only notes with attachments')
    list_parser.add_argument('--pinned', action='store_true', help='Show only pinned notes')
    list_parser.add_argument('--protected', action='store_true', help='Show only password-protected notes')
    list_parser.add_argument('--content', action='store_true', help='Include note content in output')
    list_parser.add_argument('--show-attachments', action='store_true', help='Show attachment details')
    list_parser.set_defaults(func=cmd_list)
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search notes by text content')
    search_parser.add_argument('query', help='Text to search for')
    search_parser.add_argument('--case-sensitive', action='store_true', help='Perform case-sensitive search')
    search_parser.add_argument('--content', action='store_true', help='Include note content in output')
    search_parser.add_argument('--show-attachments', action='store_true', help='Show attachment details')
    search_parser.set_defaults(func=cmd_search)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export notes to JSON file')
    export_parser.add_argument('output', help='Output JSON file path')
    export_parser.add_argument('--include-content', action='store_true', default=True, help='Include note content (default: True)')
    export_parser.add_argument('--no-content', dest='include_content', action='store_false', help='Exclude note content')
    export_parser.add_argument('--folder', help='Export only notes from specific folder')
    export_parser.add_argument('--account', help='Export only notes from specific account')
    export_parser.add_argument('--tag', help='Export only notes with specific tag')
    export_parser.set_defaults(func=cmd_export)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Attachments command
    attachments_parser = subparsers.add_parser('attachments', help='List and analyze attachments')
    attachments_parser.add_argument('--type', choices=['image', 'video', 'audio', 'document'], help='Filter by attachment type')
    attachments_parser.set_defaults(func=cmd_attachments)
    
    # Tags command
    tags_parser = subparsers.add_parser('tags', help='List and analyze tags')
    tags_parser.add_argument('--sort-by-count', action='store_true', help='Sort tags by usage count instead of alphabetically')
    tags_parser.add_argument('--show-notes', action='store_true', help='Show example notes for each tag')
    tags_parser.set_defaults(func=cmd_tags)
    
    return parser


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point.
    
    Args:
        argv: Command line arguments (uses sys.argv if None).
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return
    
    # Call the appropriate command function
    args.func(args)


if __name__ == '__main__':
    main()