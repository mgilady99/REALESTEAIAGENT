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
import os
from dotenv import load_dotenv

class FacebookScraper:
    """Scraper for Facebook real estate groups"""
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.facebook.com"
        self.setup_logging()
        load_dotenv()
        
        # Load Facebook credentials from environment variables
        self.fb_email = os.getenv('FACEBOOK_EMAIL')
        self.fb_password = os.getenv('FACEBOOK_PASSWORD')
        
        # Default Israeli real estate groups
        self.default_groups = {
            'נדלן למכירה': 'nadlan.sale',
            'דירות למכירה': 'apartments.sale',
            'נדלן להשקעה': 'nadlan.investment',
            'קבוצת נדלן ישראל': 'israel.realestate',
            'נדלן בישראל': 'israel.properties'
        }
    
    def setup_logging(self):
        self.logger = logging.getLogger('FacebookScraper')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.FileHandler('facebook_scraper.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def login(self):
        """Login to Facebook"""
        try:
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for email field and enter credentials
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.send_keys(self.fb_email)
            
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.send_keys(self.fb_password)
            
            # Click login button
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            return True
        except Exception as e:
            self.logger.error(f"Error logging in to Facebook: {str(e)}")
            return False
    
    def is_commercial_property(self, text):
        """Check if the post is about commercial property"""
        commercial_keywords = [
            'מסחרי', 'משרדים', 'חנות', 'מחסן', 'תעשייה',
            'עסק', 'בניין', 'מבנה', 'השכרה מסחרית', 'מכירה מסחרית'
        ]
        
        exclude_keywords = [
            'דירה', 'דירות', 'בית', 'וילה', 'פנטהאוז',
            'דיור', 'מגורים', 'חדרים'
        ]
        
        # Check if any commercial keyword is present
        has_commercial = any(keyword in text for keyword in commercial_keywords)
        
        # Check if any residential keyword is present
        has_residential = any(keyword in text for keyword in exclude_keywords)
        
        # Return True only if it has commercial keywords and no residential keywords
        return has_commercial and not has_residential

    def extract_property_type(self, text):
        """Extract commercial property type from text"""
        property_types = {
            'office': {
                'keywords': ['משרד', 'משרדים'],
                'english': 'office'
            },
            'retail': {
                'keywords': ['חנות', 'חנויות', 'מסחרי'],
                'english': 'retail'
            },
            'industrial': {
                'keywords': ['תעשייה', 'תעשייתי', 'מפעל'],
                'english': 'industrial'
            },
            'warehouse': {
                'keywords': ['מחסן', 'מחסנים'],
                'english': 'warehouse'
            },
            'business': {
                'keywords': ['עסק', 'עסקים'],
                'english': 'business'
            },
            'building': {
                'keywords': ['בניין', 'מבנה'],
                'english': 'building'
            }
        }
        
        for type_key, type_info in property_types.items():
            if any(keyword in text for keyword in type_info['keywords']):
                return {
                    'type': type_key,
                    'hebrew': type_info['keywords'][0],
                    'english': type_info['english']
                }
        
        return None

    def extract_commercial_features(self, text):
        """Extract commercial property features"""
        features = {
            'parking': False,
            'elevator': False,
            'air_conditioning': False,
            'accessibility': False,
            'security': False,
            'loading_area': False,
            'public_transport': False,
            'renovated': False
        }
        
        feature_keywords = {
            'parking': ['חניה', 'חנייה', 'חניון', 'מקום חניה'],
            'elevator': ['מעלית', 'מעליות'],
            'air_conditioning': ['מיזוג', 'מזגן', 'מזגנים'],
            'accessibility': ['נגישות', 'נגיש לנכים'],
            'security': ['אבטחה', 'שמירה', 'מאובטח'],
            'loading_area': ['אזור פריקה', 'רמפה', 'פריקה וטעינה'],
            'public_transport': ['תחבורה ציבורית', 'תחנת אוטובוס', 'רכבת'],
            'renovated': ['משופץ', 'שיפוץ', 'חדש', 'מחודש']
        }
        
        for feature, keywords in feature_keywords.items():
            features[feature] = any(keyword in text for keyword in keywords)
        
        return features

    def extract_price(self, text):
        """Extract price from text in various formats"""
        if not text:
            return None
            
        try:
            # Look for price patterns in both Hebrew and English
            patterns = [
                r'(?:₪|NIS|שח)\s*([\d,]+)',  # Price after currency symbol
                r'([\d,]+)\s*(?:₪|NIS|שח)',  # Price before currency symbol
                r'([\d,]+)\s*אלף',  # Price in thousands
                r'([\d,.]+)\s*(?:מיליון|million)'  # Price in millions
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    price = match.group(1).replace(',', '')
                    price = float(price)
                    
                    # Convert thousands and millions to actual number
                    if 'אלף' in text or 'thousand' in text.lower():
                        price *= 1000
                    elif 'מיליון' in text or 'million' in text.lower():
                        price *= 1000000
                    
                    return price
                    
            return None
        except Exception as e:
            self.logger.error(f"Error extracting price from text: {str(e)}")
            return None
    
    def extract_size(self, text):
        """Extract size from text"""
        if not text:
            return None
            
        try:
            # Look for size patterns
            patterns = [
                r'([\d.]+)\s*(?:מ"ר|מטר|meters|sqm)',
                r'([\d.]+)\s*(?:מ\'|מ)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return float(match.group(1))
                    
            return None
        except Exception as e:
            self.logger.error(f"Error extracting size from text: {str(e)}")
            return None
    
    def extract_rooms(self, text):
        """Extract number of rooms from text"""
        if not text:
            return None
            
        try:
            # Look for room patterns
            patterns = [
                r'([\d.]+)\s*(?:חדרים|חד\')',
                r'([\d.]+)\s*(?:rooms|room)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return float(match.group(1))
                    
            return None
        except Exception as e:
            self.logger.error(f"Error extracting rooms from text: {str(e)}")
            return None
    
    def extract_location(self, text):
        """Extract location from text with support for Israeli cities and neighborhoods"""
        # Major Israeli cities and their common variations
        cities = {
            'תל אביב': ['תל-אביב', 'תא', 'תל אביב יפו', 'תל-אביב-יפו'],
            'ירושלים': ['ירושלים', 'י-ם'],
            'חיפה': ['חיפה'],
            'ראשון לציון': ['ראשלצ', 'ראשון', 'ראשל"צ'],
            'פתח תקווה': ['פתח-תקווה', 'פת', 'פ"ת'],
            'אשדוד': ['אשדוד'],
            'נתניה': ['נתניה'],
            'באר שבע': ['באר-שבע', 'ב"ש'],
            'חולון': ['חולון'],
            'רמת גן': ['רמת-גן', 'ר"ג'],
            'בת ים': ['בת-ים'],
            'רחובות': ['רחובות'],
            'אשקלון': ['אשקלון'],
            'הרצליה': ['הרצליה'],
            'כפר סבא': ['כפר-סבא', 'כ"ס']
        }
        
        # Tel Aviv neighborhoods
        tlv_neighborhoods = [
            'פלורנטין', 'שפירא', 'נווה צדק', 'כרם התימנים', 'לב העיר',
            'רוטשילד', 'נחלת בנימין', 'מונטיפיורי', 'הצפון הישן', 'הצפון החדש',
            'רמת אביב', 'יפו', 'עג׳מי', 'צהלה', 'אפקה', 'בבלי'
        ]
        
        # Jerusalem neighborhoods
        jerusalem_neighborhoods = [
            'רחביה', 'טלביה', 'בית הכרם', 'קטמון', 'בקעה', 'תלפיות',
            'גילה', 'רמות', 'פסגת זאב', 'נווה יעקב', 'מאה שערים', 'גאולה'
        ]
        
        location_info = {
            'city': None,
            'neighborhood': None
        }
        
        # Check for cities
        for city, variations in cities.items():
            if any(var in text for var in [city] + variations):
                location_info['city'] = city
                break
        
        # If Tel Aviv, check for neighborhoods
        if location_info['city'] == 'תל אביב':
            for neighborhood in tlv_neighborhoods:
                if neighborhood in text:
                    location_info['neighborhood'] = neighborhood
                    break
        
        # If Jerusalem, check for neighborhoods
        elif location_info['city'] == 'ירושלים':
            for neighborhood in jerusalem_neighborhoods:
                if neighborhood in text:
                    location_info['neighborhood'] = neighborhood
                    break
        
        return location_info

    def extract_property_features(self, text):
        """Extract property features from Hebrew text"""
        features = {
            'parking': False,
            'elevator': False,
            'balcony': False,
            'storage': False,
            'air_conditioning': False,
            'renovated': False,
            'furnished': False,
            'immediate_entry': False
        }
        
        # Feature keywords in Hebrew
        feature_keywords = {
            'parking': ['חניה', 'חנייה', 'מקום חניה', 'חניון'],
            'elevator': ['מעלית', 'ליפט'],
            'balcony': ['מרפסת', 'מרפסת שמש', 'מרפסת סוכה'],
            'storage': ['מחסן', 'מקום אחסון'],
            'air_conditioning': ['מיזוג', 'מזגן', 'מזגנים'],
            'renovated': ['משופצת', 'שיפוץ', 'משופץ', 'חדש'],
            'furnished': ['מרוהט', 'מרוהטת', 'ריהוט מלא'],
            'immediate_entry': ['כניסה מיידית', 'פינוי מיידי', 'כניסה מיידי']
        }
        
        for feature, keywords in feature_keywords.items():
            features[feature] = any(keyword in text for keyword in keywords)
        
        return features

    def extract_deal_type(self, text):
        """Extract type of real estate deal from Hebrew text"""
        # Deal type patterns
        patterns = {
            'sale': [
                'למכירה', 'מכירה', 'להימכר', 'נמכר',
                'מחיר למכירה', 'מחיר מכירה'
            ],
            'rent': [
                'להשכרה', 'השכרה', 'להשכיר', 'מושכר',
                'מחיר להשכרה', 'מחיר שכירות', 'לשכירות'
            ],
            'roommate': [
                'שותף', 'שותפה', 'שותפים', 'שותפות',
                'חדר להשכרה', 'חדר פנוי'
            ]
        }
        
        for deal_type, keywords in patterns.items():
            if any(keyword in text for keyword in keywords):
                return deal_type
        
        return None

    def extract_post_data(self, post_element):
        """Extract data from a Facebook post with focus on commercial properties"""
        try:
            data = {}
            
            # Get post text
            text_elem = post_element.select_one('.userContent')
            if text_elem:
                post_text = text_elem.text.strip()
                
                # Check if it's a commercial property
                if not self.is_commercial_property(post_text):
                    return None
                
                data['description'] = post_text
                
                # Extract basic information
                data['price'] = self.extract_price(post_text)
                data['size'] = self.extract_size(post_text)
                data['location'] = self.extract_location(post_text)
                
                # Extract commercial-specific information
                data['property_type'] = self.extract_property_type(post_text)
                data['features'] = self.extract_commercial_features(post_text)
                data['deal_type'] = self.extract_deal_type(post_text)
            
            # Get post date
            date_elem = post_element.select_one('abbr')
            if date_elem:
                data['posted_date'] = date_elem.get('title')
            
            # Get post URL
            link_elem = post_element.select_one('a._5pcq')
            if link_elem:
                data['url'] = self.base_url + link_elem['href']
            
            # Get images
            images = post_element.select('img.scaledImageFitWidth')
            data['images'] = [img['src'] for img in images if 'src' in img.attrs]
            
            # Get contact info
            contact_info = {
                'phone': None,
                'email': None,
                'whatsapp': None
            }
            
            # Extract phone numbers (including Israeli formats)
            phone_patterns = [
                r'(?:\+972|972|0)(?:-)?(?:5[0-9]|7[0-9]|2[0-9]|3[0-9]|4[0-9]|8[0-9]|9[0-9])-?\d{3}-?\d{4}',
                r'(?:\+972|972|0)(?:-)?[23489]-?\d{7}'
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, post_text)
                if phone_match:
                    contact_info['phone'] = phone_match.group()
                    break
            
            # Extract WhatsApp
            whatsapp_match = re.search(r'(?:וואטסאפ|ווצאפ|whatsapp)[:\s]*([0-9+\-\s]+)', post_text, re.IGNORECASE)
            if whatsapp_match:
                contact_info['whatsapp'] = whatsapp_match.group(1)
            
            # Extract email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', post_text)
            if email_match:
                contact_info['email'] = email_match.group()
            
            data['contact_info'] = contact_info
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error extracting post data: {str(e)}")
            return None
    
    def scrape_group(self, group_url, max_posts=50):
        """Scrape posts from a Facebook group"""
        posts = []
        try:
            self.driver.get(group_url)
            
            # Wait for posts to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[role='feed']"))
            )
            
            # Scroll to load more posts
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            post_count = 0
            
            while post_count < max_posts:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Get all posts
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                post_elements = soup.select("[role='article']")
                
                for post in post_elements[post_count:]:
                    post_data = self.extract_post_data(post)
                    if post_data:
                        post_data['source'] = 'Facebook'
                        post_data['group_url'] = group_url
                        posts.append(post_data)
                        post_count += 1
                        
                        if post_count >= max_posts:
                            break
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            self.logger.info(f"Successfully scraped {len(posts)} posts from Facebook group")
            return posts
            
        except Exception as e:
            self.logger.error(f"Error scraping Facebook group: {str(e)}")
            return posts
    
    def scrape_multiple_groups(self, group_urls=None, max_posts_per_group=50):
        """Scrape multiple Facebook groups"""
        all_posts = []
        
        # If no group URLs provided, use default Israeli real estate groups
        if not group_urls:
            group_urls = [f"{self.base_url}/groups/{group_id}" for group_id in self.default_groups.values()]
        
        # Login to Facebook
        if not self.login():
            self.logger.error("Failed to login to Facebook")
            return all_posts
        
        # Scrape each group
        for group_url in group_urls:
            try:
                group_posts = self.scrape_group(group_url, max_posts_per_group)
                all_posts.extend(group_posts)
                
                # Wait between groups to avoid rate limiting
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error scraping group {group_url}: {str(e)}")
                continue
        
        return all_posts
