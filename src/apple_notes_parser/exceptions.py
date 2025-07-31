"""Exception classes for Apple Notes Parser."""


class AppleNotesParserError(Exception):
    """Base exception for Apple Notes Parser."""

    pass


class DatabaseError(AppleNotesParserError):
    """Error related to database operations."""

    pass


class ProtobufError(AppleNotesParserError):
    """Error related to protobuf parsing."""

    pass


class DecryptionError(AppleNotesParserError):
    """Error related to note decryption."""

    pass
