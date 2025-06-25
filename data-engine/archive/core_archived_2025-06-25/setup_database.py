#!/usr/bin/env python3
"""
Setup Calgary Analytica Database
Creates the SQLite database with tables for city-wide and district-level housing data
"""

import sqlite3
from pathlib import Path
import logging
import sys

# Add config to path
sys.path.append(str(Path(__file__).parent.parent.parent / "config"))
from config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    """Create the Calgary housing database with required tables."""
    
    # Use ConfigManager for database path
    config = ConfigManager()
    db_path = config.get_database_path()
    
    # Connect to database (creates if not exists)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create city-wide monthly data table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS housing_city_monthly (
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
    )
    """)
    
    # Create district-level monthly data table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS housing_district_monthly (
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
    )
    """)
    
    # Create extraction patterns table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS extraction_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT NOT NULL,
        pattern_type TEXT NOT NULL,
        pattern_config TEXT,  -- JSON string
        success_rate REAL,
        last_used TEXT,
        created_by TEXT,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create extraction log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS extraction_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pdf_file TEXT NOT NULL,
        extraction_type TEXT NOT NULL,  -- 'city' or 'district' or 'economic'
        status TEXT NOT NULL,  -- 'success', 'partial', 'failed'
        records_extracted INTEGER,
        confidence_score REAL,
        error_message TEXT,
        extracted_date TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create economic indicators monthly data table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS economic_indicators_monthly (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        indicator_type TEXT NOT NULL,  -- employment, gdp, population, inflation, etc.
        indicator_name TEXT,  -- specific metric name
        value REAL,
        unit TEXT,  -- percentage, thousands, millions, dollars
        yoy_change REAL,  -- year-over-year change
        mom_change REAL,  -- month-over-month change
        category TEXT,  -- labour, economy, housing, demographics
        source_file TEXT,
        extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
        confidence_score REAL DEFAULT 1.0,
        validation_status TEXT DEFAULT 'pending',
        UNIQUE(date, indicator_type, indicator_name)
    )
    """)
    
    # Create economic analysis summaries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS economic_analysis_quarterly (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quarter TEXT NOT NULL,
        year INTEGER NOT NULL,
        key_insights TEXT,  -- JSON array of key insights
        economic_outlook TEXT,  -- overall economic outlook
        housing_correlation TEXT,  -- housing market connections
        employment_trends TEXT,
        population_trends TEXT,
        source_pdf TEXT,
        extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
        confidence_score REAL DEFAULT 1.0,
        validation_status TEXT DEFAULT 'pending',
        UNIQUE(quarter, year)
    )
    """)
    
    # Create economic metadata tracking table  
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS economic_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file TEXT NOT NULL,
        file_type TEXT NOT NULL,  -- xlsx, pdf
        date_range_start TEXT,
        date_range_end TEXT,
        indicators_count INTEGER,
        processing_status TEXT DEFAULT 'pending',
        error_details TEXT,
        processed_date TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(source_file)
    )
    """)
    
    # Create crime statistics monthly data table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crime_statistics_monthly (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        community TEXT NOT NULL,  -- Calgary community/district name
        crime_category TEXT NOT NULL,  -- assault, theft, property, etc.
        crime_type TEXT,  -- specific crime subcategory
        incident_count INTEGER,  -- number of incidents
        rate_per_1000 REAL,  -- crime rate per 1000 residents
        severity_index REAL,  -- crime severity index if available
        population_base INTEGER,  -- community population for rate calculation
        source_file TEXT,
        extracted_date TEXT DEFAULT CURRENT_TIMESTAMP,
        confidence_score REAL DEFAULT 1.0,
        validation_status TEXT DEFAULT 'pending',
        UNIQUE(date, community, crime_category, crime_type)
    )
    """)
    
    # Create crime metadata and community information table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crime_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        community TEXT NOT NULL,
        district TEXT,  -- police district if different from community
        population_estimate INTEGER,
        area_km2 REAL,  -- community area for density calculations
        safety_rating REAL,  -- computed safety score (0-1)
        crime_density REAL,  -- crimes per km2
        housing_correlation REAL,  -- correlation with housing prices
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
        data_quality_score REAL DEFAULT 1.0,
        UNIQUE(community)
    )
    """)
    
    # Create crime analysis summaries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crime_analysis_monthly (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        community TEXT NOT NULL,
        total_incidents INTEGER,
        violent_crime_count INTEGER,
        property_crime_count INTEGER,
        disorder_count INTEGER,
        overall_severity REAL,
        safety_score REAL,  -- 0-1 safety rating
        crime_trend TEXT,  -- 'increasing', 'decreasing', 'stable'
        housing_impact_score REAL,  -- impact on housing desirability
        source_file TEXT,
        confidence_score REAL DEFAULT 1.0,
        validation_status TEXT DEFAULT 'pending',
        UNIQUE(date, community)
    )
    """)
    
    # Create indexes for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_city_date ON housing_city_monthly(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_city_property ON housing_city_monthly(property_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_district_date ON housing_district_monthly(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_district_property ON housing_district_monthly(property_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_district_name ON housing_district_monthly(district)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_economic_date ON economic_indicators_monthly(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_economic_type ON economic_indicators_monthly(indicator_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_economic_category ON economic_indicators_monthly(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_quarter ON economic_analysis_quarterly(quarter, year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crime_date ON crime_statistics_monthly(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crime_community ON crime_statistics_monthly(community)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crime_category ON crime_statistics_monthly(crime_category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crime_analysis_date ON crime_analysis_monthly(date, community)")
    
    # Create useful views
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS housing_city_validated AS
    SELECT * FROM housing_city_monthly 
    WHERE validation_status = 'approved'
    ORDER BY date DESC, property_type
    """)
    
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS housing_district_validated AS
    SELECT * FROM housing_district_monthly 
    WHERE validation_status = 'approved'
    ORDER BY date DESC, district, property_type
    """)
    
    # Create economic indicators views
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS economic_indicators_validated AS
    SELECT * FROM economic_indicators_monthly 
    WHERE validation_status = 'approved'
    ORDER BY date DESC, category, indicator_type
    """)
    
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS economic_analysis_validated AS
    SELECT * FROM economic_analysis_quarterly 
    WHERE validation_status = 'approved'
    ORDER BY year DESC, quarter DESC
    """)
    
    # Create crime statistics views
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS crime_statistics_validated AS
    SELECT * FROM crime_statistics_monthly 
    WHERE validation_status = 'approved'
    ORDER BY date DESC, community, crime_category
    """)
    
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS crime_analysis_validated AS
    SELECT * FROM crime_analysis_monthly 
    WHERE validation_status = 'approved'
    ORDER BY date DESC, safety_score DESC
    """)
    
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS community_safety_summary AS
    SELECT 
        c.community,
        c.safety_rating,
        c.crime_density,
        c.housing_correlation,
        COUNT(s.id) as months_reported,
        AVG(s.total_incidents) as avg_monthly_incidents,
        AVG(s.safety_score) as avg_safety_score
    FROM crime_metadata c
    LEFT JOIN crime_analysis_monthly s ON c.community = s.community
    WHERE s.validation_status = 'approved' OR s.validation_status IS NULL
    GROUP BY c.community
    ORDER BY c.safety_rating DESC
    """)
    
    # Create a summary view
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS data_coverage_summary AS
    SELECT 
        'City-wide Housing' as dataset,
        COUNT(DISTINCT date) as months_covered,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_records
    FROM housing_city_monthly
    WHERE validation_status = 'approved'
    UNION ALL
    SELECT 
        'District-level Housing' as dataset,
        COUNT(DISTINCT date) as months_covered,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_records
    FROM housing_district_monthly
    WHERE validation_status = 'approved'
    UNION ALL
    SELECT 
        'Economic Indicators' as dataset,
        COUNT(DISTINCT date) as months_covered,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_records
    FROM economic_indicators_monthly
    WHERE validation_status = 'approved'
    UNION ALL
    SELECT 
        'Economic Analysis' as dataset,
        COUNT(DISTINCT CONCAT(year, '-Q', quarter)) as quarters_covered,
        MIN(CONCAT(year, '-Q', quarter)) as earliest_quarter,
        MAX(CONCAT(year, '-Q', quarter)) as latest_quarter,
        COUNT(*) as total_records
    FROM economic_analysis_quarterly
    WHERE validation_status = 'approved'
    UNION ALL
    SELECT 
        'Crime Statistics' as dataset,
        COUNT(DISTINCT date) as months_covered,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_records
    FROM crime_statistics_monthly
    WHERE validation_status = 'approved'
    UNION ALL
    SELECT 
        'Community Safety Analysis' as dataset,
        COUNT(DISTINCT date) as months_covered,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        COUNT(*) as total_records
    FROM crime_analysis_monthly
    WHERE validation_status = 'approved'
    """)
    
    conn.commit()
    
    logger.info(f"Database created successfully at: {db_path}")
    
    # Log table creation
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    logger.info(f"Created tables: {[t[0] for t in tables]}")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = cursor.fetchall()
    logger.info(f"Created views: {[v[0] for v in views]}")
    
    conn.close()
    
    return db_path

if __name__ == "__main__":
    db_path = create_database()
    print(f"✅ Calgary Analytica database created at: {db_path}")
    print("\nTables created:")
    print("  - housing_city_monthly (city-wide aggregates)")
    print("  - housing_district_monthly (district-level detail)")
    print("  - economic_indicators_monthly (economic metrics)")
    print("  - economic_analysis_quarterly (economic analysis)")
    print("  - economic_metadata (source tracking)")
    print("  - crime_statistics_monthly (community crime data)")
    print("  - crime_analysis_monthly (community safety analysis)")
    print("  - crime_metadata (community safety profiles)")
    print("  - extraction_patterns (successful extraction methods)")
    print("  - extraction_log (extraction history and metrics)")
    print("\nViews created:")
    print("  - housing_city_validated (approved city data)")
    print("  - housing_district_validated (approved district data)")
    print("  - economic_indicators_validated (approved economic data)")
    print("  - economic_analysis_validated (approved economic analysis)")
    print("  - crime_statistics_validated (approved crime data)")
    print("  - crime_analysis_validated (approved safety analysis)")
    print("  - community_safety_summary (community safety profiles)")
    print("  - data_coverage_summary (coverage statistics)")