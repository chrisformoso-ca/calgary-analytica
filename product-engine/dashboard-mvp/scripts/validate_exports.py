#!/usr/bin/env python3
"""
Validate Dashboard JSON Exports
Ensures all exports meet MVP specification requirements
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import sys

class ExportValidator:
    """Validate dashboard JSON exports against requirements."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.errors = []
        self.warnings = []
    
    def validate_market_overview(self, data: Dict) -> None:
        """Validate market_overview.json structure."""
        required_keys = ['metadata', 'current_data', 'price_history', 'market_activity', 'changes']
        
        # Check top-level keys
        for key in required_keys:
            if key not in data:
                self.errors.append(f"market_overview: Missing required key '{key}'")
        
        # Check property types in current_data
        if 'current_data' in data:
            expected_types = ['apartment', 'detached', 'row', 'semi_detached', 'total']
            for prop_type in expected_types:
                if prop_type not in data['current_data']:
                    self.errors.append(f"market_overview: Missing property type '{prop_type}'")
        
        # Check if we have 24 months of history
        if 'price_history' in data and 'detached' in data['price_history']:
            months = len(data['price_history']['detached'])
            if months < 24:
                self.warnings.append(f"market_overview: Only {months} months of price history (spec requires 24)")
    
    def validate_economic_indicators(self, data: Dict) -> None:
        """Validate economic_indicators.json structure."""
        required_keys = ['metadata', 'indicators', 'categories']
        
        for key in required_keys:
            if key not in data:
                self.errors.append(f"economic_indicators: Missing required key '{key}'")
        
        # Check for key indicators mentioned in spec
        if 'indicators' in data:
            key_indicators = [
                'unemployment_rate',
                'population',
                'inflation_calgary',
                'oil_price',
                'housing_starts'
            ]
            
            for indicator in key_indicators:
                if indicator not in data['indicators']:
                    self.warnings.append(f"economic_indicators: Missing indicator '{indicator}'")
            
            # Check for placeholders
            for key, value in data['indicators'].items():
                if 'note' in value and 'placeholder' in value['note'].lower():
                    self.warnings.append(f"economic_indicators: '{key}' is a placeholder")
    
    def validate_district_data(self, data: Dict) -> None:
        """Validate district_data.json structure."""
        required_keys = ['metadata', 'current_data', 'pricing_table', 'best_value']
        
        for key in required_keys:
            if key not in data:
                self.errors.append(f"district_data: Missing required key '{key}'")
        
        # Check district count (should be 8)
        if 'current_data' in data:
            district_count = len(data['current_data'])
            if district_count != 8:
                self.warnings.append(f"district_data: Found {district_count} districts (expected 8)")
        
        # Check pricing table structure
        if 'pricing_table' in data and len(data['pricing_table']) > 0:
            expected_cols = ['district', 'detached', 'semi_detached', 'row_house', 'apartment']
            sample_row = data['pricing_table'][0]
            for col in expected_cols:
                if col not in sample_row:
                    self.errors.append(f"district_data: Pricing table missing column '{col}'")
    
    def validate_rate_data(self, data: Dict) -> None:
        """Validate rate_data.json structure."""
        required_keys = ['metadata', 'current_rates', 'rate_history', 'payment_scenarios']
        
        for key in required_keys:
            if key not in data:
                self.errors.append(f"rate_data: Missing required key '{key}'")
        
        # Check current rates
        if 'current_rates' in data:
            expected_rates = ['bank_of_canada', 'prime', 'mortgage']
            for rate in expected_rates:
                if rate not in data['current_rates']:
                    self.errors.append(f"rate_data: Missing rate type '{rate}'")
        
        # Check payment scenarios
        if 'payment_scenarios' in data:
            scenario_count = len(data['payment_scenarios'])
            if scenario_count < 12:
                self.warnings.append(f"rate_data: Only {scenario_count} payment scenarios (12+ recommended)")
    
    def validate_metadata(self, data: Dict) -> None:
        """Validate metadata.json structure."""
        required_keys = ['metadata', 'data_freshness', 'exported_files', 'known_issues']
        
        for key in required_keys:
            if key not in data:
                self.errors.append(f"metadata: Missing required key '{key}'")
        
        # Check if all exports are tracked
        if 'exported_files' in data:
            expected_files = ['market_overview', 'economic_indicators', 'district_data', 'rate_data']
            for file_key in expected_files:
                if file_key not in data['exported_files']:
                    self.errors.append(f"metadata: Missing export tracking for '{file_key}'")
    
    def check_file_sizes(self) -> None:
        """Check if file sizes are reasonable."""
        max_size_mb = 1.0  # 1MB max per file
        
        for json_file in self.data_dir.glob('*.json'):
            size_mb = json_file.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                self.warnings.append(f"{json_file.name}: Large file size ({size_mb:.2f}MB)")
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validations and return results."""
        validators = {
            'market_overview.json': self.validate_market_overview,
            'economic_indicators.json': self.validate_economic_indicators,
            'district_data.json': self.validate_district_data,
            'rate_data.json': self.validate_rate_data,
            'metadata.json': self.validate_metadata
        }
        
        # Validate each file
        for filename, validator in validators.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                self.errors.append(f"{filename}: File not found")
                continue
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                validator(data)
            except json.JSONDecodeError as e:
                self.errors.append(f"{filename}: Invalid JSON - {e}")
            except Exception as e:
                self.errors.append(f"{filename}: Validation error - {e}")
        
        # Check file sizes
        self.check_file_sizes()
        
        return len(self.errors) == 0, self.errors, self.warnings

def main():
    """Run validation and report results."""
    validator = ExportValidator()
    success, errors, warnings = validator.validate_all()
    
    print("=" * 70)
    print("📋 DASHBOARD EXPORT VALIDATION REPORT")
    print("=" * 70)
    
    if success:
        print("✅ All validations passed!")
    else:
        print(f"❌ Found {len(errors)} errors")
    
    if warnings:
        print(f"⚠️  Found {len(warnings)} warnings")
    
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if success and not warnings:
        print("\n🎉 All exports are ready for use with Claude Artifacts!")
    
    print("\n📂 Export directory:", Path(__file__).parent.parent / 'data')
    print("=" * 70)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())