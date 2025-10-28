#!/usr/bin/env python3
"""
Browser-based scraper for MQL5 publications that require JavaScript interaction.
Uses Playwright to click the "66 more..." link to load all 77 articles.
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def discover_all_articles():
    """Discover all 77 articles by clicking the 'more' link via browser automation."""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Navigate to the publications page
        url = "https://www.mql5.com/en/users/29210372/publications"
        print(f"Navigating to: {url}")
        await page.goto(url)

        # Wait for initial content to load
        await page.wait_for_timeout(3000)

        # Look for the "more" link and click it to load additional articles
        print("Looking for 'more' link...")
        more_link = await page.query_selector('a:has-text("more")')
        if more_link:
            print("Found 'more' link, clicking...")
            await more_link.click()
            await page.wait_for_timeout(5000)  # Wait for additional content to load
        else:
            print("No 'more' link found - all articles may already be visible")

        # Extract all article URLs
        print("Extracting article URLs...")
        article_links = await page.query_selector_all('a[href*="/en/articles/"]')

        urls = []
        for link in article_links:
            href = await link.get_attribute('href')
            if href and '/en/articles/' in href:
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = f"https://www.mql5.com{href}"
                urls.append(href)

        # Remove duplicates and sort
        unique_urls = list(set(urls))
        unique_urls.sort(key=lambda x: int(re.search(r'/articles/(\d+)', x).group(1)) if re.search(r'/articles/(\d+)', x) else 0, reverse=True)

        await browser.close()

        print(f"Discovered {len(unique_urls)} unique article URLs")
        return unique_urls

def save_urls(urls):
    """Save discovered URLs to browser_urls.txt"""
    with open('browser_urls.txt', 'w') as f:
        for i, url in enumerate(urls, 1):
            f.write(f"{i}→{url}\n")
    print(f"Saved {len(urls)} URLs to browser_urls.txt")

async def main():
    """Main function to discover and save all article URLs."""
    print("🔍 Starting browser-based article discovery...")

    urls = await discover_all_articles()
    save_urls(urls)

    print("✅ Browser discovery completed!")
    print(f"📊 Total articles discovered: {len(urls)}")

    # Show first few URLs as preview
    print("\n📋 Preview of discovered URLs:")
    for i, url in enumerate(urls[:5], 1):
        print(f"  {i}. {url}")
    if len(urls) > 5:
        print(f"  ... and {len(urls) - 5} more")

if __name__ == "__main__":
    asyncio.run(main())