"""
Text processing operations module.

This module provides various text processing operations
for the CLI text processor utility.
"""


def count_words(text: str) -> int:
    """
    Count the number of words in the given text.

    Args:
        text: The input text to process.

    Returns:
        The number of words in the text.
    """
    if not text:
        return 0
    return len(text.split())


def count_characters(text: str) -> int:
    """
    Count the number of characters in the given text.

    Args:
        text: The input text to process.

    Returns:
        The number of characters in the text.
    """
    return len(text)


def count_lines(text: str) -> int:
    """
    Count the number of lines in the given text.

    Args:
        text: The input text to process.

    Returns:
        The number of lines in the text.
    """
    if not text:
        return 0
    # Split by newline and count, accounting for final line without newline
    lines = text.split('\n')
    # Don't count empty final element if text ends with newline
    if lines and lines[-1] == '':
        return len(lines) - 1
    return len(lines)


def replace_text(text: str, old: str, new: str) -> str:
    """
    Replace occurrences of old text with new text.

    Args:
        text: The input text to process.
        old: The text to search for.
        new: The text to replace with.

    Returns:
        The text with replacements made.
    """
    return text.replace(old, new)


def convert_case(text: str, case: str) -> str:
    """
    Convert text to the specified case.

    Args:
        text: The input text to process.
        case: The case to convert to ('upper', 'lower', 'title').

    Returns:
        The text converted to the specified case.

    Raises:
        ValueError: If an invalid case is specified.
    """
    case_map = {
        'upper': text.upper,
        'lower': text.lower,
        'title': text.title,
    }

    if case not in case_map:
        raise ValueError(f"Invalid case: {case}. Must be one of: {', '.join(case_map.keys())}")

    return case_map[case]()