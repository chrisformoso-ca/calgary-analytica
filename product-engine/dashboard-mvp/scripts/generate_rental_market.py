#!/usr/bin/env python3
"""
Generate Rental Market JSON for Calgary Housing Dashboard
Outputs rental_market.json with CMHC data and rental market insights
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RentalMarketGenerator:
    """Generate rental market data for dashboard."""
    
    def __init__(self):
        self.db_path = Path(__file__).parents[3] / 'data-lake' / 'calgary_data.db'
        self.output_path = Path(__file__).parent.parent / 'data' / 'rental_market.json'
        
    def connect_db(self) -> sqlite3.Connection:
        """Connect to the Calgary data database."""
        return sqlite3.connect(self.db_path)
    
    def get_cmhc_data(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get CMHC rental market data."""
        query = """
        SELECT 
            year,
            property_type,
            bedroom_type,
            metric_type,
            value
        FROM rental_market_annual
        WHERE validation_status = 'approved'
        ORDER BY year DESC, property_type, bedroom_type, metric_type
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Organize by year, property type, and bedroom type
        cmhc_data = {}
        for year, prop_type, bedroom, metric, value in results:
            if year not in cmhc_data:
                cmhc_data[year] = {}
            if prop_type not in cmhc_data[year]:
                cmhc_data[year][prop_type] = {}
            if bedroom not in cmhc_data[year][prop_type]:
                cmhc_data[year][prop_type][bedroom] = {}
            
            cmhc_data[year][prop_type][bedroom][metric] = value
            
        return cmhc_data
    
    def get_rental_trends(self, conn: sqlite3.Connection) -> Dict[str, List]:
        """Get rental price and vacancy trends."""
        # Get average rent trends
        rent_query = """
        SELECT 
            year,
            property_type,
            bedroom_type,
            value
        FROM rental_market_annual
        WHERE metric_type = 'average_rent'
        AND validation_status = 'approved'
        ORDER BY year, property_type, bedroom_type
        """
        
        # Get vacancy rate trends
        vacancy_query = """
        SELECT 
            year,
            property_type,
            bedroom_type,
            value
        FROM rental_market_annual
        WHERE metric_type = 'vacancy_rate'
        AND validation_status = 'approved'
        ORDER BY year, property_type, bedroom_type
        """
        
        cursor = conn.cursor()
        
        # Process rent data
        cursor.execute(rent_query)
        rent_results = cursor.fetchall()
        
        # Process vacancy data
        cursor.execute(vacancy_query)
        vacancy_results = cursor.fetchall()
        
        trends = {
            'rent_trends': {},
            'vacancy_trends': {}
        }
        
        # Organize rent trends
        for year, prop_type, bedroom, value in rent_results:
            key = f"{prop_type}_{bedroom}"
            if key not in trends['rent_trends']:
                trends['rent_trends'][key] = []
            trends['rent_trends'][key].append({
                'year': year,
                'average_rent': value
            })
            
        # Organize vacancy trends
        for year, prop_type, bedroom, value in vacancy_results:
            key = f"{prop_type}_{bedroom}"
            if key not in trends['vacancy_trends']:
                trends['vacancy_trends'][key] = []
            trends['vacancy_trends'][key].append({
                'year': year,
                'vacancy_rate': value
            })
            
        return trends
    
    def get_latest_snapshot(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get latest rental listings snapshot data."""
        query = """
        SELECT 
            COUNT(*) as total_listings,
            property_type,
            AVG(rent) as avg_rent,
            MIN(rent) as min_rent,
            MAX(rent) as max_rent,
            AVG(bedrooms) as avg_bedrooms
        FROM rental_listings_snapshot
        WHERE extraction_week = (SELECT MAX(extraction_week) FROM rental_listings_snapshot)
        GROUP BY property_type
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        snapshot = {
            'by_property_type': {}
        }
        
        total_listings = 0
        for count, prop_type, avg, min_p, max_p, beds in results:
            total_listings += count
            snapshot['by_property_type'][prop_type] = {
                'count': count,
                'avg_rent': round(avg, 2) if avg else None,
                'rent_range': {'min': min_p, 'max': max_p},
                'avg_bedrooms': round(beds, 1) if beds else None
            }
            
        snapshot['total_listings'] = total_listings
        
        # Get snapshot date
        cursor.execute("SELECT MAX(extraction_week) FROM rental_listings_snapshot")
        snapshot['snapshot_week'] = cursor.fetchone()[0]
        
        return snapshot
    
    def calculate_affordability(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Calculate rental affordability metrics."""
        # Get latest CMHC average rents
        query = """
        SELECT 
            property_type,
            bedroom_type,
            value as avg_rent
        FROM rental_market_annual
        WHERE year = (SELECT MAX(year) FROM rental_market_annual)
        AND metric_type = 'average_rent'
        AND validation_status = 'approved'
        ORDER BY property_type, bedroom_type
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        affordability = {}
        for prop_type, bedroom, avg_rent in results:
            key = f"{prop_type}_{bedroom}"
            if avg_rent:
                # Calculate required income (rent should be ~30% of gross income)
                required_income = (avg_rent * 12) / 0.30
                affordability[key] = {
                    'property_type': prop_type,
                    'bedroom_type': bedroom,
                    'average_rent': avg_rent,
                    'annual_rent': avg_rent * 12,
                    'required_income': round(required_income),
                    'as_pct_median_income': round((avg_rent * 12) / 89000 * 100, 1)  # $89k median household income
                }
                
        return affordability
    
    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights from rental data."""
        insights = []
        
        # Vacancy rate insights
        latest_year = max(data['cmhc_data'].keys()) if data['cmhc_data'] else None
        if latest_year and 'apartment' in data['cmhc_data'][latest_year]:
            # Look for overall vacancy rate
            for bedroom_type in data['cmhc_data'][latest_year]['apartment']:
                if 'vacancy_rate' in data['cmhc_data'][latest_year]['apartment'][bedroom_type]:
                    vac_rate = data['cmhc_data'][latest_year]['apartment'][bedroom_type]['vacancy_rate']
                    if vac_rate < 2:
                        insights.append(f"Very tight rental market with {vac_rate}% vacancy rate")
                    elif vac_rate > 5:
                        insights.append(f"Rental market favors tenants with {vac_rate}% vacancy")
                    break
        
        # Rent trend insights
        if 'apartment_Bachelor' in data['trends']['rent_trends']:
            bach_rents = data['trends']['rent_trends']['apartment_Bachelor']
            if len(bach_rents) >= 2:
                recent = bach_rents[-1]['average_rent']
                previous = bach_rents[-2]['average_rent']
                if previous and recent:
                    change = ((recent - previous) / previous) * 100
                    if abs(change) > 5:
                        direction = "increased" if change > 0 else "decreased"
                        insights.append(f"Bachelor apartment rents {direction} {abs(change):.1f}% year-over-year")
        
        # Affordability insights
        if 'affordability' in data:
            affordable_items = [(k, v) for k, v in data['affordability'].items() if 'required_income' in v]
            if affordable_items:
                most_affordable = min(affordable_items, key=lambda x: x[1]['required_income'])
                insights.append(f"{most_affordable[0].replace('_', ' ')} most affordable at ${most_affordable[1]['average_rent']}/month")
            
        return insights
    
    def generate(self) -> None:
        """Generate the rental market JSON file."""
        logger.info("🏠 Generating rental market data...")
        
        try:
            conn = self.connect_db()
            
            # Get all data
            cmhc_data = self.get_cmhc_data(conn)
            trends = self.get_rental_trends(conn)
            snapshot = self.get_latest_snapshot(conn)
            affordability = self.calculate_affordability(conn)
            
            # Build output
            output = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'sources': {
                        'cmhc': 'Canada Mortgage and Housing Corporation annual reports',
                        'snapshot': 'RentFaster.ca listings data'
                    }
                },
                'cmhc_data': cmhc_data,
                'trends': trends,
                'current_snapshot': snapshot,
                'affordability': affordability,
                'insights': self.generate_insights({
                    'cmhc_data': cmhc_data,
                    'trends': trends,
                    'affordability': affordability
                })
            }
            
            # Save the file
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w') as f:
                json.dump(output, f, indent=2)
                
            logger.info(f"✅ Rental market data generated: {self.output_path}")
            
            # Print summary
            print("\n🏠 RENTAL MARKET EXPORT SUMMARY")
            print("="*50)
            print(f"CMHC data years: {min(cmhc_data.keys())} to {max(cmhc_data.keys())}")
            print(f"Current listings: {snapshot['total_listings']}")
            print(f"Property types: {len(snapshot['by_property_type'])}")
            if affordability:
                avg_required = sum(a['required_income'] for a in affordability.values()) / len(affordability)
                print(f"Avg required income: ${avg_required:,.0f}")
            print(f"\n📂 Output: {self.output_path}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error generating rental market data: {e}")
            raise

def main():
    """Generate rental market export."""
    generator = RentalMarketGenerator()
    generator.generate()

if __name__ == "__main__":
    main()