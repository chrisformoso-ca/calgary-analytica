#!/usr/bin/env python3
"""
Process All CREB Reports
Main script to process all PDF reports and generate both city-wide and district-level data
"""

import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_script(script_path: str, description: str) -> bool:
    """Run a Python script and return success status."""
    try:
        logger.info(f"Running {description}...")
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout:
            print(result.stdout)
        
        logger.info(f"✅ {description} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """Main processing pipeline."""
    
    scripts_dir = Path(".")  # Current directory since we're in the scripts folder
    
    print("🏠 Calgary Housing Data Processing Pipeline")
    print("=" * 50)
    
    # Step 1: Extract district-level data
    district_script = scripts_dir / "creb_extractor.py"
    if district_script.exists():
        success1 = run_script(str(district_script), "District data extraction")
    else:
        logger.warning("District extractor script not found, skipping...")
        success1 = True
    
    # Step 2: Update city-wide data
    city_script = scripts_dir / "update_calgary_creb_data.py"
    if city_script.exists():
        success2 = run_script(str(city_script), "City-wide data update")
    else:
        logger.error("City-wide updater script not found")
        success2 = False
    
    # Step 3: Combine extracted CSVs if needed
    combine_script = scripts_dir / "combine_csvs.py"
    if combine_script.exists():
        success3 = run_script(str(combine_script), "CSV combination")
    else:
        logger.warning("CSV combination script not found, skipping...")
        success3 = True
    
    # Step 4: Data analysis
    analyze_script = scripts_dir / "analyze_calgary_data.py"
    if analyze_script.exists():
        success4 = run_script(str(analyze_script), "Data quality analysis")
    else:
        logger.warning("Analysis script not found, skipping...")
        success4 = True
    
    # Summary
    print("\n" + "=" * 50)
    print("PROCESSING SUMMARY:")
    
    if success1:
        print("✅ District data extraction")
    else:
        print("❌ District data extraction")
    
    if success2:
        print("✅ City-wide data update")
    else:
        print("❌ City-wide data update")
    
    if success3:
        print("✅ CSV combination")
    else:
        print("❌ CSV combination")
    
    if success4:
        print("✅ Data quality analysis")
    else:
        print("❌ Data quality analysis")
    
    if all([success1, success2, success3, success4]):
        print("\n🎉 All processing completed successfully!")
        return True
    else:
        print("\n⚠️  Some steps failed - check logs above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)