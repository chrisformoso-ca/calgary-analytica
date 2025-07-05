#!/usr/bin/env python3
"""
Generate Market Overview JSON for Calgary Housing Dashboard MVP
Outputs market_overview.json with current snapshot and historical trends
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketOverviewGenerator:
    """Generate market overview data for dashboard."""
    
    def __init__(self):
        self.db_path = Path(__file__).parents[3] / 'data-lake' / 'calgary_data.db'
        self.output_path = Path(__file__).parent.parent / 'data' / 'market_overview.json'
        self.archive_path = Path(__file__).parent.parent / 'archive'
        
    def connect_db(self) -> sqlite3.Connection:
        """Connect to the Calgary data database."""
        return sqlite3.connect(self.db_path)
    
    def get_latest_housing_data(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get the latest month's housing data."""
        query = """
        SELECT 
            date,
            property_type,
            sales,
            new_listings,
            inventory,
            days_on_market,
            benchmark_price,
            median_price,
            average_price
        FROM housing_city_monthly
        WHERE date = (SELECT MAX(date) FROM housing_city_monthly)
        ORDER BY property_type
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        data = {}
        for row in results:
            date, prop_type, sales, listings, inventory, dom, benchmark, median, average = row
            data[prop_type.lower()] = {
                'sales': sales,
                'new_listings': listings,
                'inventory': inventory,
                'days_on_market': dom,
                'benchmark_price': benchmark,
                'median_price': median,
                'average_price': average
            }
        
        # Get the date
        if results:
            data['last_updated'] = results[0][0]
            
        return data
    
    def get_price_history(self, conn: sqlite3.Connection, months: int = 24) -> Dict[str, List]:
        """Get historical price data by property type."""
        query = """
        SELECT 
            date,
            property_type,
            benchmark_price
        FROM housing_city_monthly
        WHERE property_type != 'Total'
        ORDER BY date DESC, property_type
        LIMIT ?
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (months * 4,))  # 4 property types
        results = cursor.fetchall()
        
        # Organize by property type
        history = {}
        for date, prop_type, price in results:
            prop_type_lower = prop_type.lower().replace('_', '-')
            if prop_type_lower not in history:
                history[prop_type_lower] = []
            history[prop_type_lower].append({
                'date': date,
                'price': price
            })
        
        # Sort each by date ascending for charts
        for prop_type in history:
            history[prop_type].sort(key=lambda x: x['date'])
            
        return history
    
    def get_market_activity(self, conn: sqlite3.Connection, months: int = 12) -> Dict[str, List]:
        """Get sales volume and inventory for last N months."""
        query = """
        SELECT 
            date,
            sales,
            inventory
        FROM housing_city_monthly
        WHERE property_type = 'Total'
        ORDER BY date DESC
        LIMIT ?
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (months,))
        results = cursor.fetchall()
        
        sales_data = []
        inventory_data = []
        
        for date, sales, inventory in results:
            sales_data.append({'date': date, 'value': sales})
            inventory_data.append({'date': date, 'value': inventory})
        
        # Sort ascending for charts
        sales_data.sort(key=lambda x: x['date'])
        inventory_data.sort(key=lambda x: x['date'])
        
        return {
            'sales_volume': sales_data,
            'inventory': inventory_data
        }
    
    def calculate_changes(self, conn: sqlite3.Connection) -> Dict[str, float]:
        """Calculate MoM and YoY changes for key metrics."""
        # Get current, last month, and last year data
        query = """
        SELECT 
            date,
            benchmark_price,
            sales,
            inventory
        FROM housing_city_monthly
        WHERE property_type = 'Total'
        ORDER BY date DESC
        LIMIT 13  -- Need 13 months for YoY
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        
        changes = {}
        
        if len(results) >= 2:
            # MoM changes
            current = results[0]
            last_month = results[1]
            
            changes['price_change_mom'] = ((current[1] - last_month[1]) / last_month[1]) * 100
            changes['sales_change_mom'] = ((current[2] - last_month[2]) / last_month[2]) * 100
            changes['inventory_change_mom'] = ((current[3] - last_month[3]) / last_month[3]) * 100
        
        if len(results) >= 13:
            # YoY changes
            current = results[0]
            last_year = results[12]
            
            changes['price_change_yoy'] = ((current[1] - last_year[1]) / last_year[1]) * 100
            changes['sales_change_yoy'] = ((current[2] - last_year[2]) / last_year[2]) * 100
            changes['inventory_change_yoy'] = ((current[3] - last_year[3]) / last_year[3]) * 100
            
        return changes
    
    def get_market_drivers(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get population, housing starts, and other key drivers."""
        drivers = {}
        
        # Get latest population
        query = """
        SELECT value, date 
        FROM economic_indicators_monthly 
        WHERE indicator_name LIKE '%Population%' 
        ORDER BY date DESC 
        LIMIT 13
        """
        cursor = conn.cursor()
        cursor.execute(query)
        pop_results = cursor.fetchall()
        
        if pop_results:
            current_pop = pop_results[0][0]
            drivers['population'] = {
                'value': int(current_pop * 1000) if current_pop < 10000 else int(current_pop),  # Convert if needed
                'formatted': f"{current_pop:.1f}M" if current_pop < 10000 else f"{int(current_pop):,}"
            }
            
            # Calculate YoY growth if we have 13 months
            if len(pop_results) >= 13:
                last_year_pop = pop_results[12][0]
                pop_growth = ((current_pop - last_year_pop) / last_year_pop) * 100
                drivers['population']['change_yoy'] = round(pop_growth, 1)
        
        # Get latest housing starts
        query = """
        SELECT value, date 
        FROM economic_indicators_monthly 
        WHERE indicator_name LIKE '%Housing Starts%' 
        ORDER BY date DESC 
        LIMIT 2
        """
        cursor.execute(query)
        starts_results = cursor.fetchall()
        
        if starts_results:
            current_starts = starts_results[0][0]
            drivers['housing_starts'] = {
                'value': int(current_starts),
                'formatted': f"{int(current_starts):,}"
            }
            
            # Calculate MoM change
            if len(starts_results) >= 2:
                last_month_starts = starts_results[1][0]
                starts_change = ((current_starts - last_month_starts) / last_month_starts) * 100
                drivers['housing_starts']['change_mom'] = round(starts_change, 1)
        
        return drivers
    
    def get_interest_rates(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get current interest rates."""
        rates = {}
        
        # Bank of Canada rate
        query = """
        SELECT value 
        FROM economic_indicators_monthly 
        WHERE indicator_name LIKE '%Bank of Canada Interest Rate%' 
        ORDER BY date DESC 
        LIMIT 1
        """
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            rates['bank_of_canada'] = result[0]
            
        # Prime rate
        query = """
        SELECT value 
        FROM economic_indicators_monthly 
        WHERE indicator_name LIKE '%Prime Lending Rate%' 
        ORDER BY date DESC 
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            rates['prime'] = result[0]
            
        # Placeholder for mortgage rates (to be updated manually)
        rates['five_year_fixed'] = 6.95  # Placeholder from spec
        
        return rates
    
    def calculate_months_of_inventory(self, sales: int, inventory: int) -> Optional[float]:
        """Calculate months of inventory."""
        if sales and sales > 0:
            return round(inventory / sales, 1)
        return None
    
    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate dynamic insights based on current data."""
        insights = []
        
        # First-time buyer insight
        if 'apartment' in data['current_data']:
            apt_price = data['current_data']['apartment']['benchmark_price']
            insights.append({
                'target': 'first_time_buyers',
                'text': f"Apartments at ${apt_price:,.0f} offer most affordable entry"
            })
        
        # Current owner insight
        if 'changes' in data and 'price_change_yoy' in data['changes']:
            yoy_change = data['changes']['price_change_yoy']
            insights.append({
                'target': 'current_owners',
                'text': f"Home values {'up' if yoy_change > 0 else 'down'} {abs(yoy_change):.1f}% year-over-year"
            })
        
        # Investor insight
        if 'current_data' in data and 'total' in data['current_data']:
            total_data = data['current_data']['total']
            moi = self.calculate_months_of_inventory(
                total_data['sales'], 
                total_data['inventory']
            )
            if moi:
                market_type = "balanced" if 2 <= moi <= 4 else "seller's" if moi < 2 else "buyer's"
                insights.append({
                    'target': 'investors',
                    'text': f"{moi} months inventory = {market_type} market conditions"
                })
        
        return insights
    
    def generate(self) -> None:
        """Generate the market overview JSON file."""
        logger.info("🏠 Generating market overview data...")
        
        try:
            conn = self.connect_db()
            
            # Gather all data
            current_data = self.get_latest_housing_data(conn)
            price_history = self.get_price_history(conn)
            market_activity = self.get_market_activity(conn)
            changes = self.calculate_changes(conn)
            market_drivers = self.get_market_drivers(conn)
            interest_rates = self.get_interest_rates(conn)
            
            # Build the output structure
            output = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'data_last_updated': current_data.get('last_updated', ''),
                    'version': '1.0'
                },
                'current_data': current_data,
                'price_history': price_history,
                'market_activity': market_activity,
                'changes': changes,
                'market_drivers': market_drivers,
                'interest_rates': interest_rates,
                'insights': self.generate_insights({
                    'current_data': current_data,
                    'changes': changes
                })
            }
            
            # Archive previous version if exists
            if self.output_path.exists():
                archive_dir = self.archive_path / datetime.now().strftime('%Y-%m')
                archive_dir.mkdir(parents=True, exist_ok=True)
                archive_file = archive_dir / f"market_overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.output_path.rename(archive_file)
                logger.info(f"📦 Archived previous version to {archive_file}")
            
            # Save the new file
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w') as f:
                json.dump(output, f, indent=2)
                
            logger.info(f"✅ Market overview generated: {self.output_path}")
            
            # Print summary
            print("\n📊 MARKET OVERVIEW EXPORT SUMMARY")
            print("="*50)
            print(f"Last data update: {current_data.get('last_updated', 'Unknown')}")
            print(f"Property types: {len([k for k in current_data.keys() if k != 'last_updated'])}")
            print(f"Price history months: {len(price_history.get('detached', []))}")
            print(f"Market activity months: {len(market_activity.get('sales_volume', []))}")
            print(f"Insights generated: {len(output['insights'])}")
            print(f"\n📂 Output: {self.output_path}")
            print(f"📂 View: file://{self.output_path.absolute()}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error generating market overview: {e}")
            raise

def main():
    """Generate market overview export."""
    generator = MarketOverviewGenerator()
    generator.generate()

if __name__ == "__main__":
    main()