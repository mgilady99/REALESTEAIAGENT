from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import logging
import time
from datetime import datetime

class SelectorTester:
    def __init__(self, headless=True):
        self.logger = logging.getLogger('SelectorTester')
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def test_selector(self, url, selector, wait_time=10):
        """Test a single CSS selector on a webpage"""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            return {
                'success': True,
                'count': len(elements),
                'first_element_html': elements[0].get_attribute('outerHTML') if elements else None,
                'text_content': [el.text for el in elements[:3]]  # First 3 elements
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'count': 0,
                'first_element_html': None,
                'text_content': []
            }

    def test_website_config(self, config):
        """Test all selectors for a website configuration"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': config['base_url'],
            'selectors_results': {},
            'overall_success': True
        }
        
        # Test main listing page
        search_url = f"{config['base_url']}{config['search_path']}"
        results['selectors_results']['listings_page'] = self.test_selector(
            search_url, 
            config['selectors']['listings']
        )
        
        # If listings found, test first listing for detailed selectors
        if results['selectors_results']['listings_page']['success']:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            listing_elements = soup.select(config['selectors']['listings'])
            
            if listing_elements:
                # Get first listing URL
                link_selector = config['selectors']['link']
                link_element = listing_elements[0].select_one(link_selector)
                if link_element and link_element.get('href'):
                    listing_url = link_element['href']
                    if not listing_url.startswith('http'):
                        listing_url = f"{config['base_url']}{listing_url}"
                    
                    # Test all selectors on detail page
                    for selector_name, selector in config['selectors'].items():
                        if selector_name not in ['listings', 'link']:
                            results['selectors_results'][selector_name] = self.test_selector(
                                listing_url, 
                                selector
                            )
        
        # Check if any selectors failed
        results['overall_success'] = all(
            result['success'] 
            for result in results['selectors_results'].values()
        )
        
        return results

    def validate_selectors(self, website_config):
        """Validate and suggest fixes for selectors"""
        validation_results = {
            'valid': True,
            'suggestions': {},
            'errors': []
        }
        
        try:
            results = self.test_website_config(website_config)
            
            for selector_name, result in results['selectors_results'].items():
                if not result['success']:
                    validation_results['valid'] = False
                    validation_results['errors'].append({
                        'selector': selector_name,
                        'error': result['error']
                    })
                    
                    # Suggest alternative selectors
                    if 'no such element' in result['error'].lower():
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        original_selector = website_config['selectors'][selector_name]
                        
                        # Try common variations
                        variations = [
                            f"#{original_selector}",  # Try as ID
                            f".{original_selector}",  # Try as class
                            f"[data-test='{original_selector}']",  # Try as data attribute
                            f"*[class*='{original_selector}']"  # Try partial class match
                        ]
                        
                        working_variations = []
                        for variant in variations:
                            if soup.select(variant):
                                working_variations.append(variant)
                        
                        if working_variations:
                            validation_results['suggestions'][selector_name] = working_variations
                
                # Suggest optimization if too many elements found
                elif result['count'] > 100:
                    validation_results['suggestions'][selector_name] = [
                        f"Current selector matches {result['count']} elements. Consider making it more specific."
                    ]
        
        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append({
                'selector': 'general',
                'error': str(e)
            })
        
        return validation_results

    def generate_test_report(self, website_name, config, results):
        """Generate a detailed HTML report of selector testing results"""
        report = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .warning {{ color: orange; }}
                pre {{ background: #f5f5f5; padding: 10px; }}
            </style>
        </head>
        <body>
            <h1>Selector Test Report - {website_name}</h1>
            <h2>Website Configuration</h2>
            <pre>{json.dumps(config, indent=2)}</pre>
            
            <h2>Test Results</h2>
            <div class="{'success' if results['overall_success'] else 'error'}">
                Overall Status: {'✓ Passed' if results['overall_success'] else '✗ Failed'}
            </div>
            
            <h3>Selector Results:</h3>
        """
        
        for selector_name, result in results['selectors_results'].items():
            report += f"""
            <div class="selector-result">
                <h4>{selector_name}</h4>
                <ul>
                    <li>Status: <span class="{'success' if result['success'] else 'error'}">
                        {'✓ Success' if result['success'] else '✗ Failed'}
                    </span></li>
                    <li>Elements Found: {result['count']}</li>
                """
            
            if result['text_content']:
                report += "<li>Sample Text Content:<ul>"
                for text in result['text_content']:
                    report += f"<li>{text}</li>"
                report += "</ul></li>"
            
            if result['first_element_html']:
                report += f"""
                    <li>Sample HTML:
                        <pre>{result['first_element_html']}</pre>
                    </li>
                """
            
            if not result['success']:
                report += f"""
                    <li class="error">Error: {result['error']}</li>
                """
            
            report += "</ul></div>"
        
        report += """
            </body>
        </html>
        """
        
        return report

    def close(self):
        """Close the WebDriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
