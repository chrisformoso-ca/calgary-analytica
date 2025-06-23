# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Calgary Analytica transforms Calgary's fragmented housing data landscape into actionable intelligence through AI-augmented development. The project aggregates data from CREB, City of Calgary, and other sources into a single source of truth.

## Tech Stack

- **Data Pipeline**: Python (extraction) + SQLite (storage)
- **Web Frontend**: PHP + D3.js
- **Philosophy**: Use boring, proven technology that works

## Common Commands

### Custom Slash Commands (Recommended)
```bash
# Session management
/project:start                    # Smart session initialization
/project:save                     # Generate session summary + update next-session.md
/project:help                     # Quick command reference

# Data pipeline operations  
/project:update month 2025-06     # Process June 2025 data with validation
/project:update status            # Check database status and data freshness
/project:extract creb [path]      # Direct extraction with agent crew deployment

# Development workflows
/project:dashboard create housing-trends  # Create dashboard with standard structure
/project:load dashboard           # Load dashboard development context
```

### Legacy Python Commands (Still Supported)
```bash
# Monthly Data Update
python3 monthly_update.py --month 6 --year 2025

# First-time setup
python3 monthly_update.py --setup --import-data

# Direct Extraction (when monthly update has issues)
cd extractors/creb_reports
python3 update_calgary_creb_data.py \
  --pdf-dir /home/chris/calgary-analytica/data/raw_pdfs \
  --csv-path /home/chris/calgary-analytica/data/extracted/Calgary_CREB_Data.csv

# Database Operations
cd data-lake
python3 -c "import sqlite3; conn=sqlite3.connect('calgary_data.db'); print('City records:', conn.execute('SELECT COUNT(*), MAX(date) FROM housing_city_monthly').fetchone())"
```

## Architecture & Data Flow

### Data Pipeline
1. **PDF Storage**: `/data/raw_pdfs/` - CREB monthly reports (format: `MM_YYYY_Calgary_Monthly_Stats_Package.pdf`)
2. **Extraction**: `/extractors/creb_reports/` - Extracts city-wide (pages 11,13,15,17,19) and district (page 7) data
3. **Validation**: `/validation/pending/` - CSVs await human review before database loading
4. **Database**: `/data-lake/calgary_data.db` - Central SQLite storage with two main tables:
   - `housing_city_monthly`: City-wide aggregates (5 property types � 28+ months)
   - `housing_district_monthly`: District-level detail (8 districts � 4 property types � 16+ months)

### Extraction Success Rate
- Overall: ~95% (manual intervention needed for edge cases)
- Known issue: January 2025 PDF required manual fixes
- District data extraction occasionally fails (page 7 format variations)

### Validation Workflow
- Confidence threshold: 90% for auto-approval
- Expected records per month: 5 city + 32 district = 37 total
- Manual review triggered when confidence < 90% or extraction issues detected

## Context Management System & Custom Slash Commands

To reduce token costs by 90%, use focused context files in `/context/` via custom slash commands:

### Session Workflow with Slash Commands
```bash
/project:start              # Smart initialization (auto-loads next-session.md or shows menu)
/project:load general       # Load context-general.md (30 lines)
/project:load dashboard     # Load context-dashboard.md (25 lines)  
/project:load pipeline      # Load context-data-pipeline.md (30 lines)
/project:save              # Generate summary + update next-session.md
```

### Cost Optimization
- **Before**: Manual context loading (~20,000 tokens = $0.20/session)
- **After**: Automated slash commands (~2,000 tokens = $0.02/session)
- **90% reduction** in context costs through intelligent automation

### Available Custom Commands
Located in `.claude/commands/`:
- `start.md` - Intelligent session initialization
- `save.md` - Automated session summaries  
- `load.md` - Context loading with arguments
- `context.md` - Context file management
- `update.md` - Data pipeline operations
- `extract.md` - Extraction with agent crews
- `dashboard.md` - Development workflows
- `help.md` - Quick command reference

Full documentation remains in root directory but should only be loaded when specifically needed.

## Human-AI Partnership Model

### Human (Chris) Responsibilities
- Strategic vision and priorities
- Data validation and quality assurance
- User feedback and requirements

### Claude Code Responsibilities
- Technical implementation
- Data extraction and processing
- Dashboard development
- Pattern recognition and optimization

## Key Architectural Decisions

1. **Separate Tables**: City-wide and district data stored separately due to different granularities and time ranges
2. **Validation Gates**: All extracted data goes through `/validation/` before database loading
3. **Pattern Storage**: Successful extraction methods saved for future use (planned: `/extractors/patterns.json`)
4. **Boring Tech**: SQLite over PostgreSQL, PHP over Node.js, system fonts over custom fonts

## Agent Crew System (Future Enhancement)

When extraction confidence < 90% or new data formats encountered, deploy parallel agents:
- Agent A: pdfplumber (current primary method)
- Agent B: Firecrawl structured extraction
- Agent C: OCR for image-based PDFs
- Agent D: Web scraping fallback
- Agent E: Alternative parsing methods

Best result wins and gets documented for future use.

## Session Management

Save work sessions to `/SESSIONS/` with format: `YYYY-MM-DD_description.md`
Update `/context/next-session.md` at session end for continuity.

## Time vs Tokens

When creating a plan focus on phases, features, components, etc. instead of TIME. And instead of TIME focus on estimating how much tokens it might take.