import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import threading
from scrapers.facebook_scraper import FacebookScraper
from scrapers.yad2_scraper import Yad2Scraper
from main import RealEstateOrchestrator
import os
from dotenv import load_dotenv

class TestUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Real Estate Scraper Test Panel")
        self.root.geometry("800x600")
        self.setup_ui()
        self.load_env()
        
    def load_env(self):
        """Load environment variables"""
        load_dotenv()
        self.fb_email = os.getenv('FACEBOOK_EMAIL', '')
        self.fb_password = os.getenv('FACEBOOK_PASSWORD', '')

    def setup_ui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Credentials Frame
        cred_frame = ttk.LabelFrame(main_frame, text="Facebook Credentials", padding="5")
        cred_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(cred_frame, text="Email:").grid(row=0, column=0, padx=5)
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(cred_frame, textvariable=self.email_var, width=40)
        self.email_entry.grid(row=0, column=1, padx=5)

        ttk.Label(cred_frame, text="Password:").grid(row=1, column=0, padx=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(cred_frame, textvariable=self.password_var, show="*", width=40)
        self.password_entry.grid(row=1, column=1, padx=5)

        # Test Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Test Options", padding="5")
        options_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Facebook Options
        ttk.Label(options_frame, text="Facebook Group URL:").grid(row=0, column=0, padx=5)
        self.fb_url_var = tk.StringVar(value="https://www.facebook.com/groups/commercial.realestate.israel")
        self.fb_url_entry = ttk.Entry(options_frame, textvariable=self.fb_url_var, width=60)
        self.fb_url_entry.grid(row=0, column=1, padx=5)

        ttk.Label(options_frame, text="Max Posts:").grid(row=1, column=0, padx=5)
        self.max_posts_var = tk.StringVar(value="5")
        self.max_posts_entry = ttk.Entry(options_frame, textvariable=self.max_posts_var, width=10)
        self.max_posts_entry.grid(row=1, column=1, sticky=tk.W, padx=5)

        # Yad2 Options
        ttk.Label(options_frame, text="Max Pages:").grid(row=2, column=0, padx=5)
        self.max_pages_var = tk.StringVar(value="1")
        self.max_pages_entry = ttk.Entry(options_frame, textvariable=self.max_pages_var, width=10)
        self.max_pages_entry.grid(row=2, column=1, sticky=tk.W, padx=5)

        # Buttons Frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(buttons_frame, text="Test Facebook", command=self.test_facebook).grid(row=0, column=0, padx=5)
        ttk.Button(buttons_frame, text="Test Yad2", command=self.test_yad2).grid(row=0, column=1, padx=5)
        ttk.Button(buttons_frame, text="Test Full System", command=self.test_full_system).grid(row=0, column=2, padx=5)
        ttk.Button(buttons_frame, text="Clear Log", command=self.clear_log).grid(row=0, column=3, padx=5)

        # Log Frame
        log_frame = ttk.LabelFrame(main_frame, text="Test Log", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def log(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def clear_log(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)

    def save_credentials(self):
        """Save Facebook credentials to .env file"""
        with open('.env', 'w') as f:
            f.write(f'FACEBOOK_EMAIL={self.email_var.get()}\n')
            f.write(f'FACEBOOK_PASSWORD={self.password_var.get()}\n')
        self.log("Credentials saved to .env file")

    def test_facebook(self):
        """Test Facebook scraper"""
        def run():
            try:
                self.save_credentials()
                self.log("Starting Facebook scraper test...")
                
                options = webdriver.ChromeOptions()
                options.add_argument('--start-maximized')
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                scraper = FacebookScraper(driver)
                
                group_url = self.fb_url_var.get()
                max_posts = int(self.max_posts_var.get())
                
                self.log(f"Testing group: {group_url}")
                properties = scraper.scrape_group(group_url, max_posts=max_posts)
                self.log(f"Found {len(properties)} properties")
                
                # Save results
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'facebook_test_results_{timestamp}.json'
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(properties, f, ensure_ascii=False, indent=2)
                
                # Log results
                self.log("\nResults Summary:")
                for i, prop in enumerate(properties, 1):
                    self.log(f"\nProperty {i}:")
                    self.log(f"Type: {prop.get('property_type', 'N/A')}")
                    self.log(f"Price: {prop.get('price', 'N/A')}")
                    self.log(f"Location: {prop.get('location', 'N/A')}")
                    self.log(f"Size: {prop.get('size', 'N/A')}")
                
                self.log(f"\nResults saved to: {output_file}")
                
            except Exception as e:
                self.log(f"Error: {str(e)}")
            finally:
                driver.quit()
                
        threading.Thread(target=run, daemon=True).start()

    def test_yad2(self):
        """Test Yad2 scraper"""
        def run():
            try:
                self.log("Starting Yad2 scraper test...")
                
                options = webdriver.ChromeOptions()
                options.add_argument('--start-maximized')
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                scraper = Yad2Scraper(driver)
                
                max_pages = int(self.max_pages_var.get())
                properties = scraper.scrape_listings(max_pages=max_pages)
                self.log(f"Found {len(properties)} properties")
                
                # Save results
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'yad2_test_results_{timestamp}.json'
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(properties, f, ensure_ascii=False, indent=2)
                
                # Log results
                self.log("\nResults Summary:")
                for i, prop in enumerate(properties, 1):
                    self.log(f"\nProperty {i}:")
                    self.log(f"Type: {prop.get('property_type', 'N/A')}")
                    self.log(f"Price: {prop.get('price', 'N/A')}")
                    self.log(f"Location: {prop.get('location', 'N/A')}")
                    self.log(f"Size: {prop.get('size', 'N/A')}")
                
                self.log(f"\nResults saved to: {output_file}")
                
            except Exception as e:
                self.log(f"Error: {str(e)}")
            finally:
                driver.quit()
                
        threading.Thread(target=run, daemon=True).start()

    def test_full_system(self):
        """Test full system"""
        def run():
            try:
                self.save_credentials()
                self.log("Starting full system test...")
                
                orchestrator = RealEstateOrchestrator()
                orchestrator.run()
                
                self.log("Full system test completed")
                self.log("Check the 'data' directory for results")
                
            except Exception as e:
                self.log(f"Error: {str(e)}")
                
        threading.Thread(target=run, daemon=True).start()

    def run(self):
        """Start the UI"""
        # Load credentials if they exist
        if self.fb_email and self.fb_password:
            self.email_var.set(self.fb_email)
            self.password_var.set(self.fb_password)
        
        self.root.mainloop()

if __name__ == "__main__":
    app = TestUI()
    app.run()
