document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    const NAVY = '#1A1851';
    const GOLD = document.body.classList.contains('super-admin-analytics') ? '#FCB316' : '#FCB315';
    const MUTED = '#68728A';
    const GRID = '#EDF0F5';

    function readJson(id, fallback = {}) {
        const element = document.getElementById(id);
        if (!element) return fallback;
        try {
            return JSON.parse(element.textContent || '{}');
        } catch (_) {
            return fallback;
        }
    }

    function submitOnce(form) {
        if (!form || form.dataset.submitting === 'true') return;
        form.dataset.submitting = 'true';
        form.submit();
    }

    // Shared Date Filter Form Handlers
    const periodForm = document.getElementById('analyticsPeriodForm');
    const periodSelect = document.getElementById('analyticsPeriod');
    const customDates = document.getElementById('analyticsCustomDates');

    if (periodSelect && periodForm) {
        periodSelect.addEventListener('change', () => {
            const isCustom = periodSelect.value === 'custom';
            if (customDates) {
                customDates.classList.toggle('d-none', !isCustom);
            }
            if (!isCustom) {
                submitOnce(periodForm);
            }
        });
    }

    if (typeof Chart === 'undefined') return;

    Chart.defaults.font.family = 'Inter, sans-serif';
    Chart.defaults.color = MUTED;

    // 1. Facilities Tab: Bookings by Facility Bar Chart
    const facilityBookingsCanvas = document.getElementById('facilityBookingsChart');
    if (facilityBookingsCanvas) {
        const data = readJson('facilityBookingsChartData', {
            labels: [],
            values: [],
            tooltip_labels: [],
        });

        new Chart(facilityBookingsCanvas, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Approved Bookings',
                        data: (data.values || []).map(Number),
                        backgroundColor: NAVY,
                        borderColor: NAVY,
                        borderWidth: 1,
                        borderRadius: 4,
                        borderSkipped: false,
                        maxBarThickness: 42,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 250 },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            title: (items) => data.labels[items[0]?.dataIndex] || '',
                            label: (context) => {
                                const val = Number(context.raw || 0);
                                return ` Approved Bookings: ${val} booking${val === 1 ? '' : 's'}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: MUTED,
                            font: { family: 'Inter, sans-serif', size: 12, weight: '600' },
                            maxRotation: 20,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: GRID },
                        ticks: {
                            color: MUTED,
                            precision: 0,
                            font: { size: 12 },
                        },
                    },
                },
            },
        });
    }

    // 2. Facilities Tab: Monthly Booking Trend
    const facilityTrendCanvas = document.getElementById('facilityMonthlyTrendChart');
    if (facilityTrendCanvas) {
        const data = readJson('facilityMonthlyTrendChartData', {
            labels: [],
            values: [],
        });

        new Chart(facilityTrendCanvas, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Bookings',
                        data: (data.values || []).map(Number),
                        backgroundColor: NAVY,
                        borderColor: NAVY,
                        borderWidth: 1,
                        borderRadius: 3,
                        maxBarThickness: 32,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 250 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` Bookings: ${Number(context.raw || 0)}`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: MUTED, font: { size: 12 } },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: GRID },
                        ticks: { color: MUTED, precision: 0, font: { size: 12 } },
                    },
                },
            },
        });
    }

    // 3. Users Tab: User Registrations by Month Bar Chart
    const userMonthlyCanvas = document.getElementById('userMonthlyChart');
    if (userMonthlyCanvas) {
        const data = readJson('userMonthlyChartData', {
            labels: [],
            values: [],
        });

        new Chart(userMonthlyCanvas, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'New Registrations',
                        data: (data.values || []).map(Number),
                        backgroundColor: NAVY,
                        borderColor: NAVY,
                        borderWidth: 1,
                        borderRadius: 4,
                        borderSkipped: false,
                        maxBarThickness: 36,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 250 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => data.labels[items[0]?.dataIndex] || '',
                            label: (context) => {
                                const val = Number(context.raw || 0);
                                return ` Registrations: ${val} account${val === 1 ? '' : 's'}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: MUTED, font: { family: 'Inter, sans-serif', size: 12, weight: '600' } },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: GRID },
                        ticks: { color: MUTED, precision: 0, font: { size: 12 } },
                    },
                },
            },
        });
    }
});
