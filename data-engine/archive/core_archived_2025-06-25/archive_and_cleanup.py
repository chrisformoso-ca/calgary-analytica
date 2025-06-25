#!/usr/bin/env python3
"""
Archive and Cleanup Script
Safely archive processed validation data and clean up redundant files
"""

import shutil
from pathlib import Path
import logging
import sys
from datetime import datetime

# Add project root for config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.config_manager import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataArchiver:
    """Archive and cleanup processed validation data."""
    
    def __init__(self):
        self.config = get_config()
        self.approved_dir = self.config.get_approved_data_dir()
        self.archive_dir = self.config.get_validation_base() / "archive"
        
    def archive_approved_data(self):
        """Archive all approved validation data."""
        logger.info("📦 Archiving approved validation data...")
        
        if not self.approved_dir.exists():
            logger.info("No approved data directory found")
            return
        
        # Create archive directory
        self.archive_dir.mkdir(exist_ok=True)
        
        approved_items = list(self.approved_dir.glob("*"))
        if not approved_items:
            logger.info("No approved items to archive")
            return
        
        archived_count = 0
        
        for item in approved_items:
            if item.is_dir():
                try:
                    # Create timestamp-based archive name
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    archive_name = f"{item.name}_{timestamp}"
                    archive_path = self.archive_dir / archive_name
                    
                    # Move to archive
                    shutil.move(str(item), str(archive_path))
                    
                    logger.info(f"📦 Archived: {item.name} → {archive_name}")
                    archived_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to archive {item.name}: {e}")
        
        logger.info(f"✅ Archived {archived_count} validation items")
        return archived_count
    
    def consolidate_csv_files(self):
        """Move scattered CSV files to central location."""
        logger.info("📁 Consolidating CSV files...")
        
        # Create consolidated directory
        consolidated_dir = self.config.get_processed_dir() / "consolidated"
        consolidated_dir.mkdir(exist_ok=True)
        
        # Find CSV files in various locations
        csv_locations = [
            self.config.get_processed_dir() / "extracted",
            self.config.get_validation_base() / "pending",
            self.config.get_validation_base() / "approved"
        ]
        
        consolidated_count = 0
        
        for location in csv_locations:
            if location.exists():
                csv_files = list(location.rglob("*.csv"))
                
                for csv_file in csv_files:
                    try:
                        # Create unique name to avoid conflicts
                        relative_path = csv_file.relative_to(location)
                        target_name = str(relative_path).replace("/", "_")
                        target_path = consolidated_dir / target_name
                        
                        # Copy (don't move) to preserve originals during transition
                        shutil.copy2(csv_file, target_path)
                        
                        logger.info(f"📄 Consolidated: {csv_file.name}")
                        consolidated_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to consolidate {csv_file}: {e}")
        
        logger.info(f"✅ Consolidated {consolidated_count} CSV files")
        return consolidated_count


def main():
    """Main archival function."""
    archiver = DataArchiver()
    
    print("🧹 Calgary Analytica - Data Cleanup & Archival")
    print("=" * 50)
    
    # Archive approved validation data
    archived = archiver.archive_approved_data()
    
    # Consolidate CSV files
    consolidated = archiver.consolidate_csv_files()
    
    print(f"\n✅ Cleanup Complete:")
    print(f"  📦 Archived validation items: {archived}")
    print(f"  📁 Consolidated CSV files: {consolidated}")
    
    print(f"\n📊 Current State:")
    config = archiver.config
    
    # Show directory sizes
    locations = {
        "Database": config.get_database_path(),
        "Archive": archiver.archive_dir,
        "Consolidated CSVs": config.get_processed_dir() / "consolidated",
        "Validation": config.get_validation_base()
    }
    
    for name, path in locations.items():
        if path.exists():
            if path.is_file():
                size = path.stat().st_size
                print(f"  {name}: {size/1024:.1f}KB")
            else:
                file_count = len(list(path.rglob("*")))
                print(f"  {name}: {file_count} items")
        else:
            print(f"  {name}: Not found")


if __name__ == "__main__":
    main()