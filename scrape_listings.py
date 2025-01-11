import asyncio
import argparse
import json
from scrapers.multi_url_scraper import MultiUrlScraper

def load_urls_from_file(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

async def main():
    parser = argparse.ArgumentParser(description='Scrape real estate listings from multiple URLs')
    parser.add_argument('--urls', type=str, help='Path to file containing URLs (one per line)')
    parser.add_argument('--keywords', type=str, nargs='+', help='Keywords to filter listings')
    parser.add_argument('--output', type=str, default='scraping_results.json', help='Output JSON file path')
    
    args = parser.parse_args()
    
    if not args.urls:
        print("Please provide a file containing URLs using --urls parameter")
        return
    
    urls = load_urls_from_file(args.urls)
    if not urls:
        print("No URLs found in the specified file")
        return
    
    print(f"Found {len(urls)} URLs to scrape")
    print(f"Filtering with keywords: {args.keywords if args.keywords else 'No keywords specified'}")
    
    scraper = MultiUrlScraper(keywords=args.keywords)
    results = await scraper.scrape_urls(urls)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nScraped {len(results)} listings")
    print(f"Results saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
