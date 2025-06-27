#!/usr/bin/env python3
"""
Calgary 311 Monthly Summary Extractor
Extracts aggregated monthly 311 data by community and category
Focuses on housing-relevant and economic indicator categories
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
from collections import defaultdict

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Calgary311MonthlyExtractor:
    """Extracts monthly aggregated 311 data for housing and economic analysis."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.raw_data_path = self.config.get_project_root() / 'data-engine' / 'calgary_portal' / 'raw'
        self.validation_pending_path = self.config.get_pending_review_dir()
        
        # API configuration
        self.base_url = "https://data.calgary.ca/resource"
        self.dataset_id = "iahh-g8bj"  # Full historical dataset
        
        # Category mappings for housing and economic indicators
        self.category_mappings = {
            # Housing Quality Indicators
            'Bylaw': [
                'Bylaw - Long Grass - Weeds Infraction',
                'Bylaw - Snow and Ice on Sidewalk',
                'Bylaw - Untidy Private Property',
                'Bylaw - Material on Public Property',
                'Bylaw - Derelict Building'
            ],
            'Waste': [
                'WRS - Cart Management',
                'WRS - Waste - Residential',
                'WRS - Recycling - Blue Cart',
                'WRS - Compost - Green Cart',
                'WRS - Missed Pickup'
            ],
            'Graffiti': [
                'Corporate - Graffiti Concerns',
                'Bylaw - Graffiti Vandalism'
            ],
            'Snow/Ice': [
                'Roads - Snow and Ice Control',
                'Bylaw - Snow and Ice on Sidewalk',
                'SNIC - Snow and Ice'
            ],
            'Parks/Trees': [
                'Parks - Tree Concern',
                'Parks - Grass Maintenance',
                'Parks - Litter or Dumping'
            ],
            
            # Economic Indicators
            'Encampments': [
                'Corporate - Encampment Concerns',
                'Alpha House - Encampment'
            ],
            'Derelict Properties': [
                'Bylaw - Derelict Building',
                'Bylaw - Derelict Vehicle',
                'CBS - Vacant/Derelict Properties'
            ],
            'Business Issues': [
                'Bylaw - Business Licence',
                'Bylaw - Commercial Maintenance'
            ],
            'Infrastructure': [
                'Roads - Pothole Maintenance',
                'Roads - Streetlight Maintenance',
                'Roads - Roadway Maintenance',
                'Water - Water Main Break'
            ],
            'Transit': [
                'CT - Transit Feedback',
                'Transit - Safety Concerns'
            ],
            'Social Stress': [
                'Bylaw - Noise Concerns',
                'CPS - Community Concerns',
                'Animal - Wildlife Under Distress'
            ]
        }
        
        # Flatten mapping for reverse lookup
        self.service_to_category = {}
        for category, services in self.category_mappings.items():
            for service in services:
                self.service_to_category[service.lower()] = category
    
    def categorize_service(self, service_name: str) -> str:
        """Categorize a service name into our defined categories."""
        if not service_name:
            return 'Other'
        
        service_lower = service_name.lower()
        
        # Direct match first
        category = self.service_to_category.get(service_lower)
        if category:
            return category
        
        # Pattern matching for variations
        patterns = {
            'Bylaw': r'bylaw',
            'Waste': r'wrs|waste|recycling|cart|garbage',
            'Graffiti': r'graffiti|vandal',
            'Snow/Ice': r'snow|ice|snic',
            'Parks/Trees': r'park|tree|grass',
            'Encampments': r'encampment|homeless',
            'Derelict Properties': r'derelict|vacant|abandon',
            'Infrastructure': r'road|pothole|street|light|water main',
            'Transit': r'transit|ct -|calgary transit',
            'Social Stress': r'noise|animal|disturbance'
        }
        
        for category, pattern in patterns.items():
            if re.search(pattern, service_lower):
                return category
        
        return 'Other'
    
    def fetch_monthly_summary(self, year: int, month: int) -> pd.DataFrame:
        """Fetch and aggregate 311 data for a specific month."""
        
        # Calculate date range
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            next_month = datetime(year, month, 1) + timedelta(days=32)
            end_date = (next_month.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"📊 Fetching 311 data for {year}-{month:02d}")
        
        # Build query for aggregated data
        query_url = f"{self.base_url}/{self.dataset_id}.json"
        
        # We'll need to fetch in batches and aggregate locally
        # due to API limitations on GROUP BY queries
        all_records = []
        offset = 0
        limit = 50000  # Max allowed
        
        while True:
            params = {
                '$where': f"requested_date >= '{start_date}' AND requested_date <= '{end_date}'",
                '$select': 'service_name, comm_code, comm_name, status_description, requested_date, closed_date',
                '$limit': limit,
                '$offset': offset,
                '$order': 'requested_date'
            }
            
            try:
                logger.info(f"Fetching batch: offset={offset}")
                response = requests.get(query_url, params=params, timeout=60)
                response.raise_for_status()
                
                batch = response.json()
                if not batch:
                    break
                
                all_records.extend(batch)
                offset += len(batch)
                
                logger.info(f"Retrieved {len(batch)} records, total: {len(all_records)}")
                
                if len(batch) < limit:
                    break
                
                sleep(1)  # Be nice to the API
                
            except Exception as e:
                logger.error(f"Error fetching data: {e}")
                break
        
        if not all_records:
            return pd.DataFrame()
        
        # Convert to DataFrame and process
        df = pd.DataFrame(all_records)
        
        # Categorize services
        df['service_category'] = df['service_name'].apply(self.categorize_service)
        
        # Calculate resolution time for closed requests
        df['requested_date'] = pd.to_datetime(df['requested_date'])
        df['closed_date'] = pd.to_datetime(df['closed_date'], errors='coerce')
        df['days_to_close'] = (df['closed_date'] - df['requested_date']).dt.days
        
        # Filter out "Other" category to focus on relevant data
        df_filtered = df[df['service_category'] != 'Other'].copy()
        
        logger.info(f"Filtered {len(df_filtered)} relevant records from {len(df)} total")
        
        return df_filtered
    
    def aggregate_monthly_data(self, df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
        """Aggregate data by community and category."""
        
        if df.empty:
            return pd.DataFrame()
        
        # Rename columns to match our expected names
        df.rename(columns={
            'comm_code': 'community_code',
            'comm_name': 'community_name'
        }, inplace=True)
        
        # Group by community and category
        aggregations = {
            'service_name': 'count',  # Total requests
            'days_to_close': ['mean', 'median']  # Resolution time
        }
        
        grouped = df.groupby(['community_code', 'community_name', 'service_category']).agg(aggregations)
        
        # Flatten column names
        grouped.columns = ['total_requests', 'avg_days_to_close', 'median_days_to_close']
        grouped = grouped.reset_index()
        
        # Add temporal columns
        grouped['year'] = year
        grouped['month'] = month
        grouped['year_month'] = f"{year}-{month:02d}"
        
        # Round numeric columns
        grouped['avg_days_to_close'] = grouped['avg_days_to_close'].round(1)
        grouped['median_days_to_close'] = grouped['median_days_to_close'].round(1)
        
        return grouped
    
    def extract_year_data(self, year: int) -> pd.DataFrame:
        """Extract full year of monthly summaries."""
        
        logger.info(f"🗓️ Extracting 311 summaries for year {year}")
        
        all_months = []
        total_requests = 0
        
        for month in range(1, 13):
            # Skip future months
            if datetime(year, month, 1) > datetime.now():
                break
            
            # Fetch and aggregate month data
            month_data = self.fetch_monthly_summary(year, month)
            
            if not month_data.empty:
                aggregated = self.aggregate_monthly_data(month_data, year, month)
                all_months.append(aggregated)
                month_total = aggregated['total_requests'].sum()
                total_requests += month_total
                
                logger.info(f"✅ {year}-{month:02d}: {len(aggregated)} community-category combinations, {month_total:,} requests")
            else:
                logger.warning(f"⚠️ No data for {year}-{month:02d}")
        
        logger.info(f"📊 Year {year} complete: {total_requests:,} total requests")
        
        if all_months:
            return pd.concat(all_months, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def save_to_validation(self, df: pd.DataFrame, description: str = "monthly") -> Optional[Path]:
        """Save DataFrame to validation pending directory."""
        
        if df.empty:
            logger.warning("No data to save")
            return None
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"311_monthly_summary_{description}_{timestamp}.csv"
            csv_path = self.validation_pending_path / filename
            
            # Save CSV
            self.validation_pending_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(csv_path, index=False)
            logger.info(f"✅ Saved {len(df)} records to {csv_path}")
            
            # Create validation report
            self._create_validation_report(df, csv_path, description)
            
            return csv_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save data: {e}")
            return None
    
    def _create_validation_report(self, df: pd.DataFrame, csv_path: Path, description: str) -> None:
        """Create JSON validation report."""
        
        try:
            # Category summary
            category_summary = df.groupby('service_category').agg({
                'total_requests': 'sum',
                'community_code': 'nunique'
            }).to_dict()
            
            # Top communities by requests
            top_communities = df.groupby('community_name').agg({
                'total_requests': 'sum'
            }).nlargest(10, 'total_requests').to_dict()['total_requests']
            
            validation_report = {
                'source': '311_monthly_summary',
                'description': description,
                'extraction_date': datetime.now().isoformat(),
                'records_extracted': len(df),
                'date_range': f"{df['year_month'].min()} to {df['year_month'].max()}",
                'unique_communities': df['community_code'].nunique(),
                'category_summary': {
                    cat: {
                        'total_requests': int(category_summary['total_requests'].get(cat, 0)),
                        'communities_affected': int(category_summary['community_code'].get(cat, 0))
                    }
                    for cat in category_summary['total_requests'].keys()
                },
                'top_communities': {k: int(v) for k, v in top_communities.items()},
                'economic_indicators': self._calculate_economic_indicators(df)
            }
            
            # Save validation report
            report_path = csv_path.with_suffix('.json')
            with open(report_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            
            logger.info(f"📋 Created validation report: {report_path}")
            
        except Exception as e:
            logger.warning(f"Could not create validation report: {e}")
    
    def _calculate_economic_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate economic stress indicators from the data."""
        
        indicators = {}
        
        # Encampment trend
        encampment_data = df[df['service_category'] == 'Encampments']
        if not encampment_data.empty:
            monthly_encampments = encampment_data.groupby('year_month')['total_requests'].sum()
            indicators['encampment_trend'] = {
                'first_month': int(monthly_encampments.iloc[0]),
                'last_month': int(monthly_encampments.iloc[-1]),
                'percent_change': round(((monthly_encampments.iloc[-1] / monthly_encampments.iloc[0]) - 1) * 100, 1)
                    if monthly_encampments.iloc[0] > 0 else 0
            }
        
        # Infrastructure stress (response times)
        infra_data = df[df['service_category'] == 'Infrastructure']
        if not infra_data.empty:
            indicators['infrastructure_response'] = {
                'avg_days_to_close': float(infra_data['avg_days_to_close'].mean()),
                'total_requests': int(infra_data['total_requests'].sum())
            }
        
        return indicators
    
    def print_extraction_summary(self, df: pd.DataFrame, csv_path: Path) -> None:
        """Print formatted extraction summary."""
        
        print("\n" + "="*70)
        print("📊 311 MONTHLY SUMMARY EXTRACTION")
        print("="*70)
        print(f"\n📅 Period: {df['year_month'].min()} to {df['year_month'].max()}")
        print(f"📈 Total records: {len(df):,}")
        print(f"🏘️ Communities: {df['community_code'].nunique()}")
        
        # Category breakdown
        print(f"\n📋 CATEGORY BREAKDOWN:")
        print("-" * 50)
        category_stats = df.groupby('service_category')['total_requests'].sum().sort_values(ascending=False)
        for category, count in category_stats.items():
            print(f"  {category:20} - {count:,} requests")
        
        # Economic indicators
        print(f"\n💰 ECONOMIC INDICATORS:")
        print("-" * 50)
        
        # Encampments
        encampment_total = df[df['service_category'] == 'Encampments']['total_requests'].sum()
        print(f"  Encampment Reports: {encampment_total:,}")
        
        # Derelict properties
        derelict_total = df[df['service_category'] == 'Derelict Properties']['total_requests'].sum()
        print(f"  Derelict Properties: {derelict_total:,}")
        
        # Infrastructure response time
        infra_data = df[df['service_category'] == 'Infrastructure']
        if not infra_data.empty:
            avg_response = infra_data['avg_days_to_close'].mean()
            print(f"  Infrastructure Avg Response: {avg_response:.1f} days")
        
        print("\n" + "="*70)
        
        if csv_path:
            print(f"\n📂 Output files:")
            print(f"  file://{csv_path}")
            print(f"  file://{csv_path.with_suffix('.json')}")
            
            print(f"\n📋 Next steps:")
            print(f"  1. Review: less {csv_path}")
            print(f"  2. Approve: mv {csv_path} {csv_path.parent.parent}/approved/")
            print(f"  3. Load: cd data-engine/cli && python3 load_csv_direct.py")

def main():
    """Extract 311 monthly summary data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Calgary 311 monthly summary data')
    parser.add_argument('--year', type=int, help='Extract specific year')
    parser.add_argument('--month', type=int, help='Extract specific month (requires --year)')
    parser.add_argument('--years', nargs='+', type=int, help='Extract multiple years (e.g., --years 2023 2024)')
    parser.add_argument('--start-year', type=int, help='Start year for range extraction')
    parser.add_argument('--end-year', type=int, help='End year for range extraction (inclusive)')
    parser.add_argument('--recent', type=int, default=12, help='Extract last N months (default: 12)')
    parser.add_argument('--test', action='store_true', help='Test mode - single month')
    args = parser.parse_args()
    
    extractor = Calgary311MonthlyExtractor()
    
    if args.test:
        print("🔍 Test mode - extracting current month...")
        now = datetime.now()
        month_data = extractor.fetch_monthly_summary(now.year, now.month)
        if not month_data.empty:
            aggregated = extractor.aggregate_monthly_data(month_data, now.year, now.month)
            csv_path = extractor.save_to_validation(aggregated, f"{now.year}_{now.month:02d}_test")
            extractor.print_extraction_summary(aggregated, csv_path)
        
    elif args.year and args.month:
        # Single month
        month_data = extractor.fetch_monthly_summary(args.year, args.month)
        if not month_data.empty:
            aggregated = extractor.aggregate_monthly_data(month_data, args.year, args.month)
            csv_path = extractor.save_to_validation(aggregated, f"{args.year}_{args.month:02d}")
            extractor.print_extraction_summary(aggregated, csv_path)
    
    elif args.year:
        # Full year
        year_data = extractor.extract_year_data(args.year)
        if not year_data.empty:
            csv_path = extractor.save_to_validation(year_data, f"{args.year}_full")
            extractor.print_extraction_summary(year_data, csv_path)
    
    elif args.years:
        # Multiple specific years
        print(f"📅 Extracting data for years: {', '.join(map(str, args.years))}")
        all_years_data = []
        
        for year in args.years:
            year_data = extractor.extract_year_data(year)
            if not year_data.empty:
                all_years_data.append(year_data)
        
        if all_years_data:
            combined = pd.concat(all_years_data, ignore_index=True)
            years_str = "_".join(map(str, args.years))
            csv_path = extractor.save_to_validation(combined, f"years_{years_str}")
            extractor.print_extraction_summary(combined, csv_path)
    
    elif args.start_year and args.end_year:
        # Year range extraction
        if args.start_year > args.end_year:
            print("❌ Error: start-year must be less than or equal to end-year")
            return
        
        print(f"📅 Extracting data for {args.start_year} to {args.end_year}")
        all_years_data = []
        
        for year in range(args.start_year, args.end_year + 1):
            year_data = extractor.extract_year_data(year)
            if not year_data.empty:
                all_years_data.append(year_data)
        
        if all_years_data:
            combined = pd.concat(all_years_data, ignore_index=True)
            csv_path = extractor.save_to_validation(combined, f"{args.start_year}_{args.end_year}_range")
            extractor.print_extraction_summary(combined, csv_path)
    
    else:
        # Recent months
        all_data = []
        current_date = datetime.now()
        
        for i in range(args.recent):
            # Go back i months
            target_date = current_date - timedelta(days=30*i)
            month_data = extractor.fetch_monthly_summary(target_date.year, target_date.month)
            
            if not month_data.empty:
                aggregated = extractor.aggregate_monthly_data(month_data, target_date.year, target_date.month)
                all_data.append(aggregated)
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            csv_path = extractor.save_to_validation(combined, f"last_{args.recent}_months")
            extractor.print_extraction_summary(combined, csv_path)
    
    print(f"\n✅ Extraction completed!")

if __name__ == "__main__":
    main()