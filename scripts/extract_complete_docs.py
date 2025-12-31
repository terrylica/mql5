#!/usr/bin/env python3
"""
Complete MQL5 Documentation Extractor

Extracts entire /en/docs documentation tree with internal link conversion.

Usage:
    python extract_complete_docs.py [--output DIR] [--max-pages N] [--delay SEC]

Features:
- Discovers complete documentation structure
- Converts internal links to relative markdown paths
- Rate limiting (default 2s between requests)
- Progress tracking with statistics
- Directory structure matching URL hierarchy
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

# Import the official docs extractor
sys.path.insert(0, str(Path(__file__).parent))
from official_docs_extractor import extract_official_docs, convert_to_markdown


def discover_docs_urls(base_url: str = 'https://www.mql5.com/en/docs', max_pages: int = None) -> list[str]:
    """Discover all documentation URLs by crawling the docs tree.

    Args:
        base_url: Base documentation URL
        max_pages: Maximum pages to discover (None = unlimited)

    Returns:
        List of discovered URLs
    """

    print(f"🔍 Discovering documentation structure from {base_url}")

    discovered = set()
    to_visit = [base_url]
    visited = set()

    while to_visit and (max_pages is None or len(discovered) < max_pages):
        url = to_visit.pop(0)

        if url in visited:
            continue

        visited.add(url)

        try:
            print(f"  Crawling: {url}")
            response = httpx.get(url, timeout=30, follow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the documentation container
            container = soup.find('div', class_='docsContainer')
            if not container:
                print(f"  ⚠️  No docsContainer found, skipping")
                continue

            # Add this URL to discovered
            discovered.add(url)

            # Find all internal docs links
            for a_tag in container.find_all('a', href=True):
                href = a_tag['href']

                # Parse the link
                if href.startswith('/en/docs'):
                    # Relative path
                    full_url = urljoin(base_url, href)
                elif href.startswith('http') and '/en/docs' in href:
                    # Absolute URL
                    full_url = href
                else:
                    # External or non-docs link
                    continue

                # Remove fragment
                full_url = full_url.split('#')[0]

                # Add to visit queue if not visited
                if full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Error crawling {url}: {e}")
            continue

    print(f"\n✅ Discovered {len(discovered)} documentation pages")
    return sorted(list(discovered))


def extract_page(url: str, output_dir: Path, delay: float = 2.0) -> dict:
    """Extract a single documentation page.

    Args:
        url: Page URL
        output_dir: Output directory
        delay: Delay before extraction (rate limiting)

    Returns:
        Extraction result dict
    """

    print(f"\n📄 Extracting: {url}")

    # Rate limiting
    time.sleep(delay)

    try:
        # Download HTML
        response = httpx.get(url, timeout=30, follow_redirects=True)
        response.raise_for_status()

        # Determine output path from URL
        parsed = urlparse(url)
        path = parsed.path  # e.g., '/en/docs/basis/syntax'

        # Remove /en/docs prefix
        relative_path = path.replace('/en/docs', '').lstrip('/')

        if not relative_path:
            # Root docs page
            relative_path = 'index'

        # Create output directory
        file_path = output_dir / f"{relative_path}.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save HTML temporarily
        html_path = file_path.with_suffix('.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        # Extract using official extractor (with link conversion)
        extracted = extract_official_docs(str(html_path), source_url=url)

        # Convert to markdown
        markdown = convert_to_markdown(extracted)

        # Save markdown
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        # Delete HTML
        html_path.unlink()

        print(f"  ✅ Saved: {file_path}")
        print(f"  📊 {extracted['stats']['total_blocks']} blocks, "
              f"{extracted['stats']['code_blocks']} code, "
              f"{extracted['stats']['tables']} tables")

        return {
            'url': url,
            'file': str(file_path),
            'status': 'success',
            'stats': extracted['stats']
        }

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {
            'url': url,
            'status': 'failed',
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Extract complete MQL5 documentation')
    parser.add_argument('--output', '-o', default='/tmp/mql5-complete-docs',
                        help='Output directory (default: /tmp/mql5-complete-docs)')
    parser.add_argument('--max-pages', '-m', type=int, default=None,
                        help='Maximum pages to extract (default: unlimited)')
    parser.add_argument('--delay', '-d', type=float, default=2.0,
                        help='Delay between requests in seconds (default: 2.0)')
    parser.add_argument('--discover-only', action='store_true',
                        help='Only discover URLs, do not extract')
    parser.add_argument('--urls-file', '-u', type=str, default=None,
                        help='Save/load discovered URLs to/from file')

    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("MQL5 Complete Documentation Extractor")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Max pages: {args.max_pages or 'unlimited'}")
    print(f"Rate limit: {args.delay}s between requests")
    print()

    # Discover or load URLs
    if args.urls_file and os.path.exists(args.urls_file):
        print(f"📂 Loading URLs from {args.urls_file}")
        with open(args.urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"✅ Loaded {len(urls)} URLs")
    else:
        urls = discover_docs_urls(max_pages=args.max_pages)

        if args.urls_file:
            print(f"\n💾 Saving URLs to {args.urls_file}")
            with open(args.urls_file, 'w') as f:
                f.write('\n'.join(urls))

    if args.discover_only:
        print("\n✅ Discovery complete (--discover-only mode)")
        return

    # Extract all pages
    print("\n" + "=" * 60)
    print("Starting Extraction")
    print("=" * 60)

    results = []
    start_time = time.time()

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}]", end=' ')
        result = extract_page(url, output_dir, delay=args.delay)
        results.append(result)

    # Generate statistics
    duration = time.time() - start_time
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'failed'])

    total_blocks = sum(r.get('stats', {}).get('total_blocks', 0) for r in results if 'stats' in r)
    total_code = sum(r.get('stats', {}).get('code_blocks', 0) for r in results if 'stats' in r)
    total_tables = sum(r.get('stats', {}).get('tables', 0) for r in results if 'stats' in r)

    summary = {
        'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': round(duration, 2),
        'total_pages': len(urls),
        'successful': successful,
        'failed': failed,
        'statistics': {
            'total_blocks': total_blocks,
            'total_code_blocks': total_code,
            'total_tables': total_tables
        },
        'results': results
    }

    # Save summary
    summary_path = output_dir / 'extraction_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("Extraction Complete")
    print("=" * 60)
    print(f"✅ Successful: {successful}/{len(urls)}")
    print(f"❌ Failed: {failed}/{len(urls)}")
    print(f"⏱️  Duration: {duration:.1f}s")
    print(f"📊 Total blocks: {total_blocks}")
    print(f"📊 Code blocks: {total_code}")
    print(f"📊 Tables: {total_tables}")
    print(f"\n📁 Output: {output_dir}")
    print(f"📄 Summary: {summary_path}")


if __name__ == '__main__':
    main()
