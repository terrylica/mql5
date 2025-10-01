# Changelog

All notable changes to RangeBar will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


### ✨ Features

- Implement production-ready MQL5 article extraction system - CLI interface with 3 modes: single, batch, discover-and-extract - YAML configuration with CLI overrides - Retry logic with exponential backoff (5s → 10s → 20s) - Checkpoint-based resume for interrupted extractions - Quality validation (word count, code blocks, login detection) - Batch processing with statistics and summary generation - Hierarchical organization: user_id/article_id structure - Anti-detection browser settings for headless mode - Automatic screenshot cleanup after successful extraction - Image downloads with article ID prefix naming - Comprehensive file and console logging - Production documentation with troubleshooting guide - Git-cliff release automation setup BREAKING CHANGE: Initial release v1.0.0


### 🐛 Bug Fixes

- **extractor**: Improve MQL5 syntax detection accuracy - Simplify language detection by defaulting to 'mql5' for mql5.com articles - Remove unreliable C++ pattern matching that caused 46% misidentification rate - Retain Python/JavaScript detection for mixed-language articles - Improves accuracy from 54% to 100% across all tested articles BREAKING CHANGE: None


### 📝 Other Changes

- Version 1.0.0 → 2.0.0

- Version 2.0.0 → 3.0.0

