from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import pandas as pd
from main import RealEstateOrchestrator

app = Flask(__name__)

def load_latest_data():
    """Load the latest data from results files"""
    data = {
        'facebook': [],
        'yad2': [],
        'analytics': {}
    }
    
    try:
        # Get latest Facebook data
        fb_files = [f for f in os.listdir() if f.startswith('facebook_test_results_')]
        if fb_files:
            latest_fb = max(fb_files)
            with open(latest_fb, 'r', encoding='utf-8') as f:
                data['facebook'] = json.load(f)

        # Get latest Yad2 data
        yad2_files = [f for f in os.listdir() if f.startswith('yad2_test_results_')]
        if yad2_files:
            latest_yad2 = max(yad2_files)
            with open(latest_yad2, 'r', encoding='utf-8') as f:
                data['yad2'] = json.load(f)

        # Calculate analytics
        all_properties = data['facebook'] + data['yad2']
        if all_properties:
            df = pd.DataFrame(all_properties)
            data['analytics'] = {
                'total_properties': len(all_properties),
                'avg_price': df['price'].mean() if 'price' in df else 'N/A',
                'avg_size': df['size'].mean() if 'size' in df else 'N/A',
                'locations': df['location'].value_counts().head(5).to_dict() if 'location' in df else {},
                'property_types': df['property_type'].value_counts().to_dict() if 'property_type' in df else {},
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    except Exception as e:
        print(f"Error loading data: {str(e)}")
    
    return data

@app.route('/')
def index():
    """Render main dashboard"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """Get latest data"""
    return jsonify(load_latest_data())

@app.route('/api/run_scraper', methods=['POST'])
def run_scraper():
    """Run the scraper"""
    try:
        source = request.json.get('source', 'all')
        orchestrator = RealEstateOrchestrator()
        orchestrator.run()
        return jsonify({'status': 'success', 'message': 'Scraper started'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
