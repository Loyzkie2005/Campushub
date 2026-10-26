/* Existing server-rendered monitoring data; no credentials or mutation requests. */
(function () {
    "use strict";
    const form = document.getElementById("monitorFilters");
    if (!form) return; // The server error state deliberately has no fake metrics.
    const read = id => JSON.parse(document.getElementById(id).textContent);
    const config = read("monitorConfig");
    const charts = read("monitorChartData");
    const users = new Map(read("monitorUsersData").map(user => [user.ref, user]));
    const activities = new Map(read("recentActivityData").map(event => [event.id, event]));
    const loginLabel = config.scoped ? "Marketplace Activities" : "Successful Logins";
    const period = document.getElementById("monitorPeriod");
    const search = form.querySelector('[name="q"]');
    let searchTimer;

    function showLoading() {
        document.querySelectorAll(".monitor-users-panel,.recent-activity-panel").forEach(panel => panel.setAttribute("aria-busy", "true"));
        document.getElementById("monitorLoadStatus").textContent = "Loading monitoring data...";
    }
    function submitFilters() {
        clearTimeout(searchTimer);
        showLoading();
        form.requestSubmit();
    }
    form.addEventListener("submit", showLoading);
    search.addEventListener("input", () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(submitFilters, 450);
    });
    period.addEventListener("change", () => {
        if (period.value === "custom") {
            form.querySelector('[name="date_from"]').focus();
            return;
        }
        submitFilters();
    });
    form.querySelectorAll('select,input[type="date"]').forEach(control => {
        control.addEventListener("change", () => {
            if (control.type === "date") {
                period.value = "custom";
                const start = form.querySelector('[name="date_from"]');
                const end = form.querySelector('[name="date_to"]');
                if (!start.value || !end.value) return;
            }
            submitFilters();
        });
    });

    const chartStates = [...document.querySelectorAll("[data-chart-state]")];
    const chartMessage = (node, message) => { node.replaceChildren(document.createTextNode(message)); };
    function chartFailure() {
        chartStates.forEach(node => {
            chartMessage(node, "Unable to load chart. ");
            const retry = document.createElement("button");
            retry.type = "button";
            retry.textContent = "Retry";
            retry.addEventListener("click", () => window.location.reload());
            node.append(retry);
        });
    }
    function trendOptions(data) {
        const highest = Math.max(0, ...data.success);
        const step = Math.max(1, Math.ceil(highest / 5));
        return {
            responsive: true, maintainAspectRatio: false,
            animation: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? false : { duration: 180 },
            plugins: { legend: { display: false }, tooltip: { callbacks: {
                title: items => items.length ? data.tooltipLabels[items[0].dataIndex] : "",
                label: item => `${item.parsed.y} ${config.scoped ? (item.parsed.y === 1 ? "activity" : "activities") : (item.parsed.y === 1 ? "successful login" : "successful logins")}`,
            } } },
            scales: {
                x: { grid: { display: false }, ticks: { maxTicksLimit: 10, color: "#1A1851" } },
                y: { beginAtZero: true, max: Math.max(5, Math.ceil(highest / step) * step),
                    title: { display: true, text: config.scoped ? "Number of Activities" : "Number of Successful Logins" },
                    ticks: { stepSize: step, precision: 0, color: "#1A1851" }, grid: { color: "rgba(26,24,81,.08)" } },
            },
        };
    }
    try {
        if (!window.Chart) throw new Error("Chart library unavailable");
        const initial = charts.daily;
        const trend = new Chart(document.getElementById("loginTrendChart"), {
            type: "line", data: { labels: initial.labels, datasets: [{
                label: loginLabel, data: initial.success, borderColor: "#1A1851",
                backgroundColor: "rgba(26,24,81,.04)", borderWidth: 2, tension: 0.25,
                fill: true, pointRadius: initial.success.some(Boolean) ? 2 : 0, pointHoverRadius: 4,
            }] }, options: trendOptions(initial),
        });
        function trendState(data) {
            chartMessage(chartStates[0], data.success.some(Boolean) ? "" : (config.scoped ? "No marketplace activities in selected period." : "No successful logins in selected period."));
        }
        trendState(initial);
        document.getElementById("trendPeriod").addEventListener("change", event => {
            const data = charts[event.target.value];
            trend.data.labels = data.labels;
            trend.data.datasets[0].data = data.success;
            trend.data.datasets[0].pointRadius = data.success.some(Boolean) ? 2 : 0;
            trend.options = trendOptions(data);
            trend.update();
            trendState(data);
        });
        const peak = charts.peakHours;
        new Chart(document.getElementById("peakLoginChart"), {
            type: "bar", data: { labels: peak.labels, datasets: [{ label: loginLabel,
                data: peak.values, backgroundColor: "#1A1851", maxBarThickness: 20, borderRadius: 2 }] },
            options: { ...trendOptions({ success: peak.values, tooltipLabels: peak.labels }),
                plugins: { legend: { display: false } } },
        });
        chartMessage(chartStates[1], peak.values.some(Boolean) ? "" : (config.scoped ? "No marketplace activities in selected period." : "No successful logins in selected period."));
    } catch (_error) { chartFailure(); }

    function empty(message) {
        const node = document.createElement("p");
        node.className = "drawer-empty";
        node.textContent = message;
        return node;
    }
    function details(target, pairs) {
        target.replaceChildren();
        pairs.forEach(([label, value]) => {
            const row = document.createElement("div");
            const term = document.createElement("dt");
            const description = document.createElement("dd");
            term.textContent = label;
            if (Array.isArray(value)) {
                value.filter(Boolean).forEach((line, index) => {
                    const node = document.createElement(index ? "small" : "span");
                    node.textContent = line;
                    description.append(node);
                });
            } else description.textContent = value || "\u2014";
            row.append(term, description);
            target.append(row);
        });
    }
    function renderEvents(target, events) {
        target.replaceChildren();
        if (!events.length) { target.append(empty("No recorded data.")); return; }
        events.forEach(event => {
            const item = document.createElement("article");
            const title = document.createElement("strong");
            const meta = document.createElement("small");
            title.textContent = event.activity;
            meta.textContent = [event.time, event.module, event.result, event.ip].filter(Boolean).join(" | ");
            item.append(title, meta);
            target.append(item);
        });
    }
    const drawer = document.getElementById("monitorDrawer");
    const drawerBackdrop = document.getElementById("monitorDrawerBackdrop");
    const modal = document.getElementById("activityDetailModal");
    const modalBackdrop = document.getElementById("activityDetailBackdrop");
    let focusReturn = null;
    function togglePanel(panel, backdrop, visible) {
        if (visible) focusReturn = document.activeElement;
        panel.hidden = backdrop.hidden = !visible;
        panel.classList.toggle("open", visible);
        backdrop.classList.toggle("open", visible);
        document.body.style.overflow = visible ? "hidden" : "";
        if (visible) panel.querySelector("button").focus();
        else if (focusReturn && focusReturn.isConnected) focusReturn.focus();
    }
    function tab(name) {
        drawer.querySelectorAll("[data-tab]").forEach(button => {
            const active = button.dataset.tab === name;
            button.classList.toggle("active", active);
            button.setAttribute("aria-selected", String(active));
        });
        drawer.querySelectorAll("[data-panel]").forEach(panel => panel.classList.toggle("active", panel.dataset.panel === name));
    }
    function openDrawer(user) {
        document.getElementById("drawerInitials").textContent = user.initials;
        document.getElementById("drawerUserName").textContent = user.fullName;
        document.getElementById("drawerUserEmail").textContent = user.email || user.username;
        const pairs = [["Username", user.username], ["Account Type", user.accountType], ["Role", user.role],
            ["Account Status", user.accountStatus], ["Online Status", user.status],
            ["Last Login", user.lastLogin], ["Last Seen", user.lastSeen],
            ["Last Activity", user.lastActivity], ["Last Activity Time", user.lastActivityAt]];
        if (!config.scoped) pairs.push(["IP Address", user.ip], ["Device / Browser", user.device]);
        if (user.presenceNote) pairs.push(["Presence Tracking", user.presenceNote]);
        details(document.getElementById("drawerOverview"), pairs);
        renderEvents(document.getElementById("drawerLogins"), user.logins);
        renderEvents(document.getElementById("drawerActivities"), user.events);
        const sessions = document.getElementById("drawerSessions");
        sessions.replaceChildren();
        if (!user.sessions.length) sessions.append(empty("No recorded sessions for this account."));
        user.sessions.forEach(session => {
            const item = document.createElement("article");
            const title = document.createElement("strong");
            const description = document.createElement("small");
            title.textContent = "Authenticated session";
            description.textContent = `Created ${session.created} | Last seen ${session.last_seen} | Expires ${session.expires}`;
            item.append(title, description);
            sessions.append(item);
        });
        sessions.append(empty(user.sessionNote));
        tab("overview");
        togglePanel(drawer, drawerBackdrop, true);
    }
    document.querySelectorAll(".js-monitor-view").forEach(button => button.addEventListener("click", () => openDrawer(users.get(button.dataset.accountRef))));
    drawer.querySelectorAll("[data-tab]").forEach(button => button.addEventListener("click", () => tab(button.dataset.tab)));
    const closeDrawer = () => togglePanel(drawer, drawerBackdrop, false);
    document.getElementById("drawerClose").addEventListener("click", closeDrawer);
    drawerBackdrop.addEventListener("click", closeDrawer);
    document.querySelectorAll(".js-activity-view").forEach(button => button.addEventListener("click", () => {
        const event = activities.get(button.dataset.activityId);
        const detail = event.detail;
        const pairs = [["Date & Time", event.time],
            ["Performed By", detail.performed_by.name]];
        if (detail.performed_by.role) pairs.push(["Role", detail.performed_by.role]);
        if (detail.affected_record) pairs.push([detail.affected_record.label, detail.affected_record.name]);
        pairs.push(["Action", detail.action], ["Module", detail.module]);
        if (detail.result) pairs.push(["Result", detail.result]);
        details(document.getElementById("activityDetailList"), pairs);
        const connection = detail.connection;
        document.getElementById("activityConnectionTitle").hidden = !connection;
        document.getElementById("activityConnectionList").hidden = !connection;
        const connectionPairs = [];
        if (connection) {
            if (connection.ip_address) connectionPairs.push(["IP Address", connection.ip_address]);
            connectionPairs.push(["Device", connection.device], ["Browser", connection.browser]);
        }
        details(document.getElementById("activityConnectionList"), connectionPairs);
        togglePanel(modal, modalBackdrop, true);
    }));
    const closeModal = () => togglePanel(modal, modalBackdrop, false);
    ["activityDetailClose", "activityDetailDone"].forEach(id => document.getElementById(id).addEventListener("click", closeModal));
    modalBackdrop.addEventListener("click", closeModal);
    document.addEventListener("keydown", event => {
        const activePanel = !modal.hidden ? modal : !drawer.hidden ? drawer : null;
        if (!activePanel) return;
        if (event.key === "Escape") { event.preventDefault(); activePanel === modal ? closeModal() : closeDrawer(); }
        if (event.key === "Tab") {
            const controls = [...activePanel.querySelectorAll("button,a[href],input,select,[tabindex='0']")]
                .filter(control => !control.hidden && control.getClientRects().length);
            const first = controls[0], last = controls[controls.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
        }
    });
    if (config.selectedAccount && users.has(config.selectedAccount)) {
        openDrawer(users.get(config.selectedAccount));
        tab("activity");
    }
})();
