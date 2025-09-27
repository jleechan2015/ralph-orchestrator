"""Text processing operations module.

This module contains all text processing operations including:
- Text counting (lines, words, characters)
- Text replacement
- Case conversion
"""


def count_lines(text: str) -> int:
    """Count the number of lines in text.

    Args:
        text: The input text to count lines in.

    Returns:
        The number of lines in the text.
    """
    if not text:
        return 0
    # Count actual newline characters plus 1 for the first line
    # If text ends with newline, that creates an additional line
    lines = text.split('\n')
    return len(lines)


def count_words(text: str) -> int:
    """Count the number of words in text.

    Args:
        text: The input text to count words in.

    Returns:
        The number of words in the text.
    """
    if not text:
        return 0
    # Split on any whitespace and filter empty strings
    return len(text.split())


def count_characters(text: str) -> int:
    """Count the total number of characters in text (including spaces).

    Args:
        text: The input text to count characters in.

    Returns:
        The total number of characters including spaces and newlines.
    """
    return len(text)


def count_characters_no_spaces(text: str) -> int:
    """Count the number of characters in text (excluding whitespace).

    Args:
        text: The input text to count characters in.

    Returns:
        The number of characters excluding all whitespace.
    """
    if not text:
        return 0
    # Remove all whitespace characters
    import re
    cleaned_text = re.sub(r'\s+', '', text)
    return len(cleaned_text)