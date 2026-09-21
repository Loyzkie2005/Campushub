const { chromium } = require('C:/Users/leste/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const mime = { '.css': 'text/css', '.js': 'application/javascript', '.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const failures = [];
    try {
        for (const [name, width, height] of [['desktop', 1440, 1080], ['mobile', 390, 844], ['wide', 1920, 1080]]) {
            for (const state of ['populated', 'empty', 'marketplace-populated', 'marketplace-empty']) {
                const page = await context.newPage();
                await page.setViewportSize({ width, height });
                const errors = [];
                page.on('pageerror', (error) => errors.push(error.message));
                await page.route('http://dashboard.test/**', async (route) => {
                    const url = new URL(route.request().url());
                    if (url.pathname.startsWith('/static/')) {
                        const relative = decodeURIComponent(url.pathname.slice(8));
                        for (const directory of ['backend/static', 'backend/core/modules/marketplace/static', 'backend/core/modules/facilities/static']) {
                            const base = path.resolve(root, directory);
                            const file = path.resolve(base, relative);
                            if (file.startsWith(base + path.sep) && fs.existsSync(file) && fs.statSync(file).isFile()) {
                                return route.fulfill({ body: fs.readFileSync(file), contentType: mime[path.extname(file)] || 'application/octet-stream' });
                            }
                        }
                        return route.fulfill({ status: 404, body: '' });
                    }
                    if (url.pathname === '/admin-dashboard/') {
                        return route.fulfill({ body: fs.readFileSync(path.join(__dirname, `${state}.html`)), contentType: 'text/html' });
                    }
                    return route.fulfill({ body: '{}', contentType: 'application/json' });
                });
                await page.goto('http://dashboard.test/admin-dashboard/?facility_days=14', { waitUntil: 'networkidle' });
                await page.waitForFunction(() => window.Chart && Chart.getChart('salesOverviewChart'));
                const card = page.locator('#sales-overview-card');
                await card.scrollIntoViewIfNeeded();
                const checks = await page.evaluate(() => {
                    const section = document.querySelector('#sales-overview-card');
                    const chart = Chart.getChart('salesOverviewChart');
                    const bounds = section.getBoundingClientRect();
                    const panels = [...document.querySelector('.marketplace-overview-row').children].map((node) => {
                        const r = node.getBoundingClientRect();
                        return { top: r.top, left: r.left, right: r.right, width: r.width };
                    });
                    const overflowing = [...section.querySelectorAll('h2, h3, p, strong, select, a, canvas')]
                        .filter((node) => { const r = node.getBoundingClientRect(); return r.width && (r.right > bounds.right + 1 || r.left < bounds.left - 1); })
                        .map((node) => node.outerHTML.slice(0, 140));
                    const chartCanvas = chart.canvas;
                    const pixels = chartCanvas.getContext('2d').getImageData(0, 0, chartCanvas.width, chartCanvas.height).data;
                    let navyPixels = 0;
                    let goldPixels = 0;
                    for (let i = 0; i < pixels.length; i += 4) {
                        if (pixels[i + 3] > 200 && pixels[i] < 50 && pixels[i + 1] < 50 && pixels[i + 2] > 50) navyPixels++;
                        if (pixels[i + 3] > 200 && pixels[i] > 240 && pixels[i + 1] > 150 && pixels[i + 1] < 200 && pixels[i + 2] < 50) goldPixels++;
                    }
                    const tooltip = chart.options.plugins.tooltip.callbacks;
                    return {
                        types: chart.data.datasets.map((dataset) => dataset.type),
                        panels,
                        statusChart: Boolean(Chart.getChart('orderStatusChart')),
                        labels: chart.data.datasets.map((dataset) => dataset.label),
                        orders: chart.scales.yOrders.ticks.map((tick) => tick.value),
                        salesTicks: chart.scales.ySales.ticks.map((tick) => tick.label),
                        periodCount: chart.data.labels.length, overflowing, navyPixels, goldPixels,
                        width: bounds.width,
                        parentWidth: section.parentElement.clientWidth - parseFloat(getComputedStyle(section.parentElement).paddingLeft) - parseFloat(getComputedStyle(section.parentElement).paddingRight),
                        font: getComputedStyle(section.querySelector('h2')).fontFamily,
                        singular: tooltip.label({ dataset: { yAxisID: 'yOrders' }, parsed: { y: 1 } }),
                        plural: tooltip.label({ dataset: { yAxisID: 'yOrders' }, parsed: { y: 2 } }),
                        pesos: tooltip.label({ dataset: { yAxisID: 'ySales' }, parsed: { y: 300 } }),
                        totals: chart.data.datasets.map((dataset) => dataset.data.reduce((sum, value) => sum + value, 0)),
                        legendRows: [...section.querySelectorAll('.sales-overview__legend > span')].map((el) => el.getBoundingClientRect().top),
                    };
                });
                try {
                assert.deepEqual(checks.types, ['line', 'bar']);
                assert.deepEqual(checks.labels, ['Sales (\u20b1)', 'Orders']);
                assert(checks.orders.every(Number.isInteger));
                assert(checks.salesTicks.every((value) => value.startsWith('\u20b1')));
                assert.equal(checks.periodCount, 30);
                assert.deepEqual(checks.overflowing, []);
                assert(Math.abs(checks.width - checks.parentWidth) < 2);
                assert(checks.navyPixels > 30);
                assert(checks.font.includes('Montserrat'));
                assert.equal(checks.singular, '1 order');
                assert.equal(checks.plural, '2 orders');
                assert(checks.pesos.includes('300.00'));
                assert.equal(checks.legendRows[0], checks.legendRows[1]);
                assert.deepEqual(checks.totals, state.endsWith('empty') ? [0, 0] : state.startsWith('marketplace') ? [300, 1] : [400, 2]);
                if (state.endsWith('populated')) assert(checks.goldPixels > 50);
                if (width >= 1200) {
                    assert.equal(checks.panels[0].top, checks.panels[1].top);
                    assert.equal(checks.panels[1].top, checks.panels[2].top);
                    assert(checks.panels[0].right < checks.panels[1].left);
                    assert(checks.panels[1].right < checks.panels[2].left);
                } else if (width <= 700) {
                    assert(checks.panels[0].top < checks.panels[1].top);
                    assert(checks.panels[1].top < checks.panels[2].top);
                }
                if (state.startsWith('marketplace')) assert(checks.statusChart, 'Order Status must still render');
                assert.deepEqual(errors, []);
                } catch (error) { failures.push(`${name}/${state}: ${error.message}; browser errors: ${errors.join(', ')}`); }
                await page.locator('.marketplace-overview-row').screenshot({ path: path.join(__dirname, `${state}-${name}.png`) });
                console.log(`${name}/${state}: ${JSON.stringify(checks)}`);
                // Request parameters are verified here; actual regrouping is covered by Django tests.
                await page.locator('[aria-label="Sales grouping"]').selectOption('weekly');
                await page.waitForURL(/grouping=weekly/);
                assert.equal(new URL(page.url()).searchParams.get('sales_days'), '30');
                assert.equal(new URL(page.url()).searchParams.get('facility_days'), '14');
                await page.locator('[aria-label="Sales period"]').selectOption('7');
                await page.waitForURL(/sales_days=7/);
                assert.equal(new URL(page.url()).searchParams.get('facility_days'), '14');
                await page.close();
            }
        }
        assert.deepEqual(failures, []);
    } finally {
        await browser.close();
    }
})().catch((error) => { console.error(error); process.exitCode = 1; });
