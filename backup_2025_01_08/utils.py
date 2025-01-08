import re
from datetime import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def setup_logging(name, filename):
    """Set up logging configuration"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.FileHandler(filename)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def clean_price(price_text):
    """Convert price text to float"""
    if not price_text:
        return None
    
    try:
        # Remove currency symbols and convert to float
        price = ''.join(filter(str.isdigit, price_text))
        return float(price) if price else None
    except Exception:
        return None

def clean_size(size_text):
    """Convert size text to float"""
    if not size_text:
        return None
    
    try:
        # Extract number before 'SF' or 'AC'
        match = re.search(r'([\d,]+)\s*(?:SF|AC)', size_text)
        if match:
            size = match.group(1).replace(',', '')
            return float(size)
        return None
    except Exception:
        return None

def format_currency(amount):
    """Format number as currency"""
    if amount is None:
        return "N/A"
    return "${:,.2f}".format(amount)

def format_size(size):
    """Format size with appropriate unit"""
    if size is None:
        return "N/A"
    if size >= 43560:  # Convert to acres if >= 1 acre (43,560 sq ft)
        return "{:,.2f} AC".format(size / 43560)
    return "{:,.0f} SF".format(size)

def send_email_notification(subject, body, recipients=None):
    """Send email notification"""
    if not Config.ENABLE_EMAIL_NOTIFICATIONS:
        return
    
    if not recipients:
        recipients = Config.EMAIL_RECIPIENTS
    
    try:
        msg = MIMEMultipart()
        msg['From'] = Config.EMAIL_SENDER
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
            server.send_message(msg)
            
    except Exception as e:
        logging.error(f"Error sending email notification: {str(e)}")

def generate_listing_notification(new_listings):
    """Generate HTML email for new listings"""
    html = """
    <html>
        <head>
            <style>
                .listing {
                    margin-bottom: 20px;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                .price {
                    color: #2c3e50;
                    font-weight: bold;
                }
                .details {
                    color: #666;
                    font-size: 0.9em;
                }
            </style>
        </head>
        <body>
            <h2>New Property Listings</h2>
            <p>The following new properties were found:</p>
    """
    
    for listing in new_listings:
        html += f"""
            <div class="listing">
                <h3>{listing['title']}</h3>
                <p class="price">{format_currency(listing['price'])}</p>
                <p class="details">
                    Location: {listing['location']}<br>
                    Size: {format_size(listing['size'])}<br>
                    Type: {listing['property_type']}<br>
                    <a href="{listing['url']}">View Listing</a>
                </p>
            </div>
        """
    
    html += """
        </body>
    </html>
    """
    
    return html

def validate_search_criteria(criteria):
    """Validate search criteria"""
    errors = []
    
    # Check price range
    if criteria.get('min_price') and criteria.get('max_price'):
        if float(criteria['min_price']) > float(criteria['max_price']):
            errors.append("Minimum price cannot be greater than maximum price")
    
    # Check size range
    if criteria.get('min_size') and criteria.get('max_size'):
        if float(criteria['min_size']) > float(criteria['max_size']):
            errors.append("Minimum size cannot be greater than maximum size")
    
    # Check property types
    valid_types = ['commercial', 'retail', 'office', 'industrial']
    if criteria.get('property_types'):
        invalid_types = [t for t in criteria['property_types'] if t not in valid_types]
        if invalid_types:
            errors.append(f"Invalid property types: {', '.join(invalid_types)}")
    
    return errors

def format_listing_for_sheets(listing):
    """Format listing data for Google Sheets"""
    return [
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        listing.get('title', ''),
        format_currency(listing.get('price')),
        listing.get('location', ''),
        format_size(listing.get('size')),
        listing.get('property_type', ''),
        listing.get('url', ''),
        listing.get('source_website', ''),
        listing.get('description', '')[:500] if listing.get('description') else '',
        str(listing.get('contact_info', {}))
    ]
