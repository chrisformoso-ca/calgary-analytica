# Calgary Open Data Portal Notes

## Overview
Calgary's Open Data Portal provides 400+ datasets via Socrata API. We're starting with high-value datasets that complement our existing housing, economic, and crime data.

## API Access
- Base URL: `https://data.calgary.ca/resource/[DATASET_ID].[FORMAT]`
- Formats: json, csv, xml
- Default limit: 1000 records (use `$limit` parameter, max 50000)
- No authentication required for public datasets

## Common Query Parameters
- `$limit` - Number of records (default 1000, max 50000)
- `$offset` - Skip records for pagination
- `$where` - SQL-like filtering (e.g., `requested_date > '2025-01-01'`)
- `$order` - Sort results (e.g., `requested_date DESC`)
- `$select` - Choose specific fields

## Priority Datasets

### Geospatial Base Layers (CRITICAL FOR MAPS)

#### 1. Community Boundaries (ab7m-fwn6) 🗺️
- **Records**: ~200 communities
- **Key fields**: comm_code, name, multipolygon, area_hectares
- **Use case**: Base layer for all community-level analysis and mapping
- **Format**: GeoJSON multipolygon boundaries
- **Note**: Cache locally - rarely changes

#### 2. Community Districts (86mc-9jh2) 🗺️
- **Records**: 14 districts
- **Key fields**: district_code, district_name, multipolygon
- **Use case**: Match CREB district data, aggregate community data
- **Format**: GeoJSON multipolygon boundaries

#### 3. Community Sectors (mz2j-7eb5) 🗺️
- **Records**: 8 sectors (NW, NE, SW, SE, N, S, E, W)
- **Key fields**: sector_code, sector_name, multipolygon
- **Use case**: High-level geographic groupings
- **Format**: GeoJSON multipolygon boundaries

### Operational Data

#### 4. 311 Service Requests (iahh-g8bj)
- **Records**: 1M+ since 2012
- **Key fields**: service_request_id, requested_date, service_name, status, community, lat/lon
- **Use case**: Track city service patterns, response times, common issues by area
- **Strategy**: Extract monthly batches to avoid API limits

#### 5. Building Permits (c2es-76ed)
- **Records**: 470K since 1999
- **Key fields**: permitnum, permit_type, estimated_cost, community, dates, lat/lon
- **Use case**: Construction trends, development hotspots, permit processing times
- **Related**: Development permits (6933-unw5)

#### 6. Business Licences (vdjc-pybd)
- **Records**: ~50K active
- **Key fields**: business_name, licence_type, address, issue/expiry dates, lat/lon
- **Use case**: Business density, new business trends, licence compliance

## Extraction Strategy

1. **Incremental Updates**: Use date filtering to get only new/updated records
2. **Batch Processing**: Process large datasets in monthly chunks
3. **Error Handling**: Retry failed requests with exponential backoff
4. **Caching**: Store raw API responses in `/raw/` for debugging

## Example API Calls

```bash
# Get latest 10 building permits
curl "https://data.calgary.ca/resource/c2es-76ed.json?$order=applieddate DESC&$limit=10"

# Get 311 requests from last 7 days
curl "https://data.calgary.ca/resource/iahh-g8bj.json?$where=requested_date > '2025-06-18'"

# Get all dog parks in Bowness
curl "https://data.calgary.ca/resource/enr4-crti.json?$where=description like '%BOWNESS%'"
```

## Data Quality Notes

- **311 Data**: Very clean, consistent format since 2012
- **Building Permits**: Some historical records have missing coordinates
- **Business Licences**: Address geocoding not always accurate
- **Geospatial Data**: Use multipolygon/point fields when available

## Performance Tips

1. Always use date filters on large datasets
2. Request only needed fields with `$select`
3. Use current year dataset (arf6-qysm) for recent 311 data
4. Cache community boundaries locally (rarely changes)

## Future Enhancements

- Add more datasets based on user needs
- Implement real-time update notifications
- Create cross-dataset analysis (e.g., permits vs. 311 complaints)
- Build geospatial visualization layer

## 311 Data Aggregation Methodology

### Overview
We transform Calgary's 311 service request data from millions of individual records into meaningful monthly economic indicators.

### Data Transformation
- **Raw Data**: ~6.86 million individual 311 service requests (2010-2025)
- **Processed Data**: ~191,000 monthly aggregated records (2017-2025)
- **Compression Ratio**: 36:1
- **Database Table**: `service_requests_311_monthly`

### Why We Aggregate

1. **Focus on Trends, Not Incidents**
   - Monthly trends in community stress indicators
   - Year-over-year changes in service patterns
   - Community-level economic health signals

2. **Data Volume Management**
   - Raw: 6.86 million records would overwhelm analysis
   - Aggregated: 191K records are manageable and meaningful
   - Storage: Reduced from ~2GB to ~50MB

3. **Privacy and Relevance**
   - Individual addresses/complaints aren't relevant for economic analysis
   - Community-level aggregation protects privacy
   - Focus on patterns, not people

### Aggregation Process

#### Category Mapping
We map 100+ service types into 10 economic indicator categories:

**Housing Quality Indicators**
- `Bylaw`: Long Grass, Snow/Ice on Sidewalk, Untidy Property
- `Waste`: Cart Management, Missed Pickup, Recycling
- `Graffiti`: Graffiti Concerns, Vandalism
- `Snow/Ice`: Snow and Ice Control, SNIC
- `Parks/Trees`: Tree Concern, Grass Maintenance, Litter

**Economic Stress Indicators**
- `Encampments`: Encampment Concerns, Alpha House
- `Derelict Properties`: Derelict Building, Vacant Properties
- `Infrastructure`: Pothole, Streetlight, Water Main Break
- `Transit`: Transit Feedback, Safety Concerns
- `Social Stress`: Noise, Community Concerns, Wildlife Distress

#### Monthly Aggregation
For each month, community, and category:
- `total_requests`: Count of all requests
- `avg_days_to_close`: Mean resolution time
- `median_days_to_close`: Median resolution time

#### Data Filtering
- **Excluded**: "Other" category (~40% of requests) - not relevant for economic analysis
- **Filtered**: Rows with NULL community_code (~40-75 per year)
- **Date Range**: 2017-present (aligns with economic indicator data)

### Key Decisions

**Why Not Track Open/Closed Status?**
- Historical data becomes stale (a 2017 "open" request is meaningless in 2025)
- We care about volume and resolution time, not current status
- Simplified schema focuses on trend analysis

**Why Start from 2017?**
- Aligns with our economic indicator data (2017-present)
- Encampment data begins appearing in 2017
- Consistent data quality and categorization

### Usage Examples

```sql
-- Encampment trend analysis
SELECT year, SUM(total_requests) as encampment_reports
FROM service_requests_311_monthly
WHERE service_category = 'Encampments'
GROUP BY year;

-- Infrastructure response time trends
SELECT year, 
       ROUND(AVG(avg_days_to_close), 1) as avg_response_days
FROM service_requests_311_monthly
WHERE service_category = 'Infrastructure'
GROUP BY year;
```

### Extraction Commands

```bash
# Extract specific month
python3 extractor_311_monthly.py --year 2025 --month 7

# Extract full year
python3 extractor_311_monthly.py --year 2024

# Extract multiple years
python3 extractor_311_monthly.py --years 2023 2024

# Extract year range
python3 extractor_311_monthly.py --start-year 2017 --end-year 2022
```