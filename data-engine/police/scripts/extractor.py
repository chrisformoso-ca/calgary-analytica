#!/usr/bin/env python3
"""
Calgary Police Service Crime Statistics Extractor (Simplified)
Extracts crime, domestic, and disorder statistics from Calgary Police Service Excel reports
Handles row-based data format for all years (2018-2025)
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

class CalgaryCrimeExtractorSimplified:
    """Simplified extractor for Calgary Police Service crime statistics."""
    
    def __init__(self):
        # Initialize config manager
        self.config = ConfigManager()
        self.raw_data_path = self.config.get_project_root() / 'data-engine' / 'police' / 'raw'
        self.validation_pending_path = self.config.get_pending_review_dir()
        
        # Month name to number mapping
        self.month_map = {
            'January': '01', 'February': '02', 'March': '03', 'April': '04',
            'May': '05', 'June': '06', 'July': '07', 'August': '08',
            'September': '09', 'October': '10', 'November': '11', 'December': '12'
        }
        
        # Crime category mappings for classification
        self.category_mappings = {
            # From Crime Overview sheet
            'property': ['Property Crime'],
            'violent': ['Violent Crime'],
            # From Domestics sheet
            'domestic': ['Domestic Assault'],
            # From Disorder sheet - all disorder types map to 'disorder' category
            'disorder': ['Abandoned Auto', 'Disturbance', 'Drugs', 'Indecent Act', 
                        'Intoxicated Persons', 'Landlord Tenant', 'Mental Health Concern',
                        'Neighbour Dispute', 'Noise Complaint', 'Party Complaint',
                        'Possible Gun Shots', 'Prostitution', 'Speeder', 
                        'Suspicious Person', 'Suspicious Vehicle', 'Unwanted Guest']
        }
    
    def find_crime_files(self) -> List[Path]:
        """Find all Calgary Police Service crime statistics files."""
        crime_files = []
        
        patterns = [
            "*crime*.xlsx", "*Crime*.xlsx", "*police*.xlsx", "*Police*.xlsx",
            "*Community*.xlsx", "*Statistics*.xlsx"
        ]
        
        for pattern in patterns:
            crime_files.extend(self.raw_data_path.glob(pattern))
        
        crime_files = list(set(crime_files))
        crime_files.sort()
        
        logger.info(f"Found {len(crime_files)} police/crime statistics files")
        return crime_files
    
    def parse_count_value(self, value: Any) -> float:
        """Parse crime count, handling '<5' as 2.5."""
        if pd.isna(value):
            return 0
        
        value_str = str(value).strip()
        
        # Handle '<5' cases
        if value_str == '<5':
            return 2.5
        
        # Handle regular numbers
        try:
            return float(value_str)
        except (ValueError, TypeError):
            logger.debug(f"Could not parse value: {value}")
            return 0
    
    def standardize_name(self, name: str) -> str:
        """Convert names to snake_case for consistency."""
        if pd.isna(name):
            return 'unknown'
        
        # Clean and convert to snake_case
        name = str(name).strip().lower()
        name = re.sub(r'[^\w\s]', '', name)  # Remove special chars
        name = re.sub(r'\s+', '_', name)     # Replace spaces with underscores
        return name
    
    def extract_crime_overview(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract data from Crime Overview sheet."""
        logger.info("Extracting Crime Overview data...")
        
        try:
            df = pd.read_excel(file_path, sheet_name='Crime Overview')
            records = []
            
            # Filter out non-data rows
            df = df[df['Crime Type'].notna()]
            df = df[~df['Crime Type'].str.contains('Applied filters|Total', case=False, na=False)]
            
            for _, row in df.iterrows():
                # Skip if no year data
                if pd.isna(row['Date - Year']):
                    continue
                
                # Create record
                record = {
                    'date': f"{int(row['Date - Year'])}-{self.month_map.get(row['Date - Month'], '01')}-01",
                    'year': int(row['Date - Year']),
                    'community': row['Community'] if pd.notna(row['Community']) else None,
                    'ward': row['Ward'] if pd.notna(row['Ward']) else None,
                    'police_district': row['Police District'] if pd.notna(row['Police District']) else None,
                    'crime_category': self.standardize_name(row['Crime Type'].replace(' Crime', '')),
                    'crime_type': self.standardize_name(row['Category']),
                    'incident_count': self.parse_count_value(row['Total Crime'])
                }
                
                records.append(record)
            
            logger.info(f"Extracted {len(records)} records from Crime Overview")
            return records
            
        except Exception as e:
            logger.error(f"Error extracting Crime Overview: {e}")
            return []
    
    def extract_domestics(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract data from Domestics sheet."""
        logger.info("Extracting Domestics data...")
        
        try:
            df = pd.read_excel(file_path, sheet_name='Domestics')
            records = []
            
            for _, row in df.iterrows():
                # Skip if no year data
                if pd.isna(row['Start_Datestamp - Year']):
                    continue
                
                # Create record (note: no community data for privacy)
                record = {
                    'date': f"{int(row['Start_Datestamp - Year'])}-{self.month_map.get(row['Start_Datestamp - Month'], '01')}-01",
                    'year': int(row['Start_Datestamp - Year']),
                    'community': None,  # Not provided for privacy
                    'ward': row['Ward'] if pd.notna(row['Ward']) else None,
                    'police_district': row['Police District'] if pd.notna(row['Police District']) else None,
                    'crime_category': 'domestic',
                    'crime_type': 'domestic_assault',
                    'incident_count': self.parse_count_value(row['Total Domestic'])
                }
                
                records.append(record)
            
            logger.info(f"Extracted {len(records)} records from Domestics")
            return records
            
        except Exception as e:
            logger.error(f"Error extracting Domestics: {e}")
            return []
    
    def extract_disorder(self, file_path: Path, year_filter: List[int] = None) -> List[Dict[str, Any]]:
        """Extract data from Disorder sheet."""
        logger.info("Extracting Disorder data...")
        
        try:
            df = pd.read_excel(file_path, sheet_name='Disorder')
            records = []
            
            # Filter out non-data rows
            df = df[df['Disorder Type'].notna()]
            df = df[~df['Disorder Type'].str.contains('Total', case=False, na=False)]
            
            # Apply year filter early if specified
            if year_filter:
                df = df[df['Call_Received_Timestamp - Year'].isin(year_filter)]
                logger.info(f"Filtered to {len(df)} rows for years {year_filter}")
            
            # Process rows
            for _, row in df.iterrows():
                # Skip if no year data
                if pd.isna(row['Call_Received_Timestamp - Year']):
                    continue
                
                # Create record
                record = {
                    'date': f"{int(row['Call_Received_Timestamp - Year'])}-{self.month_map.get(row['Call_Received_Timestamp - Month'], '01')}-01",
                    'year': int(row['Call_Received_Timestamp - Year']),
                    'community': row['Community'] if pd.notna(row['Community']) else None,
                    'ward': row['Ward'] if pd.notna(row['Ward']) else None,
                    'police_district': row['District'] if pd.notna(row['District']) else None,
                    'crime_category': 'disorder',
                    'crime_type': self.standardize_name(row['Disorder Type']),
                    'incident_count': self.parse_count_value(row['Total Disorder'])
                }
                
                records.append(record)
            
            logger.info(f"Extracted {len(records)} records from Disorder")
            return records
            
        except Exception as e:
            logger.error(f"Error extracting Disorder: {e}")
            return []
    
    def process_crime_files(self, year_filter: List[int] = None) -> Dict[str, Any]:
        """Process all crime statistics files."""
        logger.info("🚔 Starting Calgary Police Service crime data extraction")
        
        # Find all crime files
        crime_files = self.find_crime_files()
        
        if not crime_files:
            return {
                'success': False,
                'error': 'No crime statistics files found',
                'files_processed': 0
            }
        
        all_records = []
        
        # Process each file
        for file_path in crime_files:
            logger.info(f"Processing {file_path.name}...")
            
            # Extract from all three sheets
            crime_records = self.extract_crime_overview(file_path)
            domestic_records = self.extract_domestics(file_path)
            disorder_records = self.extract_disorder(file_path, year_filter)
            
            # Combine all records
            all_records.extend(crime_records)
            all_records.extend(domestic_records)
            all_records.extend(disorder_records)
        
        # Filter by year if specified
        if year_filter:
            all_records = [r for r in all_records if r['year'] in year_filter]
            logger.info(f"Filtered to years {year_filter}: {len(all_records)} records")
        
        # Save to validation pipeline
        csv_path = None
        if all_records:
            csv_path = self.save_to_validation(all_records)
        
        # Generate summary statistics
        summary = self.generate_summary(all_records)
        
        logger.info(f"🚔 Crime extraction complete:")
        logger.info(f"  Total records extracted: {len(all_records)}")
        logger.info(f"  Date range: {summary['date_range']}")
        logger.info(f"  Crime categories: {len(summary['categories'])}")
        logger.info(f"  Communities: {summary['total_communities']}")
        if csv_path:
            logger.info(f"  Output saved to: {csv_path}")
        
        return {
            'success': True,
            'records': all_records,
            'files_processed': len(crime_files),
            'total_records': len(all_records),
            'summary': summary,
            'csv_path': csv_path
        }
    
    def generate_summary(self, records: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics from records."""
        if not records:
            return {
                'date_range': 'No data',
                'categories': {},
                'total_communities': 0
            }
        
        # Date range
        dates = [r['date'] for r in records]
        date_range = f"{min(dates)} to {max(dates)}"
        
        # Categories breakdown
        categories = {}
        for record in records:
            cat = record['crime_category']
            if cat not in categories:
                categories[cat] = {
                    'count': 0,
                    'total_incidents': 0,
                    'crime_types': set()
                }
            categories[cat]['count'] += 1
            categories[cat]['total_incidents'] += record['incident_count']
            categories[cat]['crime_types'].add(record['crime_type'])
        
        # Convert sets to counts for JSON serialization
        for cat in categories:
            categories[cat]['crime_types'] = len(categories[cat]['crime_types'])
            categories[cat]['total_incidents'] = int(categories[cat]['total_incidents'])
        
        # Unique communities
        communities = set(r['community'] for r in records if r['community'])
        
        return {
            'date_range': date_range,
            'categories': categories,
            'total_communities': len(communities),
            'years': sorted(set(r['year'] for r in records))
        }
    
    def save_to_validation(self, records: List[Dict]) -> Optional[Path]:
        """Save crime records to validation pending directory as CSV."""
        if not records:
            logger.warning("No crime data to save")
            return None
        
        try:
            # Create DataFrame from records
            df = pd.DataFrame(records)
            
            # Sort by date, community, and crime category
            df = df.sort_values(['date', 'community', 'crime_category', 'crime_type'])
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"crime_statistics_all_years_{timestamp}.csv"
            csv_path = self.validation_pending_path / filename
            
            # Ensure directory exists
            self.validation_pending_path.mkdir(parents=True, exist_ok=True)
            
            # Save to CSV
            df.to_csv(csv_path, index=False)
            logger.info(f"✅ Saved {len(records)} crime records to {csv_path}")
            
            # Create validation report
            self._create_validation_report(records, csv_path)
            
            return csv_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save crime data: {e}")
            return None
    
    def _create_validation_report(self, records: List[Dict], csv_path: Path) -> None:
        """Create JSON validation report for the extracted data."""
        try:
            summary = self.generate_summary(records)
            
            validation_report = {
                'source': 'calgary_police_crime_statistics',
                'extraction_date': datetime.now().isoformat(),
                'records_extracted': len(records),
                'date_range': summary['date_range'],
                'years_covered': summary['years'],
                'breakdown_by_category': {
                    'property': len([r for r in records if r['crime_category'] == 'property']),
                    'violent': len([r for r in records if r['crime_category'] == 'violent']),
                    'domestic': len([r for r in records if r['crime_category'] == 'domestic']),
                    'disorder': len([r for r in records if r['crime_category'] == 'disorder'])
                },
                'categories': summary['categories'],
                'communities': summary['total_communities'],
                'sample_records': []
            }
            
            # Sample records from each category and source
            samples_added = set()
            for cat in ['violent', 'property', 'domestic', 'disorder']:
                cat_records = [r for r in records if r['crime_category'] == cat]
                if cat_records:
                    # Get one from each year if possible
                    for year in [2025, 2024, 2023]:
                        year_records = [r for r in cat_records if r['year'] == year]
                        if year_records:
                            sample = year_records[0]
                            key = f"{cat}_{year}"
                            if key not in samples_added:
                                validation_report['sample_records'].append({
                                    'date': sample['date'],
                                    'community': sample['community'],
                                    'crime_category': sample['crime_category'],
                                    'crime_type': sample['crime_type'],
                                    'incident_count': sample['incident_count']
                                })
                                samples_added.add(key)
                                break
            
            # Save validation report
            report_path = csv_path.with_suffix('.json')
            with open(report_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            
            logger.info(f"📋 Created validation report: {report_path}")
            
        except Exception as e:
            logger.warning(f"Could not create validation report: {e}")


def main():
    """Extract Calgary Police Service crime statistics."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Calgary Police Service crime statistics (all years)')
    parser.add_argument('--years', nargs='+', type=int, help='Specific years to extract (e.g., 2024 2025)')
    parser.add_argument('--test', action='store_true', help='Test mode - show file analysis only')
    args = parser.parse_args()
    
    extractor = CalgaryCrimeExtractorSimplified()
    
    if args.test:
        # Test mode - analyze files
        print("🔍 Analyzing crime statistics files...")
        crime_files = extractor.find_crime_files()
        
        if crime_files:
            print(f"\nFound {len(crime_files)} crime files:")
            for file_path in crime_files:
                print(f"  - {file_path.name}")
                print(f"    Size: {file_path.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            print("❌ No crime statistics files found")
        return
    
    # Normal extraction mode
    print("🚔 Starting Calgary Police Service crime data extraction (all years)")
    
    # Process crime files
    result = extractor.process_crime_files(year_filter=args.years)
    
    if result['success']:
        print(f"\n✅ Crime extraction completed:")
        print(f"  Files processed: {result['files_processed']}")
        print(f"  Total records: {result['total_records']:,}")
        print(f"  Date range: {result['summary']['date_range']}")
        print(f"  Years: {result['summary']['years']}")
        print(f"  Communities: {result['summary']['total_communities']}")
        
        print(f"\n📊 Category breakdown:")
        for cat, info in result['summary']['categories'].items():
            print(f"  {cat}: {info['count']:,} records, {info['total_incidents']:,} incidents, {info['crime_types']} types")
        
        if result.get('csv_path'):
            csv_path = result['csv_path']
            json_path = csv_path.with_suffix('.json')
            
            print(f"\n📂 Output files:")
            print(f"  CSV:  {csv_path}")
            print(f"  JSON: {json_path}")
            
            # Print clickable file paths
            print(f"\n📂 Click to open:")
            print(f"  file://{csv_path}")
            print(f"  file://{json_path}")
            
            # Print validation commands
            print(f"\n📋 Next steps for validation:")
            print(f"  1. Review CSV:  less {csv_path}")
            print(f"  2. Check JSON:  less {json_path}")
            print(f"  3. If approved: mv {csv_path} {csv_path.parent.parent}/approved/")
            print(f"  4. Load to DB:  cd data-engine/core && python3 load_csv_direct.py")
    else:
        print(f"❌ Crime extraction failed: {result.get('error')}")


if __name__ == "__main__":
    main()