#!/usr/bin/env python3
"""
Combine CSV files from CREB extraction
Merges individual monthly extracts into a master dataset
"""

import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def combine_extracted_csvs():
    """Combine all extracted CSV files into master dataset."""
    
    extracted_dir = Path("../../../data/extracted")
    
    # Find all individual monthly extracts
    csv_files = list(extracted_dir.glob("*_Calgary_Monthly_Stats_Package_extracted.csv"))
    
    if not csv_files:
        logger.error("No extracted CSV files found")
        return False
    
    logger.info(f"Found {len(csv_files)} CSV files to combine")
    
    all_data = []
    
    for csv_file in sorted(csv_files):
        try:
            df = pd.read_csv(csv_file)
            
            # Extract date from filename
            import re
            match = re.match(r"(\d{2})_(\d{4})_Calgary", csv_file.name)
            if match:
                month, year = int(match.group(1)), int(match.group(2))
                df['month'] = month
                df['year'] = year
                df['date'] = f"{year}-{month:02d}-01"
            
            logger.info(f"Loaded {len(df)} records from {csv_file.name}")
            all_data.append(df)
        except Exception as e:
            logger.error(f"Error reading {csv_file.name}: {e}")
    
    if all_data:
        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by date and property type
        combined_df = combined_df.sort_values(['date', 'property_type', 'district'])
        
        # Remove duplicates
        combined_df = combined_df.drop_duplicates(
            subset=['property_type', 'district', 'month', 'year'], 
            keep='last'
        )
        
        # Save master dataset
        output_path = extracted_dir / "calgary_housing_master_dataset.csv"
        combined_df.to_csv(output_path, index=False)
        
        logger.info(f"Master dataset saved to {output_path}")
        print(f"\nCombined Dataset Summary:")
        print(f"Total records: {len(combined_df)}")
        print(f"Property types: {list(combined_df['property_type'].unique())}")
        print(f"Districts: {list(combined_df['district'].unique())}")
        print(f"Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
        
        return True
    else:
        logger.error("No data to combine")
        return False


if __name__ == "__main__":
    success = combine_extracted_csvs()
    if success:
        print("✅ CSV combination completed successfully!")
    else:
        print("❌ CSV combination failed")