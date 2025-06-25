-- Calgary Data Lake - Data Dictionary Generator
-- Run: sqlite3 calgary_data.db < data_dictionary.sql

.mode list
.separator ""

-- Header
SELECT '=================================================';
SELECT '       CALGARY DATA LAKE - DATA DICTIONARY';
SELECT '       Generated: ' || datetime('now', 'localtime');
SELECT '=================================================';
SELECT '';

-- Metadata Summary
SELECT 'METADATA SUMMARY';
SELECT '================';
SELECT 'Database Size: ' || ROUND(page_count * page_size / 1024.0 / 1024.0, 2) || ' MB' FROM pragma_page_count(), pragma_page_size();
SELECT 'Total Tables: ' || COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%';
SELECT 'Total Records: ' || (
    SELECT SUM(cnt) FROM (
        SELECT COUNT(*) as cnt FROM housing_city_monthly
        UNION ALL SELECT COUNT(*) FROM housing_district_monthly
        UNION ALL SELECT COUNT(*) FROM economic_indicators_monthly
        UNION ALL SELECT COUNT(*) FROM crime_statistics_monthly
    )
) || ' records';
SELECT '';

-- Last Updates
SELECT 'LAST DATA UPDATES';
SELECT '=================';
SELECT 'Housing City: ' || MAX(date) || ' (loaded ' || DATE(MAX(extracted_date)) || ')' FROM housing_city_monthly;
SELECT 'Housing District: ' || MAX(date) || ' (loaded ' || DATE(MAX(extracted_date)) || ')' FROM housing_district_monthly;
SELECT 'Economic: ' || MAX(date) || ' (loaded ' || DATE(MAX(extracted_date)) || ')' FROM economic_indicators_monthly;
SELECT 'Crime: ' || MAX(date) || ' (loaded ' || DATE(MAX(extracted_date)) || ')' FROM crime_statistics_monthly;
SELECT '';
SELECT '';

-- 1. TABLE OVERVIEW
SELECT '1. TABLE OVERVIEW';
SELECT '=================';
SELECT '';

.mode column
.headers on
.width 30 15 25

SELECT 
    'housing_city_monthly' as table_name,
    COUNT(*) || ' records' as record_count,
    MIN(date) || ' to ' || MAX(date) as date_range
FROM housing_city_monthly
UNION ALL
SELECT 
    'housing_district_monthly',
    COUNT(*) || ' records',
    MIN(date) || ' to ' || MAX(date)
FROM housing_district_monthly
UNION ALL
SELECT 
    'economic_indicators_monthly',
    COUNT(*) || ' records',
    MIN(date) || ' to ' || MAX(date)
FROM economic_indicators_monthly
UNION ALL
SELECT 
    'crime_statistics_monthly',
    COUNT(*) || ' records',
    MIN(date) || ' to ' || MAX(date)
FROM crime_statistics_monthly;

.mode list
.headers off
SELECT '';
SELECT '';

-- 2. SCHEMA DETAILS
SELECT '2. SCHEMA DETAILS';
SELECT '=================';
SELECT '';

-- Housing City Monthly
SELECT 'HOUSING_CITY_MONTHLY';
SELECT '--------------------';
SELECT 'Fields: id, date, property_type, sales, new_listings, inventory,';
SELECT '        days_on_market, benchmark_price, median_price, average_price,';
SELECT '        source_pdf, extracted_date, confidence_score, validation_status';
SELECT '';
SELECT 'Property Types:';

.mode column
.headers on
.width 20 10

SELECT property_type, COUNT(*) as records
FROM housing_city_monthly
GROUP BY property_type
ORDER BY property_type;

.mode list
.headers off
SELECT '';
SELECT 'Date Coverage: ' || COUNT(DISTINCT date) || ' unique months'
FROM housing_city_monthly;
SELECT '';
SELECT '';

-- Housing District Monthly
SELECT 'HOUSING_DISTRICT_MONTHLY';
SELECT '------------------------';
SELECT 'Fields: id, date, property_type, district, new_sales, new_listings,';
SELECT '        sales_to_listings_ratio, inventory, months_supply, benchmark_price,';
SELECT '        yoy_price_change, mom_price_change, source_pdf, extracted_date,';
SELECT '        confidence_score, validation_status';
SELECT '';
SELECT 'Districts:';

.mode column
.headers on
.width 15 10

SELECT district, COUNT(*) as records
FROM housing_district_monthly
GROUP BY district
ORDER BY district;

.mode list
.headers off
SELECT '';
SELECT 'Property Types by District:';

.mode column
.headers on
.width 15 20 10

SELECT district, property_type, COUNT(*) as records
FROM housing_district_monthly
GROUP BY district, property_type
ORDER BY district, property_type
LIMIT 20; -- Showing first 20 for readability

.mode list
.headers off
SELECT '';
SELECT '';

-- Economic Indicators Monthly
SELECT 'ECONOMIC_INDICATORS_MONTHLY';
SELECT '---------------------------';
SELECT 'Fields: id, date, indicator_name, value, unit, source_file,';
SELECT '        extracted_date, confidence_score, validation_status';
SELECT '';
SELECT 'Indicators Tracked:';

.mode column
.headers on
.width 35 10 25

SELECT 
    indicator_name, 
    COUNT(*) as records,
    MIN(date) || ' to ' || MAX(date) as date_range
FROM economic_indicators_monthly
GROUP BY indicator_name
ORDER BY indicator_name;

.mode list
.headers off
SELECT '';
SELECT '';

-- Crime Statistics Monthly
SELECT 'CRIME_STATISTICS_MONTHLY';
SELECT '------------------------';
SELECT 'Fields: id, date, year, community, ward, police_district,';
SELECT '        crime_category, crime_type, incident_count, source_file,';
SELECT '        extracted_date, confidence_score, validation_status';
SELECT '';
SELECT '';

-- 3. DATA DISTRIBUTIONS
SELECT '3. DATA DISTRIBUTIONS';
SELECT '=====================';
SELECT '';

-- Crime by Category
SELECT 'CRIME STATISTICS - By Category';
SELECT '------------------------------';

.mode column
.headers on
.width 15 15 20

SELECT 
    crime_category,
    COUNT(*) as total_records,
    COUNT(DISTINCT community) as communities
FROM crime_statistics_monthly
GROUP BY crime_category
ORDER BY COUNT(*) DESC;

.mode list
.headers off
SELECT '';

-- Crime by Year
SELECT 'CRIME STATISTICS - By Year';
SELECT '--------------------------';

.mode column
.headers on
.width 10 15

SELECT 
    year,
    COUNT(*) as records
FROM crime_statistics_monthly
GROUP BY year
ORDER BY year;

.mode list
.headers off
SELECT '';

-- Top 10 Communities by Crime Records
SELECT 'CRIME STATISTICS - Top 10 Communities by Record Count';
SELECT '----------------------------------------------------';

.mode column
.headers on
.width 25 15

SELECT 
    community,
    COUNT(*) as records
FROM crime_statistics_monthly
GROUP BY community
ORDER BY COUNT(*) DESC
LIMIT 10;

.mode list
.headers off
SELECT '';
SELECT '';

-- 4. GEOGRAPHIC COVERAGE
SELECT '4. GEOGRAPHIC COVERAGE';
SELECT '======================';
SELECT '';

SELECT 'Housing Districts: ' || COUNT(DISTINCT district) || ' districts'
FROM housing_district_monthly;

SELECT 'Crime Communities: ' || COUNT(DISTINCT community) || ' communities (including UNKNOWN)'
FROM crime_statistics_monthly;

SELECT 'Economic Scope: City-wide aggregates';
SELECT '';

-- List all districts
SELECT 'Housing Districts:';

.mode column
.headers on
.width 15

SELECT DISTINCT district
FROM housing_district_monthly
ORDER BY district;

.mode list
.headers off
SELECT '';
SELECT '';

-- 5. TEMPORAL ALIGNMENT
SELECT '5. TEMPORAL ALIGNMENT';
SELECT '=====================';
SELECT '';

SELECT 'Data Availability Overview (Recent 24 months):';
SELECT '';

.mode column
.headers on
.width 10 10 10 10 10

WITH all_dates AS (
    SELECT DISTINCT substr(date, 1, 7) as year_month FROM housing_city_monthly
    UNION
    SELECT DISTINCT substr(date, 1, 7) FROM housing_district_monthly
    UNION
    SELECT DISTINCT substr(date, 1, 7) FROM economic_indicators_monthly
    UNION
    SELECT DISTINCT substr(date, 1, 7) FROM crime_statistics_monthly
    ORDER BY year_month DESC
    LIMIT 24
),
coverage AS (
    SELECT 
        ad.year_month,
        CASE WHEN hc.cnt > 0 THEN 'Yes' ELSE 'No' END as housing_city,
        CASE WHEN hd.cnt > 0 THEN 'Yes' ELSE 'No' END as housing_dist,
        CASE WHEN ei.cnt > 0 THEN 'Yes' ELSE 'No' END as economic,
        CASE WHEN cs.cnt > 0 THEN 'Yes' ELSE 'No' END as crime
    FROM all_dates ad
    LEFT JOIN (SELECT substr(date, 1, 7) as ym, COUNT(*) as cnt FROM housing_city_monthly GROUP BY ym) hc ON ad.year_month = hc.ym
    LEFT JOIN (SELECT substr(date, 1, 7) as ym, COUNT(*) as cnt FROM housing_district_monthly GROUP BY ym) hd ON ad.year_month = hd.ym
    LEFT JOIN (SELECT substr(date, 1, 7) as ym, COUNT(*) as cnt FROM economic_indicators_monthly GROUP BY ym) ei ON ad.year_month = ei.ym
    LEFT JOIN (SELECT substr(date, 1, 7) as ym, COUNT(*) as cnt FROM crime_statistics_monthly GROUP BY ym) cs ON ad.year_month = cs.ym
)
SELECT * FROM coverage
ORDER BY year_month DESC;

.mode list
.headers off
SELECT '';

WITH overlap AS (
    SELECT substr(date, 1, 7) as year_month FROM housing_city_monthly
    INTERSECT
    SELECT substr(date, 1, 7) FROM economic_indicators_monthly
    INTERSECT
    SELECT substr(date, 1, 7) FROM crime_statistics_monthly
)
SELECT 'Full Overlap Period: ' || MIN(year_month) || ' to ' || MAX(year_month) FROM overlap;

SELECT '';
SELECT '';

-- 6. SAMPLE QUERIES
SELECT '6. SAMPLE QUERIES FOR ANALYSIS';
SELECT '==============================';
SELECT '';
SELECT '-- Housing price trends by property type';
SELECT 'SELECT date, property_type, benchmark_price FROM housing_city_monthly ORDER BY date, property_type;';
SELECT '';
SELECT '-- Crime trends by category over time';
SELECT 'SELECT year, crime_category, SUM(incident_count) FROM crime_statistics_monthly GROUP BY year, crime_category;';
SELECT '';
SELECT '-- Economic indicators latest values';
SELECT 'SELECT indicator_name, value, date FROM economic_indicators_monthly WHERE date = (SELECT MAX(date) FROM economic_indicators_monthly);';
SELECT '';
SELECT '-- District housing comparison';
SELECT 'SELECT district, AVG(benchmark_price) as avg_price FROM housing_district_monthly WHERE property_type = ''total'' GROUP BY district;';
SELECT '';

-- Footer
SELECT '=================================================';
SELECT 'End of Data Dictionary';
SELECT '=================================================';
SELECT '';
SELECT 'To update metadata: /project:metadata';