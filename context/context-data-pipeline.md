# Data Pipeline Context

## Extraction Workflow
1. Download CREB PDF to `/data/raw_pdfs/`
2. Run: `python3 monthly_update.py --month X --year YYYY`
3. Review validation in `/validation/pending/`
4. Data loads to `calgary_data.db`

## Extractors
- Location: `/extractors/creb_reports/`
- Success rate: ~95%
- Known issue: January 2025 PDF

## Database Schema
- **housing_city_monthly**: City-wide aggregates
- **housing_district_monthly**: District details
- **extraction_log**: Performance tracking

## Validation Rules
- City data: Expect 5 property types
- District data: Expect ~32 records (8 districts × 4 types)
- Price ranges: $250k-$900k reasonable

## Quick Fixes
```bash
# Direct extraction
cd extractors/creb_reports
python3 update_calgary_creb_data.py --pdf-dir /path/to/pdfs

# Check database
cd data-lake
python3 -c "import sqlite3; conn=sqlite3.connect('calgary_data.db'); print(conn.execute('SELECT COUNT(*), MAX(date) FROM housing_city_monthly').fetchone())"
```