#!/usr/bin/env python3
"""
Test script to verify embedded object extraction works with actual Apple Notes data.
"""

import sqlite3
from src.apple_notes_parser.embedded_objects import EmbeddedObjectExtractor

def test_embedded_object_extraction():
    """Test embedded object extraction with mock database."""
    
    # Create an in-memory SQLite database for testing
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    try:
        # Create the table structure similar to Apple Notes
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE ZICCLOUDSYNCINGOBJECT (
                Z_PK INTEGER PRIMARY KEY,
                ZNOTE INTEGER,
                ZTYPEUTI1 TEXT,
                ZALTTEXT TEXT,
                ZTOKENCONTENTIDENTIFIER TEXT
            )
        """)
        
        # Insert mock hashtag data
        cursor.execute("""
            INSERT INTO ZICCLOUDSYNCINGOBJECT 
            (Z_PK, ZNOTE, ZTYPEUTI1, ZALTTEXT, ZTOKENCONTENTIDENTIFIER)
            VALUES 
            (1, 101, 'com.apple.notes.inlinetextattachment.hashtag', '#work', 'work'),
            (2, 101, 'com.apple.notes.inlinetextattachment.hashtag', '#important', 'important'),
            (3, 102, 'com.apple.notes.inlinetextattachment.hashtag', '#personal', 'personal'),
            (4, 101, 'com.apple.notes.inlinetextattachment.mention', '@john', 'john'),
            (5, 102, 'com.apple.notes.inlinetextattachment.link', 'https://example.com', 'https://example.com')
        """)
        
        conn.commit()
        
        # Test the extractor
        extractor = EmbeddedObjectExtractor(conn, ios_version=15)
        
        print("Testing embedded object extraction...")
        
        # Test note 101 (should have work, important tags and john mention)
        objects_101 = extractor.get_embedded_objects_for_note(101)
        print(f"Note 101 objects: {objects_101}")
        
        expected_hashtags_101 = {'work', 'important'}
        actual_hashtags_101 = set(objects_101['hashtags'])
        assert actual_hashtags_101 == expected_hashtags_101, f"Expected {expected_hashtags_101}, got {actual_hashtags_101}"
        
        expected_mentions_101 = {'john'}
        actual_mentions_101 = set(objects_101['mentions'])
        assert actual_mentions_101 == expected_mentions_101, f"Expected {expected_mentions_101}, got {actual_mentions_101}"
        
        print("✅ Note 101 extraction passed")
        
        # Test note 102 (should have personal tag and example.com link)
        objects_102 = extractor.get_embedded_objects_for_note(102)
        print(f"Note 102 objects: {objects_102}")
        
        expected_hashtags_102 = {'personal'}
        actual_hashtags_102 = set(objects_102['hashtags'])
        assert actual_hashtags_102 == expected_hashtags_102, f"Expected {expected_hashtags_102}, got {actual_hashtags_102}"
        
        expected_links_102 = {'https://example.com'}
        actual_links_102 = set(objects_102['links'])
        assert actual_links_102 == expected_links_102, f"Expected {expected_links_102}, got {actual_links_102}"
        
        print("✅ Note 102 extraction passed")
        
        # Test get_all_hashtags
        all_hashtags = extractor.get_all_hashtags()
        print(f"All hashtags: {all_hashtags}")
        
        expected_all_hashtags = {'important', 'personal', 'work'}
        actual_all_hashtags = set(all_hashtags)
        assert actual_all_hashtags == expected_all_hashtags, f"Expected {expected_all_hashtags}, got {actual_all_hashtags}"
        
        print("✅ get_all_hashtags passed")
        
        # Test get_hashtag_counts
        hashtag_counts = extractor.get_hashtag_counts()
        print(f"Hashtag counts: {hashtag_counts}")
        
        expected_counts = {'work': 1, 'important': 1, 'personal': 1}
        assert hashtag_counts == expected_counts, f"Expected {expected_counts}, got {hashtag_counts}"
        
        print("✅ get_hashtag_counts passed")
        
        # Test get_notes_with_hashtag
        work_notes = extractor.get_notes_with_hashtag('work')
        print(f"Notes with 'work' hashtag: {work_notes}")
        
        assert work_notes == [101], f"Expected [101], got {work_notes}"
        
        print("✅ get_notes_with_hashtag passed")
        
        print("\n🎉 All embedded object extraction tests passed!")
        
    finally:
        conn.close()

def test_ios_version_fallback():
    """Test that iOS < 15 returns empty results gracefully."""
    
    conn = sqlite3.connect(":memory:")
    
    try:
        extractor = EmbeddedObjectExtractor(conn, ios_version=14)
        
        # Should return empty results for iOS < 15
        objects = extractor.get_embedded_objects_for_note(1)
        assert objects == {'hashtags': [], 'mentions': [], 'links': []}
        
        all_hashtags = extractor.get_all_hashtags()
        assert all_hashtags == []
        
        hashtag_counts = extractor.get_hashtag_counts()
        assert hashtag_counts == {}
        
        print("✅ iOS version fallback test passed")
        
    finally:
        conn.close()

if __name__ == "__main__":
    test_embedded_object_extraction()
    test_ios_version_fallback()
    print("\n✅ All tests completed successfully!")