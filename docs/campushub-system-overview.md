# About CampusHub

CampusHub is a campus marketplace and facilities booking system with real-time availability monitoring and an analytics dashboard for the University of Science and Technology of Southern Philippines - Oroquieta Campus.

This file explains the system's purpose, modules and data flow. Code changes, debugging notes and test results belong in the separate implementation guides linked below.

## Purpose

CampusHub brings campus product sales, facility reservations and specialized service requests into one system. Mobile users submit requests and track their records, while authorized web administrators manage the relevant operations. Dashboards summarize recorded activity and provide links to the detailed workspaces.

## Applications and architecture

| Part | Technology | Responsibility |
| --- | --- | --- |
| Web administration and main backend | Django | Products, orders, facilities, bookings, accounts, permissions, reports and decision support. |
| Main API | Django REST Framework | Exchanges authorized application data with the mobile app. |
| Mobile app | Flutter / Dart | User-facing marketplace, booking and account experiences. |
| Database | PostgreSQL | Stores application records; pgAdmin is a management tool for PostgreSQL. |
| Chat service | FastAPI | Messaging only; marketplace and booking business rules remain in Django. |

Hosting PostgreSQL on a remote server does not change its database engine. The app's API address, Django's database connection and the chat service address are separate configuration concerns.

## Accounts and access

Account types include Student, Faculty/Employee, Guest/External and Admin. Seller access is a separate approval status rather than an account type.

Super Admin oversees the system. Marketplace Admin and Facility Admin work within their existing permissions and assigned scope. Django enforces access on the server; hiding a menu item alone does not grant or protect access.

Where marketplace Program/Major scoping applies, it follows the existing seller/product relationships, not the buyer's Program/Major.

## Main modules

### Marketplace

The marketplace covers products, seller access, variants, inventory and orders. Its payment method is **Cash on Pickup**.

The established order flow is Pending, Confirmed/Processing, Ready for Pickup, then Completed, with cancellation handled by the existing workflow. Eligible completed and paid transactions supply marketplace sales analytics. Pending or unpaid order values must not be described as collected sales.

### Facilities

Facilities supports reservations and availability checking. Booking behavior depends on the facility: event/slot reservations differ from accommodation bookings and specialized requests. A facility being **Open for Booking** does not mean every time slot is free.

Official approval, payment, document, inspection and completion steps follow the existing facility workflow. A dashboard layout change does not change those steps.

### Services

Specialized services such as Food Analysis, BPP Assessment and lease applications have their own requirements and processing steps. They must not be treated as ordinary event bookings merely because they use related campus resources.

For example, the approved Food Analysis procedure includes sample receiving checks, resource checks, job-order processing, analysis, cashiering and release of results. Refer to the project's verified workflow guidance before changing service behavior.

### Reports and decision support

Analytics summarizes recorded activity: sales trends, product rankings, booking demand, service requests and account registrations.

Suggested product bundles provide decision support using association rules generated with the Apriori algorithm. The Super Admin dashboard previews existing saved product combinations and seller responses; it does not run Apriori on every dashboard visit. Ordinary dashboard UI does not expose Support, Confidence or Lift.

Charts describe activity. They should not be labelled forecasts or trained AI models. Empty states appear when eligible records are absent; demonstration data must not be presented as real production activity.

## Super Admin dashboard

The current dashboard follows this reading order:

1. Welcome message and reporting-period controls.
2. System Overview KPIs, with Suggested Product Bundles beside them on desktop.
3. Attention Required, inside the left column directly below the KPI cards.
4. Marketplace Overview.
5. Facilities Overview.
6. Services Overview.
7. Users Overview.
8. Recent System Activities.

On desktop the System Overview row keeps approximately 70% for the KPIs and Attention Required on the left, with the saved recommendation panel on the right. On smaller screens the order is KPIs, Attention Required, then recommendations. Both columns use their content heights.

The System Health display and Check status action were removed from this dashboard at the user's request on October 24, 2026. Existing protected health checks remain backend functionality.

Major headings and subtitles sit outside individual content cards. Chart and list titles stay inside their cards. The recommendation companion keeps its title inside its own card.

The recommendation panel previews up to two current eligible saved product pairs, with real product photos or placeholders, names, seller and saved response/delivery state. Separate counts show Sent to Sellers, Awaiting Seller Response and Bundles Created. Its View Recommendations link opens the existing detailed workspace; the Super Admin dashboard has no send/create/approve/reject actions.

## How data reaches the dashboard

The browser requests the dashboard from Django. Existing view and helper functions apply authorization, reporting dates and eligibility rules, then read PostgreSQL records. Django passes the results to templates and existing chart scripts. Date-filter refreshes use the existing dashboard API.

Relevant implementation entry points:

| File / anchor | Inputs and outputs |
| --- | --- |
| `backend/core/modules/reports/views.py` - dashboard view and `admin_dashboard_page` route | Authenticated request and selected filters enter; dashboard context and HTML leave. |
| `backend/templates/dashboard/partials/executive_dashboard.html` - `data-executive-dashboard` | Receives existing dashboard context; includes the Super Admin sections in reading order. |
| `backend/core/modules/marketplace/services/bundle_suggestions.py` - `dashboard_bundle_suggestions(user, limit=...)` | Receives the authorized user and preview limit; returns saved recommendation presentations and activity counts without mining on GET. |
| `backend/core/modules/marketplace/services/bundle_monitoring.py` - `presentation(row)` and `activity_summary(user)` | Maps actual saved relationships into product/seller/response text and aggregates saved workflow activity. |

For example, an eligible paid order can contribute to recorded marketplace revenue. Opening the dashboard reads the resulting totals; it does not create another order. Likewise, showing a saved bundle suggestion does not send it to a seller.

## Further reading

- [Dashboard implementation, layout, verification and troubleshooting](dashboard-analytics-operations-update.md).
- [Saved bundle recommendations and seller-response behavior](suggested-product-bundles.md).
- [Marketplace Admin dashboard](dashboard-marketplace-design.md).
- [Global web UI/UX rules](web-ui-ux-guidelines.md).
- [Project context and reference history](../CAMPUSHUB_CONTEXT.md).
- [Project engineering and verified workflow rules](../AGENTS.md).

## Safe learning exercise

Open `executive_dashboard.html` and match its includes to the dashboard sections listed above. Then open the recommendation panel partial at `backend/core/modules/marketplace/templates/marketplace/partials/super_recommendation_preview.html` and identify its product loop, three activity labels and existing View Recommendations link. This is read-only: verify the names against the running page without creating orders, changing records or generating example recommendations.

## Documentation scope

Created October 24, 2026 to separate the system explanation from engineering reports. This update adds documentation and cross-links only. Application code, APIs, permissions, database schema and records are unchanged. Runtime tests are unnecessary for this documentation-only change; link targets and referenced files are checked separately. This overview is not a claim that every planned capstone feature is already deployed or that every workflow has been audited.
