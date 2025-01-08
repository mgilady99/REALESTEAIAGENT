from scrapers.yad2_scraper import Yad2Scraper
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime

def test_yad2():
    try:
        # Setup Chrome driver
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        scraper = Yad2Scraper(driver)
        
        print("Starting Yad2 scraper test...")
        
        # Test scraping with 1 page
        properties = scraper.scrape_listings(max_pages=1)
        print(f"\nFound {len(properties)} properties")
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'yad2_test_results_{timestamp}.json'
        
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
    test_yad2()
