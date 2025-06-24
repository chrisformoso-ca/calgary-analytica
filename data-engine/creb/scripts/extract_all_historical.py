#!/usr/bin/env python3
"""
Extract ALL historical CREB data from ALL available PDFs.
This script processes every PDF and combines all unique data points.
Extracts all 9 required fields for city-wide data.
"""

import pandas as pd
import pdfplumber
from pathlib import Path
import logging
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoricalCREBExtractor:
    def __init__(self, pdf_directory: str):
        self.pdf_directory = Path(pdf_directory)
        self.property_types = {
            'Total': 11,
            'Detached': 13,
            'Semi_Detached': 15,
            'Apartment': 17,
            'Row': 19
        }
        
    def extract_from_all_pdfs(self):
        """Extract data from ALL PDFs and combine unique records."""
        all_city_data = []
        all_district_data = []
        
        # Find all PDF files
        pdf_files = list(self.pdf_directory.glob("*.pdf"))
        pdf_files.sort()  # Process in order
        
        logger.info(f"Found {len(pdf_files)} PDFs to process")
        
        for pdf_path in pdf_files:
            logger.info(f"\nProcessing {pdf_path.name}...")
            
            # Extract city data
            city_data = self.extract_city_data(pdf_path)
            if city_data:
                all_city_data.extend(city_data)
                logger.info(f"  Extracted {len(city_data)} city records")
            
            # Extract district data
            district_data = self.extract_district_data(pdf_path)
            if district_data:
                all_district_data.extend(district_data)
                logger.info(f"  Extracted {len(district_data)} district records")
        
        # Convert to DataFrames and remove duplicates
        if all_city_data:
            city_df = pd.DataFrame(all_city_data)
            city_df = city_df.drop_duplicates(subset=['Date', 'Property_Type'], keep='last')
            city_df = city_df.sort_values(['Date', 'Property_Type'])
            logger.info(f"\nTotal unique city records: {len(city_df)}")
            logger.info(f"Date range: {city_df['Date'].min()} to {city_df['Date'].max()}")
            
            # Save city data
            output_path = Path("/home/chris/calgary-analytica/data-engine/validation/pending/creb_city_all_historical.csv")
            city_df.to_csv(output_path, index=False)
            logger.info(f"Saved to {output_path}")
        
        if all_district_data:
            district_df = pd.DataFrame(all_district_data)
            district_df = district_df.drop_duplicates(
                subset=['date', 'property_type', 'district'], keep='last'
            )
            district_df = district_df.sort_values(['date', 'property_type', 'district'])
            logger.info(f"\nTotal unique district records: {len(district_df)}")
            logger.info(f"Date range: {district_df['date'].min()} to {district_df['date'].max()}")
            
            # Save district data
            output_path = Path("/home/chris/calgary-analytica/data-engine/validation/pending/creb_district_all_historical.csv")
            district_df.to_csv(output_path, index=False)
            logger.info(f"Saved to {output_path}")
    
    def extract_city_data(self, pdf_path):
        """Extract city-wide data from a single PDF."""
        all_records = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for property_type, page_num in self.property_types.items():
                    if len(pdf.pages) >= page_num:
                        page = pdf.pages[page_num - 1]
                        text = page.extract_text()
                        
                        if text:
                            # Parse the page for this property type
                            property_records = self.parse_city_page(text, property_type)
                            all_records.extend(property_records)
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")
        
        return all_records
    
    def parse_city_page(self, text, property_type):
        """Parse a city data page to extract all metrics."""
        records = []
        lines = text.split('\n')
        
        current_year = None
        metrics_by_year = {}  # Store all metrics for each year
        
        for i, line in enumerate(lines):
            # Look for year headers
            year_match = re.match(r'^(20\d{2})\s+', line)
            if year_match:
                current_year = int(year_match.group(1))
                if current_year not in metrics_by_year:
                    metrics_by_year[current_year] = {}
                continue
            
            if current_year:
                # Extract different metrics
                metric_data = self.extract_metric_from_line(line)
                if metric_data:
                    metric_name, values = metric_data
                    metrics_by_year[current_year][metric_name] = values
        
        # Build complete records from collected metrics
        for year, metrics in metrics_by_year.items():
            # Only create records if we have at least Sales data
            if 'Sales' in metrics:
                months_data = len(metrics.get('Sales', []))
                for month_idx in range(months_data):
                    month = month_idx + 1
                    date_str = f"{year}-{month:02d}"
                    
                    record = {
                        'Date': date_str,
                        'Property_Type': property_type
                    }
                    
                    # Add all available metrics
                    for metric_name, values in metrics.items():
                        if month_idx < len(values):
                            record[metric_name] = values[month_idx]
                    
                    # Only add record if it has meaningful data
                    if len(record) > 2:  # More than just Date and Property_Type
                        records.append(record)
        
        return records
    
    def extract_metric_from_line(self, line):
        """Extract metric name and values from a line."""
        # Define patterns for each metric
        metrics_patterns = [
            ('Sales', r'Sales\s+(.+)'),
            ('New_Listings', r'New Listings\s+(.+)'),
            ('Inventory', r'Inventory\s+(.+)'),
            ('Days_on_Market', r'Days on Market\s+(.+)'),
            ('Benchmark_Price', r'(?:Benchmark Price|Benchmark HPI)\s+(.+)'),
            ('Median_Price', r'Median Price\s+(.+)'),
            ('Average_Price', r'Average Price\s+(.+)')
        ]
        
        for metric_name, pattern in metrics_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Extract numbers from the matched portion
                numbers_text = match.group(1)
                numbers = self.extract_numbers(numbers_text, metric_name)
                if numbers:
                    return metric_name, numbers
        
        return None
    
    def extract_numbers(self, text, metric_name):
        """Extract numbers from text, handling various formats."""
        numbers = []
        
        # Clean up the text
        text = text.strip()
        
        if 'Price' in metric_name:
            # Handle price formats like "567,890" or "5 67,890"
            # First, try to find complete prices
            price_patterns = [
                r'\b(\d{3},\d{3})\b',  # Standard format: 567,890
                r'\b(\d{1,3})\s+(\d{2,3},\d{3})\b',  # Split format: 5 67,890
                r'\b(\d{6,})\b'  # No comma format: 567890
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    if isinstance(matches[0], tuple):
                        # Handle split format
                        for match in matches:
                            if len(match) == 2:
                                # Combine split numbers
                                combined = match[0] + match[1].replace(',', '')
                                numbers.append(int(combined))
                    else:
                        # Handle standard format
                        for match in matches:
                            numbers.append(int(match.replace(',', '')))
                    
                    if numbers:
                        break
            
            # If no prices found, try general number extraction
            if not numbers:
                all_numbers = re.findall(r'[\d,]+', text)
                for num_str in all_numbers:
                    try:
                        num = int(num_str.replace(',', ''))
                        # Validate price range
                        if num > 100000:  # Prices should be > $100k
                            numbers.append(num)
                        elif 200 <= num <= 800:  # Might be abbreviated (in thousands)
                            numbers.append(num * 1000)
                    except:
                        pass
        else:
            # For non-price metrics, simpler extraction
            all_numbers = re.findall(r'[\d,]+', text)
            for num_str in all_numbers:
                try:
                    num = int(num_str.replace(',', ''))
                    numbers.append(num)
                except:
                    pass
        
        return numbers[:12]  # Maximum 12 months
    
    def extract_district_data(self, pdf_path):
        """Extract district data from page 7."""
        records = []
        
        # Parse PDF filename for month/year
        match = re.match(r"(\d{2})_(\d{4})_Calgary", pdf_path.name)
        if not match:
            return records
        
        month, year = int(match.group(1)), int(match.group(2))
        date_str = f"{year}-{month:02d}-01"
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) >= 7:
                    page = pdf.pages[6]  # Page 7 (0-indexed)
                    text = page.extract_text()
                    
                    if text:
                        records = self.parse_district_page(text, month, year, date_str)
        except Exception as e:
            logger.error(f"Error extracting district data from {pdf_path.name}: {e}")
        
        return records
    
    def parse_district_page(self, text, month, year, date_str):
        """Parse district data from page 7."""
        records = []
        lines = text.split('\n')
        
        # Define districts
        districts = ['Centre', 'East', 'North', 'North East', 'North West', 'South', 'South East', 'West']
        
        # Property types on district page (only 4, not Total)
        property_types = ['Detached', 'Semi-Detached', 'Row', 'Apartment']
        
        current_property_type = None
        
        for line in lines:
            # Check for property type headers
            for prop_type in property_types:
                if prop_type in line and not any(d in line for d in districts):
                    current_property_type = prop_type
                    break
            
            # Check for district data
            if current_property_type:
                for district in districts:
                    if district in line:
                        # Extract numbers from the line
                        numbers = re.findall(r'[\d,]+', line.replace(district, ''))
                        
                        if len(numbers) >= 6:  # Need at least 6 numbers
                            try:
                                record = {
                                    'property_type': current_property_type,
                                    'district': district,
                                    'new_sales': int(numbers[0].replace(',', '')),
                                    'new_listings': int(numbers[1].replace(',', '')),
                                    'inventory': int(numbers[2].replace(',', '')),
                                    'benchmark_price': int(numbers[4].replace(',', '')),
                                    'month': month,
                                    'year': year,
                                    'date': date_str
                                }
                                records.append(record)
                            except:
                                pass
        
        return records


if __name__ == "__main__":
    extractor = HistoricalCREBExtractor("/home/chris/calgary-analytica/data-engine/creb/raw")
    extractor.extract_from_all_pdfs()