#!/usr/bin/env python3
"""
Simplified Calgary CREB Data Extractor
Extracts both city-wide and district-level data from CREB PDF reports

Input: /data/raw/creb_pdfs/MM_YYYY_Calgary_Monthly_Stats_Package.pdf
Output: /validation/pending/[timestamp]/city_data.csv + district_data.csv
"""

import pandas as pd
import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import re
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CREBExtractor:
    """Simplified CREB data extractor."""
    
    def __init__(self, project_root: str = None):
        # Set project root
        if project_root:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path(__file__).parent
        
        # Set paths relative to project root
        self.pdf_directory = self.project_root / "data/raw/creb_pdfs"
        self.validation_dir = self.project_root / "validation/pending"
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        
        # Property type mappings (page numbers in PDF for city-wide data)
        self.property_types = {
            'Total': 11,
            'Detached': 13,
            'Semi_Detached': 15,
            'Apartment': 17,
            'Row': 19
        }
        
        logger.info(f"🏠 CREB Extractor initialized")
        logger.info(f"   PDFs: {self.pdf_directory}")
        logger.info(f"   Output: {self.validation_dir}")
    
    def find_latest_pdf(self) -> Optional[Path]:
        """Find the most recent Calgary PDF report."""
        latest_pdf = None
        latest_date = None
        
        for pdf_file in self.pdf_directory.glob("*_Calgary_Monthly_Stats_Package.pdf"):
            # Extract date from filename
            match = re.match(r"(\d{2})_(\d{4})_Calgary", pdf_file.name)
            if match:
                month, year = int(match.group(1)), int(match.group(2))
                pdf_date = datetime(year, month, 1)
                
                if latest_date is None or pdf_date > latest_date:
                    latest_date = pdf_date
                    latest_pdf = pdf_file
        
        if latest_pdf:
            logger.info(f"Latest PDF: {latest_pdf.name} ({latest_date.strftime('%Y-%m')})")
        else:
            logger.warning("No PDF reports found")
        
        return latest_pdf
    
    def extract_page_data(self, pdf_path: Path, page_num: int) -> Optional[str]:
        """Extract text from a specific page of the PDF."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) >= page_num:
                    page = pdf.pages[page_num - 1]  # 0-indexed
                    text = page.extract_text()
                    return text
                else:
                    logger.warning(f"PDF has only {len(pdf.pages)} pages, need page {page_num}")
                    return None
        except Exception as e:
            logger.error(f"Error extracting page {page_num} from {pdf_path.name}: {e}")
            return None
    
    def parse_property_type_data(self, text: str, property_type: str) -> List[Dict]:
        """Parse data for a specific property type from page text."""
        data = []
        lines = text.split('\n')
        
        # Find year sections and parse them
        current_year = None
        current_months = []
        metrics_data = {}
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Look for year header lines
            year_match = re.match(r'^(20\d{2})\s+(.+)', line)
            if year_match:
                # Process previous year's data if exists
                if current_year and current_months and metrics_data:
                    year_records = self._build_monthly_records_for_type(
                        current_year, current_months, metrics_data, property_type
                    )
                    data.extend(year_records)
                
                # Start new year
                current_year = int(year_match.group(1))
                dates_part = year_match.group(2)
                
                # Extract months from dates
                dates = re.findall(r'(\d{2})/\d{2}/\d{2}', dates_part)
                current_months = [int(d) for d in dates if 1 <= int(d) <= 12]
                metrics_data = {}
                
                logger.debug(f"Found year {current_year} with {len(current_months)} months for {property_type}")
                continue
            
            # Parse metric lines
            if current_year and current_months:
                metric_name, values = self._parse_metric_line(line, len(current_months))
                if metric_name and values:
                    metrics_data[metric_name] = values
        
        # Process final year
        if current_year and current_months and metrics_data:
            year_records = self._build_monthly_records_for_type(
                current_year, current_months, metrics_data, property_type
            )
            data.extend(year_records)
        
        logger.debug(f"Extracted {len(data)} records for {property_type}")
        return data
    
    def _parse_metric_line(self, line: str, expected_count: int) -> Tuple[Optional[str], Optional[List[int]]]:
        """Parse a metric line to extract values."""
        
        # Map line patterns to field names (matching CSV structure)
        if line.startswith('Sales '):
            metric_name = 'Sales'
            data_part = line[6:].strip()
        elif line.startswith('New Listings '):
            metric_name = 'New_Listings'
            data_part = line[13:].strip()
        elif line.startswith('Inventory '):
            metric_name = 'Inventory'
            data_part = line[10:].strip()
        elif line.startswith('Days on Market '):
            metric_name = 'Days_on_Market'
            data_part = line[15:].strip()
        elif line.startswith('Benchmark Price '):
            metric_name = 'Benchmark_Price'
            data_part = line[16:].strip()
        elif line.startswith('Median Price '):
            metric_name = 'Median_Price'
            data_part = line[13:].strip()
        elif line.startswith('Average Price '):
            metric_name = 'Average_Price'
            data_part = line[14:].strip()
        else:
            return None, None
        
        # Extract numbers
        numbers = self._extract_numbers_from_line(data_part, expected_count, metric_name)
        
        return metric_name, numbers
    
    def _extract_numbers_from_line(self, text: str, expected_count: int, metric_name: str) -> List[int]:
        """Extract numbers from a line, handling PDF formatting issues."""
        
        # Handle different parsing strategies based on format quality
        numbers = []
        
        # Strategy 1: Split by multiple spaces (works for clean format)
        segments = re.split(r'\s{2,}', text.strip())
        
        for segment in segments:
            number = self._parse_single_number(segment, metric_name)
            if number is not None:
                numbers.append(number)
        
        # Strategy 2: If we don't have enough numbers, try alternative parsing
        if len(numbers) < expected_count * 0.5:
            # Handle messy format like "5 16,300" -> 516300
            numbers = []
            
            # Find all number patterns and fix them
            if 'Price' in metric_name:
                # Special handling for prices with spaces
                price_patterns = re.findall(r'(\d+)\s+(\d+,\d+)', text)
                for pattern in price_patterns:
                    combined = pattern[0] + pattern[1].replace(',', '')
                    numbers.append(int(combined))
                
                # Also look for normal prices
                normal_prices = re.findall(r'\b(\d{3},\d{3})\b', text)
                for price in normal_prices:
                    numbers.append(int(price.replace(',', '')))
            else:
                # For non-price fields, simpler parsing
                all_numbers = re.findall(r'\d+', text.replace(',', ''))
                numbers = [int(num) for num in all_numbers if num]
        
        return numbers[:expected_count]
    
    def _parse_single_number(self, segment: str, metric_name: str) -> Optional[int]:
        """Parse a single number segment."""
        
        # Clean the segment
        clean = re.sub(r'[^\d,]', '', segment.strip())
        
        if not clean:
            return None
        
        try:
            # Remove commas and convert
            number = int(clean.replace(',', ''))
            
            # Basic validation based on metric type
            if 'Price' in metric_name and number < 100000:
                # Prices should be reasonable - might need scaling
                if 400 <= number <= 700:
                    return number * 1000  # 567 -> 567000
            
            return number
            
        except ValueError:
            return None
    
    def _build_monthly_records_for_type(self, year: int, months: List[int], 
                                       metrics_data: Dict, property_type: str) -> List[Dict]:
        """Build monthly records for a specific property type."""
        
        records = []
        
        for i, month in enumerate(months):
            # Create base record
            record = {
                'Date': f"{year}-{month:02d}",
                'Property_Type': property_type
            }
            
            # Add metrics (using same names as existing CSV)
            field_mapping = {
                'Sales': 'Sales',
                'New_Listings': 'New_Listings', 
                'Inventory': 'Inventory',
                'Days_on_Market': 'Days_on_Market',
                'Benchmark_Price': 'Benchmark_Price',
                'Median_Price': 'Median_Price',
                'Average_Price': 'Average_Price'
            }
            
            for metric_name, values in metrics_data.items():
                if i < len(values) and metric_name in field_mapping:
                    record[field_mapping[metric_name]] = values[i]
            
            # Only include complete records
            required_fields = ['Sales', 'New_Listings', 'Benchmark_Price']
            if all(field in record for field in required_fields):
                records.append(record)
        
        return records
    
    def extract_city_data_from_pdf(self, pdf_path: Path, target_months: List[str] = None) -> pd.DataFrame:
        """Extract city-wide data for all property types from the PDF."""
        
        all_new_data = []
        
        for property_type, page_num in self.property_types.items():
            logger.info(f"Extracting {property_type} data from page {page_num}...")
            
            page_text = self.extract_page_data(pdf_path, page_num)
            if page_text:
                property_data = self.parse_property_type_data(page_text, property_type)
                
                # Filter for target months if specified
                if target_months:
                    filtered_data = []
                    for record in property_data:
                        if record['Date'] in target_months:
                            filtered_data.append(record)
                    property_data = filtered_data
                
                logger.info(f"Found {len(property_data)} records for {property_type}")
                all_new_data.extend(property_data)
            else:
                logger.warning(f"Could not extract page {page_num} for {property_type}")
        
        if all_new_data:
            new_df = pd.DataFrame(all_new_data)
            logger.info(f"Total city records extracted: {len(new_df)}")
            return new_df
        else:
            logger.warning("No city data extracted")
            return pd.DataFrame()
    
    def extract_district_data_from_pdf(self, pdf_path: Path, target_month: str = None) -> pd.DataFrame:
        """Extract district-level data from PDF (page 7)."""
        logger.info(f"Extracting district data from {pdf_path.name}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Page 7 contains district data
                if len(pdf.pages) >= 7:
                    page = pdf.pages[6]  # 0-indexed, so page 7 is index 6
                    text = page.extract_text()
                    
                    if text:
                        records = self._parse_district_page(text, pdf_path.name, target_month)
                        if records:
                            df = pd.DataFrame(records)
                            logger.info(f"Extracted {len(df)} district records")
                            return df
                
            logger.warning(f"No district data found in {pdf_path.name}")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error extracting district data from {pdf_path.name}: {e}")
            return pd.DataFrame()
    
    def _parse_district_page(self, text: str, filename: str, target_month: str = None) -> List[Dict]:
        """Parse district data from page 7 text."""
        records = []
        lines = text.split('\n')
        
        # Extract date components
        match = re.match(r"(\d{2})_(\d{4})_Calgary", filename)
        if not match:
            logger.error(f"Could not parse date from {filename}")
            return records
        
        month, year = int(match.group(1)), int(match.group(2))
        date_str = f"{year}-{month:02d}-01"
        
        # District parsing patterns - looking for typical district data structure
        current_property_type = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect property type headers
            if any(ptype.lower() in line.lower() for ptype in ['detached', 'apartment', 'row', 'semi']):
                if 'detached' in line.lower() and 'semi' not in line.lower():
                    current_property_type = 'Detached'
                elif 'apartment' in line.lower():
                    current_property_type = 'Apartment'
                elif 'row' in line.lower() or 'townhouse' in line.lower():
                    current_property_type = 'Row'
                elif 'semi' in line.lower():
                    current_property_type = 'Semi-detached'
                continue
            
            # Parse district data lines
            if current_property_type:
                record = self._parse_district_line(line, current_property_type, month, year, date_str)
                if record:
                    records.append(record)
        
        return records
    
    def _parse_district_line(self, line: str, property_type: str, month: int, year: int, date_str: str) -> Optional[Dict]:
        """Parse a single district data line with enhanced robustness."""
        
        # Common Calgary districts to look for (ordered by specificity)
        districts = ['City Centre', 'North East', 'North West', 'South East', 'South West', 'North', 'South', 'West', 'East']
        
        # Find district in line and remove it
        district = None
        remaining_line = line
        for d in districts:
            if line.startswith(d):
                district = d
                remaining_line = line[len(d):].strip()
                break
        
        if not district:
            return None
        
        logger.debug(f"Parsing {district}: {remaining_line}")
        
        # Try enhanced parsing strategy first (May 2025+ format)
        record = self._parse_strategy_v2(remaining_line, property_type, district, month, year, date_str)
        if record:
            return record
            
        # Fallback to original strategy for backward compatibility
        record = self._parse_strategy_v1(remaining_line, property_type, district, month, year, date_str)
        if record:
            return record
            
        logger.warning(f"Failed to parse district line: {district} - {remaining_line}")
        return None
    
    def _parse_strategy_v2(self, line: str, property_type: str, district: str, month: int, year: int, date_str: str) -> Optional[Dict]:
        """Enhanced parsing strategy for May 2025+ format."""
        
        # Regex pattern for May 2025 format
        # Captures: sales listings ratio% inventory months_supply $price yoy% mom%
        pattern = r'(\d+)\s+(\d+)\s+([\d.]+%)\s+(\d+)\s+([\d.]+)\s+\$([0-9,]+)\s+([-]?[\d.]+%)\s+([-]?[\d.]+%)'
        match = re.match(pattern, line.strip())
        
        if match:
            try:
                sales = int(match.group(1))
                listings = int(match.group(2))
                ratio = match.group(3)
                inventory = int(match.group(4))
                months_supply = float(match.group(5))
                price = int(match.group(6).replace(',', ''))
                yoy_change = match.group(7)
                mom_change = match.group(8)
                
                logger.debug(f"✅ Strategy v2 success: {district} - {sales} sales, ${price:,}")
                
                return {
                    'property_type': property_type,
                    'district': district,
                    'new_sales': sales,
                    'new_listings': listings,
                    'sales_to_listings_ratio': ratio,
                    'inventory': inventory,
                    'months_supply': months_supply,
                    'benchmark_price': price,
                    'yoy_price_change': yoy_change,
                    'mom_price_change': mom_change,
                    'month': month,
                    'year': year,
                    'date': date_str
                }
                
            except (ValueError, IndexError) as e:
                logger.debug(f"Strategy v2 parse error: {e}")
        
        return None
    
    def _parse_strategy_v1(self, line: str, property_type: str, district: str, month: int, year: int, date_str: str) -> Optional[Dict]:
        """Original parsing strategy for backward compatibility."""
        
        # Extract numbers from the line using original regex
        numbers = re.findall(r'[\d,]+\.?\d*%?', line)
        
        if len(numbers) >= 8:  # Need at least 8 data points for complete record
            try:
                # Parse the extracted numbers
                new_sales = int(numbers[0].replace(',', '').replace('%', ''))
                new_listings = int(numbers[1].replace(',', '').replace('%', ''))
                
                # Calculate sales to listings ratio
                if new_listings > 0:
                    ratio = f"{(new_sales / new_listings * 100):.2f}%"
                else:
                    ratio = "0.00%"
                
                # Skip the ratio field in numbers[2] and use actual data
                inventory = int(numbers[3].replace(',', '').replace('%', ''))
                months_supply = float(numbers[4].replace(',', '').replace('%', ''))
                benchmark_price = int(numbers[5].replace(',', '').replace('%', ''))
                yoy_change = numbers[6] if '%' in numbers[6] else f"{numbers[6]}%"
                mom_change = numbers[7] if '%' in numbers[7] else f"{numbers[7]}%"
                
                logger.debug(f"✅ Strategy v1 success: {district} - {new_sales} sales, ${benchmark_price:,}")
                
                return {
                    'property_type': property_type,
                    'district': district,
                    'new_sales': new_sales,
                    'new_listings': new_listings,
                    'sales_to_listings_ratio': ratio,
                    'inventory': inventory,
                    'months_supply': months_supply,
                    'benchmark_price': benchmark_price,
                    'yoy_price_change': yoy_change,
                    'mom_price_change': mom_change,
                    'month': month,
                    'year': year,
                    'date': date_str
                }
                
            except (ValueError, IndexError) as e:
                logger.debug(f"Strategy v1 parse error: {e}")
        
        return None
    
    def extract_latest(self) -> Dict[str, any]:
        """Extract data from the latest PDF and save to validation directory."""
        
        # Find latest PDF
        latest_pdf = self.find_latest_pdf()
        if not latest_pdf:
            return {"success": False, "error": "No PDF found"}
        
        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.validation_dir / f"{latest_pdf.stem}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Output directory: {output_dir}")
        
        # Extract both city and district data
        city_df = self.extract_city_data_from_pdf(latest_pdf)
        district_df = self.extract_district_data_from_pdf(latest_pdf)
        
        results = {
            "success": True,
            "pdf_file": latest_pdf.name,
            "output_dir": str(output_dir),
            "timestamp": timestamp
        }
        
        # Save city data
        if not city_df.empty:
            city_output = output_dir / "city_data.csv"
            city_df.to_csv(city_output, index=False)
            results["city_records"] = len(city_df)
            results["city_file"] = str(city_output)
            logger.info(f"✅ City data saved: {len(city_df)} records → {city_output}")
        else:
            results["city_records"] = 0
            logger.warning("⚠️  No city data extracted")
        
        # Save district data
        if not district_df.empty:
            district_output = output_dir / "district_data.csv"
            district_df.to_csv(district_output, index=False)
            results["district_records"] = len(district_df)
            results["district_file"] = str(district_output)
            logger.info(f"✅ District data saved: {len(district_df)} records → {district_output}")
        else:
            results["district_records"] = 0
            logger.warning("⚠️  No district data extracted")
        
        # Create validation report
        validation_report = {
            "extraction_timestamp": timestamp,
            "pdf_source": latest_pdf.name,
            "city_records": results.get("city_records", 0),
            "district_records": results.get("district_records", 0),
            "total_records": results.get("city_records", 0) + results.get("district_records", 0),
            "confidence": 0.95 if (results.get("city_records", 0) > 0 and results.get("district_records", 0) > 0) else 0.75,
            "extraction_method": "simplified_creb_extractor_v1",
            "status": "pending_validation"
        }
        
        validation_file = output_dir / "validation_report.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        results["validation_report"] = str(validation_file)
        
        # Summary
        total_records = results.get("city_records", 0) + results.get("district_records", 0)
        logger.info(f"🎯 Extraction complete: {total_records} total records")
        logger.info(f"   📊 City: {results.get('city_records', 0)} records")
        logger.info(f"   🏘️  District: {results.get('district_records', 0)} records")
        logger.info(f"   📁 Output: {output_dir}")
        
        return results


def main():
    """Main function for standalone usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract Calgary CREB data from PDF reports')
    parser.add_argument('--project-root', help='Project root directory')
    parser.add_argument('--pdf-path', help='Specific PDF file to process')
    
    args = parser.parse_args()
    
    extractor = CREBExtractor(args.project_root)
    
    if args.pdf_path:
        # Process specific PDF
        pdf_path = Path(args.pdf_path)
        if not pdf_path.exists():
            print(f"❌ PDF file not found: {pdf_path}")
            return
        
        # Extract data (implementation for specific PDF)
        print(f"🔄 Processing {pdf_path.name}...")
        # Implementation would go here
    else:
        # Process latest PDF
        results = extractor.extract_latest()
        
        if results["success"]:
            print("✅ CREB extraction completed successfully!")
            print(f"   📄 PDF: {results['pdf_file']}")
            print(f"   📊 City records: {results.get('city_records', 0)}")
            print(f"   🏘️  District records: {results.get('district_records', 0)}")
            print(f"   📁 Output: {results['output_dir']}")
        else:
            print(f"❌ Extraction failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()