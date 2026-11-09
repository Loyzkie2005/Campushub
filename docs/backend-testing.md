# Backend test organization

Updated November 9, 2026. Scope: organize the existing backend tests and record
their original paths. Flutter tests and application behavior are outside this change.

## 1. Cause / reason

Django tests were mixed with models, views and services. Broad files named
`tests.py` also hid several feature suites. Some suites import reusable fixtures
from other test modules, so moving files without updating imports would break
test discovery. A test's folder is its feature ownership, not a claim that it passes.

## 2. Exact files changed

The complete, machine-readable move list is [backend-test-origins.json](backend-test-origins.json).
Each entry contains `original_path`, `current_path` and the SHA-256 of the
original working-tree bytes. This records the source before this reorganization;
it does not invent an author, Git revision or original creation date.
Moved Django files record their original location at **line 1** as well.

| Feature | Current folder | Original folder |
| --- | --- | --- |
| Accounts, recovery, permissions | `backend/core/accounts/tests/` | `backend/core/accounts/` |
| REST and mobile API | `backend/core/api/tests/` | `backend/core/api/` |
| Media serving | `backend/core/core/tests/` | `backend/core/core/` |
| Marketplace, orders, inventory, bundles | `backend/core/modules/marketplace/tests/` | `backend/core/modules/marketplace/` |
| Facilities, bookings, services | `backend/core/modules/facilities/tests/` | `backend/core/modules/facilities/` |
| Reports and dashboards | `backend/core/modules/reports/tests/` | `backend/core/modules/reports/` |
| Django chat authentication bridge | `backend/core/modules/messages/tests/` | `backend/core/modules/messages/` |
| Push notifications | `backend/core/modules/notifications/tests/` | `backend/core/modules/notifications/` |
| User management placeholder | `backend/core/modules/user_management/tests/` | `backend/core/modules/user_management/tests.py` |
| SSH-monitor unit tests | `backend/tests/` | `backend/test_kamatera_db_tunnel_monitor.py` |

FastAPI already uses `backend/chat_service/tests/`; it stays in that location.
The API browser-check JavaScript helper moved alongside its Python test so
`Path(__file__).with_name(...)` still resolves the same helper.
`api/management/commands/test_gmail.py` remains a real management command in its
original location; its filename does not make it an automated test suite.

Descriptive names replace the generic or inconsistent filenames:

| Original | Current |
| --- | --- |
| `accounts/tests.py` | `accounts/tests/test_admin_workflows.py` |
| `api/tests.py` | `api/tests/test_api_contracts.py` |
| `modules/marketplace/tests.py` | `modules/marketplace/tests/test_product_administration.py` |
| `modules/marketplace/test_orders_admin.py` | `modules/marketplace/tests/test_admin_orders.py` |
| `modules/marketplace/test_thresholds.py` | `modules/marketplace/tests/test_low_stock_thresholds.py` |
| `modules/reports/tests.py` | `modules/reports/tests/test_marketplace_analytics.py` |
| `modules/messages/tests.py` | `modules/messages/tests/test_chat_authentication.py` |

These table paths are relative to `backend/core/`. Existing descriptive filenames
such as `test_fifo_inventory.py` and `test_bundle_monitoring.py` remain recognizable.
Empty `tests.py` placeholders became package `tests/__init__.py` files; they did
not contain executable tests. Other `__init__.py` files deliberately do not
import TestCase classes, which would cause duplicate discovery.

Current implementation anchors (also relative to `backend/core/`):

| File and current line | Nearby anchor | Reason |
| --- | --- | --- |
| Every relocated Django file, line 1 | `# Original location:` | Record the source path beside the test itself. |
| `modules/marketplace/tests/test_admin_orders.py:20` | `OrdersAdminTests` | Existing admin order suite under its new name. |
| `modules/marketplace/tests/test_bundle_monitoring.py:16` | `from modules.marketplace.services.bundle_monitoring import` | Import the original service after moving one folder deeper. |
| `modules/marketplace/tests/test_inventory_monitor.py:192` and `:253` | `parents[4]` | Preserve the two existing image-fixture lookups. |
| `modules/facilities/tests/test_service_configuration.py:370` | `parents[4]` | Preserve the service image-fixture lookup. |
| `modules/reports/tests/test_dashboard_bookings.py:15` | `from accounts.tests import test_admin_workflows as fixtures` | Keep the existing shared dashboard fixture. |
| `api/tests/test_seller_recommendations.py:13` | `from api.tests import test_mobile_seller_workspace as fixtures` | Keep the existing seller fixture. |

## 3. Changes made

- Relocated 82 Django source files, one browser helper and one infrastructure
  test file. No test assertion or feature implementation was removed.
- Updated relative imports to explicit application or test-package imports.
- Updated cross-suite fixtures, including dashboard fixtures from
  `accounts.tests.test_admin_workflows` and seller fixtures from
  `api.tests.test_mobile_seller_workspace`.
- Adjusted image-file lookup depth in inventory-monitor and service-configuration
  tests from `parents[3]` to `parents[4]`; the target remains the same existing
  `backend/static/assets/img/icon.png`.
- Added this guide, folder READMEs and the origin index.
- Added [backend-test-results.json](backend-test-results.json), a dated status
  snapshot for every discovered Django test module, plus unsuccessful test IDs.
  `run`, `passed`, `failures`, `errors` and `skipped` come from actual execution;
  `status` summarizes those counts, not a permanent quality guarantee. Original
  paths and test outcomes stay in separate indexes so a move cannot imply a pass.

## 4. How it works

Django discovers `test*.py` recursively inside each `tests/` package, imports its
TestCase classes and runs their existing `test_*` methods. Tests prepare temporary
fixtures, invoke the existing Django functions/views or test HTTP client, and
compare actual results with their existing assertions. This move changes module
locations, not request inputs, expected responses or application data flow.

For example:

```python
# Before: sibling test module beside the API views.
from api import test_mobile_seller_workspace as fixtures

# Now: identical fixture class inside the API tests package.
from api.tests import test_mobile_seller_workspace as fixtures
```

`OrdersAdminTests` in `tests/test_admin_orders.py` still creates isolated users,
products and orders, calls the existing admin order endpoints, and checks scope,
history and operational confirmations. Its fixture methods and assertions were
preserved. FIFO and bundle tests retain their existing inventory and transaction
checks, including tests that currently fail.

## 5. Backend / API behavior

No runtime view, API route, authentication rule, application setting, Flutter
file or FastAPI implementation was changed by this organization. The unrelated
working-tree feature changes present before this task were preserved.

Run Django from `backend/core/` using the existing virtual environment:

```powershell
# Read-only system check.
.\venv\Scripts\python.exe manage.py check

# Feature, file, and individual-test labels in the new layout.
# Integration commands require an explicitly isolated LOCAL test configuration.
.\venv\Scripts\python.exe manage.py test modules.marketplace.tests --noinput
.\venv\Scripts\python.exe manage.py test modules.marketplace.tests.test_admin_orders --noinput
.\venv\Scripts\python.exe manage.py test modules.marketplace.tests.test_admin_orders.OrdersAdminTests.test_dashboard_fragment_requires_one_explicit_scoped_order --noinput

# Discover all Django suites with that same isolated configuration.
.\venv\Scripts\python.exe manage.py test --noinput
```

From the repository root, infrastructure tests need no real database or SSH:

```powershell
backend/core/venv/Scripts/python.exe -m unittest discover -s backend/tests -t backend -v
```

Old feature guides may show historical dotted labels such as
`modules.marketplace.test_orders_admin`. Use the current label above or look up
the original file in the origin index. Do not recreate compatibility copies of
the old tests; those would run the same tests twice.

## 6. Database / migration impact

No `.env`, database selection, model, migration, application account, product,
order, payment or inventory record was changed by this task. Integration
verification used guarded, uniquely named **disposable PC PostgreSQL test
databases** on loopback port 5432. The runner verified the actual server address,
port and database identity before setup and confirmed the new test database
identity afterward. Only those disposable databases receive test migrations and
fixture writes; no online migration, application database reset or seeding ran.

The one-time audit runner lives at ignored
`scratch/test-organization-20261109/run_local_tests.py`. It reuses the project's
existing legacy unmanaged-table bootstrap from `DedicatedDomainDashboardTests`;
this organization does not redesign that pre-existing setup. The audit runner
is local verification evidence, not a newly configured default Django runner.
Standard commands above need the project's appropriate isolated local setup.
Never substitute an online/shared application database for that setup.

## 7. Tests performed

- Django discovery before and after: **1,477 test IDs**, with identical identities
  after normalizing only the documented module moves; **zero duplicate IDs**
  and **zero import errors**.
- AST comparison: all **83 relocated Python files** preserve their executable
  syntax except relocated imports and the three image-path depth adjustments.
  The browser helper is byte-for-byte unchanged. All 1,387 directly declared
  Django/infrastructure test methods remain; inherited methods explain why the
  discovered Django count differs from directly declared methods.
- Marketplace baseline: **355 run, 323 passed, 22 failed, 10 errored** in 51.788s.
- Marketplace after organization: **355 run, 323 passed, 22 failed, 10 errored**
  in 53.581s. The exact same 32 unsuccessful test identities occurred before
  and after relocation; assertions were not weakened to make them green.
- Infrastructure: **9 passed**; no real SSH process, sleep or database writes.
- FastAPI: **9 passed**, one dependency warning, in 1.15s. Existing SQLite fixtures
  were confined to an ignored temporary working directory, not an application DB.
- Django system check: **no issues**.
- Full Django execution: **1,477 run: 1,437 passed, 28 failed, 11 errored,
  1 skipped**, in 382.271s. The disposable database was destroyed afterward.
  Of 79 Django test modules, 67 passed completely, 11 contain failures/errors,
  and the opt-in browser module was skipped. Per-module counts and all
  unsuccessful IDs are in [the actual status report](backend-test-results.json).
- Original-source follow-up: the seven unsuccessful non-marketplace tests were
  rerun from the saved original files under their old module names. Five failed,
  one errored, and the signature-concurrency test passed. Together with the
  marketplace baseline, **38 of the 39 unsuccessful full-run test IDs were
  reproduced from original source**. The signature test also passed alone from
  its relocated source; its full-suite fixture received 403 instead of 201.
  This suggests a suite interaction, but its cause remains unconfirmed.

Suites requiring attention (paths below are relative to `backend/core/`):

| Current test module | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| `accounts/tests/test_roles_permissions.py` | 25 | 2 | 0 | 0 |
| `api/tests/test_facility_rental_configuration.py` | 53 | 1 | 0 | 0 |
| `api/tests/test_facility_schedule_live_browser.py` | 0 | 0 | 0 | 1 |
| `modules/facilities/tests/test_job_order_signatures.py` | 31 | 1 | 0 | 0 |
| `modules/marketplace/tests/test_admin_orders.py` | 23 | 2 | 0 | 0 |
| `modules/marketplace/tests/test_bundles.py` | 10 | 8 | 3 | 0 |
| `modules/marketplace/tests/test_fifo_concurrency.py` | 2 | 4 | 0 | 0 |
| `modules/marketplace/tests/test_hybrid_inventory.py` | 6 | 0 | 6 | 0 |
| `modules/marketplace/tests/test_low_stock_thresholds.py` | 9 | 1 | 0 | 0 |
| `modules/marketplace/tests/test_variant_inventory.py` | 5 | 7 | 1 | 0 |
| `modules/reports/tests/test_dashboard_marketplace.py` | 23 | 0 | 1 | 0 |
| `modules/reports/tests/test_sales_overview.py` | 21 | 2 | 0 | 0 |

Audit logs, original-file snapshots, discovery inventories and comparison JSON
are ignored under `scratch/test-organization-20261109/`. The origin index contains
only repository paths and hashes, not credentials or database connection strings.

## 8. Remaining limitations and troubleshooting

The marketplace suite is **not fully passing**. Confirmed pre-move failures/errors
remain in bundle ordering, hybrid inventory, variant handling, admin orders,
low-stock checks and concurrency. Their root causes were not investigated or
fixed as part of moving files. Do not use a folder called `working/`, skip marks,
deleted assertions or test renaming to conceal these results.
The full-suite signature fixture failure remains unresolved; its isolated pass
must not be used to erase the full-run failure. The other six non-marketplace
unsuccessful tests reproduced from original source as described above.

If a module cannot be found, check that the command uses `.tests.test_...` and
that the package has `__init__.py`. For an asset error, check the existing bundled
image and the updated depth. For missing unmanaged tables, use the existing
isolated setup/bootstrap rather than creating tables in a working database.
The browser test remains opt-in and requires its existing Playwright configuration;
ordinary discovery is not proof that a real browser test ran.

Safe learning exercise: open `modules/marketplace/tests/test_admin_orders.py`,
read its line-1 original-path comment, and find the matching JSON entry. Run the
single test command above against an isolated local test database. Compare its
result with the recorded baseline; do not alter live orders or delete a failing
test. Add future tests as `test_<feature>.py` under the owning app's `tests/`
folder and rerun discovery to verify the new test appears exactly once.
