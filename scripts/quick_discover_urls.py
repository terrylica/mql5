#!/usr/bin/env python3
"""
Quick URL Discovery for MQL5 Documentation
Uses httpx (faster than Playwright) for discovery only.
"""

import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def discover_urls(base_url='https://www.mql5.com/en/docs', max_pages=None):
    """Quickly discover documentation URLs using httpx."""
    discovered = set()
    to_visit = [base_url]
    visited = set()

    print(f"🔍 Discovering URLs from {base_url}")

    while to_visit and (max_pages is None or len(discovered) < max_pages):
        url = to_visit.pop(0)

        if url in visited:
            continue

        visited.add(url)

        try:
            print(f"  Crawling [{len(discovered)}]: {url}")
            response = httpx.get(url, timeout=15, follow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            container = soup.find('div', class_='docsContainer')

            if not container:
                continue

            discovered.add(url)

            # Find all internal docs links
            for a_tag in container.find_all('a', href=True):
                href = a_tag['href']

                if href.startswith('/en/docs'):
                    full_url = urljoin(base_url, href)
                elif href.startswith('http') and '/en/docs' in href:
                    full_url = href
                else:
                    continue

                full_url = full_url.split('#')[0]

                if full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    print(f"\n✅ Discovered {len(discovered)} URLs")
    return sorted(list(discovered))

if __name__ == '__main__':
    import sys

    output_file = sys.argv[1] if len(sys.argv) > 1 else 'docs_urls.txt'

    urls = discover_urls()

    with open(output_file, 'w') as f:
        f.write('\n'.join(urls))

    print(f"💾 Saved to: {output_file}")
