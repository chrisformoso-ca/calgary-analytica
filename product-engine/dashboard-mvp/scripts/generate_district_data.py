#!/usr/bin/env python3
"""
Generate District Data JSON for Calgary Housing Dashboard MVP
Outputs district_data.json with pricing and trends by district and property type
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DistrictDataGenerator:
    """Generate district-level housing data for dashboard."""
    
    def __init__(self):
        self.db_path = Path(__file__).parents[3] / 'data-lake' / 'calgary_data.db'
        self.output_path = Path(__file__).parent.parent / 'data' / 'district_data.json'
        self.archive_path = Path(__file__).parent.parent / 'archive'
        
        # Property type display names
        self.property_type_display = {
            'Detached': 'Detached',
            'Semi-detached': 'Semi-Detached',
            'Row': 'Row House',
            'Apartment': 'Apartment'
        }
        
        # District display order
        self.district_order = [
            'North West', 'North', 'North East',
            'West', 'City Centre', 'East',
            'South West', 'South', 'South East'
        ]
    
    def connect_db(self) -> sqlite3.Connection:
        """Connect to the Calgary data database."""
        return sqlite3.connect(self.db_path)
    
    def get_latest_district_data(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get the latest month's data for all districts."""
        query = """
        SELECT 
            d.district,
            d.property_type,
            d.benchmark_price,
            d.new_sales as sales,
            d.inventory,
            d.months_supply,
            d.yoy_price_change,
            d.mom_price_change,
            d.date
        FROM housing_district_monthly d
        WHERE d.date = (SELECT MAX(date) FROM housing_district_monthly)
        ORDER BY d.district, d.property_type
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Organize by district and property type
        district_data = {}
        latest_date = None
        
        for row in results:
            district, prop_type, price, sales, inventory, months_supply, yoy, mom, date = row
            
            if not latest_date:
                latest_date = date
                
            if district not in district_data:
                district_data[district] = {
                    'district_name': district,
                    'property_types': {}
                }
            
            # Use display name for property type
            display_type = self.property_type_display.get(prop_type, prop_type)
            
            district_data[district]['property_types'][display_type] = {
                'benchmark_price': price,
                'sales': sales,
                'inventory': inventory,
                'months_supply': months_supply,
                'yoy_change': yoy if yoy else 0,
                'mom_change': mom if mom else 0
            }
        
        return district_data, latest_date
    
    def get_district_history(self, conn: sqlite3.Connection, district: str, 
                           months: int = 24) -> Dict[str, List]:
        """Get historical data for a specific district."""
        query = """
        SELECT 
            date,
            property_type,
            benchmark_price
        FROM housing_district_monthly
        WHERE district = ?
        ORDER BY date DESC, property_type
        LIMIT ?
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (district, months * 4))  # 4 property types
        results = cursor.fetchall()
        
        # Organize by property type
        history = {}
        for date, prop_type, price in results:
            display_type = self.property_type_display.get(prop_type, prop_type)
            if display_type not in history:
                history[display_type] = []
            history[display_type].append({
                'date': date,
                'price': price
            })
        
        # Sort each by date ascending for charts
        for prop_type in history:
            history[prop_type].sort(key=lambda x: x['date'])
            
        return history
    
    def calculate_district_averages(self, district_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate average prices and YoY changes by district."""
        averages = {}
        
        for district, data in district_data.items():
            total_price = 0
            total_yoy = 0
            count = 0
            
            prices_by_type = {}
            
            for prop_type, metrics in data['property_types'].items():
                price = metrics['benchmark_price']
                if price and price > 0:
                    total_price += price
                    total_yoy += metrics['yoy_change']
                    count += 1
                    prices_by_type[prop_type] = price
            
            if count > 0:
                averages[district] = {
                    'average_price': total_price / count,
                    'average_yoy_change': total_yoy / count,
                    'prices_by_type': prices_by_type
                }
        
        return averages
    
    def create_pricing_table(self, district_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create the sortable pricing table data."""
        table_data = []
        
        # Get all districts in our preferred order, but only if they have data
        ordered_districts = [d for d in self.district_order if d in district_data]
        # Add any districts not in our order (just in case)
        for district in district_data:
            if district not in ordered_districts:
                ordered_districts.append(district)
        
        for district in ordered_districts:
            data = district_data[district]
            row = {
                'district': district,
                'detached': None,
                'semi_detached': None, 
                'row_house': None,
                'apartment': None,
                'yoy_change': 0
            }
            
            # Add prices for each property type
            total_yoy = 0
            count = 0
            
            for prop_type, metrics in data['property_types'].items():
                price = metrics['benchmark_price']
                yoy = metrics['yoy_change']
                
                if prop_type == 'Detached':
                    row['detached'] = price
                elif prop_type == 'Semi-Detached':
                    row['semi_detached'] = price
                elif prop_type == 'Row House':
                    row['row_house'] = price
                elif prop_type == 'Apartment':
                    row['apartment'] = price
                
                if yoy:
                    total_yoy += yoy
                    count += 1
            
            # Calculate average YoY change
            if count > 0:
                row['yoy_change'] = round(total_yoy / count, 1)
            
            table_data.append(row)
        
        return table_data
    
    def find_best_value_districts(self, district_data: Dict[str, Any]) -> Dict[str, Any]:
        """Find most affordable districts by property type."""
        best_value = {
            'most_affordable': {},
            'strongest_appreciation': {},
            'entry_level': []  # Districts with properties under $400k
        }
        
        # Track lowest prices and highest appreciation by property type
        for prop_type in self.property_type_display.values():
            lowest_price = float('inf')
            lowest_district = None
            highest_yoy = float('-inf')
            highest_district = None
            
            for district, data in district_data.items():
                if prop_type in data['property_types']:
                    metrics = data['property_types'][prop_type]
                    price = metrics['benchmark_price']
                    yoy = metrics['yoy_change']
                    
                    # Check for lowest price
                    if price and price < lowest_price:
                        lowest_price = price
                        lowest_district = district
                    
                    # Check for highest appreciation
                    if yoy and yoy > highest_yoy:
                        highest_yoy = yoy
                        highest_district = district
                    
                    # Check for entry-level pricing
                    if price and price < 400000:
                        entry = f"{district}: {prop_type} (${price:,.0f})"
                        if entry not in best_value['entry_level']:
                            best_value['entry_level'].append(entry)
            
            if lowest_district:
                best_value['most_affordable'][prop_type] = {
                    'district': lowest_district,
                    'price': lowest_price
                }
            
            if highest_district:
                best_value['strongest_appreciation'][prop_type] = {
                    'district': highest_district,
                    'yoy_change': highest_yoy
                }
        
        return best_value
    
    def get_all_district_histories(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get historical data for all districts."""
        histories = {}
        
        # Get list of all districts
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT district FROM housing_district_monthly")
        districts = [row[0] for row in cursor.fetchall()]
        
        for district in districts:
            histories[district] = self.get_district_history(conn, district)
        
        return histories
    
    def calculate_district_rankings(self, averages: Dict[str, Any]) -> List[Tuple[str, float]]:
        """Rank districts by YoY appreciation."""
        rankings = []
        
        for district, data in averages.items():
            yoy = data.get('average_yoy_change', 0)
            rankings.append((district, yoy))
        
        # Sort by YoY change descending
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings
    
    def generate(self) -> None:
        """Generate the district data JSON file."""
        logger.info("🏘️ Generating district data...")
        
        try:
            conn = self.connect_db()
            
            # Get current district data
            district_data, latest_date = self.get_latest_district_data(conn)
            
            # Calculate averages
            averages = self.calculate_district_averages(district_data)
            
            # Create pricing table
            pricing_table = self.create_pricing_table(district_data)
            
            # Find best values
            best_value = self.find_best_value_districts(district_data)
            
            # Get historical data for all districts
            histories = self.get_all_district_histories(conn)
            
            # Calculate rankings
            rankings = self.calculate_district_rankings(averages)
            
            # Build output structure
            output = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'data_last_updated': latest_date,
                    'version': '1.0',
                    'district_count': len(district_data)
                },
                'current_data': district_data,
                'pricing_table': pricing_table,
                'district_averages': averages,
                'best_value': best_value,
                'appreciation_rankings': [
                    {'district': d, 'yoy_change': yoy} 
                    for d, yoy in rankings
                ],
                'historical_trends': histories,
                'district_categories': {
                    'north': ['North West', 'North', 'North East'],
                    'south': ['South West', 'South', 'South East'],
                    'east': ['East', 'North East', 'South East'],
                    'west': ['West', 'North West', 'South West'],
                    'central': ['City Centre']
                }
            }
            
            # Archive previous version if exists
            if self.output_path.exists():
                archive_dir = self.archive_path / datetime.now().strftime('%Y-%m')
                archive_dir.mkdir(parents=True, exist_ok=True)
                archive_file = archive_dir / f"district_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.output_path.rename(archive_file)
                logger.info(f"📦 Archived previous version to {archive_file}")
            
            # Save the new file
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w') as f:
                json.dump(output, f, indent=2)
                
            logger.info(f"✅ District data generated: {self.output_path}")
            
            # Print summary
            print("\n🏘️ DISTRICT DATA EXPORT SUMMARY")
            print("="*50)
            print(f"Last data update: {latest_date}")
            print(f"Districts: {len(district_data)}")
            print(f"Entry-level options (<$400k): {len(best_value['entry_level'])}")
            
            print("\n🏆 Top 3 Districts by Appreciation:")
            for i, (district, yoy) in enumerate(rankings[:3]):
                print(f"  {i+1}. {district}: +{yoy:.1f}% YoY")
            
            print("\n💰 Most Affordable by Type:")
            for prop_type, data in best_value['most_affordable'].items():
                print(f"  {prop_type}: {data['district']} (${data['price']:,.0f})")
                
            print(f"\n📂 Output: {self.output_path}")
            print(f"📂 View: file://{self.output_path.absolute()}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error generating district data: {e}")
            raise

def main():
    """Generate district data export."""
    generator = DistrictDataGenerator()
    generator.generate()

if __name__ == "__main__":
    main()