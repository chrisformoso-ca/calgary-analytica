#!/usr/bin/env python3
"""
Simple CSV Loader for Approved Data
Loads CSV files directly from approved/ to database without complex validation structure
"""

import sqlite3
import pandas as pd
from pathlib import Path
import logging
import sys
from datetime import datetime
import shutil
import json

# Add project root for config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.config_manager import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleCSVLoader:
    """Load approved CSV files directly to database."""
    
    def __init__(self):
        self.config = get_config()
        self.db_path = self.config.get_database_path()
        self.approved_dir = self.config.get_approved_data_dir()
        self.processed_dir = self.approved_dir.parent / "processed"
        self.reports_dir = self.approved_dir.parent / "reports"
        
        # Create directories if they don't exist
        self.processed_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Create database connection
        self.conn = sqlite3.connect(self.db_path)
        
        # Load dataset registry if available
        self.dataset_registry = self._load_dataset_registry()
    
    def _load_dataset_registry(self):
        """Load dataset registry from Calgary Portal if available."""
        registry_path = self.config.get_project_root() / 'data-engine' / 'calgary_portal' / 'registry' / 'datasets.json'
        
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
                logger.info(f"📋 Loaded dataset registry with {len(registry)} datasets")
                return registry
            except Exception as e:
                logger.warning(f"Could not load dataset registry: {e}")
                return {}
        else:
            logger.debug("No dataset registry found, using default table detection")
            return {}
        
    def load_all_csvs(self):
        """Load all CSV files from approved directory."""
        logger.info("🔄 Loading CSV files from approved directory...")
        
        if not self.approved_dir.exists():
            logger.warning("No approved data directory found")
            return {"loaded": 0, "errors": 0}
        
        csv_files = list(self.approved_dir.glob("*.csv"))
        if not csv_files:
            logger.info("No CSV files to process")
            return {"loaded": 0, "errors": 0}
        
        total_loaded = 0
        error_count = 0
        
        for csv_file in csv_files:
            try:
                result = self._load_single_csv(csv_file)
                if result["success"]:
                    total_loaded += result["records_loaded"]
                    logger.info(f"✅ Loaded {result['records_loaded']} records from {csv_file.name} to {result['table']}")
                    
                    # Archive the processed files (CSV and JSON)
                    self._archive_files(csv_file)
                else:
                    error_count += 1
                    logger.error(f"❌ Failed to load {csv_file.name}: {result['error']}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing {csv_file.name}: {e}")
        
        logger.info(f"📊 Summary: {total_loaded} records loaded, {error_count} errors")
        return {"loaded": total_loaded, "errors": error_count}
    
    def _load_single_csv(self, csv_file: Path):
        """Load a single CSV file to the appropriate table."""
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            
            if df.empty:
                return {"success": False, "error": "Empty CSV file"}
            
            # Standardize column names (handle case variations)
            df.columns = df.columns.str.lower()
            
            # Determine target table
            target_table = self._determine_target_table(df, csv_file.name)
            
            # Debug: Print what table was detected
            logger.info(f"🔍 File: {csv_file.name} -> Detected table: {target_table}")
            
            if not target_table:
                return {"success": False, "error": "Could not determine target table"}
            
            # Prepare data for loading
            df_prepared = self._prepare_dataframe(df, target_table, csv_file.name)
            
            if df_prepared.empty:
                return {"success": False, "error": "No valid data after preparation"}
            
            # Load to database
            records_loaded = len(df_prepared)
            
            # Try to handle duplicates gracefully for datasets with unique constraints
            if target_table in ['service_requests_311', 'building_permits', 'business_licences', 'rental_market_annual', 'rental_listings_snapshot']:
                # Use INSERT OR REPLACE for datasets with unique constraints
                # For rental data, this handles overlapping years (CMHC) and weekly snapshots (RentFaster)
                df_prepared.to_sql(target_table, self.conn, if_exists='append', index=False, method='multi')
            else:
                df_prepared.to_sql(target_table, self.conn, if_exists='append', index=False)
            
            self.conn.commit()
            
            logger.info(f"📊 Loaded {records_loaded} records to {target_table}")
            return {"success": True, "records_loaded": records_loaded, "table": target_table}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _determine_target_table(self, df: pd.DataFrame, filename: str) -> str:
        """Determine the appropriate database table for the data."""
        columns = set(df.columns)
        
        # First, check dataset registry if available
        if self.dataset_registry:
            # Try to match by filename pattern
            for dataset_id, config in self.dataset_registry.items():
                # Check if filename contains the dataset ID
                if dataset_id in filename.lower():
                    table_name = config.get('table_name')
                    if table_name:
                        logger.info(f"📋 Matched {filename} to {table_name} via registry")
                        return table_name
                
                # Also check by required columns
                required_cols = config.get('required_columns', [])
                if required_cols and all(col in columns for col in required_cols):
                    table_name = config.get('table_name')
                    if table_name:
                        logger.info(f"📋 Matched by columns to {table_name} via registry")
                        return table_name
        
        # Fallback to original logic for existing sources
        # Check for CREB housing data
        if any(col in columns for col in ['propertytype', 'benchmarkprice', 'sales']):
            # Check if it's district data
            if 'district' in columns:
                return 'housing_district_monthly'
            else:
                return 'housing_city_monthly'
        
        # Check for economic indicators
        elif any(col in columns for col in ['indicatorname', 'economicindicator', 'unemploymentrate']):
            return 'economic_indicators_monthly'
        
        # Check for RentFaster data (must come before crime statistics due to 'community' column)
        elif any(col in columns for col in ['listing_id', 'extraction_week']):
            return 'rental_listings_snapshot'
        
        # Check for CMHC rental data
        elif any(col in columns for col in ['metric_type', 'bedroom_type', 'quality_indicator']):
            return 'rental_market_annual'
        
        # Check for crime statistics
        elif any(col in columns for col in ['crimetype', 'incidentcount', 'community']):
            return 'crime_statistics_monthly'
        
        # Fallback based on filename
        elif 'economic' in filename.lower():
            return 'economic_indicators_monthly'
        elif 'crime' in filename.lower():
            return 'crime_statistics_monthly'
        elif 'cmhc' in filename.lower():
            return 'rental_market_annual'
        elif 'rentfaster' in filename.lower():
            return 'rental_listings_snapshot'
        elif 'creb' in filename.lower() or 'housing' in filename.lower():
            if 'district' in filename.lower():
                return 'housing_district_monthly'
            else:
                return 'housing_city_monthly'
        
        return None
    
    def _prepare_dataframe(self, df: pd.DataFrame, target_table: str, filename: str) -> pd.DataFrame:
        """Prepare dataframe for loading to specific table."""
        df_prepared = df.copy()
        
        # Check if we have registry mapping for this dataset
        registry_mapping = {}
        if self.dataset_registry:
            # Find matching dataset config
            for dataset_id, config in self.dataset_registry.items():
                if config.get('table_name') == target_table or dataset_id in filename.lower():
                    registry_mapping = config.get('column_mapping', {})
                    if registry_mapping:
                        logger.info(f"📋 Using column mapping from registry for {dataset_id}")
                        break
        
        # Combine registry mapping with default mapping
        column_mapping = {
            'propertytype': 'property_type',
            'newlistings': 'new_listings',
            'daysonmarket': 'days_on_market',
            'benchmarkprice': 'benchmark_price',
            'medianprice': 'median_price',
            'averageprice': 'average_price',
            'newsales': 'new_sales',
            'salestolistingsratio': 'sales_to_listings_ratio',
            'monthssupply': 'months_supply',
            'yoypricechange': 'yoy_price_change',
            'mompricechange': 'mom_price_change',
            'indicatorname': 'indicator_name',
            'indicatortype': 'indicator_type',
            'yoychange': 'yoy_change',
            'momchange': 'mom_change',
            'sourcefile': 'source_file',
            'extracteddate': 'extracted_date',
            'extractiondate': 'extracted_date',
            'confidencescore': 'confidence_score',
            'validationstatus': 'validation_status',
            'valuetype': 'value_type'
        }
        
        # Registry mapping takes precedence
        column_mapping.update(registry_mapping)
        
        # Apply column mapping
        df_prepared.rename(columns=column_mapping, inplace=True)
        
        # Handle date column variations
        if 'Date' in df_prepared.columns:
            df_prepared.rename(columns={'Date': 'date'}, inplace=True)
        
        # Add metadata columns (table-specific)
        if target_table in ['housing_city_monthly', 'housing_district_monthly']:
            df_prepared['source_pdf'] = filename
        elif target_table == 'crime_statistics_monthly':
            df_prepared['source_file'] = filename
        
        # Only add these if they don't already exist (economic data may already have them)
        # Skip metadata columns for 311 monthly data, rental data, and economic data (simplified schemas)
        if target_table not in ['service_requests_311_monthly', 'rental_market_annual', 'rental_listings_snapshot', 'economic_indicators_monthly']:
            if 'extracted_date' not in df_prepared.columns:
                df_prepared['extracted_date'] = datetime.now().isoformat()
            if 'confidence_score' not in df_prepared.columns:
                df_prepared['confidence_score'] = 1.0  # Human approved
            if 'validation_status' not in df_prepared.columns:
                df_prepared['validation_status'] = 'approved'
        
        # Add validation status for rental data
        if target_table == 'rental_market_annual' and 'validation_status' not in df_prepared.columns:
            df_prepared['validation_status'] = 'approved'
        
        # Table-specific preparations
        if target_table == 'service_requests_311_monthly':
            # 311 data specific handling
            initial_count = len(df_prepared)
            df_prepared = df_prepared.dropna(subset=['community_code'])
            filtered_count = initial_count - len(df_prepared)
            if filtered_count > 0:
                logger.info(f"   Filtered out {filtered_count} rows with null community_code")
        elif target_table == 'housing_city_monthly':
            # Ensure required columns exist
            required_cols = ['date', 'property_type', 'sales', 'new_listings', 'inventory', 
                           'days_on_market', 'benchmark_price', 'median_price', 'average_price']
            
            # Check if all required columns exist
            missing_cols = [col for col in required_cols if col not in df_prepared.columns]
            if missing_cols:
                logger.warning(f"Missing columns for city data: {missing_cols}")
            
        elif target_table == 'housing_district_monthly':
            # Map 'sales' to 'new_sales' if needed
            if 'sales' in df_prepared.columns and 'new_sales' not in df_prepared.columns:
                df_prepared['new_sales'] = df_prepared['sales']
            
            # Remove extra columns that aren't in the database schema
            extra_columns = ['month', 'year']
            for col in extra_columns:
                if col in df_prepared.columns:
                    df_prepared = df_prepared.drop(columns=[col])
            
            # Convert percentage strings to floats
            percentage_columns = ['sales_to_listings_ratio', 'yoy_price_change', 'mom_price_change']
            for col in percentage_columns:
                if col in df_prepared.columns and df_prepared[col].dtype == 'object':
                    # Remove % sign and convert to float
                    df_prepared[col] = df_prepared[col].str.replace('%', '').astype(float)
            
            # Ensure date format
            if 'date' in df_prepared.columns and df_prepared['date'].dtype == 'object':
                # Convert date string to proper format if needed
                try:
                    df_prepared['date'] = pd.to_datetime(df_prepared['date']).dt.strftime('%Y-%m-%d')
                except:
                    pass
        
        elif target_table == 'crime_statistics_monthly':
            # Replace null communities with 'UNKNOWN' (for privacy-protected domestic violence data)
            if 'community' in df_prepared.columns:
                df_prepared['community'] = df_prepared['community'].fillna('UNKNOWN')
                logger.info(f"Replaced null community values with 'UNKNOWN'")
        
        elif target_table == 'economic_indicators_monthly':
            # Economic data already has source_file from extraction
            pass
        
        # Select only columns that exist in the dataframe
        # This handles cases where some columns might be missing
        return df_prepared
    
    def _archive_files(self, csv_file: Path):
        """Move processed CSV and its JSON report to appropriate directories."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Archive CSV to processed/
        csv_target_name = f"{csv_file.stem}_{timestamp}.csv"
        csv_target_path = self.processed_dir / csv_target_name
        shutil.move(str(csv_file), str(csv_target_path))
        logger.info(f"📦 Archived {csv_file.name} to processed/")
        
        # Archive JSON to reports/YYYY/MM/ if it exists
        json_file = csv_file.with_suffix('.json')
        if json_file.exists():
            # Create year/month subdirectory
            now = datetime.now()
            year_month_dir = self.reports_dir / str(now.year) / f"{now.month:02d}"
            year_month_dir.mkdir(parents=True, exist_ok=True)
            
            # Move JSON file
            json_target_name = f"{csv_file.stem}_{timestamp}.json"
            json_target_path = year_month_dir / json_target_name
            shutil.move(str(json_file), str(json_target_path))
            logger.info(f"📋 Archived {json_file.name} to reports/{now.year}/{now.month:02d}/")
    
    def get_database_summary(self):
        """Get summary of database contents after loading."""
        cursor = self.conn.cursor()
        
        tables = ['housing_city_monthly', 'housing_district_monthly', 
                 'economic_indicators_monthly', 'crime_statistics_monthly',
                 'service_requests_311_monthly']
        
        summary = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                # Different date column for different tables
                date_col = 'year_month' if table == 'service_requests_311_monthly' else 'date'
                cursor.execute(f"SELECT MIN({date_col}), MAX({date_col}) FROM {table}")
                date_range = cursor.fetchone()
                
                summary[table] = {
                    "records": count,
                    "date_range": f"{date_range[0]} to {date_range[1]}" if date_range[0] else "No data"
                }
            except sqlite3.OperationalError:
                summary[table] = {"records": 0, "date_range": "Table not found"}
        
        return summary
    
    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Main loading function."""
    loader = SimpleCSVLoader()
    
    try:
        # Load all CSV files
        result = loader.load_all_csvs()
        
        # Show results
        if result['loaded'] > 0:
            print(f"\n✅ Successfully loaded {result['loaded']} records")
        if result['errors'] > 0:
            print(f"❌ Failed to load {result['errors']} files")
        
        # Show database summary
        print("\n📊 Database Summary After Loading:")
        summary = loader.get_database_summary()
        for table, info in summary.items():
            print(f"  {table}: {info['records']} records ({info['date_range']})")
        
        # Show where reports were archived
        print(f"\n📋 JSON reports archived to: {loader.reports_dir}/YYYY/MM/")
        
        return result
        
    finally:
        loader.close()


if __name__ == "__main__":
    main()