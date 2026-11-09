// Only called by the opt-in disposable live-server test; no existing sessions.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {chromium} = require(process.env.CAMPUSHUB_PLAYWRIGHT_MODULE);
const base = process.env.SCHEDULE_LIVE_URL, out = process.env.SCHEDULE_LIVE_OUT;
assert(/^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(base), 'Local test server only');
let checks = 0;
const check = (value, message) => { assert.ok(value, message); checks++; };
(async () => {
    const browser = await chromium.launch({channel: 'chrome', headless: true});
    const errors = [], roles = [];
    try {
        for (const role of ['super', 'facilities', 'market']) {
            const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
            const page = await context.newPage();
            page.setDefaultTimeout(10000);
            page.on('pageerror', error => errors.push({role, message: error.message}));
            const initial = await page.goto(base + '/');
            check(initial.status() === 200, 'Login page HTTP ' + initial.status() + ' / ' + await page.title());
            await page.locator('#username').fill('schedule-' + role);
            await page.locator('#password').fill(process.env.SCHEDULE_TEST_PASSWORD);
            const login = page.waitForResponse(response => response.request().method() === 'POST' && response.url().includes('login'));
            await page.getByRole('button', {name: 'Login', exact: true}).click();
            const response = await login;
            check(response.ok(), role + ' normal login');
            await page.waitForURL(url => url.pathname.startsWith('/admin'));
            const auth = {tab_token: await page.evaluate(() => sessionStorage.getItem('campushub_admin_tab_token'))};
            check(Boolean(auth.tab_token), role + ' normal tab session');
            // Same authenticated token produced by normal login, never a forged role.
            const loadedController = role === 'market' ? null : page.waitForResponse(r => r.url().includes('/facilities/js/facility_form_controls.js'));
            await page.goto(base + '/admin-facility/?__at=' + encodeURIComponent(auth.tab_token));
            let assetHash = null;
            if (loadedController) {
                const asset = await loadedController;
                assetHash = createHash('sha256').update(await asset.body()).digest('hex');
                const localHash = createHash('sha256').update(fs.readFileSync(path.join(__dirname,
                    '../modules/facilities/static/facilities/js/facility_form_controls.js'))).digest('hex');
                check(assetHash === localHash, role + ' actual browser asset response matches disk');
            }
            if (role === 'market') {
                check(await page.locator('#addFacilityBtn').count() === 0, 'Marketplace has no Add');
                check(await page.locator('[data-facility-row-action="edit"]').count() === 0, 'Marketplace has no Edit');
                const denied = await context.request.post(base + '/api/facilities/BROWSER-HALL/update/', {
                    headers: {'X-Admin-Tab-Token': auth.tab_token}, data: {description: 'Must be denied'},
                    maxRedirects: 0,
                });
                check([302, 403].includes(denied.status()), 'Marketplace write remains denied');
                roles.push({role, checks: 'login/read/write restriction'});
                await context.close(); continue;
            }
            await page.locator('#addFacilityBtn').click();
            check(await page.locator('#facilityAllowedBookingDays, #facilityAllowedBookingDaysLabel, #facilityBookingPolicyNotice, [id^="facilityBookingDay-"]').count() === 0,
                role + ' removed booking-day section absent in Add');
            await page.locator('#facilityType').selectOption('function_hall');
            for (const preset of ['Weekdays', 'Weekends', 'Daily', 'Custom']) {
                await page.getByRole('button', {name: preset, exact: true}).click();
                check(await page.getByRole('button', {name: preset, exact: true}).getAttribute('aria-pressed') === 'true', role + ' preset ' + preset);
            }
            const monday = page.locator('#facilityDay-monday');
            for (const day of ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']) {
                const checkbox = page.locator('#facilityDay-' + day);
                await checkbox.click(); check(!await checkbox.isChecked(), role + ' ' + day + ' closes by click');
                await checkbox.click(); check(await checkbox.isChecked(), role + ' ' + day + ' opens by click');
            }
            const opening = page.getByLabel('Monday opening time', {exact: true});
            await opening.click(); await opening.press('ArrowDown'); await opening.press('Enter');
            check(await opening.inputValue() !== '08:00', role + ' native Monday time dropdown responds');
            check(await monday.isChecked(), role + ' Monday dropdown does not toggle day checkbox');
            await page.locator('#facilityName').fill('Browser Added ' + role);
            await page.locator('#facilityLocation').fill('Disposable database');
            await page.locator('#facilityPriceType').selectOption('hour');
            await page.locator('#facilityRate').fill('500');
            const createdResponse = page.waitForResponse(r => r.url().includes('/api/facilities/create/') && r.request().method() === 'POST');
            await page.locator('#saveFacilityButton').click();
            const created = await createdResponse;
            check(created.status() === 201, role + ' Add saves');
            const added = (await created.json()).facility;
            check(!Object.prototype.hasOwnProperty.call(added.workflow_config, 'allowed_booking_days'), role + ' Add does not create an invisible booking-day setting');
            const addedHours = added.workflow_config.operating_hours;
            await page.reload();
            async function edit(id) {
                const row = page.locator(`tr[data-facility-id="${id}"]`);
                await row.locator('[data-bs-toggle="dropdown"]').click();
                await row.locator('[data-facility-row-action="edit"]').click();
            }
            await edit(added.id);
            check(await opening.inputValue() === addedHours.monday.open, role + ' Add reload persists');
            await page.locator('#backToFacilitiesButton').click();
            const court = page.locator('tr[data-facility-id="BROWSER-COURT"]');
            await court.locator('[data-facility-row-action="view"]').click();
            check(await page.locator('#facilityDay-saturday').isDisabled(), role + ' View read only');
            await page.locator('#backToFacilitiesButton').click();
            await edit('BROWSER-COURT');
            check(await page.locator('#facilityDay-monday').isEnabled(), role + ' Court campus operating weekday editable');
            check(await page.getByRole('button', {name: 'Weekdays', exact: true}).isEnabled()
                && await page.getByRole('button', {name: 'Daily', exact: true}).isEnabled(), role + ' Court operating presets editable');
            await page.getByRole('button', {name: 'Weekdays', exact: true}).click();
            check(await monday.isChecked() && await page.locator('#facilityAllowedBookingDays').count() === 0,
                role + ' operating weekdays editable with booking-day section absent in Edit');
            const courtSave = page.waitForResponse(r => r.url().includes('/BROWSER-COURT/update/') && r.request().method() === 'POST');
            await page.locator('#saveFacilityButton').click();
            const courtResponse = await courtSave;
            check(courtResponse.ok(), role + ' Court enabled weekdays save');
            const courtWorkflow = (await courtResponse.json()).facility.workflow_config;
            check(!Object.prototype.hasOwnProperty.call(courtWorkflow, 'weekend_only')
                && !Object.prototype.hasOwnProperty.call(courtWorkflow, 'allowed_booking_days'),
                role + ' Court save removes retired hidden day policies');
            await page.reload(); await edit('BROWSER-COURT');
            check(await monday.isChecked() && await page.locator('#facilityAllowedBookingDays').count() === 0, role + ' Court operating hours reload without removed section');
            for (const [weekday, expected] of [[1, true], [6, false], [0, false]]) {
                const next = new Date();
                next.setDate(next.getDate() + ((weekday - next.getDay() + 7) % 7 || 7));
                const date = `${next.getFullYear()}-${String(next.getMonth()+1).padStart(2,'0')}-${String(next.getDate()).padStart(2,'0')}`;
                const result = await context.request.get(base + `/api/mobile/facilities/BROWSER-COURT/availability/?date=${date}`);
                const availability = await result.json();
                check(result.ok() && Boolean(availability.available_slots.length) === expected,
                    role + ' Court enabled operating day reaches mobile weekday ' + weekday);
            }
            await page.getByRole('button', {name: 'Custom', exact: true}).click();
            for (const day of ['Saturday', 'Sunday']) {
                await page.locator('#facilityDay-' + day.toLowerCase()).check();
                for (const kind of ['opening', 'closing']) {
                    const field = page.getByLabel(day + ' ' + kind + ' time', {exact: true});
                    await field.click(); await field.press('ArrowDown'); await field.press('Enter');
                    check(await field.inputValue() === (kind === 'opening' ? '08:15' : '17:15'), role + ' Court ' + day + ' ' + kind + ' actual dropdown click');
                    check(await page.locator('#facilityDay-' + day.toLowerCase()).isChecked(), role + ' ' + day + ' dropdown does not toggle day checkbox');
                }
            }
            await page.screenshot({path: path.join(out, role + '-court.png'), fullPage: true});
            await page.locator('[data-facility-field="operating_hours"]').screenshot({path: path.join(out, role + '-schedule.png')});
            // Discard altered Court time draft; its saved campus weekdays remain.
            await page.locator('#backToFacilitiesButton').click();
            await edit('BROWSER-HALL');
            check(await monday.isEnabled(), role + ' unrestricted weekdays enabled');
            await page.getByLabel('Tuesday opening time', {exact: true}).selectOption('09:15');
            const savedResponse = page.waitForResponse(r => r.url().includes('/BROWSER-HALL/update/') && r.request().method() === 'POST');
            await page.locator('#saveFacilityButton').click();
            const savedHall = await savedResponse;
            check(savedHall.ok(), role + ' Hall edit saves');
            check(!Object.prototype.hasOwnProperty.call((await savedHall.json()).facility.workflow_config, 'allowed_booking_days'), role + ' unrelated Hall edit preserves implicit legacy booking rules');
            await page.reload(); await edit('BROWSER-HALL');
            check(await page.getByLabel('Tuesday opening time', {exact: true}).inputValue() === '09:15', role + ' Edit reload persists');
            const nextTuesday = new Date();
            nextTuesday.setDate(nextTuesday.getDate() + ((2 - nextTuesday.getDay() + 7) % 7 || 7));
            const date = `${nextTuesday.getFullYear()}-${String(nextTuesday.getMonth()+1).padStart(2,'0')}-${String(nextTuesday.getDate()).padStart(2,'0')}`;
            const available = await context.request.get(base + `/api/mobile/facilities/BROWSER-HALL/availability/?date=${date}`);
            const availability = await available.json();
            check(available.ok() && availability.slots.some(slot => slot.start === '09:15' && slot.end === '17:00'), role + ' saved hours synchronize with mobile HTTP response');
            const asset = await page.evaluate(() => [...document.scripts].map(s => s.src).find(src => src.includes('facility_form_controls.js')));
            const script = await context.request.get(asset);
            check(script.ok() && !(await script.text()).includes('weekend_only:'), role + ' Chrome receives current operating-day JS');
            roles.push({role, checks: 'Add/Edit/View, clicks, presets, native selects, save/reload/mobile', asset: new URL(asset).pathname + new URL(asset).search, assetHash});
            await context.close();
        }
        check(errors.length === 0, 'Page errors: ' + JSON.stringify(errors));
        fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({checks, roles, errors}, null, 2));
    } finally { await browser.close(); }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
