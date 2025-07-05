# Rentfaster Data Notes

## Overview
Rentfaster is Calgary's primary rental listing platform, capturing both primary and secondary rental markets. This includes the crucial single detached house rental data that CMHC doesn't track.

## Data Source
- Website: https://www.rentfaster.ca
- API Endpoint: `https://www.rentfaster.ca/api/search.json`
- Update frequency: Real-time (current listings)
- Coverage: Calgary and surrounding areas

## Extraction Method
- Tool: Python with requests library
- API Parameters:
  - `city_id=1` (Calgary)
  - `cur_page` (pagination)
  - `proximity_type=location-city`
- No authentication required
- Respectful rate limiting implemented

## Data Available

### Property Types Captured
- **Single Detached Houses** (fills CMHC gap!)
- Apartments/Condos
- Townhouses
- Semi-detached/Duplexes
- Basement suites
- Rooms for rent

### Fields Extracted
- Listing ID and status
- Property type and size (sq ft)
- Bedrooms and bathrooms
- Monthly rent
- Utilities included
- Address and community
- Availability date
- Geographic coordinates

## Integration with Calgary Data Lake

This data complements CMHC rental data by:
1. **Filling the single detached gap** - CMHC only covers purpose-built rentals
2. **Current market pricing** - Real asking rents vs CMHC's October snapshots
3. **Geographic granularity** - Community-level data vs CMHC's CMA-level
4. **All property types** - Including basement suites and rooms

## Data Collection Strategy

### Monthly Snapshots
- Run extractor monthly to build historical dataset
- Store as snapshots to track market changes over time
- Aggregate into monthly summaries for trend analysis

### Database Tables
1. `rental_listings_snapshot` - Detailed listing data
2. `rental_market_summary_monthly` - Aggregated statistics
3. Views for current market analysis

## Limitations
- Only current listings (no historical data before collection starts)
- Asking rents (not actual transaction prices)
- May include duplicates or outdated listings
- Coverage depends on landlord adoption of platform

## Usage Notes
- Start with conservative page limits (5-10 pages)
- Each page returns ~10-20 listings
- Total Calgary listings typically 1000-2000
- Monitor for API changes or rate limits

## Comparison with CMHC Data

| Aspect | CMHC | Rentfaster |
|--------|------|------------|
| Update Frequency | Annual (October) | Real-time |
| Property Types | Apartments, Townhouses | All types including single detached |
| Geographic Detail | CMA level | Community level |
| Historical Data | 2019-2024 | Current only (build over time) |
| Data Type | Survey data | Listing data |
| Market Coverage | Purpose-built only | Primary + Secondary |

## Future Enhancements
- Automated monthly collection via cron job
- Deduplication logic for repeat listings
- Price change tracking for same units
- Integration with CMHC data for complete market view