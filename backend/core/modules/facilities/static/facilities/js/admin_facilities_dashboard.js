/* Reuses the role-scoped Django dashboard endpoint and existing Chart.js. */
document.addEventListener('DOMContentLoaded', () => {
    'use strict';
    const root = document.getElementById('facilityDashboard');
    const canvas = document.getElementById('bookingTrendChart');
    const select = document.getElementById('bookingPeriodSelect');
    const message = document.getElementById('bookingTrendMessage');
    const retry = document.getElementById('bookingTrendRetry');
    if (!root || !canvas || !select || !message || !retry) return;
    let chart, controller, revision = 0, loaded = select.value, failedGrouping;
    const frame = canvas.parentElement;
    const announce = (data) => {
        const total = data.values.reduce((sum, value) => sum + Number(value), 0);
        document.getElementById('bookingPeriodTotal').textContent = String(total);
        canvas.setAttribute('aria-label', `${total} booking requests submitted across ${data.labels.length} ${select.value} periods`);
        message.textContent = total ? '' : 'No booking requests in this period.';
        frame.hidden = total === 0;
    };
    const valid = data => data && Array.isArray(data.labels) && Array.isArray(data.values) && data.labels.length === data.values.length && data.values.every(value => Number.isFinite(Number(value)) && Number(value) >= 0);
    function draw(data) {
        if (!valid(data)) throw new Error('Booking chart data is unavailable.');
        if (!data.values.some(value => Number(value) > 0)) { announce(data); return; }
        if (typeof Chart === 'undefined') throw new Error('The chart could not load. Refresh this page to try again.');
        frame.hidden = false;
        if (chart) {
            chart.data.labels = data.labels;
            chart.data.datasets[0].data = data.values;
            chart.update();
        } else {
            chart = new Chart(canvas, {
                type: 'bar',
                data: {labels: data.labels, datasets: [{label:'Booking requests', data:data.values, backgroundColor:'#1A1851', borderRadius:3, maxBarThickness:28}]},
                options: {responsive:true, maintainAspectRatio:false, animation:false,
                    plugins:{legend:{display:false}, tooltip:{displayColors:false}},
                    scales:{x:{grid:{display:false}, ticks:{color:'#606781', maxTicksLimit:8, font:{family:'Inter, sans-serif',size:12}}}, y:{beginAtZero:true, ticks:{precision:0,color:'#606781',font:{family:'Inter, sans-serif',size:12}},grid:{color:'#E8EAF0'}}}}
            });
        }
        announce(data);
    }
    try { draw(JSON.parse(document.getElementById('bookingTrendChartData').textContent)); }
    catch (error) { frame.hidden = true; message.textContent = error.message || 'Unable to display the booking chart.'; retry.hidden = false; }
    async function refresh() {
        const current = ++revision;
        controller?.abort(); controller = new AbortController();
        const requested = select.value;
        canvas.parentElement.setAttribute('aria-busy','true'); message.textContent = 'Updating booking trend…'; retry.hidden = true;
        try {
            const url = new URL(root.dataset.trendUrl, location.origin);
            const context = new URLSearchParams(location.search);
            for (const key of ['__at', 'booking_days']) {
                if (context.has(key)) url.searchParams.set(key, context.get(key));
            }
            url.searchParams.set('booking_grouping', requested);
            const response = await fetch(url, {headers:{'X-Requested-With':'XMLHttpRequest'}, credentials:'same-origin', signal:controller.signal});
            if (!response.ok) throw new Error('Unable to load the booking trend. Try again.');
            const data = await response.json();
            if (current !== revision) return;
            draw(data.booking_chart);
            document.getElementById('bookingTrendPeriod').textContent = data.booking_period_label;
            loaded = requested;
            failedGrouping = null;
        } catch (error) {
            if (error.name === 'AbortError' || current !== revision) return;
            failedGrouping = requested; select.value = loaded; if (!chart) frame.hidden = true; message.textContent = error.message || 'Unable to load the booking trend. Try again.'; retry.hidden = false;
        } finally { if (current === revision) canvas.parentElement.setAttribute('aria-busy','false'); }
    }
    select.addEventListener('change', refresh);
    retry.addEventListener('click', () => { if (typeof Chart === 'undefined') location.reload(); else { if (failedGrouping) select.value = failedGrouping; refresh(); } });
});
