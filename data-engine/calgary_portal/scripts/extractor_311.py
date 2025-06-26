#!/usr/bin/env python3
"""
Calgary 311 Service Requests Extractor
Extracts 311 service request data from Calgary Open Data Portal API
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import re
from datetime import datetime, timedelta
import json
import sys
import requests
from time import sleep

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Calgary311Extractor:
    """Extracts 311 service request data from Calgary Open Data Portal."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.raw_data_path = self.config.get_project_root() / 'data-engine' / 'calgary_portal' / 'raw'
        self.validation_pending_path = self.config.get_pending_review_dir()
        
        # API configuration
        self.base_url = "https://data.calgary.ca/resource"
        self.dataset_id = "iahh-g8bj"  # Full historical dataset
        self.current_year_id = "arf6-qysm"  # Current year only (better performance)
        
        # Load dataset registry
        registry_path = self.config.get_project_root() / 'data-engine' / 'calgary_portal' / 'registry' / 'datasets.json'
        with open(registry_path, 'r') as f:
            self.registry = json.load(f)
        
        self.dataset_config = self.registry.get('311_service_requests', {})
    
    def _get_existing_request_ids(self, start_date: str, end_date: str) -> set:
        """Get existing service request IDs from database for a date range."""
        try:
            import sqlite3
            db_path = self.config.get_database_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='service_requests_311'
            """)
            
            if not cursor.fetchone():
                logger.info("📊 Table service_requests_311 doesn't exist yet")
                return set()
            
            # Get existing IDs
            cursor.execute("""
                SELECT service_request_id 
                FROM service_requests_311 
                WHERE date >= ? AND date <= ?
            """, (start_date, end_date))
            
            existing_ids = {row[0] for row in cursor.fetchall()}
            conn.close()
            
            return existing_ids
            
        except Exception as e:
            logger.warning(f"Could not check existing records: {e}")
            return set()
        
    def fetch_data(self, start_date: str = None, end_date: str = None, limit: int = 10000) -> List[Dict[str, Any]]:
        """Fetch 311 data from the API with date filtering."""
        
        all_records = []
        offset = 0
        
        # Build query parameters
        params = {
            '$limit': min(limit, 50000),
            '$offset': offset,
            '$order': 'requested_date DESC'
        }
        
        # Add date filtering if specified
        where_clauses = []
        if start_date:
            where_clauses.append(f"requested_date >= '{start_date}'")
        if end_date:
            where_clauses.append(f"requested_date <= '{end_date}'")
        
        if where_clauses:
            params['$where'] = ' AND '.join(where_clauses)
        
        # Determine which dataset to use
        current_year = datetime.now().year
        if start_date and start_date.startswith(str(current_year)):
            dataset_id = self.current_year_id
            logger.info(f"Using current year dataset for better performance")
        else:
            dataset_id = self.dataset_id
        
        url = f"{self.base_url}/{dataset_id}.json"
        
        # Fetch data in batches
        total_fetched = 0
        while total_fetched < limit:
            try:
                params['$offset'] = offset
                
                logger.info(f"Fetching batch: offset={offset}, limit={params['$limit']}")
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                batch = response.json()
                if not batch:
                    logger.info("No more records to fetch")
                    break
                
                all_records.extend(batch)
                total_fetched += len(batch)
                offset += len(batch)
                
                logger.info(f"Fetched {len(batch)} records, total: {total_fetched}")
                
                # Be nice to the API
                if len(batch) == params['$limit']:
                    sleep(1)
                else:
                    break  # Got less than limit, so we're done
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break
        
        return all_records
    
    def process_records(self, records: List[Dict]) -> pd.DataFrame:
        """Process raw API records into clean DataFrame."""
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Apply column mapping from registry
        column_mapping = self.dataset_config.get('column_mapping', {})
        df.rename(columns=column_mapping, inplace=True)
        
        # Ensure required columns exist
        required_cols = self.dataset_config.get('required_columns', [])
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing required columns: {missing_cols}")
        
        # Convert date column to standard format
        date_col = self.dataset_config.get('date_column', 'requested_date')
        if date_col in df.columns:
            df['date'] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')
        
        # Extract year and month for filtering
        if 'date' in df.columns:
            df['year'] = pd.to_datetime(df['date']).dt.year
            df['month'] = pd.to_datetime(df['date']).dt.month
        
        # Handle missing values
        df['community_name'] = df.get('community_name', '').fillna('UNKNOWN')
        df['community_code'] = df.get('community_code', '').fillna('UNKNOWN')
        
        # Convert lat/lon to float
        for coord in ['latitude', 'longitude']:
            if coord in df.columns:
                df[coord] = pd.to_numeric(df[coord], errors='coerce')
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date', ascending=False)
        
        return df
    
    def save_to_validation(self, df: pd.DataFrame, extraction_type: str = "full") -> Optional[Path]:
        """Save DataFrame to validation pending directory."""
        
        if df.empty:
            logger.warning("No data to save")
            return None
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"311_service_requests_{extraction_type}_{timestamp}.csv"
            csv_path = self.validation_pending_path / filename
            
            # Save CSV
            self.validation_pending_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(csv_path, index=False)
            logger.info(f"✅ Saved {len(df)} records to {csv_path}")
            
            # Create validation report
            self._create_validation_report(df, csv_path, extraction_type)
            
            return csv_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save data: {e}")
            return None
    
    def _create_validation_report(self, df: pd.DataFrame, csv_path: Path, extraction_type: str) -> None:
        """Create JSON validation report."""
        
        try:
            # Service type breakdown
            service_counts = df['service_name'].value_counts().head(10).to_dict()
            
            # Status breakdown
            status_counts = df.get('status_description', pd.Series()).value_counts().to_dict()
            
            # Community breakdown (top 10)
            community_counts = df.get('community_name', pd.Series()).value_counts().head(10).to_dict()
            
            validation_report = {
                'source': '311_service_requests',
                'extraction_type': extraction_type,
                'extraction_date': datetime.now().isoformat(),
                'records_extracted': len(df),
                'date_range': f"{df['date'].min()} to {df['date'].max()}",
                'unique_services': df['service_name'].nunique(),
                'top_services': service_counts,
                'status_breakdown': status_counts,
                'top_communities': community_counts,
                'geographic_coverage': {
                    'has_coordinates': df[['latitude', 'longitude']].notna().all(axis=1).sum(),
                    'missing_coordinates': df[['latitude', 'longitude']].isna().any(axis=1).sum()
                },
                'sample_records': []
            }
            
            # Add sample records
            sample_cols = ['date', 'service_request_id', 'service_name', 'status_description', 
                          'community_name', 'agency_responsible']
            available_cols = [col for col in sample_cols if col in df.columns]
            
            for _, row in df.head(5).iterrows():
                sample = {}
                for col in available_cols:
                    val = row.get(col, '')
                    # Convert numpy types to Python types for JSON serialization
                    if hasattr(val, 'item'):
                        val = val.item()
                    sample[col] = str(val) if val is not None else ''
                validation_report['sample_records'].append(sample)
            
            # Save validation report
            report_path = csv_path.with_suffix('.json')
            with open(report_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            
            logger.info(f"📋 Created validation report: {report_path}")
            
        except Exception as e:
            logger.warning(f"Could not create validation report: {e}")
    
    def extract_recent_data(self, days_back: int = 30) -> Dict[str, Any]:
        """Extract recent 311 data (last N days)."""
        
        logger.info(f"🚔 Extracting 311 data from last {days_back} days")
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Check what we already have in the database
        existing_ids = self._get_existing_request_ids(start_date, end_date)
        logger.info(f"📊 Found {len(existing_ids)} existing records in database for this period")
        
        # Fetch data
        records = self.fetch_data(start_date=start_date, end_date=end_date)
        
        if not records:
            return {
                'success': False,
                'error': 'No data fetched from API',
                'records': 0
            }
        
        # Process records
        df = self.process_records(records)
        
        # Filter out existing records (for new inserts)
        new_records = df[~df['service_request_id'].isin(existing_ids)]
        updated_records = df[df['service_request_id'].isin(existing_ids)]
        
        logger.info(f"📊 New records: {len(new_records)}, Updated records: {len(updated_records)}")
        
        # Save both new and updated records for validation
        # In production, we might handle updates differently
        csv_path = self.save_to_validation(df, f"last_{days_back}_days")
        
        # Show summary
        self._print_extraction_summary(df, csv_path)
        
        return {
            'success': True,
            'total_records': len(df),
            'new_records': len(new_records),
            'updated_records': len(updated_records),
            'csv_path': csv_path,
            'date_range': f"{start_date} to {end_date}"
        }
    
    def extract_monthly_data(self, year: int, month: int) -> Dict[str, Any]:
        """Extract 311 data for a specific month."""
        
        logger.info(f"🚔 Extracting 311 data for {year}-{month:02d}")
        
        # Calculate date range
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            next_month = datetime(year, month, 1) + timedelta(days=32)
            end_date = (next_month.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Fetch data
        records = self.fetch_data(start_date=start_date, end_date=end_date, limit=50000)
        
        if not records:
            return {
                'success': False,
                'error': 'No data fetched from API',
                'records': 0
            }
        
        # Process records
        df = self.process_records(records)
        
        # Save to validation
        csv_path = self.save_to_validation(df, f"{year}_{month:02d}")
        
        # Show summary
        self._print_extraction_summary(df, csv_path)
        
        return {
            'success': True,
            'records': len(df),
            'csv_path': csv_path,
            'date_range': f"{start_date} to {end_date}"
        }
    
    def _print_extraction_summary(self, df: pd.DataFrame, csv_path: Path) -> None:
        """Print extraction summary with formatting."""
        
        print("\n" + "="*70)
        print("📊 311 SERVICE REQUESTS EXTRACTION SUMMARY")
        print("="*70)
        print(f"\n📁 Source: Calgary Open Data Portal API")
        print(f"📅 Period: {df['date'].min()} to {df['date'].max()}")
        print(f"📈 Total records: {len(df):,}")
        
        print(f"\n🏙️ TOP SERVICE TYPES:")
        print("-" * 50)
        for service, count in df['service_name'].value_counts().head(5).items():
            print(f"  {service[:40]:40} - {count:,} requests")
        
        print(f"\n🏘️ TOP COMMUNITIES:")
        print("-" * 50)
        for community, count in df.get('community_name', pd.Series()).value_counts().head(5).items():
            print(f"  {community[:30]:30} - {count:,} requests")
        
        print(f"\n📊 STATUS BREAKDOWN:")
        print("-" * 50)
        status_counts = df.get('status_description', pd.Series()).value_counts()
        for status, count in status_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {status:20} - {count:,} ({percentage:.1f}%)")
        
        print("\n" + "="*70)
        
        if csv_path:
            json_path = csv_path.with_suffix('.json')
            print(f"\n📂 Output files:")
            print(f"  CSV:  {csv_path}")
            print(f"  JSON: {json_path}")
            
            print(f"\n📂 Click to open:")
            print(f"  file://{csv_path}")
            print(f"  file://{json_path}")
            
            print(f"\n📋 Next steps for validation:")
            print(f"  1. Review CSV:  less {csv_path}")
            print(f"  2. Check JSON:  less {json_path}")
            print(f"  3. If approved: mv {csv_path} {csv_path.parent.parent}/approved/")
            print(f"  4. Load to DB:  cd data-engine/cli && python3 load_csv_direct.py")

def main():
    """Extract 311 service request data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Calgary 311 service request data')
    parser.add_argument('--days', type=int, help='Extract last N days of data')
    parser.add_argument('--month', type=int, help='Month to extract (1-12)')
    parser.add_argument('--year', type=int, help='Year to extract')
    parser.add_argument('--test', action='store_true', help='Test mode - fetch small sample')
    args = parser.parse_args()
    
    extractor = Calgary311Extractor()
    
    if args.test:
        print("🔍 Test mode - fetching last 7 days as sample...")
        result = extractor.extract_recent_data(days_back=7)
    elif args.month and args.year:
        result = extractor.extract_monthly_data(args.year, args.month)
    elif args.days:
        result = extractor.extract_recent_data(days_back=args.days)
    else:
        # Default: last 30 days
        result = extractor.extract_recent_data(days_back=30)
    
    if result['success']:
        print(f"\n✅ Extraction completed successfully!")
    else:
        print(f"\n❌ Extraction failed: {result.get('error')}")

if __name__ == "__main__":
    main()