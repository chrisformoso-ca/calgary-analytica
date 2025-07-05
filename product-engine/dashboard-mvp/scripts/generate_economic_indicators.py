#!/usr/bin/env python3
"""
Generate Economic Indicators JSON for Calgary Housing Dashboard MVP
Outputs economic_indicators.json with all economic metrics and trends
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EconomicIndicatorsGenerator:
    """Generate economic indicators data for dashboard."""
    
    def __init__(self):
        self.db_path = Path(__file__).parents[3] / 'data-lake' / 'calgary_data.db'
        self.output_path = Path(__file__).parent.parent / 'data' / 'economic_indicators.json'
        self.archive_path = Path(__file__).parent.parent / 'archive'
        
        # Map database indicator names to clean display names
        self.indicator_mappings = {
            'employment': {
                'db_pattern': 'Employment - CER%',
                'display_name': 'Employment (Calgary Economic Region)',
                'unit': 'thousands',
                'category': 'labour_market'
            },
            'avg_hourly_wage_calgary': {
                'db_pattern': 'avg_hourly_wage_calgary',
                'display_name': 'Avg Hourly Wage Growth (Calgary)',
                'unit': 'percent',
                'category': 'labour_market',
                'is_yoy_change': True
            },
            'unemployment_rate': {
                'db_pattern': 'Unemployment Rate - Calgary Economic Region%',
                'display_name': 'Unemployment Rate',
                'unit': 'percent',
                'category': 'labour_market'
            },
            'unemployment_rate_canada': {
                'db_pattern': 'Unemployment Rate - Canada%',
                'display_name': 'Unemployment Rate (Canada)',
                'unit': 'percent',
                'category': 'labour_market'
            },
            'population': {
                'db_pattern': 'City of Calgary Population%',
                'display_name': 'Calgary Population',
                'unit': 'thousands',
                'category': 'demographics'
            },
            'inflation_calgary': {
                'db_pattern': 'Inflation Rate - Calgary CMA%',
                'display_name': 'Inflation Rate (Calgary)',
                'unit': 'percent',
                'category': 'prices'
            },
            'inflation_canada': {
                'db_pattern': 'Inflation Rate - Canada%',
                'display_name': 'Inflation Rate (Canada)',
                'unit': 'percent',
                'category': 'prices'
            },
            'oil_price': {
                'db_pattern': 'West Texas Intermediate%',
                'display_name': 'Oil Price (WTI)',
                'unit': 'USD/barrel',
                'category': 'energy'
            },
            'natural_gas': {
                'db_pattern': 'Alberta Natural Gas%',
                'display_name': 'Natural Gas Price',
                'unit': 'CAD/GJ',
                'category': 'energy'
            },
            'housing_starts': {
                'db_pattern': 'Housing Starts - Calgary%',
                'display_name': 'Housing Starts',
                'unit': 'units',
                'category': 'construction'
            },
            'building_permits': {
                'db_pattern': 'City of Calgary Total Value of Building Permits%',
                'display_name': 'Building Permits Value',
                'unit': 'millions',
                'category': 'construction'
            },
            'retail_sales': {
                'db_pattern': 'Retail Sales - Alberta%',
                'display_name': 'Retail Sales (Alberta)',
                'unit': 'billions',
                'category': 'consumer'
            },
            'bankruptcies': {
                'db_pattern': 'Number of Personal Bankruptcies%',
                'display_name': 'Personal Bankruptcies (Alberta)',
                'unit': 'count',
                'category': 'financial_stress'
            },
            'gdp_growth': {
                'db_pattern': "Canada's Real GDP growth%",
                'display_name': 'GDP Growth (Canada)',
                'unit': 'percent',
                'category': 'economy'
            },
            'ei_beneficiaries_calgary': {
                'db_pattern': 'Employment insurance Calgary%',
                'display_name': 'EI Recipients (Calgary)',
                'unit': 'persons',
                'category': 'labour_market'
            },
            'ei_beneficiaries_alberta': {
                'db_pattern': 'Employment insurance Alberta%',
                'display_name': 'EI Recipients (Alberta)',
                'unit': 'persons',
                'category': 'labour_market'
            },
            'housing_starts_calgary': {
                'db_pattern': 'housing_starts',
                'display_name': 'Housing Starts (Calgary CMA)',
                'unit': 'units',
                'category': 'construction',
                'is_exact_match': True
            }
        }
    
    def connect_db(self) -> sqlite3.Connection:
        """Connect to the Calgary data database."""
        return sqlite3.connect(self.db_path)
    
    def get_indicator_data(self, conn: sqlite3.Connection, indicator_key: str, 
                          months: int = 24) -> Optional[Dict[str, Any]]:
        """Get data for a specific indicator."""
        mapping = self.indicator_mappings.get(indicator_key)
        if not mapping:
            return None
            
        # Use indicator_type for exact matches (like wage data)
        if mapping.get('is_yoy_change') or mapping.get('is_exact_match') or '%' not in mapping['db_pattern']:
            query = """
            SELECT date, value
            FROM economic_indicators_monthly
            WHERE indicator_type = ?
            ORDER BY date DESC
            LIMIT ?
            """
        else:
            query = """
            SELECT date, value
            FROM economic_indicators_monthly
            WHERE indicator_name LIKE ?
            ORDER BY date DESC
            LIMIT ?
            """
        
        cursor = conn.cursor()
        cursor.execute(query, (mapping['db_pattern'], months))
        results = cursor.fetchall()
        
        if not results:
            logger.warning(f"No data found for {indicator_key}")
            return None
        
        # Get current value and history
        current_value = results[0][1]
        
        # Build time series
        time_series = []
        for date, value in results:
            time_series.append({
                'date': date,
                'value': value
            })
        
        # Sort ascending for charts
        time_series.sort(key=lambda x: x['date'])
        
        # Calculate changes
        changes = {}
        
        # For YoY indicators, the value IS the year-over-year change
        if mapping.get('is_yoy_change'):
            changes['yoy'] = current_value  # The value itself is YoY%
            if len(results) >= 2:
                last_month_value = results[1][1]
                changes['mom'] = current_value - last_month_value  # Difference in YoY rates
        else:
            # For absolute values, calculate changes normally
            if len(results) >= 2:
                last_month_value = results[1][1]
                if last_month_value and last_month_value != 0:
                    changes['mom'] = ((current_value - last_month_value) / abs(last_month_value)) * 100
            
            if len(results) >= 13:
                last_year_value = results[12][1]
                if last_year_value and last_year_value != 0:
                    changes['yoy'] = ((current_value - last_year_value) / abs(last_year_value)) * 100
        
        return {
            'key': indicator_key,
            'display_name': mapping['display_name'],
            'current_value': current_value,
            'unit': mapping['unit'],
            'category': mapping['category'],
            'last_updated': results[0][0],
            'changes': changes,
            'time_series': time_series,
            'sparkline_data': [item['value'] for item in time_series[-12:]]  # Last 12 months for sparkline
        }
    
    def get_all_indicators(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get all economic indicators."""
        indicators = {}
        
        for key in self.indicator_mappings:
            data = self.get_indicator_data(conn, key)
            if data:
                indicators[key] = data
        
        return indicators
    
    def get_wage_data_placeholder(self) -> Dict[str, Any]:
        """Placeholder for wage data until extractor is updated."""
        return {
            'wage_growth': {
                'key': 'wage_growth',
                'display_name': 'Wage Growth (Calgary)',
                'current_value': 2.8,  # Placeholder from spec
                'unit': 'percent',
                'category': 'labour_market',
                'last_updated': '2025-05-01',
                'changes': {
                    'yoy': 2.8
                },
                'note': 'Placeholder - pending data extraction update',
                'time_series': [],
                'sparkline_data': []
            }
        }
    
    def get_money_supply_placeholder(self) -> Dict[str, Any]:
        """Placeholder for M2 money supply data."""
        return {
            'money_supply_m2': {
                'key': 'money_supply_m2',
                'display_name': 'Money Supply (M2)',
                'current_value': 4.2,  # Placeholder from spec
                'unit': 'percent_yoy',
                'category': 'monetary',
                'last_updated': '2025-03-01',
                'changes': {
                    'yoy': 4.2
                },
                'note': 'Placeholder - requires external data source',
                'time_series': [],
                'sparkline_data': []
            }
        }
    
    def categorize_indicators(self, indicators: Dict[str, Any]) -> Dict[str, List[str]]:
        """Group indicators by category."""
        categories = {}
        
        for key, data in indicators.items():
            category = data.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(key)
        
        return categories
    
    def calculate_employment_rate(self, indicators: Dict[str, Any]) -> Optional[float]:
        """Calculate employment rate from unemployment rate."""
        if 'unemployment_rate' in indicators:
            unemployment = indicators['unemployment_rate']['current_value']
            if unemployment is not None:
                # Convert percentage to employment rate
                return 100 - (unemployment * 100) if unemployment < 1 else 100 - unemployment
        return None
    
    def generate_context_notes(self, indicators: Dict[str, Any]) -> List[str]:
        """Generate contextual notes based on indicator values."""
        notes = []
        
        # Oil price context
        if 'oil_price' in indicators:
            oil_price = indicators['oil_price']['current_value']
            if oil_price < 60:
                notes.append("Oil prices below $60 may impact Calgary's economy")
            elif oil_price > 80:
                notes.append("Strong oil prices supporting economic growth")
        
        # Inflation context
        if 'inflation_calgary' in indicators:
            inflation = indicators['inflation_calgary']['current_value']
            if inflation > 3:
                notes.append("Inflation above Bank of Canada target range")
        
        # Housing starts vs population growth
        if 'housing_starts' in indicators and 'population' in indicators:
            if 'changes' in indicators['population'] and 'yoy' in indicators['population']['changes']:
                pop_growth = indicators['population']['changes']['yoy']
                if pop_growth > 2:
                    notes.append("Strong population growth driving housing demand")
        
        return notes
    
    def generate(self) -> None:
        """Generate the economic indicators JSON file."""
        logger.info("📊 Generating economic indicators data...")
        
        try:
            conn = self.connect_db()
            
            # Get all indicators from database
            indicators = self.get_all_indicators(conn)
            
            # Add placeholders for missing data (only money supply now)
            placeholders = {
                **self.get_money_supply_placeholder()
            }
            indicators.update(placeholders)
            
            # Calculate derived metrics
            employment_rate = self.calculate_employment_rate(indicators)
            
            # Categorize indicators
            categories = self.categorize_indicators(indicators)
            
            # Generate context notes
            context_notes = self.generate_context_notes(indicators)
            
            # Build output structure
            output = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'indicator_count': len(indicators),
                    'data_gaps': ['money_supply_m2']
                },
                'indicators': indicators,
                'categories': categories,
                'derived_metrics': {
                    'employment_rate': employment_rate
                },
                'context_notes': context_notes,
                'summary': {
                    'last_update_dates': {
                        key: data['last_updated'] 
                        for key, data in indicators.items() 
                        if 'last_updated' in data
                    }
                }
            }
            
            # Archive previous version if exists
            if self.output_path.exists():
                archive_dir = self.archive_path / datetime.now().strftime('%Y-%m')
                archive_dir.mkdir(parents=True, exist_ok=True)
                archive_file = archive_dir / f"economic_indicators_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.output_path.rename(archive_file)
                logger.info(f"📦 Archived previous version to {archive_file}")
            
            # Save the new file
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w') as f:
                json.dump(output, f, indent=2)
                
            logger.info(f"✅ Economic indicators generated: {self.output_path}")
            
            # Print summary
            print("\n📊 ECONOMIC INDICATORS EXPORT SUMMARY")
            print("="*50)
            print(f"Total indicators: {len(indicators)}")
            print(f"Categories: {', '.join(categories.keys())}")
            print(f"Data gaps: {', '.join(output['metadata']['data_gaps'])}")
            print(f"Context notes: {len(context_notes)}")
            
            # Show indicators by category
            print("\n📈 Indicators by Category:")
            for category, keys in categories.items():
                print(f"  {category}: {len(keys)} indicators")
                
            print(f"\n📂 Output: {self.output_path}")
            print(f"📂 View: file://{self.output_path.absolute()}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error generating economic indicators: {e}")
            raise

def main():
    """Generate economic indicators export."""
    generator = EconomicIndicatorsGenerator()
    generator.generate()

if __name__ == "__main__":
    main()