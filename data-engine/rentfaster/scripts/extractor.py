#!/usr/bin/env python3
"""
Rentfaster API Data Extractor
Extracts current rental listings from Rentfaster's API for Calgary
"""

import requests
import pandas as pd
import json
import sys
import os
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Define validation directory directly
VALIDATION_PENDING_DIR = "/home/chris/calgary-analytica/data-engine/validation/pending"

class Config:
    VALIDATION_PENDING_DIR = VALIDATION_PENDING_DIR

config = Config()

class RentfasterExtractor:
    def __init__(self):
        self.base_url = "https://www.rentfaster.ca/api/search.json"
        self.calgary_city_id = 1  # Calgary's ID in Rentfaster
        self.data = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def fetch_listings(self, page=1):
        """Fetch listings from Rentfaster API"""
        params = {
            'city_id': self.calgary_city_id,
            'cur_page': page,
            'proximity_type': 'location-city'
        }
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            return None
    
    def parse_listing(self, listing):
        """Parse individual listing data"""
        try:
            # Extract property type
            property_type = self.normalize_property_type(
                listing.get('type', ''),
                listing.get('property_type', '')
            )
            
            # Parse bedrooms (comes as ranges like "1 - 2" or "studio - 3")
            bedrooms = self.parse_bedrooms(listing.get('bedrooms', '0'))
            
            # Extract only market-relevant fields (no address/coordinates for privacy)
            return {
                'listing_id': listing.get('ref_id', ''),
                'property_type': property_type,
                'bedrooms': bedrooms,
                'bathrooms': float(listing.get('baths', 0)),
                'rent': float(listing.get('price', 0)),
                'sq_feet': int(listing.get('sq_feet', 0)) if listing.get('sq_feet') else None,
                'community': listing.get('community', '')
            }
        except Exception as e:
            print(f"Error parsing listing: {e}")
            return None
    
    def parse_bedrooms(self, bedroom_str):
        """Parse bedroom string which can be a range like '1 - 2' or 'studio - 3'"""
        if not bedroom_str or bedroom_str == '':
            return 0
            
        bedroom_str = str(bedroom_str).lower().strip()
        
        # Handle "studio" cases
        if 'studio' in bedroom_str:
            return 0
            
        # Handle single numbers
        if bedroom_str.isdigit():
            return int(bedroom_str)
            
        # Handle ranges like "1 - 2"
        if ' - ' in bedroom_str:
            parts = bedroom_str.split(' - ')
            if parts[0].strip().isdigit():
                return int(parts[0].strip())  # Return minimum
            
        # Default case
        return 0
    
    def normalize_property_type(self, type_str, property_type_str):
        """Normalize property type to match our database categories"""
        combined = f"{type_str} {property_type_str}".lower()
        
        if 'house' in combined or 'detached' in combined:
            return 'single_detached'
        elif 'condo' in combined or 'apartment' in combined:
            return 'apartment'
        elif 'townhouse' in combined or 'townhome' in combined or 'row' in combined:
            return 'townhouse'
        elif 'duplex' in combined or 'semi' in combined:
            return 'semi_detached'
        elif 'basement' in combined:
            return 'basement_suite'
        elif 'room' in combined:
            return 'room'
        else:
            return 'other'
    
    def extract(self, max_pages=10):
        """Main extraction method"""
        print(f"Starting Rentfaster extraction for Calgary...")
        print(f"Timestamp: {datetime.now()}")
        
        total_listings = 0
        
        for page in range(1, max_pages + 1):
            print(f"\nFetching page {page}...")
            
            data = self.fetch_listings(page)
            if not data:
                break
            
            listings = data.get('listings', [])
            if not listings:
                print("No more listings found")
                break
            
            for listing in listings:
                parsed = self.parse_listing(listing)
                if parsed:
                    self.data.append(parsed)
                    total_listings += 1
            
            print(f"Processed {len(listings)} listings (Total: {total_listings})")
            
            # Be respectful - add small delay between requests
            time.sleep(0.5)
            
            # Check if we've reached the last page
            if len(listings) < 10:  # Assuming default page size
                print("Reached last page")
                break
        
        print(f"\nExtraction complete. Total listings: {total_listings}")
        return self.format_output()
    
    def format_output(self):
        """Format extracted data for validation pipeline"""
        if not self.data:
            print("No data extracted")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(self.data)
        
        # Add extraction week for weekly snapshots
        df['extraction_week'] = datetime.now().strftime('%Y-W%U')  # Year-Week format
        
        # Calculate summary statistics
        summary_stats = df.groupby('property_type').agg({
            'rent': ['mean', 'median', 'count'],
            'bedrooms': 'mean',
            'sq_feet': 'mean'
        }).round(2)
        
        # Prepare output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"rentfaster_listings_{timestamp}"
        
        # Save detailed listings
        csv_path = os.path.join(config.VALIDATION_PENDING_DIR, f"{output_filename}.csv")
        df.to_csv(csv_path, index=False)
        print(f"\nSaved listings: {csv_path}")
        
        # Create summary report
        report = {
            "source": "rentfaster",
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_week": datetime.now().strftime('%Y-W%U'),
            "total_listings": len(df),
            "active_listings": len(df),
            "property_types": df['property_type'].value_counts().to_dict(),
            "rent_summary": {
                "mean": float(df['rent'].mean()),
                "median": float(df['rent'].median()),
                "min": float(df['rent'].min()),
                "max": float(df['rent'].max())
            },
            "bedrooms_distribution": df['bedrooms'].value_counts().to_dict(),
            "communities": df['community'].value_counts().head(20).to_dict(),
            "output_file": f"{output_filename}.csv"
        }
        
        # Save JSON report
        json_path = os.path.join(config.VALIDATION_PENDING_DIR, f"{output_filename}.json")
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Saved report: {json_path}")
        
        # Print summary
        print("\nExtraction Summary:")
        print(f"Total listings: {len(df)}")
        print(f"Property types: {', '.join(df['property_type'].unique())}")
        print(f"\nRent by property type:")
        print(summary_stats)
        
        return csv_path, json_path


def main():
    """Run the Rentfaster extractor"""
    extractor = RentfasterExtractor()
    
    # You can adjust max_pages based on how much data you want
    # Each page typically has 10-20 listings
    max_pages = 5  # Start conservative
    
    if len(sys.argv) > 1:
        max_pages = int(sys.argv[1])
    
    extractor.extract(max_pages=max_pages)


if __name__ == "__main__":
    main()