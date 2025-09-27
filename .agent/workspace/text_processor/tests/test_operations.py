"""Tests for text processing operations module."""

import pytest
from text_processor.operations import (
    count_lines,
    count_words,
    count_characters,
    count_characters_no_spaces,
    replace_text,
    replace_text_regex
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


class TestReplacementOperations:
    """Test cases for text replacement operations."""

    def test_replace_text_empty(self):
        """Test replacing text in empty string."""
        assert replace_text("", "old", "new") == ""

    def test_replace_text_no_match(self):
        """Test replacing text when pattern not found."""
        assert replace_text("Hello World", "foo", "bar") == "Hello World"

    def test_replace_text_single_match(self):
        """Test replacing text with single match."""
        assert replace_text("Hello World", "World", "Python") == "Hello Python"

    def test_replace_text_multiple_matches(self):
        """Test replacing text with multiple matches."""
        text = "The cat in the hat"
        assert replace_text(text, "the", "a") == "The cat in a hat"

    def test_replace_text_case_sensitive(self):
        """Test that replacement is case sensitive by default."""
        text = "The the THE"
        assert replace_text(text, "the", "a") == "The a THE"

    def test_replace_text_case_insensitive(self):
        """Test case insensitive replacement."""
        text = "The the THE"
        assert replace_text(text, "the", "a", case_sensitive=False) == "a a a"

    def test_replace_text_with_count(self):
        """Test replacing only first N occurrences."""
        text = "one two one two one"
        assert replace_text(text, "one", "three", count=2) == "three two three two one"

    def test_replace_text_special_chars(self):
        """Test replacing text with special characters."""
        text = "Hello! How are you?"
        assert replace_text(text, "!", "?") == "Hello? How are you?"

    def test_replace_text_multiline(self):
        """Test replacing text across multiple lines."""
        text = "Hello World\nHello Python"
        assert replace_text(text, "Hello", "Hi") == "Hi World\nHi Python"

    def test_replace_text_regex_empty(self):
        """Test regex replacement in empty string."""
        assert replace_text_regex("", r"\d+", "X") == ""

    def test_replace_text_regex_digits(self):
        """Test replacing digits using regex."""
        assert replace_text_regex("abc123def456", r"\d+", "X") == "abcXdefX"

    def test_replace_text_regex_word_boundaries(self):
        """Test replacing with word boundaries."""
        text = "The cat in the cathedral"
        assert replace_text_regex(text, r"\bcat\b", "dog") == "The dog in the cathedral"

    def test_replace_text_regex_groups(self):
        """Test regex replacement with capture groups."""
        text = "John Smith, Jane Doe"
        assert replace_text_regex(text, r"(\w+) (\w+)", r"\2, \1") == "Smith, John, Doe, Jane"

    def test_replace_text_regex_multiline(self):
        """Test regex replacement with multiline flag."""
        text = "Start\nMiddle\nEnd"
        assert replace_text_regex(text, r"^", "> ", multiline=True) == "> Start\n> Middle\n> End"

    def test_replace_text_regex_case_insensitive(self):
        """Test case insensitive regex replacement."""
        text = "Hello HELLO hello"
        assert replace_text_regex(text, r"hello", "hi", case_sensitive=False) == "hi hi hi"

    def test_replace_text_regex_invalid_pattern(self):
        """Test handling of invalid regex pattern."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            replace_text_regex("test", r"[", "replacement")

    def test_replace_text_empty_pattern(self):
        """Test replacing empty pattern."""
        assert replace_text("Hello World", "", "X") == "Hello World"

    def test_replace_text_none_input(self):
        """Test handling None input."""
        with pytest.raises(TypeError):
            replace_text(None, "old", "new")