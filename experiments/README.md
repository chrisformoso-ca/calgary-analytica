# Dashboard Architecture Comparison

This directory contains two identical-looking dashboards built with different architectures to help you understand the differences.

## Quick Summary

Both dashboards look and feel **exactly the same** to users. The difference is in how they work behind the scenes.

## Static Dashboard (Recommended for Calgary Analytica)

**Location**: `/experiments/static-dashboard/`

### How It Works
1. You run Python scripts locally to update data
2. Python exports data to JSON files
3. Upload JSON files + HTML/JS/CSS to any web host
4. Browser loads JSON and creates interactive charts

### Hosting Requirements
- **Cost**: $5/month (or free with GitHub Pages)
- **Examples**: Netlify, Vercel, GitHub Pages, any static host
- **What you need**: Just a place to host files

### To Test Locally
```bash
cd experiments/static-dashboard
python3 -m http.server 8000
# Visit http://localhost:8000
```

### Pros
- ✅ Super cheap hosting
- ✅ Fast loading (no database queries)
- ✅ Easy to deploy (just upload files)
- ✅ Scales infinitely (CDN-friendly)
- ✅ No server maintenance

### Cons
- ❌ Data updates require uploading new JSON
- ❌ No user accounts or saving preferences
- ❌ Can't query database on-demand

### Perfect For
- Monthly data updates
- Public dashboards
- MVP stage
- Cost-conscious projects

## Dynamic Dashboard (PHP + Database)

**Location**: `/experiments/dynamic-dashboard/`

### How It Works
1. PHP runs on server
2. Queries SQLite database in real-time
3. Generates HTML with current data
4. JavaScript adds interactivity

### Hosting Requirements
- **Cost**: $10-20/month
- **Examples**: DigitalOcean, Linode, any PHP host
- **What you need**: PHP 7+ and SQLite support

### To Test Locally
```bash
cd experiments/dynamic-dashboard
# First create the database
python3 setup_database.py
# Then run PHP server
php -S localhost:8001
# Visit http://localhost:8001
```

### Pros
- ✅ Real-time data updates
- ✅ Can add user features later
- ✅ Database queries on-demand
- ✅ More "traditional" web app

### Cons
- ❌ More expensive hosting
- ❌ Server maintenance required
- ❌ Slower (database queries)
- ❌ More complex deployment

### Perfect For
- Apps with user accounts
- Real-time data needs
- Complex queries
- Full platform development

## Key Differences Explained

### 1. **Where Code Runs**
- **Static**: All code runs in visitor's browser
- **Dynamic**: Some code runs on server, some in browser

### 2. **Data Storage**
- **Static**: JSON files (pre-generated)
- **Dynamic**: SQLite database (queried live)

### 3. **Updates**
- **Static**: Upload new JSON files
- **Dynamic**: Update database on server

### 4. **Performance**
- **Static**: Instant (files cached by browser/CDN)
- **Dynamic**: Slower (database queries each visit)

## Your Workflow Comparison

### With Static Approach
```
1. Download CREB PDFs
2. Run Python locally → Generate JSON
3. Upload JSON + dashboard files to host
4. Done! Site shows new data
```

### With Dynamic Approach
```
1. Download CREB PDFs
2. Run Python locally → Update local database
3. Upload database to server
4. OR: Run Python on server (more complex)
5. Site queries database for each visitor
```

## Recommendation for Calgary Analytica

**Start with Static Dashboard** because:

1. **You already run Python locally** - No change to workflow
2. **Monthly updates** - Perfect for static approach
3. **Cost-effective** - Save $15/month
4. **Simpler** - Less to manage and debug
5. **Faster for users** - Better UX
6. **Easy migration** - Can switch to dynamic later if needed

## Both Are Fully Interactive!

Remember: "Static" doesn't mean non-interactive. Both dashboards have:
- Clickable filters
- Hover tooltips
- Zoom/pan on charts
- Dynamic calculations
- Responsive design

The only difference is where the data comes from!

## Architecture Diagrams

### Static Architecture
```
Your Computer          Web Host           User's Browser
    |                     |                     |
    |-- Python -->        |                     |
    |   (monthly)         |                     |
    |                     |                     |
    |-- Upload JSON -->   |                     |
                          |                     |
                          |<-- Request ---------|
                          |                     |
                          |--- HTML/JS/JSON --->|
                                                |
                                          (Interactive Dashboard)
```

### Dynamic Architecture
```
Your Computer          Web Server          User's Browser
    |                     |                     |
    |-- Python -->        |                     |
    |   (monthly)         |                     |
    |                     |                     |
    |-- Upload DB ------->|                     |
                          |                     |
                          |<-- Request ---------|
                          |                     |
                          |-- PHP queries DB    |
                          |                     |
                          |--- Generated HTML-->|
                                                |
                                          (Interactive Dashboard)
```

## Try Both!

Test both dashboards locally to see they work identically from a user perspective. The choice is about infrastructure, not features!