# City of Calgary Open Data Catalog

## Context
- **Curated Date**: June 19, 2025
- **Coverage**: This catalog contains 40 of the 400+ datasets available on Calgary's Open Data Portal
- **Full Portal**: https://data.calgary.ca/

## API Access Pattern
```
https://data.calgary.ca/resource/[DATASET_ID].[FORMAT]
```
- **Formats**: json, csv, xml
- **Default limit**: 1000 records (max 50000)
- **Authentication**: Public access (no auth required)

---

## Dataset Catalog

### 📰 NEWS AND EVENTS

#### 1. City of Calgary Newsroom
- **Dataset ID**: `3x6m-4vs7`
- **Direct URL**: https://data.calgary.ca/News-and-Events/City-of-Calgary-Newsroom/3x6m-4vs7
- **API Endpoint**: https://data.calgary.ca/resource/3x6m-4vs7.json
- **Description**: Real-time news feed from all City sources
- **Update Frequency**: Daily (multiple times)
- **Records**: 26 (rolling window)
- **Key Fields**: title, pubdate, link
- **Use Cases**: Current city announcements, emergency updates, policy changes
- **Example Query**: `https://data.calgary.ca/resource/3x6m-4vs7.json?$order=pubdate DESC&$limit=10`

#### 2. City of Calgary Events
- **Dataset ID**: `n625-9k5x`
- **Direct URL**: https://data.calgary.ca/News-and-Events/City-of-Calgary-Events/n625-9k5x
- **API Endpoint**: https://data.calgary.ca/resource/n625-9k5x.json
- **Description**: All public meetings, recreation events, and city activities
- **Update Frequency**: Daily (twice - morning and afternoon)
- **Records**: 241
- **Key Fields**: address, host_organization, title, event_type, event_group, more_info_url, all_dates, next_date_times, longitude, latitude, point
- **Geospatial**: Yes (lat/lon coordinates)
- **RSS Feed**: https://www.trumba.com/calendars/map-feeds.rss
- **Use Cases**: Finding events by date/location, community activities, public consultations

---

### 🏞️ RECREATION AND CULTURE

#### 3. Parks Off Leash Areas
- **Dataset ID**: `enr4-crti`
- **Direct URL**: https://data.calgary.ca/Recreation-and-Culture/Parks-Off-Leash-Areas/enr4-crti
- **API Endpoint**: https://data.calgary.ca/resource/enr4-crti.json
- **Description**: All 150+ off-leash dog areas with boundaries
- **Update Frequency**: Weekly
- **Records**: 178
- **Key Fields**: OFF_LEASH_AREA_ID, CATEGORY, STATUS, DESCRIPTION, FENCING_INFO, PARCEL_LOCATION, MULTIPOLYGON
- **Geospatial**: Yes (MultiPolygon boundaries)
- **Use Cases**: Finding nearest off-leash area, checking if fenced, area status

#### 4. Recreation Facilities
- **Dataset ID**: `hxfu-6d96`
- **Direct URL**: https://data.calgary.ca/Recreation-and-Culture/Recreation-Facilities/hxfu-6d96
- **API Endpoint**: https://data.calgary.ca/resource/hxfu-6d96.json
- **Description**: All city recreation centers, pools, arenas, etc.
- **Records**: ~250
- **Key Fields**: Facility_Name, Address, Facility_Type, Amenities, Programs
- **Geospatial**: Yes
- **Use Cases**: Finding facilities by type, amenities search, program availability

---

### 🔧 SERVICES AND AMENITIES

#### 5. 311 Service Requests (Complete Historical)
- **Dataset ID**: `iahh-g8bj`
- **Direct URL**: https://data.calgary.ca/Services-and-Amenities/311-Service-Requests/iahh-g8bj
- **API Endpoint**: https://data.calgary.ca/resource/iahh-g8bj.json
- **Description**: All service requests from 2012 to present
- **Update Frequency**: Daily
- **Records**: 1M+
- **Time Period**: 2012-present
- **Key Fields**: 
  - service_request_id (unique identifier)
  - requested_date, updated_date, closed_date
  - status_description (open/closed)
  - source (phone/app/web)
  - service_name (type of request)
  - agency_responsible
  - address, comm_code, comm_name
  - longitude, latitude, point
- **Geospatial**: Yes
- **Use Cases**: Service trends, response times, common issues by area
- **Performance Note**: Use date filters for large queries

#### 6. 311 Service Requests (Current Year Only)
- **Dataset ID**: `arf6-qysm`
- **Direct URL**: https://data.calgary.ca/Services-and-Amenities/311-Service-Requests-Current-Year/arf6-qysm
- **API Endpoint**: https://data.calgary.ca/resource/arf6-qysm.json
- **Description**: Current year subset for better performance
- **Update Frequency**: Daily
- **Records**: ~100K
- **Use Cases**: Recent issues, current year analysis

---

### 🚗 TRANSPORTATION TRANSIT

#### 7. Road Construction Projects
- **Dataset ID**: `sizs-hgef`
- **Direct URL**: https://data.calgary.ca/Transportation-Transit/Road-Construction-Projects/sizs-hgef
- **API Endpoint**: https://data.calgary.ca/resource/sizs-hgef.json
- **Description**: All current and planned road construction
- **Update Frequency**: Weekly
- **Records**: ~500
- **Key Fields**: Project_Name, Location, Start_Date, End_Date, Status, Impact_Level
- **Geospatial**: Yes
- **Use Cases**: Route planning, construction impacts, project timelines

---

### 💼 BUSINESS AND ECONOMIC ACTIVITY

#### 8. Building Permits
- **Dataset ID**: `c2es-76ed`
- **Direct URL**: https://data.calgary.ca/Business-and-Economic-Activity/Building-Permits/c2es-76ed
- **API Endpoint**: https://data.calgary.ca/resource/c2es-76ed.json
- **Description**: All building permit applications since 1999
- **Update Frequency**: Daily
- **Records**: 470K
- **Time Period**: 1999-06-22 to present
- **Key Fields** (30 total):
  - PermitNum (unique ID)
  - StatusCurrent, AppliedDate, IssuedDate, CompletedDate
  - PermitType, PermitClass, WorkClass
  - Description, ApplicantName
  - EstProjectCost, TotalSqft
  - HousingUnits, CommunityCode, CommunityName
  - OriginalAddress, Latitude, Longitude
- **Geospatial**: Yes
- **Use Cases**: Construction trends, permit processing times, development hotspots
- **Related Datasets**: 
  - Building Permits by Community: `kr8b-c44i`
  - Building Permit Values by Community: `jzna-hfhu`

#### 9. Calgary Business Licences
- **Dataset ID**: `vdjc-pybd`
- **Direct URL**: https://data.calgary.ca/Business-and-Economic-Activity/Calgary-Business-Licences/vdjc-pybd
- **API Endpoint**: https://data.calgary.ca/resource/vdjc-pybd.json
- **Description**: All active business licences
- **Update Frequency**: Monthly
- **Records**: ~50K
- **Key Fields**: Business_Name, Licence_Type, Address, Issue_Date, Expiry_Date
- **Geospatial**: Yes
- **Use Cases**: Business directory, licence compliance, business density analysis

#### 10. Development Permits
- **Dataset ID**: `6933-unw5`
- **Direct URL**: https://data.calgary.ca/Business-and-Economic-Activity/Development-Permits/6933-unw5
- **API Endpoint**: https://data.calgary.ca/resource/6933-unw5.json
- **Description**: Land use and development applications
- **Update Frequency**: Daily
- **Records**: ~100K
- **Geospatial**: Yes

#### 11. Short-Term Rentals
- **Dataset ID**: `gzkz-5k9a`
- **Direct URL**: https://data.calgary.ca/Business-and-Economic-Activity/Short-Term-Rentals/gzkz-5k9a
- **API Endpoint**: https://data.calgary.ca/resource/gzkz-5k9a.json
- **Description**: Licensed STR properties (Airbnb, VRBO, etc.)
- **Update Frequency**: Monthly
- **Records**: ~2K
- **Related Datasets**:
  - STR Map View: `xmzy-ebse`
  - STR by Community: `5tyb-x8qg`

#### 12. Economic Indicators
- **Dataset ID**: `7cvb-8ame`
- **Direct URL**: https://data.calgary.ca/Business-and-Economic-Activity/Monthly-Economic-Indicators/7cvb-8ame
- **API Endpoint**: https://data.calgary.ca/resource/7cvb-8ame.json
- **Description**: Key economic metrics including unemployment, GDP, housing starts
- **Update Frequency**: Monthly

#### 13. Employment & Unemployment Rates
- **Employment Dataset ID**: `a3cq-4yfn`
- **Unemployment Dataset ID**: `wzpt-744u`
- **Direct URLs**: 
  - https://data.calgary.ca/Business-and-Economic-Activity/Employment-Rates/a3cq-4yfn
  - https://data.calgary.ca/Business-and-Economic-Activity/Unemployment-rates/wzpt-744u

---

### 🏥 HEALTH AND SAFETY

#### 14-17. Permit Inspections (Multiple Types)
- **Mechanical/HVAC**: `cdrc-r4u8`
- **Electrical**: `vxgy-id5s`
- **Plumbing**: `5pvv-k7hn`
- **Gas**: `tg24-jt7r`
- **Base URL Pattern**: https://data.calgary.ca/Health-and-Safety/[TYPE]-Permits-and-Inspections/[ID]
- **Update Frequency**: Daily
- **Use Cases**: Inspection history, permit status, contractor performance

#### 18. Community Disorder Statistics
- **Dataset ID**: `h3h6-kgme`
- **Direct URL**: https://data.calgary.ca/Health-and-Safety/Community-Disorder-Statistics/h3h6-kgme
- **Description**: Crime and disorder statistics by community
- **Update Frequency**: Monthly
- **Geospatial**: Yes

#### 19-22. Police & Fire Resources
- **Police Service Locations**: `ap4r-bav3`
- **Police Zones**: `f6ia-q8cs`
- **Police Districts**: `86mc-9jh2`
- **Fire Stations**: `cqsb-2hhg`
- **Additional Resource**: https://www.calgary.ca/cps/statistics/calgary-police-statistical-reports.html

#### 23. Playground Zones
- **Dataset ID**: `bhnd-tp2r`
- **Direct URL**: https://data.calgary.ca/Health-and-Safety/Playground-Zones/bhnd-tp2r
- **Description**: Reduced speed zones near playgrounds
- **Geospatial**: Yes

---

### 🌳 ENVIRONMENT

#### 24. Corporate Energy Consumption
- **Dataset ID**: `crbp-innf`
- **Direct URL**: https://data.calgary.ca/Environment/Corporate-Energy-Consumption/crbp-innf
- **Description**: Energy use by City facilities
- **Update Frequency**: Annual

#### 25. Tree Canopy 2022
- **Dataset ID**: `mn2n-4z98`
- **Direct URL**: https://data.calgary.ca/Environment/Tree-Canopy-2022/mn2n-4z98
- **Description**: Tree coverage analysis from 2022
- **Geospatial**: Yes (raster data)

#### 26. Natural Areas
- **Dataset ID**: `szzc-mugz`
- **Direct URL**: https://data.calgary.ca/Environment/Natural-Areas/szzc-mugz
- **Description**: Protected natural areas and parks
- **Geospatial**: Yes

#### 27. Public Trees
- **Dataset ID**: `tfs4-3wwa`
- **Direct URL**: https://data.calgary.ca/Environment/Public-Trees/tfs4-3wwa
- **Description**: Individual tree inventory
- **Geospatial**: Yes (point data)
- **Key Fields**: Species, Diameter, Height, Condition, Location

---

### 🗺️ BASE MAPS & GEOGRAPHIC DATA

#### 28. Community Boundaries
- **Dataset ID**: `ab7m-fwn6`
- **Direct URL**: https://data.calgary.ca/Base-Maps/Community-Boundaries/ab7m-fwn6
- **Description**: Official community boundaries
- **Geospatial**: Yes
- **Use Cases**: Spatial joins, community analysis

#### 29. Land Use Districts
- **Dataset ID**: `mw9j-jik5`
- **Direct URL**: https://data.calgary.ca/Base-Maps/Land-Use-Districts/mw9j-jik5
- **Description**: Zoning boundaries
- **Geospatial**: Yes

#### 30. Land Use Designation Codes
- **Dataset ID**: `svbi-k49z`
- **Direct URL**: https://data.calgary.ca/Base-Maps/Land-Use-Designation-Codes/svbi-k49z
- **Description**: Reference table for land use codes
- **Key Fields**: lud_code, lud_description, lud_district, lud_url

#### 31. Community Sectors
- **Dataset ID**: `mz2j-7eb5`
- **Direct URL**: https://data.calgary.ca/Base-Maps/Community-Sectors/mz2j-7eb5
- **Description**: Groupings of communities
- **Geospatial**: Yes

---

### 🏛️ GOVERNMENT

#### 32. City of Calgary Careers
- **Dataset ID**: `5fsi-n9xm`
- **Direct URL**: https://data.calgary.ca/Government/City-of-Calgary-Careers/5fsi-n9xm
- **Description**: Current job postings
- **Update Frequency**: Daily

---

## API Usage Guide

### Basic API Pattern
```
https://data.calgary.ca/resource/[DATASET_ID].[FORMAT]
```

### Supported Formats
- `.json` - JSON format (recommended for APIs)
- `.csv` - CSV format
- `.xml` - XML format

### Common Query Parameters
- `$limit` - Number of records (default 1000, max 50000)
- `$offset` - Skip records for pagination
- `$where` - SQL-like filtering
- `$order` - Sort results
- `$select` - Choose specific fields
- `$q` - Full-text search

### Example Queries
```
# Get latest 10 building permits
https://data.calgary.ca/resource/c2es-76ed.json?$order=applieddate DESC&$limit=10

# Find all dog parks in a community
https://data.calgary.ca/resource/enr4-crti.json?$where=description like '%BOWNESS%'

# Get 311 requests from last 7 days
https://data.calgary.ca/resource/iahh-g8bj.json?$where=requested_date > '2025-06-12'
```

### Authentication
- Most datasets are public (no auth required)
- Rate limits apply (varies by dataset)
- For high-volume access, contact: opendata@calgary.ca

### Useful Links
- **Open Data Portal**: https://data.calgary.ca/
- **API Documentation**: https://dev.socrata.com/
- **Terms of Use**: https://data.calgary.ca/d/Open-Data-Terms/u45n-7awa
- **Support**: opendata@calgary.ca

### Tips for AI/LLM Usage
1. **Use specific dataset IDs** for direct access
2. **Apply date filters** on large datasets to improve performance
3. **Check update frequency** to know data freshness
4. **Use geospatial fields** for location-based queries
5. **Combine related datasets** (e.g., building permits + community boundaries)
6. **Cache frequently used reference data** (e.g., community names, land use codes)