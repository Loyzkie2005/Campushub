/* Run against a page exported by the isolated Django test, never a live database.
 * NODE_PATH (or CAMPUSHUB_PLAYWRIGHT_MODULE) supplies an existing Playwright install.
 * SCHEDULE_REVIEW_DIR contains facility.html and a local bootstrap.min.css copy.
 */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.CAMPUSHUB_PLAYWRIGHT_MODULE || 'playwright-core');
const root = path.resolve(__dirname, '../../..');
const out = path.resolve(process.env.SCHEDULE_REVIEW_DIR || '.');
let checks = 0;
const check = (condition, label) => { assert.ok(condition, label); checks++; };

(async () => {
    const browser = await chromium.launch({channel: 'chrome', headless: true});
    try {
        const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
        const errors = [], writes = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.route('**/*', async route => {
            const request = route.request(), url = new URL(request.url());
            if (request.method() !== 'GET') writes.push(url.pathname);
            if (url.pathname === '/review') return route.fulfill({contentType: 'text/html',
                body: fs.readFileSync(path.join(out, 'facility.html'), 'utf8')});
            if (url.hostname === 'cdn.jsdelivr.net' && url.pathname.endsWith('.css')) {
                return route.fulfill({path: path.join(out, 'bootstrap.min.css')});
            }
            if (url.pathname.startsWith('/static/')) {
                const relative = url.pathname.slice(8);
                const candidates = [path.join(root, 'backend/static', relative),
                    path.join(root, 'backend/core/modules/facilities/static', relative)];
                if (relative === 'facilities/js/facility_form_controls.js' && process.env.SCHEDULE_CONTROLS_SOURCE) {
                    candidates.unshift(path.resolve(process.env.SCHEDULE_CONTROLS_SOURCE));
                }
                const file = candidates.find(candidate => fs.existsSync(candidate) && fs.statSync(candidate).isFile());
                if (file) return route.fulfill({path: file});
            }
            const asset = /\.(js|css)$/.test(url.pathname);
            return route.fulfill({contentType: asset ? (url.pathname.endsWith('.js') ? 'text/javascript' : 'text/css') : 'application/json',
                body: asset ? '' : JSON.stringify({success: true, notifications: [], unread_count: 0})});
        });
        await page.goto('http://schedule.test/review');
        await page.locator('#addFacilityBtn').click();
        check(await page.locator('#facilityAllowedBookingDays, #facilityAllowedBookingDaysLabel, #facilityBookingPolicyNotice, [id^="facilityBookingDay-"]').count() === 0,
            'Removed booking-day section and checkboxes are absent');
        const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
        const hours = Object.fromEntries(days.map(day => [day, {open: '08:07', close: '16:53'}]));
        const checkbox = day => page.locator('#facilityDay-' + day);
        const preset = name => page.getByRole('button', {name, exact: true});
        const time = (day, kind) => page.getByLabel(`${day[0].toUpperCase() + day.slice(1)} ${kind} time`, {exact: true});
        const state = () => page.evaluate(() => structuredFacilityControls.getOperatingHours());
        const types = ['covered_court', 'function_hall', 'hostel', 'other'];

        // Real page reset/fill/view/edit functions, real shared/rental controllers.
        for (const type of types) {
            await page.evaluate(() => resetFacilityForm());
            await page.locator('#facilityType').selectOption(type);
            for (const mode of ['slot', 'room', 'daily', 'custom']) {
                await page.locator('#facilityBookingMode').selectOption(mode);
                for (const [name, activeDays] of [['Weekdays', days.slice(0, 5)], ['Weekends', days.slice(5)], ['Daily', days]]) {
                    await preset(name).click();
                    const actual = await state();
                    check(days.every(day => Boolean(actual[day]) === activeDays.includes(day)), `${type}/${mode}/${name} days`);
                    check(await time(activeDays[0], 'opening').isEnabled(), `${type}/${mode}/${name} editable`);
                }
                await preset('Custom').click();
                await time('monday', 'opening').selectOption('09:15');
                await time('tuesday', 'closing').selectOption('16:45');
                await checkbox('wednesday').uncheck();
                let actual = await state();
                check(actual.monday.open === '09:15' && actual.tuesday.close === '16:45' && actual.wednesday === null,
                    `${type}/${mode} independent Custom days`);
                await checkbox('wednesday').check();
                check(await time('wednesday', 'closing').isEnabled(), `${type}/${mode} reopen day`);
                await checkbox('monday').uncheck();
                check((await state()).monday === null, `${type}/${mode} operating day can close`);
                await checkbox('monday').check();
                check(!await page.evaluate(() => Object.prototype.hasOwnProperty.call(structuredFacilityControls.getFeatureWorkflow(), 'allowed_booking_days')),
                    `${type}/${mode} form does not overwrite saved client policy`);
                await page.evaluate(({type, mode, hours}) => {
                    const row = document.querySelector('#facilityTable tbody tr[data-facility-id]');
                    renderFacilityRow(row, {id: 'ISOLATED-SCHEDULE', name: 'Isolated schedule fixture',
                        facilityType: type, mode, status: 'available', location: 'Test only', capacity: 50,
                        rate: '500', priceType: 'hour', amenities: [], workflowConfig: {operating_hours: hours},
                        customFacilityType: type === 'other' ? 'Test space' : '', images: []});
                    window.scheduleTestRow = row;
                    openViewFacilityForm(row);
                }, {type, mode, hours});
                check(await checkbox('monday').isDisabled() && await time('monday', 'opening').isDisabled()
                    && await preset('Daily').isDisabled(), `${type}/${mode} View locks controls`);
                await page.evaluate(() => openEditFacilityForm(scheduleTestRow));
                check(await checkbox('monday').isEnabled() && await time('monday', 'opening').isEnabled()
                    && await preset('Custom').isEnabled(), `${type}/${mode} View -> Edit unlocks`);
                actual = await state();
                check(JSON.stringify(actual) === JSON.stringify(hours), `${type}/${mode} saved exact minutes reload`);
            }
        }

        // Saved policies belong to the loaded facility, never to the previous row.
        await page.evaluate(({days, hours}) => {
            const workflow = {weekend_only: true, operating_hours: Object.fromEntries(days.map(day =>
                [day, ['saturday', 'sunday'].includes(day) ? hours[day] : null]))};
            scheduleTestRow.dataset.facilityType = 'covered_court';
            scheduleTestRow.dataset.bookingMode = 'slot';
            scheduleTestRow.dataset.workflowConfig = JSON.stringify(workflow);
            openViewFacilityForm(scheduleTestRow);
            openEditFacilityForm(scheduleTestRow);
        }, {days, hours});
        check(await preset('Weekdays').isEnabled() && await preset('Daily').isEnabled(), 'Court campus operating presets editable');
        for (const day of days.slice(0, 5)) check(await checkbox(day).isEnabled() && !await checkbox(day).isChecked(), `Court ${day} legacy operating values preserved`);
        await preset('Daily').click();
        check(await checkbox('monday').isChecked() && await page.evaluate(() => !Object.prototype.hasOwnProperty.call(structuredFacilityControls.getFeatureWorkflow(), 'weekend_only')), 'Court operating weekdays do not submit a hidden weekend restriction');
        check(!await page.evaluate(() => Object.prototype.hasOwnProperty.call(structuredFacilityControls.getFeatureWorkflow(), 'allowed_booking_days')), 'Court form leaves saved booking-day restrictions untouched');
        check(await time('saturday', 'opening').isEnabled() && await time('sunday', 'closing').isEnabled(), 'Court permitted weekend times editable');
        await preset('Custom').click();
        await time('saturday', 'opening').selectOption('09:15');
        check((await state()).saturday.open === '09:15', 'Court Custom weekend times retained');
        await page.screenshot({path: path.join(out, 'court-policy.png'), fullPage: true});
        // A category change must not turn a different category into a Court.
        // The original controller retained weekendOnly here, disabling weekdays.
        await page.locator('#facilityType').selectOption('function_hall');
        check(await checkbox('monday').isEnabled() && await preset('Daily').isEnabled(),
            'Changing category does not carry Court-only locks into Hall draft');
        await page.locator('#facilityType').selectOption('covered_court');
        check(await page.evaluate(() => !Object.prototype.hasOwnProperty.call(structuredFacilityControls.getFeatureWorkflow(), 'weekend_only')) && await preset('Daily').isEnabled(),
            'Returning to Court retains enabled operating controls without a hidden policy');
        for (const type of types.slice(1)) {
            await page.evaluate(({type, hours}) => {
                scheduleTestRow.dataset.facilityType = type;
                scheduleTestRow.dataset.workflowConfig = JSON.stringify({operating_hours: hours});
                openViewFacilityForm(scheduleTestRow);
                openEditFacilityForm(scheduleTestRow);
            }, {type, hours});
            check(await checkbox('monday').isEnabled() && await preset('Daily').isEnabled(), `${type} does not inherit Court policy`);
        }
        await page.evaluate(({days, hours}) => {
            scheduleTestRow.dataset.facilityType = 'function_hall';
            scheduleTestRow.dataset.workflowConfig = JSON.stringify({weekend_only: true,
                operating_hours: Object.fromEntries(days.map(day => [day,
                    ['saturday', 'sunday'].includes(day) ? hours[day] : null]))});
            openEditFacilityForm(scheduleTestRow);
        }, {days, hours});
        await page.locator('#facilityType').selectOption('hostel');
        check(await preset('Daily').isEnabled(), 'Hall policy does not leak into Hostel draft');
        await page.locator('#facilityType').selectOption('function_hall');
        check(await page.evaluate(() => !Object.prototype.hasOwnProperty.call(structuredFacilityControls.getFeatureWorkflow(), 'weekend_only')) && await preset('Daily').isEnabled(), 'Returning to Hall keeps operating controls without a hidden policy');
        await page.evaluate(() => openViewFacilityForm(scheduleTestRow));
        await page.evaluate(() => resetFacilityForm());
        await page.locator('#facilityType').selectOption('function_hall');
        check(await preset('Daily').isEnabled() && await checkbox('monday').isEnabled(), 'View -> Add resets read-only and policy');
        await page.evaluate(() => structuredFacilityControls.setWorkflow({operating_hours: 'Ask the office'}));
        check(await page.evaluate(() => structuredFacilityControls.getOperatingHours() === 'Ask the office'
            && !Object.prototype.hasOwnProperty.call(structuredFacilityControls.getFeatureWorkflow(), 'allowed_booking_days')), 'Unchanged legacy text does not seed booking days');
        await page.evaluate(() => structuredFacilityControls.setWorkflow({}));
        check(await page.evaluate(() => structuredFacilityControls.getOperatingHours() === undefined
            && !Object.prototype.hasOwnProperty.call(structuredFacilityControls.getFeatureWorkflow(), 'allowed_booking_days')), 'Legacy slots-only record preserves absent operating/booking settings');
        for (const type of ['food_analysis', 'training_kitchen', 'lease_space']) {
            await page.evaluate(() => resetFacilityForm());
            // Existing service workflows are not converted to weekly rentals.
            await page.evaluate(type => { facilityFields.type.add(new Option(type, type)); }, type);
            await page.locator('#facilityType').selectOption(type);
            check(await page.locator('[data-facility-field="operating_hours"]').isHidden(), `${type} weekly schedule stays inapplicable`);
        }
        check(errors.length === 0, 'No page errors: ' + errors.join('; '));
        check(writes.length === 0, 'No HTTP mutations: ' + writes.join('; '));
        const result = {checks, types, modes: ['slot', 'room', 'daily', 'custom'], errors, writes};
        fs.writeFileSync(path.join(out, 'browser-results.json'), JSON.stringify(result, null, 2));
        console.log(JSON.stringify(result));
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
