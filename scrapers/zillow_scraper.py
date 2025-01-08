from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import json
import time
from bs4 import BeautifulSoup

class ZillowScraper:
    """Scraper for Zillow commercial real estate listings"""
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.zillow.com"
        self.setup_logging()
    
    def setup_logging(self):
        self.logger = logging.getLogger('ZillowScraper')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.FileHandler('zillow_scraper.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def build_search_url(self, params):
        """Build search URL based on parameters"""
        # Base commercial search URL
        url = f"{self.base_url}/commercial"
        
        # Add filters
        filters = []
        
        if params.get('location'):
            filters.append(f"location={params['location']}")
        
        if params.get('property_type'):
            type_map = {
                'office': 'office',
                'retail': 'retail',
                'industrial': 'industrial',
                'multifamily': 'multiFamily',
                'land': 'land'
            }
            prop_type = type_map.get(params['property_type'].lower())
            if prop_type:
                filters.append(f"propertyType={prop_type}")
        
        if params.get('min_price'):
            filters.append(f"price-min={params['min_price']}")
        
        if params.get('max_price'):
            filters.append(f"price-max={params['max_price']}")
        
        if params.get('min_size'):
            filters.append(f"sqft-min={params['min_size']}")
        
        if params.get('max_size'):
            filters.append(f"sqft-max={params['max_size']}")
        
        if filters:
            url += "?" + "&".join(filters)
        
        return url
    
    def handle_popups(self):
        """Handle common Zillow popups"""
        try:
            # Wait for and close email subscription popup
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".email-popup-close"))
            ).click()
        except TimeoutException:
            pass
    
    def extract_listing_data(self, listing_element):
        """Extract data from a listing element"""
        try:
            data = {}
            
            # Basic information
            data['title'] = listing_element.select_one('.property-card-title')?.text.strip()
            data['address'] = listing_element.select_one('.property-card-address')?.text.strip()
            
            # Price
            price_elem = listing_element.select_one('.property-card-price')
            if price_elem:
                price_text = price_elem.text.strip()
                # Convert price text to numeric value
                data['price'] = self.extract_price(price_text)
            
            # Size
            size_elem = listing_element.select_one('.property-card-size')
            if size_elem:
                size_text = size_elem.text.strip()
                data['size'] = self.extract_size(size_text)
            
            # Property type
            data['property_type'] = listing_element.select_one('.property-card-type')?.text.strip()
            
            # Additional details
            details = listing_element.select('.property-card-details li')
            data['details'] = [detail.text.strip() for detail in details]
            
            # Link
            link_elem = listing_element.select_one('a.property-card-link')
            if link_elem and 'href' in link_elem.attrs:
                data['url'] = self.base_url + link_elem['href'] if not link_elem['href'].startswith('http') else link_elem['href']
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error extracting listing data: {str(e)}")
            return None
    
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
                EC.presence_of_element_located((By.CLASS_NAME, "property-details"))
            )
            
            # Handle any popups
            self.handle_popups()
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            details = {
                'title': soup.select_one('.property-title')?.text.strip(),
                'price': self.extract_price(
                    soup.select_one('.property-price')?.text.strip()
                ),
                'size': self.extract_size(
                    soup.select_one('.property-size')?.text.strip()
                ),
                'property_type': soup.select_one('.property-type')?.text.strip(),
                'description': soup.select_one('.property-description')?.text.strip(),
                'features': [
                    feature.text.strip() 
                    for feature in soup.select('.property-features li')
                ],
                'contact_info': {
                    'name': soup.select_one('.contact-name')?.text.strip(),
                    'phone': soup.select_one('.contact-phone')?.text.strip(),
                    'email': soup.select_one('.contact-email')?.text.strip()
                }
            }
            
            # Additional property details
            property_details = {}
            detail_rows = soup.select('.property-details-table tr')
            for row in detail_rows:
                key = row.select_one('th')?.text.strip()
                value = row.select_one('td')?.text.strip()
                if key and value:
                    property_details[key] = value
            
            details['additional_details'] = property_details
            
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
                EC.presence_of_element_located((By.CLASS_NAME, "property-card"))
            )
            
            # Handle any popups
            self.handle_popups()
            
            # Scroll to load all listings
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for content to load
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            listing_cards = soup.select('.property-card')
            
            for card in listing_cards:
                try:
                    # Extract basic listing data
                    listing_data = self.extract_listing_data(card)
                    
                    if listing_data and listing_data.get('url'):
                        # Get detailed information
                        detailed_data = self.scrape_listing_details(listing_data['url'])
                        
                        if detailed_data:
                            listing_data.update(detailed_data)
                            listing_data['source_website'] = 'Zillow'
                            listings.append(listing_data)
                        
                except Exception as e:
                    self.logger.error(f"Error processing listing card: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(listings)} listings from Zillow")
            return listings
            
        except Exception as e:
            self.logger.error(f"Error scraping Zillow listings: {str(e)}")
            return listings
