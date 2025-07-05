#!/usr/bin/env python3
"""
Generate Service Requests (311) JSON for Calgary Housing Dashboard
Outputs service_requests_311.json with neighborhood quality indicators
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceRequestsGenerator:
    """Generate 311 service request data for dashboard."""
    
    def __init__(self):
        self.db_path = Path(__file__).parents[3] / 'data-lake' / 'calgary_data.db'
        self.output_path = Path(__file__).parent.parent / 'data' / 'service_requests_311.json'
        
    def connect_db(self) -> sqlite3.Connection:
        """Connect to the Calgary data database."""
        return sqlite3.connect(self.db_path)
    
    def get_recent_trends(self, conn: sqlite3.Connection, months: int = 12) -> Dict[str, Any]:
        """Get recent 311 request trends."""
        # Calculate the cutoff year-month
        cutoff_date = datetime.now()
        cutoff_year = cutoff_date.year
        cutoff_month = cutoff_date.month - months
        while cutoff_month <= 0:
            cutoff_month += 12
            cutoff_year -= 1
        cutoff_year_month = f"{cutoff_year:04d}-{cutoff_month:02d}"
        
        query = """
        SELECT 
            year_month,
            service_category,
            SUM(total_requests) as total_requests
        FROM service_requests_311_monthly
        WHERE year_month >= ?
        GROUP BY year_month, service_category
        ORDER BY year_month DESC, service_category
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (cutoff_year_month,))
        results = cursor.fetchall()
        
        # Organize by category
        trends = {}
        for year_month, category, count in results:
            if category not in trends:
                trends[category] = []
            trends[category].append({
                'date': year_month,
                'count': count
            })
        
        # Sort each by date ascending
        for category in trends:
            trends[category].sort(key=lambda x: x['date'])
            
        return trends
    
    def get_top_issues(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """Get top service request categories."""
        # Calculate the cutoff year-month for last 12 months
        cutoff_date = datetime.now()
        cutoff_year = cutoff_date.year - 1
        cutoff_month = cutoff_date.month
        cutoff_year_month = f"{cutoff_year:04d}-{cutoff_month:02d}"
        
        query = """
        SELECT 
            service_category,
            SUM(total_requests) as total_requests,
            AVG(total_requests) as avg_monthly_requests
        FROM service_requests_311_monthly
        WHERE year_month >= ?
        GROUP BY service_category
        ORDER BY total_requests DESC
        LIMIT 10
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (cutoff_year_month,))
        results = cursor.fetchall()
        
        issues = []
        for category, total, avg in results:
            issues.append({
                'category': category,
                'total_requests_12mo': total,
                'avg_monthly': round(avg, 1)
            })
            
        return issues
    
    def get_seasonal_patterns(self, conn: sqlite3.Connection) -> Dict[str, List]:
        """Get seasonal patterns for key categories."""
        # Categories that likely have seasonal patterns
        seasonal_categories = ['Snow/Ice', 'Roads', 'Parks', 'Bylaw']
        
        query = """
        SELECT 
            service_category,
            month,
            AVG(total_requests) as avg_requests
        FROM service_requests_311_monthly
        WHERE service_category IN ({})
        GROUP BY service_category, month
        ORDER BY service_category, month
        """.format(','.join('?' * len(seasonal_categories)))
        
        cursor = conn.cursor()
        cursor.execute(query, seasonal_categories)
        results = cursor.fetchall()
        
        patterns = {}
        for category, month, avg in results:
            if category not in patterns:
                patterns[category] = []
            patterns[category].append({
                'month': int(month),
                'avg_requests': round(avg, 1)
            })
            
        return patterns
    
    def calculate_neighborhood_scores(self, conn: sqlite3.Connection) -> Dict[str, float]:
        """Calculate neighborhood quality scores based on 311 data."""
        # Calculate the cutoff year-month for last 12 months
        cutoff_date = datetime.now()
        cutoff_year = cutoff_date.year - 1
        cutoff_month = cutoff_date.month
        cutoff_year_month = f"{cutoff_year:04d}-{cutoff_month:02d}"
        
        # This is a simplified scoring - lower request counts = better score
        query = """
        WITH community_requests AS (
            SELECT 
                community_name,
                SUM(total_requests) as total_requests,
                COUNT(DISTINCT service_category) as issue_diversity
            FROM service_requests_311_monthly
            WHERE year_month >= ?
            AND community_name IS NOT NULL
            GROUP BY community_name
        ),
        community_stats AS (
            SELECT 
                AVG(total_requests) as avg_requests,
                -- SQLite doesn't have STDEV, so we'll calculate variance manually
                AVG(total_requests * total_requests) - AVG(total_requests) * AVG(total_requests) as variance
            FROM community_requests
        )
        SELECT 
            cr.community_name,
            cr.total_requests,
            cr.issue_diversity,
            -- Normalize score: lower is better, scale 0-100
            CASE 
                WHEN cs.variance > 0 THEN
                    ROUND(100 - (((cr.total_requests - cs.avg_requests) / SQRT(cs.variance) + 3) * 16.67), 1)
                ELSE 50
            END as quality_score
        FROM community_requests cr
        CROSS JOIN community_stats cs
        ORDER BY quality_score DESC
        LIMIT 20
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (cutoff_year_month,))
        results = cursor.fetchall()
        
        scores = {}
        for community, requests, diversity, score in results:
            scores[community] = {
                'quality_score': max(0, min(100, score)),  # Ensure 0-100 range
                'total_requests_12mo': requests,
                'issue_types': diversity
            }
            
        return scores
    
    def generate(self) -> None:
        """Generate the service requests JSON file."""
        logger.info("📞 Generating 311 service requests data...")
        
        try:
            conn = self.connect_db()
            
            # Get all data
            trends = self.get_recent_trends(conn)
            top_issues = self.get_top_issues(conn)
            seasonal = self.get_seasonal_patterns(conn)
            neighborhood_scores = self.calculate_neighborhood_scores(conn)
            
            # Get summary stats
            cursor = conn.cursor()
            
            # Calculate the cutoff year-month for last 12 months
            cutoff_date = datetime.now()
            cutoff_year = cutoff_date.year - 1
            cutoff_month = cutoff_date.month
            cutoff_year_month = f"{cutoff_year:04d}-{cutoff_month:02d}"
            
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT year_month) as months,
                    SUM(total_requests) as total_requests,
                    COUNT(DISTINCT service_category) as categories,
                    COUNT(DISTINCT community_name) as communities
                FROM service_requests_311_monthly
                WHERE year_month >= ?
            """, (cutoff_year_month,))
            months, total, categories, communities = cursor.fetchone()
            
            # Build output
            output = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'data_coverage': '12 months',
                    'note': 'Service request data indicates neighborhood maintenance and quality of life'
                },
                'summary': {
                    'total_requests_12mo': total,
                    'avg_monthly': round(total / months, 1),
                    'category_count': categories,
                    'community_count': communities
                },
                'top_issues': top_issues,
                'trends': trends,
                'seasonal_patterns': seasonal,
                'neighborhood_quality': neighborhood_scores,
                'insights': [
                    "Higher service request volumes may indicate more active civic engagement or maintenance needs",
                    "Seasonal patterns affect categories like snow removal and park maintenance",
                    "Quality scores are relative - compare neighborhoods with similar characteristics"
                ]
            }
            
            # Save the file
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w') as f:
                json.dump(output, f, indent=2)
                
            logger.info(f"✅ Service requests data generated: {self.output_path}")
            
            # Print summary
            print("\n📞 SERVICE REQUESTS (311) EXPORT SUMMARY")
            print("="*50)
            print(f"Total requests (12mo): {total:,}")
            print(f"Top issue: {top_issues[0]['category']} ({top_issues[0]['total_requests_12mo']:,} requests)")
            print(f"Communities tracked: {communities}")
            print(f"Best neighborhood score: {list(neighborhood_scores.keys())[0]}")
            print(f"\n📂 Output: {self.output_path}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error generating service requests data: {e}")
            raise

def main():
    """Generate service requests export."""
    generator = ServiceRequestsGenerator()
    generator.generate()

if __name__ == "__main__":
    main()