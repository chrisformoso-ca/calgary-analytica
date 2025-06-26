# Data Engine Structure

## Overview
The data-engine is organized by data source, with each source containing everything needed for that data type.

## Directory Structure

```
data-engine/
├── creb/                    # Calgary Real Estate Board data
│   ├── raw/                # Original PDF files
│   ├── scripts/            # Extraction scripts
│   ├── patterns/           # Successful extraction patterns
│   ├── config.json        # Source configuration
│   └── notes.md           # Documentation and tips
│
├── economic/               # Economic indicators data
│   ├── raw/               # Excel and PDF files
│   ├── scripts/           # Extraction scripts
│   ├── patterns/          # Extraction patterns
│   ├── config.json       # Source configuration
│   └── notes.md          # Documentation
│
├── police/                # Crime statistics data
│   ├── raw/              # Excel files
│   ├── scripts/          # Extraction scripts
│   ├── patterns/         # Extraction patterns
│   ├── config.json      # Source configuration
│   └── notes.md         # Documentation
│
├── validation/            # Shared validation pipeline
│   ├── pending/          # CSVs awaiting review
│   ├── approved/         # Human-approved CSVs
│   ├── rejected/         # Failed validation
│   └── processed/        # Successfully loaded
│
└── cli/                   # Command line scripts
    ├── load_csv_direct.py # Simple CSV loader (direct from approved/)
    ├── monthly_update.py  # Main update script
    └── validate_pending.py # Review pending CSVs
```

## Benefits of This Structure

1. **Self-contained sources** - Everything about CREB is in `/creb/`
2. **Easy to add sources** - Just create a new directory
3. **Clear workflow** - Raw → Scripts → Validation → Database
4. **Future flexibility** - Can add transformations, tests, etc.

## Adding a New Data Source

1. Create directory: `mkdir -p newsource/{raw,scripts,patterns}`
2. Add extraction script: `newsource/scripts/extractor.py`
3. Create documentation: `newsource/notes.md`
4. Add configuration: `newsource/config.json`
5. Update `data_engine.py` to include new source