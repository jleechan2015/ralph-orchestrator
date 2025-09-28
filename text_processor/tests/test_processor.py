"""Tests for the text processor CLI module."""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import os

# Import the CLI main function
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from text_processor import main


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Hello World\nThis is a test file.\nIt has three lines.")
    return str(file_path)


@pytest.fixture
def empty_file(tmp_path):
    """Create an empty file for testing."""
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")
    return str(file_path)


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_help_command(self, runner):
        """Test that --help works."""
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Text Processor" in result.output
        assert "Process text files with various operations" in result.output
        assert "--word-count" in result.output
        assert "--char-count" in result.output
        assert "--line-count" in result.output
        assert "--replace" in result.output
        assert "--case" in result.output

    def test_no_input_error(self, runner):
        """Test error when no input is provided."""
        result = runner.invoke(main, ['--word-count'])
        assert result.exit_code == 1
        assert "Error: Either provide an input file or use --stdin flag" in result.output

    def test_no_operation_error(self, runner, sample_text_file):
        """Test error when no operation is specified."""
        result = runner.invoke(main, [sample_text_file])
        assert result.exit_code == 1
        assert "Error: No operation specified" in result.output

    def test_both_file_and_stdin_error(self, runner, sample_text_file):
        """Test error when both file and stdin are specified."""
        result = runner.invoke(main, [sample_text_file, '--stdin', '--word-count'])
        assert result.exit_code == 1
        assert "Error: Cannot use both input file and --stdin" in result.output

    def test_nonexistent_file_error(self, runner):
        """Test error for non-existent file."""
        result = runner.invoke(main, ['nonexistent.txt', '--word-count'])
        assert result.exit_code == 2  # Click uses exit code 2 for missing files
        assert "does not exist" in result.output.lower() or "error" in result.output.lower()


class TestCountOperations:
    """Test counting operations."""

    def test_word_count_file(self, runner, sample_text_file):
        """Test word counting from file."""
        result = runner.invoke(main, [sample_text_file, '--word-count'])
        assert result.exit_code == 0
        assert "Words: 11" in result.output

    def test_char_count_file(self, runner, sample_text_file):
        """Test character counting from file."""
        result = runner.invoke(main, [sample_text_file, '--char-count'])
        assert result.exit_code == 0
        assert "Characters: 52" in result.output

    def test_line_count_file(self, runner, sample_text_file):
        """Test line counting from file."""
        result = runner.invoke(main, [sample_text_file, '--line-count'])
        assert result.exit_code == 0
        assert "Lines: 3" in result.output

    def test_multiple_counts(self, runner, sample_text_file):
        """Test multiple counting operations together."""
        result = runner.invoke(main, [sample_text_file, '--word-count', '--char-count', '--line-count'])
        assert result.exit_code == 0
        assert "Words: 11" in result.output
        assert "Characters: 52" in result.output
        assert "Lines: 3" in result.output

    def test_empty_file_counts(self, runner, empty_file):
        """Test counting operations on empty file."""
        result = runner.invoke(main, [empty_file, '--word-count', '--char-count', '--line-count'])
        assert result.exit_code == 0
        assert "Words: 0" in result.output
        assert "Characters: 0" in result.output
        assert "Lines: 0" in result.output


class TestStdinInput:
    """Test stdin input functionality."""

    def test_word_count_stdin(self, runner):
        """Test word counting from stdin."""
        result = runner.invoke(main, ['--stdin', '--word-count'], input="Hello World from stdin")
        assert result.exit_code == 0
        assert "Words: 4" in result.output

    def test_char_count_stdin(self, runner):
        """Test character counting from stdin."""
        result = runner.invoke(main, ['--stdin', '--char-count'], input="Hello")
        assert result.exit_code == 0
        assert "Characters: 5" in result.output

    def test_line_count_stdin(self, runner):
        """Test line counting from stdin."""
        result = runner.invoke(main, ['--stdin', '--line-count'], input="Line 1\nLine 2\nLine 3")
        assert result.exit_code == 0
        assert "Lines: 3" in result.output

    def test_empty_stdin(self, runner):
        """Test empty stdin input."""
        result = runner.invoke(main, ['--stdin', '--word-count'], input="")
        assert result.exit_code == 0
        assert "Words: 0" in result.output


class TestTextTransformations:
    """Test text transformation operations."""

    def test_replace_text_file(self, runner, sample_text_file):
        """Test text replacement from file."""
        result = runner.invoke(main, [sample_text_file, '--replace', 'Hello', 'Goodbye'])
        assert result.exit_code == 0
        assert "Replaced 'Hello' with 'Goodbye'" in result.output
        assert "Goodbye World" in result.output

    def test_replace_text_stdin(self, runner):
        """Test text replacement from stdin."""
        result = runner.invoke(main, ['--stdin', '--replace', 'old', 'new'], input="old text with old word")
        assert result.exit_code == 0
        assert "new text with new word" in result.output

    def test_case_upper(self, runner, sample_text_file):
        """Test uppercase conversion."""
        result = runner.invoke(main, [sample_text_file, '--case', 'upper'])
        assert result.exit_code == 0
        assert "HELLO WORLD" in result.output
        assert "THIS IS A TEST FILE." in result.output

    def test_case_lower(self, runner):
        """Test lowercase conversion from stdin."""
        result = runner.invoke(main, ['--stdin', '--case', 'lower'], input="HELLO WORLD")
        assert result.exit_code == 0
        assert "hello world" in result.output

    def test_case_title(self, runner):
        """Test title case conversion from stdin."""
        result = runner.invoke(main, ['--stdin', '--case', 'title'], input="hello world")
        assert result.exit_code == 0
        assert "Hello World" in result.output

    def test_combined_transformations(self, runner):
        """Test combining replacement and case conversion."""
        result = runner.invoke(main, ['--stdin', '--replace', 'hello', 'goodbye', '--case', 'upper'],
                                input="hello world")
        assert result.exit_code == 0
        assert "GOODBYE WORLD" in result.output


class TestFileOutput:
    """Test file output functionality."""

    def test_output_to_file(self, runner, sample_text_file, tmp_path):
        """Test writing output to a file."""
        output_file = tmp_path / "output.txt"
        result = runner.invoke(main, [sample_text_file, '--case', 'upper', '-o', str(output_file)])
        assert result.exit_code == 0
        assert f"Output written to: {output_file}" in result.output

        # Check the output file content
        content = output_file.read_text()
        assert "HELLO WORLD" in content
        assert "THIS IS A TEST FILE." in content

    def test_replace_and_output(self, runner, sample_text_file, tmp_path):
        """Test replacement with file output."""
        output_file = tmp_path / "output.txt"
        result = runner.invoke(main, [sample_text_file, '--replace', 'Hello', 'Hi', '-o', str(output_file)])
        assert result.exit_code == 0
        assert f"Output written to: {output_file}" in result.output

        # Check the output file content
        content = output_file.read_text()
        assert "Hi World" in content

    def test_count_with_output(self, runner, sample_text_file, tmp_path):
        """Test that counts are still shown when outputting to file."""
        output_file = tmp_path / "output.txt"
        result = runner.invoke(main, [sample_text_file, '--word-count', '--case', 'upper', '-o', str(output_file)])
        assert result.exit_code == 0
        assert "Words: 10" in result.output
        assert f"Output written to: {output_file}" in result.output

    def test_output_from_stdin(self, runner, tmp_path):
        """Test outputting stdin input to file."""
        output_file = tmp_path / "output.txt"
        result = runner.invoke(main, ['--stdin', '--case', 'upper', '-o', str(output_file)],
                                input="hello from stdin")
        assert result.exit_code == 0
        assert f"Output written to: {output_file}" in result.output

        content = output_file.read_text()
        assert "HELLO FROM STDIN" in content


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unicode_text(self, runner):
        """Test handling of Unicode text."""
        result = runner.invoke(main, ['--stdin', '--word-count'], input="Héllo Wörld 你好")
        assert result.exit_code == 0
        assert "Words: 3" in result.output

    def test_large_text(self, runner):
        """Test handling of large text input."""
        large_text = "word " * 10000  # 10,000 words
        result = runner.invoke(main, ['--stdin', '--word-count'], input=large_text)
        assert result.exit_code == 0
        assert "Words: 10000" in result.output

    def test_newline_variations(self, runner):
        """Test different newline styles."""
        # Unix style
        result = runner.invoke(main, ['--stdin', '--line-count'], input="Line1\nLine2\nLine3")
        assert result.exit_code == 0
        assert "Lines: 3" in result.output

    def test_special_characters_in_replacement(self, runner):
        """Test replacement with special characters."""
        result = runner.invoke(main, ['--stdin', '--replace', '$var', '${value}'],
                                input="The $var is here")
        assert result.exit_code == 0
        assert "The ${value} is here" in result.output

    def test_empty_replacement(self, runner):
        """Test replacing text with empty string."""
        result = runner.invoke(main, ['--stdin', '--replace', 'remove', ''],
                                input="remove this word")
        assert result.exit_code == 0
        assert " this word" in result.output

    def test_no_match_replacement(self, runner):
        """Test replacement when pattern is not found."""
        result = runner.invoke(main, ['--stdin', '--replace', 'notfound', 'replacement'],
                                input="original text")
        assert result.exit_code == 0
        assert "original text" in result.output


class TestComplexScenarios:
    """Test complex usage scenarios."""

    def test_pipeline_simulation(self, runner, tmp_path):
        """Test simulating a text processing pipeline."""
        # Create initial file
        input_file = tmp_path / "input.txt"
        input_file.write_text("hello world\nthis is a test")

        # First operation: uppercase
        temp1 = tmp_path / "temp1.txt"
        result1 = runner.invoke(main, [str(input_file), '--case', 'upper', '-o', str(temp1)])
        assert result1.exit_code == 0

        # Second operation: replace
        output_file = tmp_path / "final.txt"
        result2 = runner.invoke(main, [str(temp1), '--replace', 'HELLO', 'GOODBYE', '-o', str(output_file)])
        assert result2.exit_code == 0

        # Check final result
        final_content = output_file.read_text()
        assert "GOODBYE WORLD" in final_content
        assert "THIS IS A TEST" in final_content

    def test_all_operations_together(self, runner):
        """Test using all operations at once."""
        result = runner.invoke(main, ['--stdin', '--word-count', '--char-count',
                                '--line-count', '--replace', 'test', 'exam',
                                '--case', 'upper'],
                                input="This is a test\nSecond line")
        assert result.exit_code == 0
        assert "Words: 6" in result.output
        assert "Characters: 26" in result.output
        assert "Lines: 2" in result.output
        assert "THIS IS A EXAM" in result.output
        assert "SECOND LINE" in result.output