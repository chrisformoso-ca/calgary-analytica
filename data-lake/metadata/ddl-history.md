# DDL History - Calgary Data Lake

Track structural changes to the database schema.

## 2025-07-04
- Added rental market tables:
  - `rental_listings_snapshot` - Weekly snapshots of RentFaster rental listings
  - `rental_market_summary_weekly` - Aggregated weekly rental market statistics
  - Created views: `current_rental_market`, `rental_comparison_by_type`
  - Populated existing `rental_market_annual` table with CMHC historical data (2018-2024)

## 2025-06-24
- Modified `crime_statistics_monthly` table:
  - Added columns: `year INTEGER`, `ward TEXT`, `police_district TEXT`
  - Changed `community` from NOT NULL to nullable (for privacy-protected domestic violence data)
- Recreated table with new schema to accommodate police data structure

## 2025-06-23
- Created initial schema:
  - `housing_city_monthly` - City-wide housing statistics
  - `housing_district_monthly` - District-level housing data
  - `economic_indicators_monthly` - Economic indicators time series
  - `crime_statistics_monthly` - Crime statistics by community

## Schema Conventions
- All tables include metadata columns: `extracted_date`, `confidence_score`, `validation_status`
- Date columns use TEXT format (YYYY-MM-DD)
- Monetary values stored as INTEGER (no decimals) or REAL (with decimals)
- All tables have auto-incrementing ID as primary key