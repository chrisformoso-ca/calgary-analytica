#!/usr/bin/env python3
"""
CREB District Data Extractor
Extracts district-level housing data from Calgary CREB PDF reports
"""

import re
import pandas as pd
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CREBDistrictExtractor:
    """Extracts district-level data from CREB PDF reports."""
    
    def __init__(self, pdf_directory: str):
        self.pdf_directory = Path(pdf_directory)
        
    def extract_from_pdf(self, pdf_path: Path) -> pd.DataFrame:
        """Extract district data from a single PDF."""
        logger.info(f"Extracting data from {pdf_path.name}")
        
        all_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract data from different property type pages
                property_pages = {
                    'Detached': [3, 4, 5],  # Pages with detached home district data
                    'Apartment': [6, 7, 8], # Pages with apartment district data
                    'Row': [9, 10],         # Pages with row/townhouse district data
                    'Semi_Detached': [11, 12]  # Pages with semi-detached district data
                }
                
                for property_type, pages in property_pages.items():
                    for page_num in pages:
                        if page_num <= len(pdf.pages):
                            page_data = self._extract_page_data(pdf.pages[page_num - 1], property_type, pdf_path.name)
                            if page_data:
                                all_data.extend(page_data)
                
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
        
        if all_data:
            df = pd.DataFrame(all_data)
            logger.info(f"Extracted {len(df)} records from {pdf_path.name}")
            return df
        else:
            logger.warning(f"No data extracted from {pdf_path.name}")
            return pd.DataFrame()
    
    def _extract_page_data(self, page, property_type: str, filename: str) -> List[Dict]:
        """Extract data from a single page."""
        text = page.extract_text()
        if not text:
            return []
        
        # Parse the page text for district data
        records = []
        lines = text.split('\n')
        
        # Look for district data patterns
        for line in lines:
            record = self._parse_district_line(line, property_type, filename)
            if record:
                records.append(record)
        
        return records
    
    def _parse_district_line(self, line: str, property_type: str, filename: str) -> Optional[Dict]:
        """Parse a line that contains district data."""
        
        # Extract date from filename
        match = re.match(r"(\d{2})_(\d{4})_Calgary", filename)
        if not match:
            return None
        
        month, year = int(match.group(1)), int(match.group(2))
        
        # District patterns - this would need to be customized based on actual PDF format
        # This is a placeholder implementation
        
        districts = ['City Centre', 'East', 'North', 'North East', 'North West', 
                    'South', 'South East', 'West']
        
        for district in districts:
            if district in line:
                # Extract numbers from the line
                numbers = re.findall(r'[\d,]+', line)
                if len(numbers) >= 6:  # Need at least sales, listings, inventory, price
                    try:
                        record = {
                            'property_type': property_type,
                            'district': district,
                            'new_sales': int(numbers[0].replace(',', '')),
                            'new_listings': int(numbers[1].replace(',', '')),
                            'inventory': int(numbers[2].replace(',', '')),
                            'benchmark_price': int(numbers[3].replace(',', '')),
                            'month': month,
                            'year': year,
                            'date': f"{year}-{month:02d}-01"
                        }
                        
                        # Calculate sales to listings ratio
                        if record['new_listings'] > 0:
                            ratio = (record['new_sales'] / record['new_listings']) * 100
                            record['sales_to_listings_ratio'] = f"{ratio:.2f}%"
                        
                        return record
                    except (ValueError, IndexError):
                        continue
        
        return None
    
    def process_all_pdfs(self) -> pd.DataFrame:
        """Process all PDFs in the directory."""
        all_data = []
        
        pdf_files = list(self.pdf_directory.glob("*_Calgary_Monthly_Stats_Package.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in sorted(pdf_files):
            df = self.extract_from_pdf(pdf_file)
            if not df.empty:
                all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Sort by date and property type
            combined_df = combined_df.sort_values(['date', 'property_type', 'district'])
            
            # Remove duplicates
            combined_df = combined_df.drop_duplicates(
                subset=['property_type', 'district', 'month', 'year'], 
                keep='last'
            )
            
            logger.info(f"Total records extracted: {len(combined_df)}")
            return combined_df
        else:
            logger.error("No data extracted from any PDFs")
            return pd.DataFrame()
    
    def save_data(self, df: pd.DataFrame, output_path: str) -> bool:
        """Save the extracted data to CSV."""
        try:
            df.to_csv(output_path, index=False)
            logger.info(f"Data saved to {output_path}")
            
            # Print summary
            print(f"\nExtraction Summary:")
            print(f"Total records: {len(df)}")
            print(f"Property types: {list(df['property_type'].unique())}")
            print(f"Districts: {list(df['district'].unique())}")
            print(f"Date range: {df['date'].min()} to {df['date'].max()}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False


def main():
    """Main function."""
    pdf_directory = "../../../data/raw_pdfs"
    output_path = "../../../data/extracted/district_data_extracted.csv"
    
    extractor = CREBDistrictExtractor(pdf_directory)
    
    # Process all PDFs
    df = extractor.process_all_pdfs()
    
    if not df.empty:
        success = extractor.save_data(df, output_path)
        if success:
            print("✅ District data extraction completed successfully!")
        else:
            print("❌ Failed to save extracted data")
    else:
        print("❌ No data extracted")


if __name__ == "__main__":
    main()