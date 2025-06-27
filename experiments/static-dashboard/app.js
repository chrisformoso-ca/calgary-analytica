// Static Dashboard - Pure JavaScript, No Server Required
// This file runs entirely in the user's browser

let housingData = [];
let filteredData = [];

// Load data from JSON file
async function loadData() {
    try {
        const response = await fetch('data/housing.json');
        const jsonData = await response.json();
        housingData = jsonData.data;
        
        // Process data: parse dates and numbers
        housingData.forEach(d => {
            d.date = new Date(d.date + '-01'); // Convert YYYY-MM to Date
            d.benchmark_price = +d.benchmark_price;
            d.total_sales = +d.total_sales;
            d.price_change_yoy = +d.price_change_yoy;
        });
        
        updateDashboard();
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('avgPrice').textContent = 'Error loading data';
    }
}

// Update dashboard with current filters
function updateDashboard() {
    const propertyType = document.getElementById('propertyFilter').value;
    const metric = document.getElementById('metricFilter').value;
    
    // Filter data
    filteredData = propertyType === 'all' 
        ? housingData 
        : housingData.filter(d => d.property_type === propertyType);
    
    // Update stats cards
    updateStats();
    
    // Update chart
    updateChart(metric);
}

// Calculate and display statistics
function updateStats() {
    if (filteredData.length === 0) return;
    
    // Get latest month data
    const latestDate = d3.max(filteredData, d => d.date);
    const latestData = filteredData.filter(d => d.date.getTime() === latestDate.getTime());
    
    // Calculate averages
    const avgPrice = d3.mean(latestData, d => d.benchmark_price);
    const totalSales = d3.sum(latestData, d => d.total_sales);
    const avgChange = d3.mean(latestData, d => d.price_change_yoy);
    
    // Update displays
    document.getElementById('avgPrice').textContent = '$' + avgPrice.toLocaleString('en-CA', {maximumFractionDigits: 0});
    document.getElementById('totalSales').textContent = totalSales.toLocaleString();
    
    // Price change
    const changeEl = document.getElementById('avgChange');
    changeEl.textContent = (avgChange > 0 ? '↑ ' : '↓ ') + Math.abs(avgChange).toFixed(1) + '% YoY';
    changeEl.className = avgChange > 0 ? 'stat-change positive' : 'stat-change negative';
    
    // Market trend
    const trend = avgChange > 5 ? 'Hot Market' : avgChange > 0 ? 'Growing' : 'Cooling';
    document.getElementById('marketTrend').textContent = trend;
    
    const trendEl = document.getElementById('trendDirection');
    trendEl.textContent = avgChange > 0 ? '↑ Upward trend' : '↓ Downward trend';
    trendEl.className = avgChange > 0 ? 'stat-change positive' : 'stat-change negative';
}

// Create/update the chart
function updateChart(metric) {
    // Clear existing chart
    d3.select('#chart').selectAll('*').remove();
    
    // Set dimensions
    const margin = {top: 20, right: 80, bottom: 50, left: 70};
    const width = document.getElementById('chart').offsetWidth - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;
    
    // Create SVG
    const svg = d3.select('#chart')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Group data by property type
    const nestedData = d3.group(filteredData, d => d.property_type);
    
    // Set scales
    const x = d3.scaleTime()
        .domain(d3.extent(filteredData, d => d.date))
        .range([0, width]);
    
    const y = d3.scaleLinear()
        .domain([0, d3.max(filteredData, d => d[metric])])
        .range([height, 0]);
    
    // Color scale
    const color = d3.scaleOrdinal()
        .domain(['Detached', 'Semi-Detached', 'Row', 'Apartment'])
        .range(['#3498db', '#e74c3c', '#2ecc71', '#f39c12']);
    
    // Add axes
    g.append('g')
        .attr('class', 'axis')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickFormat(d3.timeFormat('%b %Y')));
    
    g.append('g')
        .attr('class', 'axis')
        .call(d3.axisLeft(y).tickFormat(d => {
            if (metric === 'benchmark_price') return '$' + d3.format('.2s')(d);
            if (metric === 'price_change_yoy') return d + '%';
            return d;
        }));
    
    // Add axis labels
    g.append('text')
        .attr('class', 'axis-label')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - margin.left)
        .attr('x', 0 - (height / 2))
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .text(metric === 'benchmark_price' ? 'Benchmark Price ($)' : 
              metric === 'total_sales' ? 'Total Sales' : 
              'Year-over-Year Change (%)');
    
    // Line generator
    const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d[metric]));
    
    // Draw lines for each property type
    nestedData.forEach((data, propertyType) => {
        // Sort by date
        data.sort((a, b) => a.date - b.date);
        
        // Draw line
        g.append('path')
            .datum(data)
            .attr('class', 'line')
            .attr('d', line)
            .style('stroke', color(propertyType));
        
        // Add dots
        g.selectAll(`.dot-${propertyType}`)
            .data(data)
            .enter().append('circle')
            .attr('class', 'dot')
            .attr('cx', d => x(d.date))
            .attr('cy', d => y(d[metric]))
            .attr('r', 4)
            .style('fill', color(propertyType))
            .on('mouseover', function(event, d) {
                showTooltip(event, d, metric);
            })
            .on('mouseout', hideTooltip);
    });
    
    // Add legend
    const legend = svg.append('g')
        .attr('transform', `translate(${width + margin.left + 10}, ${margin.top})`);
    
    const legendItems = Array.from(nestedData.keys());
    
    legendItems.forEach((propertyType, i) => {
        const legendRow = legend.append('g')
            .attr('transform', `translate(0, ${i * 20})`);
        
        legendRow.append('rect')
            .attr('width', 10)
            .attr('height', 10)
            .attr('fill', color(propertyType));
        
        legendRow.append('text')
            .attr('x', 15)
            .attr('y', 10)
            .style('font-size', '12px')
            .text(propertyType);
    });
}

// Tooltip functions
function showTooltip(event, d, metric) {
    const tooltip = document.getElementById('tooltip');
    
    let content = `
        <strong>${d.property_type}</strong><br>
        ${d3.timeFormat('%B %Y')(d.date)}<br>
    `;
    
    if (metric === 'benchmark_price') {
        content += `Price: $${d.benchmark_price.toLocaleString()}`;
    } else if (metric === 'total_sales') {
        content += `Sales: ${d.total_sales}`;
    } else {
        content += `YoY Change: ${d.price_change_yoy.toFixed(1)}%`;
    }
    
    tooltip.innerHTML = content;
    tooltip.style.opacity = 1;
    tooltip.style.left = (event.pageX + 10) + 'px';
    tooltip.style.top = (event.pageY - 10) + 'px';
}

function hideTooltip() {
    document.getElementById('tooltip').style.opacity = 0;
}

// Event listeners
document.getElementById('propertyFilter').addEventListener('change', updateDashboard);
document.getElementById('metricFilter').addEventListener('change', updateDashboard);
document.getElementById('refreshBtn').addEventListener('click', loadData);

// Initialize dashboard on page load
loadData();