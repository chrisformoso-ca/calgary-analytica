-- Create mapping between Calgary sectors and CREB districts
-- This allows joining geospatial sector data with CREB housing district data

-- Option 1: Create a mapping table
CREATE TABLE IF NOT EXISTS sector_district_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_code TEXT NOT NULL,
    sector_name TEXT NOT NULL,
    creb_district TEXT NOT NULL,
    UNIQUE(sector_code),
    UNIQUE(creb_district)
);

-- Populate the mapping
INSERT OR REPLACE INTO sector_district_mapping (sector_code, sector_name, creb_district) VALUES
    ('CENTRE', 'CENTRE', 'City Centre'),
    ('EAST', 'EAST', 'East'),
    ('NORTH', 'NORTH', 'North'),
    ('NORTHEAST', 'NORTHEAST', 'North East'),
    ('NORTHWEST', 'NORTHWEST', 'North West'),
    ('SOUTH', 'SOUTH', 'South'),
    ('SOUTHEAST', 'SOUTHEAST', 'South East'),
    ('WEST', 'WEST', 'West');

-- Option 2: Create a view that joins the data
CREATE VIEW IF NOT EXISTS creb_districts_with_boundaries AS
SELECT 
    s.code as sector_code,
    s.name as sector_name,
    m.creb_district,
    s.multipolygon,
    s.communities
FROM community_sectors s
JOIN sector_district_mapping m ON s.code = m.sector_code;

-- Example usage: Get housing data with geographic boundaries
-- SELECT 
--     h.*,
--     c.multipolygon
-- FROM housing_district_monthly h
-- JOIN creb_districts_with_boundaries c ON h.district = c.creb_district
-- WHERE h.date = '2025-05-01';