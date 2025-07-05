# CMHC Rental Data Extraction Pattern - 2024

## File: rmr-alberta-2024-en.xlsx

### Successfully Extracted Data Summary

**Total Records**: 34 records
**Years**: 2023, 2024 (includes previous year comparisons)
**Property Types**: apartment, townhouse, rental_condo, apartment_comparison

### Data Breakdown

1. **Apartment Data (22 records)**
   - Vacancy rates: 10 records (5 bedroom types × 2 years)
   - Average rents: 10 records (5 bedroom types × 2 years)
   - Rental universe: 2 records (incomplete extraction)

2. **Townhouse Data (6 records)**
   - Vacancy rates: 1 record (only 2BR extracted)
   - Average rents: 4 records (4 bedroom types)
   - Rental universe: 1 record (only 1BR extracted)

3. **Rental Condo Data (6 records)**
   - Average rents: 2 records (1BR, 2BR)
   - Apartment comparison: 4 records

### Sample Data Points

**Vacancy Rates (2024)**:
- Bachelor: 4.5%
- 1 Bedroom: 4.7%
- 2 Bedroom: 5.1%
- 3 Bedroom+: 3.7%
- Total: 4.8%

**Average Rents (2024)**:
- Bachelor: $1,362
- 1 Bedroom: $1,585 (apartment), $1,599 (rental condo)
- 2 Bedroom: $1,882 (apartment), $1,970 (rental condo)
- 3 Bedroom+: $1,975

**Year-over-Year Rent Increases (2023→2024)**:
- Bachelor: $1,204 → $1,362 (+13.1%)
- 1 Bedroom: $1,464 → $1,585 (+8.3%)
- 2 Bedroom: $1,695 → $1,882 (+11.0%)
- Total: $1,571 → $1,732 (+10.2%)

### Known Issues

1. **Incomplete Universe Data**: Only extracted 2 of 5 expected rental universe values for apartments
2. **Column Mapping**: Some tables have complex multi-row headers requiring careful column index mapping
3. **Townhouse Data**: Limited extraction - may need to adjust column positions

### Quality Indicators

Most data points include CMHC quality ratings:
- 'a' = Excellent (most common for average rents)
- 'b' = Very Good
- Missing indicators for some vacancy rates and universe counts