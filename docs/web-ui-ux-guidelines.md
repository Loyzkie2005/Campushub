# CampusHub global web UI/UX rules

Effective October 22, 2026. These are the user's standing rules for every CampusHub web interface created or modified. They guide work within its requested scope; they do not request an immediate redesign of every existing page. The source attachment ends with the incomplete phrase “Use restrained”; no missing requirements are inferred from that fragment.

## Scope and approach

Inspect the current implementation first. Reuse shared CSS, layouts, cards, tables, forms, navigation, typography and tokens. Preserve visual consistency, backend/business logic, permissions and verified USTP workflows. Do not redesign unrelated modules. Apply UX principles only where they improve clarity, navigation, hierarchy, accessibility and task completion, not as mechanical formulas.

Latest explicit page choices still apply. The October 24 request removes the Super Admin System Health strip and Check status control; Welcome is now first. This supersedes the earlier top-strip choice. The latest approved October 24 layout places Attention Required directly below the eight KPIs inside the left System Overview column; saved recommendations remain right on desktop and follow Attention when stacked. Do not add a replacement footer status section. The Dashboard remains the Super Admin recommendation entry point, Marketplace Admin retains its authorized detailed workspace; the approved October 25 dashboard update uses Suggested Product Bundles as its summary heading, and seller navigation stays separate. The October 24 Products request explicitly uses Montserrat for product content/modals; shared navigation and other web UI retain Inter. Visibility of task status also means useful action/loading/error feedback; it does not authorize unrelated health components.

## The 20 principles

1. **Jakob's Law — familiar patterns.** Use established administrative patterns for sidebar navigation, headers, KPI cards, tables, filters, search, forms, dropdowns, modals, pagination, charts, breadcrumbs and status indicators. Prefer the existing interaction when it already serves the task.
2. **Miller's Law — meaningful chunks.** Group related information rather than overloading a long unstructured page. Marketplace may group sales summary/trend, top products, recent orders and inventory alerts; Facilities may group booking summary/trend, facility rankings, reservations and attention; Services may group summary/trend, service distribution, recent requests and attention. This is not a strict seven-item maximum or a requirement to add every example to every screen.
3. **Hick's Law — necessary choices.** Prefer one primary action, a few secondary actions and an overflow menu for uncommon actions. Do not crowd the same surface with View, Analyze, Report, Download, Open, Inspect, Details and History. Show actions appropriate to the role and actual record state.
4. **Fitts's Law — usable targets.** Give buttons, icon controls and table action menus comfortable hit areas. Make primary/frequent actions easy to find and operate; avoid tiny essential text links or hiding frequently needed controls.
5. **Gestalt proximity.** Keep values near labels, titles near charts and filters near the records they affect. Do not combine unrelated information in a card.
6. **Gestalt common region.** Use containers to group related content. Prefer a light conceptual section wrapper with individual content cards over multiple layers of large nested cards. The parent section should remain visually quieter than its content.
7. **Gestalt similarity.** Keep comparable KPI structures, View All links, status treatments, table headers and chart presentations consistent across modules.
8. **Prägnanz — simple presentation.** Keep CampusHub calm, structured and institutional. Avoid decorative complexity, unnecessary elements, redundant information, excessive borders/shadows and charts more complex than the question requires.
9. **Tesler's Law — handle technical complexity.** Present understandable system language instead of unnecessary raw database IDs, internal status codes or API information. Keep Apriori Support, Confidence and Lift out of ordinary interfaces; authorized research/manuscript analysis stays separate. Useful human-facing booking/order/suggestion references may remain when needed for the task.
10. **Nielsen: visibility of system status.** Distinguish loading, success, error, empty and unavailable states. Clearly show actual pending, approved, rejected, processing and completed states where the workflow supports them. Give feedback after actions; never imply that an error is successful empty data.
11. **Nielsen: match the real world.** Use understandable labels such as Pending Approval, Completed Order, Low Stock, Upcoming Reservation, Service Request and Bundle Suggestion. Match actual CampusHub workflows and USTP documents, not developer terminology.
12. **Nielsen: consistency and standards.** Use consistent terms, components, spacing, fonts and behavior. Do not rename the same concept to unfamiliar terms such as Product Association Items on another screen. Preserve deliberate role-specific labels when they clarify the role's task.
13. **Nielsen: error prevention.** Validate inputs, block invalid actions, prevent duplicate booking/invalid stock and confirm genuinely destructive or irreversible operations when appropriate. Hide or disable actions invalid for the record state, while retaining server-side enforcement.
14. **Nielsen: recognition over recall.** Provide clear labels, visible status, breadcrumbs, selected filters, helpful descriptions, contextual actions and understandable icons. Users should not need to memorize previous screens or guess ambiguous icons.
15. **Progressive disclosure.** Show summaries first; open details when requested. Dashboard → Marketplace Overview → View Analytics → detailed Analytics, or Dashboard → recommendation panel → View Recommendations → existing detailed workspace. Do not crowd every detail onto the dashboard or create a duplicate destination.
16. **Visual hierarchy.** Make the current page, important information, attention items and next action clear. Use title, supporting description, primary action, important summary/KPIs, primary content, secondary content and supporting information as appropriate. Do not give all text identical prominence or force this order against a specific user-approved layout.
17. **Dashboard information hierarchy.** Organize section → summary → trend/comparison → operational information → details. Marketplace examples are sales KPIs, sales trend line, top-product bars, recent-order table and inventory alerts. Apply comparable organization to Facilities/Services where useful, without inventing missing data or functionality.
18. **Honest empty states.** Avoid large blank cards and generic No Data when a specific explanation is available. Use a small relevant icon, clear title and concise description. Keep No Recent Orders with “New marketplace orders will appear here once customers begin placing orders.” and No Inventory Alerts with “Products requiring stock attention will appear here.” Never fabricate records to fill a card.
19. **Purposeful data visualization.** Use lines for time trends, vertical bars for a few categories, horizontal bars for long names/many categories, and pie/donut charts sparingly for meaningful part-to-whole questions. Charts must explain real data, not decorate the page. Keep dashboard charts limited; detailed analysis belongs in Reports → Analytics.
20. **Accessibility / WCAG.** Verify contrast, visible focus, keyboard access, meaningful labels, readable typography, understandable validation and adequate target sizes. Status must have text or another non-color cue. A palette alone is not proof of accessibility.

## Web visual system

| Role | Color |
| --- | --- |
| Primary navy | `#1A1851` |
| Gold accent | `#FCB316` |
| White surface | `#FFFFFF` |
| Background | `#F7F8FC` |
| Primary text | `#17172A` |
| Secondary text | `#667085` |
| Muted | `#98A2B3` |
| Border | `#E8EAF0` |

Use the configured bundled Inter for web UI and SugarPie only for the CampusHub wordmark. Check actual contrast before assigning the muted color to text: necessary instructions, values and controls must remain readable; use a darker existing text token where required. Preserve meaningful existing status semantics without introducing random multicolor badges. Avoid gradients, glassmorphism and excessive shadows. These web tokens do not change Flutter's existing typography, identity fonts or gold token.

Reuse/extend existing shared tokens when implementing a requested UI change. Recording these rules does not itself require replacing every existing hardcoded value or changing colors globally in runtime files.

## Applying the rules to existing code

No runtime function is added by this guide. Normal data flow stays Django permission-checked view/query → existing template/context or API response → existing UI renderer/component → visible text, values and feedback. The rules affect how that existing output is presented, not the calculations or authorization inputs.

For example, `system_overview_summary.html` receives the same real KPI and recommendation context. Its named `bundle_monitor_list` link opens the existing workspace; progressive disclosure does not require another controller, duplicate search or additional mining request. The shared empty-state partial takes a title, description and icon; a real empty projection controls its visibility, while errors remain errors.

Before handoff, inspect the touched screen's populated, empty, loading and error paths where applicable. Check role/state actions, keyboard/focus, contrast, responsive layout, selected filters, real data and whether navigation still reaches its existing destination. Run appropriate existing checks; report exactly what was run and any unavailable browser/device verification. Do not claim that all pages comply because this policy was saved.

Safe practice exercise: inspect the Dashboard View Recommendations link, resolve its named route and verify it opens the existing list. Identify the summary, detail destination and role gate without editing files or creating data. This demonstrates progressive disclosure, familiar navigation and preserved backend authority.

## Adoption record

1. **Reason:** The user supplied global rules for subsequent web UI work.
2. **Files:** `docs/web-ui-ux-guidelines.md` records the complete actionable principles; `AGENTS.md` links the mandatory web guidance and updates Section 3's web palette; `CAMPUSHUB_CONTEXT.md` records adoption.
3. **Changes:** Persisted the standing policy, including the web gold/background/text/border values and the existing Inter/wordmark distinction.
4. **How it works:** Future web UI tasks read this guide alongside project context before changing relevant implementation; no runtime code reads this Markdown.
5. **Backend/API:** No business logic, permission or endpoint changes.
6. **Database/migrations:** None; no application records, environment, deployment or mobile files changed.
7. **Verification:** Reviewed the attachment, existing guidance and scope; checked that all 20 principle sections are represented and links/files resolve. Application tests are not needed for this documentation-only adoption.
8. **Limits:** The attachment ends mid-phrase. No further rules were invented. This records future-work guidance; it neither retroactively redesigns unrelated pages nor certifies accessibility or visual compliance of the current app.
