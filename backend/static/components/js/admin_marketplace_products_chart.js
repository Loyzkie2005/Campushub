document.addEventListener('DOMContentLoaded', async () => {
    const card = document.getElementById('topSellingProductsCard');
    const canvas = document.getElementById('topSellingProductsChart');
    if (!card || !canvas) return;
    let rows = JSON.parse(document.getElementById('topSellingProductsData').textContent).slice(0, 5);
    const content = card.querySelector('[data-products-content]');
    const empty = card.querySelector('[data-products-empty]');
    const error = card.querySelector('[data-products-error]');
    const fallback = card.querySelector('[data-products-chart-error]');
    const description = card.querySelector('[data-products-description]');
    const live = card.querySelector('[data-products-live]');
    const numbers = new Intl.NumberFormat('en-PH');
    let chart;
    let chartFailed = false;
    let active = -1;
    function sync() {
        error.hidden = true;
        content.hidden = !rows.length || chartFailed;
        fallback.hidden = !rows.length || !chartFailed;
        empty.hidden = Boolean(rows.length);
        const list = rows.map(product => {
            const item = document.createElement('li');
            item.textContent = `${product.product_name}: ${numbers.format(product.units_sold)} units sold.`;
            return item;
        });
        description.replaceChildren(...list);
        if (rows.length && !chart && !chartFailed) createChart();
        if (chart && rows.length) {
            chart.data.labels = rows.map(p => p.product_name);
            chart.data.datasets[0].data = rows.map(p => p.units_sold);
            chart.update('none');
            requestAnimationFrame(() => chart.resize());
        }
        content.hidden = !rows.length || chartFailed;
        fallback.hidden = !rows.length || !chartFailed;
        description.classList.toggle('visually-hidden', !rows.length || !chartFailed);
        active = -1;
    }
    sync();
    document.addEventListener('campushub:dashboard-data', event => {
        rows = event.detail.marketplace.top_products.slice(0, 5);
        sync();
    });
    document.addEventListener('campushub:dashboard-load-error', () => {
        content.hidden = empty.hidden = true;
        fallback.hidden = true;
        description.classList.add('visually-hidden');
        error.hidden = false;
    });
    if (document.fonts) await document.fonts.ready;
    function createChart() {
        try {
            if (typeof Chart === 'undefined') throw new Error('Chart library unavailable');
            const font = { family: 'Inter, sans-serif', size: 12 };
            chart = new Chart(canvas, {
                type: 'bar',
                data: { labels: rows.map(p => p.product_name), datasets: [{ label: 'Units sold',
                    data: rows.map(p => p.units_sold), backgroundColor: '#1A1851',
                    borderRadius: 3, maxBarThickness: 48, categoryPercentage: 0.7, barPercentage: 0.7 }] },
                options: {
                    responsive: true, maintainAspectRatio: false, animation: false,
                    plugins: { legend: { display: false }, tooltip: { titleFont: font, bodyFont: font,
                        backgroundColor: '#1A1851', callbacks: {
                            title: items => rows[items[0]?.dataIndex]?.product_name || '',
                            label: context => `${numbers.format(context.parsed.y)} units sold`,
                        } } },
                    scales: {
                        x: { grid: { display: false }, ticks: { font, color: '#626781', maxRotation: 0, autoSkip: false,
                            callback: function(value) {
                                const name = this.getLabelForValue(value);
                                const limit = Math.max(5, Math.min(16, Math.floor(this.chart.width / Math.max(1, rows.length) / 6) - 2));
                                if (name.length <= limit) return name;
                                const split = name.lastIndexOf(' ', limit);
                                if (split > 0) {
                                    const rest = name.slice(split + 1);
                                    return [name.slice(0, split), rest.length > limit ? `${rest.slice(0, limit - 1)}…` : rest];
                                }
                                return `${name.slice(0, limit - 1)}…`;
                            } } },
                        y: { beginAtZero: true, suggestedMax: 1, border: { display: false }, grid: { color: '#E8EAF0' },
                            title: { display: true, text: 'Units sold', font, color: '#626781' },
                            ticks: { precision: 0, font, color: '#626781' } },
                    },
                },
            });
            canvas.addEventListener('keydown', event => {
                if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || !rows.length ||
                    document.querySelector('[data-global-dashboard]').getAttribute('aria-busy') === 'true' || !error.hidden) return;
                event.preventDefault();
                active = event.key === 'Home' ? 0 : event.key === 'End' ? rows.length - 1 :
                    Math.max(0, Math.min(rows.length - 1, active + (event.key === 'ArrowLeft' ? -1 : 1)));
                live.textContent = `${rows[active].product_name}: ${numbers.format(rows[active].units_sold)} units sold.`;
                const items = [{ datasetIndex: 0, index: active }];
                chart.setActiveElements(items);
                chart.tooltip.setActiveElements(items, chart.getDatasetMeta(0).data[active].getCenterPoint());
                chart.update('none');
            });
        } catch (_) {
            chartFailed = true;
            content.hidden = true;
            fallback.hidden = !rows.length;
            description.classList.remove('visually-hidden');
        }
    }
    sync();
});
