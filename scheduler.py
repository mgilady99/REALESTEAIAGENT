from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from main import RealEstateOrchestrator
import signal
import sys
import time

class ScraperScheduler:
    def __init__(self):
        self.setup_logging()
        self.scheduler = BackgroundScheduler()
        self.orchestrator = RealEstateOrchestrator()
        self.setup_signal_handlers()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            filename='scheduler.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_signal_handlers(self):
        """Setup handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Received shutdown signal. Stopping scheduler...")
        self.scheduler.shutdown()
        sys.exit(0)

    def run_scraper(self):
        """Run the scraper"""
        try:
            self.logger.info(f"Starting scheduled scraping at {datetime.now()}")
            self.orchestrator.run()
            self.logger.info(f"Completed scheduled scraping at {datetime.now()}")
        except Exception as e:
            self.logger.error(f"Error in scheduled scraping: {str(e)}")

    def start(self):
        """Start the scheduler"""
        try:
            # Schedule scraping jobs
            # Run every 3 hours during business hours (8 AM to 8 PM)
            self.scheduler.add_job(
                self.run_scraper,
                CronTrigger(
                    hour='8-20/3',  # Every 3 hours from 8 AM to 8 PM
                    minute='0',     # At the start of the hour
                    day_of_week='mon-fri'  # Monday to Friday
                ),
                id='regular_scraping'
            )
            
            # Add an immediate run
            self.scheduler.add_job(
                self.run_scraper,
                'date',
                run_date=datetime.now(),
                id='immediate_run'
            )
            
            self.scheduler.start()
            self.logger.info("Scheduler started successfully")
            
            # Keep the script running
            try:
                while True:
                    time.sleep(60)
            except (KeyboardInterrupt, SystemExit):
                self.handle_shutdown(None, None)
                
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {str(e)}")
            raise

def main():
    scheduler = ScraperScheduler()
    scheduler.start()

if __name__ == "__main__":
    main()
