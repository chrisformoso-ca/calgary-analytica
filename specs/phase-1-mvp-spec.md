# Calgary Analytica - Phase 1 MVP Specification

**Version**: 1.0  
**Date**: June 17, 2025  
**Status**: Ready for Implementation

## 🎯 Executive Summary

Calgary professionals waste 60+ minutes gathering fragmented market data. Phase 1 builds the foundation for THE single source of Calgary market intelligence, starting with housing data extraction and visualization.

**Deliverables**:
1. Automated CREB data extraction with 90%+ reliability
2. Interactive housing trends dashboard 
3. Parallel agent crew system for complex extractions
4. Validated data pipeline with human QA gates

**Timeline**: 6 weeks  
**Stack**: Python + SQLite + PHP + D3.js (The Boring Quad)

## 📋 Phase 1 Components

### 1. Data Pipeline Foundation (Weeks 1-2)

#### 1.1 Database Schema
```sql
-- calgary_data.db core tables
CREATE TABLE housing_monthly (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    community TEXT NOT NULL,
    property_type TEXT NOT NULL,
    avg_price REAL,
    median_price REAL,
    sales_volume INTEGER,
    new_listings INTEGER,
    active_listings INTEGER,
    months_of_inventory REAL,
    source TEXT NOT NULL,
    confidence_score REAL,
    extracted_date TEXT,
    validation_status TEXT DEFAULT 'pending'
);

CREATE TABLE extraction_patterns (
    id INTEGER PRIMARY KEY,
    source_name TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_config JSON,
    success_rate REAL,
    last_used TEXT,
    created_by TEXT -- 'agent_crew' or 'manual'
);

CREATE TABLE agent_crew_results (
    id INTEGER PRIMARY KEY,
    task_id TEXT NOT NULL,
    crew_composition JSON,
    winner_agent TEXT,
    confidence_scores JSON,
    execution_time REAL,
    task_date TEXT
);
```

#### 1.2 CREB Data Extractor
**User Story**: As a data analyst, I need reliable monthly CREB data without manual copying from PDFs.

**Technical Requirements**:
- Handle mixed PDF/Excel formats from CREB monthly reports
- Deploy parallel agent crews when confidence < 90%
- Extract key metrics: prices, sales, inventory, trends
- Output to `/validation/csv/` for human review

**Agent Crew Composition**:
```json
{
  "creb_monthly_extraction": {
    "agents": [
      {"id": "A", "method": "pdfplumber", "focus": "table extraction"},
      {"id": "B", "method": "firecrawl", "focus": "structured extraction"},
      {"id": "C", "method": "ocr", "focus": "image-based PDFs"},
      {"id": "D", "method": "camelot", "focus": "complex tables"},
      {"id": "E", "method": "web_scrape", "focus": "CREB portal"}
    ],
    "trigger": "confidence < 0.9 OR no_pattern_exists"
  }
}
```

#### 1.3 Validation Workflow
```
Raw PDF → Extraction → CSV Output → Human Review → Database Load
                ↓                        ↓
          Pattern Storage          Rejection + Retry
```

### 2. Housing Trends Dashboard (Weeks 3-4)

#### 2.1 Core Features
**User Story**: As a realtor, I need to see Calgary housing trends by community to advise clients.

**Dashboard Components**:
- Interactive map with community boundaries
- Time series chart (5-year history)
- Key metrics cards (current vs last year)
- Community comparison tool
- Filter by property type, price range
- Export to PDF/CSV

#### 2.2 Technical Architecture
```
/dashboards/housing-trends/
├── index.php           # Main dashboard
├── api.php            # Data endpoints
├── assets/
│   ├── js/
│   │   ├── dashboard.js
│   │   ├── charts.js    # D3.js visualizations
│   │   └── filters.js
│   ├── css/
│   │   └── style.css    # Brand-aligned styles
│   └── data/
│       └── communities.geojson
```

#### 2.3 D3.js Visualizations
- **Map**: Choropleth with community boundaries
- **Time Series**: Multi-line chart with hover details
- **Comparison**: Side-by-side community metrics
- **Sparklines**: Inline trend indicators

**Brand Compliance**:
- Calgary Red (#E63946) for primary data
- System fonts for fast loading
- Card-based responsive layout
- Minimal, purposeful animations

### 3. Data Source Integration (Weeks 5-6)

#### 3.1 Priority Sources
1. **CREB** (Weekly)
   - Monthly market reports
   - Community statistics
   - Historical data archives

2. **City of Calgary** (Daily)
   - Development permits API
   - Property assessments
   - Community profiles

3. **Statistics Canada** (Monthly)
   - Population estimates
   - Economic indicators
   - Census data

4. **Alternative Data** (Weekly)
   - Reddit r/Calgary sentiment
   - Google Maps reviews
   - Social media mentions

#### 3.2 Extraction Patterns Storage
```json
{
  "patterns": [
    {
      "source": "creb_monthly_pdf",
      "method": "firecrawl",
      "config": {
        "table_headers": ["Community", "Average Price", "Sales"],
        "page_range": "5-15",
        "confidence_threshold": 0.9
      },
      "success_rate": 0.94,
      "last_updated": "2025-06-15"
    }
  ]
}
```

### 4. Infrastructure Setup

#### 4.1 Directory Structure
```bash
# Create full project structure
mkdir -p calgary-analytica/{data-lake/{raw/{creb,city,statscan},archive},extractors/{scripts,logs},validation/{csv,validated,rejected},dashboards/{housing,assets/{js,css,data}},content/{social,blog,technical}}
```

#### 4.2 Development Workflow
1. **Local Development**: WSL + Python 3.x + PHP 8.x
2. **Version Control**: Git with structured commits
3. **Testing**: Extraction validation scripts
4. **Deployment**: Simple file upload to Hostinger

#### 4.3 Session Management
- Daily progress summaries in `/SESSIONS/`
- Pattern documentation after each success
- Agent crew performance metrics
- Resource usage tracking

## 📊 Success Metrics

### Quantitative
- **Extraction Success Rate**: >90% for CREB PDFs
- **Dashboard Load Time**: <2 seconds
- **Data Freshness**: Updated within 24 hours
- **User Sessions**: 100+ weekly by week 6

### Qualitative
- **Time Saved**: 60+ minutes per user per week
- **Data Accuracy**: Human-validated to 99%+
- **User Feedback**: "This is exactly what Calgary needs"
- **Pattern Library**: 10+ documented extraction methods

## 🚨 Risk Mitigation

### Technical Risks
- **PDF Format Changes**: Agent crews adapt automatically
- **API Rate Limits**: Implement caching and scheduling
- **Data Quality**: Human validation gates
- **Scaling**: SQLite → PostgreSQL migration path ready

### Business Risks
- **User Adoption**: Start with power users, expand
- **Data Source Access**: Multiple extraction methods
- **Complexity Creep**: Maintain boring tech philosophy

## 📅 Week-by-Week Milestones

### Week 1: Database Foundation
- [ ] Set up calgary_data.db schema
- [ ] Create extraction patterns table
- [ ] Build validation workflow
- [ ] Test with sample CREB data

### Week 2: First Extractor
- [ ] Implement CREB PDF extractor
- [ ] Deploy first agent crew
- [ ] Document winning patterns
- [ ] Load validated data

### Week 3: Dashboard Framework
- [ ] Set up dashboard structure
- [ ] Create API endpoints
- [ ] Build card layout system
- [ ] Implement basic filters

### Week 4: Visualizations
- [ ] D3.js community map
- [ ] Time series charts
- [ ] Comparison tools
- [ ] Mobile responsiveness

### Week 5: Additional Sources
- [ ] City of Calgary API integration
- [ ] Alternative data scrapers
- [ ] Cross-reference system
- [ ] Pattern optimization

### Week 6: Polish & Launch
- [ ] Performance optimization
- [ ] User documentation
- [ ] Deployment to production
- [ ] Gather initial feedback

## 🛠️ Implementation Guidelines

### For Claude Code
1. **Always check patterns first** before attempting extraction
2. **Deploy agent crews** when confidence < 90%
3. **Document successful methods** in patterns.json
4. **Validate with human** before database load
5. **Use boring tech** - no unnecessary complexity

### For Human (Chris)
1. **Review validation queue** daily
2. **Provide extraction feedback** to improve patterns
3. **Test dashboard usability** with target users
4. **Monitor data quality** trends
5. **Guide strategic priorities** based on user needs

## 🎯 Definition of Done

### Phase 1 Complete When:
- [ ] CREB data extracts reliably (>90% success)
- [ ] Housing dashboard shows real Calgary data
- [ ] Agent crews improve extraction over time
- [ ] 5+ Calgary professionals using weekly
- [ ] Pattern library has 10+ documented methods
- [ ] Data updates happen automatically
- [ ] Human validation takes <10 min/day

## 🚀 Next Phase Preview

**Phase 2: Rental Market & Economics**
- Rental vacancy and pricing data
- Economic indicators dashboard
- Predictive analytics experiments
- API for other developers

**Phase 3: Community Intelligence**
- Detailed neighborhood profiles
- School and amenity data
- Sentiment analysis integration
- Mobile app considerations

## 📝 Notes

- Start small, ship fast, iterate based on usage
- Every feature must save Calgary professionals time
- Documentation IS marketing - share the journey
- When stuck, deploy an agent crew
- Remember: We're building THE source for Calgary data

---

**Ready to Build**: This spec provides clear direction while maintaining flexibility for discoveries during implementation. The boring tech stack + AI partnership + parallel agent crews = unstoppable execution.</content>
</invoke>