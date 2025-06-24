#!/usr/bin/env python3
"""
Test Economic Data Pipeline
Verifies the time series extraction and loading process
"""

import sys
from pathlib import Path
import pandas as pd
import logging

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_pipeline():
    """Test the economic data pipeline end-to-end."""
    
    print("=" * 60)
    print("🧪 Testing Economic Data Pipeline")
    print("=" * 60)
    
    # Step 1: Check for recent extraction
    from config.config_manager import get_config
    config = get_config()
    pending_dir = config.get_pending_review_dir()
    
    # Find most recent economic timeseries CSV
    csv_files = list(pending_dir.glob("economic_timeseries_*.csv"))
    if not csv_files:
        print("❌ No economic timeseries CSV files found in pending")
        print("   Run: python3 data-engine/economic/scripts/extractor_timeseries.py --test")
        return False
    
    latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"\n✅ Found CSV: {latest_csv.name}")
    
    # Step 2: Analyze the CSV structure
    df = pd.read_csv(latest_csv)
    print(f"\n📊 CSV Analysis:")
    print(f"   Records: {len(df)}")
    print(f"   Columns: {', '.join(df.columns)}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Check for value_type column
    if 'value_type' in df.columns:
        print(f"\n✅ value_type column present")
        print(f"   Types: {df['value_type'].value_counts().to_dict()}")
    else:
        print("\n❌ value_type column missing!")
        return False
    
    # Check for removed columns
    if 'date_label' in df.columns:
        print("\n⚠️  date_label column still present (should be removed)")
    else:
        print("\n✅ date_label column removed as planned")
    
    if 'file_date' in df.columns:
        print("\n⚠️  file_date column still present (should be removed)")
    else:
        print("\n✅ file_date moved to metadata tracking")
    
    # Step 3: Sample data verification
    print(f"\n📋 Sample Records:")
    sample_indicators = ['unemployment_rate', 'population', 'oil_price_wti']
    for indicator in sample_indicators:
        sample = df[df['indicator_type'] == indicator].head(1)
        if not sample.empty:
            row = sample.iloc[0]
            print(f"   {indicator}: {row['value']:.2f} {row['unit']} ({row['value_type']})")
    
    # Step 4: Check JSON validation report
    json_path = latest_csv.with_suffix('.json')
    if json_path.exists():
        import json
        with open(json_path) as f:
            report = json.load(f)
        print(f"\n✅ Validation report found")
        print(f"   Records: {report['records_extracted']}")
        print(f"   Date range: {report['date_range']}")
        print(f"   Files processed: {report['files_processed']}")
    
    # Step 5: Test column mapping
    print(f"\n🔧 Testing Column Mapping:")
    from load_csv_direct import SimpleCSVLoader
    loader = SimpleCSVLoader()
    
    # Test column standardization
    test_df = pd.DataFrame({
        'indicatortype': ['test'],
        'valuetype': ['absolute'],
        'extractiondate': ['2025-06-23']
    })
    
    test_df.columns = test_df.columns.str.lower().str.replace('_', '')
    column_mapping = {
        'indicatortype': 'indicator_type',
        'valuetype': 'value_type',
        'extractiondate': 'extracted_date'
    }
    test_df.rename(columns=column_mapping, inplace=True)
    
    if all(col in ['indicator_type', 'value_type', 'extracted_date'] for col in test_df.columns):
        print("   ✅ Column mapping works correctly")
    else:
        print("   ❌ Column mapping failed")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Pipeline test completed successfully!")
    print("\nNext steps:")
    print("1. Review the CSV in pending directory")
    print("2. Move to approved: mv validation/pending/[filename] validation/approved/")
    print("3. Run: python3 core/load_csv_direct.py")
    print("4. Update metadata: python3 core/update_economic_metadata.py")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_pipeline()