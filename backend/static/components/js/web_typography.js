/* Chart canvases do not inherit CSS fonts. Existing explicit fonts use the same face. */
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = 'Inter, sans-serif';
    Chart.defaults.font.size = 12;
    document.fonts?.ready.then(() => {
        for (const chart of Object.values(Chart.instances)) chart.update('none');
    });
}
