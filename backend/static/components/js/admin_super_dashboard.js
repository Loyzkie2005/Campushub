document.addEventListener('DOMContentLoaded', () => {
    const root = document.querySelector('.super-dashboard');
    if (!root) return;

    // Preserve the other chart's period and any existing URL parameters.
    [['revenuePeriodSelect', 'grouping'], ['facilityPeriodSelect', 'facility_days']].forEach(([id, parameter]) => {
        document.getElementById(id)?.addEventListener('change', (event) => {
            const url = new URL(window.location.href);
            url.searchParams.set(parameter, event.target.value);
            if (parameter === 'grouping') url.searchParams.delete('sales_days');
            window.location.assign(url.toString());
        });
    });

    const chatStatus = document.getElementById('superChatStatus');
    if (chatStatus?.dataset.healthUrl) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 2500);
        fetch(chatStatus.dataset.healthUrl, { cache: 'no-store', signal: controller.signal })
            .then((response) => {
                if (!response.ok) throw new Error('Health check failed');
                chatStatus.textContent = 'Online';
                chatStatus.classList.remove('service-state--checking');
            })
            .catch(() => {
                chatStatus.textContent = 'Offline';
                chatStatus.title = 'Chat health endpoint could not be reached from this browser.';
                chatStatus.classList.replace('service-state--checking', 'service-state--offline');
            })
            .finally(() => clearTimeout(timeout));
    } else if (chatStatus) {
        chatStatus.textContent = 'Not configured';
    }

    const navy = '#1A1851';
    const gold = '#FCB316';
    const pesos = new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' });
    function readData(id) {
        return JSON.parse(document.getElementById(id).textContent);
    }
    function options() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#606273', maxTicksLimit: 7, maxRotation: 0 } },
                y: { beginAtZero: true, ticks: { precision: 0, color: '#606273' }, grid: { color: '#e3e5eb' } },
            },
        };
    }
    if (typeof Chart === 'undefined') {
        root.querySelectorAll('.overview-chart-canvas').forEach((container) => {
            const message = document.createElement('p');
            message.className = 'overview-empty';
            message.textContent = 'Chart could not load. Reload to try again.';
            container.replaceWith(message);
        });
        return;
    }
    Chart.defaults.font.family = 'Montserrat, sans-serif';
    Chart.defaults.font.size = 10;

    const salesCanvas = document.getElementById('superSalesChart');
    if (salesCanvas) {
        const data = readData('superSalesData');
        const config = options();
        delete config.scales.y;
        config.scales.ySales = {
            position: 'left', beginAtZero: true,
            ticks: { color: '#606273', callback: (value) => `\u20b1${Number(value).toLocaleString()}` },
            grid: { color: '#e3e5eb' },
        };
        config.scales.yOrders = {
            position: 'right', beginAtZero: true,
            ticks: { precision: 0, color: navy },
            grid: { drawOnChartArea: false },
        };
        config.plugins.tooltip = { callbacks: {
            title: (items) => data.tooltip_labels?.[items[0]?.dataIndex] || items[0]?.label || '',
            label: (item) => item.dataset.yAxisID === 'ySales'
                ? `Sales: ${pesos.format(item.parsed.y)}`
                : `${item.parsed.y} ${item.parsed.y === 1 ? 'order' : 'orders'}`,
        } };
        new Chart(salesCanvas, {
            type: 'line',
            data: { labels: data.labels, datasets: [
                { label: 'Sales (\u20b1)', data: data.values, yAxisID: 'ySales', borderColor: navy, backgroundColor: navy, borderWidth: 2, pointRadius: 3, pointHoverRadius: 5, tension: 0.25, fill: false, order: 0 },
                { label: 'Orders', type: 'bar', data: data.order_values, yAxisID: 'yOrders', backgroundColor: gold, maxBarThickness: 16, order: 1 },
            ] },
            options: config,
        });
    }

    const bookingsCanvas = document.getElementById('superBookingsChart');
    if (bookingsCanvas) {
        const data = readData('superBookingsData');
        // Summarize the existing status series without querying or changing eligibility.
        const totals = data.labels.map((_, index) => ['approved', 'pending', 'completed', 'cancelled']
            .reduce((total, status) => total + Number(data[status]?.[index] || 0), 0));
        new Chart(bookingsCanvas, {
            type: 'bar',
            data: { labels: data.labels, datasets: [{ label: 'Bookings', data: totals, backgroundColor: navy, maxBarThickness: 20 }] },
            options: options(),
        });
    }
});

