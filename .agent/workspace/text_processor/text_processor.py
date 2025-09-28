#!/usr/bin/env python3
"""Command-line text processing utility.

This module provides a CLI interface for various text processing operations
including word/character/line counting, text replacement, and case conversion.
"""

import sys
import argparse
from typing import Optional

from operations import (
    count_lines, count_words, count_characters, count_characters_no_spaces,
    replace_text, replace_text_regex,
    to_uppercase, to_lowercase, to_title_case, to_sentence_case,
    swap_case, to_camel_case, to_snake_case
)


def parse_arguments(args=None):
    """Parse command-line arguments.

    Args:
        args: List of arguments to parse (defaults to sys.argv[1:])

    Returns:
        Namespace object with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Text processing utility with various operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --count-words input.txt
  %(prog)s --uppercase input.txt --output output.txt
  %(prog)s --replace "old" "new" input.txt
  echo "hello world" | %(prog)s --uppercase -
        """
    )

    # Input file
    parser.add_argument('file', help='Input file (use "-" for stdin)')

    # Output options
    parser.add_argument('--output', '-o', metavar='FILE',
                        help='Output file (default: stdout)')

    # Counting operations
    count_group = parser.add_argument_group('counting operations')
    count_group.add_argument('--count-lines', '-l', action='store_true',
                             help='Count number of lines')
    count_group.add_argument('--count-words', '-w', action='store_true',
                             help='Count number of words')
    count_group.add_argument('--count-chars', '-c', action='store_true',
                             help='Count number of characters')
    count_group.add_argument('--count-chars-no-spaces', action='store_true',
                             help='Count characters excluding spaces')

    # Replacement operations
    replace_group = parser.add_argument_group('replacement operations')
    replace_group.add_argument('--replace', '-r', nargs=2, metavar=('OLD', 'NEW'),
                               help='Replace text')
    replace_group.add_argument('--replace-regex', nargs=2, metavar=('PATTERN', 'REPLACEMENT'),
                               help='Replace using regex pattern')
    replace_group.add_argument('--ignore-case', '-i', action='store_true',
                               help='Case-insensitive replacement')
    replace_group.add_argument('--replace-count', type=int, metavar='N',
                               help='Maximum number of replacements')

    # Case conversion operations
    case_group = parser.add_argument_group('case conversion operations')
    case_group.add_argument('--uppercase', '-u', action='store_true',
                            help='Convert to uppercase')
    case_group.add_argument('--lowercase', action='store_true',
                            help='Convert to lowercase')
    case_group.add_argument('--titlecase', action='store_true',
                            help='Convert to title case')
    case_group.add_argument('--sentencecase', action='store_true',
                            help='Convert to sentence case')
    case_group.add_argument('--swapcase', action='store_true',
                            help='Swap case of characters')
    case_group.add_argument('--camelcase', action='store_true',
                            help='Convert to camelCase')
    case_group.add_argument('--snakecase', action='store_true',
                            help='Convert to snake_case')

    return parser.parse_args(args)


def process_text(text: str, args) -> str:
    """Process text according to command-line arguments.

    Args:
        text: Input text to process
        args: Parsed command-line arguments

    Returns:
        Processed text or statistics string
    """
    results = []

    # Counting operations (can be combined)
    if args.count_lines:
        lines = count_lines(text)
        results.append(f"Lines: {lines}")

    if args.count_words:
        words = count_words(text)
        results.append(f"Words: {words}")

    if args.count_chars:
        chars = count_characters(text)
        results.append(f"Characters: {chars}")

    if args.count_chars_no_spaces:
        chars_no_spaces = count_characters_no_spaces(text)
        results.append(f"Characters (no spaces): {chars_no_spaces}")

    # If we have counting results, return them
    if results:
        return '\n'.join(results)

    # Text transformation operations (applied in sequence)
    result = text

    # Replacement operations
    if args.replace:
        old, new = args.replace
        count = args.replace_count if hasattr(args, 'replace_count') and args.replace_count else -1
        result = replace_text(result, old, new,
                              case_sensitive=not args.ignore_case if hasattr(args, 'ignore_case') else True,
                              count=count)

    if args.replace_regex:
        pattern, replacement = args.replace_regex
        result = replace_text_regex(result, pattern, replacement,
                                     case_sensitive=not args.ignore_case if hasattr(args, 'ignore_case') else True)

    # Case conversion operations (only one should be active)
    if args.uppercase:
        result = to_uppercase(result)
    elif args.lowercase:
        result = to_lowercase(result)
    elif args.titlecase:
        result = to_title_case(result)
    elif args.sentencecase:
        result = to_sentence_case(result)
    elif args.swapcase:
        result = swap_case(result)
    elif args.camelcase:
        result = to_camel_case(result)
    elif args.snakecase:
        result = to_snake_case(result)

    return result


def process_file(filename: str, args) -> str:
    """Process a file according to command-line arguments.

    Args:
        filename: Path to input file or '-' for stdin
        args: Parsed command-line arguments

    Returns:
        Processed text or statistics string

    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If the file can't be read
    """
    try:
        if filename == '-':
            # Read from stdin
            text = sys.stdin.read()
        else:
            # Read from file
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    text = f.read()
            except FileNotFoundError:
                raise FileNotFoundError(f"File not found: {filename}")
            except PermissionError:
                raise PermissionError(f"Permission denied: {filename}")
            except Exception as e:
                # Re-raise other exceptions with context
                raise IOError(f"Error reading file {filename}: {e}")

    except Exception as e:
        # Let specific exceptions bubble up
        raise

    return process_text(text, args)


def main() -> int:
    """Main entry point for the text processor CLI.

    Returns:
        Exit code: 0 for success, 1 for error, 2 for argument parsing error
    """
    try:
        # Parse arguments
        args = parse_arguments()

        # Process the file
        result = process_file(args.file, args)

        # Handle output
        if hasattr(args, 'output') and args.output:
            # Write to output file
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"Output written to {args.output}", file=sys.stderr)
            except Exception as e:
                print(f"Error writing to output file: {e}", file=sys.stderr)
                return 1
        else:
            # Write to stdout
            print(result, end='')

        return 0

    except FileNotFoundError as e:
        print(f"Error: File not found: {str(e).replace('File not found: ', '')}", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"Error: Permission denied: {str(e).replace('Permission denied: ', '')}", file=sys.stderr)
        return 1
    except SystemExit as e:
        # argparse exits with code 2 for argument errors
        raise
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())