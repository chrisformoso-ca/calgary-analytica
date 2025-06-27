// Modern Dashboard - Highly Customized, NOT Vanilla D3!
// Using Chart.js, GSAP animations, and custom visualizations

let housingData = [];
let charts = {};
let currentFilter = 'all';
let currentTimeRange = '6M';

// Initialize dashboard
async function initDashboard() {
    await loadData();
    initializeCharts();
    setupEventListeners();
    animateEntrance();
    initializeMap();
}

// Load and process data
async function loadData() {
    try {
        const response = await fetch('data/housing.json');
        const jsonData = await response.json();
        housingData = jsonData.data;
        
        // Process dates
        housingData.forEach(d => {
            d.date = new Date(d.date + '-01');
            d.benchmark_price = +d.benchmark_price;
            d.total_sales = +d.total_sales;
            d.price_change_yoy = +d.price_change_yoy;
        });
        
        updateMetrics();
    } catch (error) {
        showToast('Error loading data', 'error');
    }
}

// Animate entrance
function animateEntrance() {
    gsap.from('.metric-card', {
        y: 50,
        opacity: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: 'power3.out'
    });
    
    gsap.from('.glassmorphism:not(.metric-card)', {
        scale: 0.9,
        opacity: 0,
        duration: 1,
        stagger: 0.15,
        delay: 0.3,
        ease: 'back.out(1.7)'
    });
}

// Update metric cards with animations
function updateMetrics() {
    const filteredData = getFilteredData();
    const latestData = getLatestData(filteredData);
    
    // Calculate metrics
    const avgPrice = d3.mean(latestData, d => d.benchmark_price);
    const totalSales = d3.sum(latestData, d => d.total_sales);
    const totalInventory = d3.sum(latestData, d => d.inventory);
    
    // Animate number changes
    animateValue('avgPrice', 0, avgPrice, 2000);
    animateValue('totalSales', 0, totalSales, 2000);
    animateValue('inventory', 0, totalInventory, 2000);
    
    // Update mini charts
    updateMiniCharts(filteredData);
}

// Smooth number animation
function animateValue(id, start, end, duration) {
    const element = document.getElementById(id);
    const increment = (end - start) / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current).toLocaleString();
    }, 16);
}

// Initialize all charts
function initializeCharts() {
    // Main trend chart
    const mainCtx = document.getElementById('mainChart').getContext('2d');
    charts.main = new Chart(mainCtx, {
        type: 'line',
        data: getMainChartData(),
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#e2e8f0',
                        padding: 20,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: '#fff',
                    bodyColor: '#e2e8f0',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (context.parsed.y !== null) {
                                label += ': $' + context.parsed.y.toLocaleString();
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { 
                        color: '#94a3b8',
                        callback: value => '$' + value.toLocaleString()
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
    
    // Distribution donut chart
    const distCtx = document.getElementById('distributionChart').getContext('2d');
    charts.distribution = new Chart(distCtx, {
        type: 'doughnut',
        data: getDistributionData(),
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return label + ': ' + percentage + '%';
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true
            }
        }
    });
    
    createDistributionLegend();
}

// Update mini sparkline charts
function updateMiniCharts(data) {
    const propertyTypes = ['Detached', 'Semi-Detached', 'Row', 'Apartment'];
    const avgPrices = propertyTypes.map(type => {
        const typeData = data.filter(d => d.property_type === type);
        return typeData.map(d => d.benchmark_price);
    });
    
    // Price mini chart
    const priceCtx = document.getElementById('miniPriceChart').getContext('2d');
    new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: Array(6).fill(''),
            datasets: [{
                data: avgPrices[0].slice(-6),
                borderColor: '#818cf8',
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 0,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
    
    // Similar for sales and inventory mini charts...
}

// Get filtered data based on current selections
function getFilteredData() {
    let filtered = housingData;
    
    if (currentFilter !== 'all') {
        filtered = filtered.filter(d => d.property_type === currentFilter);
    }
    
    // Apply time range filter
    const now = new Date();
    const ranges = {
        '1M': 1, '3M': 3, '6M': 6, '1Y': 12, 'ALL': 9999
    };
    const months = ranges[currentTimeRange];
    
    if (months !== 9999) {
        const cutoff = new Date(now.setMonth(now.getMonth() - months));
        filtered = filtered.filter(d => d.date >= cutoff);
    }
    
    return filtered;
}

// Get latest month data
function getLatestData(data) {
    const latestDate = d3.max(data, d => d.date);
    return data.filter(d => d.date.getTime() === latestDate.getTime());
}

// Prepare main chart data
function getMainChartData() {
    const filtered = getFilteredData();
    const grouped = d3.group(filtered, d => d.property_type);
    
    const colors = {
        'Detached': '#6366f1',
        'Semi-Detached': '#8b5cf6',
        'Row': '#ec4899',
        'Apartment': '#f59e0b'
    };
    
    const datasets = [];
    grouped.forEach((data, propertyType) => {
        data.sort((a, b) => a.date - b.date);
        
        datasets.push({
            label: propertyType,
            data: data.map(d => ({
                x: d.date,
                y: d.benchmark_price
            })),
            borderColor: colors[propertyType],
            backgroundColor: colors[propertyType] + '20',
            borderWidth: 3,
            tension: 0.4,
            pointRadius: 0,
            pointHoverRadius: 6,
            pointBackgroundColor: colors[propertyType],
            pointBorderColor: '#fff',
            pointBorderWidth: 2
        });
    });
    
    return { datasets };
}

// Get distribution data
function getDistributionData() {
    const latest = getLatestData(housingData);
    const grouped = d3.group(latest, d => d.property_type);
    
    const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b'];
    const labels = [];
    const data = [];
    
    let i = 0;
    grouped.forEach((values, type) => {
        labels.push(type);
        data.push(d3.sum(values, d => d.total_sales));
        i++;
    });
    
    return {
        labels,
        datasets: [{
            data,
            backgroundColor: colors,
            borderWidth: 0,
            spacing: 2
        }]
    };
}

// Create custom legend for distribution chart
function createDistributionLegend() {
    const container = document.getElementById('distributionLegend');
    const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b'];
    const labels = ['Detached', 'Semi-Detached', 'Row', 'Apartment'];
    
    labels.forEach((label, i) => {
        const item = document.createElement('div');
        item.className = 'legend-item';
        item.innerHTML = `
            <div class="legend-color" style="background: ${colors[i]}"></div>
            <span>${label}</span>
        `;
        container.appendChild(item);
    });
}

// Initialize Calgary map
function initializeMap() {
    const map = L.map('calgaryMap').setView([51.0447, -114.0719], 10);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© CARTO',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);
    
    // Add sample heat overlay for districts
    const districts = [
        { name: 'Downtown', lat: 51.0447, lng: -114.0719, heat: 0.9 },
        { name: 'Beltline', lat: 51.0380, lng: -114.0700, heat: 0.8 },
        { name: 'Kensington', lat: 51.0530, lng: -114.0870, heat: 0.7 },
        { name: 'Mission', lat: 51.0300, lng: -114.0650, heat: 0.75 },
        { name: 'Inglewood', lat: 51.0380, lng: -114.0350, heat: 0.6 }
    ];
    
    districts.forEach(district => {
        const color = district.heat > 0.7 ? '#ef4444' : district.heat > 0.5 ? '#f59e0b' : '#10b981';
        L.circle([district.lat, district.lng], {
            color: color,
            fillColor: color,
            fillOpacity: 0.5,
            radius: 1500
        }).addTo(map).bindPopup(`<b>${district.name}</b><br>Market Heat: ${(district.heat * 100).toFixed(0)}%`);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Property type buttons
    document.querySelectorAll('.property-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelector('.property-btn.active').classList.remove('active');
            this.classList.add('active');
            currentFilter = this.dataset.type;
            updateDashboard();
        });
    });
    
    // Chart type buttons
    document.querySelectorAll('.chart-type-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelector('.chart-type-btn.active').classList.remove('active');
            this.classList.add('active');
            changeChartType(this.dataset.chart);
        });
    });
    
    // Time range buttons
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelector('.time-btn.active').classList.remove('active');
            this.classList.add('active');
            currentTimeRange = this.dataset.range;
            updateDashboard();
        });
    });
    
    // FAB menu
    document.getElementById('fabMenu').addEventListener('click', () => {
        showToast('Export feature coming soon!', 'info');
    });
    
    // Time slider
    document.getElementById('timeSlider').addEventListener('input', function(e) {
        const percentage = e.target.value;
        showToast(`Viewing ${percentage}% of timeline`, 'info');
    });
}

// Change main chart type
function changeChartType(type) {
    charts.main.config.type = type;
    
    if (type === 'bar') {
        charts.main.config.options.scales.x.stacked = true;
        charts.main.config.options.scales.y.stacked = true;
    } else {
        charts.main.config.options.scales.x.stacked = false;
        charts.main.config.options.scales.y.stacked = false;
    }
    
    charts.main.update('active');
}

// Update all dashboard elements
function updateDashboard() {
    updateMetrics();
    charts.main.data = getMainChartData();
    charts.main.update('active');
    charts.distribution.data = getDistributionData();
    charts.distribution.update('active');
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <div style="color: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#6366f1'}">
            ${message}
        </div>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize on load
document.addEventListener('DOMContentLoaded', initDashboard);