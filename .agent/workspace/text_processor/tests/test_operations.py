"""Tests for text processing operations module."""

import pytest
from text_processor.operations import (
    count_lines,
    count_words,
    count_characters,
    count_characters_no_spaces
)


class TestCountingOperations:
    """Test cases for counting operations."""

    def test_count_lines_empty_text(self):
        """Test counting lines in empty text."""
        assert count_lines("") == 0

    def test_count_lines_single_line(self):
        """Test counting single line."""
        assert count_lines("Hello World") == 1

    def test_count_lines_multiple_lines(self):
        """Test counting multiple lines."""
        text = "Line 1\nLine 2\nLine 3"
        assert count_lines(text) == 3

    def test_count_lines_with_empty_lines(self):
        """Test counting with empty lines."""
        text = "Line 1\n\nLine 3\n"
        assert count_lines(text) == 4

    def test_count_words_empty_text(self):
        """Test counting words in empty text."""
        assert count_words("") == 0

    def test_count_words_single_word(self):
        """Test counting single word."""
        assert count_words("Hello") == 1

    def test_count_words_multiple_words(self):
        """Test counting multiple words."""
        assert count_words("Hello World from Python") == 4

    def test_count_words_with_punctuation(self):
        """Test counting words with punctuation."""
        assert count_words("Hello, World! How are you?") == 5

    def test_count_words_with_multiple_spaces(self):
        """Test counting words with multiple spaces."""
        assert count_words("Hello    World   Test") == 3

    def test_count_words_with_newlines(self):
        """Test counting words with newlines."""
        assert count_words("Hello\nWorld\nTest") == 3

    def test_count_characters_empty_text(self):
        """Test counting characters in empty text."""
        assert count_characters("") == 0

    def test_count_characters_single_char(self):
        """Test counting single character."""
        assert count_characters("a") == 1

    def test_count_characters_with_spaces(self):
        """Test counting characters including spaces."""
        assert count_characters("Hello World") == 11

    def test_count_characters_with_newlines(self):
        """Test counting characters including newlines."""
        assert count_characters("Hello\nWorld") == 11

    def test_count_characters_no_spaces_empty(self):
        """Test counting characters without spaces in empty text."""
        assert count_characters_no_spaces("") == 0

    def test_count_characters_no_spaces_single_word(self):
        """Test counting characters without spaces in single word."""
        assert count_characters_no_spaces("Hello") == 5

    def test_count_characters_no_spaces_multiple_words(self):
        """Test counting characters without spaces in multiple words."""
        assert count_characters_no_spaces("Hello World") == 10

    def test_count_characters_no_spaces_with_newlines(self):
        """Test counting characters without spaces or newlines."""
        assert count_characters_no_spaces("Hello\nWorld\n") == 10

    def test_count_characters_no_spaces_with_tabs(self):
        """Test counting characters without spaces or tabs."""
        assert count_characters_no_spaces("Hello\tWorld") == 10