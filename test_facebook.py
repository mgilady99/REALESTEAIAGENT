from scrapers.facebook_scraper import FacebookScraper
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime

def test_facebook():
    try:
        # Setup Chrome driver
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        scraper = FacebookScraper(driver)
        
        print("Starting Facebook scraper test...")
        
        # Test single group
        group_url = "https://www.facebook.com/groups/commercial.realestate.israel"
        print(f"\nTesting group: {group_url}")
        
        properties = scraper.scrape_group(group_url, max_posts=5)
        print(f"\nFound {len(properties)} properties")
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'facebook_test_results_{timestamp}.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(properties, f, ensure_ascii=False, indent=2)
        
        # Print summary
        print("\nResults Summary:")
        for i, prop in enumerate(properties, 1):
            print(f"\nProperty {i}:")
            print(f"Type: {prop.get('property_type', 'N/A')}")
            print(f"Price: {prop.get('price', 'N/A')}")
            print(f"Location: {prop.get('location', 'N/A')}")
            print(f"Size: {prop.get('size', 'N/A')}")
            print(f"Features: {prop.get('features', 'N/A')}")
        
        print(f"\nDetailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_facebook()
