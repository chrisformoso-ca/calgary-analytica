#!/usr/bin/env python3
"""
Generate Rate Data JSON for Calgary Housing Dashboard MVP
Outputs rate_data.json with interest rates and mortgage calculations
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RateDataGenerator:
    """Generate interest rate data for dashboard."""
    
    def __init__(self):
        self.db_path = Path(__file__).parents[3] / 'data-lake' / 'calgary_data.db'
        self.output_path = Path(__file__).parent.parent / 'data' / 'rate_data.json'
        self.archive_path = Path(__file__).parent.parent / 'archive'
        
        # Manual mortgage rates (to be updated monthly)
        # These are placeholders until we have a data source
        self.mortgage_rates = {
            'five_year_fixed': 6.95,
            'three_year_fixed': 6.75,
            'variable': 6.70,  # Typically Prime - 0.50
            'last_updated': '2025-07-01'
        }
    
    def connect_db(self) -> sqlite3.Connection:
        """Connect to the Calgary data database."""
        return sqlite3.connect(self.db_path)
    
    def get_rate_history(self, conn: sqlite3.Connection, months: int = 60) -> Dict[str, List]:
        """Get historical rate data (5 years)."""
        # Bank of Canada rate
        query = """
        SELECT date, value
        FROM economic_indicators_monthly
        WHERE indicator_name LIKE '%Bank of Canada Interest Rate%'
        ORDER BY date DESC
        LIMIT ?
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (months,))
        boc_results = cursor.fetchall()
        
        # Prime rate
        query = """
        SELECT date, value
        FROM economic_indicators_monthly
        WHERE indicator_name LIKE '%Prime Lending Rate%'
        ORDER BY date DESC
        LIMIT ?
        """
        
        cursor.execute(query, (months,))
        prime_results = cursor.fetchall()
        
        # Convert to time series format
        boc_history = []
        for date, value in boc_results:
            boc_history.append({'date': date, 'value': value})
        
        prime_history = []
        for date, value in prime_results:
            prime_history.append({'date': date, 'value': value})
        
        # Sort ascending for charts
        boc_history.sort(key=lambda x: x['date'])
        prime_history.sort(key=lambda x: x['date'])
        
        return {
            'bank_of_canada': boc_history,
            'prime_rate': prime_history
        }
    
    def get_current_rates(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get current interest rates."""
        rates = {}
        
        # Bank of Canada rate
        query = """
        SELECT value, date
        FROM economic_indicators_monthly
        WHERE indicator_name LIKE '%Bank of Canada Interest Rate%'
        ORDER BY date DESC
        LIMIT 1
        """
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            rates['bank_of_canada'] = {
                'value': result[0],
                'date': result[1]
            }
        
        # Prime rate
        query = """
        SELECT value, date
        FROM economic_indicators_monthly
        WHERE indicator_name LIKE '%Prime Lending Rate%'
        ORDER BY date DESC
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            rates['prime'] = {
                'value': result[0],
                'date': result[1]
            }
        
        # Add mortgage rates (manual for now)
        rates['mortgage'] = self.mortgage_rates
        
        return rates
    
    def calculate_mortgage_payment(self, principal: float, rate: float, 
                                 amortization_years: int = 25) -> Dict[str, float]:
        """Calculate monthly mortgage payment and total interest."""
        # Convert annual rate to monthly
        monthly_rate = (rate / 100) / 12
        num_payments = amortization_years * 12
        
        if monthly_rate > 0:
            # Standard mortgage payment formula
            payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / \
                     ((1 + monthly_rate)**num_payments - 1)
            
            total_paid = payment * num_payments
            total_interest = total_paid - principal
        else:
            # Handle zero interest rate
            payment = principal / num_payments
            total_paid = principal
            total_interest = 0
        
        return {
            'monthly_payment': round(payment, 2),
            'total_interest': round(total_interest, 2),
            'total_paid': round(total_paid, 2)
        }
    
    def generate_payment_scenarios(self) -> List[Dict[str, Any]]:
        """Generate common payment scenarios."""
        scenarios = []
        
        # Common home prices based on our data
        home_prices = [
            {'price': 300000, 'label': 'Entry Level'},
            {'price': 450000, 'label': 'Average Row House'},
            {'price': 600000, 'label': 'Average Overall'},
            {'price': 770000, 'label': 'Average Detached'}
        ]
        
        # Common down payment percentages
        down_payments = [5, 10, 20]
        
        for home in home_prices:
            price = home['price']
            
            for down_pct in down_payments:
                down_payment = price * (down_pct / 100)
                principal = price - down_payment
                
                # Calculate with current 5-year fixed rate
                calc = self.calculate_mortgage_payment(
                    principal, 
                    self.mortgage_rates['five_year_fixed']
                )
                
                scenario = {
                    'home_price': price,
                    'price_label': home['label'],
                    'down_payment_percent': down_pct,
                    'down_payment_amount': down_payment,
                    'mortgage_amount': principal,
                    'rate': self.mortgage_rates['five_year_fixed'],
                    'monthly_payment': calc['monthly_payment'],
                    'total_interest': calc['total_interest']
                }
                
                scenarios.append(scenario)
        
        return scenarios
    
    def calculate_stress_test(self, rate: float) -> float:
        """Calculate stress test rate (higher of rate + 2% or 5.25%)."""
        return max(rate + 2.0, 5.25)
    
    def get_rate_environment_summary(self, current_rates: Dict[str, Any], 
                                   history: Dict[str, List]) -> Dict[str, Any]:
        """Generate summary of current rate environment."""
        summary = {
            'current_environment': 'stable',  # placeholder
            'trend': 'stable',
            'historical_context': {}
        }
        
        # Calculate rate changes over different periods
        if 'bank_of_canada' in history and len(history['bank_of_canada']) > 0:
            current_boc = current_rates['bank_of_canada']['value']
            
            # 1 year ago
            if len(history['bank_of_canada']) >= 13:
                year_ago = history['bank_of_canada'][-13]['value']
                summary['historical_context']['one_year_change'] = current_boc - year_ago
            
            # 5 year average
            if len(history['bank_of_canada']) >= 60:
                five_year_avg = sum(r['value'] for r in history['bank_of_canada']) / len(history['bank_of_canada'])
                summary['historical_context']['five_year_average'] = round(five_year_avg, 2)
                summary['historical_context']['vs_five_year_avg'] = round(current_boc - five_year_avg, 2)
            
            # Determine trend
            if len(history['bank_of_canada']) >= 4:
                recent_rates = [r['value'] for r in history['bank_of_canada'][-4:]]
                if all(recent_rates[i] <= recent_rates[i+1] for i in range(len(recent_rates)-1)):
                    summary['trend'] = 'rising'
                elif all(recent_rates[i] >= recent_rates[i+1] for i in range(len(recent_rates)-1)):
                    summary['trend'] = 'falling'
        
        # Determine environment
        if current_rates['bank_of_canada']['value'] < 2:
            summary['current_environment'] = 'low'
        elif current_rates['bank_of_canada']['value'] > 4:
            summary['current_environment'] = 'high'
        else:
            summary['current_environment'] = 'moderate'
        
        return summary
    
    def generate_affordability_metrics(self) -> Dict[str, Any]:
        """Generate affordability metrics based on rates."""
        metrics = {}
        
        # Income required for different price points
        # Using standard 32% GDS ratio
        gds_ratio = 0.32
        
        price_points = [300000, 450000, 600000, 770000]
        
        for price in price_points:
            # Assume 20% down
            mortgage = price * 0.8
            payment = self.calculate_mortgage_payment(
                mortgage, 
                self.mortgage_rates['five_year_fixed']
            )['monthly_payment']
            
            # Add estimated property tax and heating
            property_tax = price * 0.01 / 12  # ~1% annually
            heating = 150  # Estimated
            
            total_housing_cost = payment + property_tax + heating
            required_income = (total_housing_cost * 12) / gds_ratio
            
            metrics[f'price_{price}'] = {
                'home_price': price,
                'monthly_payment': payment,
                'total_housing_cost': round(total_housing_cost, 2),
                'required_income': round(required_income, 0)
            }
        
        return metrics
    
    def generate(self) -> None:
        """Generate the rate data JSON file."""
        logger.info("💰 Generating rate data...")
        
        try:
            conn = self.connect_db()
            
            # Get current and historical rates
            current_rates = self.get_current_rates(conn)
            rate_history = self.get_rate_history(conn)
            
            # Generate payment scenarios
            payment_scenarios = self.generate_payment_scenarios()
            
            # Calculate stress test rates
            stress_test_rates = {
                'five_year_fixed': self.calculate_stress_test(self.mortgage_rates['five_year_fixed']),
                'variable': self.calculate_stress_test(self.mortgage_rates['variable'])
            }
            
            # Get rate environment summary
            rate_summary = self.get_rate_environment_summary(current_rates, rate_history)
            
            # Generate affordability metrics
            affordability = self.generate_affordability_metrics()
            
            # Build output structure
            output = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'mortgage_rates_updated': self.mortgage_rates['last_updated'],
                    'note': 'Mortgage rates are manually updated pending data source integration'
                },
                'current_rates': current_rates,
                'rate_history': rate_history,
                'payment_scenarios': payment_scenarios,
                'stress_test_rates': stress_test_rates,
                'rate_environment': rate_summary,
                'affordability_metrics': affordability,
                'calculator_defaults': {
                    'amortization_years': 25,
                    'payment_frequency': 'monthly',
                    'compound_frequency': 'semi-annual'
                }
            }
            
            # Archive previous version if exists
            if self.output_path.exists():
                archive_dir = self.archive_path / datetime.now().strftime('%Y-%m')
                archive_dir.mkdir(parents=True, exist_ok=True)
                archive_file = archive_dir / f"rate_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.output_path.rename(archive_file)
                logger.info(f"📦 Archived previous version to {archive_file}")
            
            # Save the new file
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, 'w') as f:
                json.dump(output, f, indent=2)
                
            logger.info(f"✅ Rate data generated: {self.output_path}")
            
            # Print summary
            print("\n💰 RATE DATA EXPORT SUMMARY")
            print("="*50)
            print(f"Bank of Canada Rate: {current_rates['bank_of_canada']['value']}%")
            print(f"Prime Rate: {current_rates['prime']['value']}%")
            print(f"5-Year Fixed (manual): {self.mortgage_rates['five_year_fixed']}%")
            print(f"Variable (manual): {self.mortgage_rates['variable']}%")
            print(f"\nPayment scenarios generated: {len(payment_scenarios)}")
            print(f"Historical data points: {len(rate_history['bank_of_canada'])}")
            print(f"Rate environment: {rate_summary['current_environment']}")
            print(f"Trend: {rate_summary['trend']}")
            
            print(f"\n📂 Output: {self.output_path}")
            print(f"📂 View: file://{self.output_path.absolute()}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error generating rate data: {e}")
            raise

def main():
    """Generate rate data export."""
    generator = RateDataGenerator()
    generator.generate()

if __name__ == "__main__":
    main()