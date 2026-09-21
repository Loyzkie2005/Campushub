document.addEventListener('DOMContentLoaded', async () => {
    const form = document.getElementById('salesOverviewFilters');
    const canvas = document.getElementById('salesOverviewChart');
    if (!form || !canvas) return;
    const periodSelect = form.querySelector('select[name="period"]') || form.querySelector('select[name="sales_days"]');
    const customDates = document.getElementById('salesCustomDates');
    const daysHidden = document.getElementById('salesDaysHidden');

    if (periodSelect && customDates) {
        periodSelect.addEventListener('change', () => {
            if (periodSelect.value === 'custom') {
                customDates.classList.remove('d-none');
                const fromInput = document.getElementById('salesDateFrom');
                if (fromInput) fromInput.focus();
            } else {
                customDates.classList.add('d-none');
                if (daysHidden) {
                    if (['1', '7', '14', '30'].includes(periodSelect.value)) {
                        daysHidden.value = periodSelect.value;
                    } else if (periodSelect.value === 'today') {
                        daysHidden.value = '1';
                    }
                }
                form.requestSubmit();
            }
        });
    }

    form.querySelectorAll('select:not([name="period"]):not([name="sales_days"])').forEach((select) => {
        select.addEventListener('change', () => form.requestSubmit());
    });
    const error = document.getElementById('salesOverviewChartError');
    if (typeof Chart === 'undefined') {
        error.hidden = false;
        canvas.parentElement.hidden = true;
        return;
    }
    if (document.fonts) await document.fonts.ready;
    try {
        const data = JSON.parse(document.getElementById('revenueChartData').textContent);
        const navy = '#1A1851';
        const gold = '#FCB316';
        const muted = '#626781';
        const money = new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' });
        const numbers = new Intl.NumberFormat('en-PH', { maximumFractionDigits: 0 });
        // Both axes have five intervals, with independently scaled units.
        function scaleFor(values, minimumStep) {
            const rawStep = Math.max(minimumStep, Math.max(0, ...values) / 5);
            const magnitude = 10 ** Math.floor(Math.log10(rawStep));
            const step = [1, 2, 5, 10].map((value) => value * magnitude)
                .find((value) => value >= rawStep);
            return { max: step * 5, step };
        }
        const salesScale = scaleFor(data.sales, 100);
        const ordersScale = scaleFor(data.orders, 1);
        const font = { family: 'Montserrat, sans-serif', size: 11 };
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        type: 'line', label: 'Sales (\u20b1)', data: data.sales,
                        yAxisID: 'ySales', borderColor: navy,
                        backgroundColor: 'rgba(26, 24, 81, 0.035)',
                        borderWidth: 2, pointStyle: 'rect', pointRadius: 4, pointHoverRadius: 6,
                        pointBackgroundColor: navy, pointBorderColor: '#FFFFFF',
                        pointBorderWidth: 1.5, tension: 0.3, cubicInterpolationMode: 'monotone',
                        fill: true, order: 0,
                    },
                    {
                        type: 'bar', label: 'Orders', data: data.orders,
                        yAxisID: 'yOrders', backgroundColor: gold, borderColor: gold,
                        borderWidth: 0, borderRadius: 2, maxBarThickness: 22,
                        categoryPercentage: 0.8, barPercentage: 0.7, order: 1,
                    },
                ],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                animation: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        titleFont: font, bodyFont: font, backgroundColor: navy,
                        callbacks: {
                            title: (items) => data.tooltip_labels?.[items[0]?.dataIndex] || items[0]?.label || '',
                            label: (context) => context.dataset.yAxisID === 'ySales'
                                ? `Sales: ${money.format(context.parsed.y)}`
                                : `${numbers.format(context.parsed.y)} ${context.parsed.y === 1 ? 'order' : 'orders'}`,
                        },
                    },
                },
                scales: {
                    x: {
                        offset: true,
                        grid: { display: false }, border: { color: '#e3e6ef' },
                        ticks: { color: muted, font, maxRotation: 0, autoSkip: true, maxTicksLimit: 12 },
                    },
                    ySales: {
                        position: 'left', min: 0, max: salesScale.max,
                        title: { display: true, text: 'Sales Amount (\u20b1)', color: muted, font },
                        grid: { color: '#edf0f5' }, border: { display: false },
                        ticks: { color: muted, font, stepSize: salesScale.step, callback: (value) => `\u20b1${numbers.format(value)}` },
                    },
                    yOrders: {
                        position: 'right', min: 0, max: ordersScale.max,
                        title: { display: true, text: 'Number of Orders', color: muted, font },
                        grid: { drawOnChartArea: false }, border: { display: false },
                        ticks: { color: muted, font, precision: 0, stepSize: ordersScale.step },
                    },
                },
            },
        });
    } catch (exception) {
        error.hidden = false;
        canvas.parentElement.hidden = true;
        console.error('Sales Overview chart could not be rendered.', exception);
    }
});
