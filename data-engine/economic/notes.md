# Economic Data Source Notes

## Overview
City of Calgary Economic Development provides monthly/quarterly economic indicators.

## Data Formats
- **Recent Files (2015+)**: Excel files (.xlsx)
- **Historical Files (2009-2015)**: PDF files
- **Naming Convention**: 
  - Excel: `Current-Economic-Indicators-YYYY-MM.xlsx`
  - PDF: `current-economic-analysis-YYYY-MM.pdf`

## Key Indicators
- Unemployment rate
- Population growth
- GDP estimates
- Housing starts
- Building permits
- Employment by sector
- Consumer price index (CPI)
- Business licenses

## Known Issues
1. **Format Changes**: Excel structure changed around 2015
2. **Missing Data**: Some months have incomplete indicators
3. **Units Vary**: Percentages, thousands, millions - check units carefully

## Extraction Tips
- Excel files: Use pandas read_excel with specific sheet names
- PDF files: More challenging, may need OCR for older files
- Look for "Calgary Economic Region" data specifically

## Validation Checks
- Unemployment rate: typically 3-15%
- Population: ~1.3-1.5 million range
- Year-over-year changes: usually < 20% except crisis periods