#!/usr/bin/env python3
"""Simple test to check Python environment"""

print("Python is working!")
print("Testing imports...")

try:
    import pandas as pd
    print("✓ pandas imported successfully")
except ImportError as e:
    print(f"✗ pandas import failed: {e}")

try:
    import requests
    print("✓ requests imported successfully") 
except ImportError as e:
    print(f"✗ requests import failed: {e}")

try:
    import openpyxl
    print("✓ openpyxl imported successfully")
except ImportError as e:
    print(f"✗ openpyxl import failed: {e}")

print("\nChecking file access...")
import os
raw_dir = "/home/chris/calgary-analytica/data-engine/cmhc/rent/raw"
if os.path.exists(raw_dir):
    files = [f for f in os.listdir(raw_dir) if f.endswith('.xlsx')]
    print(f"✓ Found {len(files)} Excel files in {raw_dir}")
else:
    print(f"✗ Directory not found: {raw_dir}")

print("\nEnvironment check complete!")