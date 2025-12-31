#!/usr/bin/env python3
"""
Complete MQL5 Documentation Extractor - Playwright Version with Anti-Detection

Extracts entire /en/docs documentation tree with:
- Playwright (headless browser) instead of httpx
- Anti-detection headers and settings
- Variable random rate limiting to avoid bot detection
- Internal link conversion to relative markdown paths

Usage:
    # Discover URLs only (use existing URLs file)
    python extract_complete_docs_playwright.py --urls-file /tmp/mql5-all-docs-urls.txt --discover-only

    # Extract with slow, variable delays
    python extract_complete_docs_playwright.py \\
        --urls-file /tmp/mql5-all-docs-urls.txt \\
        --output /tmp/mql5-complete-docs \\
        --min-delay 3.0 \\
        --max-delay 8.0

CRITICAL: Do NOT use parallel extraction - will trigger IP ban.
         Use slow, sequential extraction with random delays.
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Import the official docs extractor
sys.path.insert(0, str(Path(__file__).parent))
from official_docs_extractor import extract_official_docs, convert_to_markdown


# Anti-detection browser settings (from lib/extractor.py)
ANTI_DETECTION_SETTINGS = {
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'viewport': {'width': 1920, 'height': 1080},
    'locale': 'en-US',
    'timezone_id': 'America/New_York'
}


async def discover_docs_urls_playwright(base_url: str = 'https://www.mql5.com/en/docs',
                                        max_pages: int = None,
                                        min_delay: float = 2.0,
                                        max_delay: float = 5.0) -> list[str]:
    """Discover all documentation URLs using Playwright with anti-detection.

    Args:
        base_url: Base documentation URL
        max_pages: Maximum pages to discover (None = unlimited)
        min_delay: Minimum delay between requests (seconds)
        max_delay: Maximum delay between requests (seconds)

    Returns:
        List of discovered URLs
    """

    print(f"🔍 Discovering documentation structure from {base_url}")
    print(f"⏱️  Random delays: {min_delay}s - {max_delay}s between requests")

    discovered = set()
    to_visit = [base_url]
    visited = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**ANTI_DETECTION_SETTINGS)
        page = await context.new_page()

        try:
            while to_visit and (max_pages is None or len(discovered) < max_pages):
                url = to_visit.pop(0)

                if url in visited:
                    continue

                visited.add(url)

                # Variable random delay
                if len(visited) > 1:  # Skip delay on first request
                    delay = random.uniform(min_delay, max_delay)
                    print(f"  ⏳ Waiting {delay:.1f}s before next request...")
                    await asyncio.sleep(delay)

                try:
                    print(f"  Crawling: {url}")
                    await page.goto(url, timeout=30000, wait_until='networkidle')

                    # Get HTML content
                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')

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

                except Exception as e:
                    print(f"  ❌ Error crawling {url}: {e}")
                    continue

        finally:
            await browser.close()

    print(f"\n✅ Discovered {len(discovered)} documentation pages")
    return sorted(list(discovered))


async def extract_page_playwright(url: str, output_dir: Path,
                                  min_delay: float = 3.0,
                                  max_delay: float = 8.0) -> dict:
    """Extract a single documentation page using Playwright.

    Args:
        url: Page URL
        output_dir: Output directory
        min_delay: Minimum delay before extraction (seconds)
        max_delay: Maximum delay before extraction (seconds)

    Returns:
        Extraction result dict
    """

    print(f"\n📄 Extracting: {url}")

    # Variable random delay for rate limiting
    delay = random.uniform(min_delay, max_delay)
    print(f"  ⏳ Rate limiting: waiting {delay:.1f}s...")
    await asyncio.sleep(delay)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(**ANTI_DETECTION_SETTINGS)
            page = await context.new_page()

            try:
                # Navigate with timeout
                await page.goto(url, timeout=30000, wait_until='networkidle')

                # Get HTML content
                html = await page.content()

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
                    f.write(html)

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

            finally:
                await browser.close()

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {
            'url': url,
            'status': 'failed',
            'error': str(e)
        }


async def batch_extract_playwright(urls: list[str], output_dir: Path,
                                   min_delay: float = 3.0,
                                   max_delay: float = 8.0) -> list[dict]:
    """Extract all pages sequentially with variable random delays.

    Args:
        urls: List of URLs to extract
        output_dir: Output directory
        min_delay: Minimum delay between requests (seconds)
        max_delay: Maximum delay between requests (seconds)

    Returns:
        List of extraction results
    """

    print("\n" + "=" * 60)
    print("Starting Sequential Extraction (Anti-Detection Mode)")
    print("=" * 60)
    print(f"⚠️  SEQUENTIAL ONLY - NO PARALLEL (to avoid bot detection)")
    print(f"⏱️  Random delays: {min_delay}s - {max_delay}s between requests")
    print(f"📦 Total pages: {len(urls)}")
    print(f"⏳ Estimated time: {len(urls) * ((min_delay + max_delay) / 2) / 60:.1f} minutes")
    print()

    results = []
    start_time = time.time()

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}]", end=' ')
        result = await extract_page_playwright(url, output_dir, min_delay, max_delay)
        results.append(result)

    return results


async def main_async():
    parser = argparse.ArgumentParser(
        description='Extract complete MQL5 documentation with Playwright anti-detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract with slow, variable delays (RECOMMENDED)
  python extract_complete_docs_playwright.py \\
      --urls-file /tmp/mql5-all-docs-urls.txt \\
      --min-delay 3.0 --max-delay 8.0

  # Test with just 5 pages
  python extract_complete_docs_playwright.py \\
      --urls-file /tmp/test-urls.txt \\
      --max-pages 5 \\
      --min-delay 2.0 --max-delay 4.0

CRITICAL: Use slow, variable delays to avoid bot detection!
        """
    )

    parser.add_argument('--output', '-o', default='/tmp/mql5-complete-docs',
                        help='Output directory (default: /tmp/mql5-complete-docs)')
    parser.add_argument('--max-pages', '-m', type=int, default=None,
                        help='Maximum pages to extract (default: unlimited)')
    parser.add_argument('--min-delay', type=float, default=3.0,
                        help='Minimum delay between requests in seconds (default: 3.0)')
    parser.add_argument('--max-delay', type=float, default=8.0,
                        help='Maximum delay between requests in seconds (default: 8.0)')
    parser.add_argument('--discover-only', action='store_true',
                        help='Only discover URLs, do not extract')
    parser.add_argument('--urls-file', '-u', type=str, default=None,
                        help='Save/load discovered URLs to/from file')

    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("MQL5 Complete Documentation Extractor (Playwright)")
    print("=" * 60)
    print(f"🌐 Method: Playwright with anti-detection")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Max pages: {args.max_pages or 'unlimited'}")
    print(f"⏱️  Rate limit: {args.min_delay}s - {args.max_delay}s (variable random)")
    print()

    # Discover or load URLs
    if args.urls_file and os.path.exists(args.urls_file):
        print(f"📂 Loading URLs from {args.urls_file}")
        with open(args.urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"✅ Loaded {len(urls)} URLs")
    else:
        urls = await discover_docs_urls_playwright(
            max_pages=args.max_pages,
            min_delay=args.min_delay,
            max_delay=args.max_delay
        )

        if args.urls_file:
            print(f"\n💾 Saving URLs to {args.urls_file}")
            with open(args.urls_file, 'w') as f:
                f.write('\n'.join(urls))

    if args.discover_only:
        print("\n✅ Discovery complete (--discover-only mode)")
        return

    # Limit URLs if max_pages specified
    if args.max_pages:
        urls = urls[:args.max_pages]

    # Extract all pages
    start_time = time.time()
    results = await batch_extract_playwright(
        urls, output_dir,
        min_delay=args.min_delay,
        max_delay=args.max_delay
    )

    # Generate statistics
    duration = time.time() - start_time if results else 0
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
        'rate_limiting': {
            'min_delay_seconds': args.min_delay,
            'max_delay_seconds': args.max_delay,
            'method': 'variable_random'
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


def main():
    """Synchronous wrapper for async main."""
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
