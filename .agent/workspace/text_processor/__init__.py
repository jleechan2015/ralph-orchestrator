"""
Text Processing Utility Package

A command-line text processing utility with word/character/line count,
text replacement, and case conversion operations.
"""

__version__ = "1.0.0"

from .text_processor import main, parse_arguments, process_file, process_text

__all__ = ['main', 'parse_arguments', 'process_file', 'process_text']