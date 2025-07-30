"""Protobuf parsing utilities for Apple Notes data."""

import gzip
import re
from typing import Optional, List, Dict, Any
from google.protobuf.message import DecodeError

from .notestore_pb2 import NoteStoreProto, MergableDataProto
from .exceptions import ProtobufError


class ProtobufParser:
    """Handles parsing of Apple Notes protobuf data."""
    
    @staticmethod
    def extract_note_text(zdata: bytes) -> Optional[str]:
        """Extract plain text from compressed note data."""
        if not zdata:
            return None
        
        try:
            # Check if data is gzipped
            if len(zdata) > 2 and zdata[0:2] == b'\x1f\x8b':
                # Decompress gzipped data
                decompressed = gzip.decompress(zdata)
                
                # Parse as protobuf
                try:
                    note_store = NoteStoreProto()
                    note_store.ParseFromString(decompressed)
                    
                    if note_store.HasField('document') and note_store.document.HasField('note'):
                        return note_store.document.note.note_text
                    
                except DecodeError:
                    # If protobuf parsing fails, try to extract text manually
                    return ProtobufParser._extract_text_fallback(decompressed)
            else:
                # Try to decode as plain text (legacy format)
                try:
                    return zdata.decode('utf-8', errors='ignore')
                except:
                    return None
                    
        except Exception as e:
            raise ProtobufError(f"Failed to extract note text: {e}")
    
    @staticmethod
    def _extract_text_fallback(data: bytes) -> Optional[str]:
        """Fallback method to extract text when protobuf parsing fails."""
        try:
            # Try to find readable text in the binary data
            text = data.decode('utf-8', errors='ignore')
            # Clean up the text by removing non-printable characters
            text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            return text if text else None
        except:
            return None
    
    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """Extract hashtags from note text."""
        if not text:
            return []
        
        # Pattern to match hashtags
        hashtag_pattern = r'#(\w+)'
        matches = re.findall(hashtag_pattern, text)
        return list(set(matches))  # Remove duplicates
    
    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """Extract @mentions from note text."""
        if not text:
            return []
        
        # Pattern to match @mentions
        mention_pattern = r'@(\w+)'
        matches = re.findall(mention_pattern, text)
        return list(set(matches))  # Remove duplicates
    
    @staticmethod
    def extract_links(text: str) -> List[str]:
        """Extract URLs from note text."""
        if not text:
            return []
        
        # Pattern to match URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,!?;:)]'
        matches = re.findall(url_pattern, text)
        return list(set(matches))  # Remove duplicates
    
    @staticmethod
    def parse_note_structure(zdata: bytes) -> Dict[str, Any]:
        """Parse note structure and extract metadata."""
        if not zdata:
            return {}
        
        try:
            # Check if data is gzipped
            if len(zdata) > 2 and zdata[0:2] == b'\x1f\x8b':
                decompressed = gzip.decompress(zdata)
                
                try:
                    note_store = NoteStoreProto()
                    note_store.ParseFromString(decompressed)
                    
                    result = {
                        'has_document': note_store.HasField('document'),
                        'text': None,
                        'attribute_runs': [],
                        'attachments': [],
                        'hashtags': [],
                        'mentions': [],
                        'links': []
                    }
                    
                    if note_store.HasField('document') and note_store.document.HasField('note'):
                        note = note_store.document.note
                        result['text'] = note.note_text
                        
                        # Extract hashtags, mentions, and links
                        if note.note_text:
                            result['hashtags'] = ProtobufParser.extract_hashtags(note.note_text)
                            result['mentions'] = ProtobufParser.extract_mentions(note.note_text)
                            result['links'] = ProtobufParser.extract_links(note.note_text)
                        
                        # Process attribute runs (formatting information)
                        for i, attr_run in enumerate(note.attribute_run):
                            run_info = {
                                'index': i,
                                'length': attr_run.length if attr_run.HasField('length') else 0,
                                'has_attachment': attr_run.HasField('attachment_info'),
                                'has_link': attr_run.HasField('link'),
                                'has_font': attr_run.HasField('font'),
                                'has_paragraph_style': attr_run.HasField('paragraph_style')
                            }
                            
                            if attr_run.HasField('attachment_info'):
                                attachment = {
                                    'identifier': attr_run.attachment_info.attachment_identifier,
                                    'type_uti': attr_run.attachment_info.type_uti
                                }
                                result['attachments'].append(attachment)
                            
                            result['attribute_runs'].append(run_info)
                    
                    return result
                    
                except DecodeError:
                    # If protobuf parsing fails, return basic structure
                    text = ProtobufParser._extract_text_fallback(decompressed)
                    return {
                        'has_document': False,
                        'text': text,
                        'attribute_runs': [],
                        'attachments': [],
                        'hashtags': ProtobufParser.extract_hashtags(text) if text else [],
                        'mentions': ProtobufParser.extract_mentions(text) if text else [],
                        'links': ProtobufParser.extract_links(text) if text else []
                    }
            else:
                # Legacy format
                try:
                    text = zdata.decode('utf-8', errors='ignore')
                    return {
                        'has_document': False,
                        'text': text,
                        'attribute_runs': [],
                        'attachments': [],
                        'hashtags': ProtobufParser.extract_hashtags(text),
                        'mentions': ProtobufParser.extract_mentions(text),
                        'links': ProtobufParser.extract_links(text)
                    }
                except:
                    return {}
                    
        except Exception as e:
            raise ProtobufError(f"Failed to parse note structure: {e}")
    
    @staticmethod
    def is_gzipped(data: bytes) -> bool:
        """Check if data is gzip compressed."""
        return len(data) > 2 and data[0:2] == b'\x1f\x8b'