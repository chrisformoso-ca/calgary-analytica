#!/usr/bin/env python3
"""Comprehensive analysis of police crime data Excel file"""

import pandas as pd
from pathlib import Path
import numpy as np

file_path = Path(__file__).parent.parent / "raw" / "Monthly Community Crime Disorder Statistics updated January to April 2025.xlsx"

print(f"=== CALGARY POLICE DATA ANALYSIS ===")
print(f"File: {file_path.name}")
print(f"Size: {file_path.stat().st_size / 1024 / 1024:.1f} MB\n")

# Load Excel file
excel_file = pd.ExcelFile(file_path)
print(f"Sheet names: {excel_file.sheet_names}\n")

# Analyze each sheet
for sheet_name in excel_file.sheet_names:
    print(f"\n{'='*60}")
    print(f"SHEET: {sheet_name}")
    print(f"{'='*60}")
    
    # Read the sheet
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    print(f"\nShape: {df.shape} (rows: {len(df)}, columns: {len(df.columns)})")
    print(f"\nColumn names:")
    for i, col in enumerate(df.columns):
        print(f"  {i}: {col}")
    
    # Data types
    print(f"\nData types:")
    print(df.dtypes)
    
    # Check for unique values in key columns
    print(f"\nUnique values analysis:")
    
    # Crime Type
    if 'Crime Type' in df.columns:
        crime_types = df['Crime Type'].dropna().unique()
        print(f"\nCrime Types ({len(crime_types)}):")
        for ct in sorted(crime_types)[:10]:
            print(f"  - {ct}")
        if len(crime_types) > 10:
            print(f"  ... and {len(crime_types) - 10} more")
    
    # Category
    if 'Category' in df.columns:
        categories = df['Category'].unique()
        print(f"\nCategories ({len(categories)}):")
        for cat in sorted(categories)[:15]:
            print(f"  - {cat}")
        if len(categories) > 15:
            print(f"  ... and {len(categories) - 15} more")
    
    # Community
    if 'Community' in df.columns:
        communities = df['Community'].dropna().unique()
        print(f"\nCommunities ({len(communities)}):")
        for comm in sorted(communities)[:10]:
            print(f"  - {comm}")
        if len(communities) > 10:
            print(f"  ... and {len(communities) - 10} more")
    
    # Date columns
    date_cols = [col for col in df.columns if 'Date' in col or 'Month' in col]
    if date_cols:
        print(f"\nDate-related columns: {date_cols}")
        for col in date_cols:
            print(f"  {col}: {df[col].dropna().unique()[:5].tolist()}")
    
    # Numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print(f"\nNumeric columns: {numeric_cols}")
    
    # Sample data
    print(f"\nSample data (first 5 rows):")
    print(df.head())
    
    # Check for special values like '<5'
    print(f"\nChecking for special values:")
    for col in df.columns:
        if df[col].dtype == 'object':
            special_vals = df[col].apply(lambda x: str(x) if pd.notna(x) else '').str.contains('<', na=False).sum()
            if special_vals > 0:
                print(f"  {col}: {special_vals} cells contain '<' (likely <5)")
    
    # Value ranges for numeric columns
    if 'Total Crime' in df.columns:
        print(f"\nTotal Crime statistics:")
        # Convert to numeric, treating '<5' as 2.5
        crime_vals = df['Total Crime'].apply(lambda x: 2.5 if str(x).strip() == '<5' else pd.to_numeric(x, errors='coerce'))
        print(f"  Min: {crime_vals.min()}")
        print(f"  Max: {crime_vals.max()}")
        print(f"  Mean: {crime_vals.mean():.2f}")
        print(f"  Total incidents: {crime_vals.sum():.0f}")

print("\n\n=== EXTRACTION STRATEGY RECOMMENDATIONS ===")
print("""
Based on the analysis, the data appears to be in a long format where:
- Each row represents: Crime Type + Category + Community + Month
- The 'Total Crime' column contains the incident count
- Special value '<5' appears for small counts (privacy protection)
- Data covers January to April 2025

Key fields to extract:
1. Date (from 'Date - Month' column)
2. Community 
3. Crime Type (maps to our crime_category)
4. Category (maps to our crime_type)
5. Total Crime (incident_count)
6. Ward and Police District (for additional context)

The extractor should:
1. Read each sheet separately
2. Handle '<5' values (convert to 2 or 2.5)
3. Map Crime Type to our categories (violent, property, etc.)
4. Aggregate by community for analysis
5. Calculate severity indices based on crime types
""")