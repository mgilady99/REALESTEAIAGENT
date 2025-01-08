import os
import shutil
import time
from datetime import datetime
import logging

class AutoBackup:
    def __init__(self, source_dir, backup_dir, interval_minutes=5, duration_hours=2):
        self.source_dir = source_dir
        self.backup_dir = backup_dir
        self.interval_minutes = interval_minutes
        self.duration_hours = duration_hours
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename='backup.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def create_backup(self):
        try:
            # Create timestamp for backup folder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'backup_{timestamp}')

            # Create backup directory if it doesn't exist
            os.makedirs(self.backup_dir, exist_ok=True)

            # Copy all files and directories
            shutil.copytree(self.source_dir, backup_path, dirs_exist_ok=True)

            # Log success
            logging.info(f'Backup created successfully at {backup_path}')
            print(f'Backup created successfully at {backup_path}')

            # Clean old backups (keep last 5)
            self.cleanup_old_backups()

        except Exception as e:
            logging.error(f'Backup failed: {str(e)}')
            print(f'Backup failed: {str(e)}')

    def cleanup_old_backups(self):
        try:
            # Get all backup directories
            backups = [d for d in os.listdir(self.backup_dir) if d.startswith('backup_')]
            backups.sort(reverse=True)  # Sort by name (timestamp) in descending order

            # Keep only the last 5 backups
            for old_backup in backups[5:]:
                old_backup_path = os.path.join(self.backup_dir, old_backup)
                shutil.rmtree(old_backup_path)
                logging.info(f'Cleaned up old backup: {old_backup}')

        except Exception as e:
            logging.error(f'Cleanup failed: {str(e)}')

    def run(self):
        start_time = time.time()
        end_time = start_time + (self.duration_hours * 3600)  # Convert hours to seconds

        while time.time() < end_time:
            self.create_backup()
            
            # Wait for the next interval
            time.sleep(self.interval_minutes * 60)  # Convert minutes to seconds

        logging.info('Backup session completed')
        print('Backup session completed')

if __name__ == '__main__':
    # Set source and backup directories
    source_dir = os.path.dirname(os.path.abspath(__file__))
    backup_dir = os.path.join(source_dir, 'backups')

    # Create and run backup
    auto_backup = AutoBackup(
        source_dir=source_dir,
        backup_dir=backup_dir,
        interval_minutes=5,
        duration_hours=2
    )
    auto_backup.run()
