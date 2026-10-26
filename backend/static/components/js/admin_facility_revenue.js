document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('[data-facility-revenue]');
    if (!card) return;
    const superAnalytics = document.body.classList.contains('super-admin-analytics');
    const find = name => card.querySelector(`[data-revenue-${name}]`);
    const canvas = card.querySelector('canvas');
    const money = value => `₱${Number(value).toLocaleString('en-PH', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    let chart = null, current = null, selected = 0;
    function state(value) {
        card.setAttribute('aria-busy', String(value === 'loading'));
        find('content').hidden = value !== 'ready';
        find('loading').hidden = value !== 'loading';
        find('error').hidden = value !== 'error';
        find('keyboard').hidden = true;
    }
    function inspect() {
        if (!current || find('content').hidden) return;
        const series = current.chart;
        const text = `${series.tooltip_labels[selected]} — Revenue: ${money(series.values[selected])}; Paid Transactions: ${series.transactions[selected]}`;
        find('keyboard').textContent = text; find('keyboard').hidden = false;
        if (chart) {
            const active = [{datasetIndex: 0, index: selected}];
            chart.setActiveElements(active);
            const point = chart.getDatasetMeta(0).data[selected];
            chart.tooltip.setActiveElements(active, {x: point.x, y: point.y}); chart.update('none');
        }
    }
    function render(data) {
        const series = data?.chart;
        if (!data || !series || typeof data.total !== 'string' || !/^\d+\.\d{2}$/.test(data.total) || !Number.isFinite(Number(data.total)) ||
            !Number.isSafeInteger(data.transactions) || data.transactions < 0 ||
            typeof data.comparison?.comparison_text !== 'string' ||
            !['labels', 'tooltip_labels', 'dates', 'values', 'transactions'].every(key => Array.isArray(series[key]) && series[key].length === series.labels?.length) ||
            !series.labels.length || !series.values.every(value => Number.isFinite(value) && value >= 0) ||
            !series.transactions.every(value => Number.isSafeInteger(value) && value >= 0) ||
            series.transactions.reduce((sum, value) => sum + value, 0) !== data.transactions ||
            Math.abs(series.values.reduce((sum, value) => sum + value, 0) - Number(data.total)) > 0.005 ||
            !series.tooltip_labels.every(value => typeof value === 'string') ||
            !/^\d{4}-\d{2}-\d{2}$/.test(data.start_date) || !/^\d{4}-\d{2}-\d{2}$/.test(data.end_date)) {
            current = null; state('error'); return;
        }
        current = data; selected = 0; state('ready');
        find('total').textContent = money(data.total);
        find('comparison').textContent = data.comparison.comparison_text;
        find('empty').hidden = data.transactions !== 0;
        const link = new URL(find('report').href, window.location.href);
        link.searchParams.set('report_type', 'facility_revenue');
        link.searchParams.set('date_from', data.start_date); link.searchParams.set('date_to', data.end_date);
        find('report').href = link.href;
        canvas.setAttribute('aria-label', `Facility revenue ${data.start_date} to ${data.end_date}: ${money(data.total)}, ${data.transactions} paid transactions. Use Left and Right arrow keys to inspect daily revenue.`);
        if (superAnalytics) {
            canvas.parentElement.hidden = data.transactions === 0;
            const table = find('table');
            table.hidden = data.transactions === 0;
            table.querySelector('tbody').replaceChildren(...series.values.map((amount, index) => {
                const row = document.createElement('tr');
                [series.tooltip_labels[index], money(amount), series.transactions[index]].forEach((value, column) => {
                    const cell = document.createElement(column === 0 ? 'th' : 'td');
                    if (column === 0) cell.scope = 'row';
                    cell.textContent = value; row.append(cell);
                });
                return row;
            }));
            if (!data.transactions) { chart?.destroy(); chart = null; return; }
        }
        try {
            if (typeof Chart === 'undefined') throw new Error('Chart unavailable');
            if (chart) {
                chart.data.labels = series.labels; chart.data.datasets[0].data = series.values;
                chart.data.datasets[0].pointRadius = series.values.length === 1 ? 3 : 0;
                chart.options.scales.y.suggestedMax = data.transactions ? undefined : 100;
                chart.setActiveElements([]); chart.tooltip.setActiveElements([], {x: 0, y: 0});
                chart.update('none'); chart.resize();
            } else {
                chart = new Chart(canvas.getContext('2d'), {
                    type: 'line',
                    data: {labels: series.labels, datasets: [{label: 'Revenue', data: series.values,
                        borderColor: '#1A1851', backgroundColor: '#1A1851', borderWidth: 2,
                        pointRadius: series.values.length === 1 ? 3 : 0, pointHoverRadius: 5,
                        pointHoverBackgroundColor: '#FCB315', pointHitRadius: 10, tension: 0, fill: false}]},
                    options: {responsive: true, maintainAspectRatio: false, animation: false,
                        interaction: {mode: 'index', intersect: false},
                        plugins: {legend: {display: false}, tooltip: {
                            backgroundColor: '#1A1851', titleColor: '#fff', bodyColor: '#fff', displayColors: false,
                            callbacks: {
                                title: items => current.chart.tooltip_labels[items[0].dataIndex],
                                label: item => [`Revenue: ${money(current.chart.values[item.dataIndex])}`,
                                    `Paid Transactions: ${current.chart.transactions[item.dataIndex]}`],
                            }}},
                        scales: {x: {grid: {display: false}, ticks: {maxTicksLimit: 5, maxRotation: 0,
                            color: '#1A1851', font: {size: 12}}},
                            y: {beginAtZero: true, suggestedMax: data.transactions ? undefined : 100,
                                title: {display: true, text: 'Revenue (₱)', color: '#1A1851', font: {size: 12}},
                                ticks: {maxTicksLimit: 4, color: '#1A1851', font: {size: 12},
                                    callback: value => `₱${Number(value).toLocaleString('en-PH')}`},
                                grid: {color: 'rgba(26,24,81,.08)'}}}},
                });
            }
        } catch (_) { current = null; state('error'); }
    }
    canvas.addEventListener('focus', inspect);
    canvas.addEventListener('keydown', event => {
        if (!current || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault(); const last = current.chart.values.length - 1;
        selected = event.key === 'Home' ? 0 : event.key === 'End' ? last :
            Math.max(0, Math.min(last, selected + (event.key === 'ArrowRight' ? 1 : -1)));
        inspect();
    });
    canvas.addEventListener('blur', () => { find('keyboard').hidden = true; });
    find('retry').addEventListener('click', () => document.getElementById('dashboardRefresh')?.click());
    document.addEventListener('campushub:dashboard-loading', () => { state('loading'); });
    document.addEventListener('campushub:dashboard-load-error', () => { current = null; state('error'); });
    document.addEventListener('campushub:dashboard-data', event => { render(event.detail?.facilities?.revenue_overview); });
    try { render(JSON.parse(document.getElementById('facilityPaidRevenueData').textContent)); }
    catch (_) { state('error'); }
});
