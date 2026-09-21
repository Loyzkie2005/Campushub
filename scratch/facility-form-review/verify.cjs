// Run with: node scratch/facility-form-review/verify.cjs <path-to-playwright>
const {chromium} = require(process.argv[2] || 'playwright');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const render = spawnSync(path.join(root, 'backend/core/venv/Scripts/python.exe'), [path.join(__dirname, 'render.py')]);
if (render.status !== 0) throw new Error(render.stderr.toString());

(async () => {
    const browser = await chromium.launch({headless: true});
    try {
        const page = await browser.newPage({viewport: {width: 1440, height: 1050}});
        const errors = [];
        const saves = [];
        page.on('pageerror', (error) => errors.push(error.message));
        await page.route('http://facility.test/**', async (route) => {
            const url = new URL(route.request().url());
            if (url.pathname === '/') return route.fulfill({contentType: 'text/html', body: render.stdout});
            if (url.pathname.startsWith('/static/')) {
                const relative = decodeURIComponent(url.pathname.slice('/static/'.length));
                const roots = [path.join(root, 'backend/static'), path.join(root, 'backend/core/modules/facilities/static')];
                for (const base of roots) {
                    const file = path.resolve(base, relative);
                    if (file.startsWith(base + path.sep) && fs.existsSync(file)) return route.fulfill({path: file});
                }
                return route.fulfill({status: 404, body: ''});
            }
            if (url.pathname === '/api/facilities/create/') {
                saves.push(route.request().postDataJSON());
                return route.fulfill({status: 400, contentType: 'application/json', body: JSON.stringify({error: 'Isolated browser test: no data saved.'})});
            }
            return route.fulfill({contentType: 'application/json', body: '{}'});
        });
        await page.goto('http://facility.test/', {waitUntil: 'networkidle'});
        await page.locator('#addFacilityBtn').click();
        await page.locator('#facilityName').fill('Test Form Court');
        await page.locator('#facilityLocation').fill('Test Campus');
        await page.locator('#facilityCapacity').fill('50');
        await page.locator('#facilityRate').fill('500');
        assert.equal(await page.locator('.facility-hours-row').count(), 7);
        await page.getByLabel('Lighting', {exact: true}).check();
        await page.locator('#facilityOtherAmenity').check();
        await page.locator('#saveFacilityButton').click();
        assert.equal(saves.length, 0, 'Other must require a description');
        await page.locator('#facilityOtherAmenityText').fill('Custom | equipment');
        for (const day of ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']) {
            await page.locator(`#facilityDay-${day}`).check();
            const title = day[0].toUpperCase() + day.slice(1);
            await page.getByRole('combobox', {name: `${title} opening time`, exact: true}).selectOption('08:00');
            await page.getByRole('combobox', {name: `${title} closing time`, exact: true}).selectOption('17:00');
        }
        await page.locator('#facilityMinimumBookingDuration').selectOption('0.5');
        const mondayClose = page.getByRole('combobox', {name: 'Monday closing time', exact: true});
        await mondayClose.selectOption('07:00');
        await page.locator('#saveFacilityButton').click();
        assert.equal(saves.length, 0, 'Invalid hours must not submit');
        await mondayClose.selectOption('17:00');
        const saved = page.waitForResponse('http://facility.test/api/facilities/create/');
        await page.locator('#saveFacilityButton').click();
        await saved;
        assert.equal(saves.length, 1);
        assert.deepEqual(saves[0].amenities, ['Lighting', 'Custom | equipment']);
        assert.equal(saves[0].workflow_config.operating_hours.saturday, null);
        assert.deepEqual(saves[0].workflow_config.operating_hours.monday, {open: '08:00', close: '17:00'});
        assert.equal(saves[0].workflow_config.minimum_booking_duration, '0.5');
        await page.locator('[data-facility-field="operating_hours"]').scrollIntoViewIfNeeded();
        await page.screenshot({path: path.join(__dirname, 'desktop.png')});
        await page.setViewportSize({width: 390, height: 844});
        await page.locator('[data-facility-field="operating_hours"]').scrollIntoViewIfNeeded();
        await page.screenshot({path: path.join(__dirname, 'mobile.png')});
        const overflow = await page.locator('.facility-hours-times:visible').evaluateAll((rows) => rows.some((row) => row.scrollWidth > row.clientWidth));
        assert.equal(overflow, false, 'Time controls must not overflow');
        await page.setViewportSize({width: 1440, height: 1050});
        await page.locator('#backToFacilitiesButton').click();
        await page.locator('[data-facility-row-action="view"]').first().click();
        assert.equal(await page.locator('#facilityMinimumBookingDuration').isVisible(), false, 'Preset slots hide minimum');
        assert.equal(await page.locator('#facilityDay-monday').isChecked(), true);
        assert.equal(await page.locator('#facilityDay-saturday').isChecked(), false);
        assert.equal(await page.getByLabel('Custom | equipment', {exact: true}).isChecked(), true);
        assert.equal(await page.locator('#facilityDay-monday').isDisabled(), true);
        await page.locator('#backToFacilitiesButton').click();
        // Open the same record for editing; no save is sent to any real API.
        await page.locator('[data-facility-id="TEST-FORM"] [data-bs-toggle="dropdown"]').click();
        await page.locator('[data-facility-id="TEST-FORM"] [data-facility-row-action="edit"]').click();
        assert.equal(await page.locator('#facilityDay-monday').isDisabled(), false);
        assert.equal(await page.locator('#facilityMinimumBookingDuration').isVisible(), false);
        assert.equal(await page.getByRole('combobox', {name: 'Monday opening time', exact: true}).inputValue(), '08:00');
        assert.equal(await page.getByLabel('Custom | equipment', {exact: true}).isChecked(), true);
        await page.locator('#backToFacilitiesButton').click();
        await page.locator('#addFacilityBtn').click();
        await page.locator('#facilityType').selectOption('food_analysis');
        assert.equal(await page.getByLabel('Protein Analysis', {exact: true}).count(), 1);
        assert.equal(await page.locator('#facilityOperatingHours').isVisible(), false);
        assert.equal(await page.locator('#facilityMinimumBookingDuration').isVisible(), false);
        await page.locator('#facilityType').selectOption('covered_court');
        assert.equal(await page.locator('#facilityMinimumBookingDuration').isVisible(), true);
        assert.deepEqual(errors, [], 'No browser runtime errors');
        console.log('PASS: structured payload, invalid hours, custom amenities, closed days, view round-trip, preset slots, type changes, desktop/mobile layout.');
    } finally {
        await browser.close();
    }
})().catch((error) => {console.error(error); process.exitCode = 1;});
