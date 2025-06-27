<?php
// API endpoint for fetching chart data
// Returns JSON data for JavaScript to consume

header('Content-Type: application/json');

// Database connection
$db = new SQLite3('database/sample.db');

// Get parameters
$propertyFilter = isset($_GET['property']) ? $_GET['property'] : 'all';
$startDate = isset($_GET['start']) ? $_GET['start'] : '2024-01';
$endDate = isset($_GET['end']) ? $_GET['end'] : '2024-12';

// Build query
$query = "SELECT 
    date,
    property_type,
    benchmark_price,
    total_sales,
    price_change_yoy,
    inventory
FROM housing_data 
WHERE date BETWEEN :start AND :end";

if ($propertyFilter !== 'all') {
    $query .= " AND property_type = :property";
}

$query .= " ORDER BY date, property_type";

// Prepare and execute
$stmt = $db->prepare($query);
$stmt->bindValue(':start', $startDate, SQLITE3_TEXT);
$stmt->bindValue(':end', $endDate, SQLITE3_TEXT);
if ($propertyFilter !== 'all') {
    $stmt->bindValue(':property', $propertyFilter, SQLITE3_TEXT);
}

// Fetch results
$data = [];
$result = $stmt->execute();
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    // Convert numeric strings to numbers for JavaScript
    $row['benchmark_price'] = (float)$row['benchmark_price'];
    $row['total_sales'] = (int)$row['total_sales'];
    $row['price_change_yoy'] = (float)$row['price_change_yoy'];
    $row['inventory'] = (int)$row['inventory'];
    $data[] = $row;
}

// Get metadata
$metaQuery = "SELECT 
    COUNT(DISTINCT date) as months,
    COUNT(DISTINCT property_type) as property_types,
    MIN(date) as start_date,
    MAX(date) as end_date
FROM housing_data";

$metaResult = $db->query($metaQuery);
$metadata = $metaResult->fetchArray(SQLITE3_ASSOC);

$db->close();

// Return JSON response
echo json_encode([
    'success' => true,
    'metadata' => [
        'source' => 'Calgary Real Estate Board',
        'last_updated' => date('Y-m-d'),
        'total_months' => $metadata['months'],
        'property_types' => $metadata['property_types'],
        'date_range' => [
            'start' => $metadata['start_date'],
            'end' => $metadata['end_date']
        ]
    ],
    'data' => $data
]);
?>