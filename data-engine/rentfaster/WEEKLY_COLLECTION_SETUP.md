# RentFaster Weekly Collection Setup Guide

This guide explains how to set up automated weekly collection of RentFaster rental listings data.

## Overview

The RentFaster data collection runs weekly to capture:
- Current rental market listings
- Price changes week-over-week
- Market velocity (new vs removed listings)
- Seasonal rental patterns

## Scripts

1. **extractor.py** - Fetches current listings from RentFaster API
2. **aggregate_weekly.py** - Aggregates snapshots into weekly summaries

## Manual Collection

To run manually:
```bash
# Extract current listings (adjust page count as needed)
cd /home/chris/calgary-analytica/data-engine/rentfaster/scripts
python3 extractor.py 20  # Fetches 20 pages (~400 listings)

# After approval, load to database
cd /home/chris/calgary-analytica/data-engine/cli
python3 load_csv_direct.py

# Run aggregation
cd /home/chris/calgary-analytica/data-engine/rentfaster/scripts
python3 aggregate_weekly.py
```

## Automated Weekly Collection

### Option 1: Linux Cron Job (WSL2)

1. First, ensure cron is installed:
```bash
sudo apt-get update
sudo apt-get install cron
sudo service cron start
```

2. Create a collection script:
```bash
cat > ~/calgary-analytica/data-engine/rentfaster/scripts/weekly_collection.sh << 'EOF'
#!/bin/bash
# RentFaster Weekly Collection Script

# Set up environment
export PATH="/usr/local/bin:/usr/bin:/bin"
cd /home/chris/calgary-analytica/data-engine/rentfaster/scripts

# Log file
LOG_FILE="/home/chris/calgary-analytica/data-engine/validation/logs/rentfaster_$(date +%Y%m%d).log"

echo "Starting RentFaster collection at $(date)" >> "$LOG_FILE"

# Run extraction (30 pages for thorough coverage)
python3 extractor.py 30 >> "$LOG_FILE" 2>&1

# Auto-approve and load (since it's automated)
cd /home/chris/calgary-analytica/data-engine/validation
PENDING_FILE=$(ls -t pending/rentfaster_listings_*.csv 2>/dev/null | head -1)

if [ -f "$PENDING_FILE" ]; then
    mv "$PENDING_FILE" approved/
    echo "Moved to approved: $PENDING_FILE" >> "$LOG_FILE"
    
    # Load to database
    cd /home/chris/calgary-analytica/data-engine/cli
    python3 load_csv_direct.py >> "$LOG_FILE" 2>&1
    
    # Run aggregation
    cd /home/chris/calgary-analytica/data-engine/rentfaster/scripts
    python3 aggregate_weekly.py >> "$LOG_FILE" 2>&1
else
    echo "No pending file found" >> "$LOG_FILE"
fi

echo "Collection completed at $(date)" >> "$LOG_FILE"
EOF

chmod +x ~/calgary-analytica/data-engine/rentfaster/scripts/weekly_collection.sh
```

3. Add to crontab (runs every Sunday at 2 AM):
```bash
crontab -e
# Add this line:
0 2 * * 0 /home/chris/calgary-analytica/data-engine/rentfaster/scripts/weekly_collection.sh
```

### Option 2: Windows Task Scheduler

1. Create a batch file `weekly_collection.bat`:
```batch
@echo off
cd C:\Users\chris\calgary-analytica
wsl python3 /home/chris/calgary-analytica/data-engine/rentfaster/scripts/extractor.py 30
wsl python3 /home/chris/calgary-analytica/data-engine/rentfaster/scripts/auto_approve_load.py
```

2. Open Task Scheduler:
   - Press Win+R, type `taskschd.msc`
   - Create Basic Task
   - Name: "RentFaster Weekly Collection"
   - Trigger: Weekly, Sunday, 2:00 AM
   - Action: Start a program
   - Program: Path to your batch file

## Monitoring

Check collection logs:
```bash
ls -la ~/calgary-analytica/data-engine/validation/logs/rentfaster_*.log
tail -f ~/calgary-analytica/data-engine/validation/logs/rentfaster_$(date +%Y%m%d).log
```

Check database for latest data:
```bash
cd ~/calgary-analytica/data-lake
sqlite3 calgary_data.db "SELECT extraction_week, COUNT(*) FROM rental_listings_snapshot GROUP BY extraction_week ORDER BY extraction_week DESC LIMIT 5;"
```

## Maintenance

- **Adjust page count**: Monitor total listings. If consistently > 600, increase pages
- **Check for API changes**: If extraction fails, check RentFaster API response format
- **Disk space**: Weekly snapshots use ~2-3MB each. Clean old processed files quarterly
- **Aggregation**: Run `aggregate_weekly.py` after each collection to update summaries

## Troubleshooting

1. **No data extracted**: Check API is accessible, rate limits
2. **Duplicate errors**: Normal for re-runs in same week (UNIQUE constraint handles it)
3. **WSL cron not running**: Ensure WSL2 is running and cron service is started
4. **Permission errors**: Check file ownership and executable permissions

## Weekly Data Usage

The collected data powers:
- Rental market trends dashboard
- Property type comparison analysis
- Community-level rental heat maps
- Asking vs actual rent analysis (when combined with CREB data)
- Market tightness indicators

## Notes

- Collection happens early Sunday morning when listing activity is low
- Each weekly snapshot captures ~400-800 active listings
- Data is privacy-conscious (no addresses or exact coordinates stored)
- Aggregations provide the analytical value while minimizing storage