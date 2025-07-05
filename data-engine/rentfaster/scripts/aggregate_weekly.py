#!/usr/bin/env python3
"""
RentFaster Weekly Aggregation Script
Aggregates rental listings snapshots into weekly summaries for trend analysis
"""

import sqlite3
import pandas as pd
from pathlib import Path
import logging
import sys
from datetime import datetime
import json

# Add project root for config
sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.config_manager import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RentfasterAggregator:
    """Aggregate weekly rental snapshots into summary statistics."""
    
    def __init__(self):
        self.config = get_config()
        self.db_path = self.config.get_database_path()
        self.conn = sqlite3.connect(self.db_path)
        
    def get_unprocessed_weeks(self):
        """Find weeks in rental_listings_snapshot that aren't in summary table."""
        query = """
        SELECT DISTINCT extraction_week 
        FROM rental_listings_snapshot
        WHERE extraction_week NOT IN (
            SELECT DISTINCT week FROM rental_market_summary_weekly
        )
        ORDER BY extraction_week
        """
        return pd.read_sql_query(query, self.conn)['extraction_week'].tolist()
    
    def aggregate_week(self, week):
        """Create aggregated summary for a specific week."""
        logger.info(f"📊 Aggregating data for week {week}")
        
        # Get all listings for this week
        query = """
        SELECT * FROM rental_listings_snapshot
        WHERE extraction_week = ?
        """
        df = pd.read_sql_query(query, self.conn, params=[week])
        
        if df.empty:
            logger.warning(f"No data found for week {week}")
            return []
        
        # Create aggregations by property type and bedrooms
        aggregations = []
        
        # First, aggregate by property type only
        for prop_type in df['property_type'].unique():
            prop_df = df[df['property_type'] == prop_type]
            
            # Overall stats for this property type
            agg = {
                'week': week,
                'property_type': prop_type,
                'bedrooms': None,  # NULL for overall
                'listing_count': len(prop_df),
                'avg_rent': round(prop_df['rent'].mean(), 2),
                'median_rent': int(prop_df['rent'].median()),
                'min_rent': int(prop_df['rent'].min()),
                'max_rent': int(prop_df['rent'].max()),
                'avg_sq_feet': round(prop_df['sq_feet'].mean(), 2) if prop_df['sq_feet'].notna().any() else None,
                'top_communities': json.dumps(
                    prop_df['community'].value_counts().head(5).to_dict()
                )
            }
            aggregations.append(agg)
            
            # Then aggregate by bedroom count within property type
            for bedrooms in prop_df['bedrooms'].unique():
                if pd.notna(bedrooms):  # Skip null bedrooms
                    bed_df = prop_df[prop_df['bedrooms'] == bedrooms]
                    
                    agg = {
                        'week': week,
                        'property_type': prop_type,
                        'bedrooms': int(bedrooms),
                        'listing_count': len(bed_df),
                        'avg_rent': round(bed_df['rent'].mean(), 2),
                        'median_rent': int(bed_df['rent'].median()),
                        'min_rent': int(bed_df['rent'].min()),
                        'max_rent': int(bed_df['rent'].max()),
                        'avg_sq_feet': round(bed_df['sq_feet'].mean(), 2) if bed_df['sq_feet'].notna().any() else None,
                        'top_communities': json.dumps(
                            bed_df['community'].value_counts().head(5).to_dict()
                        )
                    }
                    aggregations.append(agg)
        
        logger.info(f"  Created {len(aggregations)} aggregated records")
        return aggregations
    
    def save_aggregations(self, aggregations):
        """Save aggregated data to rental_market_summary_weekly table."""
        if not aggregations:
            return
        
        df = pd.DataFrame(aggregations)
        
        # Convert bedrooms to integer where not null
        df['bedrooms'] = df['bedrooms'].where(pd.notna(df['bedrooms']), None)
        
        # Save to database
        df.to_sql('rental_market_summary_weekly', self.conn, 
                  if_exists='append', index=False)
        self.conn.commit()
        
        logger.info(f"✅ Saved {len(aggregations)} records to rental_market_summary_weekly")
    
    def generate_market_insights(self, week):
        """Generate insights comparing current week to previous weeks."""
        logger.info(f"📈 Generating market insights for {week}")
        
        # Get last 4 weeks of data for comparison
        query = """
        SELECT * FROM rental_market_summary_weekly
        WHERE week <= ?
        AND bedrooms IS NULL  -- Overall stats only
        ORDER BY week DESC
        LIMIT 4
        """
        df = pd.read_sql_query(query, self.conn, params=[week])
        
        if len(df) < 2:
            logger.info("  Not enough historical data for insights")
            return
        
        current_week = df.iloc[0]
        previous_week = df.iloc[1]
        
        insights = []
        
        # Overall market movement
        total_listings_current = df[df['week'] == week]['listing_count'].sum()
        total_listings_previous = df[df['week'] == previous_week['week']]['listing_count'].sum()
        
        change_pct = ((total_listings_current - total_listings_previous) / total_listings_previous * 100)
        insights.append(f"Total listings: {total_listings_current:,} ({change_pct:+.1f}% from previous week)")
        
        # Property type trends
        for prop_type in ['apartment', 'single_detached', 'townhouse']:
            curr = df[(df['week'] == week) & (df['property_type'] == prop_type)]
            prev = df[(df['week'] == previous_week['week']) & (df['property_type'] == prop_type)]
            
            if not curr.empty and not prev.empty:
                rent_change = ((curr.iloc[0]['avg_rent'] - prev.iloc[0]['avg_rent']) / prev.iloc[0]['avg_rent'] * 100)
                insights.append(f"{prop_type.title()}: ${curr.iloc[0]['avg_rent']:.0f}/mo ({rent_change:+.1f}%)")
        
        logger.info("  Market Insights:")
        for insight in insights:
            logger.info(f"    • {insight}")
    
    def run(self):
        """Main aggregation process."""
        logger.info("🚀 Starting RentFaster weekly aggregation")
        
        # Get weeks that need processing
        unprocessed_weeks = self.get_unprocessed_weeks()
        
        if not unprocessed_weeks:
            logger.info("✅ All weeks are already processed")
            return
        
        logger.info(f"📅 Found {len(unprocessed_weeks)} weeks to process")
        
        for week in unprocessed_weeks:
            # Aggregate data for this week
            aggregations = self.aggregate_week(week)
            
            # Save to database
            if aggregations:
                self.save_aggregations(aggregations)
                
                # Generate insights for the latest week
                if week == unprocessed_weeks[-1]:
                    self.generate_market_insights(week)
        
        logger.info("✅ Weekly aggregation complete")
        
        # Close connection
        self.conn.close()

def main():
    """Run the aggregation process."""
    aggregator = RentfasterAggregator()
    aggregator.run()

if __name__ == "__main__":
    main()