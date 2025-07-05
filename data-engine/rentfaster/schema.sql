-- Rentfaster Rental Listings Schema
-- Stores current rental market listings from Rentfaster API
-- This captures the secondary rental market including single detached houses

CREATE TABLE IF NOT EXISTS rental_listings_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Listing identifiers
    listing_id TEXT NOT NULL,
    extraction_week TEXT NOT NULL,       -- YYYY-W## format for weekly snapshots
    
    -- Property details
    property_type TEXT NOT NULL,         -- 'single_detached', 'apartment', 'townhouse', 'semi_detached', 'basement_suite', 'room', 'other'
    bedrooms INTEGER,
    bathrooms REAL,
    sq_feet INTEGER,
    
    -- Rental details
    rent INTEGER NOT NULL,               -- Monthly rent in dollars
    
    -- Location
    community TEXT,
    
    -- Constraints
    CHECK (property_type IN ('single_detached', 'apartment', 'townhouse', 'semi_detached', 'basement_suite', 'room', 'other')),
    UNIQUE(listing_id, extraction_week)   -- Prevent duplicates within same week
);

-- Indexes for common queries
CREATE INDEX idx_rental_listings_week ON rental_listings_snapshot(extraction_week);
CREATE INDEX idx_rental_listings_type ON rental_listings_snapshot(property_type);
CREATE INDEX idx_rental_listings_bedrooms ON rental_listings_snapshot(bedrooms);
CREATE INDEX idx_rental_listings_community ON rental_listings_snapshot(community);
CREATE INDEX idx_rental_listings_rent ON rental_listings_snapshot(rent);

-- Weekly summary table for trend analysis
CREATE TABLE IF NOT EXISTS rental_market_summary_weekly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Time period
    week TEXT NOT NULL,                  -- YYYY-W## format
    
    -- Property categorization
    property_type TEXT NOT NULL,
    bedrooms INTEGER,
    
    -- Summary statistics
    listing_count INTEGER NOT NULL,
    avg_rent REAL,
    median_rent REAL,
    min_rent INTEGER,
    max_rent INTEGER,
    avg_sq_feet REAL,
    
    -- Geographic distribution
    top_communities TEXT,                -- JSON array of top 5 communities
    
    -- Constraints
    UNIQUE(week, property_type, bedrooms)
);

-- View for latest rental market snapshot
CREATE VIEW current_rental_market AS
SELECT 
    property_type,
    bedrooms,
    COUNT(*) as listing_count,
    ROUND(AVG(rent), 0) as avg_rent,
    MIN(rent) as min_rent,
    MAX(rent) as max_rent,
    community,
    extraction_week
FROM rental_listings_snapshot
WHERE extraction_week = (SELECT MAX(extraction_week) FROM rental_listings_snapshot)
GROUP BY property_type, bedrooms, community;

-- View comparing property types
CREATE VIEW rental_comparison_by_type AS
SELECT 
    property_type,
    COUNT(*) as total_listings,
    ROUND(AVG(rent), 0) as avg_rent,
    ROUND(AVG(CASE WHEN bedrooms = 1 THEN rent END), 0) as avg_1br_rent,
    ROUND(AVG(CASE WHEN bedrooms = 2 THEN rent END), 0) as avg_2br_rent,
    ROUND(AVG(CASE WHEN bedrooms = 3 THEN rent END), 0) as avg_3br_rent,
    ROUND(AVG(sq_feet), 0) as avg_sq_feet
FROM rental_listings_snapshot
WHERE extraction_week = (SELECT MAX(extraction_week) FROM rental_listings_snapshot)
GROUP BY property_type
ORDER BY total_listings DESC;