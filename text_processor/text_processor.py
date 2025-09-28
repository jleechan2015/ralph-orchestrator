#!/usr/bin/env python3
"""Text Processor CLI - A command-line utility for processing text files."""

import sys
import click
from pathlib import Path
from typing import Optional

from operations import (
    count_words,
    count_characters,
    count_lines,
    replace_text,
    convert_case
)


@click.command()
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--word-count', is_flag=True, help='Count words in the text')
@click.option('--char-count', is_flag=True, help='Count characters in the text')
@click.option('--line-count', is_flag=True, help='Count lines in the text')
@click.option('--replace', nargs=2, help='Replace text (old new)')
@click.option('--case', type=click.Choice(['upper', 'lower', 'title']), help='Convert text case')
@click.option('--stdin', is_flag=True, help='Read from stdin instead of file')
def main(input_file: Optional[str], output: Optional[str], word_count: bool,
         char_count: bool, line_count: bool, replace: Optional[tuple],
         case: Optional[str], stdin: bool):
    """Text Processor - Process text files with various operations.

    Read text from a file or stdin, apply operations, and output results.

    Examples:
        # Count words in a file
        python text_processor.py input.txt --word-count

        # Replace text and save to new file
        python text_processor.py input.txt --replace old new -o output.txt

        # Process from stdin
        echo "Hello World" | python text_processor.py --stdin --word-count

        # Convert case
        python text_processor.py input.txt --case upper
    """

    # Validate input source
    if not stdin and not input_file:
        click.echo("Error: Either provide an input file or use --stdin flag", err=True)
        sys.exit(1)

    if stdin and input_file:
        click.echo("Error: Cannot use both input file and --stdin", err=True)
        sys.exit(1)

    # Check if at least one operation is specified
    if not any([word_count, char_count, line_count, replace, case]):
        click.echo("Error: No operation specified. Use --help for usage information", err=True)
        sys.exit(1)

    # Read input text
    try:
        if stdin:
            text = sys.stdin.read()
        else:
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()
    except FileNotFoundError:
        click.echo(f"Error: File '{input_file}' not found", err=True)
        sys.exit(1)
    except PermissionError:
        click.echo(f"Error: Permission denied reading '{input_file}'", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error reading input: {e}", err=True)
        sys.exit(1)

    # Store results
    results = []
    processed_text = text

    # Apply operations
    try:
        if word_count:
            count = count_words(text)
            results.append(f"Words: {count}")

        if char_count:
            count = count_characters(text)
            results.append(f"Characters: {count}")

        if line_count:
            count = count_lines(text)
            results.append(f"Lines: {count}")

        if replace:
            old_text, new_text = replace
            processed_text = replace_text(processed_text, old_text, new_text)
            if not output:
                results.append(f"Replaced '{old_text}' with '{new_text}'")

        if case:
            processed_text = convert_case(processed_text, case)
            if not output:
                results.append(f"Converted to {case} case")

    except Exception as e:
        click.echo(f"Error processing text: {e}", err=True)
        sys.exit(1)

    # Output results
    try:
        if output:
            # Write processed text to output file
            with open(output, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            click.echo(f"Output written to: {output}")

            # Still show counts if requested
            for result in results:
                if result.startswith(('Words:', 'Characters:', 'Lines:')):
                    click.echo(result)
        else:
            # Show results to stdout
            if results:
                for result in results:
                    click.echo(result)

            # If text was modified but no output file specified, show the modified text
            if (replace or case) and processed_text != text:
                click.echo("\nProcessed text:")
                click.echo(processed_text, nl=False)

    except PermissionError:
        click.echo(f"Error: Permission denied writing to '{output}'", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error writing output: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()