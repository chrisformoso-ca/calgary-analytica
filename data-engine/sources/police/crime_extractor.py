#!/usr/bin/env python3
"""
Calgary Police Service Crime Statistics Extractor
Extracts community crime and disorder statistics from Calgary Police Service Excel reports
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import re
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalgaryCrimeExtractor:
    """Extracts Calgary Police Service crime statistics from Excel files."""
    
    def __init__(self, raw_data_path: str = None):
        self.raw_data_path = Path(raw_data_path) if raw_data_path else Path(__file__).parent.parent.parent / "data/raw/calgary_police_service"
        
        # Crime category mappings and severity weights
        self.crime_categories = {
            # Violent crimes - highest severity
            'violent': {
                'keywords': ['assault', 'robbery', 'sexual', 'homicide', 'domestic', 'violence'],
                'severity_weight': 3.0,
                'subcategories': ['assault', 'robbery', 'sexual_assault', 'domestic_violence', 'homicide']
            },
            
            # Property crimes - medium-high severity  
            'property': {
                'keywords': ['theft', 'break', 'enter', 'burglary', 'vandalism', 'mischief', 'fraud'],
                'severity_weight': 2.0,
                'subcategories': ['break_and_enter', 'theft_over', 'theft_under', 'mischief', 'fraud']
            },
            
            # Drug offenses - medium severity
            'drug': {
                'keywords': ['drug', 'narcotic', 'controlled', 'substance', 'possession', 'trafficking'],
                'severity_weight': 2.5,
                'subcategories': ['drug_possession', 'drug_trafficking', 'controlled_substance']
            },
            
            # Traffic offenses - medium severity
            'traffic': {
                'keywords': ['impaired', 'dangerous', 'driving', 'traffic', 'vehicle', 'hit and run'],
                'severity_weight': 1.5,
                'subcategories': ['impaired_driving', 'dangerous_driving', 'hit_and_run']
            },
            
            # Disorder/other - lower severity
            'disorder': {
                'keywords': ['disorder', 'disturbance', 'noise', 'bylaw', 'liquor', 'public'],
                'severity_weight': 1.0,
                'subcategories': ['public_disorder', 'noise_complaint', 'bylaw_violation', 'liquor_offense']
            }
        }
        
        # Community name standardization patterns
        self.community_patterns = {
            'standardize': {
                r'\s+': ' ',  # Multiple spaces to single space
                r'^the\s+': '',  # Remove leading "The "
                r'\s+(ne|nw|se|sw|n|s|e|w)$': r' \1',  # Standardize direction suffixes
            },
            'common_aliases': {
                'downtown': 'Downtown',
                'beltline': 'Beltline', 
                'kensington': 'Kensington',
                'inglewood': 'Inglewood',
                'mission': 'Mission',
                'eau claire': 'Eau Claire'
            }
        }
    
    def find_crime_files(self) -> List[Path]:
        """Find all Calgary Police Service crime statistics files."""
        crime_files = []
        
        # Look for Excel files with crime/police patterns
        patterns = [
            "*crime*.xlsx",
            "*Crime*.xlsx",
            "*police*.xlsx",
            "*Police*.xlsx",
            "*Community*.xlsx",
            "*Statistics*.xlsx"
        ]
        
        for pattern in patterns:
            crime_files.extend(self.raw_data_path.glob(pattern))
        
        # Remove duplicates and sort
        crime_files = list(set(crime_files))
        crime_files.sort()
        
        logger.info(f"Found {len(crime_files)} police/crime statistics files")
        return crime_files
    
    def extract_date_range_from_filename(self, filename: str) -> Optional[Tuple[List[str], int]]:
        """Extract date range and year from filename."""
        
        # Pattern: "January to April 2025"
        month_range_match = re.search(r'(\w+)\s+to\s+(\w+)\s+(\d{4})', filename, re.IGNORECASE)
        if month_range_match:
            start_month, end_month, year = month_range_match.groups()
            
            # Convert month names to numbers
            months_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            
            start_num = months_map.get(start_month.lower())
            end_num = months_map.get(end_month.lower())
            
            if start_num and end_num:
                dates = []
                for month_num in range(start_num, end_num + 1):
                    dates.append(f"{year}-{month_num:02d}-01")
                return dates, int(year)
        
        # Fallback: look for year only
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = int(year_match.group(1))
            # Assume full year
            dates = [f"{year}-{month:02d}-01" for month in range(1, 13)]
            return dates, year
        
        logger.warning(f"Could not extract date range from filename: {filename}")
        return None, None
    
    def analyze_excel_structure(self, file_path: Path) -> Dict[str, Any]:
        """Analyze the structure of a crime statistics Excel file."""
        
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            structure = {
                'file_path': str(file_path),
                'sheet_names': sheet_names,
                'sheet_analysis': {}
            }
            
            # Analyze each sheet
            for sheet_name in sheet_names[:5]:  # Limit to first 5 sheets
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=20)
                    
                    structure['sheet_analysis'][sheet_name] = {
                        'shape': df.shape,
                        'potential_communities': self._find_potential_communities(df),
                        'potential_crime_types': self._find_potential_crime_types(df),
                        'has_numeric_data': self._has_numeric_crime_data(df)
                    }
                    
                except Exception as e:
                    logger.debug(f"Could not analyze sheet {sheet_name}: {e}")
                    structure['sheet_analysis'][sheet_name] = {'error': str(e)}
            
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing Excel file {file_path}: {e}")
            return {'error': str(e)}
    
    def _find_potential_communities(self, df: pd.DataFrame) -> List[str]:
        """Find potential Calgary community names in the dataframe."""
        communities = []
        
        # Common Calgary community indicators
        community_indicators = [
            'beltline', 'downtown', 'kensington', 'inglewood', 'mission',
            'hillhurst', 'eau claire', 'chinatown', 'bridgeland', 'ramsay',
            'forest lawn', 'marlborough', 'temple', 'northeast', 'northwest',
            'southeast', 'southwest', 'centre', 'north', 'south', 'east', 'west'
        ]
        
        # Search all cells for community names
        for col in df.columns:
            for value in df[col].astype(str):
                value_lower = value.lower().strip()
                if any(indicator in value_lower for indicator in community_indicators):
                    if len(value) < 50:  # Reasonable name length
                        communities.append(value.strip())
        
        return list(set(communities))[:10]  # Return up to 10 unique communities
    
    def _find_potential_crime_types(self, df: pd.DataFrame) -> List[str]:
        """Find potential crime types in the dataframe."""
        crime_types = []
        
        # Search for crime-related keywords
        for category, config in self.crime_categories.items():
            for keyword in config['keywords']:
                for col in df.columns:
                    if df[col].astype(str).str.contains(keyword, case=False, na=False).any():
                        crime_types.append(f"{category}_{keyword}")
        
        return list(set(crime_types))[:15]  # Return up to 15 potential types
    
    def _has_numeric_crime_data(self, df: pd.DataFrame) -> bool:
        """Check if the dataframe contains numeric crime data."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        # Look for reasonable crime count ranges (0-1000 per community per month)
        for col in numeric_cols:
            if df[col].between(0, 1000).sum() > 5:  # At least 5 reasonable values
                return True
        
        return False
    
    def extract_crime_data_from_excel(self, file_path: Path, target_dates: List[str] = None) -> List[Dict[str, Any]]:
        """Extract crime statistics from a single Excel file."""
        
        logger.info(f"Extracting crime data from {file_path.name}")
        
        # Get date range from filename
        dates, year = self.extract_date_range_from_filename(file_path.name)
        if not dates:
            logger.error(f"Could not extract dates from {file_path.name}")
            return []
        
        # Filter dates if target specified
        if target_dates:
            dates = [d for d in dates if any(d.startswith(target) for target in target_dates)]
        
        records = []
        
        try:
            # Analyze file structure first
            structure = self.analyze_excel_structure(file_path)
            
            # Try different extraction strategies
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    # Strategy 1: Look for community-based crime data
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    if df.empty:
                        continue
                    
                    # Extract crime data from this sheet
                    sheet_records = self._extract_from_dataframe(df, dates, file_path.name, sheet_name)
                    records.extend(sheet_records)
                    
                    # If we found good data in first sheet, that's often sufficient
                    if sheet_records and sheet_name == excel_file.sheet_names[0]:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error processing sheet {sheet_name}: {e}")
                    continue
            
            logger.info(f"Extracted {len(records)} crime records from {file_path.name}")
            return records
            
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            return []
    
    def _extract_from_dataframe(self, df: pd.DataFrame, dates: List[str], filename: str, sheet_name: str) -> List[Dict[str, Any]]:
        """Extract crime statistics from a pandas DataFrame."""
        records = []
        
        # Strategy 1: Look for community columns and crime type rows
        potential_communities = self._identify_community_columns(df)
        potential_crime_types = self._identify_crime_type_rows(df)
        
        logger.debug(f"Found {len(potential_communities)} communities, {len(potential_crime_types)} crime types")
        
        # Extract data for each community-crime type-date combination
        for date in dates:
            for community_info in potential_communities:
                for crime_info in potential_crime_types:
                    record = self._extract_single_record(
                        df, date, community_info, crime_info, filename, sheet_name
                    )
                    if record:
                        records.append(record)
        
        return records
    
    def _identify_community_columns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify columns that likely contain community data."""
        communities = []
        
        # Look for columns with community-like names
        for col_idx, col_name in enumerate(df.columns):
            if isinstance(col_name, str):
                col_name_clean = str(col_name).strip().lower()
                
                # Check if this looks like a community name
                if self._is_likely_community_name(col_name_clean):
                    communities.append({
                        'name': self._standardize_community_name(str(col_name)),
                        'column_index': col_idx,
                        'column_name': col_name
                    })
        
        # Also check first few rows for community names (transposed data)
        for row_idx in range(min(5, len(df))):
            for col_idx, value in enumerate(df.iloc[row_idx]):
                if isinstance(value, str) and len(value) > 2:
                    if self._is_likely_community_name(value.lower()):
                        communities.append({
                            'name': self._standardize_community_name(value),
                            'row_index': row_idx,
                            'column_index': col_idx
                        })
        
        return communities[:20]  # Limit to 20 communities max
    
    def _identify_crime_type_rows(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify rows that likely contain crime type data."""
        crime_types = []
        
        # Look in first column for crime type names
        if len(df.columns) > 0:
            first_col = df.iloc[:, 0]
            
            for row_idx, value in enumerate(first_col):
                if isinstance(value, str) and len(value) > 2:
                    crime_category = self._classify_crime_type(value)
                    if crime_category:
                        crime_types.append({
                            'category': crime_category,
                            'type': self._standardize_crime_type(value),
                            'raw_text': value,
                            'row_index': row_idx
                        })
        
        return crime_types
    
    def _is_likely_community_name(self, text: str) -> bool:
        """Determine if text is likely a Calgary community name."""
        
        # Common Calgary community patterns
        community_indicators = [
            'hills', 'park', 'ridge', 'wood', 'view', 'heights',
            'ville', 'ton', 'dale', 'glen', 'brook', 'field',
            'downtown', 'beltline', 'kensington', 'mission',
            'inglewood', 'hillhurst', 'eau claire', 'chinatown'
        ]
        
        # Check for indicators
        if any(indicator in text for indicator in community_indicators):
            return True
        
        # Check for direction patterns (NE, NW, etc.)
        if re.search(r'\b(ne|nw|se|sw|north|south|east|west)\b', text):
            return True
        
        # Check length and format
        if 3 <= len(text) <= 30 and text.replace(' ', '').replace('-', '').isalpha():
            return True
        
        return False
    
    def _classify_crime_type(self, text: str) -> Optional[str]:
        """Classify text into crime category."""
        
        text_lower = text.lower()
        
        for category, config in self.crime_categories.items():
            if any(keyword in text_lower for keyword in config['keywords']):
                return category
        
        return None
    
    def _standardize_community_name(self, name: str) -> str:
        """Standardize community name format."""
        
        # Apply standardization patterns
        standardized = name.strip()
        
        for pattern, replacement in self.community_patterns['standardize'].items():
            standardized = re.sub(pattern, replacement, standardized, flags=re.IGNORECASE)
        
        # Apply common aliases
        standardized_lower = standardized.lower()
        for alias, standard in self.community_patterns['common_aliases'].items():
            if alias in standardized_lower:
                standardized = standard
                break
        
        return standardized.title()
    
    def _standardize_crime_type(self, crime_text: str) -> str:
        """Standardize crime type name."""
        
        # Clean and normalize
        standardized = re.sub(r'[^\w\s]', '', crime_text.lower().strip())
        standardized = re.sub(r'\s+', '_', standardized)
        
        return standardized
    
    def _extract_single_record(self, df: pd.DataFrame, date: str, community_info: Dict, 
                              crime_info: Dict, filename: str, sheet_name: str) -> Optional[Dict[str, Any]]:
        """Extract a single crime record."""
        
        try:
            # Get the incident count value
            incident_count = None
            
            if 'column_index' in community_info and 'row_index' in crime_info:
                # Standard grid format
                value = df.iloc[crime_info['row_index'], community_info['column_index']]
                
                if pd.notna(value) and isinstance(value, (int, float)):
                    incident_count = int(value)
            
            elif 'row_index' in community_info and 'column_index' in crime_info:
                # Transposed format
                value = df.iloc[community_info['row_index'], crime_info['column_index']]
                
                if pd.notna(value) and isinstance(value, (int, float)):
                    incident_count = int(value)
            
            if incident_count is not None and incident_count >= 0:
                # Calculate severity score
                severity_weight = self.crime_categories.get(crime_info['category'], {}).get('severity_weight', 1.0)
                severity_index = incident_count * severity_weight
                
                record = {
                    'date': date,
                    'community': community_info['name'],
                    'crime_category': crime_info['category'],
                    'crime_type': crime_info['type'],
                    'incident_count': incident_count,
                    'severity_index': severity_index,
                    'source_file': filename,
                    'sheet_name': sheet_name,
                    'confidence_score': 0.8  # Base confidence
                }
                
                return record
        
        except Exception as e:
            logger.debug(f"Error extracting single record: {e}")
        
        return None
    
    def process_crime_files(self, target_dates: List[str] = None) -> Dict[str, Any]:
        """Process all crime statistics files."""
        
        logger.info("🚔 Starting Calgary Police Service crime data extraction")
        
        # Find all crime files
        crime_files = self.find_crime_files()
        
        if not crime_files:
            return {
                'success': False,
                'error': 'No crime statistics files found',
                'files_processed': 0
            }
        
        # Process files
        all_records = []
        processed_files = 0
        failed_files = []
        
        for file_path in crime_files:
            try:
                records = self.extract_crime_data_from_excel(file_path, target_dates)
                
                if records:
                    all_records.extend(records)
                    processed_files += 1
                    logger.info(f"✅ Processed {file_path.name}: {len(records)} crime records")
                else:
                    logger.warning(f"⚠️  No crime data extracted from {file_path.name}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to process {file_path.name}: {e}")
                failed_files.append(str(file_path))
        
        # Deduplicate records
        unique_records = self._deduplicate_crime_records(all_records)
        
        # Generate community analysis
        community_analysis = self._generate_community_analysis(unique_records)
        
        logger.info(f"🚔 Crime extraction complete:")
        logger.info(f"  Files processed: {processed_files}/{len(crime_files)}")
        logger.info(f"  Total crime records: {len(unique_records)}")
        logger.info(f"  Communities covered: {len(community_analysis)}")
        logger.info(f"  Failed files: {len(failed_files)}")
        
        return {
            'success': True,
            'records': unique_records,
            'community_analysis': community_analysis,
            'files_processed': processed_files,
            'total_files': len(crime_files),
            'failed_files': failed_files,
            'crime_records': len(unique_records)
        }
    
    def _deduplicate_crime_records(self, records: List[Dict]) -> List[Dict]:
        """Remove duplicate crime records."""
        
        seen = set()
        unique_records = []
        
        for record in records:
            key = (
                record['date'], 
                record['community'], 
                record['crime_category'], 
                record['crime_type']
            )
            
            if key not in seen:
                seen.add(key)
                unique_records.append(record)
        
        logger.info(f"Deduplicated: {len(records)} -> {len(unique_records)} crime records")
        return unique_records
    
    def _generate_community_analysis(self, records: List[Dict]) -> List[Dict]:
        """Generate community-level safety analysis."""
        
        community_stats = {}
        
        for record in records:
            community = record['community']
            
            if community not in community_stats:
                community_stats[community] = {
                    'community': community,
                    'total_incidents': 0,
                    'violent_crime_count': 0,
                    'property_crime_count': 0,
                    'disorder_count': 0,
                    'total_severity': 0.0,
                    'months_reported': set(),
                    'crime_categories': set()
                }
            
            stats = community_stats[community]
            stats['total_incidents'] += record['incident_count']
            stats['total_severity'] += record['severity_index']
            stats['months_reported'].add(record['date'][:7])  # YYYY-MM
            stats['crime_categories'].add(record['crime_category'])
            
            # Category-specific counts
            if record['crime_category'] == 'violent':
                stats['violent_crime_count'] += record['incident_count']
            elif record['crime_category'] == 'property':
                stats['property_crime_count'] += record['incident_count']
            elif record['crime_category'] in ['disorder', 'traffic']:
                stats['disorder_count'] += record['incident_count']
        
        # Calculate safety scores and finalize analysis
        analysis = []
        for community, stats in community_stats.items():
            months_count = len(stats['months_reported'])
            
            if months_count > 0:
                avg_incidents = stats['total_incidents'] / months_count
                avg_severity = stats['total_severity'] / months_count
                
                # Safety score (0-1, higher = safer)
                # Inverse relationship with crime (normalized)
                max_monthly_incidents = 100  # Assumption for normalization
                safety_score = max(0, (max_monthly_incidents - avg_incidents) / max_monthly_incidents)
                
                # Housing impact score (how much crime affects housing desirability)
                violent_weight = 0.6
                property_weight = 0.3
                disorder_weight = 0.1
                
                housing_impact = (
                    (stats['violent_crime_count'] / max(stats['total_incidents'], 1)) * violent_weight +
                    (stats['property_crime_count'] / max(stats['total_incidents'], 1)) * property_weight +
                    (stats['disorder_count'] / max(stats['total_incidents'], 1)) * disorder_weight
                )
                
                analysis.append({
                    'community': community,
                    'total_incidents': stats['total_incidents'],
                    'violent_crime_count': stats['violent_crime_count'],
                    'property_crime_count': stats['property_crime_count'],
                    'disorder_count': stats['disorder_count'],
                    'overall_severity': avg_severity,
                    'safety_score': safety_score,
                    'housing_impact_score': housing_impact,
                    'months_reported': months_count,
                    'avg_monthly_incidents': avg_incidents
                })
        
        return sorted(analysis, key=lambda x: x['safety_score'], reverse=True)
    
    def save_to_database(self, records: List[Dict], community_analysis: List[Dict], db_path: str) -> bool:
        """Save crime records and analysis to SQLite database."""
        
        if not records and not community_analysis:
            logger.warning("No crime data to save")
            return True
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Insert crime statistics records
            crime_inserted = 0
            for record in records:
                try:
                    cursor.execute("""
                    INSERT OR REPLACE INTO crime_statistics_monthly 
                    (date, community, crime_category, crime_type, incident_count, 
                     severity_index, source_file, confidence_score, validation_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                    """, (
                        record['date'],
                        record['community'],
                        record['crime_category'],
                        record['crime_type'],
                        record['incident_count'],
                        record['severity_index'],
                        record['source_file'],
                        record.get('confidence_score', 0.8)
                    ))
                    crime_inserted += 1
                    
                except sqlite3.Error as e:
                    logger.error(f"Error inserting crime record: {e}")
                    continue
            
            # Insert community analysis records
            analysis_inserted = 0
            for analysis in community_analysis:
                try:
                    # Determine crime trend (simplified)
                    trend = 'stable'  # Default, could be enhanced with historical data
                    
                    cursor.execute("""
                    INSERT OR REPLACE INTO crime_analysis_monthly 
                    (date, community, total_incidents, violent_crime_count, property_crime_count,
                     disorder_count, overall_severity, safety_score, crime_trend, housing_impact_score,
                     source_file, confidence_score, validation_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                    """, (
                        records[0]['date'] if records else '2025-01-01',  # Use first record date
                        analysis['community'],
                        analysis['total_incidents'],
                        analysis['violent_crime_count'],
                        analysis['property_crime_count'],
                        analysis['disorder_count'],
                        analysis['overall_severity'],
                        analysis['safety_score'],
                        trend,
                        analysis['housing_impact_score'],
                        records[0]['source_file'] if records else 'community_analysis',
                        0.9  # High confidence for aggregated analysis
                    ))
                    analysis_inserted += 1
                    
                except sqlite3.Error as e:
                    logger.error(f"Error inserting community analysis: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Saved {crime_inserted} crime records and {analysis_inserted} community analyses to database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database save failed: {e}")
            return False


def main():
    """Test the crime extractor."""
    
    extractor = CalgaryCrimeExtractor()
    
    # Process all crime files
    result = extractor.process_crime_files()
    
    if result['success']:
        print(f"✅ Crime extraction completed:")
        print(f"  Files processed: {result['files_processed']}/{result['total_files']}")
        print(f"  Crime records: {result['crime_records']}")
        print(f"  Communities: {len(result['community_analysis'])}")
        
        # Show sample records
        if result['records']:
            print(f"\nSample crime records:")
            for record in result['records'][:3]:
                print(f"  {record['date']} - {record['community']}: {record['crime_category']} = {record['incident_count']} incidents")
        
        # Show sample community analysis
        if result['community_analysis']:
            print(f"\nSample community safety analysis:")
            for analysis in result['community_analysis'][:3]:
                print(f"  {analysis['community']}: Safety Score = {analysis['safety_score']:.2f}, Total Incidents = {analysis['total_incidents']}")
    else:
        print(f"❌ Crime extraction failed: {result.get('error')}")


if __name__ == "__main__":
    main()