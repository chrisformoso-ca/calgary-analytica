// Dynamic Dashboard - JavaScript that works with PHP backend
// This fetches data from the PHP API instead of static JSON files

let housingData = [];
let filteredData = [];

// Load data from PHP API
async function loadData() {
    try {
        // Get current filter from URL or default
        const urlParams = new URLSearchParams(window.location.search);
        const propertyFilter = urlParams.get('property') || 'all';
        
        // Fetch from PHP API endpoint
        const response = await fetch(`api.php?property=${propertyFilter}`);
        const jsonData = await response.json();
        
        if (jsonData.success) {
            housingData = jsonData.data;
            
            // Process data: convert date strings to Date objects
            housingData.forEach(d => {
                d.date = new Date(d.date + '-01');
            });
            
            updateChart();
        }
    } catch (error) {
        console.error('Error loading data from API:', error);
    }
}

// Update chart (stats are already rendered by PHP)
function updateChart() {
    const metric = document.getElementById('metricFilter').value;
    
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
    const nestedData = d3.group(housingData, d => d.property_type);
    
    // Set scales
    const x = d3.scaleTime()
        .domain(d3.extent(housingData, d => d.date))
        .range([0, width]);
    
    const y = d3.scaleLinear()
        .domain([0, d3.max(housingData, d => d[metric])])
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
    
    // Add server indicator
    g.append('text')
        .attr('class', 'server-indicator')
        .attr('x', width - 100)
        .attr('y', -5)
        .style('font-size', '10px')
        .style('fill', '#e74c3c')
        .text('Live from Database');
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
    
    content += `<br>Inventory: ${d.inventory}`;
    
    tooltip.innerHTML = content;
    tooltip.style.opacity = 1;
    tooltip.style.left = (event.pageX + 10) + 'px';
    tooltip.style.top = (event.pageY - 10) + 'px';
}

function hideTooltip() {
    document.getElementById('tooltip').style.opacity = 0;
}

// Event listeners
document.getElementById('metricFilter').addEventListener('change', updateChart);

// Initialize on page load
loadData();