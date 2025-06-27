<?php
// Dynamic Dashboard - PHP Backend with Database
// This runs on the server and queries a real database

// Database connection
$db = new SQLite3('database/sample.db');

// Get filter from query parameters
$propertyFilter = isset($_GET['property']) ? $_GET['property'] : 'all';

// Fetch latest stats from database
$query = "SELECT 
    property_type,
    benchmark_price,
    total_sales,
    price_change_yoy,
    date
FROM housing_data 
WHERE date = (SELECT MAX(date) FROM housing_data)";

if ($propertyFilter !== 'all') {
    $query .= " AND property_type = :property";
}

$stmt = $db->prepare($query);
if ($propertyFilter !== 'all') {
    $stmt->bindValue(':property', $propertyFilter, SQLITE3_TEXT);
}

$latestData = [];
$result = $stmt->execute();
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $latestData[] = $row;
}

// Calculate aggregates
$avgPrice = 0;
$totalSales = 0;
$avgChange = 0;

if (count($latestData) > 0) {
    foreach ($latestData as $row) {
        $avgPrice += $row['benchmark_price'];
        $totalSales += $row['total_sales'];
        $avgChange += $row['price_change_yoy'];
    }
    $avgPrice = $avgPrice / count($latestData);
    $avgChange = $avgChange / count($latestData);
}

$db->close();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calgary Housing Dashboard - Dynamic PHP Version</title>
    <link rel="stylesheet" href="style.css">
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>Calgary Housing Market Dashboard</h1>
            <p class="subtitle">Dynamic PHP Version - Database-Powered</p>
        </header>

        <div class="controls">
            <div class="filter-group">
                <label>Property Type:</label>
                <select id="propertyFilter" onchange="updateFilter()">
                    <option value="all" <?= $propertyFilter === 'all' ? 'selected' : '' ?>>All Types</option>
                    <option value="Detached" <?= $propertyFilter === 'Detached' ? 'selected' : '' ?>>Detached</option>
                    <option value="Semi-Detached" <?= $propertyFilter === 'Semi-Detached' ? 'selected' : '' ?>>Semi-Detached</option>
                    <option value="Row" <?= $propertyFilter === 'Row' ? 'selected' : '' ?>>Row House</option>
                    <option value="Apartment" <?= $propertyFilter === 'Apartment' ? 'selected' : '' ?>>Apartment/Condo</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Metric:</label>
                <select id="metricFilter">
                    <option value="benchmark_price">Benchmark Price</option>
                    <option value="total_sales">Total Sales</option>
                    <option value="price_change_yoy">Year-over-Year Change %</option>
                </select>
            </div>

            <div class="filter-group">
                <button id="refreshBtn" onclick="location.reload()">Refresh Data</button>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Average Price</h3>
                <p class="stat-value">$<?= number_format($avgPrice, 0) ?></p>
                <p class="stat-change <?= $avgChange > 0 ? 'positive' : 'negative' ?>">
                    <?= $avgChange > 0 ? '↑' : '↓' ?> <?= number_format(abs($avgChange), 1) ?>% YoY
                </p>
            </div>
            <div class="stat-card">
                <h3>Total Sales</h3>
                <p class="stat-value"><?= number_format($totalSales) ?></p>
                <p class="stat-change">Last Month</p>
            </div>
            <div class="stat-card">
                <h3>Market Trend</h3>
                <p class="stat-value">
                    <?= $avgChange > 5 ? 'Hot Market' : ($avgChange > 0 ? 'Growing' : 'Cooling') ?>
                </p>
                <p class="stat-change <?= $avgChange > 0 ? 'positive' : 'negative' ?>">
                    <?= $avgChange > 0 ? '↑ Upward trend' : '↓ Downward trend' ?>
                </p>
            </div>
        </div>

        <div class="chart-container">
            <div id="chart"></div>
            <div id="tooltip" class="tooltip"></div>
        </div>

        <footer>
            <p>This dashboard is powered by PHP and queries a SQLite database in real-time.</p>
            <p>Data updates: Database can be updated on the server anytime.</p>
        </footer>
    </div>

    <script>
        // Pass PHP filter to JavaScript
        const currentPropertyFilter = '<?= $propertyFilter ?>';
        
        function updateFilter() {
            const filter = document.getElementById('propertyFilter').value;
            window.location.href = '?property=' + filter;
        }
    </script>
    <script src="app.js"></script>
</body>
</html>