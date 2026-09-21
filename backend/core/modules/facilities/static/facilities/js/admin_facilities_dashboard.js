/**
 * CampusHub Facilities Admin Dashboard Controller
 * Handles Chart.js initialization and AJAX period switching
 */

document.addEventListener("DOMContentLoaded", function () {
    const bookingChartCanvas = document.getElementById("bookingTrendChart");
    const bookingPeriodSelect = document.getElementById("bookingPeriodSelect");
    const bookingPeriodTotalEl = document.getElementById("bookingPeriodTotal");
    const chartDataScript = document.getElementById("bookingTrendChartData");

    if (!bookingChartCanvas || !chartDataScript) return;

    let initialData = { labels: [], values: [] };
    try {
        initialData = JSON.parse(chartDataScript.textContent || "{}");
    } catch (e) {
        console.error("Failed to parse bookingTrendChartData", e);
    }

    const ctx = bookingChartCanvas.getContext("2d");
    const bookingTrendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: initialData.labels || [],
            datasets: [
                {
                    label: "New Bookings",
                    data: initialData.values || [],
                    borderColor: "#1A1851",
                    backgroundColor: "rgba(26, 24, 81, 0.06)",
                    borderWidth: 2,
                    pointBackgroundColor: "#1A1851",
                    pointRadius: 3,
                    fill: true,
                    tension: 0.25
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return ` Bookings: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 11, family: "Roboto, sans-serif" },
                        color: "#64748b"
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "#f1f5f9" },
                    ticks: {
                        font: { size: 11, family: "Roboto, sans-serif" },
                        color: "#1A1851",
                        precision: 0
                    }
                }
            }
        }
    });

    if (bookingPeriodSelect) {
        bookingPeriodSelect.addEventListener("change", function () {
            const days = this.value;
            fetch(`/admin-dashboard/?booking_days=${days}`, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data && data.booking_chart) {
                        bookingTrendChart.data.labels = data.booking_chart.labels;
                        bookingTrendChart.data.datasets[0].data = data.booking_chart.values;
                        bookingTrendChart.update();
                        if (bookingPeriodTotalEl && data.period_bookings_sum !== undefined) {
                            bookingPeriodTotalEl.textContent = data.period_bookings_sum;
                        }
                    }
                })
                .catch(err => console.error("Error refreshing booking trend chart", err));
        });
    }
});
