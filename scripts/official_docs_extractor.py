#!/usr/bin/env python3
"""
Official MQL5 Documentation Extractor

Handles official docs structure which is completely different from user articles:
- Container: div.docsContainer (not div.content)
- Code: <span class="f_CodeExample"> (not <pre class="code">)
- Paragraphs: Multiple classes (p_Function, p_CodeExample, p_BoldTitles, etc.)
- Tables: Inline with content (not separated at end)
"""

from bs4 import BeautifulSoup
import sys
from urllib.parse import urlparse, urljoin
import re


def extract_text_with_links(element) -> str:
    """Extract text from element, converting <a> tags to markdown links.

    Args:
        element: BeautifulSoup element

    Returns:
        Text with markdown links
    """
    result = []

    def process_node(node):
        """Recursively process nodes to build text with markdown links."""
        if isinstance(node, str):
            # Text node
            return node
        elif node.name == 'a' and node.get('href'):
            # Link - convert to markdown
            link_text = node.get_text()
            href = node['href']
            # Sanitize malformed URLs (extraction artifacts)
            malformed_indicators = ['%C2%A0', 'https:/www', 'http:/www']
            if any(pattern in href for pattern in malformed_indicators):
                return link_text  # Return text only, skip broken link
            return f'[{link_text}]({href})'
        else:
            # Other element - process children
            parts = []
            for child in node.children:
                parts.append(process_node(child))
            return ''.join(parts)

    return process_node(element).strip()


def convert_links_to_relative(soup, current_url: str, docs_base: str = '/en/docs') -> None:
    """Convert internal documentation links to relative markdown paths.

    Modifies soup in-place, converting:
    - https://www.mql5.com/en/docs/ABC/xyz → ../ABC/xyz.md
    - /en/docs/ABC/xyz → ../ABC/xyz.md
    - /en/docs/ABC/xyz#section → ../ABC/xyz.md#section
    - External links → unchanged

    Args:
        soup: BeautifulSoup object to modify
        current_url: Current page URL (e.g., 'https://www.mql5.com/en/docs/basis/syntax')
        docs_base: Base path for docs (default: '/en/docs')
    """

    # Extract current path from URL
    parsed = urlparse(current_url)
    current_path = parsed.path  # e.g., '/en/docs/basis/syntax'

    # Validate current path starts with docs_base
    if not current_path.startswith(docs_base):
        raise ValueError(f"Current URL path '{current_path}' does not start with docs_base '{docs_base}'")

    # Get current page's relative path within docs (e.g., 'basis/syntax')
    current_relative = current_path[len(docs_base):].lstrip('/')
    # Depth = number of directory levels (slashes), NOT +1
    # For 'dateandtime/timelocal', depth is 1 (one dir to escape)
    # The old + 1 caused links to escape out of complete_docs/
    current_depth = current_relative.count('/') if current_relative else 0

    # Find all links
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']

        # Parse the link
        link_parsed = urlparse(href)

        # Check if it's an internal docs link
        is_internal = False
        target_path = None
        anchor = link_parsed.fragment

        if link_parsed.netloc == 'www.mql5.com' or link_parsed.netloc == 'mql5.com':
            # Absolute URL to MQL5.com
            if link_parsed.path.startswith(docs_base):
                is_internal = True
                target_path = link_parsed.path
        elif not link_parsed.netloc and link_parsed.path.startswith(docs_base):
            # Relative URL starting with /en/docs
            is_internal = True
            target_path = link_parsed.path
        elif not link_parsed.netloc and link_parsed.path and not link_parsed.path.startswith('/'):
            # Relative path (rare but possible)
            # Resolve it relative to current URL
            absolute = urljoin(current_url, href)
            resolved_parsed = urlparse(absolute)
            if resolved_parsed.path.startswith(docs_base):
                is_internal = True
                target_path = resolved_parsed.path

        if is_internal and target_path:
            # Extract relative path within docs
            target_relative = target_path[len(docs_base):].lstrip('/')

            # Calculate relative path from current page to target
            if not target_relative:
                # Link to docs index
                relative_link = '../' * current_depth + 'index.md'
            else:
                # Calculate path
                relative_link = '../' * current_depth + target_relative + '.md'

            # Add anchor if present
            if anchor:
                relative_link += '#' + anchor

            # Update the href
            a_tag['href'] = relative_link


def is_code_table(table_element) -> bool:
    """Detect if a table contains code (should be skipped in favor of p_CodeExample).

    MQL5 docs often duplicate code in both <table> and <p class="p_CodeExample">.
    This function identifies tables that contain code rather than semantic data.

    Detection heuristics:
    1. Single-cell tables (1x1) are usually function signatures
    2. Tables with MQL5 keywords indicate code content
    3. Tables with code formatting indicators

    Returns:
        True if table appears to contain code (should be skipped)
    """
    rows = table_element.find_all('tr')

    # Get all cell text
    all_text = table_element.get_text()

    # MQL5 code indicators
    mql5_keywords = [
        'void ', 'int ', 'double ', 'bool ', 'string ', 'float ', 'long ', 'datetime ',
        'color ', 'char ', 'uchar ', 'short ', 'ushort ', 'uint ', 'ulong ',
        '#include', '#define', '#property',
        'return(', 'if(', 'for(', 'while(',
        'ArrayResize(', 'ArrayFree(', 'ArraySize(',
        'class ', 'public:', 'private:', 'protected:',
        '//---', '//+--',  # MQL5 comment style
    ]

    # Check for code indicators
    for keyword in mql5_keywords:
        if keyword in all_text:
            return True

    # Single-cell tables with curly braces or function signatures
    if len(rows) == 1:
        cells = rows[0].find_all(['td', 'th'])
        if len(cells) == 1:
            cell_text = cells[0].get_text()
            # Function signature patterns
            if '(' in cell_text and ')' in cell_text:
                return True
            # Block delimiters
            if '{' in cell_text or '}' in cell_text:
                return True

    return False


def extract_official_docs(html_path: str, source_url: str = None) -> dict:
    """Extract content from official MQL5 documentation HTML.

    Args:
        html_path: Path to HTML file
        source_url: Original URL for reference (optional)
    """

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Convert internal links to relative markdown paths (if source URL provided)
    if source_url:
        convert_links_to_relative(soup, source_url)

    # Find main container
    container = soup.find('div', class_='docsContainer')
    if not container:
        raise ValueError("docsContainer not found")

    # Extract title from H1
    title_tag = container.find('h1')
    title = title_tag.get_text().strip() if title_tag else "Unknown"

    # Process all elements in order (paragraphs AND tables)
    content_blocks = []
    current_code_block = []

    # Find all relevant elements (p and table tags) in document order
    for element in container.find_all(['p', 'table'], recursive=True):
        if element.name == 'table':
            # Skip tables that contain code (will be captured by p_CodeExample)
            if is_code_table(element):
                continue

            # Save any pending code block first
            if current_code_block:
                content_blocks.append({
                    'type': 'code',
                    'language': 'mql5',
                    'text': '\n'.join(current_code_block)
                })
                current_code_block = []

            # Extract table data
            rows = []
            for tr in element.find_all('tr'):
                cells = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                if cells:  # Only add non-empty rows
                    rows.append(cells)

            if rows:
                content_blocks.append({
                    'type': 'table',
                    'rows': rows
                })
            continue

        # Process paragraphs
        p = element
        classes = p.get('class', [])
        if not classes:
            continue

        p_class = classes[0]  # Primary class
        text = extract_text_with_links(p)

        if p_class == 'p_Function':
            # Function description
            content_blocks.append({
                'type': 'description',
                'text': text
            })

        elif p_class == 'p_CodeExample':
            # Code example - handle all span types and br tags
            # Process children (not descendants) to avoid duplication
            code_lines = []
            current_line_parts = []

            for elem in p.children:
                if elem.name == 'br':
                    # Line break - save current line and start new one
                    if current_line_parts or code_lines:  # Ensure we don't skip empty first line
                        code_lines.append(''.join(current_line_parts))
                        current_line_parts = []
                elif elem.name == 'span':
                    # Code span - get text (this handles nested spans correctly)
                    text = elem.get_text()
                    current_line_parts.append(text)
                elif isinstance(elem, str):
                    # Direct text node
                    text = elem.strip()
                    if text:
                        current_line_parts.append(text)

            # Don't forget the last line
            if current_line_parts:
                code_lines.append(''.join(current_line_parts))

            # Add all lines to current code block
            current_code_block.extend(code_lines)

        elif p_class == 'p_BoldTitles':
            # Section title (Parameters, Return Value, etc.)
            # Save any pending code block first
            if current_code_block:
                content_blocks.append({
                    'type': 'code',
                    'language': 'mql5',
                    'text': '\n'.join(current_code_block)
                })
                current_code_block = []

            content_blocks.append({
                'type': 'heading',
                'level': 2,
                'text': text
            })

        elif p_class == 'p_FunctionParameter':
            # Parameter name
            content_blocks.append({
                'type': 'parameter',
                'name': text
            })

        elif p_class == 'p_ParameterDesrciption':  # Note: typo in MQL5 HTML
            # Parameter description
            content_blocks.append({
                'type': 'parameter_desc',
                'text': text
            })

        elif p_class == 'p_Text':
            # Regular text
            content_blocks.append({
                'type': 'text',
                'text': text
            })

        elif p_class == 'p_FunctionRemark':
            # Remarks
            content_blocks.append({
                'type': 'remark',
                'text': text
            })

        elif p_class == 'p_SeeAlso':
            # See also links
            content_blocks.append({
                'type': 'see_also',
                'text': text
            })

    # Save any remaining code block
    if current_code_block:
        content_blocks.append({
            'type': 'code',
            'language': 'mql5',
            'text': '\n'.join(current_code_block)
        })

    # Count code blocks and tables
    code_block_count = len([b for b in content_blocks if b['type'] == 'code'])
    table_count = len([b for b in content_blocks if b['type'] == 'table'])

    return {
        'title': title,
        'source_url': source_url,
        'content_blocks': content_blocks,
        'stats': {
            'total_blocks': len(content_blocks),
            'code_blocks': code_block_count,
            'tables': table_count
        }
    }


def convert_to_markdown(extracted: dict) -> str:
    """Convert extracted content to markdown."""

    lines = []

    # Title
    lines.append(f"# {extracted['title']}\n")

    # Source URL (if provided)
    if extracted.get('source_url'):
        lines.append(f"**Source**: {extracted['source_url']}\n")
        lines.append("---\n")

    # Content blocks (in order!)
    for block in extracted['content_blocks']:
        block_type = block['type']

        if block_type == 'description':
            lines.append(f"{block['text']}\n")

        elif block_type == 'heading':
            level = block.get('level', 2)
            prefix = '#' * level
            lines.append(f"{prefix} {block['text']}\n")

        elif block_type == 'code':
            lang = block.get('language', 'python')
            lines.append(f"```{lang}")
            lines.append(block['text'])
            lines.append("```\n")

        elif block_type == 'parameter':
            lines.append(f"**{block['name']}**")

        elif block_type == 'parameter_desc':
            lines.append(f": {block['text']}\n")

        elif block_type == 'text':
            lines.append(f"{block['text']}\n")

        elif block_type == 'remark':
            lines.append(f"> {block['text']}\n")

        elif block_type == 'see_also':
            lines.append(f"**See Also**: {block['text']}\n")

        elif block_type == 'table':
            # Render table inline
            rows = block['rows']
            if not rows:
                continue

            lines.append('')  # Blank line before table

            # Header row
            if rows[0]:
                lines.append('| ' + ' | '.join(rows[0]) + ' |')
                lines.append('| ' + ' | '.join(['---'] * len(rows[0])) + ' |')

            # Data rows
            for row in rows[1:]:
                if row:
                    lines.append('| ' + ' | '.join(row) + ' |')

            lines.append('')  # Blank line after table

    return '\n'.join(lines)


if __name__ == '__main__':
    import os

    html_path = sys.argv[1] if len(sys.argv) > 1 else 'docs-page.html'
    source_url = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Extracting from: {html_path}")
    if source_url:
        print(f"Source URL: {source_url}")

    # Extract
    extracted = extract_official_docs(html_path, source_url)

    # Show stats
    print(f"\n=== Extraction Stats ===")
    print(f"Title: {extracted['title']}")
    print(f"Total blocks: {extracted['stats']['total_blocks']}")
    print(f"Code blocks: {extracted['stats']['code_blocks']}")
    print(f"Tables: {extracted['stats']['tables']}")

    # Convert to markdown
    markdown = convert_to_markdown(extracted)

    # Show preview
    print(f"\n=== Markdown Preview (first 1000 chars) ===")
    print(markdown[:1000])

    # Save
    output_path = html_path.replace('.html', '.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"\n✅ Saved to: {output_path}")
    print(f"Word count: {len(markdown.split())}")

    # Auto-delete HTML file after successful extraction
    if os.path.exists(html_path) and html_path.endswith('.html'):
        try:
            os.remove(html_path)
            print(f"🗑️  Deleted HTML: {html_path}")
        except Exception as e:
            print(f"⚠️  Could not delete HTML: {e}")
