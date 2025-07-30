"""Embedded objects extraction for Apple Notes."""

from __future__ import annotations

import sqlite3
from typing import Any
from .exceptions import DatabaseError


class EmbeddedObjectExtractor:
    """Extracts embedded objects (hashtags, mentions, etc.) from Apple Notes database."""
    
    # UTI constants for different embedded object types
    UTI_HASHTAG = "com.apple.notes.inlinetextattachment.hashtag"
    UTI_MENTION = "com.apple.notes.inlinetextattachment.mention"
    UTI_LINK = "com.apple.notes.inlinetextattachment.link"
    
    def __init__(self, connection: sqlite3.Connection, ios_version: int):
        """Initialize with database connection and iOS version."""
        self.connection = connection
        self.ios_version = ios_version
    
    def get_embedded_objects_for_note(self, note_id: int) -> dict[str, list[str]]:
        """Get all embedded objects for a specific note."""
        if self.ios_version < 15:
            # Hashtags and mentions were added in iOS 15
            return {'hashtags': [], 'mentions': [], 'links': []}
        
        try:
            cursor = self.connection.cursor()
            
            # Query for embedded objects
            # The relationship varies by iOS version - try multiple fields
            # ZNOTE1 seems to be used for hashtags in newer versions
            query = """
            SELECT 
                obj.ZTYPEUTI1,
                obj.ZALTTEXT,
                obj.ZTOKENCONTENTIDENTIFIER
            FROM ZICCLOUDSYNCINGOBJECT obj
            WHERE (obj.ZNOTE = ? OR obj.ZNOTE1 = ? OR obj.ZATTACHMENT = ?)
                AND obj.ZTYPEUTI1 IS NOT NULL
                AND obj.ZTYPEUTI1 IN (?, ?, ?)
            """
            
            cursor.execute(query, [
                note_id, note_id, note_id,  # Try multiple relationship fields
                self.UTI_HASHTAG, 
                self.UTI_MENTION, 
                self.UTI_LINK
            ])
            
            hashtags = []
            mentions = []
            links = []
            
            for row in cursor.fetchall():
                uti = row[0]
                alt_text = row[1]
                token_identifier = row[2]
                
                if uti == self.UTI_HASHTAG and alt_text:
                    # Hashtag text is in alt_text, remove # if present
                    tag = alt_text.lstrip('#')
                    if tag:
                        hashtags.append(tag)
                
                elif uti == self.UTI_MENTION and alt_text:
                    # Mention text is in alt_text, remove @ if present
                    mention = alt_text.lstrip('@')
                    if mention:
                        mentions.append(mention)
                
                elif uti == self.UTI_LINK and (alt_text or token_identifier):
                    # Link could be in either field
                    link = alt_text or token_identifier
                    if link and link.startswith(('http://', 'https://')):
                        links.append(link)
            
            return {
                'hashtags': list(set(hashtags)),  # Remove duplicates
                'mentions': list(set(mentions)),
                'links': list(set(links))
            }
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to extract embedded objects for note {note_id}: {e}")
    
    def get_all_hashtags(self) -> list[str]:
        """Get all unique hashtags across all notes."""
        if self.ios_version < 15:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT DISTINCT ZALTTEXT
            FROM ZICCLOUDSYNCINGOBJECT 
            WHERE ZTYPEUTI1 = ? 
                AND ZALTTEXT IS NOT NULL
            """
            
            cursor.execute(query, [self.UTI_HASHTAG])
            
            hashtags = []
            for row in cursor.fetchall():
                alt_text = row[0]
                if alt_text:
                    tag = alt_text.lstrip('#')
                    if tag:
                        hashtags.append(tag)
            
            return sorted(list(set(hashtags)))
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get all hashtags: {e}")
    
    def get_all_mentions(self) -> list[str]:
        """Get all unique mentions across all notes."""
        if self.ios_version < 15:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT DISTINCT ZALTTEXT
            FROM ZICCLOUDSYNCINGOBJECT 
            WHERE ZTYPEUTI1 = ? 
                AND ZALTTEXT IS NOT NULL
            """
            
            cursor.execute(query, [self.UTI_MENTION])
            
            mentions = []
            for row in cursor.fetchall():
                alt_text = row[0]
                if alt_text:
                    mention = alt_text.lstrip('@')
                    if mention:
                        mentions.append(mention)
            
            return sorted(list(set(mentions)))
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get all mentions: {e}")
    
    def get_notes_with_hashtag(self, hashtag: str) -> list[int]:
        """Get all note IDs that have a specific hashtag."""
        if self.ios_version < 15:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            # Look for hashtag with or without # prefix
            hashtag_patterns = [hashtag, f"#{hashtag}"]
            
            query = """
            SELECT DISTINCT COALESCE(ZNOTE, ZNOTE1, ZATTACHMENT) as note_id
            FROM ZICCLOUDSYNCINGOBJECT 
            WHERE ZTYPEUTI1 = ? 
                AND ZALTTEXT IN (?, ?)
                AND (ZNOTE IS NOT NULL OR ZNOTE1 IS NOT NULL OR ZATTACHMENT IS NOT NULL)
            """
            
            cursor.execute(query, [self.UTI_HASHTAG] + hashtag_patterns)
            
            return [row[0] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get notes with hashtag '{hashtag}': {e}")
    
    def get_hashtag_counts(self) -> dict[str, int]:
        """Get count of notes for each hashtag."""
        if self.ios_version < 15:
            return {}
        
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT ZALTTEXT, COUNT(DISTINCT COALESCE(ZNOTE, ZNOTE1, ZATTACHMENT)) as note_count
            FROM ZICCLOUDSYNCINGOBJECT 
            WHERE ZTYPEUTI1 = ? 
                AND ZALTTEXT IS NOT NULL
                AND (ZNOTE IS NOT NULL OR ZNOTE1 IS NOT NULL OR ZATTACHMENT IS NOT NULL)
            GROUP BY ZALTTEXT
            ORDER BY ZALTTEXT
            """
            
            cursor.execute(query, [self.UTI_HASHTAG])
            
            hashtag_counts = {}
            for row in cursor.fetchall():
                alt_text = row[0]
                count = row[1]
                if alt_text:
                    tag = alt_text.lstrip('#')
                    if tag:
                        hashtag_counts[tag] = count
            
            return hashtag_counts
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get hashtag counts: {e}")