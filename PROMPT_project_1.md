Create a command-line text processing utility with word/character/line count, text replacement, and case conversion operations. Include comprehensive CLI with argparse, error handling for file permissions and missing files, and pytest unit tests with 90%+ coverage. Structure: main CLI module, operations module, tests directory. Language: Python 3.11+.

## Progress

### Iteration 1 - COMPLETED
- ✅ Set up basic project structure in `.agent/workspace/text_processor/`
- ✅ Created directory structure:
  - `__init__.py` - Package initialization
  - `operations.py` - Will contain text processing operations
  - `text_processor.py` - Will contain main CLI
  - `tests/` directory with `test_operations.py` and `test_cli.py`
  - `requirements.txt` - Dependencies (pytest, pytest-cov)

### Iteration 2 - COMPLETED
- ✅ Created operations module with counting functions using TDD approach
- ✅ Implemented `count_lines()` - counts lines in text (handles empty lines)
- ✅ Implemented `count_words()` - counts words (handles punctuation and whitespace)
- ✅ Implemented `count_characters()` - counts all characters including spaces
- ✅ Implemented `count_characters_no_spaces()` - counts non-whitespace characters
- ✅ Wrote comprehensive pytest unit tests for counting operations (19 tests, all passing)

### Next Tasks
- [ ] Create text replacement functions in operations module
- [ ] Create case conversion functions in operations module
- [ ] Create main CLI module with argparse
- [ ] Add comprehensive error handling
- [ ] Write pytest unit tests for remaining operations
- [ ] Write integration tests for CLI
- [ ] Ensure 90%+ test coverage
