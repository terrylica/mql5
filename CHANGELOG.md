# Changelog

All notable changes to MQL5 Article Extraction System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2025-10-28

### Added

- Official MQL5 documentation extraction capability
- Topic-based content organization (tick_data/, python_integration/)
- TICK data research collection (3 official docs + 9 user articles)
- Python MT5 API complete documentation (32 official docs + 15 user articles)
- Extraction scripts for official documentation
  - `scripts/official_docs_extractor.py` (single page extraction)
  - `scripts/extract_all_python_docs.sh` (batch extraction)
- Research documentation directories
  - `docs/tick_research/` (4 research files)
  - `docs/python_research/` (1 research file)
- Content migration system (59 files from /tmp to workspace)

### Changed

- Output structure now supports both user collections and topic collections
- CLAUDE.md updated with topic collections and data sources

## [3.0.0] - 2025-10-01

### Fixed

- MQL5 syntax detection accuracy (54% → 100%)
- Simplified language detection by defaulting to 'mql5' for mql5.com articles
- Removed unreliable C++ pattern matching that caused 46% misidentification rate
- Retained Python/JavaScript detection for mixed-language articles

## [2.0.0] - 2025-09-30

### Added

- Production-ready CLI interface with 3 modes (single, batch, discover-and-extract)
- YAML configuration with CLI overrides
- Retry logic with exponential backoff (5s → 10s → 20s)
- Checkpoint-based resume for interrupted extractions
- Quality validation (word count, code blocks, login detection)
- Batch processing with statistics and summary generation
- Hierarchical organization (user_id/article_id structure)
- Anti-detection browser settings for headless mode
- Automatic screenshot cleanup after successful extraction
- Image downloads with article ID prefix naming
- File and console logging
- Production documentation with troubleshooting guide

## [1.0.0] - 2025-09-29

### Added

- Initial release
