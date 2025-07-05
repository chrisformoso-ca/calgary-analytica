# Mortgage Rate Update Process

## Overview
Mortgage rates in the Calgary Housing Dashboard are manually updated monthly since we don't have an automated data source yet.

## Current Rate Sources
- **Bank of Canada Rate**: Automatically pulled from economic indicators
- **Prime Rate**: Calculated as BoC + 1.95% (typical spread)
- **Mortgage Rates**: Manually updated from major banks

## Update Process

### 1. Check Current Rates
Visit these sources on the 1st of each month:
- RBC: https://www.rbc.com/mortgages/mortgage-rates.html
- TD: https://www.td.com/ca/en/personal-banking/products/mortgages/mortgage-rates/
- BMO: https://www.bmo.com/main/personal/mortgages/mortgage-rates/
- CIBC: https://www.cibc.com/en/personal-banking/mortgages/mortgage-rates.html
- Scotiabank: https://www.scotiabank.com/ca/en/personal/mortgages/mortgage-rates.html

### 2. Calculate Average Rates
Take the posted rates from the big 5 banks and calculate the average for:
- 5-year fixed rate
- 3-year fixed rate
- Variable rate (typically Prime - 0.50% to Prime - 0.75%)

### 3. Update rate_data.json
Edit `/product-engine/dashboard-mvp/scripts/generate_rate_data.py` and update:
```python
'mortgage': {
    'five_year_fixed': 6.95,  # Update this
    'three_year_fixed': 6.75,  # Update this
    'variable': 6.7,  # Update this
    'last_updated': '2025-07-01'  # Update date
}
```

### 4. Regenerate Data
```bash
cd /home/chris/calgary-analytica/product-engine/dashboard-mvp/scripts
python3 generate_rate_data.py
```

## Future Automation
Consider these options for automation:
1. Bank APIs (if available)
2. Web scraping (with permission)
3. RSS feeds from financial news sites
4. Integration with rate aggregator services

## Data Gaps Documented

### Money Supply (M2)
- **Status**: Not available - requires Bank of Canada API or manual download
- **Workaround**: Using placeholder value of 4.2% YoY growth
- **Display**: Dashboard shows "M2: +4.2% YoY*" with note about placeholder
- **Future**: Integrate with Bank of Canada data portal

### Actual Mortgage Rates
- **Status**: Manual monthly updates required
- **Current Process**: Check major bank websites monthly
- **Future**: Automate via API or approved web scraping