#!/usr/bin/env python3
"""
Test just folder hierarchy without notes.
"""

import json
from src.apple_notes_parser.database import AppleNotesDatabase

def test_folder_only():
    """Test folder hierarchy only."""
    db_path = "TestNoteStore.sqlite"
    
    print("=== FOLDER-ONLY HIERARCHY TESTING ===\n")
    
    with AppleNotesDatabase(db_path) as db:
        # Get accounts first
        accounts_list = db.get_accounts()
        accounts_dict = {acc.id: acc for acc in accounts_list}
        print(f"Accounts: {[acc.name for acc in accounts_list]}")
        
        # Get folders
        folders_list = db.get_folders(accounts_dict)
        folders_dict = {folder.id: folder for folder in folders_list}
        
        print(f"\n1. Raw folder data:")
        for folder in sorted(folders_list, key=lambda f: f.id):
            parent_info = f" (parent: {folder.parent_id})" if folder.parent_id else " (root)"
            print(f"   ID {folder.id}: {folder.name}{parent_info}")
        
        print(f"\n2. Folder paths:")
        for folder in sorted(folders_list, key=lambda f: f.id):
            path = folder.get_path(folders_dict)
            print(f"   {folder.name}: {path}")
        
        print(f"\n3. Testing specific methods:")
        
        # Find specific folders
        cocktails_folder = None
        classic_folder = None
        
        for folder in folders_list:
            if folder.name == "Cocktails":
                cocktails_folder = folder
            elif folder.name == "Classic":
                classic_folder = folder
        
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
        
        print(f"\n4. Folder summary:")
        print(f"   Total folders: {len(folders_list)}")
        root_folders = [f for f in folders_list if f.is_root()]
        print(f"   Root folders: {len(root_folders)} - {[f.name for f in root_folders]}")
        
        # Create export structure for folders only
        export_data = {
            'folders': [
                {
                    'id': folder.id,
                    'name': folder.name,
                    'parent_id': folder.parent_id,
                    'path': folder.get_path(folders_dict)
                }
                for folder in folders_list
            ]
        }
        
        with open("folder_only_test.json", "w") as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n✅ Saved folder-only test to folder_only_test.json")

if __name__ == "__main__":
    test_folder_only()