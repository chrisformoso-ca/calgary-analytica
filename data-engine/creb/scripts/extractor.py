#!/usr/bin/env python3
"""
Calgary CREB Data Updater (Unified)
Updates both city-wide and district-level datasets from new PDF reports
- City-wide data (pages 11,13,15,17,19) -> validation/pending/creb_city_monthly.csv
- District data (page 7) -> validation/pending/creb_district_monthly.csv
"""

import pandas as pd
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import re
from datetime import datetime, timedelta
import argparse
import sys
import os
import json

# Add parent directory to path to import from config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config_manager import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalgaryDataUpdater:
    """Updates both city-wide and district-level Calgary CREB data from PDF reports."""
    
    def __init__(self, csv_path: str = None, pdf_directory: str = None, district_csv_path: str = None):
        # Get config for paths
        config = get_config()
        
        # Use config paths with fallbacks to arguments
        if csv_path:
            self.csv_path = Path(csv_path)
        else:
            # Load from archive as base
            creb_base_dir = config.get_project_root() / 'data-engine' / 'creb'
            self.csv_path = creb_base_dir / 'archive' / 'creb_property_type.csv'
            
        if pdf_directory:
            self.pdf_directory = Path(pdf_directory)
        else:
            self.pdf_directory = config.get_creb_pdf_dir()
            
        if district_csv_path:
            self.district_csv_path = Path(district_csv_path)
        else:
            # Load from archive as base
            creb_base_dir = config.get_project_root() / 'data-engine' / 'creb'
            self.district_csv_path = creb_base_dir / 'archive' / 'creb_district.csv'
        
        # Output paths for validation/pending
        self.output_city_path = config.get_pending_review_dir() / 'creb_city_all_historical.csv'
        self.output_district_path = config.get_pending_review_dir() / 'creb_district_all_historical.csv'
        
        # Property type mappings (page numbers in PDF for city-wide data)
        self.property_types = {
            'Total': 11,
            'Detached': 13,
            'Semi_Detached': 15,
            'Apartment': 17,
            'Row': 19
        }
        
    def load_existing_data(self) -> pd.DataFrame:
        """Load the existing Calgary CREB data."""
        if self.csv_path.exists():
            df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded existing data: {len(df)} records")
            
            # Show current data range
            if not df.empty:
                logger.info(f"Current data range: {df['Date'].min()} to {df['Date'].max()}")
                
                # Show property type distribution
                type_counts = df['Property_Type'].value_counts()
                logger.info(f"Property types: {dict(type_counts)}")
            
            return df
        else:
            logger.info("No existing CSV found, will create new one")
            return pd.DataFrame()
    
    def find_latest_pdf(self) -> Optional[Path]:
        """Find the most recent Calgary PDF report."""
        latest_pdf = None
        latest_date = None
        
        for pdf_file in self.pdf_directory.glob("*_Calgary_Monthly_Stats_Package.pdf"):
            # Extract date from filename
            match = re.match(r"(\d{2})_(\d{4})_Calgary", pdf_file.name)
            if match:
                month, year = int(match.group(1)), int(match.group(2))
                pdf_date = datetime(year, month, 1)
                
                if latest_date is None or pdf_date > latest_date:
                    latest_date = pdf_date
                    latest_pdf = pdf_file
        
        if latest_pdf:
            logger.info(f"Latest PDF found: {latest_pdf.name} ({latest_date.strftime('%Y-%m')})")
        else:
            logger.warning("No PDF reports found")
        
        return latest_pdf
    
    def get_missing_months(self, existing_df: pd.DataFrame, latest_pdf_date: datetime) -> List[str]:
        """Identify which months are missing from existing data."""
        if existing_df.empty:
            # If no existing data, we need all months up to the latest PDF
            missing_months = []
            current_date = datetime(2023, 1, 1)  # Start from January 2023
            while current_date <= latest_pdf_date:
                missing_months.append(current_date.strftime('%Y-%m'))
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            return missing_months
        
        # Find the latest date in existing data
        existing_dates = pd.to_datetime(existing_df['Date']).dt.to_period('M')
        latest_existing = existing_dates.max()
        
        # Generate list of missing months
        missing_months = []
        current_period = latest_existing
        latest_period = pd.Period(latest_pdf_date.strftime('%Y-%m'), 'M')
        
        while current_period < latest_period:
            current_period += 1
            missing_months.append(str(current_period))
        
        logger.info(f"Missing months to add: {missing_months}")
        return missing_months
    
    def extract_page_data(self, pdf_path: Path, page_num: int) -> Optional[str]:
        """Extract text from a specific page of the PDF."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) >= page_num:
                    page = pdf.pages[page_num - 1]  # 0-indexed
                    text = page.extract_text()
                    return text
                else:
                    logger.warning(f"PDF has only {len(pdf.pages)} pages, need page {page_num}")
                    return None
        except Exception as e:
            logger.error(f"Error extracting page {page_num} from {pdf_path.name}: {e}")
            return None
    
    def parse_property_type_data(self, text: str, property_type: str) -> List[Dict]:
        """Parse data for a specific property type from page text."""
        data = []
        lines = text.split('\n')
        
        # Find year sections and parse them
        current_year = None
        current_months = []
        metrics_data = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for year header lines
            year_match = re.match(r'^(20\d{2})\s+(.+)', line)
            if year_match:
                # Process previous year's data if exists
                if current_year and current_months and metrics_data:
                    year_records = self._build_monthly_records_for_type(
                        current_year, current_months, metrics_data, property_type
                    )
                    data.extend(year_records)
                
                # Start new year
                current_year = int(year_match.group(1))
                dates_part = year_match.group(2)
                
                # Extract months from dates
                dates = re.findall(r'(\d{2})/\d{2}/\d{2}', dates_part)
                current_months = [int(d) for d in dates if 1 <= int(d) <= 12]
                metrics_data = {}
                
                logger.debug(f"Found year {current_year} with {len(current_months)} months for {property_type}")
                continue
            
            # Parse metric lines
            if current_year and current_months:
                metric_name, values = self._parse_metric_line(line, len(current_months))
                if metric_name and values:
                    metrics_data[metric_name] = values
        
        # Process final year
        if current_year and current_months and metrics_data:
            year_records = self._build_monthly_records_for_type(
                current_year, current_months, metrics_data, property_type
            )
            data.extend(year_records)
        
        logger.debug(f"Extracted {len(data)} records for {property_type}")
        return data
    
    def _parse_metric_line(self, line: str, expected_count: int) -> Tuple[Optional[str], Optional[List[int]]]:
        """Parse a metric line to extract values."""
        
        # Map line patterns to field names (matching CSV structure)
        if line.startswith('Sales '):
            metric_name = 'Sales'
            data_part = line[6:].strip()
        elif line.startswith('New Listings '):
            metric_name = 'New_Listings'
            data_part = line[13:].strip()
        elif line.startswith('Inventory '):
            metric_name = 'Inventory'
            data_part = line[10:].strip()
        elif line.startswith('Days on Market '):
            metric_name = 'Days_on_Market'
            data_part = line[15:].strip()
        elif line.startswith('Benchmark Price '):
            metric_name = 'Benchmark_Price'
            data_part = line[16:].strip()
        elif line.startswith('Median Price '):
            metric_name = 'Median_Price'
            data_part = line[13:].strip()
        elif line.startswith('Average Price '):
            metric_name = 'Average_Price'
            data_part = line[14:].strip()
        else:
            return None, None
        
        # Extract numbers
        numbers = self._extract_numbers_from_line(data_part, expected_count, metric_name)
        
        return metric_name, numbers
    
    def _extract_numbers_from_line(self, text: str, expected_count: int, metric_name: str) -> List[int]:
        """Extract numbers from a line, handling PDF formatting issues."""
        
        # Handle different parsing strategies based on format quality
        numbers = []
        
        # Strategy 1: Split by multiple spaces (works for clean format)
        segments = re.split(r'\s{2,}', text.strip())
        
        for segment in segments:
            number = self._parse_single_number(segment, metric_name)
            if number is not None:
                numbers.append(number)
        
        # Strategy 2: If we don't have enough numbers, try alternative parsing
        if len(numbers) < expected_count * 0.5:
            # Handle messy format like "5 16,300" -> 516300
            numbers = []
            
            # Find all number patterns and fix them
            if 'Price' in metric_name:
                # Special handling for prices with spaces
                price_patterns = re.findall(r'(\d+)\s+(\d+,\d+)', text)
                for pattern in price_patterns:
                    combined = pattern[0] + pattern[1].replace(',', '')
                    numbers.append(int(combined))
                
                # Also look for normal prices
                normal_prices = re.findall(r'\b(\d{3},\d{3})\b', text)
                for price in normal_prices:
                    numbers.append(int(price.replace(',', '')))
            else:
                # For non-price fields, simpler parsing
                all_numbers = re.findall(r'\d+', text.replace(',', ''))
                numbers = [int(num) for num in all_numbers if num]
        
        return numbers[:expected_count]
    
    def _parse_single_number(self, segment: str, metric_name: str) -> Optional[int]:
        """Parse a single number segment."""
        
        # Clean the segment
        clean = re.sub(r'[^\d,]', '', segment.strip())
        
        if not clean:
            return None
        
        try:
            # Remove commas and convert
            number = int(clean.replace(',', ''))
            
            # Basic validation based on metric type
            if 'Price' in metric_name and number < 100000:
                # Prices should be reasonable - might need scaling
                if 400 <= number <= 700:
                    return number * 1000  # 567 -> 567000
            
            return number
            
        except ValueError:
            return None
    
    def _build_monthly_records_for_type(self, year: int, months: List[int], 
                                       metrics_data: Dict, property_type: str) -> List[Dict]:
        """Build monthly records for a specific property type."""
        
        records = []
        
        for i, month in enumerate(months):
            # Create base record
            record = {
                'Date': f"{year}-{month:02d}",
                'Property_Type': property_type
            }
            
            # Add metrics (using same names as existing CSV)
            field_mapping = {
                'Sales': 'Sales',
                'New_Listings': 'New_Listings', 
                'Inventory': 'Inventory',
                'Days_on_Market': 'Days_on_Market',
                'Benchmark_Price': 'Benchmark_Price',
                'Median_Price': 'Median_Price',
                'Average_Price': 'Average_Price'
            }
            
            for metric_name, values in metrics_data.items():
                if i < len(values) and metric_name in field_mapping:
                    record[field_mapping[metric_name]] = values[i]
            
            # Only include complete records
            required_fields = ['Sales', 'New_Listings', 'Benchmark_Price']
            if all(field in record for field in required_fields):
                records.append(record)
        
        return records
    
    def extract_new_data_from_pdf(self, pdf_path: Path, target_months: List[str]) -> pd.DataFrame:
        """Extract data for all property types from the PDF."""
        
        all_new_data = []
        
        for property_type, page_num in self.property_types.items():
            logger.info(f"Extracting {property_type} data from page {page_num}...")
            
            page_text = self.extract_page_data(pdf_path, page_num)
            if page_text:
                property_data = self.parse_property_type_data(page_text, property_type)
                
                # Filter for only the target months we need
                filtered_data = []
                for record in property_data:
                    if record['Date'] in target_months:
                        filtered_data.append(record)
                
                logger.info(f"Found {len(filtered_data)} new records for {property_type}")
                all_new_data.extend(filtered_data)
            else:
                logger.warning(f"Could not extract page {page_num} for {property_type}")
        
        if all_new_data:
            new_df = pd.DataFrame(all_new_data)
            logger.info(f"Total new records extracted: {len(new_df)}")
            return new_df
        else:
            logger.warning("No new data extracted")
            return pd.DataFrame()
    
    def update_csv(self, existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
        """Combine existing and new data."""
        
        if existing_df.empty:
            combined_df = new_df.copy()
        else:
            # Append new data
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Sort by Date and Property_Type
        combined_df = combined_df.sort_values(['Date', 'Property_Type'])
        
        # Remove any duplicates (keeping the latest)
        combined_df = combined_df.drop_duplicates(subset=['Date', 'Property_Type'], keep='last')
        
        logger.info(f"Combined dataset: {len(combined_df)} records")
        return combined_df
    
    def load_existing_district_data(self) -> pd.DataFrame:
        """Load the existing district-level data."""
        if self.district_csv_path.exists():
            df = pd.read_csv(self.district_csv_path)
            logger.info(f"Loaded existing district data: {len(df)} records")
            
            if not df.empty:
                latest_date = df['date'].max()
                logger.info(f"District data range: {df['date'].min()} to {latest_date}")
                property_types = df['property_type'].unique()
                districts = df['district'].unique()
                logger.info(f"Property types: {len(property_types)}, Districts: {len(districts)}")
            
            return df
        else:
            logger.info("No existing district CSV found, will create new one")
            return pd.DataFrame()
    
    def extract_district_data_from_pdf(self, pdf_path: Path, target_month: str) -> pd.DataFrame:
        """Extract district-level data from PDF (page 7)."""
        logger.info(f"Extracting district data from {pdf_path.name} for {target_month}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Page 7 contains district data
                if len(pdf.pages) >= 7:
                    page = pdf.pages[6]  # 0-indexed, so page 7 is index 6
                    text = page.extract_text()
                    
                    if text:
                        records = self._parse_district_page(text, pdf_path.name, target_month)
                        if records:
                            df = pd.DataFrame(records)
                            logger.info(f"Extracted {len(df)} district records for {target_month}")
                            return df
                
            logger.warning(f"No district data found in {pdf_path.name}")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error extracting district data from {pdf_path.name}: {e}")
            return pd.DataFrame()
    
    def _parse_district_page(self, text: str, filename: str, target_month: str) -> List[Dict]:
        """Parse district data from page 7 text."""
        records = []
        lines = text.split('\n')
        
        # Extract date components
        match = re.match(r"(\d{2})_(\d{4})_Calgary", filename)
        if not match:
            logger.error(f"Could not parse date from {filename}")
            return records
        
        month, year = int(match.group(1)), int(match.group(2))
        date_str = f"{year}-{month:02d}-01"
        
        # District parsing patterns - looking for typical district data structure
        current_property_type = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect property type headers
            if any(ptype.lower() in line.lower() for ptype in ['detached', 'apartment', 'row', 'semi']):
                if 'detached' in line.lower() and 'semi' not in line.lower():
                    current_property_type = 'Detached'
                elif 'apartment' in line.lower():
                    current_property_type = 'Apartment'
                elif 'row' in line.lower() or 'townhouse' in line.lower():
                    current_property_type = 'Row'
                elif 'semi' in line.lower():
                    current_property_type = 'Semi-detached'
                continue
            
            # Parse district data lines
            if current_property_type:
                record = self._parse_district_line(line, current_property_type, month, year, date_str)
                if record:
                    records.append(record)
        
        return records
    
    def _parse_district_line(self, line: str, property_type: str, month: int, year: int, date_str: str) -> Optional[Dict]:
        """Parse a single district data line with enhanced robustness."""
        
        # Common Calgary districts to look for (ordered by specificity)
        districts = ['City Centre', 'North East', 'North West', 'South East', 'South West', 'North', 'South', 'West', 'East']
        
        # Find district in line and remove it
        district = None
        remaining_line = line
        for d in districts:
            if line.startswith(d):
                district = d
                remaining_line = line[len(d):].strip()
                break
        
        if not district:
            return None
        
        logger.debug(f"Parsing {district}: {remaining_line}")
        
        # Enhanced parsing for May 2025 format
        # Expected format: sales listings ratio% inventory months_supply $price yoy% mom%
        # Example: "145 251 57.77% 353 2.43 $993,500 2.81% 0.40%"
        
        # Try multiple parsing strategies
        record = self._parse_strategy_v2(remaining_line, property_type, district, month, year, date_str)
        if record:
            return record
            
        # Fallback to original strategy for backward compatibility
        record = self._parse_strategy_v1(remaining_line, property_type, district, month, year, date_str)
        if record:
            return record
            
        logger.warning(f"Failed to parse district line: {district} - {remaining_line}")
        return None
    
    def _parse_strategy_v2(self, line: str, property_type: str, district: str, month: int, year: int, date_str: str) -> Optional[Dict]:
        """Enhanced parsing strategy for May 2025+ format."""
        
        # Regex pattern for May 2025 format
        # Captures: sales listings ratio% inventory months_supply $price yoy% mom%
        pattern = r'(\d+)\s+(\d+)\s+([\d.]+%)\s+(\d+)\s+([\d.]+)\s+\$([0-9,]+)\s+([-]?[\d.]+%)\s+([-]?[\d.]+%)'
        match = re.match(pattern, line.strip())
        
        if match:
            try:
                sales = int(match.group(1))
                listings = int(match.group(2))
                ratio = match.group(3)
                inventory = int(match.group(4))
                months_supply = float(match.group(5))
                price = int(match.group(6).replace(',', ''))
                yoy_change = match.group(7)
                mom_change = match.group(8)
                
                logger.debug(f"✅ Strategy v2 success: {district} - {sales} sales, ${price:,}")
                
                return {
                    'property_type': property_type,
                    'district': district,
                    'new_sales': sales,
                    'new_listings': listings,
                    'sales_to_listings_ratio': ratio,
                    'inventory': inventory,
                    'months_supply': months_supply,
                    'benchmark_price': price,
                    'yoy_price_change': yoy_change,
                    'mom_price_change': mom_change,
                    'month': month,
                    'year': year,
                    'date': date_str
                }
                
            except (ValueError, IndexError) as e:
                logger.debug(f"Strategy v2 parse error: {e}")
        
        return None
    
    def _parse_strategy_v1(self, line: str, property_type: str, district: str, month: int, year: int, date_str: str) -> Optional[Dict]:
        """Original parsing strategy for backward compatibility."""
        
        # Extract numbers from the line using original regex
        numbers = re.findall(r'[\d,]+\.?\d*%?', line)
        
        if len(numbers) >= 8:  # Need at least 8 data points for complete record
            try:
                # Parse the extracted numbers
                new_sales = int(numbers[0].replace(',', '').replace('%', ''))
                new_listings = int(numbers[1].replace(',', '').replace('%', ''))
                
                # Calculate sales to listings ratio
                if new_listings > 0:
                    ratio = f"{(new_sales / new_listings * 100):.2f}%"
                else:
                    ratio = "0.00%"
                
                # Skip the ratio field in numbers[2] and use actual data
                inventory = int(numbers[3].replace(',', '').replace('%', ''))
                months_supply = float(numbers[4].replace(',', '').replace('%', ''))
                benchmark_price = int(numbers[5].replace(',', '').replace('%', ''))
                yoy_change = numbers[6] if '%' in numbers[6] else f"{numbers[6]}%"
                mom_change = numbers[7] if '%' in numbers[7] else f"{numbers[7]}%"
                
                logger.debug(f"✅ Strategy v1 success: {district} - {new_sales} sales, ${benchmark_price:,}")
                
                return {
                    'property_type': property_type,
                    'district': district,
                    'new_sales': new_sales,
                    'new_listings': new_listings,
                    'sales_to_listings_ratio': ratio,
                    'inventory': inventory,
                    'months_supply': months_supply,
                    'benchmark_price': benchmark_price,
                    'yoy_price_change': yoy_change,
                    'mom_price_change': mom_change,
                    'month': month,
                    'year': year,
                    'date': date_str
                }
                
            except (ValueError, IndexError) as e:
                logger.debug(f"Strategy v1 parse error: {e}")
        
        return None
    
    def update_district_data(self, existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
        """Update district dataset with new data."""
        if existing_df.empty:
            return new_df
        
        if new_df.empty:
            return existing_df
        
        # Combine dataframes
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Remove duplicates (keep latest)
        combined_df = combined_df.drop_duplicates(
            subset=['property_type', 'district', 'month', 'year'], 
            keep='last'
        )
        
        # Sort by date and district
        combined_df = combined_df.sort_values(['date', 'property_type', 'district'])
        
        logger.info(f"Updated district dataset: {len(combined_df)} total records")
        return combined_df
    
    def create_validation_report(self, df: pd.DataFrame, output_path: Path, data_type: str) -> None:
        """Create a JSON validation report for the extracted data."""
        try:
            # Calculate summary statistics
            validation_report = {
                "source": f"creb_{data_type}_data",
                "extraction_date": datetime.now().isoformat(),
                "records_extracted": len(df),
                "date_range": f"{df['date'].min() if 'date' in df else df['Date'].min()} to {df['date'].max() if 'date' in df else df['Date'].max()}",
                "confidence_metrics": {},
                "property_types": {},
                "sample_records": []
            }
            
            # Get confidence score summary if available
            if 'confidence_score' in df.columns:
                validation_report["confidence_metrics"] = {
                    "mean": float(df['confidence_score'].mean()),
                    "min": float(df['confidence_score'].min()),
                    "max": float(df['confidence_score'].max()),
                    "low_confidence_count": int((df['confidence_score'] < 0.9).sum())
                }
            
            # Property type breakdown
            prop_col = 'property_type' if 'property_type' in df.columns else 'Property_Type'
            for prop_type in df[prop_col].unique():
                prop_data = df[df[prop_col] == prop_type]
                validation_report["property_types"][prop_type] = {
                    "count": len(prop_data),
                    "date_range": f"{prop_data['date'].min() if 'date' in df else prop_data['Date'].min()} to {prop_data['date'].max() if 'date' in df else prop_data['Date'].max()}"
                }
            
            # Sample records from latest month
            latest_date = df['date'].max() if 'date' in df else df['Date'].max()
            latest_data = df[df['date' if 'date' in df else 'Date'] == latest_date]
            
            for _, row in latest_data.head(5).iterrows():
                if data_type == "city":
                    sample = {
                        "date": row.get('Date', row.get('date', '')),
                        "property_type": row.get('Property_Type', row.get('property_type', '')),
                        "sales": int(row.get('Sales', row.get('sales', 0))),
                        "benchmark_price": float(row.get('Benchmark_Price', row.get('benchmark_price', 0)))
                    }
                else:  # district
                    sample = {
                        "date": row.get('date', ''),
                        "district": row.get('district', ''),
                        "property_type": row.get('property_type', ''),
                        "new_sales": int(row.get('new_sales', 0)),
                        "benchmark_price": float(row.get('benchmark_price', 0))
                    }
                validation_report["sample_records"].append(sample)
            
            # Save validation report
            report_path = output_path.with_suffix('.json')
            with open(report_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not create validation report: {e}")
    
    def save_district_data(self, df: pd.DataFrame) -> bool:
        """Save updated district data to validation/pending."""
        try:
            df.to_csv(self.output_district_path, index=False)
            logger.info(f"District data saved to {self.output_district_path}")
            
            # Create validation report
            self.create_validation_report(df, self.output_district_path, "district")
            
            return True
        except Exception as e:
            logger.error(f"Error saving district data: {e}")
            return False
    
    def save_updated_data(self, df: pd.DataFrame) -> bool:
        """Save the updated data to validation/pending."""
        try:
            # Save to validation/pending
            df.to_csv(self.output_city_path, index=False)
            logger.info(f"Updated data saved to {self.output_city_path}")
            
            # Create validation report
            self.create_validation_report(df, self.output_city_path, "city")
            
            # Show summary
            print(f"\nUpdate Summary:")
            print(f"Total records: {len(df)}")
            print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
            
            type_counts = df['Property_Type'].value_counts()
            print(f"Records per property type:")
            for prop_type, count in type_counts.items():
                print(f"  {prop_type}: {count}")
            
            # Show latest data
            print(f"\nLatest month data:")
            latest_month = df['Date'].max()
            latest_data = df[df['Date'] == latest_month]
            print(latest_data[['Date', 'Property_Type', 'Sales', 'Benchmark_Price']].to_string(index=False))
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving updated data: {e}")
            return False
    
    def run_update(self) -> bool:
        """Run the complete update process for both city-wide and district data."""
        
        logger.info("🏠 Starting Calgary CREB data update (unified)")
        
        # Load existing data
        existing_df = self.load_existing_data()
        existing_district_df = self.load_existing_district_data()
        
        # Find latest PDF
        latest_pdf = self.find_latest_pdf()
        if not latest_pdf:
            logger.error("No PDF found to process")
            return False
        
        # Get PDF date
        match = re.match(r"(\d{2})_(\d{4})_Calgary", latest_pdf.name)
        if not match:
            logger.error(f"Could not parse date from {latest_pdf.name}")
            return False
        
        month, year = int(match.group(1)), int(match.group(2))
        pdf_date = datetime(year, month, 1)
        target_month = f"{year}-{month:02d}"
        
        # Find missing months for city-wide data
        missing_months = self.get_missing_months(existing_df, pdf_date)
        
        city_success = True
        district_success = True
        new_df = pd.DataFrame()  # Track new city data
        new_district_df = pd.DataFrame()  # Track new district data
        
        # Process city-wide data (pages 11,13,15,17,19)
        if missing_months:
            logger.info(f"📊 Processing city-wide data for {len(missing_months)} missing months")
            new_df = self.extract_new_data_from_pdf(latest_pdf, missing_months)
            
            if not new_df.empty:
                updated_df = self.update_csv(existing_df, new_df)
                city_success = self.save_updated_data(updated_df)
            else:
                logger.warning("No city-wide data extracted from PDF")
                city_success = False
        else:
            logger.info("✅ City-wide data is up to date")
        
        # Process district data (page 7)
        logger.info(f"🏘️  Processing district data for {target_month}")
        
        # Check if district data for this month already exists
        if not existing_district_df.empty:
            existing_month_data = existing_district_df[
                (existing_district_df['month'] == month) & 
                (existing_district_df['year'] == year)
            ]
            if not existing_month_data.empty:
                logger.info(f"District data for {target_month} already exists, skipping...")
                district_success = True
            else:
                # Extract new district data
                new_district_df = self.extract_district_data_from_pdf(latest_pdf, target_month)
                if not new_district_df.empty:
                    updated_district_df = self.update_district_data(existing_district_df, new_district_df)
                    district_success = self.save_district_data(updated_district_df)
                else:
                    logger.warning("No district data extracted from PDF")
                    district_success = False
        else:
            # No existing district data - extract new
            new_district_df = self.extract_district_data_from_pdf(latest_pdf, target_month)
            if not new_district_df.empty:
                district_success = self.save_district_data(new_district_df)
            else:
                logger.warning("No district data extracted from PDF")
                district_success = False
        
        # Summary
        if city_success and district_success:
            logger.info("✅ Both city-wide and district data updated successfully")
            
            # Print extraction summary
            if not new_df.empty or not new_district_df.empty:
                print("\n" + "="*70)
                print("📊 EXTRACTION SUMMARY")
                print("="*70)
                print(f"\n📁 Source PDF: file://{latest_pdf.absolute()}")
                print(f"📅 Month extracted: {target_month}")
                
                if not new_df.empty:
                    print("\n🏙️  CITY DATA (5 property types):")
                    print("-" * 50)
                    for _, row in new_df.iterrows():
                        print(f"  {row['Property_Type']:14} - Sales: {row['Sales']:4d}, "
                              f"New Listings: {row['New_Listings']:4d}, "
                              f"Benchmark: ${row['Benchmark_Price']:,}")
                
                if not new_district_df.empty:
                    print("\n🏘️  DISTRICT DATA (32 records - 8 districts × 4 types):")
                    print("-" * 50)
                    district_summary = new_district_df.groupby('property_type').agg({
                        'new_sales': 'sum',
                        'benchmark_price': 'mean'
                    }).round(0)
                    
                    for prop_type, data in district_summary.iterrows():
                        print(f"  {prop_type:14} - Total Sales: {int(data['new_sales']):4d}, "
                              f"Avg Benchmark: ${int(data['benchmark_price']):,}")
                
                print("\n" + "="*70)
                print(f"✅ Data successfully added to historical records")
                print(f"📍 Review files in: {self.output_city_path.parent}")
                print("="*70 + "\n")
            
            return True
        elif city_success:
            logger.warning("⚠️  City-wide data updated, but district data failed")
            return True  # Partial success
        elif district_success:
            logger.warning("⚠️  District data updated, but city-wide data failed")
            return True  # Partial success
        else:
            logger.error("❌ Both updates failed")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Update Calgary CREB data from latest PDF reports (unified updater)')
    parser.add_argument('--csv-path', 
                       help='Path to the Calgary CREB city-wide data CSV file (defaults to archive)')
    parser.add_argument('--district-csv-path',
                       help='Path to the district-level data CSV file (defaults to archive)')
    parser.add_argument('--pdf-dir',
                       help='Directory containing PDF reports (defaults to config path)')
    parser.add_argument('--force', action='store_true',
                       help='Force re-extraction of latest month even if it exists')
    
    args = parser.parse_args()
    
    updater = CalgaryDataUpdater(args.csv_path, args.pdf_dir, args.district_csv_path)
    
    success = updater.run_update()
    
    if success:
        print("\n✅ Calgary CREB unified data update completed successfully!")
        print(f"   📊 City-wide data: {updater.output_city_path.name}")
        print(f"   🏘️  District data: {updater.output_district_path.name}")
        print(f"\nFiles saved to: {updater.output_city_path.parent}")
        
        # Print clickable file paths
        print(f"\n📂 Click to open files:")
        print(f"   City CSV:     file://{updater.output_city_path}")
        print(f"   City JSON:    file://{updater.output_city_path.with_suffix('.json')}")
        print(f"   District CSV: file://{updater.output_district_path}")
        print(f"   District JSON:file://{updater.output_district_path.with_suffix('.json')}")
        
        # Print validation commands
        print(f"\n📋 Next steps for validation:")
        print(f"  1. Review CSVs:")
        print(f"     less {updater.output_city_path}")
        print(f"     less {updater.output_district_path}")
        print(f"  2. Check JSON validation reports:")
        print(f"     less {updater.output_city_path.with_suffix('.json')}")
        print(f"     less {updater.output_district_path.with_suffix('.json')}")
        print(f"  3. If approved, move both files:")
        print(f"     mv {updater.output_city_path} {updater.output_city_path.parent.parent}/approved/")
        print(f"     mv {updater.output_district_path} {updater.output_district_path.parent.parent}/approved/")
        print(f"  4. Load to database:")
        print(f"     cd data-engine/core && python3 load_csv_direct.py")
    else:
        print("❌ Calgary CREB unified data update failed")


if __name__ == "__main__":
    main()