-- Migration: Add value_type column to economic_indicators_monthly
-- Purpose: Distinguish between absolute values, rates, and changes
-- Date: 2025-06-23

-- Check if column already exists before adding
-- SQLite doesn't support IF NOT EXISTS for columns, so we use a workaround

-- Add the value_type column
ALTER TABLE economic_indicators_monthly ADD COLUMN value_type TEXT;

-- Update existing records based on indicator patterns
-- This is a best-effort categorization of existing data
UPDATE economic_indicators_monthly
SET value_type = CASE
    -- Rates (percentages that represent current state)
    WHEN indicator_type LIKE '%rate%' AND indicator_type NOT LIKE '%change%' THEN 'rate'
    WHEN indicator_type LIKE '%ratio%' THEN 'rate'
    
    -- Year-over-year or month-over-month changes
    WHEN indicator_name LIKE '%y/y%' OR indicator_name LIKE '%yoy%' THEN 'yoy_change'
    WHEN indicator_name LIKE '%m/m%' OR indicator_name LIKE '%mom%' THEN 'mom_change'
    WHEN indicator_name LIKE '%change%' THEN 'yoy_change'
    
    -- Everything else is absolute values
    ELSE 'absolute'
END
WHERE value_type IS NULL;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_economic_value_type ON economic_indicators_monthly(value_type);

-- Show summary of updates
SELECT 
    value_type,
    COUNT(*) as record_count,
    COUNT(DISTINCT indicator_type) as unique_indicators
FROM economic_indicators_monthly
GROUP BY value_type
ORDER BY value_type;