"""
Apple Notes Parser

A Python library for reading and parsing Apple Notes SQLite databases.
Extracts all data from Notes SQLite stores including tags and note filtering.
"""

from .exceptions import AppleNotesParserError
from .models import Account, Attachment, Folder, Note
from .parser import AppleNotesParser

__version__ = "0.1.0"
__all__ = [
    "AppleNotesParser",
    "Note",
    "Folder",
    "Account",
    "Attachment",
    "AppleNotesParserError",
]
