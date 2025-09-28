#!/usr/bin/env python3
"""
CLI Text Processing Utility.

A command-line utility for processing text files with multiple operations.
"""

import sys
import click
from pathlib import Path
from typing import Optional

from operations import (
    count_words,
    count_characters,
    count_lines,
    replace_text,
    convert_case,
)


@click.command()
@click.option('--word-count', is_flag=True, help='Count words in the text')
@click.option('--char-count', is_flag=True, help='Count characters in the text')
@click.option('--line-count', is_flag=True, help='Count lines in the text')
@click.option('--replace', nargs=2, help='Replace text (old new)')
@click.option('--case', type=click.Choice(['upper', 'lower', 'title']),
              help='Convert text case')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.argument('input_file', type=click.Path(exists=True), required=False)
def main(word_count: bool, char_count: bool, line_count: bool,
         replace: Optional[tuple], case: Optional[str],
         output: Optional[str], input_file: Optional[str]) -> None:
    """
    Process text files with various operations.

    Can read from a file or stdin and write to a file or stdout.
    """
    try:
        # Read input
        if input_file:
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    text = f.read()
            except PermissionError:
                click.echo(f"Error: Permission denied to read '{input_file}'", err=True)
                sys.exit(1)
            except Exception as e:
                click.echo(f"Error reading file '{input_file}': {e}", err=True)
                sys.exit(1)
        else:
            # Read from stdin
            text = sys.stdin.read()

        # Check if at least one operation is specified
        if not any([word_count, char_count, line_count, replace, case]):
            click.echo("Error: No operation specified. Use --help for usage.", err=True)
            sys.exit(2)

        # Perform operations
        result = text
        output_lines = []

        # Counting operations (these don't modify text, just report)
        if word_count:
            count = count_words(text)
            output_lines.append(f"Words: {count}")

        if char_count:
            count = count_characters(text)
            output_lines.append(f"Characters: {count}")

        if line_count:
            count = count_lines(text)
            output_lines.append(f"Lines: {count}")

        # Text modification operations
        if replace:
            result = replace_text(result, replace[0], replace[1])

        if case:
            result = convert_case(result, case)

        # Output
        if output:
            try:
                with open(output, 'w', encoding='utf-8') as f:
                    # If we have counting results, write them first
                    if output_lines:
                        for line in output_lines:
                            f.write(line + '\n')
                    # If we have modified text, write it
                    if replace or case:
                        f.write(result)
            except PermissionError:
                click.echo(f"Error: Permission denied to write to '{output}'", err=True)
                sys.exit(1)
            except Exception as e:
                click.echo(f"Error writing to file '{output}': {e}", err=True)
                sys.exit(1)
        else:
            # Write to stdout
            if output_lines:
                for line in output_lines:
                    click.echo(line)
            # If we have modified text, write it
            if replace or case:
                click.echo(result, nl=False)

    except KeyboardInterrupt:
        click.echo("\nOperation cancelled.", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()