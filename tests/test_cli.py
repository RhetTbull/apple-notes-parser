"""
Tests for the CLI interface using CliRunner.
"""

import json
import tempfile
from pathlib import Path

import pytest
from clirunner import CliRunner

from apple_notes_parser.cli import main


class TestCLI:
    """Test the CLI interface."""

    def setup_method(self):
        """Set up test method."""
        self.runner = CliRunner()

    def test_version(self):
        """Test --version flag."""
        result = self.runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert 'apple-notes-parser' in result.output

    def test_help(self):
        """Test help output."""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'Parse and analyze Apple Notes databases' in result.output
        assert 'list' in result.output
        assert 'search' in result.output
        assert 'export' in result.output

    def test_no_command_shows_help(self):
        """Test that running without a command shows help."""
        result = self.runner.invoke(main, [])
        assert result.exit_code == 0
        assert 'Parse and analyze Apple Notes databases' in result.output

    def test_list_help(self):
        """Test list command help."""
        result = self.runner.invoke(main, ['list', '--help'])
        assert result.exit_code == 0
        assert '--folder' in result.output
        assert '--tag' in result.output

    def test_search_help(self):
        """Test search command help."""
        result = self.runner.invoke(main, ['search', '--help'])
        assert result.exit_code == 0
        assert 'query' in result.output

    def test_export_help(self):
        """Test export command help."""
        result = self.runner.invoke(main, ['export', '--help'])
        assert result.exit_code == 0
        assert 'output' in result.output

    def test_stats_help(self):
        """Test stats command help."""
        result = self.runner.invoke(main, ['stats', '--help'])
        assert result.exit_code == 0
        assert '--verbose' in result.output

    def test_attachments_help(self):
        """Test attachments command help."""
        result = self.runner.invoke(main, ['attachments', '--help'])
        assert result.exit_code == 0
        assert '--type' in result.output

    def test_tags_help(self):
        """Test tags command help."""
        result = self.runner.invoke(main, ['tags', '--help'])
        assert result.exit_code == 0
        assert '--sort-by-count' in result.output


class TestCLIWithDatabase:
    """Test CLI commands with real database."""

    def setup_method(self):
        """Set up test method."""
        self.runner = CliRunner()
        self.database_path = Path(__file__).parent / "data" / "NoteStore-macOS-15-Seqoia.sqlite"
        if not self.database_path.exists():
            pytest.skip(f"Test database not found at {self.database_path}")

    def test_list_basic(self):
        """Test basic list command."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'list'])
        assert result.exit_code == 0
        assert 'Found' in result.output
        assert 'note(s)' in result.output

    def test_list_with_folder_filter(self):
        """Test list command with folder filter."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'list', '--folder', 'Notes'])
        assert result.exit_code == 0
        assert 'Found' in result.output

    def test_list_with_attachments_flag(self):
        """Test list command with attachments filter."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'list', '--attachments'])
        assert result.exit_code == 0

    def test_list_with_pinned_flag(self):
        """Test list command with pinned filter."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'list', '--pinned'])
        assert result.exit_code == 0

    def test_list_with_protected_flag(self):
        """Test list command with protected filter."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'list', '--protected'])
        assert result.exit_code == 0

    def test_list_with_content(self):
        """Test list command with content display."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'list', '--content'])
        assert result.exit_code == 0

    def test_list_with_show_attachments(self):
        """Test list command with attachment details."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'list', '--show-attachments'])
        assert result.exit_code == 0

    def test_search_basic(self):
        """Test basic search command."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'search', 'note'])
        assert result.exit_code == 0
        assert 'Found' in result.output
        assert 'matching' in result.output

    def test_search_case_sensitive(self):
        """Test case-sensitive search."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'search', 'Note', '--case-sensitive'])
        assert result.exit_code == 0

    def test_search_with_content(self):
        """Test search with content display."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'search', 'note', '--content'])
        assert result.exit_code == 0

    def test_export_basic(self):
        """Test basic export command."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            result = self.runner.invoke(main, ['--database', str(self.database_path), 'export', tmp_path])
            assert result.exit_code == 0
            assert 'Exported' in result.output

            # Verify the JSON file was created and is valid
            with open(tmp_path, 'r') as f:
                data = json.load(f)
                assert 'notes' in data
                assert 'folders' in data
                assert 'accounts' in data
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_export_with_folder_filter(self):
        """Test export with folder filter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            result = self.runner.invoke(main, [
                '--database', str(self.database_path), 
                'export', tmp_path, 
                '--folder', 'Notes'
            ])
            assert result.exit_code == 0
            assert 'Exported' in result.output
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_export_no_content(self):
        """Test export without content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            result = self.runner.invoke(main, [
                '--database', str(self.database_path), 
                'export', tmp_path, 
                '--no-content'
            ])
            assert result.exit_code == 0
            assert 'Exported' in result.output
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_stats_basic(self):
        """Test basic stats command."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'stats'])
        assert result.exit_code == 0
        assert 'Apple Notes Database Statistics' in result.output
        assert 'Total Notes:' in result.output
        assert 'Total Folders:' in result.output

    def test_stats_verbose(self):
        """Test verbose stats command."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'stats', '--verbose'])
        assert result.exit_code == 0
        assert 'Apple Notes Database Statistics' in result.output

    def test_attachments_basic(self):
        """Test basic attachments command."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'attachments'])
        assert result.exit_code == 0
        assert 'Found' in result.output
        assert 'attachment(s)' in result.output

    def test_attachments_with_type_filter(self):
        """Test attachments command with type filter."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'attachments', '--type', 'image'])
        assert result.exit_code == 0

    def test_tags_basic(self):
        """Test basic tags command."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'tags'])
        assert result.exit_code == 0

    def test_tags_sort_by_count(self):
        """Test tags command sorted by count."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'tags', '--sort-by-count'])
        assert result.exit_code == 0

    def test_tags_show_notes(self):
        """Test tags command with notes display."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'tags', '--show-notes'])
        assert result.exit_code == 0

    def test_database_not_found_error(self):
        """Test error handling for missing database."""
        result = self.runner.invoke(main, ['--database', '/nonexistent/path.sqlite', 'list'])
        assert result.exit_code == 1
        assert 'Error:' in result.output

    def test_search_missing_query(self):
        """Test search command without query argument."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'search'])
        assert result.exit_code == 2  # argparse error

    def test_export_missing_output(self):
        """Test export command without output argument."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'export'])
        assert result.exit_code == 2  # argparse error

    def test_invalid_attachment_type(self):
        """Test attachments command with invalid type."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'attachments', '--type', 'invalid'])
        assert result.exit_code == 2  # argparse error

    def test_complex_filtering(self):
        """Test complex filtering combinations."""
        result = self.runner.invoke(main, [
            '--database', str(self.database_path), 
            'list', 
            '--folder', 'Notes',
            '--content',
            '--show-attachments'
        ])
        assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""

    def setup_method(self):
        """Set up test method."""
        self.runner = CliRunner()

    def test_invalid_command(self):
        """Test invalid command."""
        result = self.runner.invoke(main, ['invalid-command'])
        assert result.exit_code == 2  # argparse error

    def test_export_to_invalid_path(self):
        """Test export to invalid file path."""
        database_path = Path(__file__).parent / "data" / "NoteStore-macOS-15-Seqoia.sqlite"
        if not database_path.exists():
            pytest.skip("Test database not found")

        result = self.runner.invoke(main, [
            '--database', str(database_path), 
            'export', '/invalid/path/output.json'
        ])
        assert result.exit_code == 1
        assert 'Error writing to file:' in result.output

    def test_database_file_not_found(self):
        """Test handling of non-existent database file."""
        result = self.runner.invoke(main, ['--database', '/path/does/not/exist.sqlite', 'list'])
        assert result.exit_code == 1
        assert 'Error:' in result.output

    def test_malformed_database_path(self):
        """Test handling of malformed database path."""
        result = self.runner.invoke(main, ['--database', '', 'list'])
        assert result.exit_code == 1
        assert 'Error:' in result.output


class TestCLIOutputFormatting:
    """Test CLI output formatting and display."""

    def setup_method(self):
        """Set up test method."""
        self.runner = CliRunner()
        self.database_path = Path(__file__).parent / "data" / "NoteStore-macOS-15-Seqoia.sqlite"
        if not self.database_path.exists():
            pytest.skip(f"Test database not found at {self.database_path}")

    def test_emojis_in_output(self):
        """Test that emojis are displayed correctly."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'list'])
        assert result.exit_code == 0
        # Check for emoji characters in note display
        assert '📝' in result.output

    def test_stats_formatting(self):
        """Test stats command formatting."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'stats'])
        assert result.exit_code == 0
        # Check for formatted sections
        assert '📊' in result.output
        assert '=' in result.output
        assert 'Total Notes:' in result.output

    def test_date_formatting(self):
        """Test date formatting in output."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'list'])
        assert result.exit_code == 0
        # Dates should be formatted as YYYY-MM-DD HH:MM:SS
        import re
        date_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        assert re.search(date_pattern, result.output)

    def test_size_formatting(self):
        """Test file size formatting."""
        result = self.runner.invoke(main, ['--database', str(self.database_path), 'attachments'])
        assert result.exit_code == 0
        # Should show size formatting (B, KB, MB, etc.)
        size_units = ['B', 'KB', 'MB', 'GB']
        has_size_unit = any(unit in result.output for unit in size_units)
        # Only assert if there are attachments
        if 'attachment(s)' in result.output and not result.output.startswith('Found 0'):
            assert has_size_unit or 'Unknown' in result.output


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def setup_method(self):
        """Set up test method."""
        self.runner = CliRunner()
        self.database_path = Path(__file__).parent / "data" / "NoteStore-macOS-15-Seqoia.sqlite"
        if not self.database_path.exists():
            pytest.skip(f"Test database not found at {self.database_path}")

    def test_full_workflow(self):
        """Test a complete workflow: list, search, export."""
        # First, list notes
        list_result = self.runner.invoke(main, ['--database', str(self.database_path), 'list'])
        assert list_result.exit_code == 0

        # Search for something
        search_result = self.runner.invoke(main, ['--database', str(self.database_path), 'search', 'note'])
        assert search_result.exit_code == 0

        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            export_result = self.runner.invoke(main, ['--database', str(self.database_path), 'export', tmp_path])
            assert export_result.exit_code == 0

            # Verify export was successful
            assert Path(tmp_path).exists()
            with open(tmp_path, 'r') as f:
                data = json.load(f)
                assert isinstance(data, dict)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_all_commands_work(self):
        """Test that all main commands execute without errors."""
        commands = [
            ['list'],
            ['search', 'test'],
            ['stats'],
            ['attachments'],
            ['tags']
        ]

        for cmd in commands:
            result = self.runner.invoke(main, ['--database', str(self.database_path)] + cmd)
            assert result.exit_code == 0, f"Command {cmd} failed with exit code {result.exit_code}"