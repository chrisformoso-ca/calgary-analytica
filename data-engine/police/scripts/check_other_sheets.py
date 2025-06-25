#!/usr/bin/env python3
"""Check Domestics and Disorder sheets"""

import pandas as pd
from pathlib import Path

file_path = Path(__file__).parent.parent / "raw" / "Monthly Community Crime Disorder Statistics updated January to April 2025.xlsx"

# Check Domestics sheet
print("=== DOMESTICS SHEET ===")
df_dom = pd.read_excel(file_path, sheet_name='Domestics', nrows=1000)
print(f"Shape: {df_dom.shape}")
print(f"Columns: {list(df_dom.columns)}")
print(f"\nCategories:")
categories = df_dom['Category'].dropna().unique()
for cat in sorted(categories):
    print(f"  - {cat}")

# Check for 2025 data
if 'Start_Datestamp - Year' in df_dom.columns:
    years = df_dom['Start_Datestamp - Year'].dropna().unique()
    print(f"\nYears: {sorted(years)}")

# Check Disorder sheet
print("\n=== DISORDER SHEET ===")
df_dis = pd.read_excel(file_path, sheet_name='Disorder', nrows=1000)
print(f"Shape: {df_dis.shape}")
print(f"Columns: {list(df_dis.columns)}")
print(f"\nDisorder Types:")
disorder_types = df_dis['Disorder Type'].dropna().unique()
for dt in sorted(disorder_types):
    print(f"  - {dt}")

# Check for 2025 data
if 'Call_Received_Timestamp - Year' in df_dis.columns:
    years = df_dis['Call_Received_Timestamp - Year'].dropna().unique()
    print(f"\nYears: {sorted(years)}")

# Sample data
print("\n=== SAMPLE DOMESTICS DATA ===")
print(df_dom[['Category', 'Ward', 'Start_Datestamp - Month', 'Total Domestic']].head(5))

print("\n=== SAMPLE DISORDER DATA ===")
print(df_dis[['Disorder Type', 'Community', 'Call_Received_Timestamp - Month', 'Total Disorder']].head(5))