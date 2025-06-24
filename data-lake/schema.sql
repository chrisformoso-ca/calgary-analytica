CREATE TABLE housing_city_monthly (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        property_type TEXT NOT NULL,
        sales INTEGER,
        new_listings INTEGER,
        inventory INTEGER,
        days_on_market INTEGER,
        benchmark_price INTEGER,
        median_price INTEGER,
        average_price INTEGER,
        source_pdf TEXT,
        extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
        confidence_score REAL DEFAULT 1.0,
        validation_status TEXT DEFAULT 'pending',
        UNIQUE(date, property_type)
    );
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE housing_district_monthly (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        property_type TEXT NOT NULL,
        district TEXT NOT NULL,
        new_sales INTEGER,
        new_listings INTEGER,
        sales_to_listings_ratio TEXT,
        inventory INTEGER,
        months_supply REAL,
        benchmark_price INTEGER,
        yoy_price_change REAL,
        mom_price_change REAL,
        source_pdf TEXT,
        extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
        confidence_score REAL DEFAULT 1.0,
        validation_status TEXT DEFAULT 'pending',
        UNIQUE(date, property_type, district)
    );
CREATE TABLE extraction_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT NOT NULL,
        pattern_type TEXT NOT NULL,
        pattern_config TEXT,  -- JSON string
        success_rate REAL,
        last_used TEXT,
        created_by TEXT,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP
    );
CREATE TABLE extraction_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pdf_file TEXT NOT NULL,
        extraction_type TEXT NOT NULL,  -- 'city' or 'district'
        status TEXT NOT NULL,  -- 'success', 'partial', 'failed'
        records_extracted INTEGER,
        confidence_score REAL,
        error_message TEXT,
        extracted_date TEXT DEFAULT CURRENT_TIMESTAMP
    );
CREATE INDEX idx_city_date ON housing_city_monthly(date);
CREATE INDEX idx_city_property ON housing_city_monthly(property_type);
CREATE INDEX idx_district_date ON housing_district_monthly(date);
CREATE INDEX idx_district_property ON housing_district_monthly(property_type);
CREATE INDEX idx_district_name ON housing_district_monthly(district);
CREATE VIEW housing_city_validated AS
    SELECT * FROM housing_city_monthly 
    WHERE validation_status = 'approved'
    ORDER BY date DESC, property_type
/* housing_city_validated(id,date,property_type,sales,new_listings,inventory,days_on_market,benchmark_price,median_price,average_price,source_pdf,extracted_date,confidence_score,validation_status) */;
CREATE VIEW housing_district_validated AS
    SELECT * FROM housing_district_monthly 
    WHERE validation_status = 'approved'
    ORDER BY date DESC, district, property_type
/* housing_district_validated(id,date,property_type,district,new_sales,new_listings,sales_to_listings_ratio,inventory,months_supply,benchmark_price,yoy_price_change,mom_price_change,source_pdf,extracted_date,confidence_score,validation_status) */;
CREATE VIEW data_coverage_summary AS
    SELECT 
        'City-wide' as dataset,
        COUNT(DISTINCT date) as months_covered,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_records
    FROM housing_city_monthly
    WHERE validation_status = 'approved'
    UNION ALL
    SELECT 
        'District-level' as dataset,
        COUNT(DISTINCT date) as months_covered,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_records
    FROM housing_district_monthly
    WHERE validation_status = 'approved'
/* data_coverage_summary(dataset,months_covered,earliest_date,latest_date,total_records) */;
CREATE TABLE crime_statistics_monthly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    community TEXT NOT NULL,
    crime_category TEXT NOT NULL,
    crime_type TEXT,
    incident_count INTEGER,
    rate_per_1000 REAL,
    severity_index REAL,
    population_base INTEGER,
    source_file TEXT,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL DEFAULT 1.0,
    validation_status TEXT DEFAULT 'pending',
    UNIQUE(date, community, crime_category, crime_type)
);
CREATE TABLE crime_analysis_monthly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    community TEXT NOT NULL,
    total_incidents INTEGER,
    violent_crime_count INTEGER,
    property_crime_count INTEGER,
    disorder_count INTEGER,
    overall_severity REAL,
    safety_score REAL,
    crime_trend TEXT,
    housing_impact_score REAL,
    source_file TEXT,
    confidence_score REAL DEFAULT 1.0,
    validation_status TEXT DEFAULT 'pending',
    UNIQUE(date, community)
);
CREATE TABLE housing_crime_correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_date TEXT NOT NULL,
                analysis_window TEXT NOT NULL,
                housing_metric TEXT NOT NULL,
                crime_metric TEXT NOT NULL,
                pearson_correlation REAL,
                pearson_p_value REAL,
                spearman_correlation REAL,
                spearman_p_value REAL,
                sample_size INTEGER,
                interpretation TEXT,
                data_start_date TEXT,
                data_end_date TEXT,
                confidence_score REAL DEFAULT 1.0,
                UNIQUE(analysis_date, analysis_window, housing_metric, crime_metric)
            );
CREATE TABLE housing_crime_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_date TEXT NOT NULL,
                insight_text TEXT NOT NULL,
                insight_category TEXT DEFAULT 'correlation',
                confidence_score REAL DEFAULT 1.0,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE economic_indicators_monthly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    indicator_type TEXT NOT NULL,
    indicator_name TEXT,
    value REAL,
    unit TEXT,
    yoy_change REAL,
    mom_change REAL,
    category TEXT,
    source_file TEXT,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL DEFAULT 1.0,
    validation_status TEXT DEFAULT 'pending', value_type TEXT,
    UNIQUE(date, indicator_type, indicator_name)
);
CREATE TABLE economic_analysis_quarterly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quarter TEXT NOT NULL,
    year INTEGER NOT NULL,
    key_insights TEXT,
    economic_outlook TEXT,
    housing_correlation TEXT,
    employment_trends TEXT,
    population_trends TEXT,
    source_pdf TEXT,
    extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL DEFAULT 1.0,
    validation_status TEXT DEFAULT 'pending',
    UNIQUE(quarter, year)
);
CREATE TABLE economic_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    file_type TEXT NOT NULL,
    date_range_start TEXT,
    date_range_end TEXT,
    indicators_count INTEGER,
    processing_status TEXT DEFAULT 'pending',
    error_details TEXT,
    processed_date TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_file)
);
CREATE INDEX idx_economic_value_type ON economic_indicators_monthly(value_type);
