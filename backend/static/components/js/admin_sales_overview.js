document.addEventListener('DOMContentLoaded', async () => {
    const form = document.getElementById('salesOverviewFilters');
    const canvas = document.getElementById('salesOverviewChart');
    if (!form || !canvas) return;
    // Includes Marketplace's header controls associated through the HTML form attribute.
    const periodSelect = form.elements.namedItem('period') || form.elements.namedItem('sales_days');
    const customDates = document.getElementById('salesCustomDates');
    const daysHidden = document.getElementById('salesDaysHidden');

    const globalDashboard = document.querySelector('[data-global-dashboard]');
    const executive = Boolean(document.querySelector('[data-executive-dashboard]'));
    const revenueOnly = executive || form.hasAttribute('data-revenue-only');
    if (!globalDashboard && periodSelect && customDates) {
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
        if (!globalDashboard) select.addEventListener('change', () => form.requestSubmit());
    });
    const error = document.getElementById('salesOverviewChartError');
    let data = JSON.parse(document.getElementById('revenueChartData').textContent);
    let updateChart, chart;
    const card = form.closest('.sales-overview');
    function styleComparisons() {
        card.querySelectorAll('.dashboard-comparison').forEach((comparison) => {
            const text = comparison.textContent;
            if (comparison.dataset.semanticType !== 'positive') {
                comparison.textContent = text;
                return;
            }
            const divider = text.indexOf(' vs ');
            const change = document.createElement('span');
            change.className = 'sales-comparison-change';
            change.textContent = divider < 0 ? text : text.slice(0, divider);
            comparison.replaceChildren(change, document.createTextNode(divider < 0 ? '' : text.slice(divider)));
        });
    }

    const money = new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' });
    const numbers = new Intl.NumberFormat('en-PH', { maximumFractionDigits: 0 });
    let activeBucket = -1;
    function describe(index) {
        if (executive) return `${data.tooltip_labels?.[index] || data.labels[index]}: Marketplace Revenue ${money.format(data.sales[index])}.`;
        return `${data.tooltip_labels?.[index] || data.labels[index]}: Marketplace Sales ${money.format(data.sales[index])}; Completed Orders ${numbers.format(data.orders[index])}.`;
    }
    function updateDescriptions() {
        if (!globalDashboard) return;
        const rows = document.createDocumentFragment();
        data.labels.forEach((_, index) => {
            const row = document.createElement('li'); row.textContent = describe(index); rows.append(row);
        });
        document.querySelector('[data-sales-trend-description]').replaceChildren(rows);
        document.querySelector('[data-sales-chart-live]').textContent = '';
        activeBucket = -1;
    }
    function updateChartVisibility() {
        const available = typeof Chart !== 'undefined' && !canvas.dataset.chartFailed;
        const empty = revenueOnly && !data.orders.some(value => Number(value) > 0);
        error.hidden = available || empty;
        if (globalDashboard) { canvas.hidden = !available; if (executive) canvas.parentElement.hidden = !data.orders.some(value => Number(value) > 0); }
        else canvas.parentElement.hidden = !available || (revenueOnly && !data.orders.some(value => Number(value) > 0));
    }
    document.addEventListener('campushub:dashboard-data', (event) => {
        data = event.detail.marketplace.sales_trend;
        styleComparisons();
        updateDescriptions();
        updateChartVisibility();
        ensureChart();
        if (!executive || data.orders.some(value => Number(value) > 0)) updateChart?.();
    });
    document.addEventListener('campushub:sales-trend-data', (event) => {
        data = event.detail.marketplace.sales_trend;
        updateDescriptions();
        updateChartVisibility();
        ensureChart();
        if (!executive || data.orders.some(value => Number(value) > 0)) updateChart?.();
    });
    updateChartVisibility();
    styleComparisons();
    updateDescriptions();
    if (typeof Chart === 'undefined') {
        return;
    }
    if (document.fonts) await document.fonts.ready;
    function ensureChart() {
        if (chart || (revenueOnly && !data.orders.some(value => Number(value) > 0)) || typeof Chart === 'undefined') return;
        try {
            const navy = '#1A1851';
            const gold = '#FCB315';
            const muted = '#626781';
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
            const font = { family: 'Inter, sans-serif', size: 12 };
            chart = new Chart(canvas, {
                type: revenueOnly ? 'line' : 'bar',
                data: {
                    labels: data.labels,
                    datasets: [
                        {
                            type: revenueOnly ? 'line' : globalDashboard ? 'bar' : 'line', label: revenueOnly ? 'Marketplace Revenue' : 'Sales (\u20b1)', data: data.sales,
                            yAxisID: 'ySales', borderColor: navy,
                            backgroundColor: globalDashboard ? navy : 'rgba(26, 24, 81, 0.035)',
                            borderWidth: executive ? 2 : globalDashboard ? 0 : 2, borderRadius: 2, maxBarThickness: 28,
                            categoryPercentage: 0.8, barPercentage: 0.7,
                            pointStyle: 'circle', pointRadius: executive ? 2 : 4, pointHoverRadius: 6,
                            pointBackgroundColor: navy, pointBorderColor: '#FFFFFF',
                            pointBorderWidth: 1.5, tension: 0.3, cubicInterpolationMode: 'monotone',
                            fill: !globalDashboard, order: globalDashboard ? 1 : 0,
                        },
                        ...(revenueOnly ? [] : [{
                            type: globalDashboard ? 'line' : 'bar', label: globalDashboard ? 'Completed Orders' : 'Orders', data: data.orders, hidden: executive,
                            yAxisID: 'yOrders', backgroundColor: gold, borderColor: gold,
                            borderWidth: globalDashboard ? 2.5 : 0, borderRadius: 2, maxBarThickness: 22,
                            pointStyle: 'circle', pointRadius: globalDashboard ? context => Number(context.raw) > 0 ? 3 : 0 : 3, pointHoverRadius: 5,
                            pointBackgroundColor: gold, pointBorderColor: navy, pointBorderWidth: 1,
                            tension: 0, fill: false,
                            categoryPercentage: 0.8, barPercentage: 0.7, order: globalDashboard ? 0 : 1,
                        }]),
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
                                    ? `${revenueOnly ? 'Marketplace Revenue' : 'Sales'}: ${money.format(context.parsed.y)}`
                                    : `${numbers.format(context.parsed.y)} ${context.parsed.y === 1 ? 'order' : 'orders'}`,
                            },
                        },
                    },
                    scales: {
                        x: {
                            offset: true,
                            grid: { display: false }, border: { color: '#e3e6ef' },
                            ticks: { color: muted, font, maxRotation: 0, autoSkip: true, maxTicksLimit: globalDashboard ? 8 : 12 },
                        },
                        ySales: {
                            position: 'left', min: 0, max: salesScale.max,
                            title: { display: true, text: revenueOnly ? 'Revenue (\u20b1)' : globalDashboard ? 'Sales (\u20b1)' : 'Sales Amount (\u20b1)', color: muted, font },
                            grid: { color: '#edf0f5' }, border: { display: false },
                            ticks: { color: muted, font, stepSize: salesScale.step, callback: (value) => `\u20b1${numbers.format(value)}` },
                        },
                        ...(!revenueOnly ? { yOrders: {
                            display: true, position: 'right', min: 0, max: ordersScale.max,
                            title: { display: true, text: globalDashboard ? 'Completed Orders' : 'Number of Orders', color: muted, font },
                            grid: { drawOnChartArea: false }, border: { display: false },
                            ticks: { color: muted, font, precision: 0, stepSize: ordersScale.step },
                        }} : {}),
                    },
                },
            });
            updateChart = () => {
                chart.setActiveElements([]);
                chart.tooltip.setActiveElements([], { x: 0, y: 0 });
                chart.data.labels = data.labels;
                chart.data.datasets[0].data = data.sales;
                if (!revenueOnly) chart.data.datasets[1].data = data.orders;
                const sales = scaleFor(data.sales, 100);
                const orders = scaleFor(data.orders, 1);
                chart.options.scales.ySales.max = sales.max;
                chart.options.scales.ySales.ticks.stepSize = sales.step;
                if (!revenueOnly) {
                    chart.options.scales.yOrders.max = orders.max;
                    chart.options.scales.yOrders.ticks.stepSize = orders.step;
                }
                chart.update('none');
                // Filters finish their loading state after this event. Resize once the
                // canvas is visible again, including a first sale after an empty range.
                if (globalDashboard) requestAnimationFrame(() => {
                    chart.resize?.();
                    chart.update('none');
                });
            };
            if (globalDashboard) canvas.addEventListener('keydown', (event) => {
                if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || !data.labels.length ||
                    globalDashboard.getAttribute('aria-busy') === 'true' || canvas.hidden || form.closest('[data-load-failed]')) return;
                event.preventDefault();
                if (event.key === 'Home') activeBucket = 0;
                else if (event.key === 'End') activeBucket = data.labels.length - 1;
                else if (activeBucket < 0) activeBucket = event.key === 'ArrowLeft' ? data.labels.length - 1 : 0;
                else activeBucket = Math.min(data.labels.length - 1, Math.max(0, activeBucket + (event.key === 'ArrowRight' ? 1 : -1)));
                document.querySelector('[data-sales-chart-live]').textContent = describe(activeBucket);
                const items = (executive ? [0] : [0, 1]).map((datasetIndex) => ({ datasetIndex, index: activeBucket }));
                chart.setActiveElements(items);
                chart.tooltip.setActiveElements(items, chart.getDatasetMeta(0).data[activeBucket].getCenterPoint());
                chart.update('none');
            });
        } catch (exception) {
            canvas.dataset.chartFailed = 'true';
            updateChartVisibility();
            console.error('Sales Overview chart could not be rendered.', exception);
        }
    }
    ensureChart();
});
