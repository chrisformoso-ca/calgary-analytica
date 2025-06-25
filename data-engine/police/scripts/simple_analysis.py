#!/usr/bin/env python3
"""Simple analysis of police data structure"""

import pandas as pd
from pathlib import Path

file_path = Path(__file__).parent.parent / "raw" / "Monthly Community Crime Disorder Statistics updated January to April 2025.xlsx"

# Read first sheet with limited rows to understand structure
df = pd.read_excel(file_path, sheet_name='Crime Overview', nrows=100)

print("=== CRIME OVERVIEW SHEET ANALYSIS ===")
print(f"Shape: {df.shape}")
print(f"\nColumns: {list(df.columns)}")

# Show unique values for each column
for col in df.columns:
    unique_vals = df[col].dropna().unique()
    print(f"\n{col} ({len(unique_vals)} unique values):")
    if len(unique_vals) <= 20:
        for val in sorted(str(v) for v in unique_vals):
            print(f"  - {val}")
    else:
        sample = sorted(str(v) for v in unique_vals)[:10]
        for val in sample:
            print(f"  - {val}")
        print(f"  ... and {len(unique_vals) - 10} more")

print("\n=== SAMPLE DATA ===")
print(df[['Crime Type', 'Category', 'Community', 'Date - Month', 'Total Crime']].head(20))

# Check other sheets briefly
print("\n=== OTHER SHEETS ===")
for sheet in ['Domestics', 'Disorder']:
    df_sheet = pd.read_excel(file_path, sheet_name=sheet, nrows=10)
    print(f"\n{sheet} sheet columns: {list(df_sheet.columns)}")
    print(f"Shape: {df_sheet.shape}")