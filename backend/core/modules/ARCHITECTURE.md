# CampusHub module layout

Feature code is grouped under `backend/core/modules/`. Django **database migrations** stay in the legacy apps (`api`, `accounts`) so existing PostgreSQL data and `django_migrations` history remain valid.

## Folder map

```
backend/core/
├── accounts/              # Auth ORM + migrations (User, Role, permissions)
├── api/                   # Shared ORM + migrations (Product, Facility, Order, …)
│   └── views.py           # Mobile + REST API entrypoints
└── modules/
    ├── user_management/   # Admin login, users, roles, backup UI
    ├── marketplace/       # Products, orders admin UI + services
    ├── facilities/        # Facilities, booking admin UI
    ├── notifications/     # Notifications admin UI + email service
    ├── messages/          # Messages admin UI
    └── reports/           # Dashboard + reports UI
```

## Where to put new code

| Feature | Templates | Business logic | DB migrations |
|---------|-----------|----------------|---------------|
| Products / orders | `modules/marketplace/templates/marketplace/pages/` | `modules/marketplace/services/` | `api/migrations/` |
| Facilities / booking | `modules/facilities/templates/facilities/pages/` | `modules/facilities/services/` | `api/migrations/` |
| Users / roles | `modules/user_management/templates/user_management/pages/` | `accounts/` (views, role_permissions) | `accounts/migrations/` |
| Email / alerts | `modules/notifications/templates/notifications/pages/` | `modules/notifications/services/` | `api/migrations/` |
| Dashboard / reports | `backend/templates/dashboard/pages/` and `modules/reports/templates/reports/pages/` | `modules/reports/views.py` | — (reads shared models) |

## Template and static-file convention

Keep every Django template root named `templates`; Django uses that name for
automatic app template discovery. Organize files below that root as follows:

```text
modules/<feature>/
|-- templates/<feature>/
|   |-- pages/              # complete browser pages
|   `-- components/         # feature-only includes
|-- static/<feature>/       # module dashboard CSS and JavaScript
|   |-- css/
|   `-- js/
|-- services/               # business logic, no HTML
`-- views.py                # request handling and template context

backend/core/templates/
`-- partials/               # shared header, sidebar, menus, and row actions

backend/static/components/
|-- css/                    # page and shared styles
`-- js/                     # page and shared behavior
```

Use namespaced template paths in views, for example:

Marketplace and Facilities dashboards live in their respective module template
and static directories. Their shared dashboard dispatcher and data aggregation
remain in `modules/reports/views.py`; the Super Admin dashboard remains in
`backend/templates/dashboard/pages/`. Django discovers module static files
through its app static-file finder without additional settings.

```python
return render(request, "marketplace/pages/admin_orders.html", context)
```

Do not rename a module's `templates` directory to `pages`. `pages` belongs
inside the module namespace so Django can discover it without extra settings.

## Import conventions

```python
# Marketplace logic
from modules.marketplace.services.inventory import get_product_inventory_status
from modules.marketplace.models import Product

# Legacy imports still work (thin shims in api/)
from api.inventory import get_product_inventory_status
```

## Why migrations are not split yet

Moving models from `api` → `modules.marketplace` would require a planned Django app migration (SeparateDatabaseAndState + data copy). Doing that mid-capstone risks breaking the database. Each module’s `migrations/README.md` lists which `api` or `accounts` migrations apply.

## Apply migrations

```bash
cd backend/core
python manage.py migrate accounts
python manage.py migrate api
python manage.py migrate campushub_marketplace_module
python manage.py migrate campushub_facilities_module
# … other module labels (empty 0001_initial only)
```

Module app labels: see `apps.py` in each module (`label = 'campushub_*_module'`).
