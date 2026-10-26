/* One read-only Services projection of the existing protected dashboard snapshot. */
document.addEventListener('DOMContentLoaded', () => {
    const root = document.querySelector('[data-services-overview]');
    if (!root) return;
    const $ = selector => root.querySelector(selector);
    const numbers = new Intl.NumberFormat('en-PH');
    const dates = new Intl.DateTimeFormat('en-PH', {timeZone: 'Asia/Manila', year: 'numeric', month: 'short', day: 'numeric'});
    const counts = ['active_services', 'open_requests', 'pending_requests', 'completed_requests'];
    const validCount = value => Number.isSafeInteger(value) && value >= 0;
    const text = (tag, value) => { const el = document.createElement(tag); el.textContent = value; return el; };
    const charts = {}; const rowsByChart = {}; const active = {};
    function localLink(value) {
        const url = new URL(value, location.origin);
        if (url.origin !== location.origin || !['/admin-services/', '/admin-service-requests/'].includes(url.pathname)) throw new Error('Invalid service destination');
        const token = window.CampusHubAdminSession?.getTabToken() || new URL(location.href).searchParams.get('__at');
        if (token) url.searchParams.set('__at', token);
        return url.href;
    }
    function fail() {
        $('[data-services-content]').hidden = true;
        $('[data-services-error]').hidden = false;
        $('[data-services-loading]').hidden = true;
    }
    function failTrend() {
        $('[data-service-trend-content]').hidden = true;
        $('[data-service-trend-error]').hidden = false;
        $('[data-service-chart-live]').textContent = '';
    }
    function draw(key, rows) {
        const line = key === 'trend';
        const canvas = document.getElementById(line ? 'serviceRequestTrendChart' : 'serviceDistributionChart');
        const wrap = $(`[data-service-${key}-wrap]`), empty = $(`[data-service-${key}-empty]`);
        const description = $(`[data-service-${key}-description]`), fallback = $(`[data-service-${key}-fallback]`);
        rowsByChart[key] = rows; active[key] = -1;
        description.replaceChildren(...rows.map(row => text('li', `${row.label}: ${numbers.format(row.count)} requests.`)));
        const hasData = rows.some(row => row.count > 0);
        wrap.hidden = !hasData; empty.hidden = hasData; fallback.hidden = true; description.hidden = !hasData;
        canvas.setAttribute('aria-label', `${line ? 'Service request trend' : 'Requests by service'}. Use left and right arrow keys to inspect each ${line ? 'period' : 'service'}.`);
        if (!hasData) return;
        try {
            if (typeof Chart === 'undefined') throw new Error('Chart library unavailable');
            const data = {labels: rows.map(row => row.label), datasets: [{label: line ? 'Number of Service Requests' : 'Requests', data: rows.map(row => row.count),
                borderColor: '#1A1851', backgroundColor: '#1A1851', hoverBackgroundColor: '#FCB316',
                borderWidth: line ? 2 : 0, borderRadius: 3, pointRadius: 2, pointHoverRadius: 5,
                tension: 0, fill: false, maxBarThickness: 44}]};
            if (charts[key]) {
                charts[key].setActiveElements([]); charts[key].tooltip.setActiveElements([], {x: 0, y: 0});
                charts[key].data = data; charts[key].update('none');
            } else charts[key] = new Chart(canvas, {type: line ? 'line' : 'bar', data, options: {
                responsive: true, maintainAspectRatio: false, animation: false,
                interaction: {mode: 'index', intersect: false},
                plugins: {legend: {display: false}, tooltip: {backgroundColor: '#1A1851', callbacks: {
                    title: items => rowsByChart[key][items[0]?.dataIndex]?.label || '',
                    label: context => `${numbers.format(context.parsed.y)} requests`,
                }}},
                scales: {x: {grid: {display: false}, ticks: {font: {family: 'Inter, sans-serif', size: 12}, color: '#626781', maxRotation: 0,
                    autoSkip: line, maxTicksLimit: line ? 6 : undefined,
                    callback: function(value) {
                        const label = this.getLabelForValue(value);
                        const limit = Math.max(6, Math.min(20, Math.floor(this.chart.width / Math.max(1, rowsByChart[key].length) / 6) - 2));
                        return line || label.length <= limit ? label : `${label.slice(0, limit - 1)}\u2026`;
                    }}},
                    y: {beginAtZero: true, suggestedMax: 1, ticks: {precision: 0, maxTicksLimit: 5, color: '#626781', font: {size: 12}}, grid: {color: '#E8EAF0'}}},
            }});
            description.classList.add('visually-hidden'); description.removeAttribute('tabindex');
            requestAnimationFrame(() => charts[key].resize());
        } catch (_) {
            wrap.hidden = true; fallback.hidden = false; description.classList.remove('visually-hidden'); description.tabIndex = 0;
        }
    }
    function renderTrend(services) {
        const trend = services?.request_trend;
        if (!trend || !validCount(trend.total) || !['daily', 'weekly', 'monthly'].includes(trend.grouping) ||
            !Array.isArray(trend.trend) || !trend.trend.length || !trend.trend.every(row => typeof row.label === 'string' && validCount(row.count)) ||
            trend.trend.reduce((sum, row) => sum + row.count, 0) !== trend.total) throw new Error('Invalid service trend');
        $('[data-service-trend-content]').hidden = false; $('[data-service-trend-error]').hidden = true;
        $('#serviceGroupingSelect').value = trend.grouping;
        root.dataset.renderedGrouping = trend.grouping;
        $('[data-service-chart-live]').textContent = '';
        draw('trend', trend.trend.map(row => ({label: row.label, count: row.count})));
    }
    function render(services) {
        try {
            if (!services || !counts.every(key => validCount(services[key])) || !validCount(services.total_requests) ||
                services.request_trend?.total !== services.total_requests ||
                !Array.isArray(services.requests_by_service) || services.requests_by_service.length > 5 ||
                !services.requests_by_service.every(row => typeof row.facility__facility_name === 'string' && validCount(row.total) && row.total > 0) ||
                !Array.isArray(services.recent_requests) || services.recent_requests.length > 5 ||
                !Array.isArray(services.attention) || services.attention.length > 5) throw new Error('Invalid services snapshot');
            $('[data-services-content]').hidden = false; $('[data-services-error]').hidden = true; $('[data-services-loading]').hidden = true;
            for (const key of counts) $(`[data-service-metric="${key}"]`).textContent = numbers.format(services[key]);
            renderTrend(services);
            draw('distribution', services.requests_by_service.map(row => ({label: row.facility__facility_name, count: row.total})));
            $('[data-service-distribution-live]').textContent = '';
            $('[data-service-recent]').replaceChildren(...services.recent_requests.map(row => {
                if (![row.id, row.service, row.requester, row.status, row.url].every(value => typeof value === 'string')) throw new Error('Invalid request');
                const item = text('tr', ''), reference = text('td', ''), link = text('a', row.id);
                link.href = localLink(row.url); reference.append(link); item.append(reference);
                for (const value of [row.service, row.requester, row.status]) item.append(text('td', value));
                const time = text('time', dates.format(new Date(row.submitted_at))); time.dateTime = row.submitted_at;
                const cell = text('td', ''); cell.append(time); item.append(cell); return item;
            }));
            $('[data-service-recent-wrap]').hidden = !services.recent_requests.length;
            $('[data-service-recent-empty]').hidden = Boolean(services.recent_requests.length);
            $('[data-service-attention]').replaceChildren(...services.attention.map(row => {
                if (![row.reference, row.service, row.status, row.reason, row.url].every(value => typeof value === 'string')) throw new Error('Invalid attention item');
                const item = text('li', ''), link = text('a', `${row.reference} \u00b7 ${row.service}`); link.href = localLink(row.url);
                item.append(link, text('span', row.status), text('p', row.reason)); return item;
            }));
            $('[data-service-attention-empty]').hidden = Boolean(services.attention.length);
        } catch (_) { fail(); }
    }
    for (const key of ['trend', 'distribution']) {
        const canvas = document.getElementById(key === 'trend' ? 'serviceRequestTrendChart' : 'serviceDistributionChart');
        canvas.addEventListener('keydown', event => {
            const rows = rowsByChart[key];
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || !rows?.length || !charts[key] ||
                root.getAttribute('aria-busy') === 'true' || root.closest('[data-global-dashboard]')?.getAttribute('aria-busy') === 'true' || $('[data-services-content]').hidden) return;
            event.preventDefault();
            active[key] = event.key === 'Home' ? 0 : event.key === 'End' ? rows.length - 1 :
                Math.max(0, Math.min(rows.length - 1, active[key] + (event.key === 'ArrowLeft' ? -1 : 1)));
            const index = active[key], items = [{datasetIndex: 0, index}];
            $(key === 'trend' ? '[data-service-chart-live]' : '[data-service-distribution-live]').textContent = `${rows[index].label}: ${numbers.format(rows[index].count)} requests.`;
            charts[key].setActiveElements(items); charts[key].tooltip.setActiveElements(items, charts[key].getDatasetMeta(0).data[index].getCenterPoint()); charts[key].update('none');
        });
    }
    document.addEventListener('campushub:dashboard-data', event => render(event.detail.executive?.services));
    document.addEventListener('campushub:service-trend-data', event => { try { renderTrend(event.detail.executive?.services); } catch (_) { failTrend(); } });
    document.addEventListener('campushub:service-trend-error', failTrend);
    document.addEventListener('campushub:dashboard-load-error', fail);
    document.addEventListener('campushub:dashboard-loading', () => { $('[data-services-loading]').hidden = false; $('[data-services-error]').hidden = true; });
    try { render(JSON.parse(document.getElementById('servicesOverviewData').textContent)); } catch (_) { fail(); }
});
