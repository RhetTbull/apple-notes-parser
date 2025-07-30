#!/usr/bin/env python3
"""
Integration test to verify the complete tag extraction pipeline.
"""

import sqlite3
import gzip
import json
from datetime import datetime
from src.apple_notes_parser.database import AppleNotesDatabase
from src.apple_notes_parser.parser import AppleNotesParser

def create_mock_notes_database():
    """Create a mock Apple Notes database for testing."""
    
    # Create temporary database file
    db_path = "test_notes.sqlite"
    conn = sqlite3.connect(db_path)
    
    try:
        cursor = conn.cursor()
        
        # Create the main tables (simplified schema)
        cursor.execute("""
            CREATE TABLE ZICCLOUDSYNCINGOBJECT (
                Z_PK INTEGER PRIMARY KEY,
                ZNOTE INTEGER,
                ZTITLE1 TEXT,
                ZTITLE2 TEXT,
                ZNAME TEXT,
                ZIDENTIFIER TEXT,
                ZUSERRECORDNAME TEXT,
                ZOWNER INTEGER,
                ZFOLDER INTEGER,
                ZACCOUNT7 INTEGER,
                ZCREATIONDATE3 REAL,
                ZMODIFICATIONDATE1 REAL,
                ZISPINNED INTEGER,
                ZISPASSWORDPROTECTED INTEGER,
                ZTYPEUTI1 TEXT,
                ZALTTEXT TEXT,
                ZTOKENCONTENTIDENTIFIER TEXT,
                ZSERVERRECORDDATA BLOB
            )
        """)
        
        cursor.execute("""
            CREATE TABLE ZICNOTEDATA (
                Z_PK INTEGER PRIMARY KEY,
                ZNOTE INTEGER,
                ZDATA BLOB
            )
        """)
        
        # Insert mock account
        cursor.execute("""
            INSERT INTO ZICCLOUDSYNCINGOBJECT 
            (Z_PK, ZNAME, ZIDENTIFIER)
            VALUES (1, 'Test Account', 'test-account-id')
        """)
        
        # Insert mock folder  
        cursor.execute("""
            INSERT INTO ZICCLOUDSYNCINGOBJECT 
            (Z_PK, ZTITLE2, ZOWNER, ZIDENTIFIER)
            VALUES (2, 'Test Folder', 1, 'test-folder-id')
        """)
        
        # Add columns to make it look like iOS 15+ to enable hashtag extraction
        cursor.execute("ALTER TABLE ZICCLOUDSYNCINGOBJECT ADD COLUMN ZACCOUNT5 INTEGER")
        cursor.execute("ALTER TABLE ZICCLOUDSYNCINGOBJECT ADD COLUMN ZACCOUNT4 INTEGER")
        cursor.execute("ALTER TABLE ZICCLOUDSYNCINGOBJECT ADD COLUMN ZACCOUNT3 INTEGER")
        cursor.execute("ALTER TABLE ZICCLOUDSYNCINGOBJECT ADD COLUMN ZACCOUNT2 INTEGER")
        
        # Insert mock notes
        current_time = (datetime.now().timestamp() - 978307200)  # Convert to Core Data time
        
        # Note 1: Has hashtags via embedded objects
        cursor.execute("""
            INSERT INTO ZICCLOUDSYNCINGOBJECT 
            (Z_PK, ZTITLE1, ZACCOUNT7, ZACCOUNT4, ZFOLDER, ZCREATIONDATE3, ZMODIFICATIONDATE1, ZISPINNED, ZISPASSWORDPROTECTED)
            VALUES (100, 'Note with hashtags', 1, 1, 2, ?, ?, 0, 0)
        """, (current_time, current_time))
        
        # Note 2: Simple note
        cursor.execute("""
            INSERT INTO ZICCLOUDSYNCINGOBJECT 
            (Z_PK, ZTITLE1, ZACCOUNT7, ZACCOUNT4, ZFOLDER, ZCREATIONDATE3, ZMODIFICATIONDATE1, ZISPINNED, ZISPASSWORDPROTECTED)
            VALUES (101, 'Simple note', 1, 1, 2, ?, ?, 1, 0)
        """, (current_time, current_time))
        
        # Insert note data (simplified - just plain text)
        cursor.execute("""
            INSERT INTO ZICNOTEDATA (Z_PK, ZNOTE, ZDATA)
            VALUES (1, 100, ?)
        """, (b"This is a note with some content about work and projects",))
        
        cursor.execute("""
            INSERT INTO ZICNOTEDATA (Z_PK, ZNOTE, ZDATA)
            VALUES (2, 101, ?)
        """, (b"This is a simple note without any special features",))
        
        # Insert hashtag embedded objects for note 100
        cursor.execute("""
            INSERT INTO ZICCLOUDSYNCINGOBJECT 
            (Z_PK, ZNOTE, ZTYPEUTI1, ZALTTEXT, ZTOKENCONTENTIDENTIFIER)
            VALUES 
            (200, 100, 'com.apple.notes.inlinetextattachment.hashtag', '#work', 'work'),
            (201, 100, 'com.apple.notes.inlinetextattachment.hashtag', '#project', 'project'),
            (202, 100, 'com.apple.notes.inlinetextattachment.mention', '@team', 'team')
        """)
        
        conn.commit()
        return db_path
        
    except Exception as e:
        conn.close()
        raise e

def test_full_integration():
    """Test the complete integration from database to JSON export."""
    
    print("Creating mock database...")
    db_path = create_mock_notes_database()
    
    try:
        print("Testing database connection and iOS version detection...")
        
        # Test direct database access
        with AppleNotesDatabase(db_path) as db:
            ios_version = db.get_ios_version()
            print(f"Detected iOS version: {ios_version}")
            
            accounts = db.get_accounts()
            print(f"Found {len(accounts)} accounts: {[a.name for a in accounts]}")
            
            folders_dict = {account.id: account for account in accounts}
            folders = db.get_folders(folders_dict)
            print(f"Found {len(folders)} folders: {[f.name for f in folders]}")
            
            # Test embedded object extraction
            if db._embedded_extractor:
                all_hashtags = db._embedded_extractor.get_all_hashtags()
                print(f"All hashtags from database: {all_hashtags}")
                
                hashtag_counts = db._embedded_extractor.get_hashtag_counts()
                print(f"Hashtag counts: {hashtag_counts}")
        
        print("\nTesting full parser integration...")
        
        # Test the main parser
        parser = AppleNotesParser(db_path)
        parser.load_data()
        
        print(f"Parser loaded {len(parser.notes)} notes")
        
        # Check if notes have tags
        for note in parser.notes:
            print(f"Note '{note.title}': tags={note.tags}, mentions={note.mentions}")
        
        # Test tag methods
        all_tags = parser.get_all_tags()
        print(f"All tags from parser: {all_tags}")
        
        tag_counts = parser.get_tag_counts()
        print(f"Tag counts from parser: {tag_counts}")
        
        # Test tag filtering
        work_notes = parser.get_notes_by_tag("work")
        print(f"Notes with 'work' tag: {len(work_notes)}")
        
        # Test JSON export
        print("\nTesting JSON export...")
        export_data = parser.export_notes_to_dict(include_content=True)
        
        # Check that tags are in the export
        for note_data in export_data['notes']:
            print(f"Exported note '{note_data['title']}': tags={note_data['tags']}")
        
        # Write to file
        with open("integration_test_export.json", "w") as f:
            json.dump(export_data, f, indent=2)
        
        print("✅ Integration test export written to integration_test_export.json")
        
        # Verify the tags are actually in the exported JSON
        notes_with_tags = [n for n in export_data['notes'] if n['tags']]
        print(f"Notes with tags in export: {len(notes_with_tags)}")
        
        if notes_with_tags:
            print("✅ SUCCESS: Tags are being properly extracted and exported!")
            for note in notes_with_tags:
                print(f"  - '{note['title']}' has tags: {note['tags']}")
        else:
            print("❌ PROBLEM: No tags found in exported data")
        
        print("\n🎉 Full integration test completed!")
        
    finally:
        # Clean up
        import os
        try:
            os.remove(db_path)
            print("Cleaned up test database")
        except:
            pass

if __name__ == "__main__":
    test_full_integration()