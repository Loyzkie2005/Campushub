/* Audit preview and on-demand details reuse the existing protected Activity API. */
document.addEventListener('DOMContentLoaded', () => {
    const section = document.querySelector('[data-system-activities]');
    if (!section) return;
    const $ = selector => section.querySelector(selector);
    const date = new Intl.DateTimeFormat('en-US', {timeZone: section.dataset.timeZone, year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true});
    function timeLabel(value, full = false) {
        const parts = Object.fromEntries(date.formatToParts(new Date(value)).map(part => [part.type, part.value]));
        const year = date.formatToParts(new Date()).find(part => part.type === 'year').value;
        return `${parts.month} ${parts.day}${full || parts.year !== year ? `, ${parts.year}` : ''}, ${parts.hour}:${parts.minute} ${parts.dayPeriod}`;
    }
    const element = (tag, value) => { const node = document.createElement(tag); node.textContent = value; return node; };
    const dialog = $('[data-activity-dialog]');
    let controller, opener;
    function fail() {
        $('[data-activities-table]').hidden = $('[data-activities-empty]').hidden = true;
        $('[data-activities-error]').hidden = false;
    }
    function detailURL(value) {
        const url = new URL(value, location.origin);
        if (url.origin !== location.origin || !/^\/api\/activity-logs\/\d+\/$/.test(url.pathname)) throw new Error('Invalid activity destination');
        const token = window.CampusHubAdminSession?.getTabToken() || new URL(location.href).searchParams.get('__at');
        if (token) url.searchParams.set('__at', token);
        return url;
    }
    function render(rows) {
        try {
            if (!Array.isArray(rows) || rows.length > 5) throw new Error('Invalid activity preview');
            const fragment = document.createDocumentFragment();
            for (const row of rows) {
                if (![row.time, row.user, row.activity, row.module].every(value => typeof value === 'string') ||
                    ![null, 'Success', 'Failed'].includes(row.result)) throw new Error('Invalid activity row');
                const tr = element('tr', ''), cell = element('td', ''), time = element('time', timeLabel(row.time));
                time.dateTime = row.time; cell.append(time); tr.append(cell);
                const user = element('td', row.user); user.className = 'audit-secondary';
                const result = element('td', ''), badge = element('span', row.result || 'Not recorded');
                badge.className = `audit-result${row.result ? ` audit-result-${row.result.toLowerCase()}` : ''}`;
                result.append(badge);
                const module = element('td', row.module); module.className = 'audit-secondary';
                tr.append(user, element('td', row.activity), module, result);
                const action = element('td', '');
                if (dialog && section.hasAttribute('data-can-view-details')) {
                    detailURL(row.details_url);
                    const button = element('button', ''); button.type = 'button'; button.className = 'audit-detail-button audit-icon-button';
                    button.title = 'View Details';
                    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                    for (const [key, value] of Object.entries({viewBox: '0 0 24 24', width: '18', height: '18', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.75', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true'})) svg.setAttribute(key, value);
                    const path = document.createElementNS(svg.namespaceURI, 'path'); path.setAttribute('d', 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z');
                    const circle = document.createElementNS(svg.namespaceURI, 'circle'); circle.setAttribute('cx', '12'); circle.setAttribute('cy', '12'); circle.setAttribute('r', '3');
                    svg.append(path, circle); button.append(svg);
                    button.dataset.activityDetailUrl = row.details_url;
                    button.setAttribute('aria-haspopup', 'dialog'); button.setAttribute('aria-label', `View details for ${row.activity}`);
                    action.append(button);
                } else action.textContent = '\u2014';
                tr.append(action); fragment.append(tr);
            }
            $('[data-executive-activities]').replaceChildren(fragment);
            $('[data-activities-table]').hidden = !rows.length;
            $('[data-activities-empty]').hidden = Boolean(rows.length);
            $('[data-activities-error]').hidden = true;
        } catch (_) { fail(); }
    }
    async function showDetails(button) {
        controller?.abort();
        const request = new AbortController(); controller = request; opener = button;
        const loading = $('[data-activity-detail-loading]'), error = $('[data-activity-detail-error]'), fields = $('[data-activity-detail-fields]');
        fields.replaceChildren(); loading.hidden = false; error.hidden = true;
        dialog.showModal();
        const timeout = window.setTimeout(() => request.abort(), 8000);
        try {
            const response = await fetch(detailURL(button.dataset.activityDetailUrl), {
                credentials: 'same-origin', cache: 'no-store', headers: {Accept: 'application/json'}, signal: request.signal,
            });
            if (!response.ok) {
                const messages = {401: 'Your sign-in expired. Sign in again to view activity details.',
                    403: 'You do not have permission to view this activity.', 404: 'This activity is no longer available.'};
                throw new Error(messages[response.status] || 'Unable to load activity details. Close this dialog and try again.');
            }
            const payload = await response.json();
            if (controller !== request || !dialog.open) return;
            const data = payload.data;
            if (!payload.success || !data || typeof data.performed_by?.name !== 'string' ||
                !['action', 'module', 'date_time'].every(key => typeof data[key] === 'string') ||
                ![null, 'Success', 'Failed'].includes(data.result)) throw new Error('Unable to verify activity details.');
            // Only explicit allowlisted fields are rendered; metadata/raw UA/IDs never enter the dialog.
            const pairs = [['Date & Time', timeLabel(data.date_time, true)], ['Performed By', data.performed_by.name],
                ['Role', data.performed_by.role || 'Not recorded'],
                [data.affected_record?.label || 'Affected Record', data.affected_record?.name || 'Not recorded'],
                ['Action', data.action], ['Module', data.module], ['Result', data.result || 'Not recorded']];
            if (data.connection) pairs.push(['IP Address', data.connection.ip_address || 'Not recorded'],
                ['Device', data.connection.device || 'Not recorded'], ['Browser', data.connection.browser || 'Not recorded']);
            for (const [label, value] of pairs) {
                if (typeof label !== 'string' || typeof value !== 'string') throw new Error('Unable to verify activity details.');
                fields.append(element('dt', label), element('dd', value));
            }
        } catch (failure) {
            if (controller === request && dialog.open) {
                fields.replaceChildren(); error.hidden = false;
                error.textContent = failure.name === 'AbortError' ? 'Activity details timed out. Close this dialog and try again.' :
                    ['Your sign-in expired. Sign in again to view activity details.', 'You do not have permission to view this activity.',
                        'This activity is no longer available.', 'Unable to verify activity details.'].includes(failure.message)
                        ? failure.message : 'Unable to load activity details. Close this dialog and try again.';
            }
        } finally {
            window.clearTimeout(timeout);
            if (controller === request) loading.hidden = true;
        }
    }
    if (dialog) {
        section.addEventListener('click', event => {
            const button = event.target.closest('[data-activity-detail-url]');
            if (button) showDetails(button);
        });
        dialog.addEventListener('close', () => {
            controller?.abort(); controller = null;
            $('[data-activity-detail-fields]').replaceChildren();
            if (opener?.isConnected) opener.focus(); else $('#recentActivitiesTitle').focus();
        });
    }
    document.addEventListener('campushub:dashboard-data', event => render(event.detail.executive?.activities));
    document.addEventListener('campushub:dashboard-load-error', fail);
    try { render(JSON.parse(document.getElementById('executiveDashboardData').textContent).activities); } catch (_) { fail(); }
});
