# README.md - Calgary Analytica

**Mission**: Transform Calgary's fragmented data landscape into actionable intelligence through AI-augmented development.

**Philosophy**: Data → Products → Content → Impact

## 🤝 Human-AI Partnership Model

### Claude Code (AI) Responsibilities
- **Development Assistant**: Write code, debug, and refactor
- **Technical Advisor**: Architecture recommendations and best practices
- **Documentation**: Create and maintain technical docs
- **Code Review**: Analyze code quality and suggest improvements
- **Problem Solving**: Help debug issues and design solutions

### Human (Chris) Responsibilities
- **CEO**: Vision, strategy, and final decisions
- **Data Operator**: Run scripts, validate data, approve results
- **Quality Control**: Review all data before database entry
- **Context Manager**: Maintains project history and business knowledge
- **Deployment**: Execute commands and monitor results

## 🛠️ MCP Toolkit & Capabilities

| MCP Tool | Primary Use | Example Tasks |
|----------|-------------|---------------|
| **Brave Search** | Web research | Find new data sources, verify information |
| **Fetch** | API calls | Pull data from City of Calgary APIs |
| **Filesystem** | File operations | Read PDFs, write CSVs, manage code |
| **Puppeteer** | Web scraping | Extract from JavaScript-heavy sites |
| **GitHub** | Version control | Commit code, track changes |
| **Memory** | Pattern storage | Remember successful extraction methods |
| **Sequential Thinking** | Complex reasoning | Multi-step problem solving |
| **Database Server** | SQLite operations | Query and update calgary_data.db |

## 📊 Simple Data Pipeline (No Agents)

### Core Philosophy
Keep it simple. No autonomous agents. No LLM involvement in data processing. Just run scripts, review data, load to database.

### Three-Step Monthly Update Process

#### Step 1: Extract Data
```bash
# Run monthly update script
python3 data-engine/cli/monthly_update.py --month 6 --year 2025

# Or run specific extractors directly
python3 data-engine/creb/scripts/extractor.py
python3 data-engine/economic/scripts/extractor_timeseries.py
python3 data-engine/police/scripts/extractor.py
```

**What happens**: 
- Scripts read PDFs/Excel files from source directories (e.g., `/data-engine/creb/raw/`)
- Extract data into CSV files
- Save to `/data-engine/validation/pending/` with timestamps
- Calculate confidence scores (just for your information)

#### Step 2: Human Review
```bash
# See what needs review
python3 data-engine/cli/validate_pending.py --list

# Review interactively
python3 data-engine/cli/validate_pending.py --interactive
```

**What you do**:
- Review each CSV file preview
- Check if data looks correct
- Press `a` to approve → moves to `/validation/approved/`
- Press `r` to reject → moves to `/validation/rejected/`
- Press `s` to skip for now
- Press `q` to quit

#### Step 3: Load to Database

**Option A - Load with full validation structure** (for monthly updates):
```bash
cd data-engine/core && python3 load_approved_data.py
```

**Option B - Direct CSV load** (for simple CSVs):
```bash
cd data-engine/core && python3 load_csv_direct.py
```

**What happens**:
- Reads CSVs from `/validation/approved/`
- Auto-detects which table based on column names
- Loads data into SQLite database
- Moves processed CSV files to `/validation/processed/`
- Archives JSON reports to `/validation/reports/YYYY/MM/`
- Shows summary of what was loaded

**Which loader to use?**
- `load_approved_data.py`: For data with validation subdirectories and JSON reports
- `load_csv_direct.py`: For simple CSV files placed directly in approved/ (recommended for most cases)

### That's It!
No agents. No automation. You control every step.

## 📋 Standard Operating Procedures

### 1. Monthly Data Update

**Human Actions**:
1. Download new files to appropriate source folders:
   - CREB PDFs → `/data-engine/creb/raw/`
   - Economic files → `/data-engine/economic/raw/`
   - Crime files → `/data-engine/police/raw/`
2. Run extraction: `python3 data-engine/cli/monthly_update.py --month 11 --year 2024`
3. Review pending data: `python3 data-engine/cli/validate_pending.py --interactive`
4. Approve or reject each CSV
5. Load approved data: `cd data-engine/core && python3 load_approved_data.py`

**Claude Code Support**:
- Help debug extraction scripts if they fail
- Suggest code improvements for better extraction
- Update documentation as needed

### 2. Dashboard Development

**Human Request**: "Create a dashboard showing housing price trends"

**Claude Code Actions**:
1. Write SQL queries to extract needed data
2. Create static HTML/JS dashboard structure
3. Implement D3.js visualizations
4. Add interactive filters and controls
5. Generate JSON data files from SQLite
6. Provide deployment instructions

**Human Actions**:
1. Review the code
2. Test locally: `python3 -m http.server 8000`
3. Deploy static files to production when satisfied

### 3. Content Creation

**Human Request**: "Write a LinkedIn post about new housing data"

**Claude Code Actions**:
1. Query database for latest insights
2. Draft post with data highlights
3. Suggest multiple angles/approaches
4. Format for LinkedIn best practices

**Human Actions**:
1. Review and edit the content
2. Choose preferred version
3. Post to LinkedIn

## 🌐 Web Dashboard Architecture

### Static Generation Approach
- **Data Export**: Python scripts query SQLite and export JSON files
- **Frontend**: Pure HTML/CSS/JavaScript with D3.js for visualizations
- **Interactivity**: Full client-side interactivity without server requirements
- **Hosting**: Any static file host (GitHub Pages, Netlify, S3, or traditional web hosting)
- **Updates**: Monthly refresh by regenerating and uploading new JSON files

### Benefits
- **Cost**: $0-5/month hosting (vs $20+ for dynamic hosting)
- **Performance**: Instant loading with CDN caching
- **Reliability**: No server maintenance or downtime
- **Security**: No database exposed to internet
- **Simplicity**: Just files, no server configuration

### Workflow
1. Run Python data extraction → Updates SQLite
2. Export data to JSON: `python3 export_dashboard_data.py`
3. Test locally: `python3 -m http.server 8000`
4. Deploy: Upload `/dashboards` folder to hosting

## 📁 Project Structure

```
calgary-analytica/
├── data-engine/              # Data pipeline engine
│   ├── cli/                 # Command line scripts
│   │   ├── monthly_update.py
│   │   └── validate_pending.py
│   ├── core/                # Core functionality
│   │   ├── data_engine.py
│   │   └── load_approved_data.py
│   ├── creb/                # CREB housing data
│   │   ├── raw/            # PDF files
│   │   ├── scripts/        # Extraction scripts
│   │   ├── patterns/       # Extraction patterns
│   │   ├── config.json     # Source configuration
│   │   └── notes.md        # CREB-specific docs
│   ├── economic/           # Economic indicators
│   │   ├── raw/           # Excel/PDF files
│   │   ├── scripts/       # Extraction scripts
│   │   ├── patterns/      # Extraction patterns
│   │   ├── config.json    # Source configuration
│   │   └── notes.md       # Economic data docs
│   ├── police/            # Crime statistics
│   │   ├── raw/          # Excel files
│   │   ├── scripts/      # Extraction scripts
│   │   ├── patterns/     # Extraction patterns
│   │   ├── config.json   # Source configuration
│   │   └── notes.md      # Crime data docs
│   └── validation/        # Human review pipeline
│       ├── pending/       # Awaiting review
│       ├── approved/      # Ready to load
│       ├── rejected/      # Failed review
│       ├── processed/     # Successfully loaded
│       └── reports/       # JSON validation reports (YYYY/MM/)
├── data-lake/
│   └── calgary_data.db     # Central SQLite database
├── dashboards/             # Web applications
│   ├── housing/           # Housing market dashboard
│   ├── rental/            # Rental market analysis
│   └── assets/            # Shared JS, CSS, images
├── content/               # Generated content
│   ├── social/           # LinkedIn, Twitter posts
│   └── blog/             # Long-form articles
├── config/               # Configuration
│   └── config_manager.py # Centralized path management
└── docs/                # Project documentation
```

## 📊 Expected Data Volumes

Per update:
- **Housing City**: ~5 records/month (5 property types)
- **Housing District**: ~32 records/month (8 districts × 4 types)
- **Economic Indicators**: ~10-15 records/month
- **Crime Statistics**: ~200,000+ total records (all years, includes 'UNKNOWN' community for privacy-protected domestic violence data)

## 🎯 Decision Framework

Before any action, consider:

1. **Does this serve Calgary data users?**
   - If no → Decline politely and suggest alternatives
   - If yes → Proceed to next question

2. **Can we keep it simple?**
   - Manual process > complex automation
   - Proven patterns > experimental approaches
   - Clear documentation > clever code

3. **Will this scale with our tech stack?**
   - Static HTML/JS + D3.js for web
   - Python for data processing
   - SQLite for now, PostgreSQL ready when needed

4. **Can we ship in days, not weeks?**
   - Break into smaller deliverables
   - Use boring, proven technology
   - Test manually before automating

## 🔄 Continuous Improvement

### Weekly Review
- Which extraction scripts need updates?
- Any new data formats to handle?
- Dashboard performance and user feedback
- Documentation updates needed

### Monthly Architecture Review
- Database schema evolution
- Script reliability improvements
- Performance optimizations
- New data sources to integrate

## 📊 Success Metrics

Track and report on:
- **Data Coverage**: Sources integrated, update frequency
- **Extraction Success**: Script reliability by source
- **Manual Review Time**: How long validation takes
- **Dashboard Usage**: Views and user feedback
- **Content Performance**: Engagement metrics
- **Data Quality**: Errors caught in review

## 🚨 Error Handling & Troubleshooting

### When extraction fails:
1. Check error logs in `/data-engine/validation/logs/`
2. Human reviews the problematic file manually
3. Claude Code helps debug and fix the script
4. Test fix on the failed file
5. Update script for future runs

### Database Queries:
```bash
# Check data volumes
cd data-lake
sqlite3 calgary_data.db "SELECT COUNT(*) FROM housing_city_monthly;"
sqlite3 calgary_data.db "SELECT COUNT(*) FROM crime_statistics_monthly;"
sqlite3 calgary_data.db "SELECT COUNT(*) FROM crime_statistics_monthly WHERE community = 'UNKNOWN';"

# Check date ranges
sqlite3 calgary_data.db "SELECT MIN(date), MAX(date) FROM economic_indicators_monthly;"

# Generate comprehensive database catalog
sqlite3 calgary_data.db < db_catalog.sql
# Or save to file: sqlite3 calgary_data.db < db_catalog.sql > catalog.txt
```

### Data Loading Notes:
- Column names are automatically lowercased (preserving underscores)
- JSON validation reports are archived to `/validation/reports/YYYY/MM/`
- Null communities in crime data become 'UNKNOWN' (for privacy-protected domestic violence data)
- The `load_csv_direct.py` auto-detects table type from column names

### Database Catalog:
The `db_catalog.sql` script provides a comprehensive overview of the database:
- Table summaries with record counts and date ranges
- Schema details for each table including all fields
- Data distributions (property types, crime categories, economic indicators)
- Geographic coverage (districts, communities)
- Temporal alignment showing which datasets overlap
- Sample queries for common analyses

## 💡 Key Principles

1. **Simplicity First**: Manual processes that work > complex automation that breaks
2. **Human Control**: You run every script, review every record
3. **Transparency**: Clear logs and status at each step
4. **Data Quality**: Human validation ensures accuracy
5. **Boring Tech**: SQLite, Python, PHP - proven and reliable
6. **User Focus**: Every feature must save Calgary professionals time

## 🎓 Learning Resources

- **Data Pipeline Guide**: `/data-engine/CLAUDE.md`
- **Brand Identity**: `/docs/brand_identity.md`
- **Core Strategy**: `/docs/core_strategy.md`
- **Technical Context**: `/CLAUDE.md`
- **Database Schema**: Run setup_database.py to see table structures

---

**Remember**: We're building THE source of truth for Calgary market intelligence. Keep it simple, keep it accurate, keep the human in control.