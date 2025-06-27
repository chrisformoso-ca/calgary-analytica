#!/usr/bin/env python3
"""
Create sample SQLite database for PHP dashboard demo
"""

import sqlite3
import json
from pathlib import Path

# Create database directory if it doesn't exist
Path('database').mkdir(exist_ok=True)

# Connect to database
conn = sqlite3.connect('database/sample.db')
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS housing_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    property_type TEXT NOT NULL,
    benchmark_price REAL NOT NULL,
    total_sales INTEGER NOT NULL,
    price_change_yoy REAL NOT NULL,
    inventory INTEGER NOT NULL,
    UNIQUE(date, property_type)
)
''')

# Sample data (same as JSON file)
data = [
    ("2024-01", "Detached", 742300, 512, 8.2, 1243),
    ("2024-01", "Semi-Detached", 641400, 89, 9.1, 156),
    ("2024-01", "Row", 413200, 145, 10.5, 298),
    ("2024-01", "Apartment", 336700, 367, 12.3, 892),
    ("2024-02", "Detached", 748900, 623, 7.8, 1178),
    ("2024-02", "Semi-Detached", 645200, 102, 8.5, 143),
    ("2024-02", "Row", 418100, 178, 9.8, 276),
    ("2024-02", "Apartment", 339400, 421, 11.7, 834),
    ("2024-03", "Detached", 755600, 834, 7.2, 1345),
    ("2024-03", "Semi-Detached", 649800, 134, 7.9, 167),
    ("2024-03", "Row", 422300, 234, 9.1, 312),
    ("2024-03", "Apartment", 342100, 512, 10.9, 923),
    ("2024-04", "Detached", 761200, 923, 6.5, 1423),
    ("2024-04", "Semi-Detached", 653600, 145, 7.2, 189),
    ("2024-04", "Row", 425800, 267, 8.3, 334),
    ("2024-04", "Apartment", 344500, 589, 10.1, 1012),
    ("2024-05", "Detached", 768400, 1045, 5.9, 1567),
    ("2024-05", "Semi-Detached", 658200, 167, 6.5, 201),
    ("2024-05", "Row", 429700, 298, 7.6, 356),
    ("2024-05", "Apartment", 347300, 634, 9.3, 1089),
    ("2024-06", "Detached", 773100, 987, 5.2, 1623),
    ("2024-06", "Semi-Detached", 661400, 156, 5.8, 213),
    ("2024-06", "Row", 432900, 276, 6.9, 378),
    ("2024-06", "Apartment", 349600, 602, 8.5, 1134),
]

# Insert data
cursor.executemany('''
    INSERT OR REPLACE INTO housing_data 
    (date, property_type, benchmark_price, total_sales, price_change_yoy, inventory)
    VALUES (?, ?, ?, ?, ?, ?)
''', data)

# Create an index for better query performance
cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_date_property 
    ON housing_data(date, property_type)
''')

# Commit and close
conn.commit()
conn.close()

print("Database created successfully at database/sample.db")
print(f"Inserted {len(data)} records")