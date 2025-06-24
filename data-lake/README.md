# Calgary Analytica Database

This directory contains the SQLite database for Calgary Analytica. The actual database file (`calgary_data.db`) is not included in the repository for security and size reasons.

## Database Setup

To create a new database with the correct schema:

```bash
cd data-lake
sqlite3 calgary_data.db < schema.sql
```

## Database Tables

- **housing_city_monthly**: City-wide housing statistics by property type
- **housing_district_monthly**: District-level housing statistics  
- **economic_indicators_monthly**: Economic indicators (unemployment, oil prices, etc.)
- **crime_statistics_monthly**: Crime statistics by community

## Loading Data

After creating the database, use the data pipeline to populate it:

1. Extract data from sources (CREB PDFs, Excel files)
2. Validate the extracted CSVs
3. Load approved data using `data-engine/core/load_csv_direct.py`

See the main README for detailed pipeline instructions.