-- Create tables for Calgary Portal data

-- 311 Service Requests
CREATE TABLE IF NOT EXISTS service_requests_311 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_request_id TEXT NOT NULL,
    date TEXT NOT NULL,
    updated_date TEXT,
    closed_date TEXT,
    status_description TEXT,
    source TEXT,
    service_name TEXT NOT NULL,
    agency_responsible TEXT,
    address TEXT,
    community_code TEXT,
    community_name TEXT,
    longitude REAL,
    latitude REAL,
    year INTEGER,
    month INTEGER,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL DEFAULT 1.0,
    validation_status TEXT DEFAULT 'pending',
    UNIQUE(service_request_id)
);

-- Building Permits
CREATE TABLE IF NOT EXISTS building_permits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permit_number TEXT NOT NULL,
    status_current TEXT,
    applied_date TEXT NOT NULL,
    issued_date TEXT,
    completed_date TEXT,
    permit_type TEXT NOT NULL,
    permit_class TEXT,
    work_class TEXT NOT NULL,
    description TEXT,
    applicant_name TEXT,
    estimated_project_cost REAL,
    total_sqft REAL,
    housing_units INTEGER,
    community_code TEXT,
    community_name TEXT,
    original_address TEXT,
    latitude REAL,
    longitude REAL,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL DEFAULT 1.0,
    validation_status TEXT DEFAULT 'pending',
    UNIQUE(permit_number)
);

-- Business Licences
CREATE TABLE IF NOT EXISTS business_licences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    licence_number TEXT NOT NULL,
    business_name TEXT NOT NULL,
    licence_type TEXT NOT NULL,
    business_type TEXT,
    business_category TEXT,
    address TEXT,
    issue_date TEXT NOT NULL,
    expiry_date TEXT,
    latitude REAL,
    longitude REAL,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL DEFAULT 1.0,
    validation_status TEXT DEFAULT 'pending',
    UNIQUE(licence_number)
);

-- Community Boundaries (Geospatial)
CREATE TABLE IF NOT EXISTS community_boundaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    community_code TEXT NOT NULL,
    name TEXT NOT NULL,
    community_class TEXT,
    class_code TEXT,
    community_sector TEXT,
    area_hectares REAL,
    res_units INTEGER,
    multipolygon TEXT,  -- GeoJSON stored as text
    dataset TEXT,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(community_code)
);

-- Community Districts (Geospatial)
CREATE TABLE IF NOT EXISTS community_districts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    area_hectares REAL,
    multipolygon TEXT,  -- GeoJSON stored as text
    dataset TEXT,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code)
);

-- Community Sectors (Geospatial)
CREATE TABLE IF NOT EXISTS community_sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    multipolygon TEXT,  -- GeoJSON stored as text
    dataset TEXT,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_311_date ON service_requests_311(date);
CREATE INDEX IF NOT EXISTS idx_311_community ON service_requests_311(community_code);
CREATE INDEX IF NOT EXISTS idx_311_service ON service_requests_311(service_name);
CREATE INDEX IF NOT EXISTS idx_311_status ON service_requests_311(status_description);

CREATE INDEX IF NOT EXISTS idx_permits_date ON building_permits(applied_date);
CREATE INDEX IF NOT EXISTS idx_permits_community ON building_permits(community_code);
CREATE INDEX IF NOT EXISTS idx_permits_type ON building_permits(permit_type);

CREATE INDEX IF NOT EXISTS idx_business_type ON business_licences(licence_type);
CREATE INDEX IF NOT EXISTS idx_business_expiry ON business_licences(expiry_date);