# Real Estate AI Agent Customization Guide

## How to Add Custom Sources

### 1. Adding New Websites
Edit `websites_config.yaml` and add your website under `custom_sites.sites`:

```yaml
custom_sites:
  enabled: true
  sites:
    - name: "Your Website Name"
      base_url: "https://example.com"
      search_path: "/commercial"
      selectors:
        listings: ".listing-class"
        title: ".title-class"
        price: ".price-class"
        size: ".size-class"
        location: ".location-class"
        property_type: ".type-class"
        description: ".description-class"
        contact_info: ".contact-class"
        link: ".link-class"
      property_types:
        - "משרדים"
        - "מסחרי"
```

### 2. Adding Facebook Groups
Add your groups under `facebook_groups.custom_groups`:

```yaml
facebook_groups:
  custom_groups:
    - name: "Your Group Name"
      url: "https://www.facebook.com/groups/your-group-id"
      property_types:
        - "משרדים"
        - "מסחרי"
```

### 3. Adding New Areas
Add new areas to the location detection in `facebook_scraper.py`:

```python
def extract_location(self, text):
    cities = {
        'Your City': ['variation1', 'variation2'],
    }
    
    your_city_neighborhoods = [
        'neighborhood1',
        'neighborhood2'
    ]
```

### 4. Adding Property Types
Add new property types in `websites_config.yaml`:

```yaml
commercial_property_types:
  your_type:
    hebrew: ["Hebrew Term 1", "Hebrew Term 2"]
    english: ["English Term"]
```

### 5. Adding Custom Features
Add new features in `facebook_scraper.py`:

```python
def extract_commercial_features(self, text):
    features = {
        'your_feature': False,
    }
    
    feature_keywords = {
        'your_feature': ['keyword1', 'keyword2'],
    }
```

## Important Files

1. `websites_config.yaml` - Main configuration file
2. `scrapers/facebook_scraper.py` - Facebook scraping logic
3. `scrapers/yad2_scraper.py` - Yad2 scraping logic

## Tips for Customization

1. **Testing Selectors**:
   - Use browser developer tools to find correct CSS selectors
   - Test selectors before adding them to configuration

2. **Adding New Features**:
   - Keep Hebrew and English translations consistent
   - Follow existing naming patterns

3. **Debugging**:
   - Check logs in `facebook_scraper.log`
   - Use the selector testing tool for new websites

4. **Best Practices**:
   - Backup configuration before making changes
   - Test new scrapers with small data sets first
   - Keep property types consistent across all scrapers

## Example: Adding a New Website

1. First, inspect the website's HTML structure
2. Identify the correct selectors
3. Add configuration:

```yaml
custom_sites:
  sites:
    - name: "New Commercial Site"
      base_url: "https://newsite.com"
      search_path: "/commercial"
      selectors:
        listings: ".property-card"
        title: ".property-title"
        # ... other selectors
```

## Example: Adding a New Area

1. Identify common name variations
2. Add to configuration:

```python
cities = {
    'Your Area': ['variation1', 'variation2'],
}

area_neighborhoods = [
    'neighborhood1',
    'neighborhood2',
]
```

## Need Help?

1. Check the logs for error messages
2. Use the selector testing tool
3. Follow the existing patterns in the code
4. Keep backups before making changes
