# Tests

## Test Files

- `test_access.py` - Test MQL5.com authentication
- `test_attachment_extraction.py` - Test attachment handling
- `test_attachment_simple.py` - Simple attachment test

## Test Fixtures

- `fixtures/test_batch.txt` - Batch test URLs
- `fixtures/test_resume_urls.txt` - Resume test URLs
- `fixtures/test_urls.txt` - General test URLs

## Running Tests

```bash
# Run individual test
.venv/bin/python tests/test_access.py

# Run all tests
.venv/bin/python -m pytest tests/

# Run with verbose output
.venv/bin/python -m pytest tests/ -v
```

## Implementation Notes

All test files use absolute paths and have zero dependencies on `lib/` modules.
Tests remain functional after relocation without code changes.
