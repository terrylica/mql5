# 1.0.0 (2025-12-31)


### Bug Fixes

* documentation mismatch and broken --no-checkpoint flag ([18d536f](https://github.com/terrylica/mql5/commit/18d536fd0a78cce3486267ad75aaafe4bd56814a))
* **extractor:** improve MQL5 syntax detection accuracy ([1a5b220](https://github.com/terrylica/mql5/commit/1a5b220adf79ab24dd42f434bd20e4304c2b7d26))
* **extractor:** prevent bot detection and fix article discovery ([5834e67](https://github.com/terrylica/mql5/commit/5834e674ed0638fc629e86b81d326ae883594c64))
* resolve 15k+ broken links and malformed documentation formatting ([210d548](https://github.com/terrylica/mql5/commit/210d548e2ab84af5487943a60db0589056b39057))


### Code Refactoring

* relocate build config to .config/ ([d4c6fa2](https://github.com/terrylica/mql5/commit/d4c6fa20f08a34667d926ba438ee2a213287d79e))


### Features

* add MQL5 custom indicator collection ([dc1f24b](https://github.com/terrylica/mql5/commit/dc1f24b9b7931db8c8da6199a086d43e1856f785))
* add official MQL5 documentation extraction tools ([bcc8e51](https://github.com/terrylica/mql5/commit/bcc8e51223755d05cb0b844f0b740b0c3c52dc5d))
* add TradingView Pine Script indicator collection ([800e860](https://github.com/terrylica/mql5/commit/800e860c5fa52a88cd020ad6eefe69f8948f4e8e))
* **extractor:** add authentication support and expand article collection ([72ba70a](https://github.com/terrylica/mql5/commit/72ba70ae44b005b8825389564767e240539b1b8f))
* implement production-ready MQL5 article extraction system ([1364261](https://github.com/terrylica/mql5/commit/1364261e04a0b2aacdfaeaa6577ca612df279744))


### BREAKING CHANGES

* git-cliff requires -c flag after this change
- Before: git cliff --bumped-version
- After: git cliff -c .config/cliff.toml --bumped-version

Research findings:
- git-cliff searches default locations, won't find config without -c flag
- CI/CD pipelines must update (Agent 3 validation)
- Follows XDG Base Directory Specification

SLO: 99% availability (requires -c flag, breaking change)
SLO: 100% correctness (configs relocate cleanly)
SLO: 100% observability (git cliff -c .config/cliff.toml tested)
SLO: 90% maintainability (requires flag in CI/CD)

Impact: CI/CD pipelines need updating
* **extractor:** None
* Initial release v1.0.0

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
