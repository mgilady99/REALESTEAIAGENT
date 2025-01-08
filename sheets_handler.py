from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
import logging
from datetime import datetime

class GoogleSheetsHandler:
    def __init__(self, credentials_path):
        """Initialize Google Sheets API client"""
        self.setup_logging()
        self.setup_credentials(credentials_path)
        
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            filename='sheets_handler.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def setup_credentials(self, credentials_path):
        """Set up Google Sheets API credentials"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            self.creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES)
            self.service = build('sheets', 'v4', credentials=self.creds)
            self.sheets = self.service.spreadsheets()
        except Exception as e:
            logging.error(f"Error setting up Google Sheets credentials: {str(e)}")
            raise
            
    def create_sheet(self, spreadsheet_id, sheet_name):
        """Create a new sheet in the spreadsheet"""
        try:
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }
            body = {'requests': [request]}
            response = self.sheets.batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            return response
        except HttpError as e:
            if 'already exists' in str(e):
                logging.warning(f"Sheet '{sheet_name}' already exists")
            else:
                logging.error(f"Error creating sheet: {str(e)}")
                raise
                
    def setup_headers(self, spreadsheet_id, sheet_name):
        """Set up headers in the sheet"""
        headers = [
            'Date Added', 'Title', 'Price', 'Location', 'Size', 'Type',
            'URL', 'Source', 'Description', 'Contact Info', 'Last Updated'
        ]
        
        try:
            range_name = f'{sheet_name}!A1:K1'
            body = {'values': [headers]}
            self.sheets.values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Format headers
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': self.get_sheet_id(spreadsheet_id, sheet_name),
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                            'textFormat': {'bold': True}
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }]
            
            body = {'requests': requests}
            self.sheets.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
            
        except Exception as e:
            logging.error(f"Error setting up headers: {str(e)}")
            raise
            
    def get_sheet_id(self, spreadsheet_id, sheet_name):
        """Get the sheet ID by name"""
        try:
            spreadsheet = self.sheets.get(spreadsheetId=spreadsheet_id).execute()
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            return None
        except Exception as e:
            logging.error(f"Error getting sheet ID: {str(e)}")
            raise
            
    def get_existing_listings(self, spreadsheet_id, sheet_name):
        """Get existing listings from the sheet"""
        try:
            result = self.sheets.values().get(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A:G'
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return set()
                
            # Skip header row and get URLs (column G)
            return {row[6] for row in values[1:] if len(row) > 6}
            
        except Exception as e:
            logging.error(f"Error getting existing listings: {str(e)}")
            return set()
            
    def update_sheet(self, spreadsheet_id, listings, sheet_name='Listings'):
        """Update sheet with new listings"""
        try:
            # Ensure sheet exists
            try:
                self.create_sheet(spreadsheet_id, sheet_name)
                self.setup_headers(spreadsheet_id, sheet_name)
            except:
                pass
                
            # Get existing listings
            existing_urls = self.get_existing_listings(spreadsheet_id, sheet_name)
            
            # Filter out existing listings
            new_listings = [l for l in listings if l['url'] not in existing_urls]
            
            if not new_listings:
                logging.info("No new listings to add")
                return
                
            # Prepare data for Google Sheets
            values = [[
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                listing.get('title', ''),
                listing.get('price', ''),
                listing.get('location', ''),
                listing.get('size', ''),
                listing.get('type', ''),
                listing.get('url', ''),
                listing.get('source_website', ''),
                listing.get('description', ''),
                listing.get('contact_info', ''),
                listing.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            ] for listing in new_listings]
            
            body = {
                'values': values
            }
            
            # Append new listings
            self.sheets.values().append(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A:K',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logging.info(f"Added {len(new_listings)} new listings to sheet")
            
        except Exception as e:
            logging.error(f"Error updating sheet: {str(e)}")
            raise
            
    def format_sheet(self, spreadsheet_id, sheet_name):
        """Apply formatting to the sheet"""
        try:
            sheet_id = self.get_sheet_id(spreadsheet_id, sheet_name)
            requests = [
                # Auto-resize columns
                {
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 11
                        }
                    }
                },
                # Format price column
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startColumnIndex': 2,
                            'endColumnIndex': 3
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'numberFormat': {
                                    'type': 'CURRENCY',
                                    'pattern': '"$"#,##0.00'
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.numberFormat'
                    }
                }
            ]
            
            body = {'requests': requests}
            self.sheets.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
            
        except Exception as e:
            logging.error(f"Error formatting sheet: {str(e)}")
            raise
