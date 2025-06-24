#!/usr/bin/env python3
"""
Calgary Economic Indicators Extractor
Extracts data from Calgary economic indicator Excel files (2015-2025)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import re
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalgaryEconomicExtractor:
    """Extracts Calgary economic indicators from Excel files."""
    
    def __init__(self, raw_data_path: str = None):
        self.raw_data_path = Path(raw_data_path) if raw_data_path else Path(__file__).parent.parent.parent / "data/raw/calgary_economic_indicators"
        
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
    
    def analyze_excel_structure(self, file_path: Path) -> Dict[str, Any]:
        """Analyze the structure of an Excel file to understand its format."""
        
        try:
            # Read Excel file and get sheet information
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            structure = {
                'file_path': str(file_path),
                'sheet_names': sheet_names,
                'sheet_analysis': {}
            }
            
            # Analyze each sheet
            for sheet_name in sheet_names[:3]:  # Limit to first 3 sheets
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=20)
                    
                    structure['sheet_analysis'][sheet_name] = {
                        'shape': df.shape,
                        'first_rows': df.head(10).to_dict() if not df.empty else {},
                        'potential_indicators': self._find_potential_indicators(df)
                    }
                    
                except Exception as e:
                    logger.debug(f"Could not analyze sheet {sheet_name}: {e}")
                    structure['sheet_analysis'][sheet_name] = {'error': str(e)}
            
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing Excel file {file_path}: {e}")
            return {'error': str(e)}
    
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
    
    def extract_indicators_from_excel(self, file_path: Path, target_date: str = None) -> List[Dict[str, Any]]:
        """Extract economic indicators from a single Excel file."""
        
        logger.info(f"Extracting indicators from {file_path.name}")
        
        # Get date from filename
        date_info = self.extract_date_from_filename(file_path.name)
        if not date_info:
            logger.error(f"Could not extract date from {file_path.name}")
            return []
        
        year, month = date_info
        file_date = f"{year}-{month:02d}-01"
        
        # Skip if target_date specified and doesn't match
        if target_date and not file_date.startswith(target_date):
            return []
        
        records = []
        
        try:
            # Analyze file structure first
            structure = self.analyze_excel_structure(file_path)
            
            # Try different extraction strategies
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # Strategy 1: Look for data in first sheet (most common)
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
                        'confidence_score': match['confidence']
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
        """Process all economic indicator Excel files."""
        
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
                records = self.extract_indicators_from_excel(file_path, target_month)
                
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
            'indicators_extracted': len(unique_records)
        }
    
    def _deduplicate_records(self, records: List[Dict]) -> List[Dict]:
        """Remove duplicate records (same date, indicator_type, indicator_name)."""
        
        seen = set()
        unique_records = []
        
        for record in records:
            key = (record['date'], record['indicator_type'], record['indicator_name'])
            
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
        
        logger.info(f"Deduplicated: {len(records)} -> {len(unique_records)} records")
        return unique_records
    
    def save_to_database(self, records: List[Dict], db_path: str) -> bool:
        """Save extracted records to SQLite database."""
        
        if not records:
            logger.warning("No records to save")
            return True
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Insert records
            inserted = 0
            for record in records:
                try:
                    cursor.execute("""
                    INSERT OR REPLACE INTO economic_indicators_monthly 
                    (date, indicator_type, indicator_name, value, unit, yoy_change, mom_change, 
                     category, source_file, confidence_score, validation_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                    """, (
                        record['date'],
                        record['indicator_type'], 
                        record['indicator_name'],
                        record['value'],
                        record['unit'],
                        record.get('yoy_change'),
                        record.get('mom_change'),
                        record['category'],
                        record['source_file'],
                        record.get('confidence_score', 0.8)
                    ))
                    inserted += 1
                    
                except sqlite3.Error as e:
                    logger.error(f"Error inserting record: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Saved {inserted} economic indicators to database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database save failed: {e}")
            return False


def main():
    """Test the economic extractor."""
    
    extractor = CalgaryEconomicExtractor()
    
    # Process all files
    result = extractor.process_economic_files()
    
    if result['success']:
        print(f"✅ Economic extraction completed:")
        print(f"  Files processed: {result['files_processed']}/{result['total_files']}")
        print(f"  Indicators extracted: {result['indicators_extracted']}")
        
        # Show sample records
        if result['records']:
            print(f"\nSample indicators:")
            for record in result['records'][:5]:
                print(f"  {record['date']} - {record['indicator_name']}: {record['value']} {record['unit']}")
    else:
        print(f"❌ Economic extraction failed: {result.get('error')}")


if __name__ == "__main__":
    main()