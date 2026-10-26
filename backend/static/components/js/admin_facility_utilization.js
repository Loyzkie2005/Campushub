document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('[data-facility-utilization]');
    if (!card) return;
    const content = card.querySelector('[data-utilization-content]');
    const list = card.querySelector('#facilityUtilizationList');
    const loading = card.querySelector('[data-utilization-loading]');
    const error = card.querySelector('[data-utilization-error]');
    const empty = card.querySelector('[data-utilization-empty]');
    function state(value) {
        card.setAttribute('aria-busy', String(value === 'loading'));
        content.hidden = value !== 'ready';
        loading.hidden = value !== 'loading';
        error.hidden = value !== 'error';
    }
    function render(summary) {
        if (!summary || !['ready', 'empty'].includes(summary.state) || !Array.isArray(summary.rows) || summary.rows.length !== 6) {
            state('error'); return;
        }
        const fragment = document.createDocumentFragment();
        for (const row of summary.rows) {
            const ready = row.state === 'ready';
            const percent = row.percentage;
            if (!['ready', 'unavailable'].includes(row.state) || (ready && (typeof percent !== 'number' || !Number.isFinite(percent) || percent < 0 || percent > 100))) {
                state('error'); return;
            }
            const item = document.createElement('li'); item.className = 'facility-utilization-type'; item.dataset.state = row.state;
            const name = document.createElement('strong'); name.textContent = row.name; name.title = row.context;
            const value = document.createElement('b'); value.textContent = ready ? `${percent}%` : 'Utilization unavailable';
            const context = document.createElement('span'); context.className = `facility-utilization-context${ready ? '' : ' visually-hidden'}`; context.textContent = row.context;
            item.append(name, value, context);
            if (ready) {
                const meter = document.createElement('div'); meter.className = 'facility-utilization-meter';
                for (const [key, value] of Object.entries({ role: 'progressbar', 'aria-label': `${row.name} utilization`, 'aria-valuemin': 0, 'aria-valuemax': 100, 'aria-valuenow': percent, 'aria-valuetext': row.context })) meter.setAttribute(key, value);
                const bar = document.createElement('span'); bar.style.width = `${percent}%`; meter.append(bar); item.append(meter);
            }
            fragment.append(item);
        }
        list.replaceChildren(fragment);
        const hasUsage = summary.rows.some(row => row.state === 'ready' && row.used > 0);
        list.hidden = !hasUsage;
        empty.hidden = hasUsage;
        const message = card.querySelector('[data-utilization-message]'); message.textContent = summary.message || ''; message.hidden = !summary.message;
        card.querySelector('[data-utilization-unclassified]').hidden = !summary.unclassified_count;
        state('ready');
    }
    document.addEventListener('campushub:dashboard-loading', () => { state('loading'); });
    document.addEventListener('campushub:dashboard-load-error', () => state('error'));
    document.addEventListener('campushub:dashboard-data', (event) => { render(event.detail.facilities?.utilization_summary); });
    card.querySelector('[data-utilization-retry]').addEventListener('click', () => document.getElementById('dashboardRefresh')?.click());
});
