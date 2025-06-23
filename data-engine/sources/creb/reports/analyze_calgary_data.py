#!/usr/bin/env python3
"""
Analyze Calgary CREB data for quality and insights
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def analyze_calgary_data():
    """Analyze the Calgary CREB data."""
    
    csv_path = "../../../data/extracted/Calgary_CREB_Data.csv"
    
    # Load data
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records from {csv_path}")
    
    # Basic info
    print(f"\nData Overview:")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"Property types: {list(df['Property_Type'].unique())}")
    print(f"Records per property type:")
    print(df['Property_Type'].value_counts())
    
    # Check for missing data
    print(f"\nMissing data check:")
    missing_data = df.isnull().sum()
    print(missing_data[missing_data > 0])
    
    # Data quality checks
    print(f"\nData Quality Analysis:")
    
    # Check benchmark prices (should be reasonable for Calgary)
    total_data = df[df['Property_Type'] == 'Total']
    
    if not total_data.empty:
        print(f"\nTotal Residential Analysis:")
        print(f"Sales range: {total_data['Sales'].min():,} - {total_data['Sales'].max():,}")
        print(f"Benchmark price range: ${total_data['Benchmark_Price'].min():,} - ${total_data['Benchmark_Price'].max():,}")
        print(f"Days on market range: {total_data['Days_on_Market'].min()} - {total_data['Days_on_Market'].max()}")
        
        # Latest month summary
        latest_month = total_data['Date'].max()
        latest_data = df[df['Date'] == latest_month]
        
        print(f"\nLatest Month ({latest_month}) Summary:")
        print(latest_data[['Property_Type', 'Sales', 'Benchmark_Price', 'Days_on_Market']].to_string(index=False))
        
        # Benchmark price trends
        print(f"\nBenchmark Price Trends (Total Residential):")
        recent_total = total_data.tail(6)  # Last 6 months
        for _, row in recent_total.iterrows():
            print(f"  {row['Date']}: ${row['Benchmark_Price']:,}")
    
    # Show completeness
    print(f"\nData Completeness:")
    expected_months = pd.date_range('2023-01', '2025-04', freq='MS').strftime('%Y-%m')
    property_types = df['Property_Type'].unique()
    
    for prop_type in property_types:
        prop_data = df[df['Property_Type'] == prop_type]
        actual_months = set(prop_data['Date'].tolist())
        missing_months = set(expected_months) - actual_months
        
        if missing_months:
            print(f"  {prop_type}: Missing {len(missing_months)} months: {sorted(missing_months)}")
        else:
            print(f"  {prop_type}: Complete ✓")

if __name__ == "__main__":
    analyze_calgary_data()