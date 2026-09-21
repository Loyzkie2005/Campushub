document.addEventListener("DOMContentLoaded", () => {
    if (typeof Chart === "undefined") return;

    function readJsonScript(id, fallback) {
        const element = document.getElementById(id);
        if (!element) return fallback;
        try {
            return JSON.parse(element.textContent || "{}");
        } catch (_) {
            return fallback;
        }
    }

    const salesCanvas = document.getElementById("salesTrendChart");
    const salesData = readJsonScript("salesTrendChartData", {
        labels: [],
        values: [],
        order_values: [],
    });
    let salesChart = null;

    if (salesCanvas) {
        const salesValues = (salesData.values || []).map(Number);
        const orderValues = (salesData.order_values || []).map(Number);
        salesChart = new Chart(salesCanvas.getContext("2d"), {
            type: "bar",
            data: {
                labels: salesData.labels || [],
                datasets: [
                    {
                        type: "line",
                        label: "Sales (\u20B1)",
                        data: salesValues,
                        yAxisID: "ySales",
                        borderColor: "#1A1851",
                        backgroundColor: "#1A1851",
                        borderWidth: 3,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointBackgroundColor: "#1A1851",
                        pointBorderColor: "#1A1851",
                        pointBorderWidth: 2,
                        tension: 0.35,
                        fill: false,
                        order: 1,
                    },
                    {
                        type: "bar",
                        label: "Orders",
                        data: orderValues,
                        yAxisID: "yOrders",
                        borderColor: "#FCB316",
                        backgroundColor: "#FCB316",
                        borderWidth: 1,
                        borderRadius: 2,
                        borderSkipped: false,
                        maxBarThickness: 14,
                        order: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#FFFFFF",
                        titleColor: "#1A1851",
                        bodyColor: "#64748b",
                        borderColor: "#d9dcea",
                        borderWidth: 1,
                        callbacks: {
                            title(items) {
                                const index = items[0]?.dataIndex;
                                const tooltips = salesChart?._tooltipLabels || [];
                                return tooltips[index] || items[0]?.label || "";
                            },
                            label(context) {
                                const value = Number(context.parsed.y || 0);
                                if (context.dataset.yAxisID === "yOrders") {
                                    return ` Orders: ${value}`;
                                }
                                return ` Sales: \u20B1${value.toLocaleString(undefined, {
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
                        title: { display: false },
                        offset: false,
                        ticks: {
                            color: "#68728A",
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 10,
                            font: { family: "Montserrat", size: 9, weight: "600" },
                        },
                    },
                    ySales: {
                        type: "linear",
                        position: "left",
                        beginAtZero: true,
                        suggestedMax: 10000,
                        grid: { color: "#EDF0F5" },
                        title: { display: false },
                        ticks: {
                            color: "#68728A",
                            precision: 0,
                            stepSize: 2000,
                            font: { family: "Montserrat", size: 9, weight: "600" },
                            callback: (value) => {
                                const amount = Number(value);
                                return amount === 0 ? "\u20B10" : `\u20B1${amount / 1000}K`;
                            },
                        },
                    },
                    yOrders: {
                        type: "linear",
                        position: "right",
                        beginAtZero: true,
                        suggestedMax: 50,
                        display: true,
                        grid: { drawOnChartArea: false },
                        title: { display: false },
                        ticks: {
                            color: "#FCB316",
                            precision: 0,
                            stepSize: 10,
                            font: { family: "Montserrat", size: 9, weight: "600" },
                        },
                    },
                },
            },
        });
        salesChart._tooltipLabels = salesData.tooltip_labels || [];
    }

    const statusCanvas = document.getElementById("orderStatusChart");
    const statusRows = readJsonScript("orderStatusChartData", []);
    if (statusCanvas) {
        new Chart(statusCanvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: statusRows.map((row) => row.label),
                datasets: [{
                    data: statusRows.map((row) => Number(row.count || 0)),
                    backgroundColor: ["#FCB316", "#77759a", "#4c497d", "#1A1851", "#a4a8b6"],
                    borderColor: "#FFFFFF",
                    borderWidth: 2,
                    hoverOffset: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                cutout: "68%",
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

    const salesPeriodSelect = document.getElementById("salesPeriodSelect");
    if (salesPeriodSelect) {
        salesPeriodSelect.addEventListener("change", () => {
            salesPeriodSelect.disabled = true;
            const url = new URL(window.location.href);
            url.searchParams.set("grouping", salesPeriodSelect.value);
            url.searchParams.delete("sales_days");
            window.location.href = url.toString();
        });
    }
});
