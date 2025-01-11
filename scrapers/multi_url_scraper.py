import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Set
import re
from urllib.parse import urlparse
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiUrlScraper:
    def __init__(self, keywords: List[str] = None):
        self.keywords = set(map(str.lower, keywords)) if keywords else set()
        self.session = None
        self.results = []

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    def matches_keywords(self, text: str) -> bool:
        if not self.keywords:
            return True
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)

    async def scrape_url(self, url: str) -> Dict:
        try:
            domain = urlparse(url).netloc
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {url}: Status {response.status}")
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Extract all text
                text = soup.get_text(separator=' ', strip=True)

                # Basic property information extraction
                title = soup.find('title').text if soup.find('title') else ''
                price = self._extract_price(soup, text)
                description = self._extract_description(soup)
                
                if not self.matches_keywords(f"{title} {description}"):
                    return None

                property_data = {
                    'url': url,
                    'source': domain,
                    'title': title,
                    'price': price,
                    'description': description,
                    'scraped_at': datetime.now().isoformat(),
                }

                return property_data

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None

    def _extract_price(self, soup, text) -> str:
        # Common price patterns
        price_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $XXX,XXX.XX
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*₪',    # XXX,XXX.XX ₪
            r'₪\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'     # ₪ XXX,XXX.XX
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        # Try common price-related elements
        price_elements = soup.find_all(class_=re.compile(r'price|cost|value', re.I))
        for element in price_elements:
            if element.text.strip():
                return element.text.strip()
        
        return "Price not found"

    def _extract_description(self, soup) -> str:
        # Try common description elements
        desc_elements = soup.find_all(['div', 'p'], class_=re.compile(r'desc|detail|info|about', re.I))
        descriptions = []
        
        for element in desc_elements:
            text = element.get_text(strip=True)
            if len(text) > 50:  # Assume real descriptions are longer than 50 chars
                descriptions.append(text)
        
        return max(descriptions, key=len, default="Description not found")

    async def scrape_urls(self, urls: List[str]) -> List[Dict]:
        await self.init_session()
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        await self.close_session()
        
        # Filter out None results and store
        self.results = [result for result in results if result]
        return self.results

    def save_results(self, filename: str = 'scraping_results.json'):
        """Save results to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

async def main(urls: List[str], keywords: List[str] = None):
    scraper = MultiUrlScraper(keywords=keywords)
    results = await scraper.scrape_urls(urls)
    scraper.save_results()
    return results

if __name__ == "__main__":
    # Example usage
    test_urls = [
        "https://example-real-estate.com/property1",
        "https://example-real-estate.com/property2",
    ]
    test_keywords = ["apartment", "renovated", "parking"]
    
    asyncio.run(main(test_urls, test_keywords))
