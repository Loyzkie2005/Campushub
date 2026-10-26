document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('[data-facility-operational-status]');
    if (!card) return;
    const layout = card.querySelector('[data-operational-layout]');
    const empty = card.querySelector('[data-operational-empty]');
    const loading = card.querySelector('[data-operational-loading]');
    const error = card.querySelector('[data-operational-error]');
    const canvas = card.querySelector('canvas');
    const keys = ['available', 'unavailable', 'maintenance', 'inactive'];
    const colors = ['#1A1851', '#FCB315', 'rgba(26,24,81,.55)', 'rgba(26,24,81,.2)'];
    let chart = null;
    function state(value) {
        card.setAttribute('aria-busy', String(value === 'loading'));
        layout.hidden = value !== 'ready'; empty.hidden = value !== 'empty';
        loading.hidden = value !== 'loading'; error.hidden = value !== 'error';
    }
    function render(data) {
        if (!data || !['ready', 'empty'].includes(data.state) || !Number.isSafeInteger(data.total) ||
            data.total < 0 || !Array.isArray(data.rows) || data.rows.length !== keys.length ||
            !data.rows.every((row, index) => row.key === keys[index] && typeof row.label === 'string' &&
                Number.isSafeInteger(row.count) && row.count >= 0) ||
            data.rows.reduce((sum, row) => sum + row.count, 0) !== data.total ||
            (data.state === 'empty') !== (data.total === 0)) { state('error'); return; }
        const legend = document.createDocumentFragment();
        for (const row of data.rows) {
            const item = document.createElement('div');
            const label = document.createElement('span');
            const dot = document.createElement('i'); dot.className = `facility-availability-dot operational-dot--${row.key}`;
            dot.setAttribute('aria-hidden', 'true');
            const text = document.createElement('span'); text.textContent = row.label;
            label.append(dot, text);
            const count = document.createElement('strong'); count.textContent = row.count;
            item.append(label, count); legend.append(item);
        }
        card.querySelector('[data-operational-legend]').replaceChildren(legend);
        card.querySelector('[data-operational-total]').textContent = data.total;
        card.querySelector('[data-operational-unit]').textContent = data.total === 1 ? 'Facility' : 'Facilities';
        canvas.setAttribute('aria-label', data.rows.map(row => `${row.label}: ${row.count}`).join('; '));
        state(data.state);
        if (data.state !== 'ready') return;
        const values = data.rows.map(row => row.count);
        if (chart) {
            canvas.hidden = false;
            chart.data.labels = data.rows.map(row => row.label);
            chart.data.datasets[0].data = values; chart.update('none'); chart.resize();
        } else if (typeof Chart !== 'undefined') {
            canvas.hidden = false;
            try {
                chart = new Chart(canvas.getContext('2d'), {
                    type: 'doughnut',
                    data: { labels: data.rows.map(row => row.label), datasets: [{data: values,
                        backgroundColor: colors, borderColor: '#FFFFFF', borderWidth: 2, hoverOffset: 2}] },
                    options: { responsive: true, maintainAspectRatio: false, cutout: '68%',
                        plugins: {legend: {display: false}},
                        animation: false },
                });
            } catch { canvas.hidden = true; }
        } else canvas.hidden = true;
        // If Chart.js is unavailable, the real center total and labelled counts remain readable.
    }
    document.addEventListener('campushub:dashboard-loading', () => state('loading'));
    document.addEventListener('campushub:dashboard-load-error', () => state('error'));
    document.addEventListener('campushub:dashboard-data', event => render(event.detail.facilities?.operational_status));
    card.querySelector('[data-operational-retry]').addEventListener('click', () => document.getElementById('dashboardRefresh')?.click());
    try { render(JSON.parse(document.getElementById('facilityOperationalStatusData').textContent)); }
    catch { state('error'); }
});
