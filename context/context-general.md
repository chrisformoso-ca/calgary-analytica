# Calgary Analytica - General Context

## Mission
Transform Calgary's fragmented data landscape into actionable intelligence through AI-augmented development.

## Tech Stack
- **Backend**: Python + SQLite
- **Frontend**: PHP + D3.js  
- **Philosophy**: Boring tech that works

## Project Structure
- `/data-lake/` - Database and data pipeline
- `/extractors/` - CREB data extraction (95% success rate)
- `/dashboards/` - Web visualizations
- `/validation/` - Data quality workflow

## Current Status
- ✅ Database with 145 city + 512 district records
- ✅ Monthly update workflow operational
- 🔄 Building housing dashboard (Phase 1)

## Key Commands
```bash
# Monthly data update
python3 monthly_update.py --month X --year YYYY

# Database location
/data-lake/calgary_data.db
```

## Human-AI Roles
- **Human (Chris)**: Vision, priorities, validation
- **Claude Code**: Implementation, data processing, debugging