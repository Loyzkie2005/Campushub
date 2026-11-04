document.addEventListener('DOMContentLoaded', async () => {
    // Keep this page's requested typeface in canvas labels without changing shared charts.
    if (typeof Chart !== 'undefined') Chart.register({
        id: 'marketplaceDashboardTypeface',
        beforeInit(chart) {
            if (!chart.canvas.closest('.marketplace-dashboard')) return;
            const family = getComputedStyle(chart.canvas).fontFamily;
            for (const scale of Object.values(chart.options.scales || {})) {
                if (scale.ticks?.font) scale.ticks.font.family = family;
                if (scale.title?.font) scale.title.font.family = family;
            }
            const tooltip = chart.options.plugins?.tooltip;
            if (tooltip) {
                tooltip.titleFont = {...tooltip.titleFont, family};
                tooltip.bodyFont = {...tooltip.bodyFont, family};
            }
        },
    });
    const refresh = document.getElementById('marketplaceDashboardRefresh');
    if (refresh) {
        refresh.hidden = false;
        refresh.addEventListener('click', () => {
            // Reload applied URL state, not any unfinished custom-range edits.
            // The existing authorized GET view reads saved data without running mining.
            window.location.reload();
        });
    }

    async function renderTopProducts() {
        const canvas = document.getElementById('marketplaceTopProductsChart');
        if (!canvas) return;
        const error = document.getElementById('marketplaceTopProductsError');
        try {
            if (typeof Chart === 'undefined') throw new Error('Chart library unavailable');
            const rows = JSON.parse(document.getElementById('marketplaceTopProductsData').textContent);
            if (document.fonts) await document.fonts.ready;
            new Chart(canvas, {
                type: 'bar',
                data: { labels: rows.map(row => row.product_name), datasets: [{
                    label: 'Units Sold', data: rows.map(row => row.units_sold),
                    backgroundColor: '#1A1851', borderRadius: 3, maxBarThickness: 40,
                }] },
                options: {
                    responsive: true, maintainAspectRatio: false, animation: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { title: { display: true, text: 'Product' }, grid: { display: false },
                            ticks: { font: { family: 'Inter, sans-serif' }, callback(value) {
                                const label = this.getLabelForValue(value);
                                return label.length > 18 ? label.slice(0, 16) + '\u2026' : label;
                            } } },
                        y: { beginAtZero: true, title: { display: true, text: 'Units Sold' },
                            ticks: { precision: 0, font: { family: 'Inter, sans-serif' } }, grid: { color: '#E8EAF0' } },
                    },
                },
            });
        } catch (_) {
            canvas.parentElement.hidden = true;
            error.hidden = false;
        }
    }

    async function renderCategorySales() {
        const canvas = document.getElementById('marketplaceCategorySalesChart');
        if (!canvas) return;
        try {
            if (typeof Chart === 'undefined') throw new Error('Chart library unavailable');
            const data = JSON.parse(document.getElementById('marketplaceCategorySalesData').textContent);
            if (document.fonts) await document.fonts.ready;
            const money = new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' });
            const numbers = new Intl.NumberFormat('en-PH', { maximumFractionDigits: 1 });
            new Chart(canvas, {
                type: 'doughnut',
                data: { labels: data.labels, datasets: [{ data: data.values,
                    backgroundColor: data.colors, borderColor: '#FFFFFF', borderWidth: 2, hoverOffset: 3 }] },
                options: {
                    responsive: true, maintainAspectRatio: false, animation: false, cutout: '68%',
                    plugins: { legend: { display: false }, tooltip: {
                        bodyFont: { family: 'Inter, sans-serif' },
                        callbacks: { label: context => `${context.label} \u2014 ${money.format(context.raw)} \u2014 ${numbers.format(data.percentages[context.dataIndex])}%` },
                    } },
                },
            });
        } catch (_) {
            canvas.parentElement.hidden = true;
            document.getElementById('marketplaceCategorySalesError').hidden = false;
        }
    }
    await Promise.all([renderTopProducts(), renderCategorySales()]);
});
