#!/usr/bin/env python3
"""
Simple MQL5 Article Extractor
Based on the successful debug pattern that actually works.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import httpx

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class SimpleMQL5Extractor:
    """Simple, working MQL5 article extractor."""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.results_dir = Path("simple_extraction_results")
        self.results_dir.mkdir(exist_ok=True)

    async def extract_article(self, url: str) -> Dict[str, Any]:
        """Extract article using the proven working approach."""

        article_id = self._extract_id_from_url(url)
        result = {
            "url": url,
            "article_id": article_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "content": {
                "title": None,
                "author": None,
                "user_id": None,
                "word_count": 0,
                "main_content": None,
                "code_blocks": [],
                "images": []
            }
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                print(f"🔗 Navigating to: {url}")
                await page.goto(url)
                await page.wait_for_load_state('networkidle')

                # Take screenshot for debugging
                screenshot_path = self.results_dir / f"screenshot_{article_id}.png"
                await page.screenshot(path=str(screenshot_path))
                print(f"📸 Screenshot saved: {screenshot_path}")

                # Get the page HTML
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract using verified selectors
                await self._extract_title(soup, result)
                await self._extract_author(soup, result)
                await self._extract_user_id(soup, result)
                await self._extract_images(soup, result)       # Extract images first
                await self._extract_code_blocks(soup, result)  # Extract code blocks second
                await self._extract_content(soup, result)      # Then content with placeholders

                # Create article folder and download images
                article_folder = self._create_article_folder(article_id, result["content"]["title"], result["content"]["user_id"])
                if result["content"]["images"]:
                    result["content"]["images"] = await self._download_images(result, article_folder)

                result["success"] = True
                result["article_folder"] = str(article_folder)
                print("✅ Extraction successful")

            except Exception as e:
                print(f"❌ Extraction failed: {e}")
                result["error"] = str(e)

            finally:
                await browser.close()

        # Save results
        await self._save_results(result)
        return result

    async def _extract_title(self, soup: BeautifulSoup, result: Dict):
        """Extract title using verified selector."""
        title_element = soup.select_one('title')
        if title_element:
            title = title_element.get_text().strip()
            # Remove MQL5 site suffix
            title = re.sub(r' - MQL5 Articles?$', '', title)
            result["content"]["title"] = title
            print(f"📰 Title: {title}")

    async def _extract_author(self, soup: BeautifulSoup, result: Dict):
        """Extract author using verified selectors."""
        # Try verified selectors
        author_selectors = ['.author', 'a[href*="/users/"]']

        for selector in author_selectors:
            author_element = soup.select_one(selector)
            if author_element:
                author = author_element.get_text().strip()
                if author and len(author) > 0:
                    result["content"]["author"] = author
                    print(f"👤 Author: {author}")
                    return

        result["content"]["author"] = "Unknown Author"
        print("❓ Author: Unknown")

    async def _extract_user_id(self, soup: BeautifulSoup, result: Dict):
        """Extract user ID from meta tag."""
        # Look for meta tag with article:author property
        meta_author = soup.select_one('meta[property="article:author"]')
        if meta_author:
            author_url = meta_author.get('content', '')
            # Extract user ID from URL like "https://www.mql5.com/en/users/USER_ID"
            import re
            match = re.search(r'/users/([^/?]+)', author_url)
            if match:
                user_id = match.group(1)
                result["content"]["user_id"] = user_id
                print(f"🆔 User ID: {user_id}")
                return

        result["content"]["user_id"] = "unknown"
        print("❓ User ID: Unknown")

    async def _extract_content(self, soup: BeautifulSoup, result: Dict):
        """Extract main content using verified selector with proper formatting."""
        content_element = soup.select_one('.content')
        if content_element:
            # First, replace images with placeholders to preserve their positions (images already extracted)
            img_elements = content_element.find_all('img')
            for i, img_elem in enumerate(img_elements):
                img_elem.replace_with(f"\n\n[IMAGE_{i}]\n\n")

            # Replace code blocks with placeholders (they were already extracted)
            code_elements = content_element.find_all('pre', class_='code')
            for i, code_elem in enumerate(code_elements):
                code_elem.replace_with(f"\n\n[CODE_BLOCK_{i}]\n\n")

            # Process HTML to markdown-like format
            formatted_content = self._html_to_markdown(content_element)

            # Clean up excessive whitespace but preserve paragraph breaks
            formatted_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted_content)
            formatted_content = re.sub(r'[ \t]+', ' ', formatted_content)
            formatted_content = formatted_content.strip()

            result["content"]["main_content"] = formatted_content
            result["content"]["word_count"] = len(formatted_content.split())
            print(f"📝 Content: {result['content']['word_count']} words")
            print(f"📝 Preview: {formatted_content[:200]}...")
        else:
            print("❌ No content found with .content selector")

    def _html_to_markdown(self, element):
        """Convert HTML structure to markdown format."""
        # Handle different HTML elements
        for tag in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(tag.name[1])
            header_text = tag.get_text().strip()
            tag.replace_with(f"\n\n{'#' * level} {header_text}\n\n")

        # Handle paragraphs
        for p in element.find_all('p'):
            p_text = p.get_text().strip()
            if p_text:
                p.replace_with(f"\n\n{p_text}\n\n")

        # Handle lists
        for ul in element.find_all('ul'):
            list_items = []
            for li in ul.find_all('li'):
                li_text = li.get_text().strip()
                if li_text:
                    list_items.append(f"- {li_text}")
            if list_items:
                ul.replace_with(f"\n\n" + "\n".join(list_items) + "\n\n")

        for ol in element.find_all('ol'):
            list_items = []
            for i, li in enumerate(ol.find_all('li'), 1):
                li_text = li.get_text().strip()
                if li_text:
                    list_items.append(f"{i}. {li_text}")
            if list_items:
                ol.replace_with(f"\n\n" + "\n".join(list_items) + "\n\n")

        # Handle line breaks
        for br in element.find_all('br'):
            br.replace_with('\n')

        # Get final text
        return element.get_text()

    async def _extract_code_blocks(self, soup: BeautifulSoup, result: Dict):
        """Extract code blocks using verified selector."""
        code_elements = soup.select('pre.code')

        for i, code_element in enumerate(code_elements):
            code_text = code_element.get_text().strip()
            if len(code_text) > 10:  # Meaningful code block
                # Detect language
                language = self._detect_language(code_text)

                code_block = {
                    'content': code_text,
                    'language': language,
                    'line_count': len(code_text.split('\n'))
                }
                result["content"]["code_blocks"].append(code_block)

        print(f"💻 Code blocks: {len(result['content']['code_blocks'])}")
        if result["content"]["code_blocks"]:
            first_code = result["content"]["code_blocks"][0]
            print(f"💻 First code language: {first_code['language']}")
            print(f"💻 First code preview: {first_code['content'][:100]}...")

    async def _extract_images(self, soup: BeautifulSoup, result: Dict):
        """Extract images information."""
        img_elements = soup.select('.content img')

        for img in img_elements:
            img_src = img.get('src')
            if img_src:
                # Make absolute URL
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = 'https://www.mql5.com' + img_src

                image_info = {
                    'url': img_src,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'local_path': None,  # Will be filled during download
                    'filename': None,    # Will be filled during download
                    'size_bytes': 0      # Will be filled during download
                }
                result["content"]["images"].append(image_info)

        print(f"🖼️  Images: {len(result['content']['images'])}")

    async def _download_images(self, result: Dict, article_folder: Path) -> List[Dict]:
        """Download all images locally with self-identifying names."""
        article_id = result["article_id"]
        images_folder = article_folder / "images"
        downloaded_images = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, image_info in enumerate(result["content"]["images"], 1):
                try:
                    print(f"📥 Downloading image {i}/{len(result['content']['images'])}: {image_info['url']}")

                    # Download image
                    response = await client.get(image_info['url'])
                    response.raise_for_status()

                    # Determine file extension
                    content_type = response.headers.get('content-type', '')
                    if 'png' in content_type:
                        ext = 'png'
                    elif 'jpeg' in content_type or 'jpg' in content_type:
                        ext = 'jpg'
                    elif 'gif' in content_type:
                        ext = 'gif'
                    elif 'webp' in content_type:
                        ext = 'webp'
                    else:
                        # Try to get from URL
                        url_ext = image_info['url'].split('.')[-1].lower()
                        if url_ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                            ext = 'jpg' if url_ext == 'jpeg' else url_ext
                        else:
                            ext = 'png'  # Default

                    # Create simplified filename (context is in folder structure)
                    description = self._create_image_description(image_info['alt'], image_info['title'])
                    filename = f"image_{i:03d}_{description}.{ext}"

                    # Save image
                    image_path = images_folder / filename
                    with open(image_path, 'wb') as f:
                        f.write(response.content)

                    # Update image info
                    image_info['local_path'] = f"images/{filename}"
                    image_info['filename'] = filename
                    image_info['size_bytes'] = len(response.content)

                    downloaded_images.append(image_info)
                    print(f"✅ Saved: {filename} ({len(response.content):,} bytes)")

                except Exception as e:
                    print(f"❌ Failed to download image {i}: {e}")
                    # Keep original info but mark as failed
                    image_info['local_path'] = None
                    image_info['filename'] = None
                    image_info['download_error'] = str(e)
                    downloaded_images.append(image_info)

        print(f"📁 Downloaded {len([img for img in downloaded_images if img.get('local_path')])} images successfully")
        return downloaded_images

    def _create_image_description(self, alt_text: str, title_text: str) -> str:
        """Create a descriptive filename part from alt text or title."""
        description = alt_text or title_text or "image"

        # Clean up for filename
        description = re.sub(r'[^\w\s-]', '', description.lower())
        description = re.sub(r'[-\s]+', '_', description)
        description = description[:30].strip('_')

        return description or "image"

    def _detect_language(self, code_text: str) -> str:
        """Detect programming language of code block."""
        # MQL5 patterns
        mql5_indicators = [
            r'\b(OnTick|OnInit|OnStart|OnCalculate|OnDeinit)\b',
            r'\b(input\s+|extern\s+)',
            r'\b(CArrayObj|CTrade|CPositionInfo|CSymbolInfo)\b',
            r'\b(OrderSend|OrderSelect|PositionSelect)\b',
            r'\b(PERIOD_|SYMBOL_|ORDER_|DEAL_|POSITION_)',
            r'\b(Ask|Bid|Point|Digits)\b',
            r'#property\s+',
            r'//\+------------------------------------------------------------------+',
        ]

        for pattern in mql5_indicators:
            if re.search(pattern, code_text, re.IGNORECASE):
                return 'mql5'

        # Other languages
        if re.search(r'\b(void|int|double|string)\s+\w+\s*\(', code_text):
            return 'cpp'
        elif re.search(r'\bdef\s+\w+\s*\(', code_text):
            return 'python'
        elif re.search(r'\bfunction\s+\w+\s*\(', code_text):
            return 'javascript'

        return 'unknown'

    def _extract_id_from_url(self, url: str) -> str:
        """Extract article ID from URL."""
        match = re.search(r'/articles/(\d+)', url)
        return match.group(1) if match else "unknown"

    def _create_slug(self, title: str) -> str:
        """Create a URL-friendly slug from article title."""
        if not title:
            return "untitled"

        # Remove site suffix if present
        title = re.sub(r' - MQL5 Articles?$', '', title)

        # Convert to lowercase and replace spaces/special chars
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '_', slug)

        # Limit length and clean up
        slug = slug[:50].strip('_')

        return slug or "untitled"

    def _create_article_folder(self, article_id: str, title: str, user_id: str = None) -> Path:
        """Create hierarchical folder structure: user_id/article_id/files."""
        # Use user_id for top-level folder, fallback to "unknown" if not provided
        user_folder_name = user_id or "unknown"
        user_folder = self.results_dir / user_folder_name
        user_folder.mkdir(exist_ok=True)

        # Create article folder within user folder
        article_folder_name = f"article_{article_id}"
        article_folder = user_folder / article_folder_name
        article_folder.mkdir(exist_ok=True)

        # Create images subfolder
        images_folder = article_folder / "images"
        images_folder.mkdir(exist_ok=True)

        return article_folder

    async def _save_results(self, result: Dict):
        """Save extraction results in self-identifying structure."""
        article_id = result["article_id"]
        title = result["content"].get("title", "Untitled")

        # Get or create article folder
        if result.get("article_folder"):
            article_folder = Path(result["article_folder"])
        else:
            user_id = result["content"].get("user_id")
            article_folder = self._create_article_folder(article_id, title, user_id)

        # Create self-identifying filenames
        slug = self._create_slug(title)

        # Save metadata JSON
        metadata_file = article_folder / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Metadata saved: {metadata_file}")

        # Save images manifest
        if result["content"].get("images"):
            images_manifest = {
                "article_id": article_id,
                "total_images": len(result["content"]["images"]),
                "images": result["content"]["images"]
            }
            manifest_file = article_folder / "images_manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(images_manifest, f, indent=2, ensure_ascii=False)
            print(f"📸 Images manifest saved: {manifest_file}")

        # Create markdown with simplified name (context is in folder structure)
        if result.get("success") and result["content"].get("main_content"):
            md_file = article_folder / "article.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"**Author:** {result['content'].get('author', 'Unknown')}\n")
                f.write(f"**User ID:** {result['content'].get('user_id', 'Unknown')}\n")
                f.write(f"**Article ID:** {article_id}\n")
                f.write(f"**Source:** {result.get('url', '')}\n")
                f.write(f"**Word Count:** {result['content'].get('word_count', 0)}\n")
                f.write(f"**Code Blocks:** {len(result['content'].get('code_blocks', []))}\n")
                f.write(f"**Images:** {len([img for img in result['content'].get('images', []) if img.get('local_path')])}\n\n")
                f.write("---\n\n")

                # Write main content with integrated code blocks and inline images
                main_content = result["content"]["main_content"]

                # Replace code block placeholders with actual formatted code
                for i, code_block in enumerate(result["content"].get("code_blocks", [])):
                    code_placeholder = f"[CODE_BLOCK_{i}]"
                    code_formatted = f"```{code_block['language']}\n{code_block['content']}\n```"
                    main_content = main_content.replace(code_placeholder, code_formatted)

                # Replace image placeholders with actual local images (in original positions)
                for i, image in enumerate(result["content"].get("images", [])):
                    image_placeholder = f"[IMAGE_{i}]"
                    if image.get("local_path"):
                        alt_text = image.get("alt", "MQL5 Trading Strategy Diagram")
                        if not alt_text or alt_text.strip() == "":
                            alt_text = f"Trading Strategy Diagram {i+1}"
                        image_markdown = f"![{alt_text}]({image['local_path']})"
                        main_content = main_content.replace(image_placeholder, image_markdown)
                    else:
                        # Remove placeholder if image failed to download
                        main_content = main_content.replace(image_placeholder, "")

                f.write(main_content)

            print(f"📝 Article saved: {md_file}")
            print(f"📁 Complete article folder: {article_folder}")

if __name__ == "__main__":
    async def test():
        extractor = SimpleMQL5Extractor(headless=False)
        result = await extractor.extract_article("https://www.mql5.com/en/articles/19625")

        print(f"\n🎉 FINAL RESULTS:")
        print(f"Success: {result['success']}")
        print(f"Title: {result['content']['title']}")
        print(f"Author: {result['content']['author']}")
        print(f"Word count: {result['content']['word_count']}")
        print(f"Code blocks: {len(result['content']['code_blocks'])}")

        if result['content']['code_blocks']:
            first_code = result['content']['code_blocks'][0]
            print(f"First code language: {first_code['language']}")

    asyncio.run(test())