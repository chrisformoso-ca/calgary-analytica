#!/usr/bin/env python3
"""
Calgary Economic Indicators Time Series Extractor
Extracts full time series data from Calgary economic indicator Excel files
Handles overlapping data and updates from newer files
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import re
from datetime import datetime
import json
import sys

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CalgaryEconomicTimeSeriesExtractor:
    """Extracts full time series economic indicators from Excel files."""
    
    def __init__(self):
        # Initialize config manager
        self.config = ConfigManager()
        self.raw_data_path = self.config.get_economic_data_dir()
        self.validation_pending_path = self.config.get_pending_review_dir()
        
        # Enhanced indicator mapping with value type detection
        self.indicator_patterns = {
            # Labour Market - Absolute values
            'unemployment_rate': {
                'patterns': [r'unemployment rate.*calgary', r'unemployment rate.*cer.*\%'],
                'category': 'labour',
                'unit': 'percentage',
                'value_type': 'rate',
                'expected_range': (2.0, 15.0)
            },
            'unemployment_rate_canada': {
                'patterns': [r'unemployment rate.*canada'],
                'category': 'labour',
                'unit': 'percentage',
                'value_type': 'rate',
                'expected_range': (2.0, 15.0)
            },
            'employment': {
                'patterns': [r'employment.*cer.*000s'],
                'category': 'labour',
                'unit': 'thousands',
                'value_type': 'absolute',
                'expected_range': (500, 1500)
            },
            'ei_recipients_alberta': {
                'patterns': [r'employment insurance alberta.*recipients'],
                'category': 'labour',
                'unit': 'persons',
                'value_type': 'absolute',
                'expected_range': (10000, 100000)
            },
            'ei_recipients_calgary': {
                'patterns': [r'employment insurance calgary.*recipients'],
                'category': 'labour',
                'unit': 'persons',
                'value_type': 'absolute',
                'expected_range': (5000, 50000)
            },
            
            # Demographics
            'population': {
                'patterns': [r'city of calgary population.*000s'],
                'category': 'demographics',
                'unit': 'thousands',
                'value_type': 'absolute',
                'expected_range': (1000, 2000)
            },
            
            # Energy
            'oil_price_wti': {
                'patterns': [r'west texas intermediate', r'wti.*oil'],
                'category': 'energy',
                'unit': 'USD/barrel',
                'value_type': 'absolute',
                'expected_range': (20, 150)
            },
            'natural_gas_price': {
                'patterns': [r'alberta natural gas'],
                'category': 'energy',
                'unit': 'CAD/GJ',
                'value_type': 'absolute',
                'expected_range': (0.5, 10)
            },
            
            # Prices
            'inflation_rate_calgary': {
                'patterns': [r'inflation rate.*calgary', r'calgary.*inflation.*y/y'],
                'category': 'economy',
                'unit': 'percentage',
                'value_type': 'rate',
                'expected_range': (-2.0, 10.0)
            },
            'inflation_rate_canada': {
                'patterns': [r'inflation rate.*canada.*y/y'],
                'category': 'economy',
                'unit': 'percentage',
                'value_type': 'rate',
                'expected_range': (-2.0, 10.0)
            },
            'avg_hourly_wage_alberta': {
                'patterns': [
                    r'average hourly wage rate.*alberta.*y/y.*change',
                    r'average hourly wage.*alberta.*y/y'
                ],
                'category': 'labour',
                'unit': 'percentage',
                'value_type': 'yoy_change',
                'expected_range': (-5.0, 10.0)
            },
            'avg_weekly_earnings_alberta': {
                'patterns': [
                    r'average weekly earnings.*alberta.*seph.*y/y.*change',
                    r'average weekly earnings.*alberta.*y/y'
                ],
                'category': 'labour',
                'unit': 'percentage',
                'value_type': 'yoy_change',
                'expected_range': (-5.0, 10.0)
            },
            'avg_hourly_wage_calgary': {
                'patterns': [
                    r'average hourly wage rate.*calgary.*y/y.*change',
                    r'average hourly wage.*calgary.*y/y'
                ],
                'category': 'labour',
                'unit': 'percentage',
                'value_type': 'yoy_change',
                'expected_range': (-5.0, 10.0)
            },
            'avg_weekly_wage_calgary': {
                'patterns': [
                    r'average weekly wage rate.*calgary.*y/y.*change',
                    r'average weekly wage.*calgary.*y/y'
                ],
                'category': 'labour',
                'unit': 'percentage', 
                'value_type': 'yoy_change',
                'expected_range': (-5.0, 10.0)
            },
            
            # General Indicators
            'gdp_growth_canada': {
                'patterns': [r'canada.*real gdp growth'],
                'category': 'economy',
                'unit': 'percentage',
                'value_type': 'rate',
                'expected_range': (-5.0, 10.0)
            },
            'prime_lending_rate': {
                'patterns': [r'prime lending rate'],
                'category': 'economy',
                'unit': 'percentage',
                'value_type': 'rate',
                'expected_range': (0.0, 20.0)
            },
            'bank_of_canada_rate': {
                'patterns': [r'bank of canada interest rate'],
                'category': 'economy',
                'unit': 'percentage',
                'value_type': 'rate',
                'expected_range': (0.0, 20.0)
            },
            
            # Consumer Indicators
            'retail_sales_alberta': {
                'patterns': [r'retail sales.*alberta.*billions'],
                'category': 'consumer',
                'unit': 'billions',
                'value_type': 'absolute',
                'expected_range': (50, 200)
            },
            'housing_starts': {
                'patterns': [r'housing starts.*calgary'],
                'category': 'housing',
                'unit': 'units',
                'value_type': 'absolute',
                'expected_range': (0, 50000)  # Annual can be high
            },
            'bankruptcies_personal': {
                'patterns': [r'personal bankruptcies.*alberta'],
                'category': 'consumer',
                'unit': 'count',
                'value_type': 'absolute',
                'expected_range': (0, 10000)
            },
            'mls_unit_sales': {
                'patterns': [r'residential unit sales mls'],
                'category': 'housing',
                'unit': 'units',
                'value_type': 'absolute',
                'expected_range': (0, 50000)
            },
            'mls_sales_to_listings': {
                'patterns': [r'sales-to-new listings ratio'],
                'category': 'housing',
                'unit': 'percentage',
                'value_type': 'rate',
                'expected_range': (0, 150)
            },
            'mls_average_price': {
                'patterns': [r'residential average price.*thousands'],
                'category': 'housing',
                'unit': 'thousands',
                'value_type': 'absolute',
                'expected_range': (200, 1000)
            },
            'building_permits_value': {
                'patterns': [r'building permits.*millions'],
                'category': 'housing',
                'unit': 'millions',
                'value_type': 'absolute',
                'expected_range': (0, 20000)  # Annual can be high
            },
            
            # Business Indicators - NEW
            'retail_sales_calgary': {
                'patterns': [r'retail sales.*calgary.*billions'],
                'category': 'consumer',
                'unit': 'billions',
                'value_type': 'absolute',
                'expected_range': (1, 100)
            },
            'wholesale_sales_alberta': {
                'patterns': [r'wholesale sales.*alberta.*billions'],
                'category': 'business',
                'unit': 'billions',
                'value_type': 'absolute',
                'expected_range': (10, 500)
            },
            'manufacturing_sales_alberta': {
                'patterns': [r'manufacturing sales.*alberta.*billions'],
                'category': 'business',
                'unit': 'billions',
                'value_type': 'absolute',
                'expected_range': (50, 200)
            },
            'business_bankruptcies': {
                'patterns': [
                    r'business bankruptcies.*alberta',
                    r'number of business bankruptcies.*alberta'
                ],
                'category': 'business',
                'unit': 'count',
                'value_type': 'absolute',
                'expected_range': (0, 1000)
            }
        }
        
        # Year-over-year change indicators (detect from row below main indicator)
        self.yoy_patterns = [
            r'year-over-year.*change',
            r'y/y.*change',
            r'yoy.*change'
        ]
    
    def find_excel_files(self) -> List[Path]:
        """Find all Excel economic indicator files."""
        excel_files = []
        
        patterns = [
            "*economic-indicators*.xlsx",
            "*Economic-Indicators*.xlsx",
            "*current-economic*.xlsx"
        ]
        
        for pattern in patterns:
            excel_files.extend(self.raw_data_path.glob(pattern))
        
        # Sort by filename to process chronologically
        excel_files.sort()
        
        logger.info(f"Found {len(excel_files)} Excel economic indicator files")
        return excel_files
    
    def extract_file_date(self, filename: str) -> Optional[datetime]:
        """Extract the file's publication date from filename."""
        match = re.search(r'(\d{4})-(\d{1,2})', filename)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            return datetime(year, month, 1)
        return None
    
    def parse_date_headers(self, df: pd.DataFrame) -> Dict[int, Tuple[str, datetime]]:
        """Parse date headers from row 2 of the Excel file."""
        date_columns = {}
        
        # Row 2 contains the date headers
        if len(df) > 2:
            header_row = df.iloc[2]
            
            for col_idx, header in enumerate(header_row):
                if pd.isna(header) or col_idx < 4:  # Skip metadata columns
                    continue
                
                header_str = str(header)
                parsed_date = None
                date_label = None
                
                # Try to parse different date formats
                # Annual: "2023", "2024"
                if re.match(r'^\d{4}$', header_str):
                    year = int(header_str)
                    parsed_date = datetime(year, 1, 1)
                    date_label = f"{year}-annual"
                
                # Monthly: "Jan-24", "Feb-24"
                elif re.match(r'^[A-Za-z]{3}-\d{2}$', header_str):
                    try:
                        parsed_date = pd.to_datetime(header_str, format='%b-%y')
                        date_label = parsed_date.strftime('%Y-%m')
                    except:
                        pass
                
                # datetime object (sometimes pandas reads dates as datetime)
                elif isinstance(header, datetime) or hasattr(header, 'strftime'):
                    parsed_date = pd.to_datetime(header)
                    date_label = parsed_date.strftime('%Y-%m')
                
                if parsed_date and date_label:
                    date_columns[col_idx] = (date_label, parsed_date)
        
        return date_columns
    
    def identify_indicator(self, indicator_text: str) -> Optional[Tuple[str, Dict]]:
        """Identify indicator type from text using patterns."""
        if pd.isna(indicator_text):
            return None
        
        text_lower = str(indicator_text).lower().strip()
        
        # First check if this matches a known indicator (including wage indicators with YoY)
        for indicator_type, config in self.indicator_patterns.items():
            for pattern in config['patterns']:
                if re.search(pattern, text_lower):
                    return indicator_type, config
        
        # If no match, check if it's a standalone YoY row to skip
        for pattern in self.yoy_patterns:
            if re.search(pattern, text_lower):
                return None  # Skip standalone YoY rows, we'll capture them with their parent
        
        return None
    
    def extract_value(self, value: Any, config: Dict) -> Optional[float]:
        """Extract and validate numeric value."""
        if pd.isna(value) or str(value).strip() in ['#N/A', '-', '']:
            return None
        
        try:
            # Handle different value types
            if isinstance(value, (int, float)):
                numeric_value = float(value)
            else:
                # Clean string values
                cleaned = str(value).replace(',', '').replace('$', '').replace('%', '').strip()
                numeric_value = float(cleaned)
            
            # Convert percentages stored as decimals
            if config['value_type'] in ['rate', 'yoy_change'] and config['unit'] == 'percentage':
                if -1 < numeric_value < 1:  # Likely a decimal representation
                    numeric_value *= 100
            
            # Validate against expected range
            min_val, max_val = config.get('expected_range', (-float('inf'), float('inf')))
            if not (min_val <= numeric_value <= max_val):
                logger.debug(f"Value {numeric_value} outside range {config['expected_range']} for {config}")
                # Don't reject, just note it
            
            return numeric_value
            
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse value: {value} - {e}")
            return None
    
    def extract_time_series_from_excel(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract full time series data from Excel file."""
        logger.info(f"Extracting time series from {file_path.name}")
        
        file_date = self.extract_file_date(file_path.name)
        if not file_date:
            logger.error(f"Could not extract date from {file_path.name}")
            return []
        
        records = []
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name='Table', header=None)
            
            # Parse date headers
            date_columns = self.parse_date_headers(df)
            
            if not date_columns:
                logger.error(f"No date columns found in {file_path.name}")
                return []
            
            logger.info(f"Found {len(date_columns)} date columns: {list(date_columns.values())[:5]}...")
            
            # Process each data row
            for row_idx in range(4, len(df)):
                row = df.iloc[row_idx]
                
                # Get indicator name from column 4
                indicator_text = row[4]
                indicator_match = self.identify_indicator(indicator_text)
                
                if not indicator_match:
                    continue
                
                indicator_type, config = indicator_match
                
                # Check if next row is YoY change for this indicator
                yoy_values = {}
                if row_idx + 1 < len(df):
                    next_row = df.iloc[row_idx + 1]
                    next_text = str(next_row[4]).lower() if pd.notna(next_row[4]) else ""
                    
                    is_yoy = any(re.search(pattern, next_text) for pattern in self.yoy_patterns)
                    if is_yoy:
                        # Extract YoY values
                        for col_idx, (date_label, parsed_date) in date_columns.items():
                            yoy_val = self.extract_value(next_row[col_idx], 
                                                       {'value_type': 'yoy_change', 'unit': 'percentage'})
                            if yoy_val is not None:
                                yoy_values[date_label] = yoy_val
                
                # Extract values for each date column
                for col_idx, (date_label, parsed_date) in date_columns.items():
                    value = self.extract_value(row[col_idx], config)
                    
                    if value is not None:
                        record = {
                            'date': parsed_date.strftime('%Y-%m-%d'),
                            'indicator_type': indicator_type,
                            'indicator_name': str(indicator_text).strip(),
                            'value': value,
                            'unit': config['unit'],
                            'value_type': config['value_type'],
                            'category': config['category'],
                            '_source_file': file_path.name  # Temporary for deduplication
                        }
                        
                        # Add YoY change if available
                        if date_label in yoy_values:
                            record['yoy_change'] = yoy_values[date_label]
                        
                        records.append(record)
            
            logger.info(f"Extracted {len(records)} time series records from {file_path.name}")
            return records
            
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def process_economic_files(self, year_range: Tuple[int, int] = None) -> Dict[str, Any]:
        """Process all economic files and extract time series data."""
        logger.info("🏛️  Starting Calgary economic indicators time series extraction")
        
        # Find all Excel files
        excel_files = self.find_excel_files()
        
        if not excel_files:
            return {
                'success': False,
                'error': 'No Excel files found',
                'files_processed': 0
            }
        
        # Filter by year range if specified
        if year_range:
            filtered_files = []
            for file_path in excel_files:
                file_date = self.extract_file_date(file_path.name)
                if file_date and year_range[0] <= file_date.year <= year_range[1]:
                    filtered_files.append(file_path)
            excel_files = filtered_files
        
        # Process files
        all_records = []
        processed_files = 0
        failed_files = []
        
        for file_path in excel_files:
            try:
                records = self.extract_time_series_from_excel(file_path)
                
                if records:
                    all_records.extend(records)
                    processed_files += 1
                    logger.info(f"✅ Processed {file_path.name}: {len(records)} records")
                else:
                    logger.warning(f"⚠️  No records extracted from {file_path.name}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to process {file_path.name}: {e}")
                failed_files.append(str(file_path))
        
        # Smart deduplication - keep latest file's data for each indicator-date
        unique_records = self._smart_deduplicate(all_records, excel_files)
        
        # Save to validation pipeline
        if unique_records:
            csv_path = self._save_to_validation(unique_records)
            logger.info(f"💾 Saved {len(unique_records)} records to {csv_path}")
        
        # Summary statistics
        date_range = self._get_date_range(unique_records)
        indicators_found = len(set(r['indicator_type'] for r in unique_records))
        
        logger.info(f"📊 Time series extraction complete:")
        logger.info(f"  Files processed: {processed_files}/{len(excel_files)}")
        logger.info(f"  Total records extracted: {len(unique_records)}")
        logger.info(f"  Date range: {date_range}")
        logger.info(f"  Unique indicators: {indicators_found}")
        logger.info(f"  Failed files: {len(failed_files)}")
        
        return {
            'success': True,
            'records': unique_records,
            'files_processed': processed_files,
            'total_files': len(excel_files),
            'failed_files': failed_files,
            'records_extracted': len(unique_records),
            'date_range': date_range,
            'indicators_found': indicators_found,
            'csv_path': csv_path if unique_records else None
        }
    
    def _smart_deduplicate(self, records: List[Dict], excel_files: List[Path]) -> List[Dict]:
        """Smart deduplication keeping data from newest files."""
        # Create file date mapping
        file_dates = {}
        for file_path in excel_files:
            file_date = self.extract_file_date(file_path.name)
            if file_date:
                file_dates[file_path.name] = file_date
        
        # Group by (date, indicator_type, value_type)
        grouped = {}
        
        for record in records:
            key = (record['date'], record['indicator_type'], record['value_type'])
            
            if key not in grouped:
                grouped[key] = record
            else:
                # Keep record from newer file
                existing_file_date = file_dates.get(grouped[key]['_source_file'])
                new_file_date = file_dates.get(record['_source_file'])
                
                if existing_file_date and new_file_date and new_file_date > existing_file_date:
                    grouped[key] = record
        
        unique_records = list(grouped.values())
        
        # Remove temporary source_file field
        for record in unique_records:
            record.pop('_source_file', None)
        
        logger.info(f"Deduplicated: {len(records)} -> {len(unique_records)} records")
        
        return unique_records
    
    def _get_date_range(self, records: List[Dict]) -> str:
        """Get the date range of the records."""
        if not records:
            return "No data"
        
        dates = [datetime.strptime(r['date'], '%Y-%m-%d') for r in records]
        min_date = min(dates)
        max_date = max(dates)
        
        return f"{min_date.strftime('%Y-%m')} to {max_date.strftime('%Y-%m')}"
    
    def _save_to_validation(self, records: List[Dict]) -> Path:
        """Save records to validation pending directory as CSV."""
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Sort by date and indicator for better readability
        df = df.sort_values(['date', 'indicator_type'])
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"economic_timeseries_{timestamp}.csv"
        csv_path = self.validation_pending_path / filename
        
        # Ensure directory exists
        self.validation_pending_path.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(csv_path, index=False)
        
        # Create validation report
        validation_report = {
            'source': 'economic_indicators_timeseries',
            'extraction_date': datetime.now().isoformat(),
            'records_extracted': len(records),
            'date_range': self._get_date_range(records),
            'files_processed': 'N/A',  # Source file info removed for simplicity
            'indicators_summary': {},
            'value_types': {},
            'sample_records': []
        }
        
        # Summarize by indicator
        for record in records:
            ind_type = record['indicator_type']
            if ind_type not in validation_report['indicators_summary']:
                validation_report['indicators_summary'][ind_type] = {
                    'count': 0,
                    'date_range': [],
                    'unit': record['unit'],
                    'value_type': record['value_type']
                }
            validation_report['indicators_summary'][ind_type]['count'] += 1
            validation_report['indicators_summary'][ind_type]['date_range'].append(record['date'])
        
        # Get date ranges for each indicator
        for ind_type, info in validation_report['indicators_summary'].items():
            dates = sorted(info['date_range'])
            info['date_range'] = f"{dates[0]} to {dates[-1]}"
        
        # Count by value type
        for record in records:
            vtype = record['value_type']
            validation_report['value_types'][vtype] = validation_report['value_types'].get(vtype, 0) + 1
        
        # Sample records for verification
        sample_indicators = ['unemployment_rate', 'population', 'oil_price_wti', 'inflation_rate_calgary']
        for ind in sample_indicators:
            sample = next((r for r in records if r['indicator_type'] == ind and r['date'] >= '2025-01-01'), None)
            if sample:
                validation_report['sample_records'].append({
                    'indicator': ind,
                    'date': sample['date'],
                    'value': sample['value'],
                    'unit': sample['unit'],
                    'yoy_change': sample.get('yoy_change', 'N/A')
                })
        
        # Save validation report
        report_path = csv_path.with_suffix('.json')
        with open(report_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        return csv_path


def main():
    """Test the time series extractor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Calgary economic indicators time series')
    parser.add_argument('--year-start', type=int, help='Start year for extraction')
    parser.add_argument('--year-end', type=int, help='End year for extraction')
    parser.add_argument('--test', action='store_true', help='Test with one recent file')
    parser.add_argument('--verify', action='store_true', help='Verify extraction completeness')
    parser.add_argument('--file', type=str, help='Specific file to test/verify')
    args = parser.parse_args()
    
    extractor = CalgaryEconomicTimeSeriesExtractor()
    
    if args.verify:
        # Verify mode - check what indicators we're capturing vs missing
        logger.info("🔍 Running extraction verification...")
        
        if args.file:
            test_files = [Path(extractor.raw_data_path / args.file)]
        else:
            test_files = list(extractor.raw_data_path.glob("*2025-05*.xlsx"))
        
        if test_files:
            file_path = test_files[0]
            logger.info(f"Verifying extraction from: {file_path.name}")
            
            # Read Excel to check all rows
            try:
                df = pd.read_excel(file_path, sheet_name='Table', header=None)
                
                matched_indicators = []
                unmatched_indicators = []
                
                # Check each row for potential indicators
                for row_idx in range(4, min(100, len(df))):  # Check first 100 rows
                    row = df.iloc[row_idx]
                    indicator_text = row[4] if pd.notna(row[4]) else ""
                    
                    if indicator_text and not any(re.search(p, str(indicator_text).lower()) for p in extractor.yoy_patterns):
                        indicator_match = extractor.identify_indicator(indicator_text)
                        
                        if indicator_match:
                            matched_indicators.append((indicator_text, indicator_match[0]))
                        else:
                            # Check if row has data (not just a header/blank)
                            has_data = any(pd.notna(row[col]) and str(row[col]).strip() not in ['', '-', '#N/A'] 
                                         for col in range(5, min(10, len(row))))
                            if has_data:
                                unmatched_indicators.append(indicator_text)
                
                print("\n✅ MATCHED INDICATORS:")
                print("-" * 70)
                for text, ind_type in sorted(matched_indicators, key=lambda x: x[1]):
                    print(f"{ind_type:30} | {text}")
                
                print(f"\n❌ UNMATCHED INDICATORS (potential missing data):")
                print("-" * 70)
                for text in unmatched_indicators:
                    print(f"  - {text}")
                
                print(f"\n📊 SUMMARY:")
                print(f"  Matched: {len(matched_indicators)} indicators")
                print(f"  Unmatched: {len(unmatched_indicators)} potential indicators")
                print(f"  Coverage: {len(matched_indicators)/(len(matched_indicators)+len(unmatched_indicators))*100:.1f}%")
                
            except Exception as e:
                logger.error(f"Error in verification: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            print("❌ No test files found")
        return
    
    if args.test:
        # Test with a single recent file
        test_files = list(extractor.raw_data_path.glob("*2025-05*.xlsx"))
        if test_files:
            logger.info(f"Testing with file: {test_files[0].name}")
            records = extractor.extract_time_series_from_excel(test_files[0])
            
            if records:
                print(f"\n✅ Test extraction successful!")
                print(f"Extracted {len(records)} time series records")
                
                # Show sample by indicator
                indicators = {}
                for r in records:
                    if r['indicator_type'] not in indicators:
                        indicators[r['indicator_type']] = []
                    indicators[r['indicator_type']].append(r)
                
                print(f"\nIndicators found: {len(indicators)}")
                for ind, recs in list(indicators.items())[:5]:
                    print(f"\n{ind}:")
                    for r in recs[:3]:  # Show first 3 dates
                        print(f"  {r['date']}: {r['value']:.2f} {r['unit']} (type: {r['value_type']})")
                        if 'yoy_change' in r:
                            print(f"    YoY change: {r['yoy_change']:.2f}%")
            else:
                print("❌ No records extracted in test")
        else:
            print("❌ No test files found")
        return
    
    # Set year range if provided
    year_range = None
    if args.year_start and args.year_end:
        year_range = (args.year_start, args.year_end)
    
    # Process files
    result = extractor.process_economic_files(year_range=year_range)
    
    if result['success']:
        print(f"\n✅ Time series extraction completed:")
        print(f"  Files processed: {result['files_processed']}/{result['total_files']}")
        print(f"  Records extracted: {result['records_extracted']}")
        print(f"  Date range: {result['date_range']}")
        print(f"  Unique indicators: {result['indicators_found']}")
        if result.get('csv_path'):
            csv_path = result['csv_path']
            print(f"  Output saved to: {csv_path}")
            
            # Print clickable file path
            print(f"\n📂 Click to open: file://{csv_path}")
            
            # Print validation commands
            print(f"\n📋 Next steps for validation:")
            print(f"  1. Review CSV:  less {csv_path}")
            print(f"  2. Check JSON:  less {csv_path.with_suffix('.json')}")
            print(f"  3. If approved: mv {csv_path} {csv_path.parent.parent}/approved/")
            print(f"  4. Load to DB:  cd data-engine/core && python3 load_csv_direct.py")
    else:
        print(f"❌ Extraction failed: {result.get('error')}")


if __name__ == "__main__":
    main()