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

### Next Tasks
- [ ] Create operations module with counting functions (word, character, line count)
- [ ] Create text replacement functions in operations module
- [ ] Create case conversion functions in operations module
- [ ] Create main CLI module with argparse
- [ ] Add comprehensive error handling
- [ ] Write pytest unit tests for operations
- [ ] Write integration tests for CLI
- [ ] Ensure 90%+ test coverage
