# CREB Data Source Notes

## Overview
Calgary Real Estate Board (CREB) provides monthly PDF reports with housing market statistics.

## Data Format
- **File Format**: PDF (Monthly Stats Package)
- **Naming Convention**: `MM_YYYY_Calgary_Monthly_Stats_Package.pdf`
- **Key Pages**:
  - Page 7: District-level data (8 districts × 4 property types)
  - Page 11: City-wide Total
  - Page 13: Detached homes
  - Page 15: Semi-detached homes
  - Page 17: Apartments
  - Page 19: Row houses

## Known Issues
1. **Multi-page Tables**: Some tables span multiple pages, requiring page concatenation
2. **District Names**: Can have variations (e.g., "North East" vs "Northeast")
3. **Data Quality**: Benchmark prices are most reliable; median/average can be missing

## Extraction Tips
- Use pdfplumber for best results (confidence typically > 90%)
- Expected records per month: 32 for districts, 5 for city-wide
- Validate price ranges: $200,000 - $1,500,000 typical for Calgary

## Validation Checks
- District count should be 8
- Property types should be 4 (Detached, Semi-detached, Apartment, Row)
- Total records per month: 32 district + 5 city = 37 records