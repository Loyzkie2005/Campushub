# Shared admin sidebar: white theme and Reports Analytics

Current Services editor (2026-10-13): the catalog shell now selects an independent Add/Edit Service form. `ServiceFormControls` turns selections and actual saved metadata into a service payload; `validate_service_payload` validates it before the existing Facility fields/workflow JSON are saved. See [Service configuration guide](service-configuration.md) for current files/lines, inputs/outputs, validation, tests, troubleshooting and safe practice. Sidebar behavior below remains unchanged.

## Facilities and Services navigation separation — 2026-10-11

### 1. Cause / reason

Confirmed by inspecting the models and configuration: Food Analysis, Training Kitchen/Assessment and Lease of Space are stored in the existing `Facility` table with distinct types/request modes, and submitted requests are stored in `Booking`. There was no Services route. The sidebar and physical reservation lists mixed the workflows. Reusing those records avoids duplicate models, counts and authorization logic.

The final sidebar is Dashboard; Marketplace (Products, Inventory, Orders, Sellers); User Management (Users, Roles & Permissions, User Monitoring); Facilities (Facilities, Bookings, Calendar); Services (Services, Service Requests); Reports (Analytics, Generate Reports); System Settings (Messages, Notifications, Settings); Logout. Permissions still hide unavailable items and empty groups. Existing white/navy/gold styling, Montserrat typography, panel icon, section arrows, animation, compact rail and saved preferences are reused.

### 2. Exact files, current lines and nearby anchors

Paths are relative to the repository root. Search anchors if later edits move a line.

| File | Line / anchor | What changed |
| --- | --- | --- |
| `backend/templates/partials/admin_sidebar.html` | 69, Sellers permission; 109, Facilities; 147, Services; 171, Reports; 201, System Settings | Added the Services group, made Sellers available to authorized Super Admin too, moved facility Analytics under Reports and matched the final menu labels/items. Removed Backup & Restore from the sidebar; its protected route remains. |
| `backend/core/core/urls.py` | 6, service view import; 132–133, `admin-services` / `admin-service-requests` | Added working admin page routes. |
| `backend/core/modules/facilities/services/catalog.py` | 19, `service_resources_q`; 26, `service_labels` | Added one reusable workflow selection condition and display labels based on existing configuration. |
| `backend/core/modules/facilities/service_views.py` | 14, `admin_services_page`; 23, `admin_service_requests_page` | Protected the new pages using existing permissions; reused the catalog editor; added real-record request search, status filter and twenty-row pagination. |
| `backend/core/accounts/views.py` | 720, `admin_facility_page`; 732, `facilities_qs`; 856, `_bookings_calendar_events`; 1118, `_booking_request_rows`; 1168 / 1193, Bookings / Calendar | Separated resources, summaries, recent activities, form types, booking rows, calendars and selector options. The service catalog uses the same editor and write APIs. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 16, service stylesheet; 21, shared sidebar; 147, Service Name; 429, type choices; 1082, showing text; 1135, `formatFacilityType` | Shared the existing layout with service labels, six visible service columns, restricted new-record types and matching form/footer wording. Capacity/rate columns remain available to physical facilities; they are hidden in the service list. |
| `backend/templates/partials/facility_row_menu.html` | 11, More actions; 21 / 28 / 34, Restore / Edit / Archive | Existing actions now say Service in the service catalog and Facility elsewhere. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_service_requests.html` | 20, header; 37, table; 58, dialogs; 80, detail-button listener | Added the requested eight-column table and escaped real-record View details, using native dialog keyboard/focus behavior. Reused shared header, sidebar and logout partial. |
| `backend/core/modules/facilities/static/facilities/css/admin_services.css` | 2, hidden catalog columns; 4, grid track; 13, request scrolling; mobile block, header sizing | Added local layout rules, contained table scrolling and small-screen header sizing without restyling the sidebar or other pages. |
| `backend/core/api/views.py` | 1685, `service_resources_q` guard | Rejects service resources in the ordinary reservation/schedule-create endpoint, before creating a Booking. |
| `backend/core/modules/facilities/test_service_navigation.py` | 18, `ServiceNavigationTests` | Tests separation, real data, permissions, active navigation, legacy configuration, empty states, pagination and the reservation guard; exports optional isolated browser fixtures. |
| `backend/core/accounts/tests.py` | 178, Generate Reports; 272, backup-link assertion; 276, final sidebar comment | Updated older sidebar expectations to the user's final structure while retaining authorization checks. |
| `scratch/services-navigation/check.cjs` | 1, browser verification helper | Checks actual test-rendered pages with local assets; not production application code. |
| `CAMPUSHUB_CONTEXT.md` | 1974, `Current Facilities / Services navigation` | Records the separation and current service-processing limitations. |
| `docs/sidebar-navigation-white-all.md` | 3, this section | Adds the implementation explanation, troubleshooting and safe practice. |

### 3. Changes made

Services shows real configured laboratory, assessment, leasing and Other service records with Service, Category, Pricing, Request Type, Status and existing View/Edit/Archive/Restore actions. Its Add/Edit Service form now uses separate service configuration and validation while sharing the catalog image uploader; see the Service configuration guide above. Physical Facilities lists/form options exclude service resources.

Service Requests shows Request ID, Requester, Service, Request Type, Date Submitted, Status, Assigned Office / Personnel and View. The current models have no assigned-office/personnel field, so that value is `—`, rather than an invented assignment. The existing request statuses are Pending, Approved, Rejected, Cancelled and Completed. No new status workflow was created. Archived service records' historical requests remain accessible in the request list.

### 4. How it works: functions, inputs, outputs and data flow

`service_resources_q(prefix="")` returns a Django `Q` expression. Service resource types are food_analysis, training_kitchen and lease_space; service modes are service, direct (legacy), assessment and lease. Matching either existing type or mode preserves classification of legacy records whose mode still has an old default. This is filtering, not a database update. A known physical type configured with a service mode also follows that configured workflow.

```python
# Direct Facility selection:
Facility.objects.filter(service_resources_q())
# The same condition through Booking.facility:
Booking.objects.filter(service_resources_q("facility__"))
# Physical list uses the complementary selection:
Facility.objects.exclude(service_resources_q())
```

`service_labels(facility)` receives an existing record and returns `(service_type_label, request_type_label)`. Known types use their configured workflow; generic legacy service/direct records remain generically labeled Service rather than being assumed to be a laboratory.

`admin_services_page(request)` checks existing catalog-read/manage permissions and calls the shared catalog view with an internal `services=True` argument. A query-string parameter cannot switch a normal Facilities request into the Services page. The editor sends its existing payload to existing facility create/update/archive/restore APIs; those APIs retain server-side write permission checks.

`admin_service_requests_page(request)` selects service-related bookings before applying search/status filters and pagination. `select_related("facility", "user")` loads names in the same query, avoiding per-row lookups. `_booking_display_fields` reuses recorded requester/purpose formatting. Only the selected twenty rows are prepared for display. Template escaping protects rendered text; the View button opens the corresponding native dialog, with Close/Escape support. No raw request metadata is serialized to JavaScript.

Data flow: existing Facility configuration → shared selection condition → authorized catalog/request queryset → real summaries or paginated rows → existing shell/sidebar/card styles. Sidebar `active_page` opens Services and applies the existing gold active class. The existing section handler saves `sidebar_group_services`, sets `aria-expanded`, and makes closed links inert, without a second animation system.

### 5. Backend / API and role visibility

Services requires `can_view_facilities` or `can_manage_facilities`; write actions require the existing manage permission. Service Requests requires any existing `can_view_bookings`, `can_manage_bookings`, `can_approve_bookings` or `can_record_facility_payment`. The group appears only when at least one child is authorized. Super Admin and Facilities Admin have the existing capabilities; Marketplace Admin does not receive service access. Custom roles follow their actual grants. Unauthorized direct requests return 403; anonymous requests redirect to login. The request-list page is GET-only.

Reports Analytics chooses the existing marketplace route when that permission is present, otherwise the existing facility route. Generate Reports retains its existing domain restrictions despite the standardized visible label. Sellers still uses existing permission and academic scope. Backup loses only its sidebar link; its protected endpoint and existing dashboard action remain.

Physical booking/calendar data and selector options exclude service workflows before their existing record limits. The ordinary `/api/bookings/create/` endpoint returns 400 for a service resource and writes nothing. This does not create a service intake API. Existing mobile routes and dashboard/report aggregation were not redesigned in this navigation task.

### 6. Database / migration impact

None. No new Facility/Service/Request table, permission, status field, assignment field or migration. Existing service/booking records are reclassified for display only; no live data was moved, deleted or generated. Browser examples are isolated test-database fixtures.

### 7. Tests and manual verification

Actual final verification:

- **18 Django tests passed**: service navigation/separation plus existing domain permissions and facility archive/restore regressions. Latest log: `scratch/services-navigation-verified.log`.
- **6 headless Chrome cases passed**: Services and Service Requests at 1440, 768 and 375 pixels. Verified active gold selection, the existing Services section open/close and inert state, exact visible table headers, contained page width, service form types/titles, dialog View/Escape, and no JavaScript errors. Log: `scratch/services-navigation-browser.log`. Desktop catalog and phone request screenshots were visually inspected; the harness removes external fonts/images and loads local assets for reproducible layout checks.
- Django system checks reported no issues; `makemigrations --check --dry-run` reported No changes detected. Targeted tracked-file `git diff --check` passed.
- Initial test runs exposed test-fixture issues: an absent unmanaged feedback table, a normal booking test overlapping its own fixture, and an outdated 200 expectation for the existing 201-create response. Fixtures/expectations were corrected; they were not production application failures. Browser checks found and fixed the layout causes described below, then passed after rendering the final templates.

These checks used isolated test data, not live service submissions, emails, or production writes. Manual checks:

1. Refresh the admin page; expand Services and confirm Services / Service Requests appear between Facilities and Reports. Test keyboard focus and saved open/closed state.
2. As Super Admin or Facilities Admin, open Services; confirm existing lab/assessment/lease records appear and physical spaces do not. Check Add/View/Edit labels and existing write permissions using a test environment.
3. Open Facilities, Bookings and Calendar; confirm service resources/requests are absent from their normal lists and selectors.
4. Open Service Requests; search a real request, filter its actual status, change pages, and open View. Check recorded requester/date/status/purpose, `—` assignment, Close and Escape.
5. As Marketplace Admin, confirm Services links are absent and direct service URLs are forbidden. A custom catalog-only reader should see Services/View but not Service Requests or usable write actions.
6. Resize to tablet/phone: only the table scrolls horizontally, while the page/header stay within the viewport. Verify the gold active item and section arrows still behave like the existing sidebar.

### 8. Debugging, remaining limitations and safe learning exercise

Confirmed layout issues found in verification: the reused catalog grid's default minimum track size expanded to the 1080px table width, and an existing `overflow: visible !important` rule allowed the table to escape. A local `minmax(0, 1fr)` track and local scroll override contain it. The longer Service Requests title also pushed header icons outside a phone viewport; local mobile header rules fix that. Other module layouts were not changed.

If a record appears in the wrong group, inspect its actual facility_type and booking_mode and the configuration rules before changing production data. A legacy service record with an inappropriate type may need an administrator to select its proper configured service type when editing. If access is denied, check existing facility/bookings grants; do not remove decorators or grant Marketplace global access. If an assignment is blank, the field does not exist yet; adding fake personnel in the template is not a fix.

The current service request list is read-only. The full ISO laboratory intake, sample checklist, resource approval, job order, statement of account, cashier OR, results release, assessment registration and lease-processing stages still require dedicated workflow work. This change does not claim those processes are implemented. Existing dashboards/reports still aggregate their current facility-backed data sources; separating their metrics is a separate scope decision.

Safe practice: in an isolated test fixture, create one `other` resource with booking_mode `direct`. Predict whether `service_resources_q` includes it, then run `venv/Scripts/python.exe manage.py test modules.facilities.test_service_navigation.ServiceNavigationTests.test_legacy_modes_and_types_are_not_misclassified --keepdb --noinput` from `backend/core`. The passing test proves that legacy configuration is read consistently without creating a second Service model or touching real records. Next trace the prefix version into the request queryset to understand a Django relationship filter.

## Animated open/close panel icon - 2026-10-08

### 1. Cause / reason

The sidebar already changed size and accessible button labels, but the panel icon stayed visually identical. The user requested animation when switching it on/open and closed. The icon now changes between left-panel and right-panel divider positions, without adding dots or changing its placement below the logo when compact.

### 2. Exact files changed

| File | Current line / nearby anchor | Change in this update |
| --- | --- | --- |
| `backend/templates/partials/admin_sidebar.html` | 16, `sidebar-panel-divider` | Add a CSS class to the existing SVG path; retain the plain outline and divider. |
| `backend/static/components/css/admin_layout.css` | 124, `.sidebar-panel-divider`; 128, `[aria-expanded="false"]` | Add a 240ms transform transition and a 6-unit horizontal divider movement for the collapsed state. |
| Same stylesheet | 71, restored compact preference; 2453, `prefers-reduced-motion` | Avoid startup animation when restoring a compact sidebar and disable icon motion for reduced-motion users. |
| Existing 24 page templates listed in the reference table below | Same reference lines; Dashboard example: 12 | Version-only stylesheet update to `20261008-sidebar-icon-motion`. |
| `scratch/inventory-monitor/check-sidebar-groups.cjs` | 40, `iconX`; 74, `closingX`; 80, `openingX` | Check rendered icon positions, intermediate motion, reversal and reduced motion. |
| `docs/sidebar-navigation-white-all.md` | 3, this report | Explain behavior, code flow and debugging. Earlier reports record earlier change locations. |

### 3. Changes made

Added a class and CSS rules, reusing the existing button state. The outline stays still while the vertical divider slides right during collapse and left during expansion. The icon remains navy, without decorative dots. Sidebar widths, compact vertical placement, routes and section controls are unchanged in this update.

### 4. How it works: functions, inputs/outputs and data flow

The existing click handler in `admin_sidebar.html:268` switches sidebar classes and sets `aria-expanded` at line 273. That attribute is the input to the new CSS selector. CSS outputs the divider's transform: expanded is zero movement; collapsed moves it 6 SVG coordinate units right. The browser interpolates between those positions over 240ms. This reuses the same accessible state instead of keeping a second icon-state variable or adding animation timers.

```css
.sidebar-panel-divider {
    transform: translateX(0); /* Expanded: divider at its original position. */
    transition: transform 240ms cubic-bezier(0.2, 0, 0, 1);
}
.sidebar-collapse-toggle[aria-expanded="false"] .sidebar-panel-divider {
    transform: translateX(6px); /* Collapsed: divider slides to the right. */
}
```

Why this approach: transforming one existing SVG path is small, reversible and does not resize the button or interrupt its click/keyboard handling. CSS transitions also reverse from the current rendered position when clicked again. Reduced motion uses the same final state with no transition.

The browser helper's `iconX()` reads the computed transform through `DOMMatrixReadOnly` and returns its horizontal translation. Intermediate values between 0 and 6 verify actual animation, not just the presence of a CSS declaration.

### 5. Backend / API behavior

No backend/API change. Existing permissions, routes and sessionStorage preference remain in use; no new network requests or business logic.

### 6. Database / migration impact

No migration or production data change. The template export verification used the existing isolated test fixture, not live sample records.

### 7. Tests performed / how to test

- Reran the isolated Django template-export test: 1 test passed; system check found no issues.
- Ran Chrome verification: 5 cases passed (expanded, restored group preferences, compact, 375px mobile and reduced motion). Checked divider starting/ending positions, visible intermediate values in both directions, rapid reversal, correct accessible label and zero transition duration with reduced motion. Existing compact placement and section animation checks passed.
- Targeted `git diff --check` passed.

Manual steps: Ctrl+F5, click the panel toggle and watch its divider slide right as the sidebar collapses. Click again and watch it slide left. Click twice quickly and check the final icon matches the final sidebar state. Enable reduced motion in browser rendering tools: switching should be instant while remaining functional. Reload while collapsed to check the saved state appears directly.

### 8. Limitations / debugging and safe practice

Confirmed cause of the previously static icon: its existing path had no state-dependent transform or transition. Every authenticated admin page was not opened individually; checks covered the actual shared template and stylesheet. On narrow screens, the existing responsive compact rail remains unchanged; this update only adds icon-state animation to the existing toggle.

If it looks static, inspect the loaded CSS version (`20261008-sidebar-icon-motion`), the path's `sidebar-panel-divider` class and whether `aria-expanded` changes after a click. Also check the operating system's reduced-motion setting: instant switching is intentional there. If position and label disagree, inspect the existing click handler rather than adding another state variable.

Safe practice: in DevTools only, change `240ms` to `400ms`, click twice and observe the slower movement and reversal. Check that the button's label still changes immediately, then reload to discard the experiment. Avoid changing stock, user permissions or database records while practicing animation.

---

## Toggle below the logo when collapsed - 2026-10-08

### 1. Cause / reason

The earlier placement put the toggle beside the logo in an 88px compact sidebar. The user's latest instruction, "MOVE BELOW", changes that placement. The toggle now sits below the logo when collapsed, and the compact sidebar returns to 64px. Expanded placement remains beside the CampusHub name.

### 2. Exact files changed

- `backend/static/components/css/admin_layout.css:64`, collapsed width: restore 64px.
- Same stylesheet, `:169`, collapsed logo selector, and `:176`, `flex-direction: column`: stack the logo and toggle vertically.
- Same stylesheet, `:415`, collapsed main-wrapper margin: restore the matching 64px content offset.
- Same stylesheet, `:1112`, mobile logo rule; `:1131`, mobile sidebar width; `:1143`, mobile content margin: apply the same placement and width on small screens.
- The 24 existing page templates listed in the CSS-reference table below: version-only update to `20261008-sidebar-below`; their reference lines are unchanged. This refreshes the shared stylesheet across admin pages.
- `scratch/inventory-monitor/check-sidebar-groups.cjs:41`, compact/mobile checks: verify width, vertical placement, horizontal centering and button containment.
- `docs/sidebar-navigation-white-all.md:3`: update this feature guide rather than create another document.

### 3. Changes made

Changed the compact logo row to a vertical stack. Removed the extra 24px of sidebar width introduced by the previous side-by-side arrangement. The plain divider-only panel SVG, 44px button target, expanded placement and existing section animations are retained. No icon or navigation item was removed in this correction.

### 4. How it works: functions, inputs/outputs and data flow

The existing `sidebarToggle` click handler takes a click, switches the sidebar's `collapsed`/`expanded` classes and saves the preference in sessionStorage. CSS reads those classes and the viewport width, then determines the sidebar width, logo arrangement and content offset. There is no new JavaScript function in this correction.

```css
/* Stack the logo and toggle; center them on the same vertical axis. */
flex-direction: column;
/* Reserve the same horizontal space for the sidebar and page content. */
width: 64px;       /* Collapsed sidebar. */
margin-left: 64px; /* Corresponding main content offset. */
```

These declarations belong to their respective selectors, not one combined rule. Equal width and margin values prevent overlap or an empty strip. A vertical stack preserves the button's touch target inside a narrow rail. Expanded CSS continues to arrange the CampusHub name and toggle horizontally.

### 5. Backend / API behavior

Unchanged. Existing routes, permissions, section states and click handlers are reused. No API requests are added.

### 6. Database / migration impact

None. No model, migration or production record changes. Existing sessionStorage preferences are preserved.

### 7. Tests performed / manual steps

- Ran the Chrome verification helper: five cases passed (expanded, restored preferences, compact, 375px mobile and reduced motion).
- Compact/mobile assertions verified a 64px sidebar, toggle below the logo with a gap, shared horizontal center and button containment. Existing keyboard, animation reversal, saved preference, plain SVG and inert-menu checks passed.
- Visually inspected `scratch/inventory-monitor/sidebar-groups-compact.png`: the plain panel icon is centered below the logo.
- Targeted `git diff --check` passed.
- The earlier isolated Django template-export test was not rerun for this CSS-only placement correction. Browser verification reused that actual template export with the updated stylesheet.

Manual test: refresh with Ctrl+F5, collapse the sidebar and confirm the toggle sits below the logo. Expand it and confirm the toggle returns beside CampusHub. Open/close Marketplace and Reports, then resize to mobile and verify the compact stack without clipping.

### 8. Limitations / debugging and safe practice

Confirmed cause: compact and mobile CSS used a horizontal row; both now use `column`. Browser checks used exported actual shared templates; every authenticated live page was not individually opened. If the old arrangement persists, check the loaded stylesheet version is `20261008-sidebar-below`, then inspect the logo row's computed `flex-direction`. If a page overlaps the sidebar, compare computed width and content margin; both should be 64px when compact.

Safe practice: in DevTools only, change the compact logo rule's `gap` from 4px to 8px. Predict that the toggle moves 4px farther below the logo, inspect the result and reload to discard the experiment. This teaches spacing without modifying routes or saved application code.

---

## Animated sections and relocated panel toggle - 2026-10-08

### 1. Cause / reason

The user clarified that Marketplace, User Management, Facilities, Reports and System Settings should expand/collapse individually. Existing JavaScript toggled their `open` classes, but CSS disabled pointer events on their headers and displayed every menu list regardless of state. The double-chevron outer-sidebar button also occupied the page header instead of the requested position beside CampusHub.

### 2. Exact files changed

| File | Current line / code anchor | Change |
| --- | --- | --- |
| `backend/templates/partials/admin_sidebar.html` | 8, `sidebar-brand`; 13, `sidebar-collapse-toggle` | Wrap the existing logo/name and move the existing `sidebarToggle` beside them, using a panel SVG. |
| Same sidebar template | 35, `nav-group-chevron` | Replace triangle characters with consistent chevron SVGs for section state. All five permitted sections share this structure. |
| Same sidebar template | 283, `Animate the navigation sections`; 285, `syncGroupAccessibility` | Add independent measured-height section animation, saved states, closed-content accessibility and rapid-click handling. |
| `backend/templates/partials/admin_header.html` | 4, `header-left` | Remove the old double-chevron button; retain page title, breadcrumbs and right-side actions. |
| `backend/static/components/css/admin_layout.css` | 109, `.sidebar-collapse-toggle`; 210, `.nav-group-toggle`; 260, `.nav-group-items` | Compact panel button beside the name; clickable section headers, sliding lists, rotating section chevrons and visible keyboard focus. |
| Same stylesheet | 1111, mobile media query; 2445, `prefers-reduced-motion` | Preserve the compact icon rail and turn off navigation transitions when reduced motion is requested. |
| `scratch/inventory-monitor/check-sidebar-groups.cjs` | 1, `Actual Django test HTML` | Read-only browser verification using exported real Django templates, actual inline script and CSS. |
| `docs/sidebar-navigation-white-all.md` | 3, `Animated sections` | This implementation and learning report. |

The following 24 existing page templates changed only their `admin_layout.css` cache version to `20261008-sidebar-groups`. This makes every shared admin page request the updated styles; it changes neither that page's records nor business logic:

| Page template | Current CSS reference line |
| --- | --- |
| `backend/templates/marketplace/pages/admin_sellers.html` | 11 |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 12 |
| `backend/templates/dashboard/pages/admin_facilities_dashboard.html` | 14 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_backup.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_data_export.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_roles.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_settings.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_monitoring.html` | 13 |
| `backend/core/modules/reports/templates/reports/pages/admin_facility_analytics.html` | 11 |
| `backend/core/modules/reports/templates/reports/pages/admin_generate_reports.html` | 12 |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 11 |
| `backend/core/modules/notifications/templates/notifications/pages/admin_notifications.html` | 12 |
| `backend/core/modules/messages/templates/messages/pages/admin_messages.html` | 12 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_inventory.html` | 11 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 12 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_orders.html` | 11 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 12 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_sellers.html` | 11 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_user_seller.html` | 11 |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 12 |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facilities_dashboard.html` | 12 |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 12 |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility_booking.html` | 12 |

### 3. Changes made

- Section buttons now open/close their own menu list; other sections stay in their current state. The page's active section starts open, while other groups use their saved state or existing template default.
- Menu lists slide over 240ms and fade over 160ms; section chevrons rotate. The outer sidebar keeps its prior width-toggle behavior, rather than the earlier proposed outer-sidebar animation rewrite.
- The panel icon is now to the right of CampusHub in the sidebar brand row. In the compact icon rail it remains reachable below the logo. Brand text is slightly smaller to fit the name and 44px button inside the existing 250px sidebar.
- No routes, permission conditions, menu items or current active-menu colors were removed. The sidebar remains white with navy/gold styling.

### 4. Functions, inputs/outputs and data flow

The shared Django partial receives `user`, `perms.accounts` and `active_page`, then renders only the allowed groups and links. The browser reads each group's title, existing `open` class, active link and `sessionStorage` preference. It gives the group's items an ID and connects the button with `aria-controls`/`aria-expanded`.

The section click handler measures the current list height, fixes that height in pixels, forces a layout read, changes the `open` state, and sets its new height to zero or `scrollHeight`. This also works while an earlier transition is running. When an opening height transition finishes, the handler changes height to `auto` so normal content sizing resumes. Reduced-motion users get the final height immediately.

```javascript
items.style.height = items.getBoundingClientRect().height + 'px'; // Current visible height.
void items.offsetHeight;                                        // Commit this start value.
items.style.height = nextOpen ? items.scrollHeight + 'px' : '0px'; // New destination.
```

`syncGroupAccessibility()` takes current outer-sidebar/viewport state and section classes. Its output sets `inert` and `aria-hidden` on closed lists. Closed expanded-sidebar lists cannot receive keyboard focus. In the compact 64px rail, every permitted icon remains available regardless of group preference. A viewport-change listener reapplies this rule.

Data flow: authorized Django sidebar HTML -> browser section initialization -> section button click/Enter/Space -> measured height/CSS transition -> sessionStorage state -> shared sidebar on the next page. Navigation still goes to the existing Django URLs. `sidebarToggle` retains the existing outer-sidebar handler and storage key; moving it changes its position, not its destination or purpose.

### 5. Backend / API behavior

Unchanged. The same Django permissions decide which links exist, and existing views enforce their permissions. No new API request, page or approval logic was added. Sections are presentation groups, not new modules or records.

### 6. Database / migration impact

None. Section preferences are browser-tab sessionStorage, not database fields. No migration or live record writes. The fixture export test used a separate temporary Django test database.

### 7. Tests performed / manual steps

- Ran `ProgramInventoryTests.test_export_isolated_catalog_and_inventory_for_browser_review` after the final script update: one test passed; Django system checks reported no issues.
- Ran `node scratch/inventory-monitor/check-sidebar-groups.cjs`: all five real Chrome cases passed: expanded desktop, restored section preference, compact sidebar, actual 375px mobile viewport and reduced motion.
- Browser checks verified the panel button is inside the sidebar and absent from the header, one toggle ID, fitting brand/button row, named icon links, trusted Enter activation, intermediate animated heights, rapid close/open reversal, final auto height, saved state, zero-height/inert closed menus, and compact navigation restoration.
- Inspected `scratch/inventory-monitor/sidebar-groups-expanded.png` visually. The screenshot uses test-database rows and offline styles; no sample records were inserted into the live system.

Manual steps: reload an admin page (Ctrl+F5 if needed), click Marketplace and Reports, and confirm only the selected group moves. Tab to a section heading and use Enter or Space. Close a group and verify its links are skipped when tabbing. Navigate to another permitted page and check saved groups; that page's active section should open. Click the panel icon beside CampusHub, confirm compact icons remain usable, then expand again. Enable reduced motion in browser tools or Windows and confirm the sections snap to their final state.

### 8. Remaining limitations / debugging and safe practice

Preferences belong to the current browser tab and permitted group names; another tab/device has its own state. An active page's group is deliberately reopened on page load, even if it was previously closed. Small screens retain the existing icon rail rather than receiving a new accordion drawer. Current browsers support `inert`; older unsupported browsers were not tested. Offline browser checks cover the real shared templates, not an authenticated live session for every one of the 24 pages.

If clicking a heading does nothing, inspect `.nav-group-toggle` computed `pointer-events` (it must not be `none`) and check the stylesheet version. If a group is open but clipped, inspect its inline height; it should become `auto` after opening. If a collapsed list receives focus, inspect `inert` and `aria-hidden`, and distinguish the expanded sidebar from the intentionally usable compact rail. Do not remove backend permissions to expose a missing link.

Safe practice: in DevTools only, change the list height transition from `240ms` to `400ms`; repeatedly open/close Reports and observe how current-height measurements allow reversal. Reload to discard the experiment. Run the browser helper afterward with the original timing. It verifies a height between zero and full size, then confirms the final state instead of merely checking that an `open` class exists.

---

## Latest update — Analytics first under Reports; header renamed (2026-10-06)

### 1. Cause / Reason

The user requested an **Analytics** entry under Reports, then confirmed it should be **first under Reports, above Generate Reports**. The page header and browser title should say Analytics. Reuse the existing permission-protected route instead of creating another page or changing calculations. This supersedes the earlier removal of its sidebar link. Voucher remains removed. The scope of removing page sections is awaiting the separate clarification (all sections versus section headings); current page content is retained until that choice is supplied.

### 2. Exact Files Changed

| File | Current approximate line / anchor | Change |
| --- | --- | --- |
| `backend/templates/partials/admin_sidebar.html` | 144–150, Reports group; 152–159, Analytics; 160–170, report link | Move Analytics first, preserving active/open group and permission conditions. |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 8, browser title; 19, shared header include | Rename to Analytics and remove Marketplace from the breadcrumb. |
| `CAMPUSHUB_CONTEXT.md` | 21, current sidebar preference | Save the new Reports navigation decision. |
| `docs/sidebar-navigation-white-all.md` | 1, latest update | Explain this change, checks and debugging without creating a duplicate guide. |

### 3. Changes Made

Super Admin sees **Reports → Analytics → Generate Reports**, with the last two as sibling menu items. Analytics has a navy outline chart icon and uses the existing gold selected style. The existing route remains `/admin-marketplace-analytics/`; its header is **Analytics**, browser title is **CampusHub | Analytics**, and breadcrumb is **Dashboard › Analytics**. Other authorized roles receive the same link; existing role-specific report labels remain. No cards, charts or tables have been removed in this step.

### 4. How It Works

This is a shared Django template change, not a new Python function. Inputs are `perms.accounts`, `user` and `active_page`. Output is the permitted sidebar HTML. Admin page → shared sidebar include → permission conditions → `{% url 'admin_marketplace_analytics_page' %}` resolves the destination → clicking the link reaches the existing view.

```django
{% if perms.accounts.can_view_marketplace_analytics %}
    {# Display the link only for an authorized user. #}
    <a href="{% url 'admin_marketplace_analytics_page' %}">Analytics</a>
{% endif %}
```

The actual link also uses `active_page == 'marketplace_analytics'` to add `active` and `aria-current="page"`. The Reports group's condition opens it on that page. Removing this active-page case from Marketplace avoids opening the wrong group. The Reports group includes analytics permission even when a role has no report permission; the Generate Reports link has its own report permission condition. Link order comes from HTML order, so moving the existing block above the report block is sufficient. `page_title='Analytics'` is an input to the shared header template, which renders its `<h1>`; this affects only this page, not every shared header.

### 5. Backend / API Behavior

No routes, APIs, analytics formulas or permissions were changed. The existing `admin_marketplace_analytics_page()` in `modules/reports/views.py` remains protected by `accounts.can_view_marketplace_analytics`. Hiding a link supplements the server check; it does not replace it. Existing Facility Analytics navigation remains separate.

### 6. Database / Migration Impact

None. No database records or migrations changed. Permission tests ran against the isolated test database.

### 7. Tests Performed

- **Latest follow-up: seven existing tests passed**: all six `accounts.tests.DomainAnalyticsPermissionTests` plus the Marketplace Analytics permitted/blocked page test. No test code changed in this follow-up.
- Actual Django renders verified Analytics appears before Generate Reports, stays selected in an expanded Reports group, and both header and browser title are renamed.
- During the preceding link-addition step, both former link-absence assertions were updated. The first run exposed the old Super Admin expectation; correcting that expectation matched the requested behavior without changing backend enforcement.
- Actual shared-template renders passed for Super Admin, analytics-only, reports-only and no-access permission contexts. Verified link placement, active/open Reports group and permission visibility; analytics-only users do not get a Generate Reports link.
- The earlier headless Chrome review verified the white/gold theme and selected Reports item. Its `reports-analytics-sidebar.png` shows the preceding menu order; use the current Django-render check for this follow-up's order. No CSS changes were made.
- Changed-file whitespace checks passed. No broad analytics test rerun was needed because the follow-up only alters navigation and header text.

Manual check: reload an admin page, expand Reports, confirm Analytics is above Generate Reports, then click it. Confirm its header says Analytics and the gold highlight stays on Analytics. A user without its permission must not see the link and must still receive denied access if they try its URL.

### 8. Remaining Limitations

The page is now named **Analytics**, but it still displays the existing marketplace analytics data and uses the same route/permission. Facility Analytics remains separate. The requested page-section removal awaits clarification; no removal is claimed. Already-open pages need a reload; HTML changes do not require a stylesheet cache update. The earlier Chrome review used a rendered offline sidebar, not a signed-in visit to every page.

### Debugging and safe practice

| Symptom | Check |
| --- | --- |
| Analytics missing | Reload, expand Reports, then check `can_view_marketplace_analytics`. Do not grant unrelated permissions to make a menu appear. |
| Link produces 403 | The backend permission check is denying access; inspect the role's analytics permission. |
| Wrong group opens or no gold highlight | Check the page includes the sidebar with `active_page='marketplace_analytics'`. |
| Old test expects no link | Update only the authorized role's navigation expectation; keep unauthorized route checks. |

Safe exercise: use browser Developer Tools to change only the visible Analytics label to **Marketplace Analytics**. The URL and permissions should stay unchanged. Reload to discard the temporary edit. This teaches the difference between link text, destination and authorization. See [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) for the reusable investigation workflow.

---

## Earlier implementation — removal and white theme (historical)

The report below describes the earlier request. Its link-removal expectations are superseded by the latest update above; the white theme and Voucher removal remain current.

Updated 2026-10-05.

## 1. Cause / Reason

The user requested removal of the Marketplace Analytics sidebar entry while keeping dashboard analytics, confirmed that Voucher should also be removed, and requested white sidebars on every admin page. The shared CSS already supplied the white theme, but 22 other admin templates still used older stylesheet cache versions.

## 2. Exact Files Changed

| File | Current line / nearby anchor | What changed |
| --- | --- | --- |
| `backend/templates/partials/admin_sidebar.html` | 23, Marketplace group permission condition | Removed the analytics-only permission from this group's visibility condition, avoiding an empty Marketplace heading when analytics is the only permission. |
| Same file | 46, Orders conditional immediately after Products / Inventory | Removed the disabled Voucher span and its icon/label/condition. Orders now follows Inventory. |
| Same file | 54, Sellers conditional; 61, end of Marketplace items | Removed the Marketplace Analytics link, icon, label and surrounding condition. No dashboard card or analytics route was removed. |
| `backend/core/accounts/tests.py` | 143, marketplace-admin sidebar assertion | Updated the existing test to expect the analytics link to be absent, while retaining its successful permission-protected analytics route check. |
| `CAMPUSHUB_CONTEXT.md` | 11, current admin sidebar preference | Saved the removal and all-page white-sidebar preference. |
| `docs/admin-white-sidebar.md` | 5, later update | Linked this current report and marked the earlier cache limitation as historical. |
| This document | 1 | Added the required implementation and learning report. |

The following templates changed only their existing `admin_layout.css` URL cache version to `20261005-white-sidebar`. Nearby anchor for every row: the stylesheet link in the page's `<head>`. The main dashboard already had this version and was not edited in this step.

| Template | Current line |
| --- | --- |
| `backend/templates/marketplace/pages/admin_sellers.html` | 11 |
| `backend/templates/dashboard/pages/admin_facilities_dashboard.html` | 14 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_backup.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_data_export.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_roles.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_settings.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_access_control.html` | 11 |
| `backend/core/modules/user_management/templates/user_management/pages/admin_user_monitoring.html` | 13 |
| `backend/core/modules/reports/templates/reports/pages/admin_facility_analytics.html` | 11 |
| `backend/core/modules/reports/templates/reports/pages/admin_generate_reports.html` | 12 |
| `backend/core/modules/reports/templates/reports/pages/admin_marketplace_analytics.html` | 11 |
| `backend/core/modules/notifications/templates/notifications/pages/admin_notifications.html` | 12 |
| `backend/core/modules/messages/templates/messages/pages/admin_messages.html` | 12 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_marketplace_dashboard.html` | 12 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_orders.html` | 11 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_products.html` | 12 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_sellers.html` | 11 |
| `backend/core/modules/marketplace/templates/marketplace/pages/admin_user_seller.html` | 11 |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 12 |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facilities_dashboard.html` | 12 |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 12 |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility_booking.html` | 12 |

## 3. Changes Made

Removed Voucher and Marketplace Analytics from shared sidebar navigation. Updated 22 stylesheet URLs so every one of the 23 admin references requests the white theme. No new CSS rules or logo assets were needed; the previous shared white sidebar styling applies to all these pages. Facility Analytics navigation remains for authorized facility admins.

## 4. How It Works

Admin pages include `partials/admin_sidebar.html` and load the shared `admin_layout.css`. Removing entries from that partial removes them across roles and pages. Updating the query-string version causes browsers to request the current CSS instead of their older cached copy. The sidebar therefore uses white, navy text/icons and the existing gold selected item consistently.

To check: reload Dashboard, Products, Orders, Facilities, Bookings, Users, Reports and Settings. Confirm white sidebars, no Voucher or Marketplace Analytics menu entries, and normal active-menu/collapse behavior. Confirm the Dashboard still shows Sales Overview, Sales Trend, Top Best-Selling Products and Sales by Product Categories. Detailed analytics remains reachable through existing authorized dashboard links or its URL.

## 5. Backend / API Behavior

No business logic, route or permission changes. Removing a navigation link does not revoke permission or delete the detailed analytics page. Existing server-side access checks remain. Dashboard analytics and its API are preserved.

## 6. Database / Migration Impact

No production writes or migrations. Django tests use the isolated test database.

## 7. Tests Performed

Seven existing Django tests passed: the full `accounts.tests.DomainAnalyticsPermissionTests` class and the marketplace dashboard empty/populated layout test. These cover role-scoped backend access, expected sidebar entries and preserved dashboard charts/cards. Django system checks reported no issues.

Actual shared-template checks passed for Super Admin, Marketplace Admin and an analytics-only permission context, confirming the removed entries and avoiding the empty group. All 22 updated stylesheet references were audited; the dashboard's existing current reference brings the total to 23. Three headless Chrome sidebar previews passed for expanded desktop, collapsed desktop and mobile: white surface, navy foreground, gold selected state, loaded logo, existing widths and no horizontal overflow. The desktop screenshot was visually inspected. `git diff --check` passed.

Generated review artifacts: `scratch/dashboard-global-review/white-sidebar-cache-files.json`, the refreshed `white-sidebar-visual.html`, and desktop/collapsed/mobile screenshots, DOM dumps and logs. Preview: `../scratch/dashboard-global-review/white-sidebar-desktop.png`.

## 8. Remaining Limitations

Already-open pages need a reload to receive the new HTML/menu. The detailed Marketplace Analytics page remains available to authorized users even though it has no sidebar entry. Browser previews use the actual shared template, not a signed-in browser visit to every admin page. This applies to the web admin navigation sidebar; mobile app navigation and inner settings/message panels were not restyled.
# Flutter mobile sidebar removal — clarified request, October 17, 2026

This follow-up supersedes the responsive-web interpretation below. The user meant the Flutter drawer containing Home, Marketplace, Facilities Booking, Messages, Profile & Account and My Cart.

1. **Cause / reason:** `_DashboardDrawer` duplicated four existing bottom tabs. Its hamburger button opened that separate sidebar; hiding web headings could not remove this Flutter UI.
2. **Exact files changed:** `campushub/lib/module_app/screens/dashboard_screen.dart:151`, `_DashboardScreenState.build`, removes the hamburger and adds 16px header padding; line 277, `tooltip: 'Messages'`, preserves the Messages shortcut in the header; line 303, `child: Scaffold`, no longer supplies a drawer; line 341, `bottomNavigationBar`, retains the existing four tabs and center Add Product action. The unused `_DashboardDrawer` / `_DrawerNavTile` classes after `_HeroSlideData` were deleted along with the unused `cart_screen.dart` import. `campushub/test/dashboard_search_appbar_test.dart:10` checks header/search behavior, and line 73 checks all four bottom tabs without a drawer. `campushub/test/dashboard_center_add_button_test.dart:8` verifies Add Product and the relocated Messages shortcut. This existing guide records the change; `CAMPUSHUB_CONTEXT.md` records the accepted navigation preference.
3. **Changes made:** removed the entire mobile sidebar and its Menu button. Kept Home, Marketplace, Facilities and Profile in bottom navigation. Messages is now a navy, labelled header icon. Existing Search/Back and Notifications remain. Cart remains reachable from existing product screens. No web sidebar changes were made in this follow-up.
4. **How it works:** `_goToTab(index)` accepts the selected bottom-tab index, updates `_currentIndex`, and animates the existing `PageController` to its matching page. It does not return data or call a new API. Example: tapping Facilities sends index `2` to `_goToTab`, selecting the existing `FacilitiesPage`. `_openMessages()` takes no arguments and pushes the existing Messages page with its existing Back action; the header now calls that same function instead of a drawer item. `build(context)` outputs the header, four-page `PageView`, and `FloatingBottomNavbar` without a `drawer:` property, so there is no sidebar to open by button or edge swipe. This reuses navigation rather than creating parallel routes.
5. **Backend / API behavior:** unchanged. Existing screens continue using their Django/DRF services and existing chat integration. No endpoint, authentication, seller permission, stock or booking logic changed.
6. **Database / migration impact:** none. No records, schema, packages or migration commands changed.
7. **Tests performed:** five Flutter widget tests passed using `flutter test test/dashboard_header_test.dart test/dashboard_search_appbar_test.dart test/dashboard_center_add_button_test.dart` from `campushub`. Coverage includes 320/390px header fit, search opening/closing, all four bottom tabs, no drawer/Menu button, center Add Product opening/closing and Messages opening/Back. `flutter analyze lib/module_app/screens/dashboard_screen.dart test/dashboard_search_appbar_test.dart` reported No issues found. Dart formatting and targeted `git diff --check` passed. An initial run found the existing center-action test still expected Messages in the removed drawer; its assertions were updated to match the clarified workflow and the final run passed. Tests use Flutter's isolated widget environment with blocked real HTTP, not a physical phone or live API test. The local UI/UX search returned no matching Flutter navigation entry after its retry; implementation follows existing project patterns and the skill's general navigation/accessibility guidance.
8. **Remaining limitations / debugging / practice:** restart the running Flutter app to load the updated widget tree; an already-installed APK needs a rebuilt deployment. If Menu still appears, confirm the installed build includes this change and the visible page is `DashboardScreen`. This change does not remove Home product/facility content sections or any web admin sidebar. Safe exercise: run the three tests above, temporarily change the new Messages tooltip in a local branch, rerun the center-action test and observe the missing-tooltip failure; restore `Messages` and rerun to verify recovery. Manual checks: tap each bottom tab, open/close Search, open Messages and go Back, and open Cart from a product screen. No production record is needed to verify drawer removal.

# Mobile section headings verification — October 17, 2026

1. **Reason:** the user requested that the mobile menu remain available without section headings. Inspection confirmed this behavior already exists; no application CSS, template, Flutter, or backend change was necessary.
2. **Files:** this guide records verification. `scratch/mobile-sidebar-check.cjs:1` is a read-only local Chrome check, not shipped application code. Existing implementation anchors: `backend/static/components/css/admin_layout.css:1119`, `@media (max-width: 768px)`; `backend/templates/partials/admin_sidebar.html:295`, `syncGroupAccessibility()`.
3. **Behavior:** at widths up to 768 CSS pixels, Marketplace, User Management, Facilities, Services, Reports and System Settings heading buttons are hidden. Authorized menu links remain in the compact icon menu, with accessible names. Desktop headings and their expand/collapse behavior remain.
4. **Functions and data flow:** Django first renders only permitted links in the shared sidebar. The CSS media query receives the viewport width and hides `.nav-group-toggle`, while making `.nav-group-items` visible. `syncGroupAccessibility()` reads the same breakpoint and desktop collapse state, then sets each link container's `inert` and `aria-hidden` attributes. Mobile containers remain usable even when that section was collapsed on desktop. For example, a saved closed Facilities group becomes accessible at 390px without changing its saved desktop state.
5. **Backend/API:** no change to permissions, routes, counts or API responses. Hiding headings does not grant access.
6. **Database:** no records, migrations or installation commands changed.
7. **Verification:** the read-only Chrome check passed six viewport transitions: 1440 → 768 → 390 → 320 → 844 → 390px. It used a previously Django-rendered sidebar fixture, current shared CSS and current sidebar initialization script. All 19 fixture links retained accessible names; all six mobile group containers were visible and not inert, headings were hidden, and the isolated shell had no horizontal overflow. Desktop headings returned above 768px. This was not a live authenticated or physical-phone test. Run with the existing Node runtime: `node scratch/mobile-sidebar-check.cjs`.
8. **Limitations/debugging:** this is the responsive web admin menu. The Flutter drawer already has direct links rather than these section headings and was not changed. The web breakpoint uses viewport width: a landscape viewport above 768px uses desktop headings. If headings appear below that width, hard-refresh and check that the page loads the current `admin_layout.css`; browser caching is a possibility, not a confirmed cause. Safe exercise: use browser responsive mode to close a section at 1440px, resize to 390px, and confirm its links remain available; return to desktop and confirm its closed state is preserved. This changes only browser UI state and writes no application records.



Mobile navigation follow-up (October 17, 2026): Home | Marketplace | Services | Facilities | Profile now replaces the visible center + action; the drawer remains removed. Reusable quick-action code remains dormant. Services uses real active Django records and, by user choice, service-specific contact guidance rather than submission forms. See [Mobile Services navigation](mobile-services-navigation.md) for all current source files/lines, API behavior, data flow, tests, debugging and limitations.
