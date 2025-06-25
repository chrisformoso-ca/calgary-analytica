# Data Engine Instructions for Claude Code

This file provides specific guidance for working with the data-engine directory.

## Simple Data Flow (NO EXCEPTIONS)

```
RAW FILES → Extract to CSV → Human Reviews → Load to Database
```

1. **Extract**: Scripts in `/{source}/scripts/` read raw files and output CSV to `/validation/pending/`
2. **Review**: Human manually checks CSVs and moves good ones to `/validation/approved/`
3. **Load**: Run `load_approved_data.py` to insert approved CSVs into database

## Directory Structure (Source-Based Organization)

```
data-engine/
├── creb/                    # CREB housing data
│   ├── raw/                # PDF files (MM_YYYY_Calgary_Monthly_Stats_Package.pdf)
│   ├── scripts/            # extractor.py, extract_all_historical.py
│   ├── patterns/           # extraction_patterns.json
│   ├── config.json        # Source configuration
│   └── notes.md           # CREB-specific documentation
├── economic/               # Economic indicators
│   ├── raw/               # Excel/PDF files
│   ├── scripts/           # extractor.py
│   ├── patterns/          # Extraction patterns
│   ├── config.json       # Source configuration
│   └── notes.md          # Economic data tips
├── police/                # Crime statistics
│   ├── raw/              # Excel files
│   ├── scripts/          # extractor.py
│   ├── patterns/         # Extraction patterns
│   ├── config.json      # Source configuration
│   └── notes.md         # Crime data documentation
├── validation/            # Human review pipeline
│   ├── pending/          # New extractions waiting for review
│   ├── approved/         # Human-approved, ready to load
│   ├── rejected/         # Failed validation
│   └── processed/        # Successfully loaded to DB
├── core/                  # Core functionality
│   ├── data_engine.py    # Orchestrates extraction
│   ├── load_approved_data.py # Loads to database (expects validation structure)
│   └── load_csv_direct.py # Simple CSV loader (direct from approved/)
└── cli/                   # Command line scripts
    ├── monthly_update.py  # Main update script
    └── validate_pending.py # Review pending CSVs
```

## Common Tasks

### Monthly Housing Update
```bash
# 1. Make sure PDF is in /creb/raw/
# 2. Run extraction
python cli/monthly_update.py --month 6 --year 2025

# 3. Review what was extracted
python cli/validate_pending.py --list

# 4. Manually review
python cli/validate_pending.py --interactive

# 5. Load approved data
cd core && python load_approved_data.py
```

### Check What's Pending
```bash
ls -la validation/pending/
```

### Manual Approval (Simple Way)
```bash
# If CSV looks good, move it
mv validation/pending/[filename] validation/approved/

# Then load it
cd core && python load_approved_data.py

# OR use the simple loader for CSVs directly in approved/
cd core && python load_csv_direct.py
```

## Important Rules

1. **NEVER skip validation** - All data goes through pending first
2. **NEVER write directly to database** - Only load_approved_data.py or load_csv_direct.py does this
3. **ALWAYS check confidence scores** - Low confidence needs extra review
4. **KEEP it simple** - No fancy abstractions or enterprise patterns

## Expected Data Volumes

Per month:
- Housing City: 5 records (property types)
- Housing District: 32 records (8 districts × 4 types)
- Economic: ~10-15 indicators
- Total: ~50 records/month

## Which Loader to Use?

**load_approved_data.py**: 
- For data processed through the full validation pipeline
- Expects subdirectories in approved/ with validation_report.json files
- Used by automated workflows

**load_csv_direct.py**:
- For simple CSV files placed directly in approved/
- Auto-detects table type from column names
- Good for historical data loads or manual CSV imports
- Handles column mapping and data type conversions automatically

## Troubleshooting

**Extraction failed?**
- Check the PDF exists in the source's `/raw/` directory
- Look at confidence score - if < 90%, extraction may have issues
- Check logs in `/validation/logs/`
- Review source-specific notes in `/{source}/notes.md`

**Wrong data in pending?**
- Move to rejected: `mv validation/pending/[file] validation/rejected/`
- Document why in a text file

**Need to re-extract?**
- Just run the extraction again - it creates new timestamped files
- Old attempts stay in pending until you clean them up

## Database Tables

- `housing_city_monthly` - City-wide totals
- `housing_district_monthly` - District breakdowns  
- `economic_indicators_monthly` - Economic data
- `crime_statistics_monthly` - Crime stats

Check what's in database:
```bash
cd /home/chris/calgary-analytica/data-lake
sqlite3 calgary_data.db "SELECT COUNT(*) FROM housing_city_monthly;"
```

Keep it simple. Extract → Review → Load. That's it.

## Extractor Development Patterns

When creating new extractors, follow these established patterns for consistency:

### File Naming
- Main extractor: `extractor.py` 
- Specialized variants: `extractor_[type].py` (e.g., `extractor_timeseries.py`)
- Analysis/test scripts: descriptive names (e.g., `analyze_data.py`)

### Standard Imports and Path Handling
```python
#!/usr/bin/env python3
"""
[Source] Data Extractor
Clear description of what this extracts and from where
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import re
from datetime import datetime
import json
import sys

# Add project root to path for imports (ALWAYS use this pattern)
sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
```

### Class Structure
```python
class Calgary[Source]Extractor:
    """Extract [data type] from [source]."""
    
    def __init__(self):
        # Always use ConfigManager for paths
        self.config = ConfigManager()
        self.raw_data_path = self.config.get_project_root() / 'data-engine' / '[source]' / 'raw'
        self.validation_pending_path = self.config.get_pending_review_dir()
```

### Output Formatting Patterns

#### Progress Indicators
Use emojis consistently for visual feedback:
- 🏠 Housing/CREB data
- 🚔 Police/Crime data  
- 🏛️ Economic data
- ✅ Success
- ❌ Error/Failure
- ⚠️ Warning
- 📊 Data/Statistics
- 📂 File/Directory
- 📋 Report/Summary
- 💾 Saving data

#### Summary Output Format
```python
print(f"\n✅ Extraction completed:")
print(f"  Files processed: {result['files_processed']}")
print(f"  Total records: {result['total_records']:,}")  # Use :, for thousands
print(f"  Date range: {result['date_range']}")

# Extraction summary box
print("\n" + "="*70)
print("📊 EXTRACTION SUMMARY")
print("="*70)
print(f"\n📁 Source: file://{file_path.absolute()}")  # Clickable path
print(f"📅 Period: {period}")
print(f"\n🏙️ DATA BREAKDOWN:")
print("-" * 50)
# ... data details ...
print("\n" + "="*70)
```

#### Next Steps Output
Always provide clear next steps with exact commands:
```python
print(f"\n📂 Output files:")
print(f"  CSV:  {csv_path}")
print(f"  JSON: {json_path}")

print(f"\n📂 Click to open:")
print(f"  file://{csv_path}")
print(f"  file://{json_path}")

print(f"\n📋 Next steps for validation:")
print(f"  1. Review CSV:  less {csv_path}")
print(f"  2. Check JSON:  less {json_path}")
print(f"  3. If approved: mv {csv_path} {csv_path.parent.parent}/approved/")
print(f"  4. Load to DB:  cd data-engine/core && python3 load_csv_direct.py")
```

### Data Schema Patterns

#### Keep It Simple
Only include essential data columns. Remove:
- `confidence_score` - Not needed for simple data
- `data_source` - Redundant when source is clear from context
- `extraction_date` - Metadata not needed in final data
- `source_file` - Only use temporarily for deduplication if needed

#### Temporal Data
- Always include `date` in YYYY-MM-DD format
- Include `year` as integer if useful for filtering
- Avoid separate `month` column unless specifically needed
- For annual data, use date as YYYY-01-01

### Validation Report Structure
Create JSON report alongside CSV with same base name:
```python
validation_report = {
    'source': '[source]_[type]_data',
    'extraction_date': datetime.now().isoformat(),
    'records_extracted': len(records),
    'date_range': f"{min_date} to {max_date}",
    # Category breakdowns specific to data type
    'categories': {...},
    'sample_records': [
        # Include 3-5 representative records
    ]
}

# Save with same base name as CSV
report_path = csv_path.with_suffix('.json')
with open(report_path, 'w') as f:
    json.dump(validation_report, f, indent=2)
```

### Command-Line Interface Pattern
```python
def main():
    """Extract [source] data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract [source] data')
    parser.add_argument('--years', nargs='+', type=int, help='Specific years to extract')
    parser.add_argument('--test', action='store_true', help='Test mode - analyze files only')
    args = parser.parse_args()
    
    extractor = Calgary[Source]Extractor()
    
    if args.test:
        # Implement test mode
        print("🔍 Analyzing files...")
        # ... test logic ...
        return
    
    # Normal extraction
    result = extractor.process_files(year_filter=args.years)
    
    if result['success']:
        # Show success output with patterns above
    else:
        print(f"❌ Extraction failed: {result.get('error')}")

if __name__ == "__main__":
    main()
```

### Error Handling
- Log errors with context: `logger.error(f"Error processing {file}: {e}")`
- Continue processing other files on individual failures
- Track failed files and report at end
- Return structured results dict with success/error status

### File Naming Convention
Output files use timestamp for uniqueness:
```python
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"{source}_{type}_{timestamp}.csv"
```

## Common Extractor Template

Here's a minimal template following all patterns:

```python
#!/usr/bin/env python3
"""
Calgary [Source] Data Extractor
Extracts [what] from [where]
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import re
from datetime import datetime
import json
import sys

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Calgary[Source]Extractor:
    """Extracts [data type] from [source]."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.raw_data_path = self.config.get_project_root() / 'data-engine' / '[source]' / 'raw'
        self.validation_pending_path = self.config.get_pending_review_dir()
    
    def find_files(self) -> List[Path]:
        """Find all relevant files to process."""
        files = []
        patterns = ["*.xlsx", "*.pdf", "*.csv"]  # Adjust as needed
        
        for pattern in patterns:
            files.extend(self.raw_data_path.glob(pattern))
        
        logger.info(f"Found {len(files)} files")
        return sorted(files)
    
    def extract_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract data from a single file."""
        logger.info(f"Extracting from {file_path.name}")
        records = []
        
        try:
            # Extraction logic here
            # ...
            
            logger.info(f"Extracted {len(records)} records")
            return records
            
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            return []
    
    def save_to_validation(self, records: List[Dict]) -> Optional[Path]:
        """Save records to validation pending directory."""
        if not records:
            logger.warning("No data to save")
            return None
        
        try:
            df = pd.DataFrame(records)
            df = df.sort_values(['date'])  # Adjust sort as needed
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"[source]_[type]_{timestamp}.csv"
            csv_path = self.validation_pending_path / filename
            
            # Save CSV
            self.validation_pending_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(csv_path, index=False)
            logger.info(f"✅ Saved {len(records)} records to {csv_path}")
            
            # Create validation report
            self._create_validation_report(records, csv_path)
            
            return csv_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save data: {e}")
            return None
    
    def _create_validation_report(self, records: List[Dict], csv_path: Path) -> None:
        """Create JSON validation report."""
        try:
            validation_report = {
                'source': '[source]_data',
                'extraction_date': datetime.now().isoformat(),
                'records_extracted': len(records),
                'date_range': self._get_date_range(records),
                'sample_records': records[:5]  # First 5 records
            }
            
            report_path = csv_path.with_suffix('.json')
            with open(report_path, 'w') as f:
                json.dump(validation_report, f, indent=2)
            
            logger.info(f"📋 Created validation report: {report_path}")
            
        except Exception as e:
            logger.warning(f"Could not create validation report: {e}")
    
    def _get_date_range(self, records: List[Dict]) -> str:
        """Get date range from records."""
        if not records:
            return "No data"
        
        dates = [r['date'] for r in records if 'date' in r]
        if dates:
            return f"{min(dates)} to {max(dates)}"
        return "No dates"
    
    def process_files(self) -> Dict[str, Any]:
        """Process all files and return results."""
        logger.info("🚀 Starting [source] data extraction")
        
        files = self.find_files()
        if not files:
            return {'success': False, 'error': 'No files found'}
        
        all_records = []
        
        for file_path in files:
            records = self.extract_data(file_path)
            all_records.extend(records)
        
        csv_path = None
        if all_records:
            csv_path = self.save_to_validation(all_records)
        
        return {
            'success': True,
            'records': all_records,
            'files_processed': len(files),
            'total_records': len(all_records),
            'csv_path': csv_path
        }

def main():
    """Extract [source] data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract [source] data')
    parser.add_argument('--test', action='store_true', help='Test mode')
    args = parser.parse_args()
    
    extractor = Calgary[Source]Extractor()
    
    if args.test:
        print("🔍 Test mode - analyzing files...")
        files = extractor.find_files()
        for f in files:
            print(f"  - {f.name}")
        return
    
    result = extractor.process_files()
    
    if result['success']:
        print(f"\n✅ Extraction completed:")
        print(f"  Files processed: {result['files_processed']}")
        print(f"  Total records: {result['total_records']:,}")
        
        if result.get('csv_path'):
            csv_path = result['csv_path']
            json_path = csv_path.with_suffix('.json')
            
            print(f"\n📂 Output files:")
            print(f"  CSV:  {csv_path}")
            print(f"  JSON: {json_path}")
            
            print(f"\n📂 Click to open:")
            print(f"  file://{csv_path}")
            print(f"  file://{json_path}")
            
            print(f"\n📋 Next steps for validation:")
            print(f"  1. Review CSV:  less {csv_path}")
            print(f"  2. Check JSON:  less {json_path}")
            print(f"  3. If approved: mv {csv_path} {csv_path.parent.parent}/approved/")
            print(f"  4. Load to DB:  cd data-engine/core && python3 load_csv_direct.py")
    else:
        print(f"❌ Extraction failed: {result.get('error')}")

if __name__ == "__main__":
    main()
```