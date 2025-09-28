"""Test cases for the command-line interface."""

import sys
import os
import tempfile
import pytest
from io import StringIO
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add parent directory to path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import text_processor
from text_processor import main, parse_arguments, process_file, process_text


class TestParseArguments:
    """Test cases for argument parsing."""

    def test_parse_count_lines(self):
        """Test parsing count lines arguments."""
        args = parse_arguments(['--count-lines', 'input.txt'])
        assert args.count_lines is True
        assert args.file == 'input.txt'

    def test_parse_count_words(self):
        """Test parsing count words arguments."""
        args = parse_arguments(['--count-words', 'input.txt'])
        assert args.count_words is True
        assert args.file == 'input.txt'

    def test_parse_count_chars(self):
        """Test parsing count characters arguments."""
        args = parse_arguments(['--count-chars', 'input.txt'])
        assert args.count_chars is True
        assert args.file == 'input.txt'

    def test_parse_count_chars_no_spaces(self):
        """Test parsing count characters without spaces arguments."""
        args = parse_arguments(['--count-chars-no-spaces', 'input.txt'])
        assert args.count_chars_no_spaces is True
        assert args.file == 'input.txt'

    def test_parse_replace_text(self):
        """Test parsing replace text arguments."""
        args = parse_arguments(['--replace', 'old', 'new', 'input.txt'])
        assert args.replace == ['old', 'new']
        assert args.file == 'input.txt'

    def test_parse_replace_regex(self):
        """Test parsing replace regex arguments."""
        args = parse_arguments(['--replace-regex', r'\d+', 'NUM', 'input.txt'])
        assert args.replace_regex == [r'\d+', 'NUM']
        assert args.file == 'input.txt'

    def test_parse_case_conversion(self):
        """Test parsing case conversion arguments."""
        args = parse_arguments(['--uppercase', 'input.txt'])
        assert args.uppercase is True
        assert args.file == 'input.txt'

    def test_parse_output_file(self):
        """Test parsing output file argument."""
        args = parse_arguments(['--uppercase', 'input.txt', '--output', 'output.txt'])
        assert args.output == 'output.txt'

    def test_parse_case_insensitive_replace(self):
        """Test parsing case-insensitive replace option."""
        args = parse_arguments(['--replace', 'old', 'new', 'input.txt', '--ignore-case'])
        assert args.ignore_case is True

    def test_parse_stdin_input(self):
        """Test parsing stdin input option."""
        args = parse_arguments(['--uppercase', '-'])
        assert args.file == '-'

    def test_parse_multiple_operations(self):
        """Test parsing multiple operations."""
        args = parse_arguments(['--count-lines', '--count-words', 'input.txt'])
        assert args.count_lines is True
        assert args.count_words is True


class TestProcessText:
    """Test cases for text processing function."""

    def test_process_count_lines(self):
        """Test counting lines."""
        args = MagicMock()
        args.count_lines = True
        args.count_words = False
        args.count_chars = False
        args.count_chars_no_spaces = False
        args.replace = None
        args.replace_regex = None
        args.uppercase = False
        args.lowercase = False
        args.titlecase = False
        args.sentencecase = False
        args.swapcase = False
        args.camelcase = False
        args.snakecase = False

        result = process_text("Line 1\nLine 2\nLine 3", args)
        assert "Lines: 3" in result

    def test_process_count_words(self):
        """Test counting words."""
        args = MagicMock()
        args.count_lines = False
        args.count_words = True
        args.count_chars = False
        args.count_chars_no_spaces = False
        args.replace = None
        args.replace_regex = None
        args.uppercase = False
        args.lowercase = False
        args.titlecase = False
        args.sentencecase = False
        args.swapcase = False
        args.camelcase = False
        args.snakecase = False

        result = process_text("Hello world test", args)
        assert "Words: 3" in result

    def test_process_uppercase(self):
        """Test uppercase conversion."""
        args = MagicMock()
        args.count_lines = False
        args.count_words = False
        args.count_chars = False
        args.count_chars_no_spaces = False
        args.replace = None
        args.replace_regex = None
        args.uppercase = True
        args.lowercase = False
        args.titlecase = False
        args.sentencecase = False
        args.swapcase = False
        args.camelcase = False
        args.snakecase = False

        result = process_text("hello world", args)
        assert result == "HELLO WORLD"

    def test_process_replace_text(self):
        """Test text replacement."""
        args = MagicMock()
        args.count_lines = False
        args.count_words = False
        args.count_chars = False
        args.count_chars_no_spaces = False
        args.replace = ['old', 'new']
        args.replace_regex = None
        args.uppercase = False
        args.lowercase = False
        args.titlecase = False
        args.sentencecase = False
        args.swapcase = False
        args.camelcase = False
        args.snakecase = False
        args.ignore_case = False
        args.replace_count = None

        result = process_text("old text with old word", args)
        assert result == "new text with new word"

    def test_process_multiple_counts(self):
        """Test multiple counting operations."""
        args = MagicMock()
        args.count_lines = True
        args.count_words = True
        args.count_chars = True
        args.count_chars_no_spaces = True
        args.replace = None
        args.replace_regex = None
        args.uppercase = False
        args.lowercase = False
        args.titlecase = False
        args.sentencecase = False
        args.swapcase = False
        args.camelcase = False
        args.snakecase = False

        result = process_text("Hello\nWorld", args)
        assert "Lines: 2" in result
        assert "Words: 2" in result
        assert "Characters: 11" in result
        assert "Characters (no spaces): 10" in result


class TestProcessFile:
    """Test cases for file processing function."""

    def test_process_existing_file(self):
        """Test processing an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content\nLine 2")
            temp_file = f.name

        try:
            args = MagicMock()
            args.count_lines = True
            args.count_words = False
            args.count_chars = False
            args.count_chars_no_spaces = False
            args.replace = None
            args.replace_regex = None
            args.uppercase = False
            args.lowercase = False
            args.titlecase = False
            args.sentencecase = False
            args.swapcase = False
            args.camelcase = False
            args.snakecase = False

            result = process_file(temp_file, args)
            assert "Lines: 2" in result
        finally:
            os.unlink(temp_file)

    def test_process_nonexistent_file(self):
        """Test processing a non-existent file."""
        args = MagicMock()

        with pytest.raises(FileNotFoundError, match="File not found"):
            process_file("nonexistent_file.txt", args)

    def test_process_file_permission_error(self):
        """Test processing a file with permission error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_file = f.name

        try:
            # Make file unreadable
            os.chmod(temp_file, 0o000)

            args = MagicMock()

            with pytest.raises(PermissionError, match="Permission denied"):
                process_file(temp_file, args)
        finally:
            # Restore permissions and delete
            os.chmod(temp_file, 0o644)
            os.unlink(temp_file)

    def test_process_stdin(self):
        """Test processing stdin input."""
        args = MagicMock()
        args.count_words = True
        args.count_lines = False
        args.count_chars = False
        args.count_chars_no_spaces = False
        args.replace = None
        args.replace_regex = None
        args.uppercase = False
        args.lowercase = False
        args.titlecase = False
        args.sentencecase = False
        args.swapcase = False
        args.camelcase = False
        args.snakecase = False

        with patch('sys.stdin', StringIO("Hello world test")):
            result = process_file('-', args)
            assert "Words: 3" in result


class TestMain:
    """Test cases for main function."""

    def test_main_with_file(self):
        """Test main function with file input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_file = f.name

        try:
            test_args = ['--count-words', temp_file]
            with patch('sys.argv', ['text_processor.py'] + test_args):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    result = main()
                    assert result == 0
                    assert "Words: 2" in fake_out.getvalue()
        finally:
            os.unlink(temp_file)

    def test_main_with_output_file(self):
        """Test main function with output file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("hello world")
            input_file = f.name

        output_file = tempfile.mktemp(suffix='.txt')

        try:
            test_args = ['--uppercase', input_file, '--output', output_file]
            with patch('sys.argv', ['text_processor.py'] + test_args):
                result = main()
                assert result == 0

                # Check output file content
                with open(output_file, 'r') as f:
                    content = f.read()
                    assert content == "HELLO WORLD"
        finally:
            os.unlink(input_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_main_with_error(self):
        """Test main function with error handling."""
        test_args = ['--count-words', 'nonexistent_file.txt']
        with patch('sys.argv', ['text_processor.py'] + test_args):
            with patch('sys.stderr', new=StringIO()) as fake_err:
                result = main()
                assert result == 1
                assert "Error: File not found" in fake_err.getvalue()

    def test_main_no_arguments(self):
        """Test main function with no arguments."""
        with patch('sys.argv', ['text_processor.py']):
            with patch('sys.stderr', new=StringIO()):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 2  # argparse exit code for missing arguments

    def test_main_help(self):
        """Test main function with help argument."""
        test_args = ['--help']
        with patch('sys.argv', ['text_processor.py'] + test_args):
            with pytest.raises(SystemExit) as exc_info:
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    assert "usage:" in fake_out.getvalue().lower()
            assert exc_info.value.code == 0