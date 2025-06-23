#!/usr/bin/env python3
"""
Database Loading Script
Loads approved CSV files to appropriate database tables based on content analysis
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import shutil

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_manager import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / 'data-engine' / 'validation' / 'logs' / f'load_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseLoader:
    """Handles loading approved CSV files to appropriate database tables."""
    
    def __init__(self):
        self.config = get_config()
        self.db_path = self.config.get_database_path()
        self.approved_dir = self.config.get_approved_data_dir()
        self.loaded_dir = self.approved_dir / "loaded"
        
        # Ensure loaded directory exists
        self.loaded_dir.mkdir(parents=True, exist_ok=True)
        
        # Table mapping based on column signatures
        self.table_mappings = {
            'housing_city_monthly': {
                'required_columns': ['date', 'property_type', 'sales', 'new_listings', 'benchmark_price'],
                'optional_columns': ['inventory', 'days_on_market', 'median_price', 'average_price'],
                'description': 'CREB city-wide housing data'
            },
            'housing_district_monthly': {
                'required_columns': ['date', 'property_type', 'district', 'new_sales', 'benchmark_price'],
                'optional_columns': ['new_listings', 'sales_to_listings_ratio', 'inventory', 'months_supply', 'yoy_price_change', 'mom_price_change'],
                'description': 'CREB district-level housing data'
            },
            'economic_indicators_monthly': {
                'required_columns': ['date', 'indicator_type', 'value'],
                'optional_columns': ['indicator_name', 'unit', 'yoy_change', 'mom_change', 'category'],
                'description': 'Economic indicators data'
            },
            'crime_statistics_monthly': {
                'required_columns': ['date', 'community', 'crime_category'],
                'optional_columns': ['crime_type', 'incident_count', 'rate_per_1000', 'severity_index', 'population_base'],
                'description': 'Crime statistics data'
            }
        }
        
        logger.info(f"🔧 Database Loader initialized")
        logger.info(f"   Database: {self.db_path}")
        logger.info(f"   Approved CSV dir: {self.approved_dir}")
        logger.info(f"   Archive dir: {self.loaded_dir}")
    
    def identify_table(self, csv_file: Path) -> Optional[str]:
        """Identify target table based on CSV column structure."""
        try:
            # Read just the header to analyze columns
            df = pd.read_csv(csv_file, nrows=0)
            columns = set(df.columns.str.lower())
            
            logger.info(f"📋 Analyzing {csv_file.name} with columns: {sorted(columns)}")
            
            # Score each table mapping
            best_match = None
            best_score = 0
            
            for table_name, mapping in self.table_mappings.items():
                required_cols = set(col.lower() for col in mapping['required_columns'])
                optional_cols = set(col.lower() for col in mapping['optional_columns'])
                
                # Check if all required columns are present
                missing_required = required_cols - columns
                if missing_required:
                    logger.debug(f"   ❌ {table_name}: Missing required columns {missing_required}")
                    continue
                
                # Calculate match score
                present_required = len(required_cols & columns)
                present_optional = len(optional_cols & columns)
                total_possible = len(required_cols) + len(optional_cols)
                
                score = (present_required * 2 + present_optional) / (len(required_cols) * 2 + len(optional_cols))
                
                logger.debug(f"   📊 {table_name}: Score {score:.2f} ({present_required}/{len(required_cols)} required, {present_optional}/{len(optional_cols)} optional)")
                
                if score > best_score:
                    best_score = score
                    best_match = table_name
            
            if best_match:
                logger.info(f"   ✅ Best match: {best_match} (score: {best_score:.2f})")
                return best_match
            else:
                logger.warning(f"   ❌ No matching table found for {csv_file.name}")
                return None
                
        except Exception as e:
            logger.error(f"   💥 Error analyzing {csv_file.name}: {e}")
            return None
    
    def validate_csv_data(self, csv_file: Path, table_name: str) -> Tuple[bool, List[str]]:
        """Validate CSV data quality before loading."""
        try:
            df = pd.read_csv(csv_file)
            errors = []
            
            # Basic validation
            if df.empty:
                errors.append("CSV file is empty")
                return False, errors
            
            # Check for required columns
            mapping = self.table_mappings[table_name]
            required_cols = [col.lower() for col in mapping['required_columns']]
            csv_cols = [col.lower() for col in df.columns]
            
            missing_cols = set(required_cols) - set(csv_cols)
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")
            
            # Data type validation
            if 'date' in csv_cols:
                try:
                    pd.to_datetime(df['date'])
                except:
                    errors.append("Invalid date format in 'date' column")
            
            # Check for completely empty rows
            empty_rows = df.isnull().all(axis=1).sum()
            if empty_rows > 0:
                errors.append(f"Found {empty_rows} completely empty rows")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
    
    def load_to_database(self, csv_file: Path, table_name: str) -> Tuple[bool, int, str]:
        """Load CSV data to specified database table."""
        try:
            # Read CSV data
            df = pd.read_csv(csv_file)
            
            # Add metadata columns based on table type
            if table_name.startswith('housing_'):
                df['source_pdf'] = csv_file.name  # Housing tables use source_pdf
            else:
                df['source_file'] = csv_file.name  # Other tables use source_file
            
            df['extracted_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df['confidence_score'] = 1.0
            df['validation_status'] = 'approved'
            
            # Connect to database and load data
            with sqlite3.connect(self.db_path) as conn:
                # Check if table exists
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    return False, 0, f"Table {table_name} does not exist in database"
                
                # Load data
                records_loaded = len(df)
                df.to_sql(table_name, conn, if_exists='append', index=False)
                
                return True, records_loaded, "Success"
                
        except Exception as e:
            return False, 0, f"Database loading error: {str(e)}"
    
    def archive_file(self, csv_file: Path) -> bool:
        """Move loaded file to archive directory."""
        try:
            archive_path = self.loaded_dir / csv_file.name
            
            # If file already exists in archive, add timestamp
            if archive_path.exists():
                timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
                name_parts = csv_file.stem, timestamp, csv_file.suffix
                archive_path = self.loaded_dir / f"{name_parts[0]}{name_parts[1]}{name_parts[2]}"
            
            shutil.move(str(csv_file), str(archive_path))
            logger.info(f"   📦 Archived to {archive_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"   💥 Failed to archive {csv_file.name}: {e}")
            return False
    
    def process_approved_files(self) -> Dict[str, any]:
        """Process all approved CSV files."""
        summary = {
            'total_files': 0,
            'loaded_files': 0,
            'failed_files': 0,
            'total_records': 0,
            'results': []
        }
        
        # Find all CSV files in approved directory
        csv_files = list(self.approved_dir.glob("*.csv"))
        summary['total_files'] = len(csv_files)
        
        if not csv_files:
            logger.info("📄 No CSV files found in approved directory")
            return summary
        
        logger.info(f"📄 Found {len(csv_files)} CSV files to process")
        
        for csv_file in csv_files:
            logger.info(f"\n🔄 Processing {csv_file.name}")
            
            # Identify target table
            table_name = self.identify_table(csv_file)
            if not table_name:
                logger.error(f"   ❌ Failed to identify table for {csv_file.name}")
                summary['failed_files'] += 1
                summary['results'].append({
                    'file': csv_file.name,
                    'status': 'failed',
                    'error': 'Could not identify target table',
                    'records': 0
                })
                continue
            
            # Validate data
            is_valid, validation_errors = self.validate_csv_data(csv_file, table_name)
            if not is_valid:
                logger.error(f"   ❌ Validation failed for {csv_file.name}: {'; '.join(validation_errors)}")
                summary['failed_files'] += 1
                summary['results'].append({
                    'file': csv_file.name,
                    'status': 'failed',
                    'error': f"Validation errors: {'; '.join(validation_errors)}",
                    'records': 0
                })
                continue
            
            # Load to database
            success, records_loaded, error_msg = self.load_to_database(csv_file, table_name)
            if not success:
                logger.error(f"   ❌ Database loading failed for {csv_file.name}: {error_msg}")
                summary['failed_files'] += 1
                summary['results'].append({
                    'file': csv_file.name,
                    'status': 'failed',
                    'error': error_msg,
                    'records': 0
                })
                continue
            
            # Archive file
            if self.archive_file(csv_file):
                logger.info(f"   ✅ Loaded {records_loaded} records to {table_name} from {csv_file.name}")
                summary['loaded_files'] += 1
                summary['total_records'] += records_loaded
                summary['results'].append({
                    'file': csv_file.name,
                    'status': 'success',
                    'table': table_name,
                    'records': records_loaded
                })
            else:
                logger.warning(f"   ⚠️  Data loaded but archiving failed for {csv_file.name}")
                summary['loaded_files'] += 1
                summary['total_records'] += records_loaded
                summary['results'].append({
                    'file': csv_file.name,
                    'status': 'partial_success',
                    'table': table_name,
                    'records': records_loaded,
                    'warning': 'Failed to archive file'
                })
        
        return summary
    
    def print_summary(self, summary: Dict[str, any]):
        """Print loading summary."""
        print(f"\n{'='*60}")
        print(f"📊 DATABASE LOADING SUMMARY")
        print(f"{'='*60}")
        print(f"Total files processed: {summary['total_files']}")
        print(f"Successfully loaded: {summary['loaded_files']}")
        print(f"Failed: {summary['failed_files']}")
        print(f"Total records loaded: {summary['total_records']}")
        
        if summary['results']:
            print(f"\n📋 DETAILED RESULTS:")
            for result in summary['results']:
                if result['status'] == 'success':
                    print(f"   ✅ Loaded {result['records']} records to {result['table']} from {result['file']}")
                elif result['status'] == 'partial_success':
                    print(f"   ⚠️  Loaded {result['records']} records to {result['table']} from {result['file']} (Warning: {result['warning']})")
                else:
                    print(f"   ❌ Failed to load {result['file']}: {result['error']}")
        
        print(f"{'='*60}")

def main():
    """Main execution function."""
    print("🚀 Starting database loading process...")
    
    try:
        loader = DatabaseLoader()
        summary = loader.process_approved_files()
        loader.print_summary(summary)
        
        # Exit with appropriate code
        if summary['failed_files'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        print(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()