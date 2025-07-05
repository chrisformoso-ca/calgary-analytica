#!/usr/bin/env python3
"""
Generate Metadata JSON for Calgary Housing Dashboard MVP
Outputs metadata.json with data freshness, quality scores, and source information
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MetadataGenerator:
    """Generate metadata about all dashboard data."""
    
    def __init__(self):
        self.db_path = Path(__file__).parents[3] / 'data-lake' / 'calgary_data.db'
        self.output_path = Path(__file__).parent.parent / 'data' / 'metadata.json'
        self.data_path = Path(__file__).parent.parent / 'data'
        self.archive_path = Path(__file__).parent.parent / 'archive'
    
    def connect_db(self) -> sqlite3.Connection:
        """Connect to the Calgary data database."""
        return sqlite3.connect(self.db_path)
    
    def get_data_freshness(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Check freshness of all data sources."""
        freshness = {}
        
        # Housing data
        query = """
        SELECT MAX(date) as latest_date, COUNT(DISTINCT date) as month_count
        FROM housing_city_monthly
        """
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            # Handle date that might be in YYYY-MM format
            date_str = result[0]
            if len(date_str) == 7:  # YYYY-MM format
                date_str += '-01'  # Add day
            
            freshness['housing_city'] = {
                'latest_date': result[0],
                'months_available': result[1],
                'days_old': (datetime.now().date() - datetime.fromisoformat(date_str).date()).days
            }
        
        # District data
        query = """
        SELECT MAX(date) as latest_date, COUNT(DISTINCT date) as month_count
        FROM housing_district_monthly
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            # Handle date that might be in YYYY-MM-DD format
            date_str = result[0]
            
            freshness['housing_district'] = {
                'latest_date': result[0],
                'months_available': result[1],
                'days_old': (datetime.now().date() - datetime.fromisoformat(date_str).date()).days
            }
        
        # Economic indicators - get latest date for each indicator
        query = """
        SELECT indicator_name, MAX(date) as latest_date
        FROM economic_indicators_monthly
        GROUP BY indicator_name
        ORDER BY latest_date DESC
        """
        cursor.execute(query)
        economic_results = cursor.fetchall()
        
        if economic_results:
            # Overall latest
            freshness['economic_indicators'] = {
                'latest_date': economic_results[0][1],
                'indicator_count': len(economic_results),
                'days_old': (datetime.now().date() - datetime.fromisoformat(economic_results[0][1]).date()).days
            }
            
            # Check for stale indicators (>60 days old)
            stale_indicators = []
            for indicator, date in economic_results:
                days_old = (datetime.now().date() - datetime.fromisoformat(date).date()).days
                if days_old > 60:
                    stale_indicators.append({
                        'indicator': indicator,
                        'last_updated': date,
                        'days_old': days_old
                    })
            
            if stale_indicators:
                freshness['economic_indicators']['stale_indicators'] = stale_indicators
        
        return freshness
    
    def check_data_quality(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Check data quality metrics."""
        quality = {}
        
        # Check for data gaps in housing
        query = """
        WITH date_series AS (
            SELECT DISTINCT date FROM housing_city_monthly
            ORDER BY date DESC
            LIMIT 12
        )
        SELECT COUNT(*) as expected, 
               (SELECT COUNT(*) FROM housing_city_monthly 
                WHERE date IN (SELECT date FROM date_series) 
                AND property_type = 'Total') as actual
        FROM date_series
        """
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            expected, actual = result
            quality['housing_completeness'] = {
                'expected_records': expected,
                'actual_records': actual,
                'completeness_percent': (actual / expected * 100) if expected > 0 else 0
            }
        
        # Check confidence scores
        query = """
        SELECT 
            AVG(confidence_score) as avg_confidence,
            MIN(confidence_score) as min_confidence,
            COUNT(CASE WHEN confidence_score < 0.9 THEN 1 END) as low_confidence_count
        FROM housing_city_monthly
        WHERE date >= date('now', '-6 months')
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result and result[0]:
            quality['extraction_confidence'] = {
                'average': round(result[0], 3),
                'minimum': round(result[1], 3),
                'low_confidence_records': result[2]
            }
        
        return quality
    
    def get_export_info(self) -> Dict[str, Any]:
        """Get information about exported JSON files."""
        exports = {}
        
        for json_file in self.data_path.glob('*.json'):
            if json_file.name != 'metadata.json':
                stat = json_file.stat()
                exports[json_file.stem] = {
                    'filename': json_file.name,
                    'size_bytes': stat.st_size,
                    'size_formatted': self.format_file_size(stat.st_size),
                    'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'exists': True
                }
        
        # Check for expected files that might be missing
        expected_files = ['market_overview', 'economic_indicators', 'district_data', 'rate_data']
        for expected in expected_files:
            if expected not in exports:
                exports[expected] = {
                    'filename': f'{expected}.json',
                    'exists': False,
                    'note': 'File not generated yet'
                }
        
        return exports
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def get_data_sources(self) -> Dict[str, Any]:
        """Document data sources and attribution."""
        return {
            'housing_data': {
                'provider': 'Calgary Real Estate Board (CREB)',
                'url': 'https://www.creb.ca/',
                'update_frequency': 'Monthly',
                'typical_release': '5th of each month',
                'license': 'CREB data used with permission'
            },
            'economic_indicators': {
                'provider': 'City of Calgary Economic Development',
                'url': 'https://www.calgaryeconomicdevelopment.com/',
                'update_frequency': 'Monthly',
                'typical_release': 'Mid-month',
                'license': 'Public data'
            },
            'interest_rates': {
                'provider': 'Bank of Canada',
                'url': 'https://www.bankofcanada.ca/',
                'update_frequency': '8 times per year',
                'license': 'Public data'
            },
            'mortgage_rates': {
                'provider': 'Manual collection from major banks',
                'update_frequency': 'Monthly manual update',
                'note': 'Pending automated data source'
            }
        }
    
    def get_update_schedule(self) -> Dict[str, Any]:
        """Document update schedule."""
        return {
            'monthly_updates': {
                'target_date': '5th of each month',
                'components': [
                    'CREB housing data',
                    'Economic indicators',
                    'District data'
                ]
            },
            'manual_updates': {
                'frequency': 'As needed',
                'components': [
                    'Mortgage rates',
                    'Money supply (M2)',
                    'Wage growth data'
                ]
            },
            'next_scheduled_update': self.calculate_next_update()
        }
    
    def calculate_next_update(self) -> str:
        """Calculate next scheduled update date."""
        now = datetime.now()
        # If we're past the 5th, next update is next month
        if now.day > 5:
            if now.month == 12:
                next_update = datetime(now.year + 1, 1, 5)
            else:
                next_update = datetime(now.year, now.month + 1, 5)
        else:
            next_update = datetime(now.year, now.month, 5)
        
        return next_update.strftime('%Y-%m-%d')
    
    def get_known_issues(self) -> List[Dict[str, str]]:
        """Document known data issues or gaps."""
        return [
            {
                'issue': 'Missing wage growth data',
                'impact': 'Economic context incomplete',
                'resolution': 'Update economic extractor to capture wage indicators',
                'status': 'pending'
            },
            {
                'issue': 'Manual mortgage rate updates',
                'impact': 'Rates may be outdated',
                'resolution': 'Integrate with bank API or rate aggregator',
                'status': 'investigating'
            },
            {
                'issue': 'No money supply (M2) data',
                'impact': 'Missing monetary context',
                'resolution': 'Add Bank of Canada M2 data source',
                'status': 'planned'
            }
        ]
    
    def generate(self) -> None:
        """Generate the metadata JSON file."""
        logger.info("📋 Generating metadata...")
        
        try:
            conn = self.connect_db()
            
            # Gather all metadata
            freshness = self.get_data_freshness(conn)
            quality = self.check_data_quality(conn)
            exports = self.get_export_info()
            sources = self.get_data_sources()
            schedule = self.get_update_schedule()
            issues = self.get_known_issues()
            
            # Build output structure
            output = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'dashboard_version': 'MVP 1.0',
                    'environment': 'production'
                },
                'data_freshness': freshness,
                'data_quality': quality,
                'exported_files': exports,
                'data_sources': sources,
                'update_schedule': schedule,
                'known_issues': issues,
                'api_endpoints': {
                    'note': 'Static JSON files served via web server',
                    'base_url': '/data/',
                    'files': list(exports.keys())
                },
                'contact': {
                    'maintainer': 'Calgary Analytica',
                    'email': 'support@calgaryanalytica.com',
                    'issues': 'https://github.com/calgary-analytica/issues'
                }
            }
            
            # No need to archive metadata (it's meta!)
            
            # Save the file
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w') as f:
                json.dump(output, f, indent=2)
                
            logger.info(f"✅ Metadata generated: {self.output_path}")
            
            # Print summary
            print("\n📋 METADATA EXPORT SUMMARY")
            print("="*50)
            
            # Data freshness summary
            print("\n📅 Data Freshness:")
            for source, info in freshness.items():
                print(f"  {source}: {info['days_old']} days old (last: {info['latest_date']})")
            
            # Export status
            print("\n📁 Export Files:")
            for name, info in exports.items():
                if info['exists']:
                    print(f"  ✅ {info['filename']} ({info['size_formatted']})")
                else:
                    print(f"  ❌ {info['filename']} (not generated)")
            
            # Known issues
            print(f"\n⚠️  Known Issues: {len(issues)}")
            for issue in issues:
                print(f"  - {issue['issue']} [{issue['status']}]")
            
            print(f"\n📂 Output: {self.output_path}")
            print(f"📂 View: file://{self.output_path.absolute()}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error generating metadata: {e}")
            raise

def main():
    """Generate metadata export."""
    generator = MetadataGenerator()
    generator.generate()

if __name__ == "__main__":
    main()