# Admin sidebar: white theme

## Sugar Pie wordmark on web login and sidebar — 2026-10-20

1. **Cause / reason:** The user wanted the same CampusHub lettering as the phone. Flutter already bundles `Sugar-Pie-W00-Regular.ttf` as SugarPie; the web login used Montserrat, and the sidebar had several important Montserrat overrides. The wordmark rules below supersede the historical Montserrat wordmark references later in this guide.
2. **Exact files:** Added `backend/static/assets/fonts/Sugar-Pie-W00-Regular.ttf`, copied byte-for-byte from `campushub/assets/fonts/Sugar-Pie-W00-Regular.ttf`. Added `backend/static/components/css/campushub_brand.css:2` (`@font-face`), line 10 (scoped font selectors), line 21 (sidebar size), and line 26 (Campus/Hub colors). `backend/core/modules/user_management/templates/user_management/pages/admin_login.html:17` links it after the existing login CSS; `backend/templates/partials/admin_sidebar.html:2` links it for every shared-sidebar page. `scratch/dashboard-executive/verify_brand_font.js:1` owns isolated browser/static checks. This guide records the change.
3. **Changes made:** SugarPie regular weight, zero letter spacing and no synthetic bold/italic apply only to the CampusHub wordmark and its two spans. Sidebar wordmark uses 24px, matching the mobile wordmark's nominal size. Sidebar Campus is navy #1A1851 and Hub is gold #FCB315, matching the phone on white; login already used that color arrangement. Existing icon images, menu labels, headings and form text remain unchanged.
4. **How it works:** Django's existing `{% static %}` tag resolves a versioned `campushub_brand.css` link. Its `@font-face` requests the bundled TTF at `../../assets/fonts/Sugar-Pie-W00-Regular.ttf`, relative to the CSS file. Scoped selectors override the sidebar's existing important font declarations, including the wordmark's child spans, without overriding ordinary text. Example: `.sidebar-logo .sidebar-logo-text span` resolves to SugarPie while a neighboring `.sidebar-item` keeps its existing font. No new application function or API is needed; input is existing Campus/Hub markup and the font file, output is the rendered wordmark. The link in the shared partial avoids changing every admin page stylesheet reference.
5. **Backend/API behavior:** No login submission, authentication, session, permission, navigation or backend view changes. No external font provider is required for Sugar Pie.
6. **Database/migrations:** None. Flutter assets and its existing typography implementation were not changed.
7. **Checks performed:** SHA-256 confirms the web font exactly matches the bundled mobile font. Isolated Chrome verified that the actual SugarPie face loaded, both wordmark spans resolve to it at weight 400, and normal text does not inherit it. Login checked at 1280, 390 and 320px without document overflow. Expanded sidebar checked at 1280px: navy/gold colors correct, wordmark fits before the collapse button, and collapsed state still hides it. Local Django returned HTTP 200 and matching bytes for both the font and versioned stylesheet. Screenshots were captured; the screenshot helper waits for the login's existing entrance animation before its final capture. Scoped whitespace check passed. No login was submitted, no database read/write and no app/server restart.
8. **Remaining limitations / troubleshooting:** A full signed-in navigation smoke test was not performed; the shared brand markup and production CSS were checked in isolation. Refresh the login/admin tab; if stale, use browser Ctrl+Shift+R. If a cursive fallback appears, check the font request in Network and the computed font on both spans. Do not change the site's global font to fix a wordmark issue. Safe practice: inspect `.login-brand-name` or `.sidebar-logo-text`, confirm SugarPie at weight 400, then inspect a form label/menu item and confirm its previous font. Collapse and expand the sidebar to verify the text still hides and returns without clipping.

Updated 2026-10-05.

Later update: all admin template stylesheet references now use the white theme version, and Voucher / Marketplace Analytics have been removed from sidebar navigation. See [the current implementation report](sidebar-navigation-white-all.md). The earlier cache limitation below is historical.

## 1. Cause / Reason

The user requested a white sidebar. Its previous white text, pale icons and white portion of the logo were designed for a navy background. Changing just the background would make those elements difficult to see.

## 2. Exact Files Changed

| Folder / file | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/static/components/css/admin_layout.css` | 46, `.sidebar` | White surface and subtle navy right border, using existing CSS variables. |
| Same CSS file | 112 and 134, `.logo-hub`; 117, `.sidebar-divider` | Navy Hub text and a thin navy divider on white. Campus text remains gold. |
| Same CSS file | 218, `.nav-group-title`; 277, `.sidebar-item` | Muted navy group headings and navy menu text/icons. SVG icons already inherit the text color through `currentColor`. |
| Same CSS file | 326, `.sidebar-item:hover`; 331, `:focus-visible`; 341, disabled hover | Neutral hover surface, navy text and a navy keyboard focus outline. Disabled menu items retain their disabled behavior. The existing gold active-menu style remains. |
| `backend/templates/partials/admin_sidebar.html` | 9, `sidebar-icon-img` | Switched to the existing navy-and-gold `assets/img/logo_light.png` image. No image asset was edited or added. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 12, `admin_layout.css` link | Updated the dashboard stylesheet cache version to fetch the white sidebar styling. |
| `CAMPUSHUB_CONTEXT.md` | 11, current admin sidebar preference | Saved the accepted sidebar colors for future work. |
| `docs/admin-white-sidebar.md` | 1 | Added this implementation and learning report. |

Generated review artifacts in `scratch/dashboard-global-review`: `white-sidebar-visual.html` plus desktop/collapsed/mobile `.png`, `.dom.html` and `.log` files. These are previews, not application code.

## 3. Changes Made

Changed the background, readable foreground colors, logo variant, border and hover state. Added a visible keyboard focus outline. No menu items were added, moved or removed; no navigation links or permission conditions changed.

## 4. How It Works

The shared admin stylesheet supplies the sidebar styling on pages that include it. `--campushub-surface` resolves to white, and `--campushub-navy` resolves to `#1A1851`. Existing SVG icons use `currentColor`, so changing the menu text color also changes the icons. The existing `.active` rule keeps a gold `#FCB316` background with navy text.

To check: open the dashboard, press Ctrl+F5, inspect the logo and menu, then collapse/expand the sidebar and narrow the browser. Use Tab to see the focus outline. Other admin pages that cached the old shared stylesheet may also need Ctrl+F5.

## 5. Backend / API Behavior

Unchanged. Django routes, authentication, role checks and server-side permissions retain their existing behavior. This is a shared CSS and logo-reference change.

## 6. Database / Migration Impact

No database changes, writes or migrations.

## 7. Tests Performed

The actual Django sidebar template rendered successfully with an in-memory preview context; no records were created. Three headless Chrome checks passed for expanded desktop (250px), collapsed desktop (64px) and mobile (64px). Checks verified white background, navy menu/Hub text, gold active item, loaded logo, visible focus outline and no horizontal overflow. The desktop screenshot was visually inspected. CSS parsing and the targeted `git diff --check` passed. No new automated application tests were added for this color-only change.

The UI/UX skill's verified contrast guidance recommends dark text on light backgrounds; the existing navy palette supplies that contrast.

Preview: [desktop sidebar](../scratch/dashboard-global-review/white-sidebar-desktop.png).

## 8. Remaining Limitations

The shared CSS affects admin pages that use this sidebar, rather than only the dashboard. Existing responsive/collapse dimensions and disabled-item opacity remain. Preview checks used the real sidebar template with all menu permissions enabled, not a signed-in browser session for each role. The dashboard cache version was updated; other open admin pages may require a hard refresh.
