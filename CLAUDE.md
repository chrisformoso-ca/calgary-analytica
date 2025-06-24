# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Calgary Analytica transforms Calgary's fragmented data landscape into actionable intelligence through AI-augmented development delivering value through its thre engine system. The data-engine aggregates data from CREB, City of Calgary, and other sources into a single source of truth. The product-engine utilizes data into data tools, apps and dashboards for different stakeholders. And the content-engine utilizes the aggregated data to create content for data-driven decision making and awareness.

**Tech Stack**: Python (extraction) + SQLite (storage) + PHP/D3.js (web) + Boring technology that works

## Common Commands

### Data Pipeline Operations
```bash
# Monthly data update
python3 data-engine/cli/monthly_update.py --month 6 --year 2025

# Validation workflow
python3 data-engine/cli/validate_pending.py --list          # List pending items
python3 data-engine/cli/validate_pending.py --interactive   # Manual review

# Load approved data
cd data-engine/core && python3 load_approved_data.py

# Alternative: Direct CSV load (for simple CSVs without validation structure)
cd data-engine/core && python3 load_csv_direct.py

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

2. **Data Engine** (`/data-engine/core/data_engine.py`)
   - Orchestrates extraction from multiple sources
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

## Critical Data Pipeline Rules

1. **NEVER bypass validation** - All data goes through `/validation/pending/`
2. **NEVER write directly to database** - Only `load_approved_data.py` does this
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

## Validation Guidelines

- Make sure human/user approves it manually. Make sure not to approve pending validations yourself.