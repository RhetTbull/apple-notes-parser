#!/usr/bin/env python3
"""
Test the fixed hashtag extraction.
"""

from src.apple_notes_parser import AppleNotesParser

def test_sidecar_note():
    """Test that the Sidecar note now has the #totry tag."""
    db_path = "/Users/rhet/code/applenotes/apple-notes-parser/NoteStore.sqlite"
    
    print("Testing fixed hashtag extraction...")
    
    parser = AppleNotesParser(db_path)
    parser.load_data()
    
    # Find the Sidecar note
    sidecar_notes = [n for n in parser.notes if n.title and 'sidecar' in n.title.lower()]
    
    if sidecar_notes:
        sidecar = sidecar_notes[0]
        print(f"✅ Found Sidecar note:")
        print(f"  Title: {sidecar.title}")
        print(f"  UUID: {sidecar.uuid}")
        print(f"  Folder: {sidecar.folder.name}")
        print(f"  Tags: {sidecar.tags}")
        print(f"  Mentions: {sidecar.mentions}")
        print(f"  Content preview: {sidecar.content[:100] if sidecar.content else 'None'}...")
        
        if 'totry' in sidecar.tags:
            print("🎉 SUCCESS: #totry tag found!")
        else:
            print("❌ PROBLEM: #totry tag still not found")
    else:
        print("❌ Sidecar note not found")
    
    # Test overall tag functionality
    print(f"\nOverall tag statistics:")
    all_tags = parser.get_all_tags()
    print(f"Total unique tags: {len(all_tags)}")
    print(f"Sample tags: {all_tags[:10]}")
    
    tag_counts = parser.get_tag_counts()
    print(f"Tag counts (first 5): {dict(list(tag_counts.items())[:5])}")
    
    # Test totry tag specifically
    totry_notes = parser.get_notes_by_tag("totry")
    print(f"Notes with #totry tag: {len(totry_notes)}")
    for note in totry_notes[:3]:  # Show first 3
        print(f"  - '{note.title}' in {note.folder.name}")
    
    # Export and check JSON contains tags
    print(f"\nTesting JSON export...")
    export_data = parser.export_notes_to_dict(include_content=False)
    
    notes_with_tags = [n for n in export_data['notes'] if n['tags']]
    print(f"Notes with tags in export: {len(notes_with_tags)}")
    
    # Look for Sidecar specifically in export
    sidecar_in_export = [n for n in export_data['notes'] if n['title'] == 'Sidecar']
    if sidecar_in_export:
        sidecar_export = sidecar_in_export[0]
        print(f"Sidecar in export: tags={sidecar_export['tags']}")
        if 'totry' in sidecar_export['tags']:
            print("🎉 SUCCESS: #totry tag found in JSON export!")
        else:
            print("❌ PROBLEM: #totry tag not in JSON export")
    
    # Save a sample of tagged notes to file
    sample_tagged_notes = [n for n in export_data['notes'] if n['tags']][:5]
    if sample_tagged_notes:
        import json
        with open("sample_tagged_notes.json", "w") as f:
            json.dump(sample_tagged_notes, f, indent=2)
        print("✅ Sample tagged notes saved to sample_tagged_notes.json")

if __name__ == "__main__":
    test_sidecar_note()