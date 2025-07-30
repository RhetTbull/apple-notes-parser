"""
Apple Notes Parser

A Python library for reading and parsing Apple Notes SQLite databases.
Extracts all data from Notes SQLite stores including tags and note filtering.
"""

from .parser import AppleNotesParser
from .models import Note, Folder, Account
from .exceptions import AppleNotesParserError

__version__ = "0.1.0"
__all__ = ["AppleNotesParser", "Note", "Folder", "Account", "AppleNotesParserError"]