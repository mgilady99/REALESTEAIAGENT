from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Property(db.Model):
    """Model for storing real estate property listings"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float)
    location = db.Column(db.String(200))
    size = db.Column(db.Float)
    property_type = db.Column(db.String(50))
    url = db.Column(db.String(500), unique=True)
    source_website = db.Column(db.String(100))
    description = db.Column(db.Text)
    amenities = db.Column(db.Text)
    contact_info = db.Column(db.String(200))
    date_listed = db.Column(db.DateTime)
    date_scraped = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class SearchCriteria(db.Model):
    """Model for storing search criteria configurations"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    min_price = db.Column(db.Float)
    max_price = db.Column(db.Float)
    min_size = db.Column(db.Float)
    max_size = db.Column(db.Float)
    property_types = db.Column(db.String(200))  # Comma-separated list
    locations = db.Column(db.String(500))       # Comma-separated list
    keywords = db.Column(db.String(200))        # Comma-separated list
    is_active = db.Column(db.Boolean, default=True)
    notification_email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScrapingLog(db.Model):
    """Model for logging scraping activities"""
    id = db.Column(db.Integer, primary_key=True)
    website = db.Column(db.String(100))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20))  # success, failed, partial
    items_scraped = db.Column(db.Integer)
    items_new = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    
    def calculate_duration(self):
        """Calculate duration of scraping operation"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
