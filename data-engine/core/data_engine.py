#!/usr/bin/env python3
"""
Calgary Data Engine - Simple orchestrator for data extraction operations
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import sys

# Add config to path
sys.path.append(str(Path(__file__).parent.parent.parent / "config"))
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class DataEngine:
    """Simple data engine for running extractors."""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.sources_path = self.base_path / "sources"
        
        # Use ConfigManager for all paths
        self.config = ConfigManager()
        self.database_path = self.config.get_database_path()
        
        # Raw data paths from config
        self.creb_pdf_dir = self.config.get_creb_pdf_dir()
        self.economic_data_dir = self.config.get_economic_data_dir()
        self.crime_data_dir = self.config.get_crime_data_dir()
        
        # Output paths for validation
        self.validation_dir = self.config.get_pending_review_dir()
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🏗️  Data Engine initialized")
        logger.info(f"   Database: {self.database_path}")
        logger.info(f"   Sources: {self.sources_path}")
        logger.info(f"   Validation: {self.validation_dir}")
    
    def extract_creb(self, pdf_path: str = None, month: str = None) -> Dict[str, Any]:
        """Extract CREB housing data from PDF reports."""
        try:
            logger.info("🔄 Starting CREB extraction")
            
            # Use existing CREB extractor
            extractor_script = self.base_path.parent / "extractors" / "creb_reports" / "update_calgary_creb_data.py"
            if not extractor_script.exists():
                return {"success": False, "error": "CREB extractor script not found"}
            
            # Set output path in validation directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.validation_dir / f"creb_extraction_{timestamp}.csv"
            
            # Prepare command arguments
            cmd = ["python3", str(extractor_script)]
            
            if pdf_path:
                cmd.extend(["--pdf-path", pdf_path])
            else:
                cmd.extend(["--pdf-dir", str(self.creb_pdf_dir)])
            
            cmd.extend(["--csv-path", str(output_file)])
            
            # Run extraction
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.base_path.parent)
            )
            
            if result.returncode == 0:
                # Check if output file was created
                if output_file.exists():
                    # Count records
                    import pandas as pd
                    df = pd.read_csv(output_file)
                    record_count = len(df)
                    
                    logger.info(f"✅ CREB extraction completed: {record_count} records")
                    return {
                        "success": True,
                        "output_file": str(output_file),
                        "records_extracted": record_count,
                        "message": "CREB extraction completed successfully"
                    }
                else:
                    return {"success": False, "error": "Output file not created"}
            else:
                logger.error(f"❌ CREB extraction failed: {result.stderr}")
                return {
                    "success": False,
                    "error": f"Extraction failed: {result.stderr}",
                    "output": result.stdout
                }
                
        except Exception as e:
            logger.error(f"💥 CREB extraction error: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_economic(self, source_path: str = None, indicators: list = None) -> Dict[str, Any]:
        """Extract economic indicators data."""
        try:
            logger.info("🔄 Starting economic indicators extraction")
            
            # Use existing economic extractor
            extractor_script = self.sources_path / "economic" / "extractor.py"
            if not extractor_script.exists():
                return {"success": False, "error": "Economic extractor script not found"}
            
            # Set output path in validation directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.validation_dir / f"economic_extraction_{timestamp}.csv"
            
            # Prepare command arguments
            cmd = ["python3", str(extractor_script)]
            
            if source_path:
                cmd.extend(["--source-path", source_path])
            else:
                cmd.extend(["--source-dir", str(self.economic_data_dir)])
            
            cmd.extend(["--output", str(output_file)])
            
            # Run extraction
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.base_path)
            )
            
            if result.returncode == 0:
                # Check if output file was created and count records
                if output_file.exists():
                    import pandas as pd
                    df = pd.read_csv(output_file)
                    record_count = len(df)
                    
                    logger.info(f"✅ Economic extraction completed: {record_count} records")
                    return {
                        "success": True,
                        "output_file": str(output_file),
                        "records_extracted": record_count,
                        "message": "Economic extraction completed successfully"
                    }
                else:
                    return {"success": False, "error": "Output file not created"}
            else:
                logger.error(f"❌ Economic extraction failed: {result.stderr}")
                return {
                    "success": False,
                    "error": f"Extraction failed: {result.stderr}",
                    "output": result.stdout
                }
                
        except Exception as e:
            logger.error(f"💥 Economic extraction error: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_crime(self, source_path: str = None, date_range: tuple = None) -> Dict[str, Any]:
        """Extract crime statistics data."""
        try:
            logger.info("🔄 Starting crime statistics extraction")
            
            # Use existing crime extractor
            extractor_script = self.sources_path / "police" / "extractor.py"
            if not extractor_script.exists():
                return {"success": False, "error": "Crime extractor script not found"}
            
            # Set output path in validation directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.validation_dir / f"crime_extraction_{timestamp}.csv"
            
            # Prepare command arguments
            cmd = ["python3", str(extractor_script)]
            
            if source_path:
                cmd.extend(["--source-path", source_path])
            else:
                cmd.extend(["--source-dir", str(self.crime_data_dir)])
            
            cmd.extend(["--output", str(output_file)])
            
            # Run extraction
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.base_path)
            )
            
            if result.returncode == 0:
                # Check if output file was created and count records
                if output_file.exists():
                    import pandas as pd
                    df = pd.read_csv(output_file)
                    record_count = len(df)
                    
                    logger.info(f"✅ Crime extraction completed: {record_count} records")
                    return {
                        "success": True,
                        "output_file": str(output_file),
                        "records_extracted": record_count,
                        "message": "Crime extraction completed successfully"
                    }
                else:
                    return {"success": False, "error": "Output file not created"}
            else:
                logger.error(f"❌ Crime extraction failed: {result.stderr}")
                return {
                    "success": False,
                    "error": f"Extraction failed: {result.stderr}",
                    "output": result.stdout
                }
                
        except Exception as e:
            logger.error(f"💥 Crime extraction error: {e}")
            return {"success": False, "error": str(e)}
    
    def status(self) -> Dict[str, Any]:
        """Get simple status information."""
        # Count pending validation files
        pending_files = list(self.validation_dir.glob("*.csv"))
        
        # Check database exists
        db_exists = self.database_path.exists()
        
        return {
            "database_exists": db_exists,
            "database_path": str(self.database_path),
            "pending_validations": len(pending_files),
            "validation_directory": str(self.validation_dir),
            "available_extractors": ["creb", "economic", "crime"]
        }

def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calgary Data Engine")
    parser.add_argument("source", choices=["creb", "economic", "crime"], help="Data source to extract")
    parser.add_argument("--source-path", help="Specific source file/directory path")
    parser.add_argument("--pdf-path", help="Specific PDF file path (CREB only)")
    parser.add_argument("--month", help="Target month (CREB only)")
    
    args = parser.parse_args()
    
    # Initialize data engine
    engine = DataEngine()
    
    # Run extraction based on source
    if args.source == "creb":
        result = engine.extract_creb(pdf_path=args.pdf_path, month=args.month)
    elif args.source == "economic":
        result = engine.extract_economic(source_path=args.source_path)
    elif args.source == "crime":
        result = engine.extract_crime(source_path=args.source_path)
    
    # Print results
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"   Output: {result['output_file']}")
        print(f"   Records: {result['records_extracted']}")
    else:
        print(f"❌ Extraction failed: {result['error']}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())