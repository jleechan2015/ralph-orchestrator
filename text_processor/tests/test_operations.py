"""Tests for text processing operations."""

import pytest
from text_processor.operations import (
    count_words,
    count_characters,
    count_lines,
    replace_text,
    convert_case
)


class TestCountWords:
    """Tests for count_words function."""

    def test_count_words_basic(self):
        """Test basic word counting."""
        assert count_words("Hello World") == 2
        assert count_words("The quick brown fox") == 4
        assert count_words("One") == 1

    def test_count_words_empty(self):
        """Test word counting with empty input."""
        assert count_words("") == 0
        assert count_words("   ") == 0

    def test_count_words_with_punctuation(self):
        """Test word counting with punctuation."""
        assert count_words("Hello, World!") == 2
        assert count_words("It's a test.") == 3

    def test_count_words_with_newlines(self):
        """Test word counting with newlines."""
        assert count_words("Hello\nWorld") == 2
        assert count_words("Line one\nLine two\nLine three") == 6

    def test_count_words_with_tabs(self):
        """Test word counting with tabs."""
        assert count_words("Hello\tWorld") == 2
        assert count_words("Tab\tseparated\twords") == 3

    def test_count_words_mixed_whitespace(self):
        """Test word counting with mixed whitespace."""
        assert count_words("  Hello   World  ") == 2
        assert count_words("\n\nMultiple\n\n\nNewlines\n\n") == 2


class TestCountCharacters:
    """Tests for count_characters function."""

    def test_count_characters_basic(self):
        """Test basic character counting."""
        assert count_characters("Hello") == 5
        assert count_characters("Hello World") == 11
        assert count_characters("123") == 3

    def test_count_characters_empty(self):
        """Test character counting with empty input."""
        assert count_characters("") == 0

    def test_count_characters_with_spaces(self):
        """Test character counting includes spaces."""
        assert count_characters("   ") == 3
        assert count_characters(" a b ") == 5

    def test_count_characters_with_newlines(self):
        """Test character counting with newlines."""
        assert count_characters("Hello\nWorld") == 11
        assert count_characters("\n\n\n") == 3

    def test_count_characters_special_chars(self):
        """Test character counting with special characters."""
        assert count_characters("!@#$%") == 5
        assert count_characters("😀🎉") == 2  # Unicode emoji


class TestCountLines:
    """Tests for count_lines function."""

    def test_count_lines_basic(self):
        """Test basic line counting."""
        assert count_lines("Single line") == 1
        assert count_lines("Line 1\nLine 2") == 2
        assert count_lines("Line 1\nLine 2\nLine 3") == 3

    def test_count_lines_empty(self):
        """Test line counting with empty input."""
        assert count_lines("") == 0

    def test_count_lines_empty_lines(self):
        """Test line counting with empty lines."""
        assert count_lines("\n") == 1  # splitlines() counts this as one empty line
        assert count_lines("\n\n\n") == 3  # Three empty lines
        assert count_lines("text\n\ntext") == 3  # Three lines total

    def test_count_lines_no_trailing_newline(self):
        """Test line counting without trailing newline."""
        assert count_lines("Line 1\nLine 2") == 2
        assert count_lines("Just one line") == 1

    def test_count_lines_with_carriage_return(self):
        """Test line counting with different line endings."""
        assert count_lines("Line 1\rLine 2") == 2  # \r does split in Python's splitlines()
        assert count_lines("Line 1\r\nLine 2") == 2  # Windows line ending


class TestReplaceText:
    """Tests for replace_text function."""

    def test_replace_text_basic(self):
        """Test basic text replacement."""
        assert replace_text("Hello World", "World", "Python") == "Hello Python"
        assert replace_text("foo bar foo", "foo", "baz") == "baz bar baz"

    def test_replace_text_no_match(self):
        """Test replacement when pattern not found."""
        assert replace_text("Hello World", "xyz", "abc") == "Hello World"

    def test_replace_text_empty_strings(self):
        """Test replacement with empty strings."""
        assert replace_text("", "old", "new") == ""
        assert replace_text("Hello World", "", "x") == "xHxexlxlxox xWxoxrxlxdx"
        assert replace_text("Hello World", "Hello", "") == " World"

    def test_replace_text_case_sensitive(self):
        """Test that replacement is case-sensitive."""
        assert replace_text("Hello hello", "hello", "hi") == "Hello hi"
        assert replace_text("HELLO hello", "hello", "hi") == "HELLO hi"

    def test_replace_text_overlapping(self):
        """Test replacement with overlapping patterns."""
        assert replace_text("aaaa", "aa", "b") == "bb"

    def test_replace_text_special_chars(self):
        """Test replacement with special characters."""
        assert replace_text("1+1=2", "+", "-") == "1-1=2"
        assert replace_text("hello@world.com", "@", "[at]") == "hello[at]world.com"


class TestConvertCase:
    """Tests for convert_case function."""

    def test_convert_case_upper(self):
        """Test conversion to uppercase."""
        assert convert_case("hello world", "upper") == "HELLO WORLD"
        assert convert_case("Hello World", "upper") == "HELLO WORLD"
        assert convert_case("123 abc", "upper") == "123 ABC"

    def test_convert_case_lower(self):
        """Test conversion to lowercase."""
        assert convert_case("HELLO WORLD", "lower") == "hello world"
        assert convert_case("Hello World", "lower") == "hello world"
        assert convert_case("123 ABC", "lower") == "123 abc"

    def test_convert_case_title(self):
        """Test conversion to title case."""
        assert convert_case("hello world", "title") == "Hello World"
        assert convert_case("HELLO WORLD", "title") == "Hello World"
        assert convert_case("hello-world", "title") == "Hello-World"
        assert convert_case("it's a test", "title") == "It'S A Test"  # Note: title() behavior

    def test_convert_case_empty(self):
        """Test case conversion with empty string."""
        assert convert_case("", "upper") == ""
        assert convert_case("", "lower") == ""
        assert convert_case("", "title") == ""

    def test_convert_case_invalid(self):
        """Test that invalid case raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            convert_case("Hello", "invalid")
        assert "Invalid case: invalid" in str(exc_info.value)

        with pytest.raises(ValueError):
            convert_case("Hello", "UPPER")  # Case-sensitive

        with pytest.raises(ValueError):
            convert_case("Hello", "capitalize")  # Not supported

    def test_convert_case_special_chars(self):
        """Test case conversion with special characters."""
        assert convert_case("email@example.com", "upper") == "EMAIL@EXAMPLE.COM"
        assert convert_case("Price: $99.99", "lower") == "price: $99.99"
        assert convert_case("hello_world", "title") == "Hello_World"


class TestEdgeCases:
    """Tests for edge cases across all operations."""

    def test_unicode_handling(self):
        """Test operations with Unicode characters."""
        text = "Hello 世界 🌍"
        assert count_words(text) == 3
        assert count_characters(text) == 10
        assert count_lines(text) == 1
        assert replace_text(text, "世界", "World") == "Hello World 🌍"
        assert convert_case(text, "upper") == "HELLO 世界 🌍"

    def test_large_text(self):
        """Test operations with larger text."""
        large_text = "word " * 1000
        assert count_words(large_text) == 1000
        assert count_characters(large_text) == 5000
        assert count_lines(large_text) == 1

    def test_none_like_strings(self):
        """Test operations with strings that look like None."""
        assert count_words("None") == 1
        assert replace_text("None None", "None", "Something") == "Something Something"
        assert convert_case("none", "upper") == "NONE"