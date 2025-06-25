#!/usr/bin/env python3
"""
Load Approved Validation Data
Processes approved validation items and loads them into the central database
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
import logging
import sys
from datetime import datetime

# Add project root for config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.config_manager import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApprovedDataLoader:
    """Load approved validation data into central database."""
    
    def __init__(self):
        self.config = get_config()
        self.db_path = self.config.get_database_path()
        self.approved_dir = self.config.get_approved_data_dir()
        
        # Create database connection
        self.conn = sqlite3.connect(self.db_path)
        
    def load_all_approved_data(self):
        """Load all approved validation data into database."""
        logger.info("🔄 Loading approved validation data into database...")
        
        if not self.approved_dir.exists():
            logger.warning("No approved data directory found")
            return {"loaded": 0, "errors": 0}
        
        approved_items = list(self.approved_dir.glob("*"))
        if not approved_items:
            logger.info("No approved items to process")
            return {"loaded": 0, "errors": 0}
        
        loaded_count = 0
        error_count = 0
        
        for item_dir in approved_items:
            if item_dir.is_dir():
                try:
                    result = self._load_single_approved_item(item_dir)
                    if result["success"]:
                        loaded_count += result["records_loaded"]
                        logger.info(f"✅ Loaded {result['records_loaded']} records from {item_dir.name}")
                        
                        # Move to processed directory
                        self._archive_approved_item(item_dir)
                    else:
                        error_count += 1
                        logger.error(f"❌ Failed to load {item_dir.name}: {result['error']}")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Error processing {item_dir.name}: {e}")
        
        logger.info(f"📊 Summary: {loaded_count} records loaded, {error_count} errors")
        return {"loaded": loaded_count, "errors": error_count}
    
    def _load_single_approved_item(self, item_dir: Path):
        """Load a single approved validation item."""
        
        # Read validation report to understand data type
        validation_report = item_dir / "validation_report.json"
        if not validation_report.exists():
            return {"success": False, "error": "No validation report found"}
        
        with open(validation_report) as f:
            report = json.load(f)
        
        # Find CSV files in the directory
        csv_files = list(item_dir.glob("*.csv"))
        if not csv_files:
            return {"success": False, "error": "No CSV files found"}
        
        total_loaded = 0
        
        for csv_file in csv_files:
            # Determine data type and target table
            result = self._load_csv_to_appropriate_table(csv_file, report)
            if result["success"]:
                total_loaded += result["records_loaded"]
            else:
                return {"success": False, "error": f"Failed to load {csv_file.name}: {result['error']}"}
        
        return {"success": True, "records_loaded": total_loaded}
    
    def _load_csv_to_appropriate_table(self, csv_file: Path, validation_report: dict):
        """Load CSV to the appropriate database table based on content analysis."""
        
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            
            if df.empty:
                return {"success": False, "error": "Empty CSV file"}
            
            # Determine target table first to know what columns to expect
            target_table = self._determine_target_table(df, csv_file.name)
            
            if not target_table:
                return {"success": False, "error": "Could not determine target table"}
            
            # Split CREB data if it contains both city and district data
            if target_table == 'housing_city_monthly' and 'data_type' in df.columns:
                # This CSV contains both city and district data - split it
                city_data = df[df['data_type'] == 'city'].copy()
                district_data = df[df['data_type'] == 'district'].copy()
                
                total_loaded = 0
                
                # Load city data
                if not city_data.empty:
                    city_result = self._load_split_data(city_data, 'housing_city_monthly', csv_file, validation_report)
                    if city_result['success']:
                        total_loaded += city_result['records_loaded']
                    else:
                        return city_result
                
                # Load district data
                if not district_data.empty:
                    district_result = self._load_split_data(district_data, 'housing_district_monthly', csv_file, validation_report)
                    if district_result['success']:
                        total_loaded += district_result['records_loaded']
                    else:
                        return district_result
                
                return {"success": True, "records_loaded": total_loaded}
            
            else:
                # Single table load
                return self._load_split_data(df, target_table, csv_file, validation_report)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _load_split_data(self, df: pd.DataFrame, target_table: str, csv_file: Path, validation_report: dict):
        """Load prepared dataframe to specific table."""
        
        # Add metadata columns based on target table schema
        if 'source_pdf' not in df.columns:
            df['source_pdf'] = csv_file.parent.name
        if 'extracted_date' not in df.columns:
            df['extracted_date'] = datetime.now().isoformat()
        if 'confidence_score' not in df.columns:
            df['confidence_score'] = validation_report.get('confidence_score', 1.0)
        if 'validation_status' not in df.columns:
            df['validation_status'] = 'approved'
        
        # Remove columns that don't belong in target table
        df_clean = self._clean_dataframe_for_table(df, target_table)
        
        if df_clean.empty:
            return {"success": False, "error": f"No valid data for {target_table}"}
        
        # Load to database
        records_loaded = len(df_clean)
        df_clean.to_sql(target_table, self.conn, if_exists='append', index=False)
        self.conn.commit()
        
        logger.info(f"📊 Loaded {records_loaded} records to {target_table}")
        return {"success": True, "records_loaded": records_loaded}
    
    def _clean_dataframe_for_table(self, df: pd.DataFrame, target_table: str):
        """Remove columns that don't exist in target table schema."""
        
        # Define expected columns for each table
        table_schemas = {
            'housing_city_monthly': [
                'date', 'property_type', 'sales', 'new_listings', 'inventory', 
                'days_on_market', 'benchmark_price', 'median_price', 'average_price',
                'source_pdf', 'extracted_date', 'confidence_score', 'validation_status'
            ],
            'housing_district_monthly': [
                'date', 'property_type', 'district', 'new_sales', 'new_listings',
                'sales_to_listings_ratio', 'inventory', 'months_supply', 'benchmark_price',
                'yoy_price_change', 'mom_price_change', 'source_pdf', 'extracted_date',
                'confidence_score', 'validation_status'
            ],
            'economic_indicators_monthly': [
                'date', 'indicator_type', 'indicator_name', 'value', 'unit',
                'yoy_change', 'mom_change', 'category', 'source_file',
                'extracted_date', 'confidence_score', 'validation_status'
            ]
        }
        
        if target_table not in table_schemas:
            return df
        
        expected_columns = table_schemas[target_table]
        
        # Keep only columns that exist in both dataframe and target schema
        available_columns = [col for col in expected_columns if col in df.columns]
        
        # Map sales column for district data
        if target_table == 'housing_district_monthly' and 'sales' in df.columns and 'new_sales' not in df.columns:
            df['new_sales'] = df['sales']
        
        # For economic data, map source_pdf to source_file
        if target_table == 'economic_indicators_monthly' and 'source_pdf' in df.columns and 'source_file' not in df.columns:
            df['source_file'] = df['source_pdf']
            available_columns = [col if col != 'source_pdf' else 'source_file' for col in available_columns]
        
        return df[available_columns].copy()
    
    def _determine_target_table(self, df: pd.DataFrame, filename: str) -> str:
        """Determine the appropriate database table for the data."""
        
        columns = set(df.columns.str.lower())
        
        # CREB housing data patterns
        if any(col in columns for col in ['property_type', 'benchmark_price', 'sales']):
            if 'district' in columns:
                return 'housing_district_monthly'
            else:
                return 'housing_city_monthly'
        
        # Economic indicators
        elif any(col in columns for col in ['indicator_name', 'economic_indicator', 'unemployment_rate']):
            return 'economic_indicators_monthly'
        
        # Crime statistics
        elif any(col in columns for col in ['crime_type', 'incident_count', 'community']):
            return 'crime_statistics_monthly'
        
        # Fallback based on filename
        elif 'economic' in filename.lower():
            return 'economic_indicators_monthly'
        elif 'crime' in filename.lower():
            return 'crime_statistics_monthly'
        elif 'creb' in filename.lower():
            if len(df) > 50:  # Likely district data
                return 'housing_district_monthly'
            else:
                return 'housing_city_monthly'
        
        return None
    
    def _archive_approved_item(self, item_dir: Path):
        """Move approved item to processed archive."""
        processed_dir = self.approved_dir.parent / "processed"
        processed_dir.mkdir(exist_ok=True)
        
        target_path = processed_dir / item_dir.name
        item_dir.rename(target_path)
        
        logger.info(f"📦 Archived {item_dir.name} to processed/")
    
    def get_database_summary(self):
        """Get summary of database contents after loading."""
        cursor = self.conn.cursor()
        
        tables = ['housing_city_monthly', 'housing_district_monthly', 
                 'economic_indicators_monthly', 'crime_statistics_monthly']
        
        summary = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT MIN(date), MAX(date) FROM {table}")
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
    loader = ApprovedDataLoader()
    
    try:
        # Load all approved data
        result = loader.load_all_approved_data()
        
        # Show database summary
        print("\n📊 Database Summary After Loading:")
        summary = loader.get_database_summary()
        for table, info in summary.items():
            print(f"  {table}: {info['records']} records ({info['date_range']})")
        
        return result
        
    finally:
        loader.close()


if __name__ == "__main__":
    main()