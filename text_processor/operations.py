"""Text processing operations module."""


def count_words(text: str) -> int:
    """Count the number of words in the text.

    Args:
        text: The input text to process

    Returns:
        The number of words in the text
    """
    if not text:
        return 0
    return len(text.split())


def count_characters(text: str) -> int:
    """Count the number of characters in the text.

    Args:
        text: The input text to process

    Returns:
        The number of characters in the text
    """
    return len(text)


def count_lines(text: str) -> int:
    """Count the number of lines in the text.

    Args:
        text: The input text to process

    Returns:
        The number of lines in the text
    """
    if not text:
        return 0
    return len(text.splitlines())


def replace_text(text: str, old: str, new: str) -> str:
    """Replace all occurrences of old text with new text.

    Args:
        text: The input text to process
        old: The text to replace
        new: The replacement text

    Returns:
        The text with replacements made
    """
    return text.replace(old, new)


def convert_case(text: str, case: str) -> str:
    """Convert text to specified case.

    Args:
        text: The input text to process
        case: The case to convert to ('upper', 'lower', 'title')

    Returns:
        The text converted to the specified case

    Raises:
        ValueError: If an invalid case is specified
    """
    if case == 'upper':
        return text.upper()
    elif case == 'lower':
        return text.lower()
    elif case == 'title':
        return text.title()
    else:
        raise ValueError(f"Invalid case: {case}. Must be 'upper', 'lower', or 'title'")