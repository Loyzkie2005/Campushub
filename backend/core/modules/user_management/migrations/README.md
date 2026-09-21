# User management migrations index

**Schema owner:** `accounts` app (`backend/core/accounts/migrations/`)

| Migration | What it adds |
|-----------|----------------|
| `0001`–`0008` | Users, departments, roles |
| `0010`–`0011` | Role options, table renames |
| `0012_admintabtoken.py` | Per-tab admin sessions |
| `0013_role_granted_permissions.py` | DB-backed role permissions |
| `0014_split_facility_permissions.py` | Book vs manage facilities |
| `0015_split_product_permissions.py` | Buy vs manage products |

**Models:** `accounts.models` — `User`, `Role`, `Department`, `AdminTabToken`

**Admin UI:** `modules/user_management/templates/user_management/pages/`

**New migrations:** Add auth/permission changes under `accounts/migrations/`.
