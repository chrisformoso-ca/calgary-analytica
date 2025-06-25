#!/usr/bin/env python3
"""Check all crime types by reading full dataset"""

import pandas as pd
from pathlib import Path

file_path = Path(__file__).parent.parent / "raw" / "Monthly Community Crime Disorder Statistics updated January to April 2025.xlsx"

print("Loading full Crime Overview sheet...")
df = pd.read_excel(file_path, sheet_name='Crime Overview')

print(f"\n=== FULL DATASET ANALYSIS ===")
print(f"Total rows: {len(df):,}")
print(f"Columns: {list(df.columns)}")

# Crime types
crime_types = df['Crime Type'].dropna().unique()
print(f"\nAll Crime Types ({len(crime_types)}):")
for ct in sorted(crime_types):
    count = len(df[df['Crime Type'] == ct])
    pct = count / len(df) * 100
    print(f"  - {ct}: {count:,} rows ({pct:.1f}%)")

# Check 2025 data specifically
df_2025 = df[df['Date - Year'] == 2025]
print(f"\n=== 2025 DATA ONLY ===")
print(f"Total 2025 rows: {len(df_2025):,}")

# Crime types in 2025
crime_types_2025 = df_2025['Crime Type'].dropna().unique()
print(f"\n2025 Crime Types ({len(crime_types_2025)}):")
for ct in sorted(crime_types_2025):
    count = len(df_2025[df_2025['Crime Type'] == ct])
    print(f"  - {ct}: {count:,} rows")
    
    # Show categories for this crime type
    categories = df_2025[df_2025['Crime Type'] == ct]['Category'].dropna().unique()
    print(f"    Categories ({len(categories)}):")
    for cat in sorted(categories)[:10]:
        cat_count = len(df_2025[(df_2025['Crime Type'] == ct) & (df_2025['Category'] == cat)])
        print(f"      - {cat}: {cat_count} rows")
    if len(categories) > 10:
        print(f"      ... and {len(categories) - 10} more")

# Communities in 2025
communities_2025 = df_2025['Community'].dropna().unique()
print(f"\n2025 Communities: {len(communities_2025)}")

# Months in 2025
months_2025 = df_2025['Date - Month'].dropna().unique()
print(f"2025 Months: {sorted(months_2025)}")

# Memory usage
print(f"\nDataFrame memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")