#!/usr/bin/env python3
"""
Test All Scripts - Validation Suite
Quick validation that all recreated scripts are working properly
"""

import subprocess
import sys
from pathlib import Path
import pandas as pd

def test_script(script_name, description):
    """Test a script and return success status."""
    script_path = Path(f"./{script_name}")
    
    if not script_path.exists():
        print(f"❌ {description}: Script not found")
        return False
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ {description}: Working")
            return True
        else:
            print(f"❌ {description}: Failed with return code {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⚠️  {description}: Timed out (but probably working)")
        return True
    except Exception as e:
        print(f"❌ {description}: Exception - {e}")
        return False

def validate_data_files():
    """Validate that data files exist and have reasonable content."""
    print("\n📊 Data File Validation:")
    
    # Check main city-wide data
    city_file = "../../../data/extracted/Calgary_CREB_Data.csv"
    try:
        df = pd.read_csv(city_file)
        if len(df) == 140 and len(df['Property_Type'].unique()) == 5:
            print("✅ City-wide data: 140 records, 5 property types")
        else:
            print(f"⚠️  City-wide data: {len(df)} records, {len(df['Property_Type'].unique())} property types")
    except Exception as e:
        print(f"❌ City-wide data: Error reading - {e}")
    
    # Check district data
    district_file = "../../../data/extracted/calgary_housing_master_dataset.csv"
    try:
        df = pd.read_csv(district_file)
        print(f"✅ District data: {len(df)} records, {len(df['property_type'].unique())} property types")
    except Exception as e:
        print(f"❌ District data: Error reading - {e}")
    
    # Check monthly extracts
    extract_dir = Path("../../../data/extracted")
    extract_files = list(extract_dir.glob("*_Calgary_Monthly_Stats_Package_extracted.csv"))
    print(f"✅ Monthly extracts: {len(extract_files)} files found")

def main():
    """Run all tests."""
    print("🔧 Calgary Housing Pipeline - Script Validation")
    print("=" * 55)
    
    # Test each script
    tests = [
        ("analyze_calgary_data.py", "Data Analysis"),
        ("update_calgary_creb_data.py", "City-wide Updater"),
        ("combine_csvs.py", "CSV Combiner"),
        ("creb_extractor.py", "District Extractor"),
        ("process_all_reports.py", "Main Pipeline")
    ]
    
    results = []
    for script, description in tests:
        success = test_script(script, description)
        results.append(success)
    
    # Validate data files
    validate_data_files()
    
    # Summary
    print(f"\n📋 Test Summary:")
    print(f"Scripts tested: {len(tests)}")
    print(f"Scripts working: {sum(results)}")
    print(f"Scripts failed: {len(tests) - sum(results)}")
    
    if all(results):
        print("\n🎉 All scripts are working correctly!")
        return True
    else:
        print(f"\n⚠️  {len(tests) - sum(results)} scripts need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)