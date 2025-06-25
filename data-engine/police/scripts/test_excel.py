#!/usr/bin/env python3
"""Quick test to examine the Excel file structure"""

import pandas as pd
from pathlib import Path

file_path = Path(__file__).parent.parent / "raw" / "Monthly Community Crime Disorder Statistics updated January to April 2025.xlsx"

print(f"Examining file: {file_path.name}")
print(f"File size: {file_path.stat().st_size / 1024 / 1024:.1f} MB\n")

# Get sheet names
excel_file = pd.ExcelFile(file_path)
print(f"Sheet names: {excel_file.sheet_names}\n")

# Look at first sheet briefly
for sheet_name in excel_file.sheet_names[:1]:
    print(f"Sheet: {sheet_name}")
    df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)[:5]}...")
    print(f"\nFirst few rows:")
    print(df.head(3))
    print("\n")