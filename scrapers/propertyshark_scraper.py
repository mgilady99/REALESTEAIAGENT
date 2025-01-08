from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
import json
import time
import re
from bs4 import BeautifulSoup

class PropertySharkScraper:
    """Scraper for PropertyShark commercial real estate listings"""
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.propertyshark.com"
        self.setup_logging()
    
    def setup_logging(self):
        self.logger = logging.getLogger('PropertySharkScraper')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.FileHandler('propertyshark_scraper.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def build_search_url(self, params):
        """Build search URL based on parameters"""
        # Base commercial search URL
        url = f"{self.base_url}/commercial-property/us"
        
        # Add location if provided
        if params.get('location'):
            location = params['location'].replace(' ', '-').lower()
            url += f"/{location}"
        
        # Add filters
        filters = []
        
        if params.get('property_type'):
            type_map = {
                'office': 'office',
                'retail': 'retail',
                'industrial': 'industrial',
                'multifamily': 'multifamily',
                'land': 'land'
            }
            prop_type = type_map.get(params['property_type'].lower())
            if prop_type:
                filters.append(f"propertyType={prop_type}")
        
        if params.get('min_price'):
            filters.append(f"priceMin={params['min_price']}")
        
        if params.get('max_price'):
            filters.append(f"priceMax={params['max_price']}")
        
        if params.get('min_size'):
            filters.append(f"sizeMin={params['min_size']}")
        
        if params.get('max_size'):
            filters.append(f"sizeMax={params['max_size']}")
        
        if filters:
            url += "?" + "&".join(filters)
        
        return url
    
    def extract_listing_data(self, listing_element):
        """Extract data from a listing element"""
        try:
            data = {}
            
            # Basic information
            data['title'] = listing_element.select_one('.listing-title')?.text.strip()
            data['address'] = listing_element.select_one('.listing-address')?.text.strip()
            
            # Price
            price_elem = listing_element.select_one('.listing-price')
            if price_elem:
                price_text = price_elem.text.strip()
                data['price'] = self.extract_price(price_text)
            
            # Size
            size_elem = listing_element.select_one('.listing-size')
            if size_elem:
                size_text = size_elem.text.strip()
                data['size'] = self.extract_size(size_text)
            
            # Property type
            data['property_type'] = listing_element.select_one('.listing-type')?.text.strip()
            
            # Additional details
            details = listing_element.select('.listing-details li')
            data['details'] = [detail.text.strip() for detail in details]
            
            # Link
            link_elem = listing_element.select_one('a.listing-link')
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
            
            # Property history
            history = []
            history_rows = soup.select('.property-history-table tr')
            for row in history_rows[1:]:  # Skip header row
                cols = row.select('td')
                if len(cols) >= 3:
                    history.append({
                        'date': cols[0].text.strip(),
                        'type': cols[1].text.strip(),
                        'price': self.extract_price(cols[2].text.strip())
                    })
            
            details['property_history'] = history
            
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
                EC.presence_of_element_located((By.CLASS_NAME, "listing-item"))
            )
            
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
            listing_items = soup.select('.listing-item')
            
            for item in listing_items:
                try:
                    # Extract basic listing data
                    listing_data = self.extract_listing_data(item)
                    
                    if listing_data and listing_data.get('url'):
                        # Get detailed information
                        detailed_data = self.scrape_listing_details(listing_data['url'])
                        
                        if detailed_data:
                            listing_data.update(detailed_data)
                            listing_data['source_website'] = 'PropertyShark'
                            listings.append(listing_data)
                        
                except Exception as e:
                    self.logger.error(f"Error processing listing item: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(listings)} listings from PropertyShark")
            return listings
            
        except Exception as e:
            self.logger.error(f"Error scraping PropertyShark listings: {str(e)}")
            return listings
