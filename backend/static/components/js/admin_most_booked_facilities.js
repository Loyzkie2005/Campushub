document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('[data-most-booked-facilities]');
    if (!card) return;
    const heading = card.querySelector('[data-facility-ranking-heading]');
    const list = card.querySelector('[data-facility-ranking-list]');
    const empty = card.querySelector('[data-facility-ranking-empty]');
    const loading = card.querySelector('[data-facility-ranking-loading]');
    const error = card.querySelector('[data-facility-ranking-error]');
    const number = new Intl.NumberFormat('en-PH', { maximumFractionDigits: 0 });
    const canvas = card.querySelector('[data-facility-ranking-chart]');
    let chart, chartRows = [], active = -1;
    function state(value, hasRows = false) {
        card.setAttribute('aria-busy', String(value === 'loading'));
        heading.hidden = list.hidden = value !== 'ready' || !hasRows;
        empty.hidden = value !== 'ready' || hasRows;
        loading.hidden = value !== 'loading';
        error.hidden = value !== 'error';
        if (canvas) canvas.parentElement.hidden = value !== 'ready' || !hasRows;
    }
    function draw(rows) {
        if (!canvas) return;
        chartRows = rows; active = -1;
        const live = card.querySelector('[data-facility-ranking-live]');
        live.textContent = '';
        if (!rows.length) {
            canvas.parentElement.hidden = true;
            card.querySelector('[data-facility-ranking-chart-error]').hidden = true;
            return;
        }
        canvas.setAttribute('aria-label', `Top ${rows.length} facilities by approved and completed bookings scheduled in the selected period. Use arrow keys to inspect counts.`);
        try {
            if (typeof Chart === 'undefined') throw new Error('Chart unavailable');
            const data = {labels: rows.map(row => row.name), datasets: [{label: 'Bookings',
                data: rows.map(row => row.bookings), backgroundColor: '#1A1851',
                borderRadius: 3, maxBarThickness: 44}]};
            if (chart) { chart.setActiveElements([]); chart.tooltip.setActiveElements([], {x: 0, y: 0}); chart.data = data; chart.update('none'); }
            else chart = new Chart(canvas, {type: 'bar', data, options: {
                responsive: true, maintainAspectRatio: false, animation: false,
                plugins: {legend: {display: false}, tooltip: {backgroundColor: '#1A1851', callbacks: {
                    title: items => chartRows[items[0]?.dataIndex]?.name || '',
                    label: context => `${number.format(context.parsed.y)} bookings`,
                }}},
                scales: {x: {grid: {display: false}, ticks: {color: '#626781', maxRotation: 0, autoSkip: false, font: {size: 12},
                    callback: function(value) {
                        const name = this.getLabelForValue(value);
                        const limit = Math.max(5, Math.min(18, Math.floor(this.chart.width / Math.max(1, chartRows.length) / 6) - 2));
                        return name.length > limit ? `${name.slice(0, limit - 1)}\u2026` : name;
                    }}},
                    y: {beginAtZero: true, suggestedMax: 1, ticks: {precision: 0, color: '#626781', font: {size: 12}}, grid: {color: '#E8EAF0'}}},
            }});
            heading.classList.add('visually-hidden'); list.classList.add('visually-hidden'); list.tabIndex = -1;
            card.querySelector('[data-facility-ranking-chart-error]').hidden = true;
            requestAnimationFrame(() => chart.resize());
        } catch (_) {
            canvas.parentElement.hidden = true;
            heading.classList.remove('visually-hidden'); list.classList.remove('visually-hidden'); list.tabIndex = 0;
            card.querySelector('[data-facility-ranking-chart-error]').hidden = !rows.length;
        }
    }
    function render(rows) {
        if (!Array.isArray(rows) || rows.length > 5 || !rows.every((row, index) =>
            row.rank === index + 1 && typeof row.name === 'string' &&
            Number.isSafeInteger(row.bookings) && row.bookings > 0)) {
            state('error'); return;
        }
        const fragment = document.createDocumentFragment();
        for (const row of rows) {
            const item = document.createElement('li');
            const thumbnail = document.createElement('span'); thumbnail.className = 'facility-ranking-image';
            thumbnail.setAttribute('aria-hidden', 'true');
            const fallback = document.createElement('span'); fallback.setAttribute('data-facility-image-fallback', '');
            const icon = empty.querySelector('svg');
            if (icon) fallback.append(icon.cloneNode(true)); else fallback.textContent = '—';
            thumbnail.append(fallback);
            if (typeof row.image_url === 'string' && row.image_url) {
                const image = document.createElement('img'); image.src = row.image_url;
                image.alt = ''; image.loading = 'lazy'; image.width = image.height = 40;
                fallback.hidden = true;
                image.addEventListener('error', () => { image.hidden = true; fallback.hidden = false; }, {once: true});
                thumbnail.prepend(image);
            }
            const details = document.createElement('div'); details.className = 'marketplace-product-details';
            const name = document.createElement('strong');
            const rank = document.createElement('span'); rank.className = 'marketplace-product-rank';
            rank.setAttribute('aria-hidden', 'true'); rank.textContent = `${row.rank}.`;
            name.append(rank, document.createTextNode(` ${row.name}`)); details.append(name);
            const stats = document.createElement('div'); stats.className = 'marketplace-product-stats';
            const count = document.createElement('span'); count.className = 'marketplace-product-units';
            count.textContent = `${number.format(row.bookings)} booking${row.bookings === 1 ? '' : 's'}`;
            stats.append(count); item.append(thumbnail, details, stats); fragment.append(item);
        }
        list.replaceChildren(fragment);
        state('ready', rows.length > 0);
        draw(rows);
    }
    document.addEventListener('campushub:dashboard-loading', () => { state('loading'); });
    document.addEventListener('campushub:dashboard-load-error', () => { state('error'); });
    document.addEventListener('campushub:dashboard-data', event => { render(event.detail.facilities?.most_booked_facilities); });
    card.querySelector('[data-facility-ranking-retry]').addEventListener('click', () => document.getElementById('dashboardRefresh')?.click());
    if (canvas) {
        canvas.addEventListener('keydown', event => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || !chartRows.length || !chart ||
                card.closest('[data-global-dashboard]')?.getAttribute('aria-busy') === 'true' || !error.hidden) return;
            event.preventDefault();
            active = event.key === 'Home' ? 0 : event.key === 'End' ? chartRows.length - 1 :
                Math.max(0, Math.min(chartRows.length - 1, active + (event.key === 'ArrowLeft' ? -1 : 1)));
            card.querySelector('[data-facility-ranking-live]').textContent = `${chartRows[active].name}: ${number.format(chartRows[active].bookings)} bookings.`;
            const items = [{datasetIndex: 0, index: active}];
            chart.setActiveElements(items);
            chart.tooltip.setActiveElements(items, chart.getDatasetMeta(0).data[active].getCenterPoint()); chart.update('none');
        });
        try { render(JSON.parse(document.getElementById('facilityRankingData').textContent)); }
        catch (_) { state('error'); }
    }
    // Initial Django rows need the same missing/broken-image fallback as refreshed rows.
    for (const image of list.querySelectorAll('img')) {
        const failed = () => { image.hidden = true; image.nextElementSibling.hidden = false; };
        image.addEventListener('error', failed, {once: true});
        if (image.complete && !image.naturalWidth) failed();
    }
});
