import yaml
import logging
from datetime import datetime
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from scrapers.facebook_scraper import FacebookScraper
from scrapers.yad2_scraper import Yad2Scraper
from processors.data_processor import CommercialPropertyProcessor

class RealEstateOrchestrator:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_processor()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            filename='orchestrator.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open('websites_config.yaml', 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            raise

    def setup_processor(self):
        """Setup data processor"""
        self.processor = CommercialPropertyProcessor()

    def setup_webdriver(self):
        """Setup Selenium WebDriver"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')  # Run in headless mode
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={self.config["settings"]["user_agent"]}')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            return driver
        except Exception as e:
            self.logger.error(f"Error setting up WebDriver: {str(e)}")
            raise

    def scrape_facebook_groups(self):
        """Scrape Facebook groups"""
        try:
            driver = self.setup_webdriver()
            scraper = FacebookScraper(driver)
            
            all_properties = []
            groups_config = self.config['facebook_groups']
            
            # Scrape default groups
            for group in groups_config['groups']:
                try:
                    properties = scraper.scrape_group(
                        group['url'],
                        self.config['facebook_settings']['max_posts_per_group']
                    )
                    all_properties.extend(properties)
                    self.logger.info(f"Scraped {len(properties)} properties from {group['name']}")
                except Exception as e:
                    self.logger.error(f"Error scraping group {group['name']}: {str(e)}")
            
            # Scrape custom groups
            for group in groups_config.get('custom_groups', []):
                try:
                    properties = scraper.scrape_group(
                        group['url'],
                        self.config['facebook_settings']['max_posts_per_group']
                    )
                    all_properties.extend(properties)
                    self.logger.info(f"Scraped {len(properties)} properties from {group['name']}")
                except Exception as e:
                    self.logger.error(f"Error scraping custom group {group['name']}: {str(e)}")
            
            driver.quit()
            return all_properties
            
        except Exception as e:
            self.logger.error(f"Error in Facebook scraping: {str(e)}")
            return []

    def scrape_yad2(self):
        """Scrape Yad2"""
        try:
            driver = self.setup_webdriver()
            scraper = Yad2Scraper(driver)
            
            properties = scraper.scrape_listings()
            self.logger.info(f"Scraped {len(properties)} properties from Yad2")
            
            driver.quit()
            return properties
            
        except Exception as e:
            self.logger.error(f"Error in Yad2 scraping: {str(e)}")
            return []

    def run(self):
        """Run the orchestrator"""
        try:
            self.logger.info("Starting scraping process")
            
            # Scrape Facebook groups
            fb_properties = self.scrape_facebook_groups()
            if fb_properties:
                df = self.processor.process_properties(fb_properties)
                self.processor.save_data(df, 'facebook')
            
            # Scrape Yad2
            yad2_properties = self.scrape_yad2()
            if yad2_properties:
                df = self.processor.process_properties(yad2_properties)
                self.processor.save_data(df, 'yad2')
            
            # Generate market analysis
            self.processor.analyze_market_trends()
            
            self.logger.info("Scraping process completed")
            
        except Exception as e:
            self.logger.error(f"Error in orchestrator: {str(e)}")

def main():
    orchestrator = RealEstateOrchestrator()
    orchestrator.run()

if __name__ == "__main__":
    main()
