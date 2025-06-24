# Economic Data Pipeline Updates - June 2025

## What Changed

1. **Time Series Extraction**: Now extracts ALL monthly data from Excel files, not just one month
2. **Smart Deduplication**: Newer files update historical data automatically
3. **Value Type Classification**: Distinguishes between absolute values, rates, and year-over-year changes
4. **Simplified Structure**: Removed redundant columns (date_label, file_date)

## New Workflow

### 1. Extract Time Series Data
```bash
# Extract specific years
python3 data-engine/economic/scripts/extractor_timeseries.py --year-start 2024 --year-end 2025

# Or extract all available data (2016-2025) - takes ~2 minutes
python3 data-engine/economic/scripts/extractor_timeseries.py --year-start 2016 --year-end 2025
```

### 2. Apply Database Migration (One Time Only)
```bash
# Add value_type column to database
sqlite3 data-lake/calgary_data.db < data-engine/core/migrations/add_value_type_column.sql
```

### 3. Review and Approve Data
```bash
# Check what was extracted
python3 data-engine/cli/validate_pending.py --list

# Review the CSV
less data-engine/validation/pending/economic_timeseries_*.csv

# If looks good, move to approved
mv data-engine/validation/pending/economic_timeseries_*.csv data-engine/validation/approved/
```

### 4. Load to Database
```bash
# Load the approved CSV
cd data-engine/core && python3 load_csv_direct.py

# Update metadata tracking
python3 update_economic_metadata.py
```

### 5. Verify Results
```bash
# Check database
sqlite3 data-lake/calgary_data.db "SELECT date, indicator_type, value, value_type FROM economic_indicators_monthly WHERE date >= '2025-01-01' LIMIT 10;"

# Check metadata
python3 data-engine/core/update_economic_metadata.py --status
```

## Key Benefits

- **Complete Historical Data**: Each Excel file contains 12-18 months of data, all captured
- **Automatic Updates**: Newer files correct/update historical values
- **Better Classification**: value_type field prevents misinterpretation
- **Audit Trail**: source_file and extraction_date track data provenance

## Example Output

```
date        indicator_type     value    unit        value_type
2025-05-01  unemployment_rate  8.1      percentage  rate
2025-05-01  population        1567.7   thousands   absolute  
2025-05-01  oil_price_wti     62.17    USD/barrel  absolute
2025-05-01  avg_wage_growth   0.8      percentage  yoy_change
```

## Notes

- The JSON file in pending/ is a validation report for quick quality checks
- Files processed: ~195 Excel files available (2009-2025)
- Expected records: ~10,000+ when processing full historical data
- Processing time: ~2 minutes for full extraction