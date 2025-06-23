#!/usr/bin/env python3
"""
Consolidate Database Files
Moves any database files from incorrect locations to the configured location
"""

import shutil
import sqlite3
from pathlib import Path
import sys
import logging

# Add config to path
sys.path.append(str(Path(__file__).parent.parent / "config"))
from config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def consolidate_databases():
    """Find and consolidate all database files to the correct location."""
    
    # Get the correct database path from config
    config = ConfigManager()
    correct_db_path = config.get_database_path()
    
    logger.info(f"Correct database location: {correct_db_path}")
    
    # Ensure the directory exists
    correct_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Search for all calgary_data.db files
    project_root = Path(__file__).parent.parent
    db_files = list(project_root.rglob("calgary_data.db"))
    
    if not db_files:
        logger.warning("No database files found!")
        return
    
    logger.info(f"Found {len(db_files)} database file(s):")
    for db in db_files:
        logger.info(f"  - {db}")
    
    # If the correct database already exists, check if we need to merge
    if correct_db_path.exists():
        logger.info(f"Database already exists at correct location: {correct_db_path}")
        
        # Show info about the correct database
        conn = sqlite3.connect(correct_db_path)
        cursor = conn.cursor()
        
        # Check city data
        cursor.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM housing_city_monthly")
        city_count, city_min, city_max = cursor.fetchone()
        
        # Check district data
        cursor.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM housing_district_monthly")
        district_count, district_min, district_max = cursor.fetchone()
        
        conn.close()
        
        logger.info(f"Current database contains:")
        logger.info(f"  - City records: {city_count} ({city_min} to {city_max})")
        logger.info(f"  - District records: {district_count} ({district_min} to {district_max})")
        
    else:
        # Find the most complete database to use
        best_db = None
        best_count = 0
        
        for db_path in db_files:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Count total records
                cursor.execute("SELECT COUNT(*) FROM housing_city_monthly")
                city_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM housing_district_monthly")
                district_count = cursor.fetchone()[0]
                
                total_count = city_count + district_count
                
                logger.info(f"  {db_path}: {total_count} total records")
                
                if total_count > best_count:
                    best_count = total_count
                    best_db = db_path
                
                conn.close()
                
            except Exception as e:
                logger.warning(f"  Could not read {db_path}: {e}")
        
        if best_db and best_db != correct_db_path:
            logger.info(f"\nMoving best database from {best_db} to {correct_db_path}")
            shutil.move(str(best_db), str(correct_db_path))
            logger.info("Database moved successfully!")
    
    # Clean up any remaining database files
    for db_path in db_files:
        if db_path != correct_db_path and db_path.exists():
            logger.info(f"Removing duplicate database: {db_path}")
            db_path.unlink()
    
    logger.info("\nDatabase consolidation complete!")
    logger.info(f"Single database now at: {correct_db_path}")

if __name__ == "__main__":
    consolidate_databases()