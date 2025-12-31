#!/usr/bin/env python3
"""Fix malformed single-column tables containing code in MQL5 docs.

Pattern to remove:
| int  ArrayInitialize(
   char    array[],     // initialized array
   char    value        // value that will be set
   ); |
| --- |

These are duplicate content - the code appears properly in code blocks elsewhere.
"""

import re
import sys
from pathlib import Path

def is_code_table_start(line: str) -> bool:
    """Check if line starts a malformed code table."""
    if not line.startswith('| '):
        return False

    # Code indicators in the first line (with optional leading whitespace after |)
    code_patterns = [
        r'^\| \s*(int|void|double|bool|string|float|long|datetime|color|char|uchar|short|ushort|uint|ulong)\s+\w+',
        r'^\| \s*#(include|define|property)',
        r'^\| \s*class \w+',
        r'^\| \s*struct \w+',
        r'^\| \s*enum \w+',
        # Function declarations
        r'^\| \s*\w+\s+On\w+\s*\(',
        # Continuation of code (indented)
        r'^\| \s{2,}\w+',
        # Multi-line code blocks starting with comments
        r'^\| \s*//[+-]+',
    ]

    for pattern in code_patterns:
        if re.match(pattern, line):
            return True

    return False

def is_multiline_code_table_start(line: str) -> bool:
    """Check if line starts a multi-line code table (| class Foo ... without ending |)."""
    if not line.startswith('| '):
        return False
    # Doesn't end with | (continues on next line)
    if line.rstrip().endswith(' |'):
        return False

    # Code indicators
    code_patterns = [
        r'^\| \s*(class|struct|enum)\s+\w+',
        r'^\| \s*//[+-]+',  # MQL5 comment headers
        r'^\| \s*(for|while|if|switch)\s*\(',  # Control flow
        r'^\| \s*expression\d*;',  # Pseudo-code expressions
        r'^\| \s*\w+\s*[=\[{(]',  # Assignments, arrays, blocks
        r'^\| \s*[A-Z][a-z]+\s+of\s+',  # Description tables: "Sum of variables", etc.
        r'^\| \s*True\s+if\s+',  # Boolean descriptions
        r'^\| \s*[A-Z][a-z]+ing\s+',  # Gerund descriptions: "Adding", "Subtracting"
    ]

    for pattern in code_patterns:
        if re.match(pattern, line):
            return True

    return False

def is_single_line_code_table(line: str, next_line: str) -> bool:
    """Check if this is a single-line code table (e.g., | void OnStart(); |)."""
    if not line.startswith('| ') or not line.rstrip().endswith(' |'):
        return False

    # Check if next line is a table separator
    next_stripped = next_line.strip() if next_line else ''
    if not (next_stripped == '| --- |' or next_stripped.startswith('| ---')):
        return False

    # Check for code patterns in the line
    code_indicators = [
        r'\bvoid\b', r'\bint\b', r'\bdouble\b', r'\bbool\b', r'\bstring\b',
        r'\bclass\b', r'\bstruct\b', r'\benum\b',
        r'\(.*\)', r';',  # Function calls or statements
    ]

    for pattern in code_indicators:
        if re.search(pattern, line):
            return True

    return False

def fix_malformed_tables(content: str) -> tuple[str, int]:
    """Remove malformed single-column tables containing code.

    Returns: (fixed_content, count_of_tables_removed)
    """
    lines = content.split('\n')
    result = []
    i = 0
    tables_removed = 0

    while i < len(lines):
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else ''

        # Check for single-line code table (| void OnStart(); | followed by | --- |)
        if is_single_line_code_table(line, next_line):
            # Skip both lines (the code line and separator)
            tables_removed += 1
            i += 2
            continue

        # Check if this starts a multi-line malformed code table (| class Foo ... }; | pattern)
        if is_multiline_code_table_start(line):
            # Look for line ending with }; | or ); | followed by | --- |
            j = i + 1
            found_end = False

            while j < len(lines):
                current = lines[j]

                # End of multi-line code cell (ends with }; | or similar)
                if current.rstrip().endswith('}; |') or current.rstrip().endswith('); |') or current.rstrip().endswith(' |'):
                    # Check if next line is separator
                    if j + 1 < len(lines) and lines[j + 1].strip() == '| --- |':
                        found_end = True
                        j += 1  # Include the separator
                        break

                # If we hit a code fence or header, stop
                if current.startswith('```') or (current.startswith('#') and not current.startswith('| ')):
                    break

                j += 1

            if found_end:
                tables_removed += 1
                i = j + 1
                continue

        # Check if this starts a single-line malformed code table
        if is_code_table_start(line):
            # Look ahead to find the end of this table
            table_lines = [line]
            j = i + 1
            found_separator = False

            while j < len(lines):
                table_lines.append(lines[j])

                # Single-column table separator
                if lines[j].strip() == '| --- |':
                    found_separator = True
                    break

                # If we hit a blank line or proper content, this isn't a malformed table
                if lines[j].strip() == '' or (lines[j].startswith('#') and not lines[j].startswith('| ')):
                    break

                j += 1

            if found_separator:
                # Skip this malformed table
                tables_removed += 1
                i = j + 1
                continue

        result.append(line)
        i += 1

    return '\n'.join(result), tables_removed

def main():
    docs_dir = Path('/Users/terryli/eon/mql5/mql5_articles/complete_docs')

    total_fixed = 0
    files_modified = 0

    for md_file in docs_dir.rglob('*.md'):
        content = md_file.read_text(encoding='utf-8')
        fixed_content, count = fix_malformed_tables(content)

        if count > 0:
            md_file.write_text(fixed_content, encoding='utf-8')
            files_modified += 1
            total_fixed += count
            print(f"Fixed {count} table(s) in {md_file.relative_to(docs_dir)}")

    print(f"\nTotal: {total_fixed} malformed tables removed from {files_modified} files")

if __name__ == '__main__':
    main()
