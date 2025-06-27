// Simplified version with better error handling

let housingData = [];

// Initialize dashboard with error handling
async function initDashboard() {
    try {
        await loadData();
        updateMetrics();
        createSimpleChart();
        animateEntrance();
        console.log('Dashboard initialized successfully');
    } catch (error) {
        console.error('Dashboard initialization error:', error);
        document.querySelector('.dashboard').innerHTML += `
            <div style="color: red; padding: 20px;">
                Error loading dashboard: ${error.message}
            </div>
        `;
    }
}

// Load data with better error handling
async function loadData() {
    try {
        const response = await fetch('data/housing.json');
        if (!response.ok) throw new Error('Failed to load data');
        
        const jsonData = await response.json();
        housingData = jsonData.data;
        
        // Process data
        housingData.forEach(d => {
            d.date = new Date(d.date + '-01');
            d.benchmark_price = +d.benchmark_price;
            d.total_sales = +d.total_sales;
        });
        
        console.log('Data loaded:', housingData.length, 'records');
    } catch (error) {
        console.error('Error loading data:', error);
        throw error;
    }
}

// Simple entrance animation
function animateEntrance() {
    // Only animate if GSAP is loaded
    if (typeof gsap !== 'undefined') {
        gsap.from('.metric-card', {
            y: 30,
            opacity: 0,
            duration: 0.6,
            stagger: 0.1
        });
    }
}

// Update metrics with simple numbers
function updateMetrics() {
    if (housingData.length === 0) return;
    
    // Get latest month data
    const latestDate = Math.max(...housingData.map(d => d.date.getTime()));
    const latestData = housingData.filter(d => d.date.getTime() === latestDate);
    
    // Calculate simple averages
    const avgPrice = latestData.reduce((sum, d) => sum + d.benchmark_price, 0) / latestData.length;
    const totalSales = latestData.reduce((sum, d) => sum + d.total_sales, 0);
    
    // Update display
    document.getElementById('avgPrice').textContent = Math.round(avgPrice).toLocaleString();
    document.getElementById('totalSales').textContent = totalSales.toLocaleString();
    document.getElementById('inventory').textContent = '3,456'; // Placeholder
}

// Create a simple chart without Chart.js complexity
function createSimpleChart() {
    const canvas = document.getElementById('mainChart');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = 300;
    
    // Draw simple line chart
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    // Group by property type
    const detached = housingData.filter(d => d.property_type === 'Detached');
    detached.sort((a, b) => a.date - b.date);
    
    // Simple line drawing
    const width = canvas.width - 60;
    const height = canvas.height - 60;
    const xStep = width / (detached.length - 1);
    
    const prices = detached.map(d => d.benchmark_price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice;
    
    detached.forEach((d, i) => {
        const x = 30 + (i * xStep);
        const y = 30 + height - ((d.benchmark_price - minPrice) / priceRange * height);
        
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    
    ctx.stroke();
    
    // Add simple label
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '14px sans-serif';
    ctx.fillText('Detached Home Prices', 30, 20);
}

// Property filter functionality
function filterByProperty(propertyType) {
    console.log('Filtering by:', propertyType);
    
    // Show feedback
    showToast(`Showing ${propertyType === 'all' ? 'all properties' : propertyType}`, 'info');
    
    // Update chart with filtered data
    updateChartForProperty(propertyType);
    
    // Update metrics
    updateMetricsForProperty(propertyType);
}

// Update chart for selected property
function updateChartForProperty(propertyType) {
    const canvas = document.getElementById('mainChart');
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Filter data
    let filtered = propertyType === 'all' 
        ? housingData 
        : housingData.filter(d => d.property_type === propertyType);
    
    if (filtered.length === 0) return;
    
    // Get unique property types in filtered data
    const types = [...new Set(filtered.map(d => d.property_type))];
    const colors = {
        'Detached': '#6366f1',
        'Semi-Detached': '#8b5cf6', 
        'Row': '#ec4899',
        'Apartment': '#f59e0b'
    };
    
    const width = canvas.width - 60;
    const height = canvas.height - 60;
    
    // Find price range across all data
    const allPrices = filtered.map(d => d.benchmark_price);
    const minPrice = Math.min(...allPrices);
    const maxPrice = Math.max(...allPrices);
    const priceRange = maxPrice - minPrice;
    
    // Draw line for each property type
    types.forEach((type, typeIndex) => {
        const typeData = filtered.filter(d => d.property_type === type);
        typeData.sort((a, b) => a.date - b.date);
        
        ctx.strokeStyle = colors[type] || '#666';
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        const xStep = width / (typeData.length - 1);
        
        typeData.forEach((d, i) => {
            const x = 30 + (i * xStep);
            const y = 30 + height - ((d.benchmark_price - minPrice) / priceRange * height);
            
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
            
            // Draw dots
            ctx.fillStyle = colors[type] || '#666';
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });
        
        ctx.stroke();
    });
    
    // Add labels
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '14px sans-serif';
    ctx.fillText(propertyType === 'all' ? 'All Property Types' : propertyType + ' Prices', 30, 20);
}

// Update metrics for selected property
function updateMetricsForProperty(propertyType) {
    const filtered = propertyType === 'all'
        ? housingData
        : housingData.filter(d => d.property_type === propertyType);
    
    if (filtered.length === 0) return;
    
    const latestDate = Math.max(...filtered.map(d => d.date.getTime()));
    const latestData = filtered.filter(d => d.date.getTime() === latestDate);
    
    const avgPrice = latestData.reduce((sum, d) => sum + d.benchmark_price, 0) / latestData.length;
    const totalSales = latestData.reduce((sum, d) => sum + d.total_sales, 0);
    
    // Animate the number changes
    animateNumber('avgPrice', parseInt(document.getElementById('avgPrice').textContent.replace(/,/g, '')), Math.round(avgPrice));
    animateNumber('totalSales', parseInt(document.getElementById('totalSales').textContent.replace(/,/g, '')), totalSales);
}

// Animate number changes
function animateNumber(id, start, end) {
    const element = document.getElementById(id);
    const duration = 1000;
    const steps = 60;
    const increment = (end - start) / steps;
    let current = start;
    let step = 0;
    
    const timer = setInterval(() => {
        current += increment;
        step++;
        
        if (step >= steps) {
            current = end;
            clearInterval(timer);
        }
        
        element.textContent = Math.round(current).toLocaleString();
    }, duration / steps);
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.cssText = `
        background: rgba(99, 102, 241, 0.9);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 10px;
        animation: slideIn 0.3s ease-out;
    `;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// Simple property button handlers
document.addEventListener('DOMContentLoaded', () => {
    // Initialize dashboard
    initDashboard();
    
    // Property buttons with functionality
    document.querySelectorAll('.property-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelector('.property-btn.active')?.classList.remove('active');
            this.classList.add('active');
            filterByProperty(this.dataset.type);
        });
    });
    
    // Time buttons with feedback
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelector('.time-btn.active')?.classList.remove('active');
            this.classList.add('active');
            showToast(`Showing last ${this.dataset.range}`, 'info');
        });
    });
    
    // Chart type buttons
    document.querySelectorAll('.chart-type-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelector('.chart-type-btn.active')?.classList.remove('active');
            this.classList.add('active');
            showToast(`${this.dataset.chart} chart selected`, 'info');
        });
    });
    
    // FAB button
    document.getElementById('fabMenu')?.addEventListener('click', () => {
        showToast('Export coming soon!', 'info');
    });
    
    // Hide complex elements
    document.getElementById('distributionChart')?.parentElement.style.display = 'none';
    document.getElementById('calgaryMap')?.parentElement.style.display = 'none';
});