#!/usr/bin/env python3
"""
Calgary Economic Indicators Extractor - Validation Pipeline Version
Extracts data from Calgary economic indicator Excel files and outputs to validation pipeline
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
        
        # Common economic indicator categories and patterns
        self.indicator_mapping = {
            # Employment indicators
            'employment_rate': {'category': 'labour', 'unit': 'percentage', 'keywords': ['employment rate', 'employment']},
            'unemployment_rate': {'category': 'labour', 'unit': 'percentage', 'keywords': ['unemployment rate', 'unemployment']},
            'labour_force': {'category': 'labour', 'unit': 'thousands', 'keywords': ['labour force', 'labor force']},
            'participation_rate': {'category': 'labour', 'unit': 'percentage', 'keywords': ['participation rate']},
            
            # Population indicators  
            'population': {'category': 'demographics', 'unit': 'thousands', 'keywords': ['population']},
            'migration': {'category': 'demographics', 'unit': 'persons', 'keywords': ['migration', 'net migration']},
            
            # Economic indicators
            'gdp': {'category': 'economy', 'unit': 'millions', 'keywords': ['gdp', 'gross domestic product']},
            'inflation': {'category': 'economy', 'unit': 'percentage', 'keywords': ['inflation', 'cpi', 'consumer price']},
            'average_weekly_earnings': {'category': 'labour', 'unit': 'dollars', 'keywords': ['average weekly earnings', 'weekly earnings']},
            
            # Housing indicators in economic reports
            'housing_starts': {'category': 'housing', 'unit': 'units', 'keywords': ['housing starts', 'housing start']},
            'building_permits': {'category': 'housing', 'unit': 'permits', 'keywords': ['building permits', 'building permit']},
            'mls_sales': {'category': 'housing', 'unit': 'sales', 'keywords': ['mls sales', 'resale']},
            'average_house_price': {'category': 'housing', 'unit': 'dollars', 'keywords': ['average house price', 'house price']},
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
        
        # Alternative patterns
        patterns = [
            r'(\d{4})[-_](\d{1,2})',  # 2025-05 or 2025_05
            r'(\d{1,2})[-_](\d{4})',  # 05-2025 or 05_2025 (month first)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                if len(match.group(1)) == 4:  # Year first
                    year, month = int(match.group(1)), int(match.group(2))
                else:  # Month first
                    month, year = int(match.group(1)), int(match.group(2))
                
                if 1 <= month <= 12 and 2000 <= year <= 2030:
                    return year, month
        
        logger.warning(f"Could not extract date from filename: {filename}")
        return None
    
    def _find_potential_indicators(self, df: pd.DataFrame) -> List[str]:
        """Find potential economic indicators in a dataframe."""
        indicators = []
        
        # Convert all cells to strings and search for keywords
        for indicator_type, config in self.indicator_mapping.items():
            for keyword in config['keywords']:
                # Search in all cells
                found = False
                for col in df.columns:
                    if df[col].astype(str).str.contains(keyword, case=False, na=False).any():
                        indicators.append(indicator_type)
                        found = True
                        break
                if found:
                    break
        
        return indicators
    
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
            # Try different extraction strategies
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # Look for data in each sheet
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    if df.empty:
                        continue
                    
                    # Extract indicators from this sheet
                    sheet_records = self._extract_from_dataframe(df, file_date, file_path.name, sheet_name)
                    records.extend(sheet_records)
                    
                    # If we found indicators in first sheet, often that's sufficient
                    if sheet_records and sheet_name == excel_file.sheet_names[0]:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error processing sheet {sheet_name}: {e}")
                    continue
            
            logger.info(f"Extracted {len(records)} indicators from {file_path.name}")
            return records
            
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            return []
    
    def _extract_from_dataframe(self, df: pd.DataFrame, file_date: str, filename: str, sheet_name: str) -> List[Dict[str, Any]]:
        """Extract indicators from a pandas DataFrame."""
        records = []
        
        # Strategy 1: Look for indicator patterns in rows
        for indicator_type, config in self.indicator_mapping.items():
            for keyword in config['keywords']:
                # Search for the keyword in the dataframe
                matches = self._find_indicator_data(df, keyword, config)
                
                for match in matches:
                    record = {
                        'date': file_date,
                        'indicator_type': indicator_type,
                        'indicator_name': keyword,
                        'value': match['value'],
                        'unit': config['unit'],
                        'category': config['category'],
                        'source_file': filename,
                        'sheet_name': sheet_name,
                        'confidence_score': match['confidence'],
                        'validation_status': 'pending'
                    }
                    
                    # Add YoY and MoM changes if available
                    if 'yoy_change' in match:
                        record['yoy_change'] = match['yoy_change']
                    if 'mom_change' in match:
                        record['mom_change'] = match['mom_change']
                    
                    records.append(record)
                    break  # Only take first match per indicator type
        
        return records
    
    def _find_indicator_data(self, df: pd.DataFrame, keyword: str, config: Dict) -> List[Dict[str, Any]]:
        """Find specific indicator data in the dataframe."""
        matches = []
        
        # Convert dataframe to string for searching
        df_str = df.astype(str)
        
        # Find rows containing the keyword
        for idx, row in df_str.iterrows():
            for col in df_str.columns:
                cell_value = row[col].lower()
                
                if keyword.lower() in cell_value:
                    # Found the indicator, now look for numerical data
                    numeric_data = self._extract_numeric_from_row(df.iloc[idx], keyword)
                    
                    if numeric_data:
                        matches.append({
                            'value': numeric_data['value'],
                            'confidence': numeric_data['confidence'],
                            'yoy_change': numeric_data.get('yoy_change'),
                            'mom_change': numeric_data.get('mom_change')
                        })
        
        return matches
    
    def _extract_numeric_from_row(self, row: pd.Series, keyword: str) -> Optional[Dict[str, Any]]:
        """Extract numeric value from a row containing an indicator."""
        
        numeric_values = []
        
        # Look for numeric values in the row
        for value in row:
            if pd.isna(value):
                continue
                
            # Try to extract number
            if isinstance(value, (int, float)):
                numeric_values.append(float(value))
            elif isinstance(value, str):
                # Clean and parse string numbers
                cleaned = re.sub(r'[^\d.-]', '', value.replace(',', ''))
                if cleaned and cleaned.replace('.', '').replace('-', '').isdigit():
                    try:
                        numeric_values.append(float(cleaned))
                    except ValueError:
                        continue
        
        if numeric_values:
            # Take the first reasonable numeric value
            for val in numeric_values:
                if abs(val) < 1e10:  # Reasonable range check
                    return {
                        'value': val,
                        'confidence': 0.8 if len(numeric_values) == 1 else 0.6
                    }
        
        return None
    
    def process_economic_files(self, year_range: Tuple[int, int] = None, target_month: str = None) -> Dict[str, Any]:
        """Process all economic indicator Excel files and save to validation pipeline."""
        
        logger.info("🏛️  Starting Calgary economic indicators extraction")
        
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
        
        # Deduplicate records (same indicator, same date)
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
                'high': sum(1 for r in records if r['confidence_score'] >= 0.8),
                'medium': sum(1 for r in records if 0.6 <= r['confidence_score'] < 0.8),
                'low': sum(1 for r in records if r['confidence_score'] < 0.6)
            },
            'indicators_by_category': {}
        }
        
        # Count by category
        for record in records:
            cat = record['category']
            if cat not in validation_report['indicators_by_category']:
                validation_report['indicators_by_category'][cat] = 0
            validation_report['indicators_by_category'][cat] += 1
        
        # Save validation report
        report_path = csv_path.with_suffix('.json')
        with open(report_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        return csv_path


def main():
    """Test the economic extractor."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Calgary economic indicators')
    parser.add_argument('--year-start', type=int, help='Start year for extraction')
    parser.add_argument('--year-end', type=int, help='End year for extraction')
    parser.add_argument('--month', type=str, help='Target month (YYYY-MM format)')
    args = parser.parse_args()
    
    extractor = CalgaryEconomicExtractor()
    
    # Set year range if provided
    year_range = None
    if args.year_start and args.year_end:
        year_range = (args.year_start, args.year_end)
    
    # Process files
    result = extractor.process_economic_files(year_range=year_range, target_month=args.month)
    
    if result['success']:
        print(f"✅ Economic extraction completed:")
        print(f"  Files processed: {result['files_processed']}/{result['total_files']}")
        print(f"  Indicators extracted: {result['indicators_extracted']}")
        if result['csv_path']:
            print(f"  Output saved to: {result['csv_path']}")
        
        # Show sample records
        if result['records']:
            print(f"\nSample indicators:")
            for record in result['records'][:5]:
                print(f"  {record['date']} - {record['indicator_name']}: {record['value']} {record['unit']}")
    else:
        print(f"❌ Economic extraction failed: {result.get('error')}")


if __name__ == "__main__":
    main()