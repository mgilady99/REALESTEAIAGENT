import pandas as pd
import json
from datetime import datetime
import logging
import os
from typing import List, Dict, Any
import numpy as np

class CommercialPropertyProcessor:
    def __init__(self, output_dir: str = 'data'):
        self.output_dir = output_dir
        self.setup_logging()
        self.ensure_directories()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            filename='property_processor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def ensure_directories(self):
        """Ensure necessary directories exist"""
        directories = [
            self.output_dir,
            os.path.join(self.output_dir, 'raw'),
            os.path.join(self.output_dir, 'processed'),
            os.path.join(self.output_dir, 'analytics')
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def normalize_price(self, price: Any) -> float:
        """Normalize price to standard format"""
        try:
            if isinstance(price, (int, float)):
                return float(price)
            if not price or not isinstance(price, str):
                return np.nan
            
            # Remove currency symbols and commas
            price = price.replace('₪', '').replace(',', '').strip()
            
            # Handle different formats
            if 'מיליון' in price or 'million' in price:
                num = float(''.join(filter(str.isdigit, price))) * 1_000_000
            elif 'אלף' in price or 'thousand' in price:
                num = float(''.join(filter(str.isdigit, price))) * 1_000
            else:
                num = float(''.join(filter(str.isdigit, price)))
            
            return num
        except Exception as e:
            self.logger.error(f"Error normalizing price {price}: {str(e)}")
            return np.nan

    def normalize_size(self, size: Any) -> float:
        """Normalize size to square meters"""
        try:
            if isinstance(size, (int, float)):
                return float(size)
            if not size or not isinstance(size, str):
                return np.nan
            
            # Extract numeric value
            num = float(''.join(filter(str.isdigit, size)))
            
            # Convert to square meters if necessary
            if 'sqft' in size.lower() or 'sq ft' in size.lower():
                num *= 0.092903  # Convert square feet to square meters
            
            return num
        except Exception as e:
            self.logger.error(f"Error normalizing size {size}: {str(e)}")
            return np.nan

    def process_properties(self, properties: List[Dict]) -> pd.DataFrame:
        """Process list of properties into standardized DataFrame"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(properties)
            
            # Normalize numeric columns
            df['price_normalized'] = df['price'].apply(self.normalize_price)
            df['size_normalized'] = df['size'].apply(self.normalize_size)
            
            # Calculate price per square meter
            df['price_per_sqm'] = df['price_normalized'] / df['size_normalized']
            
            # Add timestamp
            df['processed_at'] = datetime.now()
            
            return df
        except Exception as e:
            self.logger.error(f"Error processing properties: {str(e)}")
            return pd.DataFrame()

    def save_data(self, df: pd.DataFrame, source: str):
        """Save processed data to files"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save raw data
            raw_path = os.path.join(self.output_dir, 'raw', f'{source}_{timestamp}.json')
            df.to_json(raw_path, orient='records', force_ascii=False)
            
            # Save processed data
            processed_path = os.path.join(self.output_dir, 'processed', f'{source}_{timestamp}.csv')
            df.to_csv(processed_path, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"Saved data for {source}: {len(df)} records")
            
            # Generate analytics
            self.generate_analytics(df, source, timestamp)
            
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")

    def generate_analytics(self, df: pd.DataFrame, source: str, timestamp: str):
        """Generate analytics from processed data"""
        try:
            analytics = {
                'source': source,
                'timestamp': timestamp,
                'total_properties': len(df),
                'price_stats': {
                    'mean': df['price_normalized'].mean(),
                    'median': df['price_normalized'].median(),
                    'min': df['price_normalized'].min(),
                    'max': df['price_normalized'].max()
                },
                'size_stats': {
                    'mean': df['size_normalized'].mean(),
                    'median': df['size_normalized'].median(),
                    'min': df['size_normalized'].min(),
                    'max': df['size_normalized'].max()
                },
                'price_per_sqm_stats': {
                    'mean': df['price_per_sqm'].mean(),
                    'median': df['price_per_sqm'].median(),
                    'min': df['price_per_sqm'].min(),
                    'max': df['price_per_sqm'].max()
                },
                'property_types': df['property_type'].value_counts().to_dict(),
                'locations': df['location'].value_counts().to_dict()
            }
            
            # Save analytics
            analytics_path = os.path.join(self.output_dir, 'analytics', f'{source}_{timestamp}.json')
            with open(analytics_path, 'w', encoding='utf-8') as f:
                json.dump(analytics, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Generated analytics for {source}")
            
        except Exception as e:
            self.logger.error(f"Error generating analytics: {str(e)}")

    def analyze_market_trends(self, days_back: int = 30):
        """Analyze market trends from historical data"""
        try:
            # Get all processed files
            processed_dir = os.path.join(self.output_dir, 'processed')
            all_files = os.listdir(processed_dir)
            
            # Combine recent files
            dfs = []
            for file in all_files:
                if file.endswith('.csv'):
                    file_path = os.path.join(processed_dir, file)
                    df = pd.read_csv(file_path)
                    dfs.append(df)
            
            if not dfs:
                return
            
            # Combine all data
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Calculate trends
            trends = {
                'price_trend': {
                    'mean_change': self._calculate_trend(combined_df, 'price_normalized'),
                    'median_change': self._calculate_trend(combined_df, 'price_normalized', 'median')
                },
                'price_per_sqm_trend': {
                    'mean_change': self._calculate_trend(combined_df, 'price_per_sqm'),
                    'median_change': self._calculate_trend(combined_df, 'price_per_sqm', 'median')
                },
                'popular_areas': combined_df['location'].value_counts().head(10).to_dict(),
                'popular_types': combined_df['property_type'].value_counts().head(5).to_dict()
            }
            
            # Save trends
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            trends_path = os.path.join(self.output_dir, 'analytics', f'market_trends_{timestamp}.json')
            with open(trends_path, 'w', encoding='utf-8') as f:
                json.dump(trends, f, ensure_ascii=False, indent=2)
            
            self.logger.info("Generated market trends analysis")
            
        except Exception as e:
            self.logger.error(f"Error analyzing market trends: {str(e)}")

    def _calculate_trend(self, df: pd.DataFrame, column: str, method: str = 'mean') -> float:
        """Calculate trend for a specific column"""
        try:
            if method == 'mean':
                return df[column].mean()
            elif method == 'median':
                return df[column].median()
        except Exception:
            return 0.0
