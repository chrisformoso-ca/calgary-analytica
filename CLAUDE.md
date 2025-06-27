# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Calgary Analytica transforms Calgary's fragmented data landscape into actionable intelligence through AI-augmented development delivering value through its thre engine system. The data-engine aggregates data from CREB, City of Calgary, and other sources into a single source of truth. The product-engine utilizes data into data tools, apps and dashboards for different stakeholders. And the content-engine utilizes the aggregated data to create content for data-driven decision making and awareness.

**Tech Stack**: Python (extraction) + SQLite (storage) + HTML/JS/D3.js (web) + Boring technology that works

## Common Commands

### Data Pipeline Operations
```bash
# Monthly data update
python3 data-engine/cli/monthly_update.py --month 6 --year 2025

# Validation workflow
python3 data-engine/cli/validate_pending.py --list          # List pending items
python3 data-engine/cli/validate_pending.py --interactive   # Manual review

# Load approved data
cd data-engine/cli && python3 load_approved_data.py

# Alternative: Direct CSV load (for simple CSVs without validation structure)
cd data-engine/cli && python3 load_csv_direct.py

# Database status check
cd data-lake && sqlite3 calgary_data.db "SELECT COUNT(*) FROM housing_city_monthly;"
```

## High-Level Architecture

### Data Flow: RAW → CSV → VALIDATE → DATABASE

```
/data-engine/[source]/raw/     # Original PDFs, Excel files
    ↓
/data-engine/[source]/scripts/ # Extraction scripts output to...
    ↓
/data-engine/validation/pending/     # Human reviews CSVs here
    ↓
/data-engine/validation/approved/    # Approved CSVs loaded by...
    ↓
/data-lake/calgary_data.db  # Central SQLite database
```

### Key Components

1. **ConfigManager** (`/config/config_manager.py`)
   - Centralized path management
   - Always use: `from config.config_manager import get_config`
   - Never hardcode paths

2. **Data Engine** (extractors in each source directory)
   - Each source has its own extraction scripts
   - Outputs CSVs with confidence scores to validation queue
   - Simple, manual process - no autonomous agents

3. **Validation Pipeline** (`/data-engine/validation/`)
   - All data requires manual review (no auto-approval)
   - Simple workflow: pending → approved → loaded
   - Maintains full audit trail

4. **Database Schema**
   - `housing_city_monthly`: City-wide aggregates (5 property types)
   - `housing_district_monthly`: District breakdowns (8 districts × 4 types)
   - `economic_indicators_monthly`: Economic data
   - `crime_statistics_monthly`: Crime statistics

### Source Organization

Each data source is self-contained:
- `/data-engine/creb/` - CREB housing data
- `/data-engine/economic/` - Economic indicators
- `/data-engine/police/` - Crime statistics

Each source contains:
- `raw/` - Original data files
- `scripts/` - Extraction scripts
- `patterns/` - Successful extraction patterns
- `notes.md` - Source-specific documentation
- `config.json` - Source configuration

## Documentation Structure & Conventions

### Directory Documentation Rules
- **One notes.md per data source** - All documentation for a source stays in its directory
- **No separate docs/ directories** - Avoid scattered documentation
- **Methodology sections** - Complex transformations go in source's notes.md

### Documentation Hierarchy
```
/data-engine/[source]/
├── notes.md           # Primary documentation for this source
│   ├── Overview
│   ├── Data Sources
│   ├── Extraction Methods
│   ├── Data Quality Notes
│   └── Methodology (if complex transformations)
├── patterns/          # Successful extraction patterns
└── config.json        # Source configuration
```

### Naming Conventions

#### Extractors
- Main: `extractor.py`
- Variants: `extractor_[type].py` (e.g., `extractor_311_monthly.py`)
- Analysis: `analyze_[purpose].py` (e.g., `analyze_categories.py`)

#### Output Files
- CSV: `[source]_[type]_[timestamp].csv`
- JSON: `[source]_[type]_[timestamp].json` (validation report)
- Examples:
  - `creb_housing_city_20250625_143022.csv`
  - `calgary_portal_311_monthly_20250625_143022.csv`

#### Database Tables
- Monthly aggregates: `[domain]_[type]_monthly`
- Raw data: `[domain]_[type]`
- Examples:
  - `service_requests_311_monthly`
  - `housing_city_monthly`

### notes.md Template
```markdown
# [Source Name] Notes

## Overview
Brief description of data source and purpose

## Data Sources
- Primary source: [URL/location]
- Update frequency: [monthly/daily/etc]
- Historical coverage: [date range]

## Extraction Methods
- Tool/library used
- Key challenges
- Success patterns

## Data Quality Notes
- Known issues
- Filtering decisions
- Validation thresholds

## [Methodology] (if applicable)
For complex transformations like aggregations
```

## Critical Data Pipeline Rules

1. **NEVER bypass validation** - All data goes through `/validation/pending/`
2. **NEVER write directly to database** - Only `load_approved_data.py` or `load_csv_direct.py` does this
3. **ALWAYS use ConfigManager** - No hardcoded paths
4. **ALWAYS check confidence scores** - Review carefully when < 90%
5. **ALWAYS preserve audit trail** - Archive processed files

## Expected Data Volumes

Per month:
- Housing City: 5 records
- Housing District: 32 records
- Economic: 10-15 indicators
- Total: ~50 records/month

## Human-AI Partnership

**Human (Chris)**: Strategic vision, data validation, quality assurance
**Claude Code**: Technical implementation, extraction, pattern recognition

## Guiding Principles

# Always Keep It Simple and Consistent for a non-technical human solo dev
# Remove all enterprise patterns and abstractions

- Use boring, proven technology
- Every feature must save Calgary professionals time
- No fancy abstractions or enterprise patterns
- Direct, simple code that works

## Documentation

- `/specs/data-flow.md`: Complete pipeline documentation
- `/data-engine/CLAUDE.md`: Data engine specific instructions
- `/README.md`: Project overview and workflows

## Data Loading and Audit Trail

When using `load_csv_direct.py`:
- CSV files are moved from `/validation/approved/` to `/validation/processed/`
- JSON validation reports are archived to `/validation/reports/YYYY/MM/`
- This provides a complete audit trail of all data loads
- Reports are organized by year and month for easy access

## Validation Guidelines

- Make sure human/user approves it manually. Make sure not to approve pending validations yourself.