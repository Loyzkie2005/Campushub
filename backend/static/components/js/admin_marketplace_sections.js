/* Additional charts on the existing authorized Super Admin Marketplace tab. */
document.addEventListener('DOMContentLoaded', () => {
    const root = document.querySelector('.marketplace-five-sections');
    if (!root) return;
    const orderGrouping = document.getElementById('orderGrouping');
    if (orderGrouping) {
        orderGrouping.form.querySelector('[data-order-grouping-apply]').hidden = true;
        orderGrouping.addEventListener('change', () => orderGrouping.form.requestSubmit());
        // Preserve this card's grouping when existing date/sales/forecast forms submit.
        root.closest('body')?.querySelectorAll('form.analytics-period-form, form.analytics-inline-form, form.analytics-forecast-form').forEach(form => {
            if (form === orderGrouping.form || form.querySelector('[name="order_grouping"]')) return;
            const input = document.createElement('input');
            input.type = 'hidden'; input.name = 'order_grouping'; input.value = orderGrouping.value;
            form.append(input);
        });
    }
    if (typeof Chart === 'undefined') {
        root.querySelectorAll('.analytics-chart, .analytics-donut').forEach(wrap => {
            wrap.hidden = true;
            const note = document.createElement('p'); note.className = 'marketplace-chart-fallback';
            note.textContent = wrap.closest('.marketplace-orders-section') ? 'Chart unavailable. Recorded counts remain available in this card.' : 'Chart unavailable. Recorded values remain in the accompanying tables.';
            wrap.before(note);
        });
        return;
    }
    const colors = ['#1A1851', '#FCB316', '#98A2B3'];
    for (const [canvasId, sourceId, type] of [
        ['marketplacePaymentChart', 'marketplacePaymentChartData', 'doughnut'],
        ['marketplaceFulfillmentChart', 'marketplaceFulfillmentChartData', 'doughnut'],
        ['marketplaceOrderVolumeChart', 'marketplaceOrderVolumeData', 'bar'],
    ]) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) continue;
        const data = JSON.parse(document.getElementById(sourceId).textContent);
        const volume = canvasId === 'marketplaceOrderVolumeChart';
        canvas.closest('.marketplace-order-distribution-layout')?.querySelectorAll('.marketplace-order-indicator').forEach((indicator, index) => {
            indicator.style.backgroundColor = colors[index % colors.length];
        });
        new Chart(canvas, {
            type, data: {labels: data.labels, datasets: [{label: 'Submitted orders',
                data: data.values, backgroundColor: volume ? colors[0] : colors,
                borderColor: volume ? colors[0] : '#FFFFFF', borderWidth: 2,
                ...(volume ? {maxBarThickness: 28, borderRadius: 3} : {})}]},
            options: {responsive: true, maintainAspectRatio: false, animation: false,
                ...(volume ? {scales: {x: {grid: {display: false}, ticks: {autoSkip: true, maxTicksLimit: canvas.clientWidth < 400 ? 3 : 7, maxRotation: 0,
                    callback(value) { const label = this.getLabelForValue(value); return canvas.clientWidth < 400 ? label.replace(/,\s*\d{4}$/, '') : label; }}}, y: {beginAtZero: true, ticks: {precision: 0}, grid: {color: '#E8EAF0'}}}} : {cutout: '65%'}),
                plugins: {legend: {display: false, position: 'bottom', labels: {boxWidth: 10, padding: 10,
                    filter: (item, chartData) => Number(chartData.datasets[0].data[item.index]) > 0}},
                    tooltip: {callbacks: {label: context => `${volume ? 'Submitted orders' : context.label}: ${context.raw}${volume ? '' : ' orders'}`}}}},
        });
    }
});
