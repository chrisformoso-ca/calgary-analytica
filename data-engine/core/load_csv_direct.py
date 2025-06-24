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
        
        # Create processed directory if it doesn't exist
        self.processed_dir.mkdir(exist_ok=True)
        
        # Create database connection
        self.conn = sqlite3.connect(self.db_path)
        
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
                    logger.info(f"✅ Loaded {result['records_loaded']} records from {csv_file.name}")
                    
                    # Archive the processed file
                    self._archive_csv(csv_file)
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
            df.columns = df.columns.str.lower().str.replace('_', '')
            
            # Determine target table
            target_table = self._determine_target_table(df, csv_file.name)
            
            if not target_table:
                return {"success": False, "error": "Could not determine target table"}
            
            # Prepare data for loading
            df_prepared = self._prepare_dataframe(df, target_table, csv_file.name)
            
            if df_prepared.empty:
                return {"success": False, "error": "No valid data after preparation"}
            
            # Load to database
            records_loaded = len(df_prepared)
            df_prepared.to_sql(target_table, self.conn, if_exists='append', index=False)
            self.conn.commit()
            
            logger.info(f"📊 Loaded {records_loaded} records to {target_table}")
            return {"success": True, "records_loaded": records_loaded}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _determine_target_table(self, df: pd.DataFrame, filename: str) -> str:
        """Determine the appropriate database table for the data."""
        columns = set(df.columns)
        
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
        
        # Check for crime statistics
        elif any(col in columns for col in ['crimetype', 'incidentcount', 'community']):
            return 'crime_statistics_monthly'
        
        # Fallback based on filename
        elif 'economic' in filename.lower():
            return 'economic_indicators_monthly'
        elif 'crime' in filename.lower():
            return 'crime_statistics_monthly'
        elif 'creb' in filename.lower() or 'housing' in filename.lower():
            if 'district' in filename.lower():
                return 'housing_district_monthly'
            else:
                return 'housing_city_monthly'
        
        return None
    
    def _prepare_dataframe(self, df: pd.DataFrame, target_table: str, filename: str) -> pd.DataFrame:
        """Prepare dataframe for loading to specific table."""
        df_prepared = df.copy()
        
        # Restore underscores in column names for database
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
        
        # Apply column mapping
        df_prepared.rename(columns=column_mapping, inplace=True)
        
        # Handle date column variations
        if 'Date' in df_prepared.columns:
            df_prepared.rename(columns={'Date': 'date'}, inplace=True)
        
        # Add metadata columns (table-specific)
        if target_table in ['housing_city_monthly', 'housing_district_monthly', 'crime_statistics_monthly']:
            df_prepared['source_pdf'] = filename
        
        # Only add these if they don't already exist (economic data may already have them)
        if 'extracted_date' not in df_prepared.columns:
            df_prepared['extracted_date'] = datetime.now().isoformat()
        if 'confidence_score' not in df_prepared.columns:
            df_prepared['confidence_score'] = 1.0  # Human approved
        if 'validation_status' not in df_prepared.columns:
            df_prepared['validation_status'] = 'approved'
        
        # Table-specific preparations
        if target_table == 'housing_city_monthly':
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
        
        elif target_table == 'economic_indicators_monthly':
            # Economic data already has source_file from extraction
            pass
        
        # Select only columns that exist in the dataframe
        # This handles cases where some columns might be missing
        return df_prepared
    
    def _archive_csv(self, csv_file: Path):
        """Move processed CSV to processed directory."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        target_name = f"{csv_file.stem}_{timestamp}.csv"
        target_path = self.processed_dir / target_name
        
        shutil.move(str(csv_file), str(target_path))
        logger.info(f"📦 Archived {csv_file.name} to processed/")
    
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
    loader = SimpleCSVLoader()
    
    try:
        # Load all CSV files
        result = loader.load_all_csvs()
        
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