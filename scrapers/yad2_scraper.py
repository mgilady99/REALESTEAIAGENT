from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import logging
import json
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime

class Yad2Scraper:
    """Scraper for Yad2 real estate listings"""
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.yad2.co.il"
        self.setup_logging()
    
    def setup_logging(self):
        self.logger = logging.getLogger('Yad2Scraper')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.FileHandler('yad2_scraper.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def build_search_url(self, params):
        """Build search URL based on parameters"""
        # Base real estate search URL
        url = f"{self.base_url}/realestate/forsale"
        
        # Add filters
        filters = []
        
        # City/Location
        if params.get('city'):
            filters.append(f"city={params['city']}")
        
        # Property type mapping
        if params.get('property_type'):
            type_map = {
                'apartment': '1',
                'house': '2',
                'duplex': '3',
                'land': '4',
                'garden_apartment': '5',
                'townhouse': '6',
                'agricultural': '7',
                'office': '8',
                'warehouse': '9',
                'business': '10',
                'parking': '11',
                'general': '12'
            }
            prop_type = type_map.get(params['property_type'].lower())
            if prop_type:
                filters.append(f"propertyGroup={prop_type}")
        
        # Price range
        if params.get('min_price'):
            filters.append(f"price={params['min_price']}-{params.get('max_price', '')}")
        
        # Room range
        if params.get('min_rooms'):
            filters.append(f"rooms={params['min_rooms']}-{params.get('max_rooms', '')}")
        
        # Size range
        if params.get('min_size'):
            filters.append(f"square={params['min_size']}-{params.get('max_size', '')}")
        
        if filters:
            url += "?" + "&".join(filters)
        
        return url
    
    def handle_popups(self):
        """Handle common Yad2 popups"""
        try:
            # Wait for and close cookie consent
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "cookie-consent-button"))
            ).click()
        except TimeoutException:
            pass
        
        try:
            # Close subscription popup if present
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "modal-close"))
            ).click()
        except TimeoutException:
            pass
    
    def extract_hebrew_number(self, text):
        """Convert Hebrew number words to digits"""
        hebrew_numbers = {
            'אפס': 0, 'אחת': 1, 'שתיים': 2, 'שלוש': 3, 'ארבע': 4,
            'חמש': 5, 'שש': 6, 'שבע': 7, 'שמונה': 8, 'תשע': 9,
            'עשר': 10
        }
        
        for hebrew, digit in hebrew_numbers.items():
            text = text.replace(hebrew, str(digit))
        
        return text
    
    def extract_price(self, price_text):
        """Extract numeric price from Hebrew text"""
        if not price_text:
            return None
        
        try:
            # Remove non-digit characters except commas
            price = ''.join(c for c in price_text if c.isdigit() or c == ',')
            price = price.replace(',', '')
            return float(price) if price else None
        except Exception as e:
            self.logger.error(f"Error extracting price from {price_text}: {str(e)}")
            return None
    
    def extract_size(self, size_text):
        """Extract numeric size from Hebrew text"""
        if not size_text:
            return None
            
        try:
            # Convert Hebrew numbers if present
            size_text = self.extract_hebrew_number(size_text)
            # Extract number before 'מ"ר'
            match = re.search(r'([\d,]+)\s*(?:מ"ר|מטר)', size_text)
            if match:
                size = match.group(1).replace(',', '')
                return float(size)
            return None
        except Exception as e:
            self.logger.error(f"Error extracting size from {size_text}: {str(e)}")
            return None
    
    def extract_rooms(self, rooms_text):
        """Extract number of rooms from Hebrew text"""
        if not rooms_text:
            return None
            
        try:
            # Convert Hebrew numbers if present
            rooms_text = self.extract_hebrew_number(rooms_text)
            # Extract number before 'חדרים'
            match = re.search(r'([\d.]+)\s*(?:חדרים|חד\')', rooms_text)
            if match:
                return float(match.group(1))
            return None
        except Exception as e:
            self.logger.error(f"Error extracting rooms from {rooms_text}: {str(e)}")
            return None
    
    def extract_listing_data(self, listing_element):
        """Extract data from a listing element"""
        try:
            data = {}
            
            # Basic information
            data['title'] = listing_element.select_one('.title')?.text.strip()
            data['address'] = listing_element.select_one('.subtitle')?.text.strip()
            
            # Price
            price_elem = listing_element.select_one('.price')
            if price_elem:
                price_text = price_elem.text.strip()
                data['price'] = self.extract_price(price_text)
            
            # Rooms
            rooms_elem = listing_element.select_one('.rooms')
            if rooms_elem:
                rooms_text = rooms_elem.text.strip()
                data['rooms'] = self.extract_rooms(rooms_text)
            
            # Size
            size_elem = listing_element.select_one('.square_meters')
            if size_elem:
                size_text = size_elem.text.strip()
                data['size'] = self.extract_size(size_text)
            
            # Floor
            floor_elem = listing_element.select_one('.floor')
            if floor_elem:
                data['floor'] = floor_elem.text.strip()
            
            # Additional details
            details = listing_element.select('.listing-details li')
            data['details'] = [detail.text.strip() for detail in details]
            
            # Link
            link_elem = listing_element.select_one('a.feed_item')
            if link_elem and 'href' in link_elem.attrs:
                data['url'] = self.base_url + link_elem['href'] if not link_elem['href'].startswith('http') else link_elem['href']
            
            # Updated date
            date_elem = listing_element.select_one('.date')
            if date_elem:
                data['updated_date'] = date_elem.text.strip()
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error extracting listing data: {str(e)}")
            return None
    
    def scrape_listing_details(self, url):
        """Scrape detailed information from a single listing"""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "main_details"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            details = {
                'description': soup.select_one('.description')?.text.strip(),
                'features': [
                    feature.text.strip() 
                    for feature in soup.select('.properties li')
                ],
                'contact_info': {
                    'name': soup.select_one('.contact_name')?.text.strip(),
                    'phone': soup.select_one('.contact_phone')?.text.strip()
                }
            }
            
            # Property details table
            property_details = {}
            detail_rows = soup.select('.details_table tr')
            for row in detail_rows:
                key = row.select_one('th')?.text.strip()
                value = row.select_one('td')?.text.strip()
                if key and value:
                    property_details[key] = value
            
            details['property_details'] = property_details
            
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
                EC.presence_of_element_located((By.CLASS_NAME, "feeditem"))
            )
            
            # Handle any popups
            self.handle_popups()
            
            # Click "More Results" button until no more results
            while True:
                try:
                    more_button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "load_more"))
                    )
                    more_button.click()
                    time.sleep(2)  # Wait for new listings to load
                except TimeoutException:
                    break
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            listing_items = soup.select('.feeditem')
            
            for item in listing_items:
                try:
                    # Skip promoted listings if specified
                    if search_params.get('skip_promoted') and 'promoted' in item.get('class', []):
                        continue
                    
                    # Extract basic listing data
                    listing_data = self.extract_listing_data(item)
                    
                    if listing_data and listing_data.get('url'):
                        # Get detailed information
                        detailed_data = self.scrape_listing_details(listing_data['url'])
                        
                        if detailed_data:
                            listing_data.update(detailed_data)
                            listing_data['source_website'] = 'Yad2'
                            listings.append(listing_data)
                        
                except Exception as e:
                    self.logger.error(f"Error processing listing item: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(listings)} listings from Yad2")
            return listings
            
        except Exception as e:
            self.logger.error(f"Error scraping Yad2 listings: {str(e)}")
            return listings
