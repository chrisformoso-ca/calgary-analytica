# Geographic Boundaries Datasets

## Overview
Extracts Calgary's official geographic boundaries including communities, districts, and sectors.

## Extractors

### extractor.py
Original boundary extractor for community boundaries.
```bash
python3 extractor.py
```

### extractor_batch.py
Batch extractor for all geospatial datasets (recommended).
```bash
# Extract all geospatial data
python3 extractor_batch.py

# Test mode - show what would be extracted
python3 extractor_batch.py --test
```

## Datasets Extracted

### 1. Community Boundaries (`surr-xmvs`)
- 313 communities with official boundaries
- Fields: community_code, name, sector, multipolygon
- Base layer for all community-level analysis

### 2. Community Districts (`86mc-9jh2`)
- 9 administrative districts (1-8 + P)
- NOT the same as CREB districts
- Fields: code, name, multipolygon

### 3. Community Sectors (`mz2j-7eb5`)
- 8 geographic sectors (NORTH, NORTHEAST, etc.)
- **These match CREB housing districts!**
- Fields: code, name, multipolygon

## Key Discovery: Sectors = CREB Districts
The `sector_district_mapping` table maps Calgary sectors to CREB district names:
- CENTRE → City Centre
- NORTHEAST → North East (etc.)

This enables joining CREB housing data with geographic boundaries.

## Database Tables
- `community_boundaries` - All Calgary communities
- `community_districts` - Administrative districts
- `community_sectors` - Geographic sectors
- `sector_district_mapping` - Maps sectors to CREB districts

## Usage Example
```sql
-- Get CREB housing data with boundaries
SELECT h.*, c.multipolygon
FROM housing_district_monthly h
JOIN creb_districts_with_boundaries c ON h.district = c.creb_district
```