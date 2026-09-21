document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    const NAVY = '#1A1851';
    const GOLD = '#FCB316';
    const MUTED = '#68728A';
    const GRID = '#EDF0F5';

    function readJson(id, fallback = {}) {
        const element = document.getElementById(id);
        if (!element) return fallback;
        try {
            return JSON.parse(element.textContent || '{}');
        } catch (_) {
            return fallback;
        }
    }

    function formatPeso(value) {
        return `₱${Number(value || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    }

    function submitOnce(form) {
        if (!form || form.dataset.submitting === 'true') return;
        form.dataset.submitting = 'true';
        form.submit();
    }

    const periodForm = document.getElementById('analyticsPeriodForm');
    const periodSelect = document.getElementById('analyticsPeriod');
    const customDates = document.getElementById('analyticsCustomDates');
    periodSelect?.addEventListener('change', () => {
        const custom = periodSelect.value === 'custom';
        customDates?.classList.toggle('d-none', !custom);
        if (!custom) submitOnce(periodForm);
    });

    const groupingSelect = document.getElementById('salesGrouping');
    groupingSelect?.addEventListener('change', () => submitOnce(groupingSelect.form));

    ['forecastProduct', 'forecastHorizon'].forEach((id) => {
        const select = document.getElementById(id);
        select?.addEventListener('change', () => submitOnce(select.form));
    });

    document.querySelectorAll('.analytics-category-bars i[data-width]').forEach((bar) => {
        const width = Math.max(0, Math.min(100, Number(bar.dataset.width) || 0));
        bar.style.width = `${width}%`;
    });

    if (typeof Chart === 'undefined') return;

    Chart.defaults.font.family = 'Roboto, sans-serif';
    Chart.defaults.color = MUTED;

    function lineOptions({ yTitle, tooltipLabel, tooltipTitles = [] }) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 240 },
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    display: true,
                    align: 'start',
                    labels: {
                        boxWidth: 10,
                        boxHeight: 3,
                        color: NAVY,
                        font: { family: 'Montserrat', size: 10, weight: '600' },
                    },
                },
                tooltip: {
                    callbacks: {
                        title: (items) => tooltipTitles[items[0]?.dataIndex] || items[0]?.label || '',
                        label: tooltipLabel,
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    title: { display: true, text: 'Date / Time Period', color: MUTED, font: { size: 10, weight: '600' } },
                    ticks: { color: MUTED, maxRotation: 0, autoSkip: true, maxTicksLimit: 10, font: { size: 9 } },
                },
                y: {
                    beginAtZero: true,
                    grid: { color: GRID },
                    title: { display: true, text: yTitle, color: MUTED, font: { size: 10, weight: '600' } },
                    ticks: { color: MUTED, precision: 0, font: { size: 9 } },
                },
            },
        };
    }

    const salesCanvas = document.getElementById('marketplaceSalesChart');
    if (salesCanvas) {
        const data = readJson('marketplaceSalesChartData', {
            labels: [],
            sales: [],
            orders: [],
            tooltip_labels: [],
        });
        const options = lineOptions({
            yTitle: 'Sales Amount (₱)',
            tooltipTitles: data.tooltip_labels || [],
            tooltipLabel: (context) => {
                const value = Number(context.raw || 0);
                if (context.dataset.yAxisID === 'yOrders') {
                    return ` Orders: ${value} order${value === 1 ? '' : 's'}`;
                }
                return ` Sales (₱): ${formatPeso(value)}`;
            },
        });
        options.plugins.legend.position = 'top';
        options.plugins.legend.align = 'center';
        options.plugins.legend.labels = {
            ...options.plugins.legend.labels,
            boxWidth: 10,
            boxHeight: 10,
            padding: 24,
            usePointStyle: true,
            pointStyle: 'rect',
            pointStyleWidth: 10,
        };
        options.scales.x.grid = {
            display: false,
        };
        options.scales.x.title.display = false;
        options.scales.x.offset = false;
        options.scales.ySales = {
            ...options.scales.y,
            position: 'left',
            suggestedMax: 10000,
            title: { display: false },
        };
        options.scales.ySales.ticks.stepSize = 2000;
        options.scales.ySales.ticks.callback = (value) => {
            const amount = Number(value);
            return amount === 0 ? '₱0' : `₱${amount / 1000}K`;
        };
        options.scales.yOrders = {
            beginAtZero: true,
            suggestedMax: 50,
            position: 'right',
            grid: { drawOnChartArea: false },
            title: { display: false },
            ticks: {
                color: GOLD,
                precision: 0,
                stepSize: 10,
                font: { size: 9 },
            },
        };
        delete options.scales.y;
        new Chart(salesCanvas, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        type: 'line',
                        label: 'Sales (₱)',
                        data: (data.sales || []).map(Number),
                        yAxisID: 'ySales',
                        borderColor: NAVY,
                        backgroundColor: NAVY,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.35,
                        fill: false,
                        order: 1,
                    },
                    {
                        type: 'bar',
                        label: 'Orders',
                        data: (data.orders || []).map(Number),
                        yAxisID: 'yOrders',
                        borderColor: GOLD,
                        backgroundColor: GOLD,
                        borderWidth: 1,
                        borderRadius: 2,
                        borderSkipped: false,
                        maxBarThickness: 14,
                        order: 2,
                    },
                ],
            },
            options,
        });
    }

    const categoryCanvas = document.getElementById('marketplaceCategoryChart');
    if (categoryCanvas) {
        const data = readJson('marketplaceCategoryChartData', { labels: [], values: [] });
        new Chart(categoryCanvas, {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: (data.values || []).map(Number),
                    backgroundColor: [NAVY, GOLD, '#59577C', '#C9CAD5', '#8A5B00', '#E7E8EE'],
                    borderColor: '#FFFFFF',
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '66%',
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: (context) => ` ${context.label}: ${formatPeso(context.raw)}` } },
                },
            },
        });
    }

    const buyerCanvas = document.getElementById('buyerPurchaseChart');
    if (buyerCanvas) {
        const data = readJson('buyerPurchaseChartData', { labels: [], values: [], tooltip_labels: [] });
        const options = lineOptions({
            yTitle: 'Completed Orders',
            tooltipTitles: data.tooltip_labels || [],
            tooltipLabel: (context) => {
                const value = Number(context.raw || 0);
                return ` ${value} completed order${value === 1 ? '' : 's'}`;
            },
        });
        options.plugins.legend.display = false;
        new Chart(buyerCanvas, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Completed Orders',
                    data: (data.values || []).map(Number),
                    borderColor: NAVY,
                    backgroundColor: NAVY,
                    borderWidth: 2,
                    pointRadius: 2.5,
                    tension: 0.2,
                    fill: false,
                }],
            },
            options,
        });
    }

    const forecastCanvas = document.getElementById('demandForecastChart');
    if (forecastCanvas) {
        const data = readJson('demandForecastChartData', { labels: [], historical: [], forecast: [] });
        const options = lineOptions({
            yTitle: 'Units',
            tooltipLabel: (context) => ` ${context.dataset.label}: ${Number(context.raw || 0).toFixed(2)} units`,
        });
        new Chart(forecastCanvas, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Historical Demand',
                        data: data.historical || [],
                        borderColor: NAVY,
                        backgroundColor: NAVY,
                        borderWidth: 2,
                        pointRadius: 2,
                        tension: 0.2,
                        spanGaps: false,
                    },
                    {
                        label: 'Forecast',
                        data: data.forecast || [],
                        borderColor: GOLD,
                        backgroundColor: GOLD,
                        borderWidth: 2,
                        borderDash: [6, 4],
                        pointRadius: 2,
                        tension: 0.2,
                        spanGaps: false,
                    },
                ],
            },
            options,
        });
    }

    const peakCanvas = document.getElementById('peakSalesChart');
    if (peakCanvas) {
        const data = readJson('peakSalesChartData', { labels: [], values: [] });
        new Chart(peakCanvas, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Sales',
                    data: (data.values || []).map(Number),
                    backgroundColor: NAVY,
                    borderRadius: 3,
                    maxBarThickness: 28,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: (context) => ` Sales: ${formatPeso(context.raw)}` } },
                },
                scales: {
                    x: { grid: { display: false }, ticks: { color: MUTED, maxRotation: 0, font: { size: 8 } } },
                    y: {
                        beginAtZero: true,
                        grid: { color: GRID },
                        ticks: { color: MUTED, callback: (value) => `₱${Number(value).toLocaleString()}`, font: { size: 8 } },
                    },
                },
            },
        });
    }
});
