# README.md - Calgary Analytica

**Mission**: Transform Calgary's fragmented data landscape into actionable intelligence through AI-augmented development.

**Philosophy**: Data → Products → Content → Impact

## 🤝 Human-AI Partnership Model

### Claude Code (AI) Responsibilities
- **CTO**: Technical architecture decisions
- **Director of Data**: Data pipeline design and optimization
- **Senior Developer**: Code implementation and debugging
- **Automation Engineer**: Pattern recognition and workflow optimization
- **Documentation Lead**: Technical docs and methodology guides

### Human (Chris) Responsibilities
- **CEO**: Vision, strategy, and final decisions
- **COO**: Operations, resource allocation, prioritization
- **Context Manager**: Maintains project history and business knowledge
- **Quality Assurance**: Validates data accuracy and user experience
- **Relationship Manager**: User feedback and community engagement

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

## 🤖 Parallel Agent Crews

### Core Concept
When facing complex extraction or creation challenges, deploy multiple agents simultaneously to attack the same problem with different approaches. The best result wins and gets documented for future use.

### Data Extraction Crews

**CREB Mixed Format Challenge**
```
Problem: "Extract housing data from CREB's mixed PDF/Excel formats"

Parallel Agents:
- Agent A: PDF table extraction (pdfplumber + pandas)
- Agent B: OCR approach (Tesseract + image processing) 
- Agent C: Web scraping CREB's data portal
- Agent D: Excel/CSV parsing from downloadable files
- Agent E: Firecrawl structured extraction

Result: Best extraction method wins, gets saved to patterns.json
```

**City of Calgary Data Inconsistencies**
```
Problem: "Get development permits from City's inconsistent API formats"

Parallel Agents:
- Agent A: Official Open Data portal API
- Agent B: Development tracker web scraping
- Agent C: PDF permit reports extraction
- Agent D: GIS data parsing from shapefiles
- Agent E: News/announcement scraping

Result: Most reliable data source combination identified
```

### UI Design Crews

**Dashboard Layout Optimization**
```
Problem: "Create housing dashboard layout for mobile + desktop"

Parallel Agents:
- Agent A: Card-based layout (following brand_identity.md)
- Agent B: Full-width chart approach 
- Agent C: Sidebar + main content split
- Agent D: Tabbed interface design
- Agent E: Single-page scroll layout

Result: Pick best elements from each, combine into final design
```

### Content Creation Crews

**Social Media Content Generation**
```
Problem: "Write LinkedIn post about new rental market insights"

Parallel Agents:
- Agent A: Data-first approach (lead with numbers)
- Agent B: Story-driven angle (Calgary renter's journey)
- Agent C: Question-hook format ("Did you know...?")
- Agent D: Trend analysis angle (compared to last year)
- Agent E: Actionable tips format (what this means for you)

Result: Multiple post variations, choose best or combine elements
```

### Implementation Methods

**Option 1: Explicit Request**
```
Human: "Use agent crew to extract CREB data"
Claude: *launches 5 parallel agents with different methods*
```

**Option 2: Automatic Pipeline Triggers**
```python
# Built into extraction scripts
if source_type == "mixed_format" and confidence < 0.8:
    launch_agent_crew(extraction_methods=['pdf', 'ocr', 'scrape', 'api'])
```

**Option 3: Workflow Integration**
- Deploy agent crew when single extraction fails
- Activate crew when confidence < 90%
- Use for new/unknown data formats automatically

### Race Condition Logic
1. All agents work simultaneously on same problem
2. Each reports back with confidence score and results
3. Best result wins and gets documented in `/extractors/patterns.json`
4. Failed approaches inform future crew compositions

## 📋 Standard Operating Procedures

### 1. Data Extraction Workflow

**Human Input**: 
```
"New CREB report for November 2024 is available at [URL]"
```

**Claude Code Actions**:
1. Check memory for CREB extraction patterns
2. Download PDF to `/data-lake/raw/creb/2024-11/`
3. Run appropriate extractor(s) based on patterns
4. If no pattern exists OR confidence < 90%:
   - **Deploy Agent Crew**: Multiple extraction approaches simultaneously
   - Analyze PDF structure with different methods
   - Test multiple extraction techniques in parallel
   - Document winning approach
5. Output CSV to `/validation/csv/creb_2024_11.csv`
6. Generate extraction report:
   ```
   Extraction Summary - CREB November 2024
   - Source: creb_monthly_report_2024_11.pdf
   - Method: Agent Crew - firecrawl winner over pdfplumber
   - Records extracted: 1,247
   - Key fields: average_price, sales_volume, inventory
   - Confidence: 94%
   - Output: /validation/csv/creb_2024_11.csv
   ```

**Human Validation**:
- Review CSV for accuracy
- Respond with: "approved" or "issues found: [description]"

**Claude Code Follow-up**:
- If approved: Load to database and update patterns
- If issues: Deploy different agent crew composition and retry

### 2. Product Development Workflow

**Human Input**:
```
"Create a dashboard showing Calgary housing price trends by community"
```

**Claude Code Actions**:
1. Query database for relevant data
2. **Deploy UI Design Crew**: Multiple layout approaches simultaneously
3. Create winning design in `/dashboards/housing-trends/`
4. Use D3.js for visualizations following brand guidelines
5. Output deployment instructions:
   ```
   Dashboard Ready: Housing Trends by Community
   - Location: /dashboards/housing-trends/
   - Design: Card-based layout (Agent A winner)
   - Test locally: php -S localhost:8000
   - WordPress embed: [iframe code]
   - Key features: Interactive map, time series, filters
   ```

### 3. Content Creation Workflow

**Human Input**:
```
"Write a LinkedIn post about our new housing trends dashboard"
```

**Claude Code Actions**:
1. Read dashboard features and latest data insights
2. **Deploy Content Crew**: Multiple post angles simultaneously
3. Select best approach or combine elements
4. Create post in `/content/social/linkedin/2024-11-housing-trends.md`
5. Include:
   - Hook: Interesting data insight (winning approach)
   - Value prop: Time saved for professionals
   - CTA: Visit dashboard
   - Hashtags: #CalgaryData #YYC #RealEstate

### 4. Session Management (Automated with Custom Slash Commands)

**New Workflow with Custom Commands**:
```
/project:start    # Smart session initialization
/project:save     # Automated session summary + next-session.md update
```

**Legacy Manual Workflow**:
```
"/save" (still supported)
```

**Enhanced Claude Code Actions**:
1. **Smart Session Start** (`/project:start`):
   - Check if `next-session.md` exists
   - If yes: Load continuation context automatically
   - If no: Present context menu (general/dashboard/pipeline)
   - Display current project status after loading

2. **Automated Session Summary** (`/project:save`):
   - Generate comprehensive session summary
   ```markdown
   # Session Summary - [Date]
   
   ## Achievements
   - Extracted CREB November data (1,247 records)
   - Created housing trends dashboard (card layout won)
   - Published LinkedIn content (data-first angle performed best)
   
   ## Agent Crew Results
   - CREB extraction: Firecrawl beat pdfplumber (94% vs 78% confidence)
   - Dashboard design: Card layout beat sidebar approach
   - LinkedIn content: Data-first beat story-driven approach
   
   ## Problems Encountered
   - PDF table spanning multiple pages
   - Memory MCP timeout on large pattern
   
   ## Solutions Applied
   - Used page concatenation before extraction
   - Chunked pattern storage
   
   ## Patterns Learned
   - CREB reports: Firecrawl more reliable for multi-page tables
   - Dashboard users prefer card layouts on mobile
   - Data-first LinkedIn posts get 2x engagement
   
   ## Resource Usage
   - Duration: 47 minutes
   - Agents deployed: 15 total (3 crews)
   - Tokens: ~125,000
   - Estimated cost: $0.75
   ```
3. **Automatic Next Session Preparation**:
   - Update `/context/next-session.md` with immediate next tasks
   - Include quick-start commands and context recommendations
   - Ensure seamless session continuity

4. **Context-Aware Operations**:
   - All commands automatically load appropriate context files
   - 90% reduction in token usage through focused context loading
   - Maintains full project knowledge while optimizing costs

## 🎯 **Custom Slash Commands Reference**

### Session Commands
- `/project:start` - Intelligent session initialization
- `/project:save` - Generate session summary + update next-session.md  
- `/project:load [context]` - Load specific context (general|dashboard|pipeline|continue)
- `/project:context` - Manage and explore context files
- `/project:help` - Quick command reference

### Data Pipeline Commands  
- `/project:update month YYYY-MM` - Process monthly data updates
- `/project:update status` - Check database and data freshness
- `/project:extract creb [path]` - Direct extraction with agent crews

### Development Commands
- `/project:dashboard create [name]` - Create dashboard with standard structure

### Typical Session Flow
```bash
/project:start              # Begin session (auto-loads context)
# ... work on tasks ...
/project:save              # End session (creates summary + updates next-session.md)
```

2. Save to `/SESSIONS/2024-11-14_creb_extraction.md`

## 📁 Project Structure

```
calgaryanalytica-v2/
├── data-lake/
│   ├── calgary_data.db      # Central SQLite database
│   ├── raw/                 # Original source files
│   │   ├── creb/           # CREB reports by year/month
│   │   ├── city/           # City of Calgary data
│   │   └── statscan/       # Statistics Canada files
│   └── archive/            # Historical versions
├── extractors/
│   ├── scripts/            # Extraction scripts by source
│   ├── patterns.json       # Successful extraction patterns
│   ├── agent-crews.json   # Agent crew compositions and results
│   └── logs/              # Extraction history
├── validation/
│   ├── csv/               # Awaiting human validation
│   ├── validated/         # Approved for loading
│   └── rejected/          # Failed validation
├── dashboards/            # Web applications
│   ├── housing/          # Housing market dashboard
│   ├── rental/           # Rental market analysis
│   └── assets/           # Shared JS, CSS, images
├── content/
│   ├── social/           # LinkedIn, Twitter posts
│   ├── blog/             # Long-form articles
│   └── technical/        # Methodology guides
├── SESSIONS/             # Work session summaries
└── docs/                 # Project documentation
```

## 🎯 Decision Framework

Before any action, Claude Code should consider:

1. **Does this serve Calgary data users?**
   - If no → Decline politely and suggest alternatives
   - If yes → Proceed to next question

2. **Is there an existing pattern OR should we deploy agent crew?**
   - If pattern exists → Use it and note in response
   - If no pattern OR confidence < 90% → Deploy agent crew
   - Document new approaches after success

3. **Will this scale with our tech stack?**
   - PHP + D3.js for web
   - Python for data processing
   - SQLite → PostgreSQL migration path ready

4. **Can we ship in days, not weeks?**
   - Break into smaller deliverables
   - Use boring, proven technology
   - Leverage agent crews for parallel development

## 🔄 Continuous Improvement

### Weekly Pattern Review
- Which extraction methods worked best?
- What new data sources were discovered?
- Which dashboards got the most usage?
- **Agent crew performance**: Which compositions work best?

### Monthly Architecture Review
- Database schema evolution needs?
- Performance bottlenecks?
- New MCP tools to integrate?
- **Agent crew optimization**: Refine crew compositions based on results

## 📊 Success Metrics

Track and report on:
- **Data Coverage**: Sources integrated, update frequency
- **Extraction Success**: Success rate by source type
- **Agent Crew Efficiency**: Time saved vs single-agent approach
- **Product Usage**: Dashboard views, user feedback
- **Content Reach**: Post engagement, article reads
- **Time Saved**: Human hours automated

## 🚨 Error Handling

When things go wrong:
1. Log the full error with context
2. Check if pattern exists for this error
3. **If no pattern OR high failure rate**: Deploy agent crew
4. Try alternative approaches in parallel
5. If crew still failing, create detailed report for human
6. Never fail silently

## 💡 Key Principles

1. **Transparency**: Always explain what you're doing and why
2. **Patterns**: Learn from every task, document what works
3. **Parallel Processing**: Use agent crews for complex/new challenges
4. **Validation**: Never load unvalidated data
5. **Simplicity**: Boring tech that works > exciting tech that breaks
6. **User Focus**: Every feature must save Calgary professionals time

## 🎓 Learning Resources

- **Brand Identity**: `/docs/brand_identity.md`
- **Core Strategy**: `/docs/core_strategy.md`
- **Technical Context**: `/docs/CLAUDE.md`
- **MCP Setup Guide**: `/docs/mcp_setup_guide.md`
- **Agent Crew Results**: `/extractors/agent-crews.json`

---

**Remember**: We're building THE source of truth for Calgary market intelligence. Every line of code, every data point, every visualization serves this mission. When in doubt, deploy an agent crew to find the best path forward.