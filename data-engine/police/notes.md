# Police/Crime Data Source Notes

## Overview
Calgary Police Service provides monthly community crime and disorder statistics.

## Data Format
- **File Format**: Excel (.xlsx)
- **Update Frequency**: Monthly
- **Coverage**: Community-level crime statistics

## Data Categories
- Person crimes
- Property crimes
- Disorder events
- Traffic incidents
- By community (100+ communities)

## Known Issues
1. **Community Names**: Must match official Calgary community names
2. **Data Delays**: Usually 1-2 months behind current date
3. **Privacy**: Some communities may have suppressed data (< 5 incidents)

## Extraction Tips
- Multiple sheets in Excel file
- Look for "YTD" (Year-to-Date) comparisons
- Community names in first column
- Check for data notes/footnotes

## Validation Checks
- Community count: Should be ~150-200
- No negative crime counts
- Year-over-year changes typically within ±50%
- Total city crimes should sum correctly