#!/usr/bin/env python3
"""
Test AppleScript ID functionality.
"""

import json
from src.apple_notes_parser import AppleNotesParser

def test_applescript_id():
    """Test AppleScript ID construction."""
    db_path = "/Users/rhet/code/applenotes/apple-notes-parser/NoteStore.sqlite"
    
    parser = AppleNotesParser(db_path)
    parser.load_data()
    
    print("=== APPLESCRIPT ID TESTING ===\n")
    
    # Find Sidecar note
    sidecar_notes = [n for n in parser.notes if n.title and 'sidecar' in n.title.lower()]
    
    if sidecar_notes:
        sidecar = sidecar_notes[0]
        print(f"Sidecar note:")
        print(f"  Title: {sidecar.title}")
        print(f"  Database UUID: {sidecar.uuid}")
        print(f"  AppleScript ID: {sidecar.applescript_id}")
        print(f"  Z_PK (note_id): {sidecar.note_id}")
        
        # Expected AppleScript ID from user: x-coredata://5A2C18B7-767B-41A9-BF71-E4E966775D32/ICNote/p4840
        expected_applescript_id = "x-coredata://5A2C18B7-767B-41A9-BF71-E4E966775D32/ICNote/p4840"
        
        print(f"\n  Expected AppleScript ID: {expected_applescript_id}")
        print(f"  Actual AppleScript ID:   {sidecar.applescript_id}")
        print(f"  AppleScript IDs match: {sidecar.applescript_id == expected_applescript_id}")
        
        if sidecar.applescript_id:
            # Parse the AppleScript ID to extract components
            parts = sidecar.applescript_id.split('/')
            if len(parts) >= 4:
                z_uuid_from_id = parts[2]
                z_pk_from_id = parts[3][1:]  # Remove 'p' prefix
                print(f"\n  Components from AppleScript ID:")
                print(f"    Z_UUID: {z_uuid_from_id}")
                print(f"    Z_PK: {z_pk_from_id}")
                print(f"    Z_PK matches note_id: {z_pk_from_id == str(sidecar.note_id)}")
    
    # Test a few other notes
    print(f"\n--- Testing other notes for AppleScript ID ---")
    for i, note in enumerate(parser.notes[:5]):
        if note.title:
            print(f"{i+1}. '{note.title}' (Z_PK: {note.note_id})")
            print(f"   AppleScript ID: {note.applescript_id}")
    
    # Test in JSON export
    print(f"\n--- Testing AppleScript ID in JSON export ---")
    export_data = parser.export_notes_to_dict(include_content=False)
    
    if sidecar_notes:
        sidecar_export = [n for n in export_data['notes'] if n['title'] == 'Sidecar'][0]
        print(f"Sidecar in JSON export:")
        print(f"  AppleScript ID: {sidecar_export['applescript_id']}")
        print(f"  Matches in-memory: {sidecar_export['applescript_id'] == sidecar.applescript_id}")
    
    # Save sample export to file
    sample_notes = [n for n in export_data['notes'] if n['applescript_id']][:3]
    with open("applescript_id_sample.json", "w") as f:
        json.dump(sample_notes, f, indent=2)
    
    print(f"\n✅ Saved sample notes with AppleScript IDs to applescript_id_sample.json")

if __name__ == "__main__":
    test_applescript_id()