/* Compact projections of the same protected dashboard response; no extra data source. */
document.addEventListener('DOMContentLoaded', () => {
    const root = document.querySelector('[data-executive-dashboard]');
    if (!root) return;
    function safeLink(value) {
        const url = new URL(value, location.origin);
        if (url.origin !== location.origin) return '#';
        const token = window.CampusHubAdminSession?.getTabToken() || new URL(location.href).searchParams.get('__at');
        if (token) url.searchParams.set('__at', token);
        return url.href;
    }
    const users = root.querySelector('[data-users-overview]');
    const userCharts = {};
    const trendView = users?.querySelector('#userRegistrationView');
    let renderTrend = null;
    function groupRegistrations(trend, grouping) {
        if (grouping === 'daily') return trend.map(row => ({ ...row }));
        const buckets = new Map();
        const format = new Intl.DateTimeFormat('en-PH', grouping === 'weekly'
            ? { month: 'short', day: '2-digit', year: 'numeric', timeZone: 'UTC' }
            : { month: 'short', year: 'numeric', timeZone: 'UTC' });
        for (const row of trend) {
            // Source dates are already campus-local calendar dates; UTC prevents browser-zone shifts.
            const start = new Date(`${row.date}T00:00:00Z`);
            if (grouping === 'weekly') start.setUTCDate(start.getUTCDate() - (start.getUTCDay() + 6) % 7);
            else start.setUTCDate(1);
            const key = start.toISOString().slice(0, 10);
            if (!buckets.has(key)) buckets.set(key, {
                date: key, label: (grouping === 'weekly' ? 'Week of ' : '') + format.format(start), count: 0,
            });
            buckets.get(key).count += row.count;
        }
        return [...buckets.values()];
    }
    function failUsers() {
        if (!users) return;
        renderTrend = null;
        if (trendView) trendView.disabled = true;
        users.setAttribute('aria-busy', 'false');
        users.querySelectorAll('[data-user-metric]').forEach(el => { el.textContent = '\u2014'; });
        users.querySelector('[data-users-content]').hidden = true;
        users.querySelector('[data-users-error]').hidden = false;
    }
    function renderUsers(data) {
        if (!users) return;
        if (!data || !['new_registrations', 'verified_users', 'untyped'].every(key => Number.isSafeInteger(data[key]) && data[key] >= 0)
            || !Array.isArray(data.trend) || !Array.isArray(data.distribution)
            || !data.trend.every(row => row && typeof row.label === 'string' && Number.isSafeInteger(row.count) && row.count >= 0
                && /^\d{4}-\d{2}-\d{2}$/.test(row.date)
                && !Number.isNaN(Date.parse(`${row.date}T00:00:00Z`))
                && new Date(`${row.date}T00:00:00Z`).toISOString().slice(0, 10) === row.date)
            || !Number.isSafeInteger(data.trend.reduce((total, row) => total + row.count, 0))) { failUsers(); return; }
        users.setAttribute('aria-busy', 'false');
        users.querySelector('[data-users-content]').hidden = false;
        users.querySelector('[data-users-error]').hidden = true;
        users.querySelectorAll('[data-user-metric]').forEach(el => { el.textContent = data[el.dataset.userMetric].toLocaleString('en-PH'); });
        function rows(selector, entries) {
            const fragment = document.createDocumentFragment();
            entries.forEach(values => {
                const row = document.createElement('tr');
                values.forEach((value, index) => { const cell = document.createElement(index ? 'td' : 'th');
                    if (!index) cell.scope = 'row'; cell.textContent = value; row.append(cell); });
                fragment.append(row);
            });
            users.querySelector(selector).replaceChildren(fragment);
        }
        rows('[data-user-distribution-rows]', data.distribution.map(row => [row.name, row.count.toLocaleString('en-PH'), `${row.percentage}%`]));
        const note = users.querySelector('[data-user-untyped-note]');
        note.hidden = !data.untyped; note.textContent = `Account type is unavailable for ${data.untyped.toLocaleString('en-PH')} mobile accounts.`;
        users.querySelector('[data-user-distribution-table]').hidden = !data.distribution.length;
        function chart(id, kind, entries, hasData, grouping = 'daily') {
            const prefix = kind === 'line' ? 'trend' : 'distribution';
            const wrap = users.querySelector(`[data-user-${prefix}-wrap]`);
            const fallback = users.querySelector(`[data-user-${prefix}-fallback]`);
            users.querySelector(`[data-user-${prefix}-empty]`).hidden = hasData;
            fallback.hidden = true; wrap.hidden = !hasData;
            userCharts[id]?.destroy(); delete userCharts[id];
            if (!hasData) return;
            try {
                if (typeof Chart === 'undefined') throw new Error('Chart library unavailable');
                const font = { family: 'Inter, sans-serif', size: 12 };
                userCharts[id] = new Chart(document.getElementById(id), {
                    type: kind,
                    data: { labels: entries.map(row => row.label || row.name), datasets: [{
                        label: kind === 'line' ? 'New Registrations' : 'Accounts', data: entries.map(row => row.count),
                        backgroundColor: kind === 'line' ? '#1A1851' : ['#1A1851', '#FCB316', '#69717E'],
                        borderColor: kind === 'line' ? '#1A1851' : '#FFFFFF', borderWidth: 2,
                        pointRadius: 2, tension: 0.15, fill: false,
                    }] },
                    options: { responsive: true, maintainAspectRatio: false, animation: false,
                        ...(kind === 'doughnut' ? { cutout: '65%' } : {}),
                        plugins: { legend: { display: false }, tooltip: { bodyFont: font,
                            callbacks: { label: context => `${context.label}: ${Number(context.raw).toLocaleString('en-PH')}${kind === 'doughnut' ? ` (${entries[context.dataIndex].percentage}%)` : ' registrations'}` } } },
                        ...(kind === 'line' ? { scales: {
                            x: { title: { display: true, text: grouping === 'weekly' ? 'Week' : grouping === 'monthly' ? 'Month' : 'Date' }, grid: { display: false }, ticks: { font, maxTicksLimit: grouping === 'weekly' ? 4 : 8, maxRotation: 0,
                                callback: value => grouping === 'weekly' ? entries[value].label.replace('Week of ', '').replace(/, \d{4}$/, '') : entries[value].label } },
                            y: { beginAtZero: true, title: { display: true, text: 'Number of new registrations' }, ticks: { precision: 0, font }, grid: { color: '#E8EAF0' } },
                        } } : {}),
                    },
                });
            } catch (_) { wrap.hidden = true; fallback.hidden = false; }
        }
        renderTrend = () => {
            const grouping = ['daily', 'weekly', 'monthly'].includes(trendView?.value) ? trendView.value : 'daily';
            const entries = groupRegistrations(data.trend, grouping);
            const unit = grouping === 'weekly' ? 'Week' : grouping === 'monthly' ? 'Month' : 'Date';
            const title = grouping[0].toUpperCase() + grouping.slice(1);
            users.querySelector('[data-user-trend-subtitle]').textContent = grouping === 'weekly'
                ? 'Calendar weeks (Monday–Sunday); counts limited to the selected period.'
                : grouping === 'monthly' ? 'Calendar months; counts limited to the selected period.'
                : 'Daily new registrations in the selected period.';
            users.querySelector('[data-user-trend-date-column]').textContent = unit;
            users.querySelector('[data-user-trend-column]').textContent = `${title} Registrations`;
            users.querySelector('[data-user-trend-caption]').textContent = grouping === 'daily'
                ? 'New registrations by date' : `New registrations by ${unit.toLowerCase()} within the selected period`;
            users.querySelector('#userRegistrationTrendChart').setAttribute('aria-label',
                `Number of new registrations by ${unit.toLowerCase()} within the selected period. Exact values follow in the chart data table.`);
            rows('[data-user-trend-rows]', entries.map(row => [row.label, row.count.toLocaleString('en-PH')]));
            chart('userRegistrationTrendChart', 'line', entries, data.new_registrations > 0, grouping);
        };
        renderTrend();
        if (trendView) trendView.disabled = false;
        chart('usersByTypeChart', 'doughnut', data.distribution, data.distribution.length > 0);
    }
    trendView?.addEventListener('change', () => renderTrend?.());
    function fail() {
        failUsers();
        root.querySelectorAll('[data-facility-attention-count]').forEach(el => { el.textContent = '\u2014'; el.removeAttribute('data-needs-attention'); });
        root.querySelector('[data-facility-attention-error]').hidden = false;
        root.querySelector('[data-facility-attention]').hidden = true;
        root.querySelector('[data-facility-attention-empty]').hidden = true;
    }
    function render(data, payload) {
        if (!data) { fail(); return; }
        renderUsers(data.users);
        const attention = data?.facility_attention;
        const attentionKeys = ['maintenance', 'unavailable'];
        const attentionValid = attention && attentionKeys.every(key => Number.isSafeInteger(attention[key]) && attention[key] >= 0);
        root.querySelector('[data-facility-attention-error]').hidden = Boolean(attentionValid);
        root.querySelector('[data-facility-attention]').hidden = !attentionValid;
        root.querySelector('[data-facility-attention-empty]').hidden = !attentionValid || attentionKeys.some(key => attention[key] > 0);
        root.querySelectorAll('[data-facility-attention-count]').forEach(el => {
            const value = attentionValid ? attention[el.dataset.facilityAttentionCount] : null;
            el.textContent = value === null ? '\u2014' : value.toLocaleString('en-PH');
            el.toggleAttribute('data-needs-attention', value > 0);
            el.closest('li').hidden = !(value > 0);
        });
        root.querySelectorAll('[data-executive-analytics]').forEach(link => {
            if (data.analytics_urls?.[link.dataset.executiveAnalytics]) link.href = safeLink(data.analytics_urls[link.dataset.executiveAnalytics]);
        });
        if (payload?.kpis && root.querySelector('[data-executive-sellers]')) root.querySelector('[data-executive-sellers]').textContent = payload.kpis.active_sellers.value.toLocaleString('en-PH');
    }
    document.addEventListener('campushub:dashboard-data', event => render(event.detail.executive, event.detail));
    document.addEventListener('campushub:dashboard-load-error', fail);
    document.addEventListener('campushub:dashboard-loading', () => {
        users?.setAttribute('aria-busy', 'true');
        renderTrend = null;
        if (trendView) trendView.disabled = true;
    });
    try { render(JSON.parse(document.getElementById('executiveDashboardData').textContent)); }
    catch (_) { fail(); }
});
