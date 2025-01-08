import argparse
import yaml
import json
from pathlib import Path
from datetime import datetime
from scrapers.selector_tester import SelectorTester
from website_manager import WebsiteManager

def main():
    parser = argparse.ArgumentParser(description='Test website selectors')
    parser.add_argument('--website', help='Name of website to test (from config)')
    parser.add_argument('--config', help='Path to website config file', default='websites_config.yaml')
    parser.add_argument('--output', help='Directory for test reports', default='selector_tests')
    parser.add_argument('--headless', help='Run in headless mode', action='store_true', default=True)
    args = parser.parse_args()

    # Load website configurations
    website_manager = WebsiteManager(args.config)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    with SelectorTester(headless=args.headless) as tester:
        if args.website:
            # Test specific website
            config = website_manager.get_website_config(args.website)
            if not config:
                print(f"Website '{args.website}' not found in configuration")
                return
            
            websites_to_test = {args.website: config}
        else:
            # Test all enabled websites
            websites_to_test = website_manager.get_enabled_websites()
        
        # Run tests for each website
        for website_name, config in websites_to_test.items():
            print(f"\nTesting selectors for {website_name}...")
            
            # Test selectors
            results = tester.test_website_config(config)
            
            # Generate validation report
            validation = tester.validate_selectors(config)
            
            # Generate HTML report
            report = tester.generate_test_report(website_name, config, results)
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save HTML report
            report_path = output_dir / f"{website_name}_{timestamp}_report.html"
            report_path.write_text(report, encoding='utf-8')
            
            # Save validation results
            validation_path = output_dir / f"{website_name}_{timestamp}_validation.json"
            validation_path.write_text(json.dumps(validation, indent=2), encoding='utf-8')
            
            # Print summary
            print(f"Results for {website_name}:")
            print(f"Overall Success: {'✓' if results['overall_success'] else '✗'}")
            print(f"Report saved to: {report_path}")
            print(f"Validation saved to: {validation_path}")
            
            if not validation['valid']:
                print("\nValidation Errors:")
                for error in validation['errors']:
                    print(f"- {error['selector']}: {error['error']}")
            
            if validation['suggestions']:
                print("\nSuggestions:")
                for selector, suggestions in validation['suggestions'].items():
                    print(f"- {selector}:")
                    for suggestion in suggestions:
                        print(f"  * {suggestion}")

if __name__ == '__main__':
    main()
