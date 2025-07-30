#!/usr/bin/env python3
"""
Test content export with default parameters.
"""

import json
from src.apple_notes_parser import AppleNotesParser

def test_content_defaults():
    """Test content export with default parameters."""
    db_path = "/Users/rhet/code/applenotes/apple-notes-parser/NoteStore.sqlite"
    
    parser = AppleNotesParser(db_path)
    parser.load_data()
    
    print("=== TESTING CONTENT EXPORT DEFAULTS ===\n")
    
    # Test 1: Default export (should include content)
    print("1. Default export (no parameters):")
    default_export = parser.export_notes_to_dict()
    sidecar_default = [n for n in default_export['notes'] if n['title'] == 'Sidecar'][0]
    print(f"   Content: {repr(sidecar_default['content'][:50]) if sidecar_default['content'] else 'None'}...")
    print(f"   Content is None: {sidecar_default['content'] is None}")
    
    # Test 2: Explicit True
    print("\n2. Explicit include_content=True:")
    true_export = parser.export_notes_to_dict(include_content=True)
    sidecar_true = [n for n in true_export['notes'] if n['title'] == 'Sidecar'][0]
    print(f"   Content: {repr(sidecar_true['content'][:50]) if sidecar_true['content'] else 'None'}...")
    print(f"   Content is None: {sidecar_true['content'] is None}")
    
    # Test 3: Explicit False
    print("\n3. Explicit include_content=False:")
    false_export = parser.export_notes_to_dict(include_content=False)
    sidecar_false = [n for n in false_export['notes'] if n['title'] == 'Sidecar'][0]
    print(f"   Content: {repr(sidecar_false['content'])}")
    print(f"   Content is None: {sidecar_false['content'] is None}")
    
    # Test 4: Save default export to file
    print("\n4. Saving default export to file...")
    with open("default_export_with_content.json", "w") as f:
        json.dump([sidecar_default], f, indent=2)
    
    print("✅ Saved default export to default_export_with_content.json")
    
    # Test 5: Check consistency
    print(f"\n5. Consistency checks:")
    print(f"   Default == True: {sidecar_default['content'] == sidecar_true['content']}")
    print(f"   False is None: {sidecar_false['content'] is None}")

if __name__ == "__main__":
    test_content_defaults()