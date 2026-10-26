document.addEventListener('DOMContentLoaded', () => {
    const section = document.getElementById('dashboardSystemStatus');
    if (!section) return;
    const labels = { online: 'Online', degraded: 'Degraded', unavailable: 'Unavailable', unknown: 'Unknown',
        healthy: 'Healthy', warning: 'Warning', failed: 'Failed', no_backup_available: 'No Backup Available' };
    const footerLabels = { online: 'Operational', healthy: 'Operational', degraded: 'Degraded', warning: 'Degraded',
        unavailable: 'Unavailable', failed: 'Unavailable', no_backup_available: 'Unavailable', unknown: 'Unknown' };
    const allowed = { database: ['online', 'degraded', 'unavailable', 'unknown'],
        chat_service: ['online', 'degraded', 'unavailable', 'unknown'],
        backup: ['healthy', 'warning', 'failed', 'no_backup_available', 'unknown'] };
    const date = new Intl.DateTimeFormat('en-PH', { timeZone: 'Asia/Manila', year: 'numeric', month: 'short', day: '2-digit', hour: 'numeric', minute: '2-digit' });
    const checkedTime = new Intl.DateTimeFormat('en-PH', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
    let controller;
    function validDate(value) {
        return value && Number.isFinite(new Date(value).getTime());
    }
    function render(statuses, checking = false) {
        // A status word without a real check time is not a verified health result.
        statuses = Object.fromEntries(Object.keys(allowed).map(key => {
            const data = statuses?.[key];
            return [key, validDate(data?.checked_at) && allowed[key].includes(data?.status) ? data : {
                status: 'unknown', message: checking ? 'Checking service status…' : 'Unable to verify service status.',
            }];
        }));
        const unavailable = section.querySelector('[data-system-unavailable]');
        if (unavailable) {
            const verified = Object.keys(allowed).some(key => validDate(statuses?.[key]?.checked_at) && allowed[key].includes(statuses?.[key]?.status) && statuses[key].status !== 'unknown');
            section.querySelector('.dashboard-service-list').hidden = checking || !verified;
            unavailable.hidden = checking || verified;
        }
        document.dispatchEvent(new CustomEvent('campushub:system-status', { detail: statuses }));
        for (const row of section.querySelectorAll('[data-system-service]')) {
            const key = row.dataset.systemService;
            const data = statuses?.[key];
            const state = allowed[key].includes(data?.status) ? data.status : 'unknown';
            const status = row.querySelector('[data-system-state]');
            status.dataset.systemState = state;
            status.textContent = (section.hasAttribute('data-status-inline') || section.hasAttribute('data-status-top')) && key === 'database' && state === 'online'
                ? 'Connected' : (section.hasAttribute('data-status-footer') && !section.hasAttribute('data-status-top') ? footerLabels : labels)[state];
            row.querySelector('[data-system-message]').textContent = data?.message || 'Unable to verify service status.';
            const checked = row.querySelector('[data-system-checked]');
            checked.hidden = !validDate(data?.checked_at);
            if (!checked.hidden) {
                checked.dateTime = data.checked_at;
                checked.textContent = `Last checked: ${(section.hasAttribute('data-status-footer') ? date : checkedTime).format(new Date(data.checked_at))}`;
                checked.title = `Last checked: ${date.format(new Date(data.checked_at))}`;
                checked.setAttribute('aria-label', checked.title);
            } else {
                checked.removeAttribute('datetime');
                checked.removeAttribute('title');
                checked.removeAttribute('aria-label');
                checked.textContent = '';
            }
            if (key === 'backup') {
                const last = row.querySelector('[data-system-last-backup]');
                last.hidden = !validDate(data?.last_successful_backup);
                if (validDate(data?.last_successful_backup)) {
                    last.dateTime = data.last_successful_backup;
                    last.textContent = `Last backup: ${date.format(new Date(data.last_successful_backup))}`;
                } else {
                    last.removeAttribute('datetime');
                    last.textContent = state === 'no_backup_available' ? 'No completed backup available.' : 'Last backup not verified.';
                }
            }
        }
    }
    async function checkSystemStatus() {
        controller?.abort();
        const active = new AbortController();
        controller = active;
        section.setAttribute('aria-busy', 'true');
        const retry = document.getElementById('systemStatusRetry');
        if (retry) retry.disabled = true;
        section.querySelector('.dashboard-system-checking').hidden = false;
        // Previous health is no longer presented as a fresh verification.
        render(Object.fromEntries(Object.keys(allowed).map((key) => [key, { status: 'unknown', message: 'Checking service status…' }])), true);
        const timeout = window.setTimeout(() => active.abort(), 5000);
        try {
            const url = new URL(section.dataset.apiUrl, window.location.origin);
            url.searchParams.set('system_status_only', '1');
            const token = new URL(window.location.href).searchParams.get('__at');
            if (token) url.searchParams.set('__at', token);
            const response = await fetch(url, { cache: 'no-store', credentials: 'same-origin', headers: { Accept: 'application/json' }, signal: active.signal });
            if (!response.ok) throw new Error('Unable to verify system status');
            const payload = await response.json();
            if (controller === active) render(payload.system_status);
        } catch (_) {
            if (controller === active) render(null);
        } finally {
            window.clearTimeout(timeout);
            if (controller === active) {
                section.setAttribute('aria-busy', 'false');
                if (retry) retry.disabled = false;
                section.querySelector('.dashboard-system-checking').hidden = true;
            }
        }
    }
    document.getElementById('dashboardRefresh')?.addEventListener('click', checkSystemStatus);
    document.getElementById('dashboardRetry')?.addEventListener('click', checkSystemStatus);
    document.getElementById('systemStatusRetry')?.addEventListener('click', checkSystemStatus);
    checkSystemStatus();
});
