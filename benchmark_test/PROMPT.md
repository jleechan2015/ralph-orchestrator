# Task: CLI Text Processing Utility

Create a command-line utility for processing text files with multiple operations and comprehensive testing.

## Requirements

### Core Functionality
- CLI tool that can read, transform, and output text files
- Operations: word count, character count, line count, text replacement, case conversion
- Support file input/output and stdin/stdout
- Use Click for CLI with comprehensive help text

### Error Handling
- Graceful handling of missing files
- Permission errors
- Invalid arguments
- Proper exit codes

### Testing & Quality
- Unit tests covering all operations with edge cases using pytest
- Target 90%+ test coverage
- PEP 8 compliance
- Professional documentation

### Technical Specifications
- Language: Python 3.11+
- Structure: Single module with clear separation of concerns
- Include README with usage examples and API documentation
- Dependencies: Click for CLI, pytest for testing

## Success Criteria

The task is complete when:

1. ✅ CLI executable with `--help` functionality works correctly
2. ✅ All 5 text operations (word count, char count, line count, replace, case conversion) working correctly
3. ✅ Error handling for common failure scenarios (missing files, permissions, invalid args)
4. ✅ 90%+ test coverage with passing tests using pytest
5. ✅ Professional documentation with usage examples in README
6. ✅ Code follows PEP 8 standards and is properly structured

## Expected Directory Structure

```
text_processor/
├── text_processor.py      # Main CLI module
├── operations.py          # Text processing operations
├── tests/
│   ├── test_processor.py  # CLI tests
│   └── test_operations.py # Operation tests
├── README.md             # Documentation
└── requirements.txt      # Dependencies
```

## Validation Commands

The implementation must pass these validation tests:

```bash
# Functional validation
python text_processor.py --help
echo "Hello World" | python text_processor.py --word-count
python text_processor.py --replace "old" "new" input.txt

# Test validation
pytest tests/ -v --cov=text_processor
```

<!-- Ralph will continue iterating until all success criteria are met -->