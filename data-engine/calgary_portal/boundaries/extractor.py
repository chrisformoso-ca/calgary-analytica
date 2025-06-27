#!/usr/bin/env python3
"""
Calgary Community Boundaries Extractor
Extracts community boundaries, districts, and sectors geospatial data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import json
import sys
import requests
from datetime import datetime

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CalgaryBoundariesExtractor:
    """Extracts geospatial boundary data from Calgary Open Data Portal."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.raw_data_path = self.config.get_project_root() / 'data-engine' / 'calgary_portal' / 'raw'
        self.validation_pending_path = self.config.get_pending_review_dir()
        
        # API configuration
        self.base_url = "https://data.calgary.ca/resource"
        
        # Load dataset registry
        registry_path = self.config.get_project_root() / 'data-engine' / 'calgary_portal' / 'registry' / 'datasets.json'
        with open(registry_path, 'r') as f:
            self.registry = json.load(f)
        
        # Boundary dataset configurations
        self.boundary_datasets = {
            'community_boundaries': self.registry.get('community_boundaries', {}),
            'community_districts': self.registry.get('community_districts', {}),
            'community_sectors': self.registry.get('community_sectors', {})
        }
    
    def fetch_boundaries(self, dataset_name: str) -> List[Dict[str, Any]]:
        """Fetch boundary data from the API."""
        
        if dataset_name not in self.boundary_datasets:
            logger.error(f"Unknown dataset: {dataset_name}")
            return []
        
        config = self.boundary_datasets[dataset_name]
        dataset_id = config.get('api_dataset_id')
        
        if not dataset_id:
            logger.error(f"No dataset ID found for {dataset_name}")
            return []
        
        url = f"{self.base_url}/{dataset_id}.json"
        
        try:
            logger.info(f"🗺️ Fetching {dataset_name} from {url}")
            
            # These datasets are small, so we can fetch all at once
            params = {'$limit': 1000}
            
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Fetched {len(data)} {dataset_name} records")
            
            # Cache raw response
            self._cache_raw_response(data, dataset_name)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return []
    
    def _cache_raw_response(self, data: List[Dict], dataset_name: str) -> None:
        """Cache raw API response for debugging."""
        
        try:
            self.raw_data_path.mkdir(parents=True, exist_ok=True)
            
            cache_file = self.raw_data_path / f"{dataset_name}_raw_{datetime.now().strftime('%Y%m%d')}.json"
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"📦 Cached raw response to {cache_file}")
            
        except Exception as e:
            logger.warning(f"Could not cache response: {e}")
    
    def process_boundaries(self, records: List[Dict], dataset_name: str) -> pd.DataFrame:
        """Process raw boundary records into clean DataFrame."""
        
        if not records:
            return pd.DataFrame()
        
        config = self.boundary_datasets[dataset_name]
        df = pd.DataFrame(records)
        
        # Apply column mapping
        column_mapping = config.get('column_mapping', {})
        df.rename(columns=column_mapping, inplace=True)
        
        # Extract multipolygon as text (for storage)
        if 'multipolygon' in df.columns:
            # Convert complex geometry to string representation
            df['multipolygon'] = df['multipolygon'].apply(
                lambda x: json.dumps(x) if isinstance(x, dict) else str(x)
            )
        
        # Add metadata
        df['dataset'] = dataset_name
        df['extracted_date'] = datetime.now().isoformat()
        
        # Sort by primary key
        id_cols = config.get('id_columns', [])
        if id_cols and id_cols[0] in df.columns:
            df = df.sort_values(id_cols[0])
        
        return df
    
    def extract_all_boundaries(self) -> Dict[str, Any]:
        """Extract all boundary datasets."""
        
        logger.info("🗺️ Starting Calgary boundary data extraction")
        
        all_results = {}
        total_records = 0
        
        for dataset_name in self.boundary_datasets:
            logger.info(f"\n📍 Processing {dataset_name}...")
            
            # Fetch data
            records = self.fetch_boundaries(dataset_name)
            
            if not records:
                logger.warning(f"⚠️ No data fetched for {dataset_name}")
                continue
            
            # Process records
            df = self.process_boundaries(records, dataset_name)
            
            # Save to validation
            csv_path = self.save_to_validation(df, dataset_name)
            
            all_results[dataset_name] = {
                'success': True,
                'records': len(df),
                'csv_path': csv_path
            }
            
            total_records += len(df)
            
            # Print dataset summary
            self._print_dataset_summary(df, dataset_name)
        
        # Print overall summary
        self._print_extraction_summary(all_results, total_records)
        
        return {
            'success': True,
            'datasets': all_results,
            'total_records': total_records
        }
    
    def save_to_validation(self, df: pd.DataFrame, dataset_name: str) -> Optional[Path]:
        """Save DataFrame to validation pending directory."""
        
        if df.empty:
            logger.warning("No data to save")
            return None
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{dataset_name}_{timestamp}.csv"
            csv_path = self.validation_pending_path / filename
            
            # Save CSV
            self.validation_pending_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(csv_path, index=False)
            logger.info(f"✅ Saved {len(df)} records to {csv_path}")
            
            # Create validation report
            self._create_validation_report(df, csv_path, dataset_name)
            
            return csv_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save data: {e}")
            return None
    
    def _create_validation_report(self, df: pd.DataFrame, csv_path: Path, dataset_name: str) -> None:
        """Create JSON validation report."""
        
        try:
            config = self.boundary_datasets[dataset_name]
            
            validation_report = {
                'source': dataset_name,
                'extraction_date': datetime.now().isoformat(),
                'records_extracted': len(df),
                'dataset_info': {
                    'api_id': config.get('api_dataset_id'),
                    'description': config.get('description'),
                    'update_frequency': config.get('update_frequency')
                },
                'columns': list(df.columns),
                'sample_records': []
            }
            
            # Add dataset-specific information
            if dataset_name == 'community_boundaries':
                validation_report['community_stats'] = {
                    'total_communities': len(df),
                    'with_residential_units': df[df.get('res_units', 0) > 0].shape[0] if 'res_units' in df else 0,
                    'sectors': df['community_sector'].value_counts().to_dict() if 'community_sector' in df else {}
                }
            elif dataset_name == 'community_districts':
                validation_report['district_count'] = len(df)
            elif dataset_name == 'community_sectors':
                validation_report['sector_count'] = len(df)
            
            # Add sample records (without multipolygon for readability)
            sample_cols = [col for col in df.columns if col != 'multipolygon']
            for _, row in df.head(3).iterrows():
                sample = {col: row.get(col, '') for col in sample_cols}
                validation_report['sample_records'].append(sample)
            
            # Save validation report
            report_path = csv_path.with_suffix('.json')
            with open(report_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            
            logger.info(f"📋 Created validation report: {report_path}")
            
        except Exception as e:
            logger.warning(f"Could not create validation report: {e}")
    
    def _print_dataset_summary(self, df: pd.DataFrame, dataset_name: str) -> None:
        """Print summary for a specific dataset."""
        
        print(f"\n{'='*50}")
        print(f"📍 {dataset_name.upper().replace('_', ' ')}")
        print(f"{'='*50}")
        print(f"Records: {len(df)}")
        
        if dataset_name == 'community_boundaries' and 'name' in df.columns:
            print(f"Sample communities: {', '.join(df['name'].head(5).tolist())}")
        elif dataset_name == 'community_districts' and 'name' in df.columns:
            print(f"Districts: {', '.join(df['name'].tolist())}")
        elif dataset_name == 'community_sectors' and 'name' in df.columns:
            print(f"Sectors: {', '.join(df['name'].tolist())}")
    
    def _print_extraction_summary(self, results: Dict, total_records: int) -> None:
        """Print overall extraction summary."""
        
        print("\n" + "="*70)
        print("🗺️ BOUNDARY DATA EXTRACTION SUMMARY")
        print("="*70)
        print(f"\n📊 Total records extracted: {total_records:,}")
        
        for dataset_name, result in results.items():
            if result['success']:
                print(f"\n✅ {dataset_name}: {result['records']} records")
                if result['csv_path']:
                    print(f"   📂 {result['csv_path'].name}")
        
        print("\n" + "="*70)
        print("\n📋 Next steps:")
        print("  1. Review the CSV files in validation/pending/")
        print("  2. Check the JSON validation reports")
        print("  3. Move approved files to validation/approved/")
        print("  4. Run: cd data-engine/cli && python3 load_csv_direct.py")
        print("\n💡 Note: These boundary files rarely change, so they can be cached locally")

def main():
    """Extract Calgary boundary data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Calgary boundary data')
    parser.add_argument('--dataset', choices=['community_boundaries', 'community_districts', 'community_sectors'],
                       help='Extract specific dataset only')
    parser.add_argument('--test', action='store_true', help='Test mode - show available datasets')
    args = parser.parse_args()
    
    extractor = CalgaryBoundariesExtractor()
    
    if args.test:
        print("🔍 Available boundary datasets:")
        for name, config in extractor.boundary_datasets.items():
            print(f"  - {name}: {config.get('description', 'No description')}")
            print(f"    API ID: {config.get('api_dataset_id')}")
        return
    
    if args.dataset:
        # Extract single dataset
        records = extractor.fetch_boundaries(args.dataset)
        if records:
            df = extractor.process_boundaries(records, args.dataset)
            csv_path = extractor.save_to_validation(df, args.dataset)
            extractor._print_dataset_summary(df, args.dataset)
    else:
        # Extract all boundaries
        result = extractor.extract_all_boundaries()
    
    print(f"\n✅ Boundary extraction completed!")

if __name__ == "__main__":
    main()