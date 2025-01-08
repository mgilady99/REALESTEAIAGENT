import yaml
import logging
from pathlib import Path

class WebsiteManager:
    def __init__(self, config_path='websites_config.yaml'):
        self.config_path = config_path
        self.logger = logging.getLogger('WebsiteManager')
        self.load_config()

    def load_config(self):
        """Load website configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
                self.logger.info(f"Successfully loaded configuration from {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            self.config = {'websites': {}, 'settings': {}, 'proxy_settings': {}}

    def save_config(self):
        """Save current configuration to YAML file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config, file, allow_unicode=True, sort_keys=False)
            self.logger.info(f"Successfully saved configuration to {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False

    def get_enabled_websites(self):
        """Get list of enabled websites"""
        return {
            name: config 
            for name, config in self.config['websites'].items() 
            if config.get('enabled', True)
        }

    def add_website(self, name, config):
        """Add a new website configuration"""
        if name in self.config['websites']:
            self.logger.warning(f"Website {name} already exists. Use update_website to modify.")
            return False

        self.config['websites'][name] = config
        return self.save_config()

    def update_website(self, name, config):
        """Update existing website configuration"""
        if name not in self.config['websites']:
            self.logger.warning(f"Website {name} does not exist. Use add_website to create new.")
            return False

        self.config['websites'][name].update(config)
        return self.save_config()

    def remove_website(self, name):
        """Remove a website from configuration"""
        if name not in self.config['websites']:
            self.logger.warning(f"Website {name} does not exist.")
            return False

        del self.config['websites'][name]
        return self.save_config()

    def enable_website(self, name):
        """Enable a website"""
        if name not in self.config['websites']:
            return False
        self.config['websites'][name]['enabled'] = True
        return self.save_config()

    def disable_website(self, name):
        """Disable a website"""
        if name not in self.config['websites']:
            return False
        self.config['websites'][name]['enabled'] = False
        return self.save_config()

    def get_website_config(self, name):
        """Get configuration for a specific website"""
        return self.config['websites'].get(name)

    def get_settings(self):
        """Get global scraping settings"""
        return self.config.get('settings', {})

    def update_settings(self, settings):
        """Update global scraping settings"""
        self.config['settings'] = settings
        return self.save_config()

    def get_proxy_settings(self):
        """Get proxy settings"""
        return self.config.get('proxy_settings', {})

    def update_proxy_settings(self, settings):
        """Update proxy settings"""
        self.config['proxy_settings'] = settings
        return self.save_config()

    def validate_website_config(self, config):
        """Validate website configuration structure"""
        required_fields = ['name', 'base_url', 'search_path', 'selectors']
        required_selectors = ['listings', 'title', 'price', 'size', 'location', 'property_type', 'link']

        # Check required fields
        for field in required_fields:
            if field not in config:
                self.logger.error(f"Missing required field: {field}")
                return False

        # Check required selectors
        for selector in required_selectors:
            if selector not in config['selectors']:
                self.logger.error(f"Missing required selector: {selector}")
                return False

        return True

    def create_website_template(self):
        """Create a template for new website configuration"""
        return {
            'name': 'New Website',
            'enabled': True,
            'base_url': 'https://www.example.com',
            'search_path': '/search',
            'selectors': {
                'listings': '.listing-container',
                'title': '.title',
                'price': '.price',
                'size': '.size',
                'location': '.location',
                'property_type': '.type',
                'description': '.description',
                'contact_info': '.contact',
                'link': '.link'
            }
        }
