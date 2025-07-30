#!/usr/bin/env python3
"""
Test folder hierarchy and path functionality.
"""

import json
from src.apple_notes_parser import AppleNotesParser

def test_folder_hierarchy():
    """Test folder hierarchy and path construction."""
    db_path = "TestNoteStore.sqlite"
    
    parser = AppleNotesParser(db_path)
    parser.load_data()
    
    print("=== FOLDER HIERARCHY TESTING ===\n")
    
    # Test folder paths
    print("1. Folder hierarchy:")
    folders_dict = parser.folders_dict
    
    for folder in sorted(parser.folders, key=lambda f: f.id):
        path = folder.get_path(folders_dict)
        parent_info = f" (parent: {folder.parent_id})" if folder.parent_id else " (root)"
        print(f"   {folder.name}: {path}{parent_info}")
    
    # Test specific paths
    print(f"\n2. Testing specific folder paths:")
    
    # Find specific folders
    cocktails_folder = None
    classic_folder = None
    projects_folder = None
    
    for folder in parser.folders:
        if folder.name == "Cocktails":
            cocktails_folder = folder
        elif folder.name == "Classic":
            classic_folder = folder
        elif folder.name == "Projects":
            projects_folder = folder
    
    if cocktails_folder:
        print(f"   Cocktails path: {cocktails_folder.get_path(folders_dict)}")
        print(f"   Cocktails is root: {cocktails_folder.is_root()}")
        parent = cocktails_folder.get_parent(folders_dict)
        print(f"   Cocktails parent: {parent.name if parent else 'None'}")
    
    if classic_folder:
        print(f"   Classic path: {classic_folder.get_path(folders_dict)}")
        print(f"   Classic is root: {classic_folder.is_root()}")
        parent = classic_folder.get_parent(folders_dict)
        print(f"   Classic parent: {parent.name if parent else 'None'}")
    
    if projects_folder:
        print(f"   Projects path: {projects_folder.get_path(folders_dict)}")
    
    # Test JSON export with folder paths
    print(f"\n3. Testing JSON export with folder paths:")
    export_data = parser.export_notes_to_dict(include_content=False)
    
    print("   Folders in export:")
    for folder in export_data['folders']:
        print(f"     {folder['name']}: {folder['path']} (parent_id: {folder['parent_id']})")
    
    # Save export to file
    with open("folder_hierarchy_test.json", "w") as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✅ Saved folder hierarchy test to folder_hierarchy_test.json")
    
    # Test edge cases
    print(f"\n4. Testing edge cases:")
    
    # Test with empty folders_dict
    if cocktails_folder:
        path_without_dict = cocktails_folder.get_path(None)
        print(f"   Cocktails path without dict: {path_without_dict}")
    
    print(f"\n5. Folder summary:")
    print(f"   Total folders: {len(parser.folders)}")
    root_folders = [f for f in parser.folders if f.is_root()]
    print(f"   Root folders: {len(root_folders)} - {[f.name for f in root_folders]}")

if __name__ == "__main__":
    test_folder_hierarchy()