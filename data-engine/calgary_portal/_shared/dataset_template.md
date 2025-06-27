# Dataset Template for New Calgary Portal Datasets

## To add a new dataset:

1. **Create dataset directory**:
   ```bash
   mkdir -p calgary_portal/[dataset_name]
   ```

2. **Copy template files**:
   - `extractor.py` - Modify from template below
   - `README.md` - Document the dataset
   - Any SQL files specific to the dataset

3. **Update registry**:
   Add dataset to `/calgary_portal/registry/datasets.json`

## Template Extractor Structure

```python
#!/usr/bin/env python3
"""
Calgary [Dataset Name] Extractor
Extracts [description] from Calgary Open Data Portal
"""

import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.config_manager import ConfigManager

class Calgary[Dataset]Extractor:
    def __init__(self):
        self.config = ConfigManager()
        self.validation_pending_path = self.config.get_pending_review_dir()
        # Dataset-specific setup
    
    # Implementation...

if __name__ == "__main__":
    extractor = Calgary[Dataset]Extractor()
    # Run extraction
```

## Naming Conventions

- **Directory**: lowercase, underscores (e.g., `building_permits`)
- **Extractor class**: CamelCase (e.g., `CalgaryBuildingPermitsExtractor`)
- **Output files**: `calgary_[dataset]_[timestamp].csv`
- **Table name**: Match registry definition

## Next Datasets to Implement

Priority based on existing tables and use cases:
1. `permits/` - Building permits (table: building_permits)
2. `licenses/` - Business licenses (table: business_licences)
3. `traffic/` - Traffic incidents
4. `transit/` - Transit data