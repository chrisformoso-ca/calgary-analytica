#!/usr/bin/env python3
"""
Data Pipeline Manager
Simple orchestrator for Calgary Analytica ETL operations
"""

import configparser
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataPipelineManager:
    """Simple pipeline manager for extract → validate → load workflow."""
    
    def __init__(self, config_path: str = None):
        # Load configuration
        self.base_path = Path(__file__).parent.parent
        self.config_path = Path(config_path) if config_path else self.base_path.parent / "config" / "calgary_analytica.ini"
        self.config = self._load_config()
        
        # Set up paths from config
        self.database_path = Path(self.config['database']['primary_db'])
        self.pending_path = Path(self.config['validation']['pending_review'])
        self.approved_path = Path(self.config['validation']['approved_data'])
        self.rejected_path = Path(self.config['validation']['rejected_data'])
        
        # Ensure directories exist
        self.pending_path.mkdir(parents=True, exist_ok=True)
        self.approved_path.mkdir(parents=True, exist_ok=True)
        self.rejected_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("🏗️  Pipeline Manager initialized")
        logger.info(f"   Database: {self.database_path}")
        logger.info(f"   Pending: {self.pending_path}")
        logger.info(f"   Approved: {self.approved_path}")
    
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration file."""
        config = configparser.ConfigParser()
        
        if self.config_path.exists():
            config.read(self.config_path)
            logger.info(f"📄 Loaded configuration: {self.config_path}")
        else:
            logger.warning(f"⚠️  Configuration file not found: {self.config_path}")
            # Use default config
            config.read_string("""
            [database]
            primary_db = /home/chris/calgary-analytica/data-lake/calgary_data.db
            
            [validation]
            pending_review = /home/chris/calgary-analytica/data-engine/validation/pending
            approved_data = /home/chris/calgary-analytica/data-engine/validation/approved
            rejected_data = /home/chris/calgary-analytica/data-engine/validation/rejected
            """)
        
        return config
    
    def run_extraction(self, extractor_name: str, source_path: str = None, **kwargs) -> Dict[str, any]:
        """Run extraction and save CSV to validation/pending."""
        try:
            logger.info(f"🔄 Running {extractor_name} extraction")
            
            # Call the appropriate extractor script
            if extractor_name == "creb":
                result = self._run_creb_extraction(source_path, **kwargs)
            elif extractor_name == "economic":
                result = self._run_economic_extraction(source_path, **kwargs)
            elif extractor_name == "crime":
                result = self._run_crime_extraction(source_path, **kwargs)
            else:
                return {"success": False, "error": f"Unknown extractor: {extractor_name}"}
            
            if result["success"]:
                logger.info(f"✅ {extractor_name} extraction completed: {result['output_file']}")
            else:
                logger.error(f"❌ {extractor_name} extraction failed: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"💥 Extraction error: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_creb_extraction(self, source_path: str = None, **kwargs) -> Dict[str, any]:
        """Run CREB extraction."""
        try:
            # Use CREB extractor
            extractor_path = self.base_path / "sources" / "creb" / "extractor.py"
            if not extractor_path.exists():
                return {"success": False, "error": "CREB extractor not found"}
            
            # Run extraction (simplified - could call Python directly)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.pending_path / f"creb_extraction_{timestamp}.csv"
            
            # For now, return placeholder - in practice would call extractor
            return {
                "success": True,
                "output_file": str(output_file),
                "records_extracted": 0,
                "message": "CREB extraction placeholder"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _run_economic_extraction(self, source_path: str = None, **kwargs) -> Dict[str, any]:
        """Run economic indicators extraction."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.pending_path / f"economic_extraction_{timestamp}.csv"
        
        return {
            "success": True,
            "output_file": str(output_file),
            "records_extracted": 0,
            "message": "Economic extraction placeholder"
        }
    
    def _run_crime_extraction(self, source_path: str = None, **kwargs) -> Dict[str, any]:
        """Run crime statistics extraction."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.pending_path / f"crime_extraction_{timestamp}.csv"
        
        return {
            "success": True,
            "output_file": str(output_file),
            "records_extracted": 0,
            "message": "Crime extraction placeholder"
        }
    
    def validate_pending(self) -> List[Dict[str, any]]:
        """List files in pending directory for human review."""
        pending_files = []
        
        for csv_file in self.pending_path.glob("*.csv"):
            file_info = {
                "filename": csv_file.name,
                "full_path": str(csv_file),
                "size_kb": round(csv_file.stat().st_size / 1024, 2),
                "created": datetime.fromtimestamp(csv_file.stat().st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            }
            pending_files.append(file_info)
        
        logger.info(f"📋 Found {len(pending_files)} files pending validation")
        return pending_files
    
    def approve_file(self, filename: str) -> Dict[str, any]:
        """Move file from pending to approved."""
        try:
            source_file = self.pending_path / filename
            if not source_file.exists():
                return {"success": False, "error": f"File not found: {filename}"}
            
            target_file = self.approved_path / filename
            shutil.move(str(source_file), str(target_file))
            
            logger.info(f"✅ Approved: {filename}")
            return {"success": True, "message": f"Approved {filename}"}
            
        except Exception as e:
            logger.error(f"💥 Failed to approve {filename}: {e}")
            return {"success": False, "error": str(e)}
    
    def reject_file(self, filename: str, reason: str = None) -> Dict[str, any]:
        """Move file from pending to rejected."""
        try:
            source_file = self.pending_path / filename
            if not source_file.exists():
                return {"success": False, "error": f"File not found: {filename}"}
            
            target_file = self.rejected_path / filename
            shutil.move(str(source_file), str(target_file))
            
            # Log rejection reason
            if reason:
                logger.info(f"❌ Rejected: {filename} - {reason}")
            else:
                logger.info(f"❌ Rejected: {filename}")
            
            return {"success": True, "message": f"Rejected {filename}"}
            
        except Exception as e:
            logger.error(f"💥 Failed to reject {filename}: {e}")
            return {"success": False, "error": str(e)}
    
    def load_approved(self) -> Dict[str, any]:
        """Load approved CSV files to database using load_to_database.py script."""
        try:
            # Check if we have any approved files
            approved_files = list(self.approved_path.glob("*.csv"))
            if not approved_files:
                return {"success": True, "message": "No approved files to load", "files_loaded": 0}
            
            # Run the database loading script
            script_path = self.base_path.parent / "scripts" / "load_to_database.py"
            if not script_path.exists():
                return {"success": False, "error": "Database loading script not found"}
            
            logger.info(f"🔄 Loading {len(approved_files)} approved files to database")
            
            # Execute the loading script
            result = subprocess.run(
                ["python3", str(script_path)],
                capture_output=True,
                text=True,
                cwd=str(self.base_path.parent)
            )
            
            if result.returncode == 0:
                logger.info("✅ Database loading completed successfully")
                return {
                    "success": True,
                    "message": "Database loading completed",
                    "output": result.stdout
                }
            else:
                logger.error(f"❌ Database loading failed: {result.stderr}")
                return {
                    "success": False,
                    "error": f"Loading failed: {result.stderr}",
                    "output": result.stdout
                }
                
        except Exception as e:
            logger.error(f"💥 Database loading error: {e}")
            return {"success": False, "error": str(e)}