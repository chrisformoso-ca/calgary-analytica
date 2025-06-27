# 311 Service Requests Dataset

## Overview
Extracts and processes Calgary's 311 service request data from the Open Data Portal.

## Data Sources
- **Historical**: All service requests from 2012-present (`iahh-g8bj`)
- **Current Year**: Performance-optimized subset (`arf6-qysm`)

## Extractors

### extractor.py
Extracts raw 311 service requests with all fields.
```bash
python3 extractor.py --year 2025 --month 6
```

### extractor_monthly.py
Aggregates 311 data into monthly economic indicators by community and category.
```bash
# Extract specific month
python3 extractor_monthly.py --year 2025 --month 6

# Extract full year
python3 extractor_monthly.py --year 2024

# Extract year range
python3 extractor_monthly.py --start-year 2017 --end-year 2022
```

## Key Features
- Transforms 6.86M individual requests into ~191K monthly aggregated records
- Maps 100+ service types into 10 economic indicator categories
- Tracks resolution times (avg/median days to close)
- Filters out non-economic categories

## Economic Categories
- **Housing Quality**: Bylaw, Waste, Graffiti, Snow/Ice, Parks/Trees
- **Economic Stress**: Encampments, Derelict Properties, Infrastructure, Transit, Social Stress

## Database Table
- `service_requests_311_monthly` - Monthly aggregated data by community/category