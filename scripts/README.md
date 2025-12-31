# Scripts

## Official Documentation Extraction

### `official_docs_extractor.py`

Extracts official MQL5 documentation pages (Python MetaTrader5 API).

**Usage**:

```bash
# Download HTML
curl -s "https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksfrom_py" > page.html

# Extract with auto-delete
.venv/bin/python scripts/official_docs_extractor.py page.html "URL"

# Result: page.md created, page.html auto-deleted
```

**Features**:

- Handles `div.docsContainer` HTML structure (different from user articles)
- Preserves inline tables and code examples
- Embeds source URL in markdown
- Auto-deletes HTML after conversion

**Output**: Markdown file with function documentation

---

### `extract_all_python_docs.sh`

Batch extraction of all 32 Python MetaTrader5 API functions.

**Usage**:

```bash
./scripts/extract_all_python_docs.sh
```

**Features**:

- Extracts complete Python MT5 API (32 functions)
- Auto-deletes HTML files after conversion
- Progress reporting

**Output**: `official_docs/` directory with 32 markdown files

---

## User Article Extraction

For user article extraction, use the main CLI:

```bash
.venv/bin/python mql5_extract.py discover-and-extract
```

See [CLAUDE.md](../CLAUDE.md) for complete usage guide.

---

## Legacy Scripts

See `legacy/` directory for deprecated scripts kept for reference.
