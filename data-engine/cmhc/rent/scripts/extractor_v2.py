#!/usr/bin/env python3
"""
CMHC Rental Market Data Extractor V2
Improved version that extracts all available Calgary rental market data
"""

import pandas as pd
import numpy as np
import sys
import os
import json
from datetime import datetime
import re
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Define validation directory directly
VALIDATION_PENDING_DIR = "/home/chris/calgary-analytica/data-engine/validation/pending"

class Config:
    VALIDATION_PENDING_DIR = VALIDATION_PENDING_DIR

config = Config()

class CMHCRentalExtractorV2:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.year = self.extract_year_from_filename()
        self.data = []
        self.confidence_scores = {}
        
    def extract_year_from_filename(self):
        """Extract year from filename like 'rmr-alberta-2024-en.xlsx'"""
        match = re.search(r'(\d{4})', self.file_name)
        if match:
            return int(match.group(1))
        raise ValueError(f"Could not extract year from filename: {self.file_name}")
    
    def clean_value(self, value):
        """Clean and parse a cell value"""
        if pd.isna(value):
            return None, None
            
        value_str = str(value).strip()
        
        # Handle special cases
        if value_str in ['**', 'n/a', '-', '']:
            return None, None
        
        # Extract quality indicator if present
        quality = None
        if value_str and value_str[-1] in ['a', 'b', 'c', 'd']:
            quality = value_str[-1]
            value_str = value_str[:-1].strip()
        
        # Clean numeric value
        value_str = value_str.replace(',', '').replace('$', '').strip()
        
        try:
            return float(value_str), quality
        except:
            return None, quality
    
    def extract_table_1_1_1(self, xl_file):
        """Extract vacancy rates for private apartments"""
        print("Extracting Table 1.1.1 - Private Apartment Vacancy Rates...")
        
        try:
            df = xl_file.parse('Table 1.1.1', header=None)
            
            # Find Calgary row
            for idx, row in df.iterrows():
                if 'Calgary CMA' in str(row.iloc[0]):
                    # Headers are in rows 5-6
                    # Row 5: Bachelor, 1 Bedroom, 2 Bedroom, 3 Bedroom+, Total
                    # Row 6: Oct-23, Oct-24 for each bedroom type
                    
                    # Column mapping (approximate, may need adjustment)
                    columns = [
                        (1, 3, 'Bachelor'),      # Oct-23, Oct-24
                        (6, 8, '1 Bedroom'),     
                        (11, 13, '2 Bedroom'),   
                        (16, 18, '3 Bedroom+'),  
                        (21, 23, 'Total')        
                    ]
                    
                    for prev_col, curr_col, bedroom_type in columns:
                        # Previous year (2023)
                        prev_val, prev_qual = self.clean_value(row.iloc[prev_col])
                        if prev_val is not None:
                            self.data.append({
                                'date': f"{self.year-1}-10-01",
                                'year': self.year - 1,
                                'property_type': 'apartment',
                                'metric_type': 'vacancy_rate',
                                'bedroom_type': bedroom_type,
                                'value': prev_val,
                                'quality_indicator': prev_qual,
                                'unit': 'percent'
                            })
                        
                        # Current year (2024)
                        curr_val, curr_qual = self.clean_value(row.iloc[curr_col])
                        if curr_val is not None:
                            self.data.append({
                                'date': f"{self.year}-10-01",
                                'year': self.year,
                                'property_type': 'apartment',
                                'metric_type': 'vacancy_rate',
                                'bedroom_type': bedroom_type,
                                'value': curr_val,
                                'quality_indicator': curr_qual,
                                'unit': 'percent'
                            })
                            self.confidence_scores[f'apt_vacancy_{bedroom_type}'] = 95.0 if curr_qual in ['a', 'b'] else 85.0
                    break
                    
        except Exception as e:
            print(f"Error in Table 1.1.1: {e}")
    
    def extract_table_1_1_2(self, xl_file):
        """Extract average rents for private apartments"""
        print("Extracting Table 1.1.2 - Private Apartment Average Rents...")
        
        try:
            df = xl_file.parse('Table 1.1.2', header=None)
            
            # Find Calgary row
            for idx, row in df.iterrows():
                if 'Calgary CMA' in str(row.iloc[0]):
                    # Based on the structure shown, columns are:
                    # Bachelor: cols 1-4 (Oct-23 val/qual, Oct-24 val/qual)
                    # 1 Bedroom: cols 5-8
                    # 2 Bedroom: cols 9-12
                    # 3 Bedroom+: cols 13-16
                    # Total: cols 17-20
                    
                    bedroom_configs = [
                        (1, 'Bachelor'),
                        (5, '1 Bedroom'),
                        (9, '2 Bedroom'),
                        (13, '3 Bedroom+'),
                        (17, 'Total')
                    ]
                    
                    for start_col, bedroom_type in bedroom_configs:
                        # Previous year
                        prev_val, prev_qual = self.clean_value(row.iloc[start_col])
                        if prev_val is not None:
                            self.data.append({
                                'date': f"{self.year-1}-10-01",
                                'year': self.year - 1,
                                'property_type': 'apartment',
                                'metric_type': 'average_rent',
                                'bedroom_type': bedroom_type,
                                'value': int(prev_val),
                                'quality_indicator': prev_qual or row.iloc[start_col + 1] if pd.notna(row.iloc[start_col + 1]) and str(row.iloc[start_col + 1]) in ['a','b','c','d'] else None,
                                'unit': 'dollars'
                            })
                        
                        # Current year
                        curr_val, curr_qual = self.clean_value(row.iloc[start_col + 2])
                        if curr_val is not None:
                            self.data.append({
                                'date': f"{self.year}-10-01",
                                'year': self.year,
                                'property_type': 'apartment',
                                'metric_type': 'average_rent',
                                'bedroom_type': bedroom_type,
                                'value': int(curr_val),
                                'quality_indicator': curr_qual or row.iloc[start_col + 3] if pd.notna(row.iloc[start_col + 3]) and str(row.iloc[start_col + 3]) in ['a','b','c','d'] else None,
                                'unit': 'dollars'
                            })
                            self.confidence_scores[f'apt_rent_{bedroom_type}'] = 95.0 if curr_qual in ['a', 'b'] else 85.0
                    break
                    
        except Exception as e:
            print(f"Error in Table 1.1.2: {e}")
    
    def extract_table_1_1_3(self, xl_file):
        """Extract rental universe for private apartments"""
        print("Extracting Table 1.1.3 - Private Apartment Rental Universe...")
        
        try:
            df = xl_file.parse('Table 1.1.3', header=None)
            
            for idx, row in df.iterrows():
                if 'Calgary CMA' in str(row.iloc[0]):
                    # Similar structure to other tables
                    bedroom_configs = [
                        (1, 'Bachelor'),
                        (5, '1 Bedroom'), 
                        (9, '2 Bedroom'),
                        (13, '3 Bedroom+'),
                        (17, 'Total')
                    ]
                    
                    for start_col, bedroom_type in bedroom_configs:
                        try:
                            # Current year only for universe (it's the stock of units)
                            # Table 1.1.3 has different column layout - only current year data
                            if start_col + 1 < len(row):
                                curr_val, curr_qual = self.clean_value(row.iloc[start_col])
                                if curr_val is not None:
                                    self.data.append({
                                        'date': f"{self.year}-10-01",
                                        'year': self.year,
                                        'property_type': 'apartment',
                                        'metric_type': 'rental_universe',
                                        'bedroom_type': bedroom_type,
                                        'value': int(curr_val),
                                        'quality_indicator': curr_qual,
                                        'unit': 'units'
                                    })
                                    self.confidence_scores[f'apt_universe_{bedroom_type}'] = 95.0
                        except IndexError:
                            continue
                    break
                    
        except Exception as e:
            print(f"Error in Table 1.1.3: {e}")
    
    def extract_table_2_series(self, xl_file):
        """Extract data for private row (townhouse) - Tables 2.1.1, 2.1.2, 2.1.3"""
        print("Extracting Tables 2.1.x - Private Row (Townhouse) Data...")
        
        # Similar structure to apartment tables but for townhouses
        table_configs = [
            ('Table 2.1.1', 'vacancy_rate', 'percent'),
            ('Table 2.1.2', 'average_rent', 'dollars'),
            ('Table 2.1.3', 'rental_universe', 'units')
        ]
        
        for table_name, metric_type, unit in table_configs:
            try:
                if table_name in xl_file.sheet_names:
                    df = xl_file.parse(table_name, header=None)
                    
                    for idx, row in df.iterrows():
                        if 'Calgary CMA' in str(row.iloc[0]):
                            # Townhouses typically have fewer bedroom types
                            # Often just 1 Bedroom, 2 Bedroom, 3 Bedroom+, Total
                            self.extract_row_data(row, 'townhouse', metric_type, unit)
                            break
            except Exception as e:
                print(f"Error in {table_name}: {e}")
    
    def extract_table_4_1_2(self, xl_file):
        """Extract rental condo rents only (skip apartment comparison data)"""
        print("Extracting Table 4.1.2 - Rental Condo Rents...")
        
        try:
            df = xl_file.parse('Table 4.1.2', header=None)
            
            for idx, row in df.iterrows():
                if 'Calgary CMA' in str(row.iloc[0]):
                    # This table compares rental condos with purpose-built rentals
                    # We only want the rental condo data, not the duplicate apartment data
                    
                    configs = [
                        (1, 'Bachelor'),      # Condo col 1
                        (6, '1 Bedroom'),     # Condo col 6
                        (11, '2 Bedroom'),    # Condo col 11
                        (16, '3 Bedroom+')    # Condo col 16
                    ]
                    
                    for condo_col, bedroom_type in configs:
                        # Rental condo only
                        condo_val, condo_qual = self.clean_value(row.iloc[condo_col])
                        if condo_val is not None:
                            self.data.append({
                                'date': f"{self.year}-10-01",
                                'year': self.year,
                                'property_type': 'rental_condo',
                                'metric_type': 'average_rent',
                                'bedroom_type': bedroom_type,
                                'value': int(condo_val),
                                'quality_indicator': condo_qual,
                                'unit': 'dollars'
                            })
                    break
                    
        except Exception as e:
            print(f"Error in Table 4.1.2: {e}")
    
    def extract_row_data(self, row, property_type, metric_type, unit):
        """Generic method to extract data from a row"""
        # This is a simplified version - actual column mapping would need refinement
        bedroom_configs = [
            (5, '1 Bedroom'),
            (9, '2 Bedroom'),
            (13, '3 Bedroom+'),
            (17, 'Total')
        ]
        
        for start_col, bedroom_type in bedroom_configs:
            try:
                curr_val, curr_qual = self.clean_value(row.iloc[start_col + 2])
                if curr_val is not None:
                    value = int(curr_val) if unit == 'dollars' or unit == 'units' else curr_val
                    self.data.append({
                        'date': f"{self.year}-10-01",
                        'year': self.year,
                        'property_type': property_type,
                        'metric_type': metric_type,
                        'bedroom_type': bedroom_type,
                        'value': value,
                        'quality_indicator': curr_qual,
                        'unit': unit
                    })
            except:
                continue
    
    def extract(self):
        """Main extraction method"""
        print(f"\nProcessing: {self.file_name}")
        print(f"Year: {self.year}")
        
        try:
            xl_file = pd.ExcelFile(self.file_path)
            
            # Extract apartment data (Tables 1.x.x)
            self.extract_table_1_1_1(xl_file)  # Vacancy rates
            self.extract_table_1_1_2(xl_file)  # Average rents
            self.extract_table_1_1_3(xl_file)  # Rental universe
            
            # Extract townhouse data (Tables 2.x.x)
            self.extract_table_2_series(xl_file)
            
            # Extract rental condo data (Table 4.1.2)
            self.extract_table_4_1_2(xl_file)
            
            print(f"Extracted {len(self.data)} records")
            
            return self.format_output()
            
        except Exception as e:
            print(f"Error processing file: {e}")
            raise
    
    def format_output(self):
        """Format extracted data for validation pipeline"""
        if not self.data:
            return None
        
        # Create DataFrame
        df = pd.DataFrame(self.data)
        
        # Calculate overall confidence
        if self.confidence_scores:
            overall_confidence = np.mean(list(self.confidence_scores.values()))
        else:
            overall_confidence = 85.0
        
        # Prepare output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"cmhc_rental_{self.year}_{timestamp}"
        
        # Save to validation pending
        csv_path = os.path.join(config.VALIDATION_PENDING_DIR, f"{output_filename}.csv")
        df.to_csv(csv_path, index=False)
        print(f"Saved CSV: {csv_path}")
        
        # Create validation report
        # Convert tuple keys to strings for JSON serialization
        metrics_summary = {}
        for (prop_type, metric), count in df.groupby(['property_type', 'metric_type'])['value'].count().items():
            key = f"{prop_type}_{metric}"
            metrics_summary[key] = int(count)
        
        report = {
            "source_file": self.file_name,
            "year": self.year,
            "extraction_timestamp": datetime.now().isoformat(),
            "total_records": len(df),
            "confidence_score": round(overall_confidence, 2),
            "confidence_details": self.confidence_scores,
            "property_types": sorted(df['property_type'].unique().tolist()),
            "metrics_summary": metrics_summary,
            "years_extracted": sorted(df['year'].unique().tolist()),
            "bedroom_types": sorted(df['bedroom_type'].unique().tolist()),
            "output_file": f"{output_filename}.csv"
        }
        
        # Save JSON report
        json_path = os.path.join(config.VALIDATION_PENDING_DIR, f"{output_filename}.json")
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Saved JSON report: {json_path}")
        
        # Print summary
        print("\nExtraction Summary:")
        print(f"Property types: {[pt for pt in report['property_types'] if pt != 'apartment_comparison']}")
        print(f"Years: {report['years_extracted']}")
        print(f"Metrics breakdown:")
        for key, count in report['metrics_summary'].items():
            print(f"  {key}: {count} records")
        
        return csv_path, json_path


def main():
    """Process CMHC rental files"""
    if len(sys.argv) > 1:
        # Process specific file
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        
        extractor = CMHCRentalExtractorV2(file_path)
        extractor.extract()
    else:
        # Process all files in raw directory
        raw_dir = "/home/chris/calgary-analytica/data-engine/cmhc/rent/raw"
        files = sorted([f for f in os.listdir(raw_dir) if f.endswith('.xlsx')])
        
        print(f"Found {len(files)} CMHC rental files to process")
        
        for file_name in files:
            file_path = os.path.join(raw_dir, file_name)
            try:
                extractor = CMHCRentalExtractorV2(file_path)
                extractor.extract()
                print("-" * 50)
            except Exception as e:
                print(f"Failed to process {file_name}: {e}")
                continue


if __name__ == "__main__":
    main()