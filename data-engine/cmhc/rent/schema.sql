-- CMHC Rental Market Annual Data Schema
-- This table stores annual rental market data from CMHC reports
-- Data is captured in October of each year

CREATE TABLE IF NOT EXISTS rental_market_annual (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Temporal fields
    date TEXT NOT NULL,              -- Always YYYY-10-01 (October snapshot)
    year INTEGER NOT NULL,           -- Year of the data
    
    -- Property categorization
    property_type TEXT NOT NULL,     -- 'apartment', 'townhouse', 'all_types', 'rental_condo', 'apartment_comparison'
    
    -- Rental metrics
    metric_type TEXT NOT NULL,       -- 'vacancy_rate', 'average_rent', 'rental_universe'
    bedroom_type TEXT NOT NULL,      -- 'Bachelor', '1 Bedroom', '2 Bedroom', '3 Bedroom+', 'Total'
    value REAL,                      -- The metric value (percent for vacancy, dollars for rent, count for universe)
    unit TEXT NOT NULL,              -- 'percent', 'dollars', 'units'
    quality_indicator TEXT,          -- CMHC quality rating: 'a', 'b', 'c', 'd'
    
    -- Metadata fields
    validation_status TEXT DEFAULT 'pending',
    
    -- Constraints
    CHECK (property_type IN ('apartment', 'townhouse', 'all_types', 'rental_condo', 'apartment_comparison')),
    CHECK (metric_type IN ('vacancy_rate', 'average_rent', 'rental_universe')),
    CHECK (bedroom_type IN ('Bachelor', '1 Bedroom', '2 Bedroom', '3 Bedroom+', 'Total')),
    CHECK (quality_indicator IN ('a', 'b', 'c', 'd') OR quality_indicator IS NULL),
    CHECK (validation_status IN ('pending', 'approved', 'rejected'))
);

-- Indexes for common queries
CREATE INDEX idx_rental_year ON rental_market_annual(year);
CREATE INDEX idx_rental_metric ON rental_market_annual(metric_type);
CREATE INDEX idx_rental_bedroom ON rental_market_annual(bedroom_type);
CREATE INDEX idx_rental_property ON rental_market_annual(property_type);
CREATE INDEX idx_rental_date ON rental_market_annual(date);

-- Unique constraint to prevent duplicates
CREATE UNIQUE INDEX idx_rental_unique ON rental_market_annual(date, property_type, metric_type, bedroom_type);

-- View for latest rental data by bedroom and property type
CREATE VIEW latest_rental_metrics AS
SELECT 
    property_type,
    bedroom_type,
    MAX(CASE WHEN metric_type = 'vacancy_rate' THEN value END) as vacancy_rate,
    MAX(CASE WHEN metric_type = 'average_rent' THEN value END) as average_rent,
    MAX(CASE WHEN metric_type = 'rental_universe' THEN value END) as rental_units,
    MAX(year) as latest_year
FROM rental_market_annual
WHERE validation_status = 'approved'
GROUP BY property_type, bedroom_type;

-- View for rental trends over time
CREATE VIEW rental_trends AS
SELECT 
    year,
    property_type,
    bedroom_type,
    metric_type,
    value,
    quality_indicator
FROM rental_market_annual
WHERE validation_status = 'approved'
ORDER BY year, property_type, bedroom_type, metric_type;