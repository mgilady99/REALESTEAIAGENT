# Real Estate AI Agent

An intelligent agent for scraping and analyzing commercial real estate listings. This tool automatically collects property listings from specified websites and organizes them in Google Sheets.

## Features

- 🤖 Automated web scraping of real estate listings
- 📊 Google Sheets integration for data storage and analysis
- ⏰ Configurable scheduling (hourly/daily/weekly)
- 🔍 Advanced filtering capabilities
- 📧 Email notifications for new listings
- 🌐 Support for multiple websites
- 📱 Modern web interface for monitoring and configuration

## Setup

1. Clone the repository:
```bash
git clone https://github.com/mgilady99/REALESTEAIAGENT.git
cd REALESTEAIAGENT
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy `.env.example` to `.env`
- Update the variables with your configuration

5. Set up Google Sheets API:
- Create a Google Cloud Project
- Enable Google Sheets API
- Create service account and download credentials
- Save as `credentials.json` in project root
- Share target Google Sheet with service account email

## Configuration

### Website Configuration
Add your target websites in `config.py`:
```python
WEBSITES = {
    'website_name': {
        'url': 'https://example.com/commercial',
        'selectors': {
            'listings': '.property-listing',
            'title': '.property-title',
            'price': '.property-price',
            'size': '.property-size',
            'location': '.property-location',
            'type': '.property-type',
            'link': '.property-link'
        }
    }
}
```

### Search Criteria
Configure default search criteria in `config.py`:
```python
DEFAULT_CRITERIA = {
    'min_price': 0,
    'max_price': float('inf'),
    'min_size': 0,
    'max_size': float('inf'),
    'property_types': ['commercial', 'retail', 'office', 'industrial'],
    'locations': []
}
```

## Usage

1. Start the scraper:
```bash
python main.py
```

2. Monitor through web interface:
```bash
python app.py
```

Access the dashboard at `http://localhost:5000`

## Project Structure

```
REALESTEAIAGENT/
├── app.py              # Web interface
├── config.py           # Configuration settings
├── scraper.py          # Main scraping logic
├── sheets_handler.py   # Google Sheets integration
├── models.py           # Database models
├── utils.py           # Utility functions
├── templates/         # Web interface templates
├── static/           # Static files (CSS, JS)
├── requirements.txt   # Python dependencies
└── README.md         # Project documentation
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
