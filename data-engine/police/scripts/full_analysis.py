#!/usr/bin/env python3
"""Full analysis of crime types and categories"""

import pandas as pd
from pathlib import Path

file_path = Path(__file__).parent.parent / "raw" / "Monthly Community Crime Disorder Statistics updated January to April 2025.xlsx"

# Read more rows to see variety
df = pd.read_excel(file_path, sheet_name='Crime Overview', nrows=5000)

print("=== FULL DATA STRUCTURE ANALYSIS ===")
print(f"Total rows sampled: {len(df)}")

# Crime types
crime_types = df['Crime Type'].dropna().unique()
print(f"\nCrime Types ({len(crime_types)}):")
for ct in sorted(crime_types):
    count = len(df[df['Crime Type'] == ct])
    print(f"  - {ct}: {count} rows")

# Categories by crime type
print("\nCategories by Crime Type:")
for ct in sorted(crime_types):
    print(f"\n{ct}:")
    categories = df[df['Crime Type'] == ct]['Category'].dropna().unique()
    for cat in sorted(categories)[:20]:  # Show first 20
        print(f"  - {cat}")
    if len(categories) > 20:
        print(f"  ... and {len(categories) - 20} more")

# Date analysis
print("\n=== DATE ANALYSIS ===")
years = sorted(df['Date - Year'].dropna().unique())
print(f"Years: {years}")

# 2025 data specifically
df_2025 = df[df['Date - Year'] == 2025]
print(f"\n2025 Data:")
print(f"Total rows: {len(df_2025)}")
months_2025 = df_2025['Date - Month'].dropna().unique()
print(f"Months: {sorted(months_2025)}")

# Communities
communities = df['Community'].dropna().unique()
print(f"\n=== COMMUNITIES ({len(communities)}) ===")
print("First 20 communities:")
for comm in sorted(communities)[:20]:
    print(f"  - {comm}")

# Sample of 2025 data with all crime types
print("\n=== SAMPLE 2025 DATA (Different Crime Types) ===")
for ct in crime_types:
    sample = df_2025[df_2025['Crime Type'] == ct].head(2)
    if not sample.empty:
        print(f"\n{ct}:")
        print(sample[['Category', 'Community', 'Date - Month', 'Total Crime']].to_string(index=False))

# Check Total Crime values
print("\n=== TOTAL CRIME VALUES ===")
crime_values = df['Total Crime'].value_counts().head(20)
print(crime_values)