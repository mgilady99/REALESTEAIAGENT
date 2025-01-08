from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
from scraper import RealEstateScraper
from models import db, Property, SearchCriteria, ScrapingLog
from sheets_handler import GoogleSheetsHandler
import pandas as pd
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()

def start_scraper():
    """Initialize and start the scraper"""
    with app.app_context():
        scraper = RealEstateScraper()
        listings = scraper.run()
        
        # Log scraping activity
        log = ScrapingLog(
            website="all",
            end_time=datetime.utcnow(),
            status="success" if listings else "failed",
            items_scraped=len(listings),
            items_new=len(listings)
        )
        db.session.add(log)
        db.session.commit()

def setup_scheduler():
    """Setup scheduled tasks"""
    scheduler = BackgroundScheduler()
    
    # Add scraping jobs
    if Config.SCRAPING_INTERVALS['hourly']:
        scheduler.add_job(start_scraper, 'interval', hours=1)
    if Config.SCRAPING_INTERVALS['daily']:
        scheduler.add_job(start_scraper, 'cron', hour=9)  # Run at 9 AM
    if Config.SCRAPING_INTERVALS['weekly']:
        scheduler.add_job(start_scraper, 'cron', day_of_week='mon', hour=9)  # Run Mondays at 9 AM
        
    scheduler.start()

@app.route('/')
def home():
    """Home page"""
    return render_template('index.html')

@app.route('/properties')
def properties():
    """List properties"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Apply filters
    query = Property.query
    
    if request.args.get('min_price'):
        query = query.filter(Property.price >= float(request.args.get('min_price')))
    if request.args.get('max_price'):
        query = query.filter(Property.price <= float(request.args.get('max_price')))
    if request.args.get('property_type'):
        query = query.filter(Property.property_type == request.args.get('property_type'))
    if request.args.get('location'):
        query = query.filter(Property.location.ilike(f"%{request.args.get('location')}%"))
        
    properties = query.order_by(Property.date_scraped.desc()).paginate(page=page, per_page=per_page)
    return render_template('properties.html', properties=properties)

@app.route('/search-criteria', methods=['GET', 'POST'])
def search_criteria():
    """Manage search criteria"""
    if request.method == 'POST':
        data = request.json
        criteria = SearchCriteria(
            name=data['name'],
            min_price=data.get('min_price'),
            max_price=data.get('max_price'),
            min_size=data.get('min_size'),
            max_size=data.get('max_size'),
            property_types=','.join(data.get('property_types', [])),
            locations=','.join(data.get('locations', [])),
            keywords=','.join(data.get('keywords', [])),
            notification_email=data.get('notification_email'),
            is_active=True
        )
        db.session.add(criteria)
        db.session.commit()
        return jsonify({'message': 'Search criteria added successfully'})
    
    criteria_list = SearchCriteria.query.all()
    return render_template('search_criteria.html', criteria=criteria_list)

@app.route('/api/properties')
def api_properties():
    """API endpoint for properties"""
    properties = Property.query.order_by(Property.date_scraped.desc()).limit(100).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'price': p.price,
        'location': p.location,
        'size': p.size,
        'property_type': p.property_type,
        'url': p.url,
        'source_website': p.source_website,
        'date_scraped': p.date_scraped.isoformat()
    } for p in properties])

@app.route('/export-properties')
def export_properties():
    """Export properties to CSV"""
    properties = Property.query.all()
    df = pd.DataFrame([{
        'Title': p.title,
        'Price': p.price,
        'Location': p.location,
        'Size': p.size,
        'Type': p.property_type,
        'URL': p.url,
        'Source': p.source_website,
        'Date Scraped': p.date_scraped
    } for p in properties])
    
    csv_file = 'properties_export.csv'
    df.to_csv(csv_file, index=False)
    return send_file(csv_file, as_attachment=True)

@app.route('/logs')
def view_logs():
    """View scraping logs"""
    logs = ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).limit(100).all()
    return render_template('logs.html', logs=logs)

if __name__ == '__main__':
    init_db()
    setup_scheduler()
    app.run(debug=True)
