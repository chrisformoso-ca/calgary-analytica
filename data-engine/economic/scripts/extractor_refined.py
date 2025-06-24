#!/usr/bin/env python3
"""
Calgary Economic Indicators Extractor - Refined Version
Correctly extracts data from Calgary economic indicator Excel files
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalgaryEconomicExtractor:
    """Extracts Calgary economic indicators from Excel files."""
    
    def __init__(self):
        # Initialize config manager
        self.config = ConfigManager()
        self.raw_data_path = self.config.get_economic_data_dir()
        self.validation_pending_path = self.config.get_pending_review_dir()
        
        # Updated indicator mapping with better patterns and expected ranges
        self.indicator_mapping = {
            # Employment indicators
            'unemployment_rate': {
                'category': 'labour',
                'unit': 'percentage',
                'keywords': ['unemployment rate.*calgary', 'unemployment rate.*cer'],
                'expected_range': (0.01, 0.20),  # 1% to 20%
                'multiply_by': 100  # Convert decimal to percentage if needed
            },
            'employment': {
                'category': 'labour',
                'unit': 'thousands',
                'keywords': ['employment.*cer.*000s', 'employment.*calgary.*000s'],
                'expected_range': (500, 1500)  # thousands of people
            },
            'labour_force': {
                'category': 'labour',
                'unit': 'thousands',
                'keywords': ['labour force', 'labor force'],
                'expected_range': (500, 1500)
            },
            'participation_rate': {
                'category': 'labour',
                'unit': 'percentage',
                'keywords': ['participation rate'],
                'expected_range': (0.50, 0.80),
                'multiply_by': 100
            },
            
            # Population indicators  
            'population': {
                'category': 'demographics',
                'unit': 'thousands',
                'keywords': ['city of calgary population.*000s', 'population estimate.*000s'],
                'expected_range': (1000, 2000)  # thousands
            },
            'migration': {
                'category': 'demographics',
                'unit': 'persons',
                'keywords': ['migration', 'net migration'],
                'expected_range': (-50000, 50000)
            },
            
            # Economic indicators
            'gdp': {
                'category': 'economy',
                'unit': 'millions',
                'keywords': ['gdp', 'gross domestic product'],
                'expected_range': (50000, 200000)
            },
            'inflation': {
                'category': 'economy',
                'unit': 'percentage',
                'keywords': ['inflation rate.*calgary', 'calgary.*inflation'],
                'expected_range': (-0.05, 0.10),
                'multiply_by': 100
            },
            'average_weekly_earnings': {
                'category': 'labour',
                'unit': 'dollars',
                'keywords': ['average weekly earnings.*alberta', 'weekly earnings.*alberta'],
                'expected_range': (800, 2000)
            },
            
            # Housing indicators
            'housing_starts': {
                'category': 'housing',
                'unit': 'units',
                'keywords': ['housing starts', 'total starts'],
                'expected_range': (0, 5000)
            },
            'building_permits': {
                'category': 'housing',
                'unit': 'permits',
                'keywords': ['building permits.*total', 'total.*building permits'],
                'expected_range': (0, 5000)
            },
            'average_house_price': {
                'category': 'housing',
                'unit': 'dollars',
                'keywords': ['average house price', 'average price.*total residential'],
                'expected_range': (200000, 1000000)
            },
            
            # Energy indicators
            'oil_price_wti': {
                'category': 'energy',
                'unit': 'USD/barrel',
                'keywords': ['west texas intermediate', 'wti.*oil'],
                'expected_range': (20, 150)
            },
            'natural_gas_price': {
                'category': 'energy',
                'unit': 'CAD/GJ',
                'keywords': ['alberta natural gas', 'natural gas.*alberta'],
                'expected_range': (0.5, 10)
            }
        }
    
    def find_excel_files(self) -> List[Path]:
        """Find all Excel economic indicator files."""
        excel_files = []
        
        # Look for xlsx files with economic indicator patterns
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
    
    def extract_date_from_filename(self, filename: str) -> Optional[Tuple[int, int]]:
        """Extract year and month from filename."""
        
        # Pattern: Current-Economic-Indicators-YYYY-MM.xlsx
        match = re.search(r'(\d{4})-(\d{1,2})', filename)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            return year, month
        
        logger.warning(f"Could not extract date from filename: {filename}")
        return None
    
    def extract_indicators_from_excel(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract economic indicators from a single Excel file."""
        
        logger.info(f"Extracting indicators from {file_path.name}")
        
        # Get date from filename
        date_info = self.extract_date_from_filename(file_path.name)
        if not date_info:
            logger.error(f"Could not extract date from {file_path.name}")
            return []
        
        year, month = date_info
        file_date = f"{year}-{month:02d}-01"
        
        records = []
        
        try:
            # Read the Excel file
            df = pd.read_excel(file_path, sheet_name='Table', header=None)
            
            # The structure is typically:
            # Row 0: Main date header (e.g., "December 2024")
            # Row 2: Column headers with years/dates
            # Row 3+: Categories and data
            # Column 0-3: Metadata
            # Column 4: Indicator names
            # Column 5+: Data values
            
            # Extract the current month's data (usually column 5)
            records = self._extract_indicators_from_dataframe(df, file_date, file_path.name)
            
            logger.info(f"Extracted {len(records)} indicators from {file_path.name}")
            return records
            
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            return []
    
    def _extract_indicators_from_dataframe(self, df: pd.DataFrame, file_date: str, filename: str) -> List[Dict[str, Any]]:
        """Extract indicators from a pandas DataFrame with the correct structure."""
        records = []
        
        # Skip header rows and process data rows
        for row_idx in range(4, len(df)):
            row = df.iloc[row_idx]
            
            # Skip empty rows
            if pd.isna(row[4]) or str(row[4]).strip() == '':
                continue
            
            # Get the indicator name from column 4
            indicator_text = str(row[4]).lower().strip()
            
            # Try to match with known indicators
            for indicator_type, config in self.indicator_mapping.items():
                matched = False
                for keyword in config['keywords']:
                    if re.search(keyword.lower(), indicator_text):
                        matched = True
                        break
                
                if matched:
                    # Extract the value from column 5 (current month's data)
                    value = self._extract_value(row, 5, config)
                    
                    if value is not None:
                        # Calculate confidence based on value validity
                        confidence = self._calculate_confidence(value, config)
                        
                        record = {
                            'date': file_date,
                            'indicator_type': indicator_type,
                            'indicator_name': row[4] if pd.notna(row[4]) else indicator_type,
                            'value': value,
                            'unit': config['unit'],
                            'category': config['category'],
                            'source_file': filename,
                            'sheet_name': 'Table',
                            'confidence_score': confidence,
                            'validation_status': 'pending'
                        }
                        
                        # Extract YoY change if available (usually column 6 or 7)
                        yoy_value = self._extract_percentage_change(row, 6)
                        if yoy_value is not None:
                            record['yoy_change'] = yoy_value
                        
                        records.append(record)
                        break  # Only match once per indicator
        
        return records
    
    def _extract_value(self, row: pd.Series, col_idx: int, config: Dict) -> Optional[float]:
        """Extract and validate a numeric value from a specific column."""
        
        if col_idx >= len(row):
            return None
        
        value = row[col_idx]
        
        # Handle different value types
        if pd.isna(value):
            return None
        
        try:
            if isinstance(value, (int, float)):
                numeric_value = float(value)
            else:
                # Clean string values
                cleaned = str(value).replace(',', '').replace('$', '').strip()
                if cleaned == '' or cleaned == '-' or cleaned.lower() == 'nan':
                    return None
                numeric_value = float(cleaned)
            
            # Apply multiplication factor if needed (e.g., convert decimal to percentage)
            if 'multiply_by' in config:
                # Check if value needs multiplication (e.g., 0.06 -> 6%)
                if numeric_value < 1 and config['unit'] == 'percentage':
                    numeric_value *= config['multiply_by']
            
            # Validate against expected range
            if 'expected_range' in config:
                min_val, max_val = config['expected_range']
                if not (min_val <= numeric_value <= max_val):
                    logger.warning(f"Value {numeric_value} outside expected range {config['expected_range']}")
                    # Don't reject, just flag with lower confidence
            
            return numeric_value
            
        except (ValueError, TypeError) as e:
            logger.debug(f"Could not parse value: {value} - {e}")
            return None
    
    def _extract_percentage_change(self, row: pd.Series, col_idx: int) -> Optional[float]:
        """Extract a percentage change value (YoY or MoM)."""
        
        if col_idx >= len(row):
            return None
        
        value = row[col_idx]
        
        if pd.isna(value):
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            else:
                # Clean percentage strings
                cleaned = str(value).replace('%', '').replace(',', '').strip()
                if cleaned == '' or cleaned == '-':
                    return None
                return float(cleaned)
        except:
            return None
    
    def _calculate_confidence(self, value: float, config: Dict) -> float:
        """Calculate confidence score based on value validity."""
        
        confidence = 0.9  # Base confidence
        
        # Check if value is within expected range
        if 'expected_range' in config:
            min_val, max_val = config['expected_range']
            if min_val <= value <= max_val:
                confidence = 0.95
            else:
                # Reduce confidence if outside range
                confidence = 0.7
        
        return confidence
    
    def process_economic_files(self, year_range: Tuple[int, int] = None, target_month: str = None) -> Dict[str, Any]:
        """Process all economic indicator Excel files and save to validation pipeline."""
        
        logger.info("🏛️  Starting Calgary economic indicators extraction (refined)")
        
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
                date_info = self.extract_date_from_filename(file_path.name)
                if date_info and year_range[0] <= date_info[0] <= year_range[1]:
                    filtered_files.append(file_path)
            excel_files = filtered_files
        
        # Process files
        all_records = []
        processed_files = 0
        failed_files = []
        
        for file_path in excel_files:
            try:
                # Extract for specific month if specified
                if target_month:
                    date_info = self.extract_date_from_filename(file_path.name)
                    if not date_info:
                        continue
                    year, month = date_info
                    file_date = f"{year}-{month:02d}"
                    if not file_date.startswith(target_month):
                        continue
                
                records = self.extract_indicators_from_excel(file_path)
                
                if records:
                    all_records.extend(records)
                    processed_files += 1
                    logger.info(f"✅ Processed {file_path.name}: {len(records)} indicators")
                else:
                    logger.warning(f"⚠️  No indicators extracted from {file_path.name}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to process {file_path.name}: {e}")
                failed_files.append(str(file_path))
        
        # Deduplicate records
        unique_records = self._deduplicate_records(all_records)
        
        # Save to validation pipeline
        if unique_records:
            csv_path = self._save_to_validation(unique_records)
            logger.info(f"💾 Saved {len(unique_records)} indicators to {csv_path}")
        
        logger.info(f"📊 Economic extraction complete:")
        logger.info(f"  Files processed: {processed_files}/{len(excel_files)}")
        logger.info(f"  Total indicators extracted: {len(unique_records)}")
        logger.info(f"  Failed files: {len(failed_files)}")
        
        return {
            'success': True,
            'records': unique_records,
            'files_processed': processed_files,
            'total_files': len(excel_files),
            'failed_files': failed_files,
            'indicators_extracted': len(unique_records),
            'csv_path': csv_path if unique_records else None
        }
    
    def _deduplicate_records(self, records: List[Dict]) -> List[Dict]:
        """Remove duplicate records (same date, indicator_type)."""
        
        seen = set()
        unique_records = []
        
        for record in records:
            key = (record['date'], record['indicator_type'])
            
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
        
        logger.info(f"Deduplicated: {len(records)} -> {len(unique_records)} records")
        return unique_records
    
    def _save_to_validation(self, records: List[Dict]) -> Path:
        """Save records to validation pending directory as CSV."""
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"economic_indicators_{timestamp}.csv"
        csv_path = self.validation_pending_path / filename
        
        # Ensure directory exists
        self.validation_pending_path.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(csv_path, index=False)
        
        # Also save a validation report
        validation_report = {
            'source': 'economic_indicators',
            'extraction_date': datetime.now().isoformat(),
            'records_extracted': len(records),
            'confidence_scores': {
                'high': sum(1 for r in records if r['confidence_score'] >= 0.9),
                'medium': sum(1 for r in records if 0.7 <= r['confidence_score'] < 0.9),
                'low': sum(1 for r in records if r['confidence_score'] < 0.7)
            },
            'indicators_by_category': {},
            'sample_values': {}
        }
        
        # Count by category and collect sample values
        for record in records:
            cat = record['category']
            if cat not in validation_report['indicators_by_category']:
                validation_report['indicators_by_category'][cat] = 0
            validation_report['indicators_by_category'][cat] += 1
            
            # Store sample values for verification
            if record['indicator_type'] not in validation_report['sample_values']:
                validation_report['sample_values'][record['indicator_type']] = {
                    'value': record['value'],
                    'unit': record['unit'],
                    'date': record['date']
                }
        
        # Save validation report
        report_path = csv_path.with_suffix('.json')
        with open(report_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        return csv_path


def main():
    """Test the refined economic extractor."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Calgary economic indicators (refined)')
    parser.add_argument('--year-start', type=int, help='Start year for extraction')
    parser.add_argument('--year-end', type=int, help='End year for extraction')
    parser.add_argument('--month', type=str, help='Target month (YYYY-MM format)')
    parser.add_argument('--test', action='store_true', help='Test with one file')
    args = parser.parse_args()
    
    extractor = CalgaryEconomicExtractor()
    
    if args.test:
        # Test with a single recent file
        test_files = list(extractor.raw_data_path.glob("*2025-05*.xlsx"))
        if test_files:
            logger.info(f"Testing with file: {test_files[0].name}")
            records = extractor.extract_indicators_from_excel(test_files[0])
            
            if records:
                print(f"\n✅ Test extraction successful!")
                print(f"Extracted {len(records)} indicators:")
                for record in records:
                    print(f"  {record['indicator_type']}: {record['value']} {record['unit']} (confidence: {record['confidence_score']:.2f})")
            else:
                print("❌ No indicators extracted in test")
        else:
            print("❌ No test files found")
        return
    
    # Set year range if provided
    year_range = None
    if args.year_start and args.year_end:
        year_range = (args.year_start, args.year_end)
    
    # Process files
    result = extractor.process_economic_files(year_range=year_range, target_month=args.month)
    
    if result['success']:
        print(f"\n✅ Economic extraction completed:")
        print(f"  Files processed: {result['files_processed']}/{result['total_files']}")
        print(f"  Indicators extracted: {result['indicators_extracted']}")
        if result.get('csv_path'):
            print(f"  Output saved to: {result['csv_path']}")
        
        # Show sample records with actual values
        if result['records']:
            print(f"\nSample indicators with values:")
            for record in result['records'][:10]:
                print(f"  {record['date']} - {record['indicator_type']}: {record['value']:.2f} {record['unit']}")
    else:
        print(f"❌ Economic extraction failed: {result.get('error')}")


if __name__ == "__main__":
    main()