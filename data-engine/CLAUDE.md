# Data Engine Instructions for Claude Code

This file provides specific guidance for working with the data-engine directory.

## Simple Data Flow (NO EXCEPTIONS)

```
RAW FILES → Extract to CSV → Human Reviews → Load to Database
```

1. **Extract**: Scripts in `/{source}/scripts/` read raw files and output CSV to `/validation/pending/`
2. **Review**: Human manually checks CSVs and moves good ones to `/validation/approved/`
3. **Load**: Run `load_approved_data.py` to insert approved CSVs into database

## Directory Structure (Source-Based Organization)

```
data-engine/
├── creb/                    # CREB housing data
│   ├── raw/                # PDF files (MM_YYYY_Calgary_Monthly_Stats_Package.pdf)
│   ├── scripts/            # extractor.py, extract_all_historical.py
│   ├── patterns/           # extraction_patterns.json
│   ├── config.json        # Source configuration
│   └── notes.md           # CREB-specific documentation
├── economic/               # Economic indicators
│   ├── raw/               # Excel/PDF files
│   ├── scripts/           # extractor.py
│   ├── patterns/          # Extraction patterns
│   ├── config.json       # Source configuration
│   └── notes.md          # Economic data tips
├── police/                # Crime statistics
│   ├── raw/              # Excel files
│   ├── scripts/          # extractor.py
│   ├── patterns/         # Extraction patterns
│   ├── config.json      # Source configuration
│   └── notes.md         # Crime data documentation
├── validation/            # Human review pipeline
│   ├── pending/          # New extractions waiting for review
│   ├── approved/         # Human-approved, ready to load
│   ├── rejected/         # Failed validation
│   └── processed/        # Successfully loaded to DB
├── core/                  # Core functionality
│   ├── data_engine.py    # Orchestrates extraction
│   ├── load_approved_data.py # Loads to database (expects validation structure)
│   └── load_csv_direct.py # Simple CSV loader (direct from approved/)
└── cli/                   # Command line scripts
    ├── monthly_update.py  # Main update script
    └── validate_pending.py # Review pending CSVs
```

## Common Tasks

### Monthly Housing Update
```bash
# 1. Make sure PDF is in /creb/raw/
# 2. Run extraction
python cli/monthly_update.py --month 6 --year 2025

# 3. Review what was extracted
python cli/validate_pending.py --list

# 4. Manually review
python cli/validate_pending.py --interactive

# 5. Load approved data
cd core && python load_approved_data.py
```

### Check What's Pending
```bash
ls -la validation/pending/
```

### Manual Approval (Simple Way)
```bash
# If CSV looks good, move it
mv validation/pending/[filename] validation/approved/

# Then load it
cd core && python load_approved_data.py

# OR use the simple loader for CSVs directly in approved/
cd core && python load_csv_direct.py
```

## Important Rules

1. **NEVER skip validation** - All data goes through pending first
2. **NEVER write directly to database** - Only load_approved_data.py or load_csv_direct.py does this
3. **ALWAYS check confidence scores** - Low confidence needs extra review
4. **KEEP it simple** - No fancy abstractions or enterprise patterns

## Expected Data Volumes

Per month:
- Housing City: 5 records (property types)
- Housing District: 32 records (8 districts × 4 types)
- Economic: ~10-15 indicators
- Total: ~50 records/month

## Which Loader to Use?

**load_approved_data.py**: 
- For data processed through the full validation pipeline
- Expects subdirectories in approved/ with validation_report.json files
- Used by automated workflows

**load_csv_direct.py**:
- For simple CSV files placed directly in approved/
- Auto-detects table type from column names
- Good for historical data loads or manual CSV imports
- Handles column mapping and data type conversions automatically

## Troubleshooting

**Extraction failed?**
- Check the PDF exists in the source's `/raw/` directory
- Look at confidence score - if < 90%, extraction may have issues
- Check logs in `/validation/logs/`
- Review source-specific notes in `/{source}/notes.md`

**Wrong data in pending?**
- Move to rejected: `mv validation/pending/[file] validation/rejected/`
- Document why in a text file

**Need to re-extract?**
- Just run the extraction again - it creates new timestamped files
- Old attempts stay in pending until you clean them up

## Database Tables

- `housing_city_monthly` - City-wide totals
- `housing_district_monthly` - District breakdowns  
- `economic_indicators_monthly` - Economic data
- `crime_statistics_monthly` - Crime stats

Check what's in database:
```bash
cd /home/chris/calgary-analytica/data-lake
sqlite3 calgary_data.db "SELECT COUNT(*) FROM housing_city_monthly;"
```

Keep it simple. Extract → Review → Load. That's it.