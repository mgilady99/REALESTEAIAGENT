from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import logging

class LoopNetScraper:
    """Scraper for LoopNet commercial real estate listings"""
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.loopnet.com"
        self.setup_logging()
    
    def setup_logging(self):
        self.logger = logging.getLogger('LoopNetScraper')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.FileHandler('loopnet_scraper.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def build_search_url(self, params):
        """Build search URL based on parameters"""
        base_search_url = f"{self.base_url}/search/commercial-real-estate"
        
        # Add location
        if params.get('location'):
            location = params['location'].replace(' ', '-').lower()
            base_search_url += f"/{location}"
        
        # Add property type
        if params.get('property_type'):
            prop_type = params['property_type'].replace(' ', '-').lower()
            base_search_url += f"/for-sale/{prop_type}"
        
        # Add query parameters
        query_params = []
        if params.get('min_price'):
            query_params.append(f"price-min={params['min_price']}")
        if params.get('max_price'):
            query_params.append(f"price-max={params['max_price']}")
        if params.get('min_size'):
            query_params.append(f"size-min={params['min_size']}")
        if params.get('max_size'):
            query_params.append(f"size-max={params['max_size']}")
        
        if query_params:
            base_search_url += "?" + "&".join(query_params)
        
        return base_search_url
    
    def extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
            
        try:
            # Remove currency symbols and convert to float
            price = ''.join(filter(str.isdigit, price_text))
            return float(price) if price else None
        except Exception as e:
            self.logger.error(f"Error extracting price from {price_text}: {str(e)}")
            return None
    
    def extract_size(self, size_text):
        """Extract numeric size from text"""
        if not size_text:
            return None
            
        try:
            # Extract number before 'SF' or 'AC'
            match = re.search(r'([\d,]+)\s*(?:SF|AC)', size_text)
            if match:
                size = match.group(1).replace(',', '')
                return float(size)
            return None
        except Exception as e:
            self.logger.error(f"Error extracting size from {size_text}: {str(e)}")
            return None
    
    def scrape_listing_details(self, url):
        """Scrape detailed information from a single listing"""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "profile-hero"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract detailed information
            details = {
                'title': soup.select_one('.profile-hero h1')?.text.strip(),
                'price': self.extract_price(
                    soup.select_one('.profile-hero .price-text')?.text.strip()
                ),
                'size': self.extract_size(
                    soup.select_one('.profile-hero .size-text')?.text.strip()
                ),
                'property_type': soup.select_one('.property-type')?.text.strip(),
                'description': soup.select_one('.property-description')?.text.strip(),
                'amenities': [
                    item.text.strip() 
                    for item in soup.select('.amenities-section .amenity-item')
                ],
                'contact_info': {
                    'name': soup.select_one('.contact-info .contact-name')?.text.strip(),
                    'phone': soup.select_one('.contact-info .contact-phone')?.text.strip(),
                    'email': soup.select_one('.contact-info .contact-email')?.text.strip()
                }
            }
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error scraping listing details from {url}: {str(e)}")
            return None
    
    def scrape_listings(self, search_params):
        """Scrape listings based on search parameters"""
        listings = []
        try:
            url = self.build_search_url(search_params)
            self.driver.get(url)
            
            # Wait for listings to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "placard"))
            )
            
            # Scroll to load all listings
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                WebDriverWait(self.driver, 5).until(lambda d: 
                    d.execute_script("return document.readyState") == "complete"
                )
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            listing_cards = soup.select('.placard')
            
            for card in listing_cards:
                try:
                    listing_url = self.base_url + card.select_one('a')['href']
                    listing_details = self.scrape_listing_details(listing_url)
                    
                    if listing_details:
                        listing_details['url'] = listing_url
                        listing_details['source_website'] = 'LoopNet'
                        listings.append(listing_details)
                        
                except Exception as e:
                    self.logger.error(f"Error processing listing card: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(listings)} listings from LoopNet")
            return listings
            
        except Exception as e:
            self.logger.error(f"Error scraping LoopNet listings: {str(e)}")
            return listings
