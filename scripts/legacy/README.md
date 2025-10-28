# Legacy Scripts

These scripts are deprecated and kept for reference only.

## Deprecated Scripts

- `browser_scraper.py` - Replaced by `lib/discovery.py`
- `simple_mql5_extractor.py` - Replaced by `lib/extractor.py`
- `debug_discovery.py` - Debugging script, no longer needed

**Do not use these scripts.** Use `mql5_extract.py` instead.

## Migration

All functionality has been migrated to:

- `lib/extractor.py` - Production extractor with retry logic
- `lib/discovery.py` - Article discovery
- `lib/batch_processor.py` - Batch orchestration
- `mql5_extract.py` - CLI interface
