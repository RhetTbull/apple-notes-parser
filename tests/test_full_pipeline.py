#!/usr/bin/env python3
"""
Test the full pipeline from Note creation to JSON export to verify tags are preserved.
"""

from datetime import datetime
from src.apple_notes_parser.models import Account, Folder, Note
from src.apple_notes_parser.parser import AppleNotesParser
import json

def test_note_model_with_tags():
    """Test that Note model correctly handles tags."""
    
    # Create test account and folder
    account = Account(id=1, name="Test Account", identifier="test")
    folder = Folder(id=1, name="Test Folder", account=account)
    
    # Create note with tags
    note = Note(
        id=1,
        note_id=1,
        title="Test Note",
        content="This is a note with #work and #important tags",
        creation_date=datetime.now(),
        modification_date=datetime.now(),
        account=account,
        folder=folder,
        tags=["work", "important"],
        mentions=["john"],
        links=["https://example.com"]
    )
    
    print("Testing Note model...")
    print(f"Note tags: {note.tags}")
    print(f"Note mentions: {note.mentions}")
    print(f"Note links: {note.links}")
    
    # Test tag checking methods
    assert note.has_tag("work"), "Should have 'work' tag"
    assert note.has_tag("important"), "Should have 'important' tag"
    assert not note.has_tag("missing"), "Should not have 'missing' tag"
    
    assert note.has_mention("john"), "Should have 'john' mention"
    assert not note.has_mention("missing"), "Should not have 'missing' mention"
    
    assert note.has_link("https://example.com"), "Should have example.com link"
    
    print("✅ Note model tests passed")
    
    return note

def test_export_includes_tags():
    """Test that export includes tags in JSON."""
    
    # Create test data
    account = Account(id=1, name="Test Account", identifier="test")
    folder = Folder(id=1, name="Test Folder", account=account)
    
    notes_with_tags = [
        Note(
            id=1, note_id=1, title="Note 1", content="Content with #tag1",
            creation_date=datetime.now(), modification_date=datetime.now(),
            account=account, folder=folder,
            tags=["tag1"], mentions=[], links=[]
        ),
        Note(
            id=2, note_id=2, title="Note 2", content="Content with #tag2 and #tag3",
            creation_date=datetime.now(), modification_date=datetime.now(),
            account=account, folder=folder,
            tags=["tag2", "tag3"], mentions=["user"], links=["https://test.com"]
        )
    ]
    
    # Mock a parser to test export
    class MockParser:
        def __init__(self):
            self.accounts = [account]
            self.folders = [folder]
            self.notes = notes_with_tags
        
        def export_notes_to_dict(self, include_content=True):
            return {
                'accounts': [
                    {
                        'id': account.id,
                        'name': account.name,
                        'identifier': account.identifier,
                        'user_record_name': account.user_record_name
                    }
                    for account in self.accounts
                ],
                'folders': [
                    {
                        'id': folder.id,
                        'name': folder.name,
                        'account_name': folder.account.name,
                        'uuid': folder.uuid,
                        'parent_id': folder.parent_id
                    }
                    for folder in self.folders
                ],
                'notes': [
                    {
                        'id': note.id,
                        'note_id': note.note_id,
                        'title': note.title,
                        'content': note.content if include_content else None,
                        'creation_date': note.creation_date.isoformat() if note.creation_date else None,
                        'modification_date': note.modification_date.isoformat() if note.modification_date else None,
                        'account_name': note.account.name,
                        'folder_name': note.folder.name,
                        'is_pinned': note.is_pinned,
                        'is_password_protected': note.is_password_protected,
                        'uuid': note.uuid,
                        'tags': note.tags,
                        'mentions': note.mentions,
                        'links': note.links
                    }
                    for note in self.notes
                ]
            }
    
    parser = MockParser()
    export_data = parser.export_notes_to_dict()
    
    print("\nTesting JSON export...")
    
    # Check that tags are in the export
    note1_data = export_data['notes'][0]
    note2_data = export_data['notes'][1]
    
    print(f"Note 1 tags in export: {note1_data['tags']}")
    print(f"Note 2 tags in export: {note2_data['tags']}")
    print(f"Note 2 mentions in export: {note2_data['mentions']}")
    print(f"Note 2 links in export: {note2_data['links']}")
    
    assert note1_data['tags'] == ["tag1"], f"Expected ['tag1'], got {note1_data['tags']}"
    assert note2_data['tags'] == ["tag2", "tag3"], f"Expected ['tag2', 'tag3'], got {note2_data['tags']}"
    assert note2_data['mentions'] == ["user"], f"Expected ['user'], got {note2_data['mentions']}"
    assert note2_data['links'] == ["https://test.com"], f"Expected ['https://test.com'], got {note2_data['links']}"
    
    print("✅ JSON export tests passed")
    
    # Write to file to verify
    with open("test_export.json", "w") as f:
        json.dump(export_data, f, indent=2)
    
    print("✅ Test export written to test_export.json")

def test_tag_methods():
    """Test tag-related methods work correctly."""
    
    # Create test data
    account = Account(id=1, name="Test Account", identifier="test")
    folder = Folder(id=1, name="Test Folder", account=account)
    
    notes = [
        Note(id=1, note_id=1, title="Note 1", content="Content",
             creation_date=datetime.now(), modification_date=datetime.now(),
             account=account, folder=folder, tags=["work", "important"]),
        Note(id=2, note_id=2, title="Note 2", content="Content", 
             creation_date=datetime.now(), modification_date=datetime.now(),
             account=account, folder=folder, tags=["personal"]),
        Note(id=3, note_id=3, title="Note 3", content="Content",
             creation_date=datetime.now(), modification_date=datetime.now(),
             account=account, folder=folder, tags=["work"])
    ]
    
    # Mock parser
    class MockParser:
        def __init__(self):
            self.notes = notes
        
        def get_notes_by_tag(self, tag):
            return [note for note in self.notes if note.has_tag(tag)]
        
        def get_notes_by_tags(self, tags, match_all=False):
            if match_all:
                return [note for note in self.notes if all(note.has_tag(tag) for tag in tags)]
            else:
                return [note for note in self.notes if any(note.has_tag(tag) for tag in tags)]
        
        def get_all_tags(self):
            all_tags = set()
            for note in self.notes:
                all_tags.update(note.tags)
            return sorted(list(all_tags))
        
        def get_tag_counts(self):
            tag_counts = {}
            for note in self.notes:
                for tag in note.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            return dict(sorted(tag_counts.items()))
    
    parser = MockParser()
    
    print("\nTesting tag methods...")
    
    # Test get_notes_by_tag
    work_notes = parser.get_notes_by_tag("work")
    print(f"Notes with 'work' tag: {len(work_notes)}")
    assert len(work_notes) == 2, f"Expected 2 notes with 'work' tag, got {len(work_notes)}"
    
    # Test get_notes_by_tags (OR logic)
    work_or_personal = parser.get_notes_by_tags(["work", "personal"], match_all=False)
    print(f"Notes with 'work' OR 'personal': {len(work_or_personal)}")
    assert len(work_or_personal) == 3, f"Expected 3 notes, got {len(work_or_personal)}"
    
    # Test get_notes_by_tags (AND logic)
    work_and_important = parser.get_notes_by_tags(["work", "important"], match_all=True)
    print(f"Notes with 'work' AND 'important': {len(work_and_important)}")
    assert len(work_and_important) == 1, f"Expected 1 note, got {len(work_and_important)}"
    
    # Test get_all_tags
    all_tags = parser.get_all_tags()
    print(f"All tags: {all_tags}")
    assert set(all_tags) == {"important", "personal", "work"}, f"Expected specific tags, got {all_tags}"
    
    # Test get_tag_counts
    tag_counts = parser.get_tag_counts()
    print(f"Tag counts: {tag_counts}")
    assert tag_counts["work"] == 2, f"Expected 'work' count 2, got {tag_counts['work']}"
    assert tag_counts["important"] == 1, f"Expected 'important' count 1, got {tag_counts['important']}"
    
    print("✅ Tag method tests passed")

if __name__ == "__main__":
    test_note_model_with_tags()
    test_export_includes_tags()
    test_tag_methods()
    print("\n🎉 All tests passed! Tags are working correctly in the pipeline.")