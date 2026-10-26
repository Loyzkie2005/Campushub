document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('[data-booking-overview]');
    if (!card) return;
    const content = card.querySelector('[data-booking-content]');
    const error = card.querySelector('[data-booking-error]');
    const canvas = card.querySelector('canvas');
    const number = new Intl.NumberFormat('en-PH', { maximumFractionDigits: 0 });
    let chart;
    let trendRows = [];
    let activeBucket = -1;
    const executiveMode = Boolean(card.closest('[data-executive-dashboard]'));
    const keys = ['pending', 'approved', 'completed', 'rejected_cancelled'];
    const series = [
        { key: 'approved', label: 'Approved', color: '#1A1851' },
        { key: 'pending', label: 'Pending', color: '#FCB315' },
        { key: 'completed', label: 'Completed', color: 'rgba(26,24,81,.5)' },
        { key: 'rejected_cancelled', label: 'Rejected / Cancelled', color: 'rgba(26,24,81,.2)' },
    ];
    const displayedSeries = executiveMode ? [{key: 'count', label: 'Number of facility bookings', color: '#1A1851'}] : series;
    function describe(row) {
        if (executiveMode) return `${row.label}: ${number.format(row.count)} facility bookings.`;
        return `${row.label}: Total Bookings ${number.format(row.count)}; ${series.map((item) => `${item.label} ${number.format(row[item.key])}`).join('; ')}.`;
    }
    function link(url) {
        const target = new URL(url, window.location.origin);
        const token = window.CampusHubAdminSession?.getTabToken() || new URL(location.href).searchParams.get('__at');
        if (target.origin === window.location.origin && token) target.searchParams.set('__at', token);
        return target.href;
    }
    function fail() {
        content.hidden = true;
        const trend = card.querySelector('[data-booking-trend-content]');
        if (trend) trend.hidden = true;
        error.hidden = false;
    }
    function render(overview, chartOnly = false) {
        const validCount = (count) => Number.isSafeInteger(count) && count >= 0;
        if (!overview || !validCount(overview.total) || !keys.every((key) => validCount(overview[key])) ||
            (executiveMode && !validCount(overview.reserved_confirmed)) ||
            !Array.isArray(overview.statuses) || !Array.isArray(overview.trend) || !overview.trend.length ||
            !['daily', 'weekly', 'monthly'].includes(overview.grouping) ||
            typeof overview.start_date !== 'string' || typeof overview.end_date !== 'string' ||
            !overview.trend.every((row) => typeof row.label === 'string' && validCount(row.count) &&
                keys.every((key) => validCount(row[key])) && keys.reduce((total, key) => total + row[key], 0) === row.count) ||
            overview.trend.reduce((total, row) => total + row.count, 0) !== overview.total ||
            !keys.every((key) => overview.trend.reduce((total, row) => total + row[key], 0) === overview[key]) ||
            typeof overview.comparison?.comparison_text !== 'string' || typeof overview.view_all_url !== 'string') {
            fail();
            return;
        }
        content.hidden = false;
        const trend = card.querySelector('[data-booking-trend-content]');
        if (trend) trend.hidden = false;
        error.hidden = true;
        card.querySelector('#bookingGroupingSelect').value = overview.grouping;
        if (!chartOnly) {
            card.querySelector('[data-booking-total]').textContent = number.format(overview.total);
            card.querySelector('[data-booking-comparison]').textContent = overview.total > 0 && overview.comparison.previous_value === 0
                ? 'New booking activity' : overview.comparison.comparison_text;
            for (const key of keys) {
                const row = card.querySelector(`[data-booking-status="${key}"]`);
                if (!row) continue;
                row.querySelector('strong').textContent = number.format(overview[key]);
                row.toggleAttribute('data-attention', key === 'pending' && overview.pending > 0);
                const status = overview.statuses.find((item) => item.key === key);
                if (row.tagName === 'A' && status?.url) row.href = link(status.url);
                row.setAttribute('aria-label', `${row.querySelector('h3').textContent}: ${number.format(overview[key])}${key === 'pending' && overview.pending ? ', may need review' : ''}`);
            }
            const reserved = card.querySelector('[data-booking-status="reserved_confirmed"] strong');
            if (reserved) reserved.textContent = number.format(overview.reserved_confirmed);
            const attention = card.querySelector('[data-booking-attention]');
            if (attention) {
                attention.hidden = overview.pending === 0;
                card.querySelector('[data-booking-attention-text]').textContent = `${number.format(overview.pending)} pending request${overview.pending === 1 ? '' : 's'} may need review.`;
            }
        }
        card.querySelector('[data-booking-empty]').hidden = overview.total > 0;
        card.querySelector('[data-booking-period]').textContent = `${overview.grouping[0].toUpperCase() + overview.grouping.slice(1)} requests submitted · ${overview.start_date} – ${overview.end_date}`;
        card.querySelector('[data-booking-view-all]').href = link(overview.view_all_url);
        const rows = document.createDocumentFragment();
        for (const item of overview.trend) {
            const row = document.createElement('li');
            row.textContent = describe(item);
            rows.append(row);
        }
        card.querySelector('[data-booking-trend-description]').replaceChildren(rows);
        trendRows = overview.trend;
        activeBucket = -1;
        card.querySelector('[data-booking-chart-live]').textContent = '';
        canvas.setAttribute('aria-label', `${number.format(overview.total)} booking requests submitted from ${overview.start_date} to ${overview.end_date}${executiveMode ? ', line chart' : ', stacked by status'}. Use left and right arrow keys to inspect each period.`);
        const chartError = card.querySelector('[data-booking-chart-error]');
        const textDescription = card.querySelector('#bookingTrendDescription');
        function textFallback(visible) {
            if (!executiveMode) return;
            textDescription.classList.toggle('visually-hidden', !visible);
            if (visible) textDescription.tabIndex = 0; else textDescription.removeAttribute('tabindex');
        }
        if (executiveMode) {
            canvas.parentElement.hidden = overview.total === 0;
            if (!overview.total) { chartError.hidden = true; textFallback(false); return; }
        }
        if (typeof window.Chart === 'undefined') {
            canvas.hidden = true;
            chartError.hidden = false;
            textFallback(true);
            return;
        }
        try {
            const data = { labels: overview.trend.map((row) => row.label), datasets: displayedSeries.map((item) => ({
                label: item.label, data: overview.trend.map((row) => row[item.key]),
                stack: 'bookings', backgroundColor: item.color, borderRadius: 2, maxBarThickness: 28,
                borderColor: item.color,
                borderWidth: executiveMode ? 2 : item.key === 'rejected_cancelled' ? 1 : 0,
                pointRadius: executiveMode ? 2 : 0, pointHoverRadius: 5,
                tension: 0, fill: false,
            })) };
            if (chart) {
                chart.setActiveElements([]);
                chart.tooltip.setActiveElements([], { x: 0, y: 0 });
                chart.data = data;
                chart.resize();
                chart.update('none');
            } else {
                chart = new Chart(canvas, { type: executiveMode ? 'line' : 'bar', data, options: {
                    responsive: true, maintainAspectRatio: false, animation: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: { legend: { display: false }, tooltip: {
                        backgroundColor: '#1A1851', titleColor: '#FFFFFF', bodyColor: '#FFFFFF',
                        callbacks: {
                            beforeBody: (items) => items.length ? `Total Bookings: ${number.format(trendRows[items[0].dataIndex].count)}` : '',
                            label: (context) => ` ${context.dataset.label}: ${number.format(context.parsed.y)}`,
                        },
                    } },
                    scales: {
                        x: { stacked: !executiveMode, grid: { display: false }, ticks: { color: '#626781', maxRotation: 0, maxTicksLimit: 6, font: { size: 12 } } },
                        y: { stacked: !executiveMode, beginAtZero: true, suggestedMax: 1, ticks: { precision: 0, color: '#626781', maxTicksLimit: 5, font: { size: 12 } }, grid: { color: '#eef2f7' } },
                    },
                } });
            }
            canvas.hidden = false;
            chartError.hidden = true;
            textFallback(false);
        } catch (_) {
            canvas.hidden = true;
            chartError.hidden = false;
            textFallback(true);
        }
    }
    canvas.addEventListener('keydown', (event) => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || !trendRows.length || content.hidden) return;
        if (card.closest('[data-global-dashboard]')?.getAttribute('aria-busy') === 'true') return;
        event.preventDefault();
        if (event.key === 'Home') activeBucket = 0;
        else if (event.key === 'End') activeBucket = trendRows.length - 1;
        else if (activeBucket < 0) activeBucket = event.key === 'ArrowLeft' ? trendRows.length - 1 : 0;
        else activeBucket = Math.min(trendRows.length - 1, Math.max(0, activeBucket + (event.key === 'ArrowRight' ? 1 : -1)));
        card.querySelector('[data-booking-chart-live]').textContent = describe(trendRows[activeBucket]);
        if (chart) {
            const items = displayedSeries.map((_, datasetIndex) => ({ datasetIndex, index: activeBucket }));
            chart.setActiveElements(items);
            const position = chart.getDatasetMeta(0).data[activeBucket].getCenterPoint();
            chart.tooltip.setActiveElements(items, position);
            chart.update('none');
        }
    });
    document.addEventListener('campushub:dashboard-data', event => { render(executiveMode ? event.detail.executive?.booking_overview : event.detail.facilities?.booking_overview); });
    document.addEventListener('campushub:booking-trend-data', event => {
        render(executiveMode ? event.detail.executive?.booking_overview : event.detail.facilities?.booking_overview, true);
    });
    document.addEventListener('campushub:booking-trend-error', () => { fail(); });
    document.addEventListener('campushub:dashboard-load-error', () => { fail(); });
    document.addEventListener('campushub:dashboard-loading', () => { error.hidden = true; });
    try { render(JSON.parse(document.getElementById('bookingOverviewData').textContent)); }
    catch (_) { fail(); }
});
