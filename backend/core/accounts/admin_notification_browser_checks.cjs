/* Existing bell behavior on Django-exported isolated role fixtures. No writes. */
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {chromium} = require(process.env.CAMPUSHUB_PLAYWRIGHT_MODULE);
const out = process.env.ADMIN_BELL_REVIEW_DIR;
const staticRoot = path.resolve(__dirname, '../../static');
let checks = 0;
const check = (value, label) => {assert.ok(value, label); checks++;};
(async () => {
    const browser = await chromium.launch({channel: 'chrome', headless: true});
    const errors = [], writes = [];
    try {
        const expected = JSON.parse(fs.readFileSync(path.join(out, 'expected.json')));
        for (const [role, fixture] of Object.entries(expected)) {
            const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
            page.on('pageerror', error => errors.push({role, error: error.message}));
            await page.route('**/*', route => {
                const request = route.request(), url = new URL(request.url());
                if (request.method() !== 'GET') writes.push(url.pathname);
                if (url.pathname === '/review') return route.fulfill({path: path.join(out, role + '.html'), contentType: 'text/html'});
                if (url.pathname === '/admin-messages/' || url.pathname === '/admin-settings/') {
                    return route.fulfill({body: `<!doctype html><html><body><h1>${url.pathname}</h1></body></html>`, contentType: 'text/html'});
                }
                if (['/bootstrap.min.css', '/bootstrap.bundle.min.js'].includes(url.pathname)) {
                    return route.fulfill({path: path.join(out, url.pathname.slice(1))});
                }
                if (url.pathname.startsWith('/static/') &&
                    (url.pathname.endsWith('.css') || url.pathname.endsWith('/admin_notifications.js'))) {
                    return route.fulfill({path: path.join(staticRoot, url.pathname.slice(8))});
                }
                return route.fulfill({body: '', contentType: 'text/javascript'});
            });
            await page.goto('http://bell.test/review');
            check(await page.locator('a.sidebar-item[href*="admin-notifications"]').count() === 0, role + ' no retired sidebar link');
            check(await page.locator('a.sidebar-item[href*="admin-messages"]').count() === 0, role + ' no duplicate sidebar messages link');
            check(await page.locator('a.sidebar-item[href*="admin-settings"]').count() === 0, role + ' no duplicate sidebar settings link');
            check(await page.locator('.sidebar .nav-group-title', {hasText: /^System/}).count() === 0, role + ' no empty System sidebar group');
            check(await page.locator('.chat-header-see-all[href="/admin-messages/"]').count() === 1, role + ' header See all Messages link retained');
            check(await page.locator('.admin-profile-menu a.admin-profile-item[href="/admin-settings/"]').count() === 1, role + ' profile dropdown Settings link points to /admin-settings/');
            check(await page.locator('.admin-profile-menu a.admin-profile-item[href="/admin-logout/"]').count() === 1, role + ' profile dropdown Logout link retained');
            const bell = page.getByRole('button', {name: 'Notifications', exact: true});
            await bell.click();
            check(await page.locator('.notification-menu').isVisible(), role + ' bell opens');
            check(await page.locator('.notif-dot').count() === Number(fixture.count > 0), role + ' existing pending indicator retained');
            check(await page.locator('.notification-menu-item:visible').count() === fixture.count, role + ' role-scoped list count');
            const unread = page.locator('[data-notification-filter="unseen"]'), all = page.locator('[data-notification-filter="all"]');
            await unread.click();
            check(await unread.getAttribute('class').then(value => value.includes('active')), role + ' Unread selected');
            if (fixture.count) {
                const item = page.locator('.notification-menu-item').first();
                await item.locator('[data-notification-more]').click();
                await item.locator('[data-mark-seen]').click();
                check(await page.locator('.notification-menu-item:visible').count() === fixture.count - 1, role + ' mark seen hides item in Unread');
                await all.click();
                check(await page.locator('.notification-menu-item:visible').count() === fixture.count, role + ' All restores seen item');
                check(await item.getAttribute('class').then(value => value.includes('is-seen')), role + ' seen class preserved');
                for (const action of fixture.approve_actions) {
                    check(await page.locator(`.notification-menu form[action="${action}"]`).count() === 1, role + ' existing action targets exact seller request');
                }
            } else {
                check(await page.locator('.notification-menu-empty').isVisible(), role + ' empty bell remains usable');
                await all.click();
            }
            await page.screenshot({path: path.join(out, role + '-header.png')});
            await bell.click();
            check(!await page.locator('.notification-menu').isVisible(), role + ' bell closes');
            const chatBtn = page.getByRole('button', {name: 'Messages', exact: true});
            await chatBtn.click();
            check(await page.locator('.chat-header-menu').isVisible(), role + ' messages dropdown opens');
            check(await page.locator('.chat-header-see-all[href="/admin-messages/"]').isVisible(), role + ' See all Messages visible');
            await chatBtn.click();
            const profileBtn = page.locator('.header-profile-dropdown button.header-profile');
            await profileBtn.click();
            check(await page.locator('.admin-profile-menu').isVisible(), role + ' profile dropdown opens');
            const settingsLink = page.locator('.admin-profile-menu a.admin-profile-item[href="/admin-settings/"]');
            check(await settingsLink.isVisible(), role + ' profile Settings item visible');
            await Promise.all([
                page.waitForURL('http://bell.test/admin-settings/'),
                settingsLink.click(),
            ]);
            check(page.url() === 'http://bell.test/admin-settings/', role + ' clicking Settings opens /admin-settings/ without login redirect');
            await page.close();
        }
        check(errors.length === 0, 'No JavaScript errors: ' + JSON.stringify(errors));
        check(writes.length === 0, 'No HTTP mutations');
        fs.writeFileSync(path.join(out, 'browser-results.json'), JSON.stringify({checks, errors, writes}, null, 2));
        console.log(JSON.stringify({checks, errors, writes}));
    } finally {await browser.close();}
})().catch(error => {console.error(error); process.exitCode = 1;});
