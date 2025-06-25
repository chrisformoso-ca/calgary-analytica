#!/usr/bin/env python3
"""
Update Economic Metadata Table
Tracks which economic indicator files have been processed
"""

import sqlite3
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime
import sys

# Add project root for config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.config_manager import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EconomicMetadataUpdater:
    """Update economic_metadata table with file processing information."""
    
    def __init__(self):
        self.config = get_config()
        self.db_path = self.config.get_database_path()
        self.conn = sqlite3.connect(self.db_path)
        
    def update_from_csv(self, csv_path: Path):
        """Update metadata based on processed CSV file."""
        try:
            # Read CSV to get metadata
            df = pd.read_csv(csv_path)
            
            if df.empty:
                logger.warning(f"Empty CSV file: {csv_path}")
                return
            
            # Extract unique source files
            if 'source_file' in df.columns:
                source_files = df['source_file'].unique()
            else:
                logger.warning("No source_file column found in CSV")
                return
            
            # Process each source file
            for source_file in source_files:
                # Get data for this source file
                file_data = df[df['source_file'] == source_file]
                
                # Calculate metadata
                date_range_start = file_data['date'].min()
                date_range_end = file_data['date'].max()
                indicators_count = len(file_data)
                
                # Check if already exists
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT id FROM economic_metadata 
                    WHERE source_file = ?
                """, (source_file,))
                
                exists = cursor.fetchone()
                
                if exists:
                    # Update existing record
                    cursor.execute("""
                        UPDATE economic_metadata 
                        SET date_range_start = ?,
                            date_range_end = ?,
                            indicators_count = ?,
                            processing_status = 'completed',
                            processed_date = ?
                        WHERE source_file = ?
                    """, (date_range_start, date_range_end, indicators_count, 
                         datetime.now().isoformat(), source_file))
                    
                    logger.info(f"Updated metadata for {source_file}")
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO economic_metadata 
                        (source_file, file_type, date_range_start, date_range_end, 
                         indicators_count, processing_status, processed_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (source_file, 'xlsx', date_range_start, date_range_end,
                         indicators_count, 'completed', datetime.now().isoformat()))
                    
                    logger.info(f"Created metadata for {source_file}")
            
            self.conn.commit()
            logger.info(f"✅ Updated metadata for {len(source_files)} source files")
            
        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
            self.conn.rollback()
    
    def mark_file_processed(self, source_file: str, status: str = 'completed', 
                          error_details: str = None):
        """Mark a specific file as processed."""
        try:
            cursor = self.conn.cursor()
            
            # Check if exists
            cursor.execute("""
                SELECT id FROM economic_metadata 
                WHERE source_file = ?
            """, (source_file,))
            
            exists = cursor.fetchone()
            
            if exists:
                # Update status
                cursor.execute("""
                    UPDATE economic_metadata 
                    SET processing_status = ?,
                        error_details = ?,
                        processed_date = ?
                    WHERE source_file = ?
                """, (status, error_details, datetime.now().isoformat(), source_file))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO economic_metadata 
                    (source_file, file_type, processing_status, error_details, processed_date)
                    VALUES (?, 'xlsx', ?, ?, ?)
                """, (source_file, status, error_details, datetime.now().isoformat()))
            
            self.conn.commit()
            logger.info(f"Marked {source_file} as {status}")
            
        except Exception as e:
            logger.error(f"Error marking file processed: {e}")
            self.conn.rollback()
    
    def get_processing_status(self):
        """Get summary of processing status."""
        cursor = self.conn.cursor()
        
        # Get counts by status
        cursor.execute("""
            SELECT processing_status, COUNT(*) as count
            FROM economic_metadata
            GROUP BY processing_status
        """)
        
        status_counts = cursor.fetchall()
        
        # Get recently processed
        cursor.execute("""
            SELECT source_file, processed_date, indicators_count
            FROM economic_metadata
            WHERE processing_status = 'completed'
            ORDER BY processed_date DESC
            LIMIT 10
        """)
        
        recent_files = cursor.fetchall()
        
        return {
            'status_counts': dict(status_counts),
            'recent_files': recent_files
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Update metadata from approved CSV files."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update economic metadata table')
    parser.add_argument('--csv', type=str, help='Path to CSV file to process')
    parser.add_argument('--status', action='store_true', help='Show processing status')
    args = parser.parse_args()
    
    updater = EconomicMetadataUpdater()
    
    try:
        if args.status:
            status = updater.get_processing_status()
            print("\n📊 Economic Metadata Status:")
            print("\nProcessing Status:")
            for status_type, count in status['status_counts'].items():
                print(f"  {status_type}: {count}")
            
            print("\nRecently Processed Files:")
            for file_info in status['recent_files']:
                print(f"  {file_info[0]} - {file_info[1][:10]} ({file_info[2]} indicators)")
        
        elif args.csv:
            csv_path = Path(args.csv)
            if csv_path.exists():
                updater.update_from_csv(csv_path)
            else:
                print(f"CSV file not found: {csv_path}")
        
        else:
            # Process all CSVs in approved directory
            config = get_config()
            approved_dir = config.get_approved_data_dir()
            
            csv_files = list(approved_dir.glob("economic*.csv"))
            print(f"Found {len(csv_files)} economic CSV files in approved directory")
            
            for csv_file in csv_files:
                print(f"Processing {csv_file.name}...")
                updater.update_from_csv(csv_file)
    
    finally:
        updater.close()


if __name__ == "__main__":
    main()