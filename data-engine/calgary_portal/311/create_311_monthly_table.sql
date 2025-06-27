-- Create table for 311 monthly summaries with housing and economic indicators

CREATE TABLE IF NOT EXISTS service_requests_311_monthly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month TEXT NOT NULL,           -- '2024-06' format
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    community_code TEXT NOT NULL,
    community_name TEXT,
    service_category TEXT NOT NULL,     -- Our defined categories
    total_requests INTEGER NOT NULL,
    open_requests INTEGER,
    closed_requests INTEGER,
    avg_days_to_close REAL,
    median_days_to_close REAL,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL DEFAULT 1.0,
    validation_status TEXT DEFAULT 'pending',
    UNIQUE(year_month, community_code, service_category)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_311_monthly_date ON service_requests_311_monthly(year_month);
CREATE INDEX IF NOT EXISTS idx_311_monthly_year ON service_requests_311_monthly(year);
CREATE INDEX IF NOT EXISTS idx_311_monthly_community ON service_requests_311_monthly(community_code);
CREATE INDEX IF NOT EXISTS idx_311_monthly_category ON service_requests_311_monthly(service_category);

-- Create a view for economic indicators
CREATE VIEW IF NOT EXISTS economic_indicators_311 AS
SELECT 
    year_month,
    -- Encampment indicators
    SUM(CASE WHEN service_category = 'Encampments' THEN total_requests ELSE 0 END) as encampment_reports,
    -- Property distress
    SUM(CASE WHEN service_category = 'Derelict Properties' THEN total_requests ELSE 0 END) as derelict_properties,
    -- Infrastructure stress
    SUM(CASE WHEN service_category = 'Infrastructure' THEN total_requests ELSE 0 END) as infrastructure_issues,
    AVG(CASE WHEN service_category = 'Infrastructure' THEN avg_days_to_close ELSE NULL END) as infrastructure_response_days,
    -- Social stress
    SUM(CASE WHEN service_category = 'Social Stress' THEN total_requests ELSE 0 END) as social_stress_reports,
    -- Overall service demand
    SUM(total_requests) as total_311_requests,
    COUNT(DISTINCT community_code) as communities_reporting
FROM service_requests_311_monthly
WHERE validation_status = 'approved'
GROUP BY year_month;

-- Create a view for community stress scores
CREATE VIEW IF NOT EXISTS community_stress_scores AS
SELECT 
    community_code,
    community_name,
    year_month,
    -- Calculate stress score based on various factors
    (
        SUM(CASE WHEN service_category = 'Encampments' THEN total_requests * 3 ELSE 0 END) +
        SUM(CASE WHEN service_category = 'Derelict Properties' THEN total_requests * 2.5 ELSE 0 END) +
        SUM(CASE WHEN service_category = 'Graffiti' THEN total_requests * 2 ELSE 0 END) +
        SUM(CASE WHEN service_category = 'Bylaw' THEN total_requests * 1.5 ELSE 0 END) +
        SUM(CASE WHEN service_category = 'Social Stress' THEN total_requests * 1.5 ELSE 0 END) +
        SUM(CASE WHEN service_category = 'Infrastructure' THEN total_requests * 1 ELSE 0 END)
    ) as stress_score,
    SUM(total_requests) as total_issues,
    COUNT(DISTINCT service_category) as category_diversity
FROM service_requests_311_monthly
WHERE validation_status = 'approved'
GROUP BY community_code, community_name, year_month;