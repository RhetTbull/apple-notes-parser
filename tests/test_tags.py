#!/usr/bin/env python3
"""
Test script to verify tag parsing is working correctly.
"""

from src.apple_notes_parser.protobuf_parser import ProtobufParser

def test_hashtag_extraction():
    """Test hashtag extraction from sample text."""
    
    # Test cases
    test_cases = [
        ("This is a note with #work and #important tags", ["work", "important"]),
        ("Meeting notes #project #urgent", ["project", "urgent"]),
        ("No tags here", []),
        ("#single", ["single"]),
        ("Multiple #test #test #different", ["test", "different"]),  # Should deduplicate
        ("Mixed case #Work #IMPORTANT #work", ["Work", "IMPORTANT", "work"]),  # Case sensitive
        ("Edge cases #123 #tag-with-dash #tag_with_underscore", ["123", "tag", "tag_with_underscore"]),
    ]
    
    print("Testing hashtag extraction...")
    for text, expected in test_cases:
        result = ProtobufParser.extract_hashtags(text)
        result_set = set(result)
        expected_set = set(expected)
        
        if result_set == expected_set:
            print(f"✅ PASS: '{text}' -> {result}")
        else:
            print(f"❌ FAIL: '{text}' -> Expected {expected}, got {result}")

def test_mention_extraction():
    """Test @mention extraction from sample text."""
    
    test_cases = [
        ("Meeting with @john and @mary", ["john", "mary"]),
        ("No mentions here", []),
        ("@single", ["single"]),
        ("CC: @team @manager", ["team", "manager"]),
    ]
    
    print("\nTesting mention extraction...")
    for text, expected in test_cases:
        result = ProtobufParser.extract_mentions(text)
        result_set = set(result)
        expected_set = set(expected)
        
        if result_set == expected_set:
            print(f"✅ PASS: '{text}' -> {result}")
        else:
            print(f"❌ FAIL: '{text}' -> Expected {expected}, got {result}")

def test_link_extraction():
    """Test URL extraction from sample text."""
    
    test_cases = [
        ("Check out https://example.com", ["https://example.com"]),
        ("Multiple links: https://google.com and http://apple.com", ["https://google.com", "http://apple.com"]),
        ("No links here", []),
    ]
    
    print("\nTesting link extraction...")
    for text, expected in test_cases:
        result = ProtobufParser.extract_links(text)
        result_set = set(result)
        expected_set = set(expected)
        
        if result_set == expected_set:
            print(f"✅ PASS: '{text}' -> {result}")
        else:
            print(f"❌ FAIL: '{text}' -> Expected {expected}, got {result}")

def test_note_structure_parsing():
    """Test parsing note structure with mock data."""
    
    # Test with simple text data (non-gzipped)
    simple_text = b"This is a test note with #work and #important tags @john"
    
    print("\nTesting note structure parsing with simple text...")
    try:
        result = ProtobufParser.parse_note_structure(simple_text)
        print(f"Result: {result}")
        
        if result.get('hashtags') == ['work', 'important']:
            print("✅ PASS: Hashtags extracted correctly from simple text")
        else:
            print(f"❌ FAIL: Expected hashtags ['work', 'important'], got {result.get('hashtags')}")
            
        if result.get('mentions') == ['john']:
            print("✅ PASS: Mentions extracted correctly from simple text")
        else:
            print(f"❌ FAIL: Expected mentions ['john'], got {result.get('mentions')}")
            
    except Exception as e:
        print(f"Error in note structure parsing: {e}")

if __name__ == "__main__":
    test_hashtag_extraction()
    test_mention_extraction()  
    test_link_extraction()
    test_note_structure_parsing()