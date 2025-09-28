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


def to_uppercase(text: str) -> str:
    """Convert text to uppercase.

    Args:
        text: The input text to convert.

    Returns:
        The text converted to uppercase.
    """
    return text.upper()


def to_lowercase(text: str) -> str:
    """Convert text to lowercase.

    Args:
        text: The input text to convert.

    Returns:
        The text converted to lowercase.
    """
    return text.lower()


def to_title_case(text: str) -> str:
    """Convert text to title case (capitalize each word).

    Args:
        text: The input text to convert.

    Returns:
        The text converted to title case.
    """
    return text.title()


def to_sentence_case(text: str) -> str:
    """Convert text to sentence case (capitalize first letter of sentences).

    Args:
        text: The input text to convert.

    Returns:
        The text converted to sentence case.
    """
    if not text:
        return text

    import re

    # First convert everything to lowercase
    result = text.lower()

    # Find the first non-whitespace character and capitalize it
    result = re.sub(r'^(\s*)(\w)', lambda m: m.group(1) + m.group(2).upper(), result)

    # Capitalize first letter after sentence endings (. ! ?)
    result = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), result)

    return result


def swap_case(text: str) -> str:
    """Swap the case of each character in text.

    Args:
        text: The input text to convert.

    Returns:
        The text with swapped case for each character.
    """
    return text.swapcase()


def to_camel_case(text: str) -> str:
    """Convert text to camelCase.

    Args:
        text: The input text to convert.

    Returns:
        The text converted to camelCase.
    """
    if not text:
        return text

    import re

    # Replace multiple delimiters with single space
    text = re.sub(r'[-_\s]+', ' ', text)

    # Split into words
    words = text.split()
    if not words:
        return ""

    # Handle leading numbers
    result = []
    for i, word in enumerate(words):
        if i == 0:
            # First word - check if it starts with a number
            if word and word[0].isdigit():
                # Keep numbers as is, capitalize rest
                j = 0
                while j < len(word) and word[j].isdigit():
                    j += 1
                if j < len(word):
                    result.append(word[:j] + word[j:].capitalize())
                else:
                    result.append(word)
            else:
                result.append(word.lower())
        else:
            result.append(word.capitalize())

    return ''.join(result)


def to_snake_case(text: str) -> str:
    """Convert text to snake_case.

    Args:
        text: The input text to convert.

    Returns:
        The text converted to snake_case.
    """
    if not text:
        return text

    import re

    # Handle camelCase and PascalCase by inserting underscores
    # Before uppercase letters that follow lowercase letters
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)

    # Handle consecutive uppercase letters (e.g., HTTPResponse -> HTTP_Response)
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', text)

    # Replace spaces, hyphens, and multiple underscores with single underscore
    text = re.sub(r'[-\s]+', '_', text)

    # Remove multiple underscores
    text = re.sub(r'_+', '_', text)

    # Strip leading/trailing underscores and convert to lowercase
    return text.strip('_').lower()