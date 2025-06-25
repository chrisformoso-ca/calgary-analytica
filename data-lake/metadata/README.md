# Calgary Data Lake - Metadata Management

This directory contains metadata tracking for the Calgary Data Lake.

## Structure

- **`/data-dictionary/`** - Timestamped snapshots of the database structure and contents
- **`ddl-history.md`** - Log of all structural changes (DDL) to the database
- **`current-state.md`** - Symlink to the most recent data dictionary

## Usage

To generate a new data dictionary and update metadata:
```
/project:metadata
```

This command will:
1. Create a new timestamped data dictionary
2. Update the current-state symlink
3. Show recent data loads
4. Remind you to update DDL history if you made schema changes

## Data Dictionary Contents

Each data dictionary includes:
- Metadata summary (database size, total records, last updates)
- Table overview (record counts, date ranges)
- Schema details for each table
- Data distributions (categories, types, geographic coverage)
- Temporal alignment showing data overlap
- Sample queries for analysis

## DDL History

The `ddl-history.md` file tracks all structural changes:
- Table creation/deletion
- Column additions/removals
- Data type changes
- Constraint modifications

Update this manually when you make schema changes, following the date-based format.