document.addEventListener('DOMContentLoaded', function () {
    const paletteRoot = document.querySelector('[data-dashboard-palette]') || document.documentElement;
    const paletteStyle = getComputedStyle(paletteRoot);
    const palette = {
        navy: paletteStyle.getPropertyValue('--dashboard-navy').trim() || '#1A1851',
        gold: paletteStyle.getPropertyValue('--dashboard-gold').trim() || '#FCB315',
        muted: paletteStyle.getPropertyValue('--dashboard-muted').trim() || '#626781',
        grayLight: paletteStyle.getPropertyValue('--dashboard-gray-light').trim() || '#d5d7e0',
    };
    document.querySelectorAll('.legend-dot[data-color]').forEach((dot) => {
        const color = dot.dataset.color;
        if (color && CSS.supports('color', color)) {
            dot.style.backgroundColor = color;
        }
    });

    document.querySelectorAll('.util-bar[data-utilization]').forEach((bar) => {
        const utilization = Number(bar.dataset.utilization);
        const clampedValue = Number.isFinite(utilization)
            ? Math.min(100, Math.max(0, utilization))
            : 0;
        bar.style.width = `${clampedValue}%`;
    });

    document.querySelectorAll('.booking-bar[data-booking-bar]').forEach((bar) => {
        const bookingBar = Number(bar.dataset.bookingBar);
        const clampedValue = Number.isFinite(bookingBar)
            ? Math.min(100, Math.max(0, bookingBar))
            : 0;
        bar.style.width = `${clampedValue}%`;
    });

    function applyFacilityUtilizationBars(root = document) {
        root.querySelectorAll('.facility-utilization-track span[data-utilization]').forEach((bar) => {
            const utilization = Number(bar.dataset.utilization);
            const clampedValue = Number.isFinite(utilization)
                ? Math.min(100, Math.max(0, utilization))
                : 0;
            bar.style.width = `${clampedValue}%`;
        });
    }

    applyFacilityUtilizationBars();

    let revenueChart = null;
    let facilityBookingChart = null;
    let facilityRevenueChart = null;
    let facilityStatusChart = null;
    document.addEventListener('campushub:dashboard-data', (event) => {
        updateFacilityAnalytics(event.detail.facilities);
    });
    if (typeof Chart === 'undefined') return;

    function parseChartData(elementId) {
        const dataEl = document.getElementById(elementId);
        if (!dataEl) return { labels: [], values: [], orderValues: [] };
        try {
            const payload = JSON.parse(dataEl.textContent || '{}');
            return {
                labels: Array.isArray(payload.labels) ? payload.labels : [],
                values: Array.isArray(payload.values) ? payload.values.map(Number) : [],
                orderValues: Array.isArray(payload.order_values)
                    ? payload.order_values.map(Number)
                    : [],
            };
        } catch (_) {
            return { labels: [], values: [], orderValues: [] };
        }
    }

    function parseFacilityChartData(elementId) {
        const dataEl = document.getElementById(elementId);
        const empty = {
            labels: [], approved: [], pending: [], completed: [], cancelled: [],
        };
        if (!dataEl) return empty;
        try {
            const payload = JSON.parse(dataEl.textContent || '{}');
            return {
                labels: Array.isArray(payload.labels) ? payload.labels : [],
                approved: Array.isArray(payload.approved) ? payload.approved.map(Number) : [],
                pending: Array.isArray(payload.pending) ? payload.pending.map(Number) : [],
                completed: Array.isArray(payload.completed) ? payload.completed.map(Number) : [],
                cancelled: Array.isArray(payload.cancelled) ? payload.cancelled.map(Number) : [],
            };
        } catch (_) {
            return empty;
        }
    }

    function parseSingleSeriesChartData(elementId) {
        const dataEl = document.getElementById(elementId);
        if (!dataEl) return { labels: [], values: [] };
        try {
            const payload = JSON.parse(dataEl.textContent || '{}');
            return {
                labels: Array.isArray(payload.labels) ? payload.labels : [],
                values: Array.isArray(payload.values) ? payload.values.map(Number) : [],
            };
        } catch (_) {
            return { labels: [], values: [] };
        }
    }

    function parseJsonObject(elementId) {
        const dataEl = document.getElementById(elementId);
        if (!dataEl) return {};
        try {
            const payload = JSON.parse(dataEl.textContent || '{}');
            return payload && typeof payload === 'object' ? payload : {};
        } catch (_) {
            return {};
        }
    }

    const revenueCanvas = document.getElementById('revenueOverviewChart');
    if (revenueCanvas) {
        const { labels, values, orderValues } = parseChartData('revenueChartData');
        const maxSales = values.reduce((max, value) => Math.max(max, Number(value) || 0), 0);
        const maxOrders = orderValues.reduce((max, value) => Math.max(max, Number(value) || 0), 0);
        const salesMax = Math.max(100, Math.ceil(maxSales / 50) * 50 || 100);
        const ordersMax = Math.max(5, Math.ceil(maxOrders / 2) * 2 || 5);
        const ctx = revenueCanvas.getContext('2d');

        revenueChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Sales (₱)',
                        data: values,
                        yAxisID: 'ySales',
                        borderColor: '#1A1851',
                        backgroundColor: '#1A1851',
                        borderWidth: 2.5,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#1A1851',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        tension: 0.35,
                        fill: false,
                    },
                    {
                        label: 'Orders',
                        data: orderValues,
                        yAxisID: 'yOrders',
                        borderColor: '#FCB315',
                        backgroundColor: '#FCB315',
                        borderWidth: 2.5,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#FCB315',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        tension: 0.35,
                        fill: false,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        backgroundColor: '#ffffff',
                        titleColor: '#0f172a',
                        bodyColor: '#64748b',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {
                            label: (context) => {
                                const value = Number(context.parsed.y || 0);
                                if (context.dataset.yAxisID === 'yOrders') {
                                    return ` Orders: ${value}`;
                                }
                                return ` Sales: ₱${value.toLocaleString(undefined, {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2,
                                })}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        offset: false,
                        ticks: {
                            color: '#94a3b8',
                            font: { family: 'Inter, sans-serif', size: 12, weight: '600' },
                        },
                    },
                    ySales: {
                        type: 'linear',
                        position: 'left',
                        min: 0,
                        max: salesMax,
                        grid: {
                            display: true,
                            drawOnChartArea: true,
                            color: '#eef2f7',
                            borderDash: [4, 4],
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: { family: 'Inter, sans-serif', size: 12, weight: '600' },
                            callback: (value) => `₱${Number(value).toLocaleString()}`,
                        },
                    },
                    yOrders: {
                        type: 'linear',
                        position: 'right',
                        min: 0,
                        max: ordersMax,
                        display: false,
                        grid: { display: false },
                        ticks: { display: false },
                    },
                },
            },
        });
    }

    const facilityBookingCanvas = document.getElementById('facilityBookingOverviewChart');
    if (facilityBookingCanvas && !document.querySelector('[data-booking-overview]')) {
        const chartData = parseFacilityChartData('facilityBookingChartData');
        const ctx = facilityBookingCanvas.getContext('2d');

        facilityBookingChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: 'Approved',
                        data: chartData.approved,
                        backgroundColor: palette.navy,
                        borderRadius: 3,
                        maxBarThickness: 28,
                    },
                    {
                        label: 'Pending',
                        data: chartData.pending,
                        backgroundColor: palette.gold,
                        borderRadius: 3,
                        maxBarThickness: 28,
                    },
                    {
                        label: 'Completed',
                        data: chartData.completed,
                        backgroundColor: palette.muted,
                        borderRadius: 3,
                        maxBarThickness: 28,
                    },
                    {
                        label: 'Rejected / Cancelled',
                        data: chartData.cancelled,
                        backgroundColor: palette.grayLight,
                        borderColor: palette.muted,
                        borderWidth: 1,
                        borderRadius: 3,
                        maxBarThickness: 28,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#ffffff',
                        titleColor: '#0f172a',
                        bodyColor: '#64748b',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: { label: (context) => ` ${context.dataset.label}: ${Number(context.parsed.y || 0)}` },
                    },
                },
                scales: {
                    x: {
                        stacked: true,
                        grid: { display: false },
                        ticks: {
                            color: '#94a3b8',
                            font: { family: 'Inter, sans-serif', size: 12, weight: '600' },
                        },
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        min: 0,
                        ticks: {
                            stepSize: 1,
                            precision: 0,
                            color: '#94a3b8',
                            font: { family: 'Inter, sans-serif', size: 12, weight: '600' },
                        },
                        grid: {
                            color: '#eef2f7',
                            borderDash: [4, 4],
                        },
                    },
                },
            },
        });
    }

    const facilityRevenueCanvas = document.getElementById('facilityRevenueChart');
    if (facilityRevenueCanvas) {
        const chartData = parseSingleSeriesChartData('facilityRevenueChartData');
        const ctx = facilityRevenueCanvas.getContext('2d');

        facilityRevenueChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Facility revenue',
                    data: chartData.values,
                    borderColor: palette.navy,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 2.5,
                    pointHoverRadius: 5,
                    pointBackgroundColor: palette.navy,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 1.5,
                    tension: 0.35,
                    fill: false,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#ffffff',
                        titleColor: '#0f172a',
                        bodyColor: '#64748b',
                        borderColor: '#e5e7eb',
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => ` Revenue: ${formatPeso(context.parsed.y)}`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#94a3b8',
                            maxTicksLimit: 5,
                            font: { family: 'Inter, sans-serif', size: 12, weight: '600' },
                        },
                    },
                    y: {
                        beginAtZero: true,
                        display: false,
                        grid: { display: false },
                    },
                },
            },
        });
    }

    const facilityStatusCanvas = document.getElementById('facilityStatusChart');
    if (facilityStatusCanvas) {
        const availability = parseJsonObject('facilityStatusChartData');
        facilityStatusChart = new Chart(facilityStatusCanvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Available', 'Occupied', 'Maintenance', 'Blocked'],
                datasets: [{
                    data: [
                        Number(availability.available || 0),
                        Number(availability.occupied || 0),
                        Number(availability.maintenance || 0),
                        Number(availability.blocked || 0),
                    ],
                    backgroundColor: [palette.navy, palette.muted, palette.gold, palette.grayLight],
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverOffset: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                cutout: '68%',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` ${context.label}: ${Number(context.raw || 0)}`,
                        },
                    },
                },
            },
        });
    }

    function updateRevenueChart(labels, values, orderValues) {
        if (!revenueChart) return;
        const maxSales = values.reduce((max, value) => Math.max(max, Number(value) || 0), 0);
        const maxOrders = orderValues.reduce((max, value) => Math.max(max, Number(value) || 0), 0);
        revenueChart.data.labels = labels;
        revenueChart.data.datasets[0].data = values;
        if (revenueChart.data.datasets[1]) {
            revenueChart.data.datasets[1].data = orderValues;
        }
        revenueChart.options.scales.ySales.max = Math.max(100, Math.ceil(maxSales / 50) * 50 || 100);
        revenueChart.options.scales.yOrders.max = Math.max(5, Math.ceil(maxOrders / 2) * 2 || 5);
        revenueChart.update('none');
    }

    function updateFacilityBookingChart(chartData) {
        if (!facilityBookingChart) return;
        facilityBookingChart.data.labels = chartData.labels || [];
        const series = ['approved', 'pending', 'completed', 'cancelled'];
        series.forEach((key, index) => {
            if (facilityBookingChart.data.datasets[index]) {
                facilityBookingChart.data.datasets[index].data = (chartData[key] || []).map(Number);
            }
        });
        facilityBookingChart.update('none');
    }

    function updateFacilityRevenueChart(chartData) {
        if (!facilityRevenueChart) return;
        facilityRevenueChart.data.labels = chartData.labels || [];
        facilityRevenueChart.data.datasets[0].data = (chartData.values || []).map(Number);
        facilityRevenueChart.update('none');
    }

    function updateFacilityStatusChart(availability) {
        const status = availability || {};
        const values = [
            Number(status.available || 0),
            Number(status.occupied || 0),
            Number(status.maintenance || 0),
            Number(status.blocked || 0),
        ];
        if (facilityStatusChart) {
            facilityStatusChart.data.datasets[0].data = values;
            facilityStatusChart.update('none');
        }
        setDashboardText('facilityStatusTotal', values.reduce((total, value) => total + value, 0));
    }

    function setDashboardText(id, value) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }

    function formatPeso(value) {
        const amount = Number(value || 0);
        return `\u20B1${amount.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    }

    function updateFacilityUtilization(rows) {
        const list = document.getElementById('facilityUtilizationList');
        if (!list || list.closest('[data-facility-utilization]')) return;
        list.replaceChildren();

        if (!Array.isArray(rows) || rows.length === 0) {
            const empty = document.createElement('p');
            empty.className = 'facility-analytics-empty';
            empty.textContent = 'No facility usage in this period.';
            list.appendChild(empty);
            return;
        }

        rows.forEach((facility) => {
            const row = document.createElement('div');
            row.className = 'facility-utilization-row';

            const details = document.createElement('div');
            details.className = 'facility-utilization-copy';
            const name = document.createElement('strong');
            name.textContent = facility.name || 'Facility';
            const hours = document.createElement('span');
            hours.textContent = `${Number(facility.booked_hours || 0).toLocaleString()} booked hours`;
            details.append(name, hours);

            const track = document.createElement('div');
            track.className = 'facility-utilization-track';
            const bar = document.createElement('span');
            bar.dataset.utilization = String(facility.util_pct || 0);
            track.appendChild(bar);

            const percent = document.createElement('b');
            percent.textContent = `${Number(facility.util_pct || 0).toLocaleString()}%`;
            row.append(details, track, percent);
            list.appendChild(row);
        });

        applyFacilityUtilizationBars(list);
    }

    function updateFacilityAnalytics(analytics) {
        if (!analytics) return;
        updateFacilityBookingChart(analytics.chart || {});
        updateFacilityRevenueChart(analytics.revenue_chart || {});

        const totals = analytics.status_totals || {};
        setDashboardText('facilityStatusApproved', totals.approved || 0);
        setDashboardText('facilityStatusPending', totals.pending || 0);
        setDashboardText('facilityStatusCompleted', totals.completed || 0);
        setDashboardText('facilityStatusCancelled', totals.cancelled || 0);

        const availability = analytics.availability || {};
        setDashboardText('facilityAvailabilityAvailable', availability.available || 0);
        setDashboardText('facilityAvailabilityOccupied', availability.occupied || 0);
        setDashboardText('facilityAvailabilityMaintenance', availability.maintenance || 0);
        setDashboardText('facilityAvailabilityBlocked', availability.blocked || 0);
        setDashboardText('facilityScheduleConflicts', analytics.schedule_conflicts || 0);
        setDashboardText('facilityPeriodRevenue', formatPeso(analytics.period_revenue));
        updateFacilityStatusChart(availability);

        const mostBooked = analytics.most_booked;
        setDashboardText('facilityMostBookedName', mostBooked?.name || 'No bookings yet');
        setDashboardText(
            'facilityMostBookedCount',
            mostBooked ? `${mostBooked.bookings} approved/completed bookings` : 'Selected period',
        );
        updateFacilityUtilization(analytics.facilities || []);
    }

    function updateRevenueAmount(weekRevenue) {
        const amountEl = document.querySelector('#sales-overview-card .revenue-amount strong');
        if (!amountEl || weekRevenue == null) return;
        const amount = Number(weekRevenue);
        amountEl.innerHTML = Number.isFinite(amount)
            ? `\u20B1${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : `\u20B1${weekRevenue}`;
    }

    async function refreshDashboardCharts() {
        const revenueSelect = document.getElementById('revenuePeriodSelect');
        const facilitySelect = document.getElementById('facilityPeriodSelect');
        const url = new URL(window.location.href);
        if (revenueSelect) {
            url.searchParams.set('grouping', revenueSelect.value);
            url.searchParams.set('sales_grouping', revenueSelect.value);
            url.searchParams.delete('sales_days');
        }
        if (facilitySelect) url.searchParams.set('facility_days', facilitySelect.value);

        const response = await fetch(url.toString(), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                Accept: 'application/json',
            },
        });
        if (!response.ok) throw new Error('Failed to load chart data');
        const payload = await response.json();

        const chartPayload = payload.revenue_chart || payload.sales_chart;
        if (chartPayload) {
            updateRevenueChart(
                chartPayload.labels || [],
                (chartPayload.values || chartPayload.sales || []).map(Number),
                (chartPayload.order_values || chartPayload.orders || []).map(Number),
            );
            updateRevenueAmount(payload.week_revenue || payload.period_sales_sum);
        }
        if (payload.facility_analytics) updateFacilityAnalytics(payload.facility_analytics);

        window.history.replaceState({}, '', url.toString());
    }

    const chartPeriodSelects = document.querySelectorAll(
        '#revenuePeriodSelect, #facilityPeriodSelect',
    );
    chartPeriodSelects.forEach((select) => {
        select.addEventListener('change', () => {
            select.disabled = true;
            const url = new URL(window.location.href);
            if (select.id === 'revenuePeriodSelect') {
                url.searchParams.set('grouping', select.value);
                url.searchParams.delete('sales_days');
            } else {
                url.searchParams.set('facility_days', select.value);
            }
            window.location.href = url.toString();
        });
    });

    document.querySelectorAll('.pending-approve-form').forEach((form) => {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const button = form.querySelector('.pending-approve-btn');
            if (button) {
                button.disabled = true;
                button.textContent = 'Approving…';
            }
            try {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                    },
                    body: new FormData(form),
                });
                if (!response.ok) throw new Error('Approve failed');
                const row = form.closest('.pending-product-row');
                if (row) row.remove();
                const list = document.querySelector('.pending-products-list');
                if (list && !list.querySelector('.pending-product-row')) {
                    list.innerHTML = '<p class="pending-products-empty">No products waiting for approval.</p>';
                }
            } catch (_) {
                if (button) {
                    button.disabled = false;
                    button.textContent = 'Approve';
                }
                form.submit();
            }
        });
    });
});
