# Calgary Analytica Data Flow Architecture

## Overview

Calgary Analytica follows a strict Extract-Transform-Load (ETL) pipeline that ensures data quality through human validation checkpoints. This document defines the canonical data flow that all Claude Code sessions must follow.

## Data Flow Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   RAW FILES     │     │    EXTRACTION    │     │   VALIDATION     │     │    DATABASE     │
├─────────────────┤     ├──────────────────┤     ├──────────────────┤     ├─────────────────┤
│ • CREB PDFs     │ --> │ • data_engine.py │ --> │ • Pending Review │ --> │ • SQLite DB     │
│ • Economic XLS  │     │ • Extractors     │     │ • Human Approval │     │ • housing_city  │
│ • Crime XLS     │     │ • CSV Output     │     │ • Confidence >90%│     │ • housing_dist  │
│                 │     │ • Patterns.json  │     │                  │     │ • economic_ind  │
└─────────────────┘     └──────────────────┘     └──────────────────┘     └─────────────────┘
      /data/raw/         → /validation/pending/  → /validation/approved/ → /data-lake/
```

## Detailed Pipeline Stages

### 1. Raw Data Sources

**Location**: `/data/raw/`

- **CREB Housing Reports**: `/data/raw/creb_pdfs/`
  - Format: `MM_YYYY_Calgary_Monthly_Stats_Package.pdf`
  - Contains: City-wide and district-level housing statistics
  - Pages: City data (11,13,15,17,19), District data (7)

- **Economic Indicators**: `/data/raw/calgary_economic_indicators/`
  - Format: `Current-Economic-Indicators-YYYY-MM.xlsx`
  - Contains: Employment, GDP, inflation, construction metrics

- **Crime Statistics**: `/data/raw/calgary_police_service/`
  - Format: Excel files with monthly crime data by community

### 2. Extraction Phase

**Scripts**: `/data-engine/sources/*/extractor.py`

**Process**:
1. DataEngine orchestrates extraction via `data_engine.py`
2. Extractors read raw files and output CSV to validation queue
3. Each extraction includes:
   - Timestamp: When extraction occurred
   - Confidence Score: 0.0 to 1.0 (target >0.90)
   - Source Reference: Original filename
   - Validation Status: 'pending'

**Output**: `/data-engine/validation/pending/`

### 3. Validation Gate

**Location**: `/data-engine/validation/`

**Structure**:
```
validation/
├── pending/      # Awaiting review
├── approved/     # Ready for database
├── rejected/     # Failed validation
├── processed/    # Successfully loaded
└── logs/         # Audit trail
```

**Rules**:
- All items require manual review (no auto-approval)
- Confidence ≥ 0.90: High confidence indicator
- Confidence < 0.90: Needs careful review
- Confidence < 0.50: Likely extraction failure

**Expected Records Per Month**:
- Housing City: 5 records (property types)
- Housing District: 32 records (8 districts × 4 types)
- Economic: 10-15 indicators
- Total: ~47-52 records/month

### 4. Database Loading

**Script**: `/data-engine/core/load_approved_data.py`

**Process**:
1. Read approved CSV files
2. Validate schema compatibility
3. Insert into appropriate table
4. Archive to `/validation/processed/`
5. Update load timestamp

**Database**: `/data-lake/calgary_data.db`

**Tables**:
- `housing_city_monthly`: City-wide aggregates
- `housing_district_monthly`: District-level detail
- `economic_indicators_monthly`: Economic metrics
- `crime_statistics_monthly`: Crime data by community

## Configuration Management

All paths are centralized in `/config/calgary_analytica.ini` and accessed via ConfigManager:

```python
from config.config_manager import get_config
config = get_config()

# Always use config methods for paths:
pending_dir = config.get_pending_review_dir()
db_path = config.get_database_path()
```

## Validation Workflow Commands

### Monthly Update (Standard Flow)
```bash
# Extract new month's data
python data-engine/cli/monthly_update.py --month 6 --year 2025
```

### Direct Extraction (When Monthly Update Fails)
```bash
cd data-engine
python -m core.data_engine creb --pdf-path /path/to/specific.pdf
```

### Manual Validation Review
```bash
# Check pending validations
ls -la data-engine/validation/pending/

# Review specific file
cat data-engine/validation/pending/[filename].csv

# Approve by moving to approved/
mv data-engine/validation/pending/[dir] data-engine/validation/approved/
```

### Load Approved Data
```bash
cd data-engine/core
python load_approved_data.py
```

## Agent Crew System

When extraction confidence < 90%, deploy parallel extraction agents:

1. **Agent A**: pdfplumber (current primary)
2. **Agent B**: Firecrawl structured extraction  
3. **Agent C**: OCR for image-based PDFs
4. **Agent D**: Web scraping fallback
5. **Agent E**: Alternative parsing methods

Best result wins and gets documented in `/data-engine/agents/patterns.json`.

## Critical Rules for Claude Code

1. **NEVER bypass validation**: All extracted data MUST go through `/validation/pending/`
2. **NEVER direct database writes**: Only `load_approved_data.py` writes to database
3. **ALWAYS use ConfigManager**: Never hardcode paths
4. **ALWAYS check confidence**: Log when confidence < 90%
5. **ALWAYS preserve audit trail**: Archive loaded files to `/validation/processed/`

## Error Handling

- Extraction failures: Log to `/validation/logs/` with full context
- Low confidence: Deploy agent crew for alternative methods
- Validation rejection: Move to `/validation/rejected/` with reason
- Database errors: Rollback transaction, keep CSV in approved/

## Monitoring & Maintenance

Regular checks:
1. Pending validation backlog
2. Extraction success rates by source
3. Database record counts vs expected
4. Pattern effectiveness in patterns.json

This data flow ensures data quality, traceability, and consistency across all Claude Code sessions.