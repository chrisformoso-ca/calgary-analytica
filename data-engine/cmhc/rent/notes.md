# CMHC Rental Market Data Notes

## Overview
CMHC (Canada Mortgage and Housing Corporation) rental market reports provide annual snapshots of Calgary's rental market conditions. This data complements our housing sales data by providing insights into the rental side of the market.

## Data Sources
- Primary source: CMHC Rental Market Reports (RMR) for Alberta
- Files: `rmr-alberta-YYYY-en.xlsx` (2019-2024)
- Update frequency: Annual (October data released in January/February)
- Historical coverage: 2019-2024 (6 years)

## Extraction Methods
- Tool: Python with pandas and openpyxl
- Extractor: `extractor_v2.py` (improved version)
- Key tables extracted:
  - Table 1.1.1: Vacancy rates by bedroom type
  - Table 1.1.2: Average rents by bedroom type
  - Table 1.1.3: Rental universe (total units)
  - Table 1.1.5: Percentage change in average rent
  - Table 1.1.6: Turnover rates
  - Table 2.x.x: Townhouse data
  - Table 4.1.2: Rental condo vs apartment comparison
- Challenges:
  - Excel files have merged cells and complex headers
  - Data quality indicators (a,b,c,d) need parsing
  - Some values suppressed for confidentiality (**)
  - Multi-row headers require careful column mapping

## Data Quality Notes
- CMHC uses letter grades for data reliability:
  - a = Excellent (CV ≤ 2.5%)
  - b = Very Good (2.5% < CV ≤ 5%)
  - c = Good (5% < CV ≤ 10%)
  - d = Use with caution (10% < CV ≤ 16.5%)
- Data is from October survey each year
- Calgary data is at CMA (Census Metropolitan Area) level only
- No zone/neighborhood breakdowns available in these files

## Key Metrics Available
1. **Vacancy Rate (%)**: Percentage of rental units that are vacant and available
2. **Average Rent ($)**: Mean monthly rent by bedroom type
3. **Rental Universe**: Total number of purpose-built rental units
4. **Property Types**: Apartments, townhouses, rental condos
5. **Bedroom Types**: Bachelor, 1 Bedroom, 2 Bedroom, 3 Bedroom+, Total
6. **Year-over-Year Changes**: Both current and previous year data extracted

## Integration with Calgary Data Lake
This rental data enhances our housing market analysis by:
- Providing rental market tightness indicators (vacancy rates)
- Tracking rental affordability trends
- Enabling rent vs. buy comparisons
- Supporting investment property analysis
- Showing differences between rental condos and purpose-built rentals

## Extraction Results (2024 file)
- Total records: ~34 per file
- Property types: apartment, townhouse, rental_condo, apartment_comparison
- Years covered: Both 2023 and 2024 data for trend analysis
- Confidence score: 85-95% depending on data quality indicators

## Data Limitations and Known Gaps

### Missing Data by Property Type
CMHC only reports data where sample sizes are sufficient for reliability:

1. **Apartments** - Most complete coverage:
   - All bedroom types typically available
   - All metrics (vacancy, rent, universe) reported

2. **Townhouses** - Limited data:
   - No data for 2018 (CMHC didn't report)
   - Vacancy rates: Only 2 Bedroom reported (sample size too small for other types)
   - Average rents: Various bedroom types by year
   - Rental universe: Only 1 Bedroom reported

3. **Rental Condos** - Variable coverage:
   - Bachelor units rare (few condos have studio units)
   - Coverage varies by year based on sample availability
   - Only average rent data (no vacancy or universe data)

### Quality Indicators
- Many records have blank quality indicators - this is normal CMHC reporting
- Only ~30% of data points receive a/b/c/d ratings
- Blank doesn't mean bad data, just unrated

### Table 4.1.2 Note
- This table contains both rental condo AND duplicate apartment data
- We extract only rental condo data to avoid duplication
- Apartment data is already captured from Tables 1.1.x

## Future Improvements
- Extract additional metrics (turnover rates, rent change percentages)
- Improve column mapping for more complete extraction
- Add validation for expected record counts
- Create automated comparison with previous year's data