#!/usr/bin/env python3
"""
Test content export with different settings.
"""

import json
from src.apple_notes_parser import AppleNotesParser

def test_content_export():
    """Test content export with include_content True vs False."""
    db_path = "/Users/rhet/code/applenotes/apple-notes-parser/NoteStore.sqlite"
    
    parser = AppleNotesParser(db_path)
    parser.load_data()
    
    print("=== CONTENT EXPORT TESTING ===\n")
    
    # Find Sidecar note
    sidecar_notes = [n for n in parser.notes if n.title and 'sidecar' in n.title.lower()]
    
    if sidecar_notes:
        sidecar = sidecar_notes[0]
        print(f"Sidecar note in memory:")
        print(f"  Title: {sidecar.title}")
        print(f"  Content: {repr(sidecar.content)}")
        print(f"  Content length: {len(sidecar.content) if sidecar.content else 0}")
        
        # Test export with content
        print(f"\n--- Export with include_content=True ---")
        export_with_content = parser.export_notes_to_dict(include_content=True)
        sidecar_with_content = [n for n in export_with_content['notes'] if n['title'] == 'Sidecar'][0]
        print(f"Content: {repr(sidecar_with_content['content'])}")
        print(f"Content is None: {sidecar_with_content['content'] is None}")
        
        # Test export without content
        print(f"\n--- Export with include_content=False ---")
        export_without_content = parser.export_notes_to_dict(include_content=False)
        sidecar_without_content = [n for n in export_without_content['notes'] if n['title'] == 'Sidecar'][0]
        print(f"Content: {repr(sidecar_without_content['content'])}")
        print(f"Content is None: {sidecar_without_content['content'] is None}")
        
        # Save both exports
        with open("sidecar_with_content.json", "w") as f:
            json.dump([sidecar_with_content], f, indent=2)
        
        with open("sidecar_without_content.json", "w") as f:
            json.dump([sidecar_without_content], f, indent=2)
        
        print(f"\n✅ Exported samples to sidecar_with_content.json and sidecar_without_content.json")
        
        # Also test a few other notes
        print(f"\n--- Testing other notes for content ---")
        for i, note in enumerate(parser.notes[:3]):
            if note.title:
                print(f"{i+1}. '{note.title}': {len(note.content) if note.content else 0} chars")
                
                # Check in export
                export_note = [n for n in export_with_content['notes'] if n['id'] == note.id][0]
                export_content_len = len(export_note['content']) if export_note['content'] else 0
                print(f"   In export: {export_content_len} chars")
                
                if (note.content is None) != (export_note['content'] is None):
                    print(f"   ❌ MISMATCH: Memory={note.content is None}, Export={export_note['content'] is None}")

if __name__ == "__main__":
    test_content_export()