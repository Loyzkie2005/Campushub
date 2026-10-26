document.addEventListener('DOMContentLoaded', () => {
    const card = document.querySelector('[data-upcoming-reservations]');
    if (!card) return;
    const list = card.querySelector('[data-upcoming-list]');
    const empty = card.querySelector('[data-upcoming-empty]');
    const loading = card.querySelector('[data-upcoming-loading]');
    const error = card.querySelector('[data-upcoming-error]');
    function state(value, hasRows = false) {
        card.setAttribute('aria-busy', String(value === 'loading'));
        list.hidden = value !== 'ready' || !hasRows;
        if (list.tagName === 'TBODY') list.closest('.facilities-table-scroll').hidden = value !== 'ready' || !hasRows;
        empty.hidden = value !== 'ready' || hasRows;
        loading.hidden = value !== 'loading';
        error.hidden = value !== 'error';
    }
    function render(rows) {
        if (!Array.isArray(rows) || rows.length > 5 || !rows.every(row =>
            typeof row.facility === 'string' && typeof row.when === 'string' &&
            row.status === 'approved' && row.status_label === 'Approved' &&
            (list.tagName !== 'TBODY' || (typeof row.id === 'string' && typeof row.url === 'string' && row.url.startsWith('/admin-bookings/'))))) {
            state('error'); return;
        }
        const fragment = document.createDocumentFragment();
        for (const row of rows) {
            if (list.tagName === 'TBODY') {
                const item = document.createElement('tr');
                const reference = document.createElement('td');
                const link = document.createElement('a'); link.textContent = row.id;
                const url = new URL(row.url, location.origin);
                if (url.origin !== location.origin) { state('error'); return; }
                const token = window.CampusHubAdminSession?.getTabToken() || new URL(location.href).searchParams.get('__at');
                if (token) url.searchParams.set('__at', token);
                link.href = url.href; reference.append(link); item.append(reference);
                for (const text of [row.facility, row.requester || 'Not recorded', row.when, row.status_label]) {
                    const cell = document.createElement('td'); cell.textContent = text; item.append(cell);
                }
                fragment.append(item); continue;
            }
            const item = document.createElement('li');
            const name = document.createElement('strong'); name.textContent = row.facility;
            const when = document.createElement('span'); when.className = 'upcoming-reservation-when'; when.textContent = row.when;
            const status = document.createElement('span'); status.className = 'upcoming-reservation-status'; status.textContent = row.status_label;
            item.append(name, when, status); fragment.append(item);
        }
        list.replaceChildren(fragment);
        state('ready', rows.length > 0);
    }
    document.addEventListener('campushub:dashboard-loading', () => { state('loading'); });
    document.addEventListener('campushub:dashboard-load-error', () => { state('error'); });
    document.addEventListener('campushub:dashboard-data', event => { render(event.detail.facilities?.upcoming_reservations); });
    card.querySelector('[data-upcoming-retry]').addEventListener('click', () => document.getElementById('dashboardRefresh')?.click());
});
