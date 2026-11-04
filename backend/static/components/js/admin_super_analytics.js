// Enhancements are loaded only by the authorized Super Admin Analytics templates.
document.addEventListener('DOMContentLoaded', () => {
    if (!document.body.classList.contains('super-admin-analytics')) return;
    // Hidden custom inputs must not override an explicitly selected preset.
    const period = document.getElementById('analyticsPeriod');
    const syncDates = () => document.querySelectorAll('#analyticsCustomDates input').forEach(input => {
        input.disabled = period?.value !== 'custom';
    });
    period?.addEventListener('change', syncDates);
    syncDates();
    const navigation = document.querySelector('.analytics-module-nav');
    const activeTab = navigation?.querySelector('[aria-current="page"]');
    const revealActiveTab = () => {
        if (!activeTab) return;
        const navBox = navigation.getBoundingClientRect(), tabBox = activeTab.getBoundingClientRect();
        if (tabBox.left < navBox.left) navigation.scrollLeft -= navBox.left - tabBox.left;
        else if (tabBox.right > navBox.right) navigation.scrollLeft += tabBox.right - navBox.right;
    };
    revealActiveTab();
    document.fonts?.ready.then(revealActiveTab);
    window.addEventListener('resize', revealActiveTab, {passive: true});
    document.fonts?.ready.then(() => {
        if (typeof Chart === 'undefined') return;
        document.querySelectorAll('.super-analytics-content canvas').forEach(canvas => {
            const chart = Chart.getChart(canvas);
            if (chart) { chart.resize(); chart.update('none'); }
        });
    });
    document.querySelectorAll('.analytics-table').forEach(table => {
        const rows = Array.from(table.tBodies[0]?.rows || []);
        // Accessible chart tables retain chronological order. Bounded existing rankings
        // may be re-sorted locally; no extra records or permissions are requested.
        if (table.closest('.analytics-chart-data') || rows.length < 2 || rows.some(row => row.cells[0]?.colSpan > 1)) return;
        table.querySelectorAll('thead th').forEach((heading, column) => {
            heading.scope = 'col';
            const button = document.createElement('button');
            button.type = 'button'; button.className = 'analytics-sort';
            button.textContent = heading.textContent.trim();
            button.setAttribute('aria-label', 'Sort by ' + button.textContent);
            heading.replaceChildren(button);
            button.addEventListener('click', () => {
                const descending = heading.getAttribute('aria-sort') !== 'descending';
                table.querySelectorAll('thead th').forEach(th => th.removeAttribute('aria-sort'));
                heading.setAttribute('aria-sort', descending ? 'descending' : 'ascending');
                const numeric = heading.classList.contains('number-cell');
                const value = row => row.cells[column]?.textContent.trim() || '';
                const ordered = rows.map((row, index) => ({row, index})).sort((a, b) => {
                    const left = value(a.row), right = value(b.row);
                    const result = numeric ? Number(left.replace(/[^\d.-]/g, '')) - Number(right.replace(/[^\d.-]/g, ''))
                        : left.localeCompare(right, 'en-PH', {numeric: true, sensitivity: 'base'});
                    return (descending ? -result : result) || a.index - b.index;
                });
                table.tBodies[0].replaceChildren(...ordered.map(item => item.row));
            });
        });
    });
    const sections = document.querySelector('.super-analytics-sections');
    if (!sections) return;
    if (typeof Chart === 'undefined') {
        sections.querySelectorAll('.analytics-chart, .analytics-donut').forEach(wrap => {
            wrap.hidden = true;
            const note = document.createElement('p'); note.className = 'marketplace-chart-fallback';
            note.textContent = 'Chart unavailable. Recorded values remain in the accompanying tables and summaries.';
            wrap.before(note);
        });
        return;
    }
    Chart.defaults.font.family = 'Montserrat, sans-serif';
    for (const [id, source, type, horizontal] of [
        ['facilityDemandChart', 'facilityDemandChartData', 'line', false],
        ['serviceRequestTrendChart', 'serviceRequestTrendChartData', 'line', false],
        ['serviceRequestDistributionChart', 'serviceRequestDistributionChartData', 'bar', true],
        ['serviceWeekdayChart', 'serviceWeekdayChartData', 'bar', false],
        ['userAccountTypeChart', 'userAccountTypeChartData', 'doughnut', false],
    ]) {
        const canvas = document.getElementById(id);
        if (!canvas) continue;
        const data = JSON.parse(document.getElementById(source).textContent);
        const donut = type === 'doughnut';
        new Chart(canvas, {type, data: {labels: data.labels, datasets: [{label: 'Recorded count', data: data.values,
            borderColor: donut ? '#FFFFFF' : '#1A1851', borderWidth: 2,
            backgroundColor: donut ? ['#1A1851', '#FCB316', '#667085', '#B6B9C7', '#E8EAF0'] : '#1A1851',
            pointRadius: 2, tension: 0.15, fill: false, maxBarThickness: 32}]},
            options: {responsive: true, maintainAspectRatio: false, animation: false,
                layout: {padding: {left: horizontal ? 8 : 0}},
                ...(donut ? {cutout: '65%'} : {indexAxis: horizontal ? 'y' : 'x', scales: {
                    [horizontal ? 'x' : 'y']: {beginAtZero: true, ticks: {precision: 0}, grid: {color: '#E8EAF0'}},
                    [horizontal ? 'y' : 'x']: {grid: {display: false}, ...(horizontal ? {ticks: {callback(value) {
                        const text = String(this.getLabelForValue(value));
                        return (text.match(/.{1,14}(?:\s|$)|.{1,14}/g) || [text]).map(line => line.trim());
                    }}} : {})}}}),
                plugins: {legend: {display: false}}}});
    }
    sections.querySelectorAll('canvas').forEach(canvas => Chart.getChart(canvas)?.update('none'));
});
