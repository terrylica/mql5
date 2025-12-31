# MQL5 Documentation Extraction Patterns

## Summary

This document captures the patterns and lessons learned from extracting the complete MQL5 official documentation.

## Final Statistics

- **Total Pages**: 973 markdown files
- **Total Size**: 10 MB
- **Link Validation**: 0 errors (11,176 total links, 8,661 OK, 2,515 excluded)
- **Starting Errors**: 6,228 broken links
- **Final Errors**: 0 broken links
- **Reduction**: 100%

## HTML Structure Patterns

### MQL5 Documentation CSS Classes

| Class                      | Purpose                                         | Handling                     |
| -------------------------- | ----------------------------------------------- | ---------------------------- |
| `div.docsContainer`        | Main content container                          | Entry point for extraction   |
| `p.p_Function`             | Function description                            | Convert to description text  |
| `p.p_CodeExample`          | Code examples                                   | Extract as `mql5` code block |
| `p.p_BoldTitles`           | Section headings                                | Convert to H2                |
| `p.p_FunctionParameter`    | Parameter names                                 | Bold text                    |
| `p.p_ParameterDesrciption` | Parameter description (note: typo in MQL5 HTML) | Definition text              |
| `p.p_Text`                 | Regular text                                    | Paragraph                    |
| `p.p_FunctionRemark`       | Remarks/notes                                   | Blockquote                   |
| `p.p_SeeAlso`              | Related links                                   | "See Also" section           |
| `span.f_CodeExample`       | Code spans                                      | Inline code                  |

### Critical Pattern: Code Duplication in Tables

**Problem**: MQL5 documentation duplicates code content in both:

1. `<table>` elements (for visual formatting)
2. `<p class="p_CodeExample">` elements (semantic code)

**Solution**: Added `is_code_table()` function to detect and skip tables containing code:

```python
def is_code_table(table_element) -> bool:
    """Detect if a table contains code (should be skipped)."""
    all_text = table_element.get_text()

    # MQL5 code indicators
    mql5_keywords = [
        'void ', 'int ', 'double ', 'bool ', 'string ',
        '#include', '#define', '#property',
        'return(', 'if(', 'for(', 'while(',
        'class ', 'public:', 'private:', 'protected:',
        '//---', '//+--',  # MQL5 comment style
    ]

    for keyword in mql5_keywords:
        if keyword in all_text:
            return True

    return False
```

### Language Tag Fix

**Problem**: Hardcoded `python` language tag for code blocks
**Solution**: Changed to `mql5` for proper syntax highlighting

## Extraction Workflow

1. **Playwright Download**: Use anti-detection settings (user-agent, viewport)
2. **Rate Limiting**: 5-10 second random delays between requests (CRITICAL)
3. **BeautifulSoup Parse**: Extract from `div.docsContainer`
4. **Link Conversion**: Convert internal links to relative markdown paths
5. **URL Sanitization**: Filter malformed URLs (`%C2%A0`, `https:/www`, `http:/www`)
6. **Markdown Output**: Structured conversion with proper sections

## Cascading Link Resolution

The extraction process requires multiple cycles due to cascading broken links:

| Cycle   | Pages | Duration | Description        |
| ------- | ----- | -------- | ------------------ |
| Initial | 98    | -        | Core documentation |
| Cycle 2 | 186   | 24 min   | First cascade      |
| Cycle 3 | 86    | 13 min   | Second cascade     |
| Cycle 4 | 41    | 6 min    | Third cascade      |
| Cycle 5 | 10    | 2 min    | Fourth cascade     |
| Cycle 6 | 6     | 1 min    | Fifth cascade      |
| Cycle 7 | 3     | 0.5 min  | Final cascade      |

**Pattern**: Each extraction reveals new internal links that require additional pages.

## lychee.toml Configuration

```toml
# MQL5 Documentation Link Validation Config
exclude = [
  'https:/www',           # Missing slash in https
  'http:/www',            # Missing slash in http
  '%C2%A0',               # URL-encoded non-breaking space
  '^https?://(www\.)?linkedin\.com',
  '^https?://(www\.)?(twitter|x)\.com',
  '^https?://(www\.)?facebook\.com',
]
exclude_all_private = true
include_mail = false
timeout = 30
max_concurrency = 8
accept = [200, 204, 301, 302, 307, 308]
```

## Key Files

| File                                          | Purpose                                  |
| --------------------------------------------- | ---------------------------------------- |
| `scripts/official_docs_extractor.py`          | Core extraction logic with deduplication |
| `scripts/extract_complete_docs_playwright.py` | Playwright-based batch extraction        |
| `lychee.toml`                                 | Link validation configuration            |
| `/tmp/fix_links_properly.py`                  | Post-extraction link fixer               |

## Anti-Detection Measures

1. **User-Agent**: Standard Chrome/macOS user agent
2. **Viewport**: 1920x1080 (standard desktop)
3. **Variable Delays**: Random 5-10 seconds between requests
4. **Sequential Only**: Never parallel requests to same domain
5. **NetworkIdle**: Wait for page to fully load

## Lessons Learned

1. **Never hardcode language tags** - Always use the correct language for the content
2. **Detect code-in-tables pattern** - MQL5 docs duplicate content for visual formatting
3. **Plan for cascading links** - Each extraction reveals new dependencies
4. **Use lychee exclusions** - Handle malformed URLs at validation level
5. **Rate limit aggressively** - Bot detection triggers 24h+ blocks
