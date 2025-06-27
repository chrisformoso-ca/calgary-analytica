#!/usr/bin/env python3
"""
Calgary Geospatial Data Batch Extractor
Extracts community boundaries, districts, and sectors from Calgary Open Data Portal

These datasets are foundational for mapping and rarely change (quarterly updates).
Extract once, use forever approach.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import requests
import json
from datetime import datetime
import sys

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CalgaryGeospatialExtractor:
    """Extracts geospatial boundary data from Calgary Open Data Portal."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.validation_pending_path = self.config.get_pending_review_dir()
        self.base_url = "https://data.calgary.ca/resource"
        
        # Load dataset registry
        registry_path = Path(__file__).parent.parent / 'registry' / 'datasets.json'
        with open(registry_path, 'r') as f:
            self.registry = json.load(f)
        
        # Define geospatial datasets to extract
        self.geospatial_datasets = [
            'community_boundaries',
            'community_districts', 
            'community_sectors'
        ]
    
    def fetch_dataset(self, dataset_id: str, config: Dict) -> List[Dict[str, Any]]:
        """Fetch all records from a geospatial dataset."""
        api_id = config['api_dataset_id']
        url = f"{self.base_url}/{api_id}.json"
        
        logger.info(f"🌐 Fetching {dataset_id} from {url}...")
        
        all_records = []
        offset = 0
        limit = 1000  # Socrata default
        
        # First try without parameters to see if it works
        try:
            response = requests.get(url)
            response.raise_for_status()
            records = response.json()
            
            if records and len(records) < 1000:
                # If we got all records in one shot, return them
                logger.info(f"✅ Fetched {len(records)} records for {dataset_id}")
                return records
        except:
            # If that fails, try with pagination
            pass
        
        # Try with pagination
        while True:
            params = {
                '$limit': limit,
                '$offset': offset
            }
            
            # Only add $order if we have a valid column
            if 'id_columns' in config and config['id_columns']:
                params['$order'] = config['id_columns'][0]
            
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                records = response.json()
                if not records:
                    break
                
                all_records.extend(records)
                logger.info(f"   Retrieved {len(records)} records (total: {len(all_records)})")
                
                if len(records) < limit:
                    break
                    
                offset += limit
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error fetching {dataset_id}: {e}")
                logger.error(f"   URL: {response.url if 'response' in locals() else url}")
                return all_records if all_records else []
        
        logger.info(f"✅ Fetched {len(all_records)} total records for {dataset_id}")
        return all_records
    
    def extract_all_geospatial(self) -> Dict[str, List[Dict]]:
        """Extract all geospatial datasets."""
        logger.info("🗺️ Starting geospatial data extraction")
        logger.info("="*70)
        
        results = {}
        
        for dataset_id in self.geospatial_datasets:
            if dataset_id not in self.registry:
                logger.warning(f"⚠️ {dataset_id} not found in registry")
                continue
            
            config = self.registry[dataset_id]
            logger.info(f"\n📊 Extracting: {config['description']}")
            
            records = self.fetch_dataset(dataset_id, config)
            if records:
                # Apply column mapping if needed
                if 'column_mapping' in config:
                    mapped_records = []
                    for record in records:
                        mapped_record = {}
                        for api_col, db_col in config['column_mapping'].items():
                            if api_col in record:
                                mapped_record[db_col] = record[api_col]
                        # Keep unmapped columns too
                        for key, value in record.items():
                            if key not in config['column_mapping']:
                                mapped_record[key] = value
                        
                        # Special handling for sectors - duplicate code as name
                        if dataset_id == 'community_sectors' and 'code' in mapped_record:
                            mapped_record['name'] = mapped_record['code']
                        
                        mapped_records.append(mapped_record)
                    records = mapped_records
                
                results[dataset_id] = records
            
        return results
    
    def save_geospatial_data(self, data: Dict[str, List[Dict]]) -> List[Path]:
        """Save each geospatial dataset to CSV."""
        saved_files = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for dataset_id, records in data.items():
            if not records:
                continue
            
            config = self.registry[dataset_id]
            df = pd.DataFrame(records)
            
            # Generate filename
            filename = f"calgary_portal_{dataset_id}_{timestamp}.csv"
            csv_path = self.validation_pending_path / filename
            
            # Save CSV
            self.validation_pending_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(csv_path, index=False)
            
            logger.info(f"💾 Saved {len(records)} {dataset_id} records to {csv_path.name}")
            
            # Create validation report
            self._create_validation_report(dataset_id, records, csv_path, config)
            
            saved_files.append(csv_path)
        
        return saved_files
    
    def _create_validation_report(self, dataset_id: str, records: List[Dict], 
                                  csv_path: Path, config: Dict) -> None:
        """Create JSON validation report for geospatial data."""
        try:
            # Sample the multipolygon field to show it's present
            sample_records = []
            for record in records[:5]:  # First 5 records
                sample = {k: v for k, v in record.items() if k != 'multipolygon'}
                sample['has_multipolygon'] = 'multipolygon' in record and record['multipolygon'] is not None
                sample_records.append(sample)
            
            validation_report = {
                'source': f'calgary_portal_{dataset_id}',
                'extraction_date': datetime.now().isoformat(),
                'dataset_id': config['api_dataset_id'],
                'description': config['description'],
                'records_extracted': len(records),
                'geospatial': True,
                'update_frequency': config.get('update_frequency', 'quarterly'),
                'sample_records': sample_records,
                'fields_extracted': list(records[0].keys()) if records else []
            }
            
            report_path = csv_path.with_suffix('.json')
            with open(report_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            
            logger.info(f"📋 Created validation report: {report_path.name}")
            
        except Exception as e:
            logger.warning(f"Could not create validation report: {e}")
    
    def show_extraction_summary(self, data: Dict[str, List[Dict]], saved_files: List[Path]) -> None:
        """Display extraction summary."""
        print("\n" + "="*70)
        print("🗺️ GEOSPATIAL EXTRACTION SUMMARY")
        print("="*70)
        
        total_records = sum(len(records) for records in data.values())
        print(f"\n📊 Total Records Extracted: {total_records:,}")
        print("-" * 50)
        
        for dataset_id, records in data.items():
            if records:
                config = self.registry[dataset_id]
                print(f"\n{dataset_id}:")
                print(f"  Description: {config['description']}")
                print(f"  Records: {len(records):,}")
                print(f"  Update frequency: {config.get('update_frequency', 'quarterly')}")
                
                # Show sample record fields (excluding multipolygon)
                if records:
                    fields = [k for k in records[0].keys() if k != 'multipolygon']
                    print(f"  Fields: {', '.join(fields[:10])}")
                    if len(fields) > 10:
                        print(f"          ... and {len(fields)-10} more")
        
        print("\n" + "="*70)
        
        if saved_files:
            print(f"\n📂 Output files saved to: {saved_files[0].parent}")
            for path in saved_files:
                print(f"  - {path.name}")
            
            print(f"\n📋 Next steps for validation:")
            print(f"  1. Review sample records in JSON files")
            print(f"  2. Quick validation: python3 data-engine/cli/validate_pending.py --list")
            print(f"  3. Bulk approve: mv {saved_files[0].parent}/*.csv {saved_files[0].parent.parent}/approved/")
            print(f"  4. Load to DB: cd data-engine/cli && python3 load_csv_direct.py")
            
            print(f"\n💡 Note: These are foundational geospatial datasets that rarely change.")
            print(f"   Once validated and loaded, they can be cached for mapping applications.")


def main():
    """Extract all geospatial data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Calgary geospatial boundary data')
    parser.add_argument('--test', action='store_true', help='Test mode - show what would be extracted')
    args = parser.parse_args()
    
    extractor = CalgaryGeospatialExtractor()
    
    if args.test:
        print("🔍 Test mode - datasets to extract:")
        for dataset_id in extractor.geospatial_datasets:
            if dataset_id in extractor.registry:
                config = extractor.registry[dataset_id]
                print(f"\n{dataset_id}:")
                print(f"  API ID: {config['api_dataset_id']}")
                print(f"  Description: {config['description']}")
                print(f"  Table: {config['table_name']}")
        return
    
    # Extract all geospatial data
    data = extractor.extract_all_geospatial()
    
    if data:
        # Save to validation
        saved_files = extractor.save_geospatial_data(data)
        
        # Show summary
        extractor.show_extraction_summary(data, saved_files)
    else:
        print("❌ No geospatial data extracted")


if __name__ == "__main__":
    main()