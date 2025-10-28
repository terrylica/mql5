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


def extract_official_docs(html_path: str, source_url: str = None) -> dict:
    """Extract content from official MQL5 documentation HTML.

    Args:
        html_path: Path to HTML file
        source_url: Original URL for reference (optional)
    """

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

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
            # Save any pending code block first
            if current_code_block:
                content_blocks.append({
                    'type': 'code',
                    'language': 'python',
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
        text = p.get_text().strip()

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
                    'language': 'python',
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
            'language': 'python',
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
