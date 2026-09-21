# Product

<!-- impeccable:product-schema 1 -->

## Platform

adaptive

## Users

CampusHub serves the USTP community. Students, faculty members, and guest or external users use the Flutter mobile application to access campus services. Super Admin, Marketplace Admin, and Facilities Admin users operate the Django web administration interface to manage the parts of the system allowed by their roles.

Primary mobile jobs include discovering and ordering campus marketplace products, requesting seller access, finding and reserving facilities, managing account information, and communicating with sellers or administrators. Administrative jobs include managing users and permissions, marketplace records and orders, facilities and bookings, reports, system activity, and operational settings.

## Product Purpose

CampusHub unifies campus marketplace ordering, seller management, facility discovery and reservations, messaging, notifications, reporting, and role-based administration in one platform for USTP.

Success means that members of the USTP community can complete common campus transactions from the mobile application while authorized administrators can monitor and manage those transactions from the web interface without relying on disconnected tools or duplicate records.

## Positioning

CampusHub combines USTP-specific marketplace and facility workflows under one account and role model. Its defining mechanism is the connection between the student-facing mobile experience and the role-scoped administrative system, with shared operational data rather than separate marketplace, reservation, messaging, and reporting tools.

## Operating Context

- Mobile users access CampusHub from Android devices on campus networks, mobile data, or a phone hotspot.
- Administrators use the browser-based control panel for repeated operational work such as reviewing products, orders, seller requests, facilities, bookings, users, permissions, activity, and reports.
- Marketplace transactions use the implemented CampusHub order and pickup workflow.
- Facility operations include availability, schedules, booking approval, payments, utilization, and related reporting where real records exist.
- Messaging is a real-time service shared by the web and mobile clients.

## Capabilities and Constraints

- The web administration interface and REST API use Django.
- The mobile application uses Flutter.
- PostgreSQL is the system database.
- FastAPI is used only for chat, with PostgreSQL-backed chat records and WebSocket delivery.
- Django authentication, secure password hashing, role-based access control, and existing account protections must be preserved.
- Existing PostgreSQL tables, migration history, relationships, and compatibility with Flutter-authenticated users must not be broken by interface work.
- Core domains include accounts and roles, marketplace products and orders, seller access, facilities and bookings, messaging, notifications, reports, activity monitoring, and backup and restore.
- Product recommendations use existing interaction data and the implemented recommendation service; recommendations must not be presented as demand forecasting.
- Demand or stock forecasting is not yet a confirmed implemented capability and must not be shown as operational until a real model, training data, evaluation, and workflow exist.
- Notification functionality is incomplete and must not be represented as fully operational until its delivery behavior is implemented and verified.
- Hosting and always-online availability are deployment concerns; local development servers must not be described as production hosting.

## Brand Commitments

- Preserve the product name `CampusHub` and its existing logo assets.
- Use USTP and campus terminology accurately.
- Keep interface language direct, basic, and task-oriented.
- Administrative screens should prioritize operational clarity and efficient repeated use.
- Mobile screens should prioritize straightforward campus transactions and clear status feedback.

## Evidence on Hand

- Existing Django templates, views, models, migrations, tests, and static assets under `backend/` are the source of truth for web and API behavior.
- Existing Flutter screens, services, models, routes, tests, and assets under `campushub/` are the source of truth for mobile behavior.
- Existing FastAPI and Alembic files under `backend/chat_service/` are the source of truth for chat behavior.
- Existing database records may be displayed in the interface, but future design work must not fabricate users, activity, bookings, sales, availability, forecasts, reviews, testimonials, or performance claims.

## Product Principles

1. Keep campus services unified while preserving clear ownership boundaries between marketplace, facilities, users, and messaging.
2. Show real system state and meaningful empty states instead of fabricated demonstration data.
3. Make permissions and account status explicit so every administrator understands the effect of an action before confirming it.
4. Preserve web, mobile, API, database, and chat compatibility when changing any shared workflow.
5. Optimize operational interfaces for scanning, comparison, and repeated action, and mobile interfaces for focused task completion.
