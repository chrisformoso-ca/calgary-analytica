#!/usr/bin/env python3
"""Check all disorder types"""

import pandas as pd
from pathlib import Path

file_path = Path(__file__).parent.parent / "raw" / "Monthly Community Crime Disorder Statistics updated January to April 2025.xlsx"

# Read full Disorder sheet
print("Loading Disorder sheet...")
df_dis = pd.read_excel(file_path, sheet_name='Disorder')

print(f"Total rows: {len(df_dis):,}")

# All disorder types
disorder_types = df_dis['Disorder Type'].dropna().unique()
print(f"\nAll Disorder Types ({len(disorder_types)}):")
for dt in sorted(disorder_types):
    count = len(df_dis[df_dis['Disorder Type'] == dt])
    print(f"  - {dt}: {count:,} rows")

# Check 2025 data
df_2025 = df_dis[df_dis['Call_Received_Timestamp - Year'] == 2025]
print(f"\n2025 Disorder Data: {len(df_2025):,} rows")
print(f"Communities: {len(df_2025['Community'].dropna().unique())}")

# Sample data
print("\nSample 2025 Disorder data:")
for dt in disorder_types[:5]:
    sample = df_2025[df_2025['Disorder Type'] == dt].head(1)
    if not sample.empty:
        print(f"\n{dt}:")
        print(f"  Community: {sample.iloc[0]['Community']}")
        print(f"  Month: {sample.iloc[0]['Call_Received_Timestamp - Month']}")
        print(f"  Total: {sample.iloc[0]['Total Disorder']}")