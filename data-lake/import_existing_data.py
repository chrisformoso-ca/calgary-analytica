#!/usr/bin/env python3
"""
Import Existing CSV Data to Database
Loads the existing Calgary_CREB_Data.csv and calgary_housing_master_dataset.csv into the database
"""

import sqlite3
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataImporter:
    """Import existing CSV data into the Calgary housing database."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        
    def import_city_data(self, csv_path: str) -> int:
        """Import city-wide data from Calgary_CREB_Data.csv."""
        logger.info(f"Importing city-wide data from: {csv_path}")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Found {len(df)} city-wide records")
        
        # Prepare data for database
        df['source_pdf'] = 'historical_import'
        df['extracted_date'] = datetime.now().isoformat()
        df['confidence_score'] = 1.0  # Historical data assumed validated
        df['validation_status'] = 'approved'  # Already validated data
        
        # Rename columns to match database schema
        df = df.rename(columns={
            'Date': 'date',
            'Property_Type': 'property_type',
            'Sales': 'sales',
            'New_Listings': 'new_listings',
            'Inventory': 'inventory',
            'Days_on_Market': 'days_on_market',
            'Benchmark_Price': 'benchmark_price',
            'Median_Price': 'median_price',
            'Average_Price': 'average_price'
        })
        
        # Import to database
        try:
            imported = df.to_sql('housing_city_monthly', self.conn, 
                               if_exists='append', index=False)
            self.conn.commit()
            logger.info(f"✅ Imported {len(df)} city-wide records")
            return len(df)
        except Exception as e:
            logger.error(f"Error importing city data: {e}")
            self.conn.rollback()
            return 0
    
    def import_district_data(self, csv_path: str) -> int:
        """Import district-level data from calgary_housing_master_dataset.csv."""
        logger.info(f"Importing district data from: {csv_path}")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        logger.info(f"Found {len(df)} district records")
        
        # Prepare data for database
        df['source_pdf'] = 'historical_import'
        df['extracted_date'] = datetime.now().isoformat()
        df['confidence_score'] = 1.0  # Historical data assumed validated
        df['validation_status'] = 'approved'  # Already validated data
        
        # Select only columns that exist in the database
        db_columns = ['date', 'property_type', 'district', 'new_sales', 'new_listings',
                     'sales_to_listings_ratio', 'inventory', 'months_supply', 
                     'benchmark_price', 'yoy_price_change', 'mom_price_change',
                     'source_pdf', 'extracted_date', 'confidence_score', 'validation_status']
        
        # Keep only columns that exist in both dataframe and database
        existing_columns = [col for col in db_columns if col in df.columns]
        df_to_import = df[existing_columns]
        
        # Import to database
        try:
            imported = df_to_import.to_sql('housing_district_monthly', self.conn, 
                                         if_exists='append', index=False)
            self.conn.commit()
            logger.info(f"✅ Imported {len(df_to_import)} district records")
            return len(df_to_import)
        except Exception as e:
            logger.error(f"Error importing district data: {e}")
            self.conn.rollback()
            return 0
    
    def verify_import(self):
        """Verify the imported data."""
        cursor = self.conn.cursor()
        
        # Check city data
        cursor.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM housing_city_monthly")
        city_count, city_min, city_max = cursor.fetchone()
        
        # Check district data
        cursor.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM housing_district_monthly")
        district_count, district_min, district_max = cursor.fetchone()
        
        # Property type distribution
        cursor.execute("""
            SELECT property_type, COUNT(*) 
            FROM housing_city_monthly 
            GROUP BY property_type
        """)
        city_types = cursor.fetchall()
        
        cursor.execute("""
            SELECT property_type, COUNT(DISTINCT district), COUNT(*) 
            FROM housing_district_monthly 
            GROUP BY property_type
        """)
        district_types = cursor.fetchall()
        
        print("\n📊 Import Verification:")
        print(f"\nCity-wide Data:")
        print(f"  - Total records: {city_count}")
        print(f"  - Date range: {city_min} to {city_max}")
        print(f"  - Property types:")
        for ptype, count in city_types:
            print(f"    - {ptype}: {count} records")
        
        print(f"\nDistrict-level Data:")
        print(f"  - Total records: {district_count}")
        print(f"  - Date range: {district_min} to {district_max}")
        print(f"  - Property types:")
        for ptype, districts, count in district_types:
            print(f"    - {ptype}: {count} records across {districts} districts")
    
    def close(self):
        """Close database connection."""
        self.conn.close()

def main():
    """Main import function."""
    # Use centralized configuration for paths
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config.config_manager import get_config
    
    config = get_config()
    db_path = config.get_database_path()
    city_csv = config.get_city_csv_path()
    district_csv = config.get_district_csv_path()
    
    # Check if files exist
    if not city_csv.exists():
        logger.error(f"City data CSV not found: {city_csv}")
        return
    
    if not district_csv.exists():
        logger.error(f"District data CSV not found: {district_csv}")
        return
    
    if not db_path.exists():
        logger.error(f"Database not found. Run setup_database.py first!")
        return
    
    # Import data
    importer = DataImporter(db_path)
    
    city_count = importer.import_city_data(city_csv)
    district_count = importer.import_district_data(district_csv)
    
    if city_count > 0 and district_count > 0:
        importer.verify_import()
        print(f"\n✅ Successfully imported {city_count + district_count} total records!")
    else:
        print("\n❌ Import failed - check logs above")
    
    importer.close()

if __name__ == "__main__":
    main()