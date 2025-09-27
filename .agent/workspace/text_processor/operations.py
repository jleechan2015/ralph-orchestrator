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


def replace_text(text: str, old: str, new: str,
                 case_sensitive: bool = True, count: int = -1) -> str:
    """Replace occurrences of a substring in text.

    Args:
        text: The input text to perform replacements in.
        old: The substring to search for.
        new: The substring to replace with.
        case_sensitive: Whether to perform case-sensitive matching (default True).
        count: Maximum number of replacements to make. -1 means replace all.

    Returns:
        The text with replacements made.

    Raises:
        TypeError: If text is None.
    """
    if text is None:
        raise TypeError("text cannot be None")

    if not old:
        return text

    if case_sensitive:
        if count == -1:
            return text.replace(old, new)
        else:
            return text.replace(old, new, count)
    else:
        # Case-insensitive replacement using regex
        import re
        pattern = re.escape(old)
        flags = re.IGNORECASE
        if count == -1:
            return re.sub(pattern, new, text, flags=flags)
        else:
            return re.sub(pattern, new, text, count=count, flags=flags)


def replace_text_regex(text: str, pattern: str, replacement: str,
                       case_sensitive: bool = True,
                       multiline: bool = False) -> str:
    """Replace text using regular expressions.

    Args:
        text: The input text to perform replacements in.
        pattern: The regular expression pattern to search for.
        replacement: The replacement string (can include backreferences).
        case_sensitive: Whether to perform case-sensitive matching (default True).
        multiline: Whether to enable multiline mode (default False).

    Returns:
        The text with regex replacements made.

    Raises:
        ValueError: If the regex pattern is invalid.
    """
    import re

    if not text:
        return text

    flags = 0
    if not case_sensitive:
        flags |= re.IGNORECASE
    if multiline:
        flags |= re.MULTILINE

    try:
        return re.sub(pattern, replacement, text, flags=flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")