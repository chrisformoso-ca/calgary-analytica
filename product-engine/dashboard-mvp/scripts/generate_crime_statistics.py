#!/usr/bin/env python3
"""
Generate Crime Statistics JSON for Calgary Housing Dashboard
Outputs crime_statistics.json with community safety indicators
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrimeStatisticsGenerator:
    """Generate crime statistics data for dashboard."""
    
    def __init__(self):
        self.db_path = Path(__file__).parents[3] / 'data-lake' / 'calgary_data.db'
        self.output_path = Path(__file__).parent.parent / 'data' / 'crime_statistics.json'
        
    def connect_db(self) -> sqlite3.Connection:
        """Connect to the Calgary data database."""
        return sqlite3.connect(self.db_path)
    
    def get_crime_trends(self, conn: sqlite3.Connection) -> Dict[str, List]:
        """Get crime trends by category over time."""
        query = """
        SELECT 
            year,
            crime_category,
            SUM(incident_count) as total_incidents
        FROM crime_statistics_monthly
        WHERE year >= 2020
        GROUP BY year, crime_category
        ORDER BY year DESC, crime_category
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        trends = {}
        for year, category, count in results:
            if category not in trends:
                trends[category] = []
            trends[category].append({
                'year': year,
                'incidents': count
            })
        
        # Sort each by year ascending
        for category in trends:
            trends[category].sort(key=lambda x: x['year'])
            
        return trends
    
    def get_community_safety_scores(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Calculate community safety scores."""
        # Get recent crime data by community
        query = """
        WITH community_crime AS (
            SELECT 
                community,
                SUM(incident_count) as total_incidents,
                COUNT(DISTINCT crime_category) as crime_diversity,
                SUM(CASE WHEN crime_category IN ('Violence', 'Person Crimes') 
                    THEN incident_count ELSE 0 END) as violent_crimes,
                SUM(CASE WHEN crime_category IN ('Property', 'Theft', 'Break and Enter') 
                    THEN incident_count ELSE 0 END) as property_crimes
            FROM crime_statistics_monthly
            WHERE year >= 2023
            AND community != 'UNKNOWN'
            GROUP BY community
        ),
        community_stats AS (
            SELECT 
                AVG(total_incidents) as avg_incidents,
                -- SQLite doesn't have STDEV, so we'll calculate variance manually
                AVG(total_incidents * total_incidents) - AVG(total_incidents) * AVG(total_incidents) as variance
            FROM community_crime
        )
        SELECT 
            cc.community,
            cc.total_incidents,
            cc.violent_crimes,
            cc.property_crimes,
            cc.crime_diversity,
            -- Calculate safety score (higher is safer)
            CASE 
                WHEN cs.variance > 0 THEN
                    ROUND(100 - (((cc.total_incidents - cs.avg_incidents) / SQRT(cs.variance) + 3) * 16.67), 1)
                ELSE 50
            END as safety_score
        FROM community_crime cc
        CROSS JOIN community_stats cs
        ORDER BY safety_score DESC
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        scores = {}
        for community, total, violent, property, diversity, score in results:
            scores[community] = {
                'safety_score': max(0, min(100, score)),  # Ensure 0-100 range
                'total_incidents': total,
                'violent_crimes': violent,
                'property_crimes': property,
                'crime_types': diversity,
                'primary_concern': 'Property crimes' if property > violent else 'Violent crimes'
            }
            
        return scores
    
    def get_crime_by_category(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """Get crime statistics by category."""
        query = """
        SELECT 
            crime_category,
            SUM(incident_count) as total_incidents,
            COUNT(DISTINCT community) as affected_communities,
            ROUND(AVG(incident_count), 1) as avg_per_community
        FROM crime_statistics_monthly
        WHERE year >= 2023
        GROUP BY crime_category
        ORDER BY total_incidents DESC
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        categories = []
        for category, total, communities, avg in results:
            categories.append({
                'category': category,
                'total_incidents': total,
                'affected_communities': communities,
                'avg_per_community': avg
            })
            
        return categories
    
    def get_safest_neighborhoods(self, conn: sqlite3.Connection, limit: int = 10) -> List[Dict[str, Any]]:
        """Get safest neighborhoods based on crime data."""
        query = """
        SELECT 
            community,
            SUM(incident_count) as total_incidents,
            ROUND(SUM(incident_count) * 1.0 / COUNT(DISTINCT strftime('%Y-%m', date)), 1) as avg_monthly
        FROM crime_statistics_monthly
        WHERE year >= 2023
        AND community != 'UNKNOWN'
        GROUP BY community
        ORDER BY total_incidents ASC
        LIMIT ?
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        neighborhoods = []
        for community, total, avg_monthly in results:
            neighborhoods.append({
                'community': community,
                'total_incidents': total,
                'avg_monthly_incidents': avg_monthly
            })
            
        return neighborhoods
    
    def get_year_over_year_change(self, conn: sqlite3.Connection) -> Dict[str, float]:
        """Calculate year-over-year crime rate changes."""
        query = """
        WITH yearly_totals AS (
            SELECT 
                year,
                SUM(incident_count) as total_incidents
            FROM crime_statistics_monthly
            WHERE year IN (2023, 2024)
            GROUP BY year
        )
        SELECT 
            year,
            total_incidents
        FROM yearly_totals
        ORDER BY year
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        if len(results) >= 2:
            prev_year, prev_total = results[0]
            curr_year, curr_total = results[1]
            change_pct = ((curr_total - prev_total) / prev_total) * 100
            
            return {
                'previous_year': prev_year,
                'current_year': curr_year,
                'change_percent': round(change_pct, 1),
                'direction': 'increased' if change_pct > 0 else 'decreased'
            }
        
        return {}
    
    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from crime data."""
        insights = []
        
        # Year-over-year change
        if data['year_over_year']:
            yoy = data['year_over_year']
            insights.append(f"Overall crime {yoy['direction']} {abs(yoy['change_percent'])}% from {yoy['previous_year']}")
        
        # Safest neighborhoods
        if data['safest_neighborhoods']:
            safest = data['safest_neighborhoods'][0]['community']
            insights.append(f"{safest} recorded the fewest incidents among tracked communities")
        
        # Crime category insights
        if data['crime_categories']:
            top_category = data['crime_categories'][0]
            insights.append(f"{top_category['category']} accounts for the most incidents across the city")
        
        # Add context
        insights.append("Crime statistics should be considered alongside community size and reporting rates")
        
        return insights
    
    def generate(self) -> None:
        """Generate the crime statistics JSON file."""
        logger.info("🚨 Generating crime statistics data...")
        
        try:
            conn = self.connect_db()
            
            # Get all data
            trends = self.get_crime_trends(conn)
            safety_scores = self.get_community_safety_scores(conn)
            categories = self.get_crime_by_category(conn)
            safest = self.get_safest_neighborhoods(conn)
            yoy = self.get_year_over_year_change(conn)
            
            # Get summary stats
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT community) as communities,
                    COUNT(DISTINCT crime_category) as categories,
                    SUM(incident_count) as total_incidents,
                    MIN(year) as first_year,
                    MAX(year) as last_year
                FROM crime_statistics_monthly
                WHERE community != 'UNKNOWN'
            """)
            communities, cat_count, total, first_year, last_year = cursor.fetchone()
            
            # Build output
            output = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'data_coverage': f"{first_year} to {last_year}",
                    'note': 'Crime statistics help assess neighborhood safety but should be considered with other factors'
                },
                'summary': {
                    'communities_tracked': communities,
                    'crime_categories': cat_count,
                    'total_incidents': total,
                    'years_covered': f"{first_year}-{last_year}"
                },
                'trends': trends,
                'community_safety': dict(list(safety_scores.items())[:50]),  # Top 50 communities
                'crime_categories': categories,
                'safest_neighborhoods': safest,
                'year_over_year': yoy,
                'insights': self.generate_insights({
                    'year_over_year': yoy,
                    'safest_neighborhoods': safest,
                    'crime_categories': categories
                })
            }
            
            # Save the file
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w') as f:
                json.dump(output, f, indent=2)
                
            logger.info(f"✅ Crime statistics data generated: {self.output_path}")
            
            # Print summary
            print("\n🚨 CRIME STATISTICS EXPORT SUMMARY")
            print("="*50)
            print(f"Communities tracked: {communities}")
            print(f"Total incidents: {total:,}")
            print(f"Years covered: {first_year}-{last_year}")
            if safest:
                print(f"Safest community: {safest[0]['community']}")
            print(f"\n📂 Output: {self.output_path}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error generating crime statistics data: {e}")
            raise

def main():
    """Generate crime statistics export."""
    generator = CrimeStatisticsGenerator()
    generator.generate()

if __name__ == "__main__":
    main()