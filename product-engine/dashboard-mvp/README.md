# Calgary Housing Dashboard MVP - Data Exports

This directory contains the JSON data exports for the Calgary Housing Dashboard MVP, designed for use with Claude Artifacts or any static web application.

## 📁 Directory Structure

```
dashboard-mvp/
├── data/                  # Current JSON exports
│   ├── market_overview.json
│   ├── economic_indicators.json
│   ├── district_data.json
│   ├── rate_data.json
│   └── metadata.json
├── scripts/               # Export generation scripts
│   ├── generate_all_exports.py    # Main runner
│   └── generate_*.py              # Individual generators
└── archive/               # Historical exports by month
```

## 🚀 Quick Start

### Generate All Exports
```bash
cd scripts
python3 generate_all_exports.py
```

### Generate Single Export
```bash
python3 generate_all_exports.py --single market
```

### Validate Exports
```bash
python3 validate_exports.py
```

## 📊 JSON Files Overview

### market_overview.json
- Current housing prices by property type
- 24-month price history
- Sales volume and inventory trends
- YoY/MoM changes
- Market insights

### economic_indicators.json
- Employment and unemployment rates
- Population growth
- Interest rates
- Oil prices
- Housing starts
- Building permits

### district_data.json
- Pricing by district and property type
- Sortable pricing table
- Best value districts
- Entry-level options (<$400k)
- Appreciation rankings

### rate_data.json
- Current interest rates
- 5-year rate history
- Payment scenarios
- Affordability metrics
- Stress test calculations

### metadata.json
- Data freshness information
- Quality scores
- Known issues
- Update schedule
- Source attribution

## 📅 Monthly Update Process

1. **Data Collection** (1st-5th of month)
   - CREB releases housing data
   - Economic indicators updated
   
2. **Run Exports** (5th of month)
   ```bash
   cd scripts
   python3 generate_all_exports.py
   ```

3. **Manual Updates Required**
   - Mortgage rates in `generate_rate_data.py`
   - Check for new wage data
   - Update M2 money supply when available

## ⚠️ Known Data Gaps

1. **Wage Growth Data** - Available in source files but not extracted yet
2. **Money Supply (M2)** - Need to source from Bank of Canada
3. **Mortgage Rates** - Currently manual, need API integration

## 🔧 Development

### Adding New Indicators
1. Update the appropriate generator script
2. Run validation to ensure compatibility
3. Update metadata generator if needed

### Testing
```bash
# Dry run to see what would be generated
python3 generate_all_exports.py --dry-run

# Validate all exports
python3 validate_exports.py
```

## 📈 Using with Claude Artifacts

Simply copy the JSON files to your Artifacts project and reference them:

```javascript
// Example usage
fetch('market_overview.json')
  .then(response => response.json())
  .then(data => {
    console.log('Current benchmark price:', data.current_data.total.benchmark_price);
  });
```

## 📝 Notes

- All prices are in CAD
- Dates are in YYYY-MM or YYYY-MM-DD format
- Population in thousands (multiply by 1000 for actual)
- Building permits in millions
- Interest rates as percentages

## 🤝 Support

For issues or questions about the data exports, please contact the Calgary Analytica team.