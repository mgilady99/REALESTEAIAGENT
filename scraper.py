from scrapers.multi_url_scraper import MultiUrlScraper
from scrapers.yad2_scraper import Yad2Scraper
import logging
from datetime import datetime
from models import db, Property, ScrapingLog
import asyncio
from typing import List, Dict
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealEstateScraper:
    def __init__(self):
        self.multi_scraper = MultiUrlScraper()
        self.yad2_scraper = Yad2Scraper()
        self.results = []

    async def scrape_urls(self, urls: List[str], keywords: List[str] = None) -> List[Dict]:
        """
        Scrape multiple URLs for real estate listings
        """
        try:
            # Log the start of scraping
            log_entry = ScrapingLog(
                start_time=datetime.now(),
                status='running',
                urls_count=len(urls)
            )
            db.session.add(log_entry)
            db.session.commit()

            # Use multi_url_scraper for generic URLs
            self.results = await self.multi_scraper.scrape_urls(urls)

            # Process and store results
            for result in self.results:
                # Check if property already exists
                existing_property = Property.query.filter_by(
                    url=result['url']
                ).first()

                if not existing_property:
                    # Create new property
                    new_property = Property(
                        title=result.get('title', ''),
                        description=result.get('description', ''),
                        price=result.get('price', ''),
                        url=result['url'],
                        source=result.get('source', ''),
                        scraped_at=datetime.now()
                    )
                    db.session.add(new_property)

            # Commit changes
            db.session.commit()

            # Update log entry
            log_entry.end_time = datetime.now()
            log_entry.status = 'completed'
            log_entry.properties_found = len(self.results)
            db.session.commit()

            return self.results

        except Exception as e:
            logger.error(f"Error in scraping: {str(e)}")
            if 'log_entry' in locals():
                log_entry.status = 'failed'
                log_entry.error_message = str(e)
                log_entry.end_time = datetime.now()
                db.session.commit()
            raise

    def save_results(self, filename: str = 'scraping_results.json'):
        """Save results to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

    async def scrape_yad2(self, search_params: Dict = None):
        """
        Scrape Yad2 using specific scraper
        """
        try:
            results = await self.yad2_scraper.scrape(search_params)
            self.results.extend(results)
            return results
        except Exception as e:
            logger.error(f"Error scraping Yad2: {str(e)}")
            raise
