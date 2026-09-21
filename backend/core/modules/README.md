# CampusHub Core Modules

Feature-based layout for the Django admin panel and shared business logic.

## Quick links

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — full folder map and where to add code
- **`*/migrations/README.md`** — which Django migrations belong to each domain

## Modules

| Module | Purpose | Migrations |
|--------|---------|------------|
| `user_management` | Login, users, roles, backup UI | `accounts/migrations/` |
| `marketplace` | Products, orders, variations | `api/migrations/` (see module README) |
| `facilities` | Facilities, booking UI | `api/migrations/` |
| `notifications` | Alerts, Gmail email | `api/migrations/` |
| `messages` | Admin messaging UI | none yet |
| `reports` | Dashboard, generate reports | none yet |

## Services (business logic)

- `marketplace/services/` — inventory, customization, product images, recommendations
- `notifications/services/` — email delivery
- `facilities/services/` — reserved for booking helpers

Legacy `api/*.py` files re-export these modules so older imports keep working.
                 