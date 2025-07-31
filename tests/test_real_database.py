"""
Tests using the real macOS 15 NoteStore database.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from apple_notes_parser import AppleNotesParser


def test_database_version_detection(database_with_connection, database_metadata):
    """Test that the database is correctly identified as macOS 15."""
    macos_version = database_with_connection.get_macos_version()
    assert macos_version == database_metadata["macos_version"]


def test_database_uuid_extraction(database_with_connection, database_metadata):
    """Test extraction of Z_UUID for AppleScript ID construction."""
    z_uuid = database_with_connection.get_z_uuid()
    assert z_uuid == database_metadata["z_uuid"]


def test_accounts_extraction(database_with_connection, database_metadata):
    """Test extraction of accounts from real database."""
    accounts = database_with_connection.get_accounts()
    assert len(accounts) >= 1

    # Find the "On My Mac" account
    on_my_mac_account = next(
        (acc for acc in accounts if acc.name == database_metadata["account_name"]),
        None,
    )
    assert on_my_mac_account is not None
    assert on_my_mac_account.name == database_metadata["account_name"]


def test_folders_extraction_and_hierarchy(database_with_connection, sample_folders_data):
    """Test extraction of folders and their hierarchy."""
    accounts_list = database_with_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts_list}
    folders_list = database_with_connection.get_folders(accounts_dict)
    assert len(folders_list) == sample_folders_data["total_count"]

    # Verify specific folder hierarchy
    folders_by_name = {f.name: f for f in folders_list}

    for expected in sample_folders_data["expected_folders"]:
        folder = folders_by_name.get(expected["name"])
        assert folder is not None, f"Folder '{expected['name']}' not found"


def test_folders_exclude_deleted(database_with_connection):
    """Test that deleted folders are excluded from results."""

    accounts_list = database_with_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts_list}

    # Get current folder count
    folders_before = database_with_connection.get_folders(accounts_dict)
    folder_count_before = len(folders_before)

    # Directly check the database to verify our filtering works
    cursor = database_with_connection.connection.cursor()

    # Count all folders (including deleted)
    cursor.execute("""
        SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTITLE2 IS NOT NULL
    """)
    total_folders_including_deleted = cursor.fetchone()[0]

    # Count non-deleted folders (what our method should return)
    cursor.execute("""
        SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTITLE2 IS NOT NULL AND ZMARKEDFORDELETION = 0
    """)
    non_deleted_folders = cursor.fetchone()[0]

    # Count deleted folders
    cursor.execute("""
        SELECT COUNT(*) FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTITLE2 IS NOT NULL AND ZMARKEDFORDELETION = 1
    """)
    deleted_folders = cursor.fetchone()[0]

    # Our method should return the same count as non-deleted folders
    assert folder_count_before == non_deleted_folders

    # Verify that we're actually filtering something if there are deleted folders
    if deleted_folders > 0:
        assert total_folders_including_deleted > non_deleted_folders
        print(f"Successfully filtered out {deleted_folders} deleted folders")
    else:
        print("No deleted folders found in test database (this is normal)")


def test_notes_extraction_basic(database_with_connection, database_metadata):
    """Test basic note extraction."""
    accounts_list = database_with_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts_list}
    folders_list = database_with_connection.get_folders(accounts_dict)
    folders_dict = {folder.id: folder for folder in folders_list}
    notes_list = database_with_connection.get_notes(accounts_dict, folders_dict)

    assert len(notes_list) == database_metadata["total_notes"]

    # Verify all notes have required fields
    for note in notes_list:
        assert note.id is not None
        assert note.note_id is not None
        assert note.title is not None
        assert note.folder is not None
        assert note.account is not None
        assert note.applescript_id is not None
        assert database_metadata["z_uuid"] in note.applescript_id


def test_specific_notes_content(database_with_connection, sample_notes_data):
    """Test extraction of specific notes and their content."""
    accounts_list = database_with_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts_list}
    folders_list = database_with_connection.get_folders(accounts_dict)
    folders_dict = {folder.id: folder for folder in folders_list}
    notes_list = database_with_connection.get_notes(accounts_dict, folders_dict)

    notes_by_title = {note.title: note for note in notes_list}

    # Test tagged note
    tagged_note = notes_by_title.get(sample_notes_data["tagged_note"]["title"])
    assert tagged_note is not None
    assert tagged_note.folder.name == sample_notes_data["tagged_note"]["folder"]
    assert (
        tagged_note.is_password_protected
        == sample_notes_data["tagged_note"]["password_protected"]
    )
    assert (
        tagged_note.applescript_id
        == sample_notes_data["tagged_note"]["applescript_id"]
    )
    # Tags should be extracted (may be empty if hashtag extraction needs improvement)
    assert tagged_note.tags is not None

    # Test password protected note
    protected_note = notes_by_title.get(
        sample_notes_data["protected_note"]["title"]
    )
    assert protected_note is not None
    assert (
        protected_note.is_password_protected
        == sample_notes_data["protected_note"]["password_protected"]
    )
    assert (
        protected_note.applescript_id
        == sample_notes_data["protected_note"]["applescript_id"]
    )

    # Test note with attachment
    attachment_note = notes_by_title.get(
        sample_notes_data["attachment_note"]["title"]
    )
    assert attachment_note is not None
    assert (
        attachment_note.applescript_id
        == sample_notes_data["attachment_note"]["applescript_id"]
    )

    # Test that attachments are loaded
    assert attachment_note.has_attachments(), (
        "Attachment note should have attachments"
    )
    assert len(attachment_note.attachments) >= 1, (
        "Should have at least one attachment"
    )

    # Test attachment properties
    first_attachment = attachment_note.attachments[0]
    assert first_attachment.filename == "bitcoin.pdf"
    assert first_attachment.file_size == 184292
    assert first_attachment.type_uti == "com.adobe.pdf"
    assert first_attachment.mime_type == "application/pdf"
    assert first_attachment.file_extension == "pdf"
    assert first_attachment.is_document is True
    assert first_attachment.is_image is False
    assert first_attachment.is_video is False
    assert first_attachment.is_audio is False

    # Test subfolder note
    subfolder_note = notes_by_title.get(
        sample_notes_data["subfolder_note"]["title"]
    )
    assert subfolder_note is not None
    assert (
        subfolder_note.folder.name == sample_notes_data["subfolder_note"]["folder"]
    )
    assert (
        subfolder_note.applescript_id
        == sample_notes_data["subfolder_note"]["applescript_id"]
    )


def test_note_content_extraction(database_with_connection):
    """Test that note content is properly extracted and not null."""
    accounts_list = database_with_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts_list}
    folders_list = database_with_connection.get_folders(accounts_dict)
    folders_dict = {folder.id: folder for folder in folders_list}
    notes_list = database_with_connection.get_notes(accounts_dict, folders_dict)

    # At least some notes should have non-null content
    notes_with_content = [note for note in notes_list if note.content]
    assert len(notes_with_content) > 0, (
        "No notes have content - content extraction may be failing"
    )

    # Check specific notes we know should have content
    notes_by_title = {note.title: note for note in notes_list}

    simple_note = notes_by_title.get("This is a note")
    if simple_note:
        assert simple_note.content is not None
        assert len(simple_note.content.strip()) > 0


def test_folder_path_reconstruction(database_with_connection):
    """Test full folder path reconstruction for notes."""
    accounts_list = database_with_connection.get_accounts()
    accounts_dict = {acc.id: acc for acc in accounts_list}
    folders_list = database_with_connection.get_folders(accounts_dict)
    folders_dict = {folder.id: folder for folder in folders_list}
    notes_list = database_with_connection.get_notes(accounts_dict, folders_dict)

    notes_by_title = {note.title: note for note in notes_list}

    # Test deep hierarchy
    deep_note = notes_by_title.get("This note is deeply buried")
    if deep_note:
        folder_path = deep_note.get_folder_path(folders_dict)
        expected_path = "Folder2/Subfolder/Subsubfolder"
        assert folder_path == expected_path

    # Test single level
    folder_note = notes_by_title.get("This note is in Folder")
    if folder_note:
        folder_path = folder_note.get_folder_path(folders_dict)
        expected_path = "Folder"  # Folder is a root folder
        assert folder_path == expected_path


def test_parser_initialization_with_real_db(real_database):
    """Test parser can initialize with real database."""
    parser = AppleNotesParser(real_database)
    assert parser.database_path.exists()


def test_parser_data_loading(real_database, database_metadata):
    """Test parser can load all data from real database."""
    parser = AppleNotesParser(real_database)
    parser.load_data()

    assert len(parser.accounts) >= 1
    assert len(parser.folders) == database_metadata["total_folders"]
    assert len(parser.notes) == database_metadata["total_notes"]


def test_tag_functionality(real_database, sample_notes_data):
    """Test tag extraction and search functionality."""
    parser = AppleNotesParser(real_database)

    # Get all tags
    all_tags = parser.get_all_tags()
    assert isinstance(all_tags, list)

    # Test tag searching if tags are found
    if all_tags:
        tag_counts = parser.get_tag_counts()
        assert isinstance(tag_counts, dict)

        # Test searching for specific tags
        for tag in all_tags[:2]:  # Test first few tags
            notes_with_tag = parser.get_notes_by_tag(tag)
            assert isinstance(notes_with_tag, list)


def test_password_protection_detection(real_database):
    """Test detection of password-protected notes."""
    parser = AppleNotesParser(real_database)

    protected_notes = parser.get_protected_notes()
    assert isinstance(protected_notes, list)

    # Should find at least one protected note based on our test data
    assert len(protected_notes) >= 1

    # Verify the specific protected note
    protected_titles = [note.title for note in protected_notes]
    assert "This note is password protected" in protected_titles


def test_search_functionality(real_database):
    """Test note search functionality."""
    parser = AppleNotesParser(real_database)

    # Search for specific text that should exist
    results = parser.search_notes("subfolder")
    assert len(results) >= 1

    # Case insensitive search
    results_case = parser.search_notes("SUBFOLDER", case_sensitive=False)
    assert len(results_case) >= len(results)

    # Search for text in title
    results_title = parser.search_notes("attachment")
    assert len(results_title) >= 1


def test_export_functionality(real_database):
    """Test data export functionality."""
    parser = AppleNotesParser(real_database)

    export_data = parser.export_notes_to_dict(include_content=True)

    assert "accounts" in export_data
    assert "folders" in export_data
    assert "notes" in export_data

    assert len(export_data["accounts"]) >= 1
    assert len(export_data["folders"]) == 6
    assert len(export_data["notes"]) == 8

    # Verify folder paths are included
    for folder_data in export_data["folders"]:
        assert "path" in folder_data
        assert folder_data["path"] is not None

    # Verify AppleScript IDs are included
    for note_data in export_data["notes"]:
        assert "applescript_id" in note_data
        assert note_data["applescript_id"] is not None
        assert "09FBEB4A-5B24-424E-814B-4AE8E757FB83" in note_data["applescript_id"]


def test_attachment_functionality(real_database, sample_notes_data):
    """Test attachment extraction and search functionality."""
    parser = AppleNotesParser(real_database)

    # Test notes with attachments
    notes_with_attachments = parser.get_notes_with_attachments()
    assert len(notes_with_attachments) >= 1, (
        "Should find at least one note with attachments"
    )

    # Test specific attachment note
    attachment_note_title = sample_notes_data["attachment_note"]["title"]
    attachment_notes = [
        note
        for note in notes_with_attachments
        if note.title == attachment_note_title
    ]
    assert len(attachment_notes) == 1, (
        f"Should find exactly one note titled '{attachment_note_title}'"
    )

    attachment_note = attachment_notes[0]
    assert attachment_note.has_attachments()
    assert len(attachment_note.attachments) >= 1

    # Test attachment type filtering
    document_notes = parser.get_notes_by_attachment_type("document")
    assert len(document_notes) >= 1, "Should find notes with document attachments"
    assert attachment_note in document_notes, (
        "PDF attachment should be classified as document"
    )

    # Test image, video, audio filtering (should be empty for our test data)
    image_notes = parser.get_notes_by_attachment_type("image")
    video_notes = parser.get_notes_by_attachment_type("video")
    audio_notes = parser.get_notes_by_attachment_type("audio")

    # These may be empty in our test database
    assert isinstance(image_notes, list)
    assert isinstance(video_notes, list)
    assert isinstance(audio_notes, list)

    # Test getting all attachments
    all_attachments = parser.get_all_attachments()
    assert len(all_attachments) >= 1, (
        "Should find at least one attachment across all notes"
    )

    # Verify PDF attachment properties
    pdf_attachments = [
        att for att in all_attachments if att.filename == "bitcoin.pdf"
    ]
    assert len(pdf_attachments) == 1, (
        "Should find exactly one bitcoin.pdf attachment"
    )

    pdf_attachment = pdf_attachments[0]
    assert pdf_attachment.file_size == 184292
    assert pdf_attachment.type_uti == "com.adobe.pdf"
    assert pdf_attachment.mime_type == "application/pdf"
    assert pdf_attachment.is_document
    assert not pdf_attachment.is_image
    assert not pdf_attachment.is_video
    assert not pdf_attachment.is_audio


def test_attachment_export(real_database):
    """Test that attachments are included in export data."""
    parser = AppleNotesParser(real_database)

    export_data = parser.export_notes_to_dict(include_content=True)

    # Find note with attachment in export data
    attachment_note_data = None
    for note_data in export_data["notes"]:
        if note_data["title"] == "This note has an attachment":
            attachment_note_data = note_data
            break

    assert attachment_note_data is not None, "Should find attachment note in export"
    assert "attachments" in attachment_note_data, (
        "Note data should include attachments field"
    )
    assert len(attachment_note_data["attachments"]) >= 1, (
        "Should export at least one attachment"
    )

    # Verify attachment data structure
    first_attachment = attachment_note_data["attachments"][0]
    expected_fields = [
        "id",
        "filename",
        "file_size",
        "type_uti",
        "file_extension",
        "mime_type",
        "is_image",
        "is_video",
        "is_audio",
        "is_document",
        "creation_date",
        "modification_date",
        "uuid",
        "is_remote",
        "remote_url",
    ]

    for field in expected_fields:
        assert field in first_attachment, f"Attachment should have '{field}' field"

    # Verify specific values for our known attachment
    assert first_attachment["filename"] == "bitcoin.pdf"
    assert first_attachment["file_size"] == 184292
    assert first_attachment["type_uti"] == "com.adobe.pdf"
    assert first_attachment["mime_type"] == "application/pdf"
    assert first_attachment["file_extension"] == "pdf"
    assert first_attachment["is_document"] is True
    assert first_attachment["is_image"] is False


def test_get_note_by_applescript_id(real_database, sample_notes_data):
    """Test getting a note by its AppleScript ID."""
    parser = AppleNotesParser(real_database)

    # Test with a known AppleScript ID from sample data
    expected_applescript_id = sample_notes_data["tagged_note"]["applescript_id"]
    expected_title = sample_notes_data["tagged_note"]["title"]

    # Get the note by AppleScript ID
    note = parser.get_note_by_applescript_id(expected_applescript_id)

    assert note is not None, (
        f"Should find note with AppleScript ID: {expected_applescript_id}"
    )
    assert note.title == expected_title, (
        f"Expected title '{expected_title}', got '{note.title}'"
    )
    assert note.applescript_id == expected_applescript_id

    # Test with non-existent AppleScript ID
    non_existent_id = "x-coredata://FAKE-UUID/ICNote/p999"
    note_not_found = parser.get_note_by_applescript_id(non_existent_id)
    assert note_not_found is None, (
        "Should return None for non-existent AppleScript ID"
    )
