# Calgary CREB Data Updater (Unified)

This directory contains scripts to maintain and update both Calgary housing datasets from PDF reports.

## Overview

The Calgary CREB data pipeline processes two complementary datasets:

### 1. City-Wide Data (`Calgary_CREB_Data.csv`)
Monthly housing statistics for 5 property types:
- **Total**: All residential properties combined (page 11)
- **Detached**: Single family detached homes (page 13)  
- **Apartment**: Condominiums and apartments (page 17)
- **Semi_Detached**: Semi-detached homes (page 15)
- **Row**: Townhouses and row houses (page 19)

### 2. District-Level Data (`calgary_housing_master_dataset.csv`)
Detailed breakdown by Calgary districts and property types (page 7):
- District-specific metrics for each property type
- Sales, listings, inventory, pricing data
- Year-over-year and month-over-month changes

## Files

### Data Files
- `data/extracted/Calgary_CREB_Data.csv` - City-wide monthly housing statistics
- `data/extracted/calgary_housing_master_dataset.csv` - District-level detailed data
- `data/raw_pdfs/` - Directory containing CREB monthly PDF reports

### Scripts
- `update_calgary_creb_data.py` - **Unified updater script** (RECOMMENDED)
- `creb_extractor.py` - District data extractor (standalone)
- `combine_csvs.py` - Combines monthly extracts into master dataset
- `analyze_calgary_data.py` - Data quality analysis
- `process_all_reports.py` - Full pipeline processing
- `city_totals_extractor_*.py` - Previous extraction attempts (archived)

## Usage

### Update Both Datasets with Latest PDF (RECOMMENDED)

When a new CREB monthly report is released, use the **unified updater**:

1. **Download** the new PDF to `data/raw_pdfs/`
2. **Run the unified updater**:
   ```bash
   cd /home/chris/calgary-housing-pipeline
   python scripts/update_calgary_creb_data.py
   ```

The unified script will:
- 📊 **City-wide data**: Extract from pages 11, 13, 15, 17, 19
- 🏘️ **District data**: Extract from page 7
- Load existing data for both datasets
- Find the latest PDF report  
- Identify missing months and data
- Update both CSV files
- Create backups of previous versions
- Skip processing if data already exists (no duplicates)

### Analyze Data Quality

To check data completeness and quality:
```bash
python scripts/analyze_calgary_data.py
```

### Advanced Options

```bash
# Specify custom paths for both datasets
python scripts/update_calgary_creb_data.py \
  --csv-path /path/to/city_data.csv \
  --district-csv-path /path/to/district_data.csv \
  --pdf-dir /path/to/pdfs

# Force re-extraction of latest month (both datasets)
python scripts/update_calgary_creb_data.py --force

# Get help and see all options
python scripts/update_calgary_creb_data.py --help
```

### Individual Dataset Processing

If you need to process only one dataset:

```bash
# City-wide data only (pages 11,13,15,17,19)
# Use the unified updater - it will skip district processing if that data exists

# District data only (page 7)
python scripts/creb_extractor.py
python scripts/combine_csvs.py
```

## Data Structure

### City-Wide Data (`Calgary_CREB_Data.csv`)
- `Date` - YYYY-MM format (e.g., "2025-04")
- `Property_Type` - One of: Total, Detached, Apartment, Semi_Detached, Row
- `Sales` - Number of sales in the month
- `New_Listings` - Number of new listings
- `Inventory` - Total active listings
- `Days_on_Market` - Average days properties stay on market
- `Benchmark_Price` - CREB benchmark price (dollars)
- `Median_Price` - Median sale price (dollars)
- `Average_Price` - Average sale price (dollars)

### District Data (`calgary_housing_master_dataset.csv`)
- `property_type` - Property category (Detached, Apartment, Row, Semi-detached)
- `district` - Calgary district (City Centre, North, South, East, West, etc.)
- `new_sales` - Monthly sales count
- `new_listings` - Monthly new listings
- `sales_to_listings_ratio` - Sales/listings percentage
- `inventory` - Active listings count
- `months_supply` - Inventory duration at current sales pace
- `benchmark_price` - CREB benchmark price
- `yoy_price_change` - Year-over-year price change %
- `mom_price_change` - Month-over-month price change %
- `month`, `year`, `date` - Time identifiers

## Data Quality

### City-Wide Dataset (as of 2025-04):
- **Complete**: All property types have data from 2023-01 to 2025-04
- **140 total records** (28 months × 5 property types)
- **No missing values**
- **Reasonable price ranges** for Calgary market

### District Dataset (as of 2025-04):
- **512+ records** covering 2024-01 to 2025-04
- **4 property types** across **8 Calgary districts**
- Comprehensive district-level coverage
- Detailed pricing and market metrics

### Benchmark Price Ranges (April 2025)
- Total Residential: ~$591,100
- Detached: ~$769,300  
- Apartment: ~$336,000
- Semi-Detached: ~$691,700
- Row: ~$457,400

## Troubleshooting

### Common Issues

1. **"No PDF found"**
   - Check that PDF files are in `data/raw_pdfs/`
   - Ensure filename format: `MM_YYYY_Calgary_Monthly_Stats_Package.pdf`

2. **"No new data extracted"**
   - PDF formatting may have changed
   - Check debug logs for parsing errors
   - Manual verification may be needed

3. **"Unrealistic prices"**
   - PDF number formatting issues (spaces in numbers)
   - Script includes validation and correction logic

### Backup Recovery

If an update goes wrong:
```bash
# Restore from backup
mv Calgary_CREB_Data.csv.backup Calgary_CREB_Data.csv
```

## Workflow Summary

**For routine updates (RECOMMENDED):**
1. Download new CREB PDF to `data/raw_pdfs/`
2. Run: `python scripts/update_calgary_creb_data.py`
3. ✅ Both datasets updated automatically!

**For initial setup or troubleshooting:**
- Use individual scripts (`creb_extractor.py`, `combine_csvs.py`)
- Run full pipeline (`process_all_reports.py`)
- Analyze data quality (`analyze_calgary_data.py`)

## Future Enhancements

Potential improvements:
- Automated PDF download from CREB website
- Email notifications when new data is available
- Data visualization dashboard
- API endpoint for accessing the data

## Contact

For issues or questions about the data updater, check the Calgary housing pipeline documentation.