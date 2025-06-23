#!/usr/bin/env python3
"""
Load May 2025 data into the database
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

# Add config to path
sys.path.append(str(Path(__file__).parent.parent / "config"))
from config_manager import ConfigManager

# Use ConfigManager for database path
config = ConfigManager()
db_path = config.get_database_path()
conn = sqlite3.connect(db_path)

# Read the May 2025 data
city_data = pd.read_csv("/home/chris/calgary-analytica/data/extracted/Calgary_CREB_Data.csv")
may_data = city_data[city_data['Date'] == '2025-05']

print(f"Found {len(may_data)} May 2025 records")
print(may_data)

# Prepare for database
may_data_db = may_data.copy()
may_data_db['source_pdf'] = '05_2025_Calgary_Monthly_Stats_Package.pdf'
may_data_db['extracted_date'] = '2025-06-17'
may_data_db['confidence_score'] = 1.0
may_data_db['validation_status'] = 'approved'

# Rename columns to match database
may_data_db = may_data_db.rename(columns={
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

# Insert into database
try:
    may_data_db.to_sql('housing_city_monthly', conn, if_exists='append', index=False)
    conn.commit()
    print(f"\n✅ Successfully loaded {len(may_data_db)} May 2025 records into database")
    
    # Verify
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM housing_city_monthly WHERE date = '2025-05'")
    count = cursor.fetchone()[0]
    print(f"Database now has {count} records for May 2025")
    
    cursor.execute("SELECT COUNT(*), MAX(date) FROM housing_city_monthly")
    total, latest = cursor.fetchone()
    print(f"Total city records: {total}, Latest: {latest}")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

conn.close()