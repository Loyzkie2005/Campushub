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
});
