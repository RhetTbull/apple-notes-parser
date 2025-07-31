"""
Tests for the CLI interface using CliRunner.
"""

import json
import tempfile
from pathlib import Path

import pytest
from clirunner import CliRunner

from apple_notes_parser.cli import main


@pytest.fixture
def runner():
    """Fixture providing a CliRunner instance."""
    return CliRunner()


@pytest.fixture
def test_database():
    """Fixture providing path to test database."""
    database_path = Path(__file__).parent / "data" / "NoteStore-macOS-15-Seqoia.sqlite"
    if not database_path.exists():
        pytest.skip(f"Test database not found at {database_path}")
    return str(database_path)


# Basic CLI functionality tests
def test_version(runner):
    """Test --version flag."""
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "apple-notes-parser" in result.output


def test_help(runner):
    """Test help output."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Parse and analyze Apple Notes databases" in result.output
    assert "list" in result.output
    assert "search" in result.output
    assert "export" in result.output


def test_no_command_shows_help(runner):
    """Test that running without a command shows help."""
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert "Parse and analyze Apple Notes databases" in result.output


def test_list_help(runner):
    """Test list command help."""
    result = runner.invoke(main, ["list", "--help"])
    assert result.exit_code == 0
    assert "--folder" in result.output
    assert "--tag" in result.output


def test_search_help(runner):
    """Test search command help."""
    result = runner.invoke(main, ["search", "--help"])
    assert result.exit_code == 0
    assert "query" in result.output


def test_export_help(runner):
    """Test export command help."""
    result = runner.invoke(main, ["export", "--help"])
    assert result.exit_code == 0
    assert "output" in result.output


def test_stats_help(runner):
    """Test stats command help."""
    result = runner.invoke(main, ["stats", "--help"])
    assert result.exit_code == 0
    assert "--verbose" in result.output


def test_attachments_help(runner):
    """Test attachments command help."""
    result = runner.invoke(main, ["attachments", "--help"])
    assert result.exit_code == 0
    assert "--type" in result.output


def test_tags_help(runner):
    """Test tags command help."""
    result = runner.invoke(main, ["tags", "--help"])
    assert result.exit_code == 0
    assert "--sort-by-count" in result.output


# Database operation tests
def test_list_basic(runner, test_database):
    """Test basic list command."""
    result = runner.invoke(main, ["--database", test_database, "list"])
    assert result.exit_code == 0
    assert "Found" in result.output
    assert "note(s)" in result.output


def test_list_with_folder_filter(runner, test_database):
    """Test list command with folder filter."""
    result = runner.invoke(
        main, ["--database", test_database, "list", "--folder", "Notes"]
    )
    assert result.exit_code == 0
    assert "Found" in result.output


def test_list_with_attachments_flag(runner, test_database):
    """Test list command with attachments filter."""
    result = runner.invoke(main, ["--database", test_database, "list", "--attachments"])
    assert result.exit_code == 0


def test_list_with_pinned_flag(runner, test_database):
    """Test list command with pinned filter."""
    result = runner.invoke(main, ["--database", test_database, "list", "--pinned"])
    assert result.exit_code == 0


def test_list_with_protected_flag(runner, test_database):
    """Test list command with protected filter."""
    result = runner.invoke(main, ["--database", test_database, "list", "--protected"])
    assert result.exit_code == 0


def test_list_with_content(runner, test_database):
    """Test list command with content display."""
    result = runner.invoke(main, ["--database", test_database, "list", "--content"])
    assert result.exit_code == 0


def test_list_with_show_attachments(runner, test_database):
    """Test list command with attachment details."""
    result = runner.invoke(
        main, ["--database", test_database, "list", "--show-attachments"]
    )
    assert result.exit_code == 0


def test_search_basic(runner, test_database):
    """Test basic search command."""
    result = runner.invoke(main, ["--database", test_database, "search", "note"])
    assert result.exit_code == 0
    assert "Found" in result.output
    assert "matching" in result.output


def test_search_case_sensitive(runner, test_database):
    """Test case-sensitive search."""
    result = runner.invoke(
        main, ["--database", test_database, "search", "Note", "--case-sensitive"]
    )
    assert result.exit_code == 0


def test_search_with_content(runner, test_database):
    """Test search with content display."""
    result = runner.invoke(
        main, ["--database", test_database, "search", "note", "--content"]
    )
    assert result.exit_code == 0


def test_export_basic(runner, test_database):
    """Test basic export command."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tmp_file:
        tmp_path = tmp_file.name

    try:
        result = runner.invoke(main, ["--database", test_database, "export", tmp_path])
        assert result.exit_code == 0
        assert "Exported" in result.output

        # Verify the JSON file was created and is valid
        with open(tmp_path, "r") as f:
            data = json.load(f)
            assert "notes" in data
            assert "folders" in data
            assert "accounts" in data
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_export_with_folder_filter(runner, test_database):
    """Test export with folder filter."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tmp_file:
        tmp_path = tmp_file.name

    try:
        result = runner.invoke(
            main, ["--database", test_database, "export", tmp_path, "--folder", "Notes"]
        )
        assert result.exit_code == 0
        assert "Exported" in result.output
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_export_no_content(runner, test_database):
    """Test export without content."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tmp_file:
        tmp_path = tmp_file.name

    try:
        result = runner.invoke(
            main, ["--database", test_database, "export", tmp_path, "--no-content"]
        )
        assert result.exit_code == 0
        assert "Exported" in result.output
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_stats_basic(runner, test_database):
    """Test basic stats command."""
    result = runner.invoke(main, ["--database", test_database, "stats"])
    assert result.exit_code == 0
    assert "Apple Notes Database Statistics" in result.output
    assert "Total Notes:" in result.output
    assert "Total Folders:" in result.output


def test_stats_verbose(runner, test_database):
    """Test verbose stats command."""
    result = runner.invoke(main, ["--database", test_database, "stats", "--verbose"])
    assert result.exit_code == 0
    assert "Apple Notes Database Statistics" in result.output


def test_attachments_basic(runner, test_database):
    """Test basic attachments command."""
    result = runner.invoke(main, ["--database", test_database, "attachments"])
    assert result.exit_code == 0
    assert "Found" in result.output
    assert "attachment(s)" in result.output


def test_attachments_with_type_filter(runner, test_database):
    """Test attachments command with type filter."""
    result = runner.invoke(
        main, ["--database", test_database, "attachments", "--type", "image"]
    )
    assert result.exit_code == 0


def test_tags_basic(runner, test_database):
    """Test basic tags command."""
    result = runner.invoke(main, ["--database", test_database, "tags"])
    assert result.exit_code == 0


def test_tags_sort_by_count(runner, test_database):
    """Test tags command sorted by count."""
    result = runner.invoke(
        main, ["--database", test_database, "tags", "--sort-by-count"]
    )
    assert result.exit_code == 0


def test_tags_show_notes(runner, test_database):
    """Test tags command with notes display."""
    result = runner.invoke(main, ["--database", test_database, "tags", "--show-notes"])
    assert result.exit_code == 0


def test_database_not_found_error(runner):
    """Test error handling for missing database."""
    result = runner.invoke(main, ["--database", "/nonexistent/path.sqlite", "list"])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_search_missing_query(runner, test_database):
    """Test search command without query argument."""
    result = runner.invoke(main, ["--database", test_database, "search"])
    assert result.exit_code == 2  # argparse error


def test_export_missing_output(runner, test_database):
    """Test export command without output argument."""
    result = runner.invoke(main, ["--database", test_database, "export"])
    assert result.exit_code == 2  # argparse error


def test_invalid_attachment_type(runner, test_database):
    """Test attachments command with invalid type."""
    result = runner.invoke(
        main, ["--database", test_database, "attachments", "--type", "invalid"]
    )
    assert result.exit_code == 2  # argparse error


def test_complex_filtering(runner, test_database):
    """Test complex filtering combinations."""
    result = runner.invoke(
        main,
        [
            "--database",
            test_database,
            "list",
            "--folder",
            "Notes",
            "--content",
            "--show-attachments",
        ],
    )
    assert result.exit_code == 0


# Error handling tests
def test_invalid_command(runner):
    """Test invalid command."""
    result = runner.invoke(main, ["invalid-command"])
    assert result.exit_code == 2  # argparse error


def test_export_to_invalid_path(runner, test_database):
    """Test export to invalid file path."""
    result = runner.invoke(
        main, ["--database", test_database, "export", "/invalid/path/output.json"]
    )
    assert result.exit_code == 1
    assert "Error writing to file:" in result.output


def test_database_file_not_found(runner):
    """Test handling of non-existent database file."""
    result = runner.invoke(main, ["--database", "/path/does/not/exist.sqlite", "list"])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_malformed_database_path(runner):
    """Test handling of malformed database path."""
    result = runner.invoke(main, ["--database", "", "list"])
    assert result.exit_code == 1
    assert "Error:" in result.output


# Output formatting tests
def test_emojis_in_output(runner, test_database):
    """Test that emojis are displayed correctly."""
    result = runner.invoke(main, ["--database", test_database, "list"])
    assert result.exit_code == 0
    # Check for emoji characters in note display
    assert "📝" in result.output


def test_stats_formatting(runner, test_database):
    """Test stats command formatting."""
    result = runner.invoke(main, ["--database", test_database, "stats"])
    assert result.exit_code == 0
    # Check for formatted sections
    assert "📊" in result.output
    assert "=" in result.output
    assert "Total Notes:" in result.output


def test_date_formatting(runner, test_database):
    """Test date formatting in output."""
    result = runner.invoke(main, ["--database", test_database, "list"])
    assert result.exit_code == 0
    # Dates should be formatted as YYYY-MM-DD HH:MM:SS
    import re

    date_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    assert re.search(date_pattern, result.output)


def test_size_formatting(runner, test_database):
    """Test file size formatting."""
    result = runner.invoke(main, ["--database", test_database, "attachments"])
    assert result.exit_code == 0
    # Should show size formatting (B, KB, MB, etc.)
    size_units = ["B", "KB", "MB", "GB"]
    has_size_unit = any(unit in result.output for unit in size_units)
    # Only assert if there are attachments
    if "attachment(s)" in result.output and not result.output.startswith("Found 0"):
        assert has_size_unit or "Unknown" in result.output


# Integration tests
def test_full_workflow(runner, test_database):
    """Test a complete workflow: list, search, export."""
    # First, list notes
    list_result = runner.invoke(main, ["--database", test_database, "list"])
    assert list_result.exit_code == 0

    # Search for something
    search_result = runner.invoke(main, ["--database", test_database, "search", "note"])
    assert search_result.exit_code == 0

    # Export to temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tmp_file:
        tmp_path = tmp_file.name

    try:
        export_result = runner.invoke(
            main, ["--database", test_database, "export", tmp_path]
        )
        assert export_result.exit_code == 0

        # Verify export was successful
        assert Path(tmp_path).exists()
        with open(tmp_path, "r") as f:
            data = json.load(f)
            assert isinstance(data, dict)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_all_commands_work(runner, test_database):
    """Test that all main commands execute without errors."""
    commands = [["list"], ["search", "test"], ["stats"], ["attachments"], ["tags"]]

    for cmd in commands:
        result = runner.invoke(main, ["--database", test_database] + cmd)
        assert (
            result.exit_code == 0
        ), f"Command {cmd} failed with exit code {result.exit_code}"
