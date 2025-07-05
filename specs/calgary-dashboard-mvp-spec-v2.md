# Calgary Housing Dashboard - MVP Specification

**Version**: 2.0  
**Focus**: First-time buyers, current owners, and investors  
**Philosophy**: Present data with context, not predictions

## Executive Summary

A streamlined dashboard providing Calgary housing market data with essential economic context. Three core pages deliver exactly what users need to make informed decisions without overwhelming complexity.

## Target Users & Their Needs

### First-Time Buyers
- What can I afford at current rates?
- Which districts offer best value?
- Is it a good time to enter the market?

### Current Owners  
- How is my home value trending?
- Should I consider refinancing?
- Is my district performing well?

### Investors
- Which property types show strong appreciation?
- What's the market liquidity like?
- Are economic fundamentals supportive?

## Core Pages (MVP)

### Page 1: Market Overview

**Purpose**: Immediate snapshot of Calgary's housing market health

#### Layout
```
Calgary Housing Market Dashboard
Last updated: May 2025 | Data from CREB & Statistics Canada

[Primary Metrics Row]
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Benchmark Price │ │ Monthly Sales   │ │ Active Listings │ │ 5-Yr Fixed Rate │
│ $592,500       │ │ 2,568 homes     │ │ 6,740          │ │ 6.95%          │
│ ↑ 1.0% MoM     │ │ ↑ 14% from Apr  │ │ ↑ 28% from Apr │ │ (as of July 1) │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘

[Price Trends Chart - Full Width]
Title: "Benchmark Prices by Property Type (24 months)"
- Interactive line chart
- Lines: Detached, Semi-Detached, Row, Apartment
- Toggle property types on/off
- Hover shows exact values
- Y-axis: Price ($), X-axis: Month
- Download as PNG button

[Market Activity Section - 2 columns]
Left: "Monthly Sales Volume"
- Bar chart, last 12 months
- Shows seasonal patterns
- Hover for exact numbers

Right: "Active Inventory"  
- Line chart with area fill
- Same 12-month period
- Months of inventory overlay

[Key Insights Panel]
Dynamic content based on current data:
• For First-time Buyers: "Apartments at $336k offer most affordable entry"
• For Current Owners: "Home values up 0.65% year-over-year"
• For Investors: "2.6 months inventory = balanced market conditions"

[Footer]
Next update: June 5, 2025 | View affordability calculator →
```

#### Data Requirements
- Current month + 24 months historical: prices by property type
- Current month + 12 months historical: sales volume, inventory
- Latest mortgage rates
- Calculated: MoM and YoY changes, months of inventory

#### Mobile Considerations
- Stack metrics 2x2
- Charts full width with horizontal scroll
- Reduce default timeframe to 12 months

---

### Page 2: Affordability & Economic Context

**Purpose**: Help users understand what they can afford and economic factors affecting housing

#### Layout
```
Understanding Affordability & Economic Context
"Market conditions that influence housing decisions"

[Interactive Payment Calculator]
┌─────────────────────────────────────────────────────────┐
│ Monthly Payment Calculator                              │
│                                                         │
│ Home Price:    [$450,000]    [slider $200k-$1M]       │
│ Down Payment:  [20%]         [5% | 10% | 20%]         │
│ Mortgage Rate: [6.95%]       [current 5-yr fixed]      │
│ Amortization: [25 years]     [25 | 30]                │
│                                                         │
│ Monthly Payment: $2,533                                 │
│ Total Interest: $399,880                                │
│                                                         │
│ ⚠️ Stress Test: You need to qualify at 8.95%           │
└─────────────────────────────────────────────────────────┘

[Interest Rate Environment]
┌─────────────────────────────────────────────────────────┐
│ Historical Mortgage Rates                                │
│ [Line chart: BoC rate & 5-yr fixed, 5 years]           │
│                                                         │
│ Current Bank of Canada Rate: 3.00%                      │
│ Current Prime Rate: 4.95%                               │
│ Typical Variable: Prime - 0.25%                         │
└─────────────────────────────────────────────────────────┘

[Economic Indicators Grid]
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Employment      │ │ Inflation       │ │ Wage Growth     │
│ Calgary CER     │ │ Calgary CMA     │ │ Calgary         │
│ 96.8%          │ │ 2.8% YoY       │ │ +0.77% YoY     │
│ [Sparkline]     │ │ [Sparkline]     │ │ [Sparkline]     │
└─────────────────┘ └─────────────────┘ └─────────────────┘

┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Oil Price (WTI) │ │ Population      │ │ Housing Starts  │
│ $77.20 USD     │ │ 1.67M          │ │ 3,102 units    │
│ ↓ $0.80 MoM    │ │ +2.0% YoY      │ │ ↑ 69% YoY      │
└─────────────────┘ └─────────────────┘ └─────────────────┘

[Context for Decision Making]
"Questions to Consider:"
□ Can you comfortably afford payments if rates rise 2%?
□ Is your employment stable if oil prices change?
□ How does wage growth compare to housing appreciation?
□ Are you buying for lifestyle or investment?

[Data Note]
"Money Supply (M2) data temporarily unavailable. 
Housing starts showing strong growth at 69% year-over-year."
```

#### Data Requirements
- Current + 5 years historical: BoC rate, mortgage rates
- Current + 2 years historical: All economic indicators
- Housing starts data from economic indicators
- Calculated: Mortgage payments, stress test rates

#### Key Features
- Real-time payment calculations
- Stress test visualization
- Economic indicator trends
- No predictions, just current state

---

### Page 3: Districts & Price Trends

**Purpose**: Geographic view of pricing and appreciation across Calgary's districts

#### Layout
```
Calgary Districts - Pricing & Trends
"Compare districts to find your best fit"

[District Selector Tabs]
[All Districts] [North] [South] [East] [West]

[District Pricing Table - Sortable]
Click any column header to sort

District      | Detached | Semi-Det | Row      | Apartment | YoY Change
--------------|----------|----------|----------|-----------|------------
North West    | $811k    | $681k    | $458k    | $316k     | +0.8%
North         | $683k    | $523k    | $419k    | $330k     | -0.6%
North East    | $593k    | $435k    | $368k    | $297k     | -2.7%
West          | $973k    | $757k    | $548k    | $460k     | +0.9%
City Centre   | $994k    | $968k    | $616k    | $348k     | +2.8%
South         | $871k    | $569k    | $491k    | $312k     | +1.5%
South East    | $691k    | $512k    | $426k    | $316k     | -0.4%
East          | $525k    | $402k    | $305k    | $249k     | -0.9%

[Visual Comparison Section]
Two side-by-side visualizations:

Left: "District Price Map"
- Choropleth map of Calgary
- Color intensity = price level
- Click for district details

Right: "Price Appreciation by District"
- Horizontal bar chart
- YoY % change by district
- Highlight positive growth

[Property Type Analysis]
"Best Value by Property Type"
┌─────────────────────────┐ ┌─────────────────────────┐
│ Most Affordable         │ │ Strongest Appreciation  │
│ Apartments: East $249k  │ │ Semi-Det: Centre +5.0%  │
│ Row: East $305k        │ │ Detached: Centre +2.8%  │
│ Semi-Det: East $402k   │ │ Row: South +2.1%       │
└─────────────────────────┘ └─────────────────────────┘

[District Trend Explorer]
Select a district to see historical trends:
[Dropdown: Select District]
[Line chart appears showing 24-month price history by property type]

[Entry-Level Buyer Guide]
"Districts with homes under $400k"
- East: All property types
- North East: Apartments, some row houses
- South East: Apartments
- North: Apartments
```

#### Data Requirements
- All district-level pricing data
- 24 months historical by district and property type
- Calculated: YoY changes, affordability thresholds
- District boundary data for map

#### Interactive Features
- Sortable table (any column)
- Clickable map for district selection
- Downloadable district reports
- Share specific district data

---

## Data Architecture

### Core JSON Exports (MVP)
1. **market_overview.json** (10.6 KB)
   - Latest month summary statistics
   - 24 months price history by type
   - 12 months sales/inventory
   - Property types: apartment, detached, row, semi_detached, total

2. **economic_indicators.json** (43.7 KB)
   - 17 economic indicators with history
   - Includes housing starts, employment, wages, inflation
   - Money supply (M2) using placeholder value
   - Calculated changes (MoM, YoY)

3. **district_data.json** (57.6 KB)
   - Current prices by district/type
   - 8 districts: City Centre, East, North, North East, North West, South, South East, West
   - Historical trends
   - Calculated appreciation rates

4. **rate_data.json** (13.6 KB)
   - Current mortgage rates (manually updated)
   - Historical BoC and prime rates
   - Stress test rates
   - Payment scenarios

5. **metadata.json** (12.1 KB)
   - Dashboard configuration
   - Last update timestamps
   - Data source information

### Additional Data Exports (Available)
6. **service_requests_311.json** (13.7 KB)
   - Neighborhood quality indicators
   - 316K requests from 313 communities
   - Seasonal patterns by category
   - Community quality scores

7. **rental_market.json** (25.5 KB)
   - CMHC data 2018-2024
   - Vacancy rates and average rents
   - 294 current rental listings
   - Affordability calculations

8. **crime_statistics.json** (14.9 KB)
   - Community safety scores
   - 265 communities tracked
   - Crime trends by category
   - Year-over-year changes

### Data Gaps & Notes
- **Money Supply (M2)**: Not available in current data pipeline, using 4.2% placeholder
- **Mortgage Rates**: Require manual monthly updates (see `/docs/mortgage_rate_updates.md`)
- **Property Type Names**: Database uses "Row" not "Row House", "Semi_Detached" not "Semi-Detached"

### Update Frequency
- Housing data: Monthly (by 5th)
- Economic data: Monthly (varies by indicator)
- Mortgage rates: Manual monthly update
- Cache with 24-hour TTL

## Technical Implementation

### Stack
- **Frontend**: Vanilla JavaScript (ES6+)
- **Charts**: D3.js for complex visualizations, Chart.js for simple
- **Styling**: CSS Grid/Flexbox, Calgary Red (#E63946) accent
- **Data**: Static JSON files, updated via Python pipeline
- **Hosting**: Static files on any web server

### Performance Targets
- Initial load: <2 seconds
- Chart interactions: <100ms response
- Mobile-optimized: Touch-friendly, responsive

### Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- No IE11 support
- Progressive enhancement for older browsers

## Future Enhancements (Post-MVP)

### Phase 2 Possibilities
- Email alerts for significant changes
- Rental market data integration (data ready)
- Community safety scores (data ready)
- Neighborhood quality indicators (data ready)
- Historical transaction data
- School catchment areas
- Commute time analysis

### User-Requested Features
Track all requests but only build based on:
- Multiple user requests
- Data availability
- Alignment with core purpose

## Success Metrics

### Quantitative
- Page load times <2 seconds
- 100+ weekly active users within 6 weeks
- <5% bounce rate on landing page
- Data updates within 24 hours of source

### Qualitative  
- "This is exactly what I needed"
- "Finally, all the data in one place"
- "Helps me understand without telling me what to do"
- Users recommend to others

---

**Remember**: We show what IS, not what WILL BE. Context over conclusions.