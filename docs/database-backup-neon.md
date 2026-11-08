# PostgreSQL backups and server transfers

## Dashboard missing seller-delivery column — November 8, 2026

**Current status: fixed after the user explicitly approved “Apply only migration 0052”.** Applied only `api.0052_seller_delivery_setting` to the confirmed existing Kamatera database. There are no pending migrations. Read-only dashboard renders returned 200 for all four active admin accounts (two Marketplace Admins, one Facilities Admin, one Super Admin). All 48 tables' original row contents matched before/after, excluding only the intended new field and migration-history record. Refresh **http://127.0.0.1:8000/admin-dashboard/** in the existing signed-in browser.

### 1. Cause / reason

`backend/core/api/models.py:392`, `SellerRequest.seller_delivery_enabled`, exists in the current code. Kamatera has migrations through `api.0051_hybrid_inventory`, but not `0052_seller_delivery_setting`. The missing column was confirmed by read-only introspection. `backend/core/modules/reports/views.py:1070` iterates seller requests for dashboard approvals; line 1204 also loads seller requests for activities. A normal Django model query selects all concrete fields, including the missing delivery field, even when the dashboard only displays seller names/status. A read-only request using an existing active Super Admin reproduced `ProgrammingError` for that field without logging in or using the submitted browser token. This is confirmed schema drift, not a guessed template issue or failed PostgreSQL connection.

### 2. Exact files changed / current anchors

| File / current line | Anchor | Action |
| --- | --- | --- |
| `scratch/reconnect-kamatera-20261108/prepare_0052.py:1` | Read-only preparation script | Added ignored diagnostic/backup helper; no migration execution path. |
| `scratch/reconnect-kamatera-20261108/prepare_0052.py:90` | `columns` | Records original column order so later comparisons can exclude only the new column. |
| `scratch/reconnect-kamatera-20261108/apply_0052.py:11`, `:50`, `:71`, `:97` | Approval flag, `fingerprints`, targeted migrate, dashboard requests | Added ignored guarded application/verification helper, run only after explicit approval. |
| `docs/database-backup-neon.md:3` | This report | Record cause, exact pending SQL, backup verification, data flow and approval status. |
| `CAMPUSHUB_CONTEXT.md:3` | Dashboard migration note | Preserve current unresolved dashboard state. |

No Django application code, model, template, database configuration or migration source was changed. The required migration already exists at `backend/core/api/migrations/0052_seller_delivery_setting.py:4`, `class Migration`; that existing file was applied without modification. Helpers/results are local Git-ignored artifacts; the private backup is outside the repository.

### 3. Changes made

Reused the healthy existing SSH tunnel. First reproduced the error and prepared SQL/backup without executing schema changes. After the user explicitly approved only migration 0052, refreshed the full private backup, confirmed that the entire pending plan still contained only that migration, captured an immediate content baseline and ran the targeted existing Django migration. Used a five-second lock timeout and sixty-second statement timeout. Returned the helper's connection to read-only mode for preservation checks and protected dashboard renders. No application restart or remote source deployment was needed for this schema repair. No other migration, sample-data operation, delivery enablement, fulfillment/payment update or stock operation ran.

### 4. How it works / functions, inputs, outputs and data flow

The preparation script loads the active Django settings, requires `127.0.0.1:15432/campushub` and verifies the actual database/role with PostgreSQL read-only mode on. `MigrationExecutor` checks that the entire pending plan contains exactly `api.0052_seller_delivery_setting`. `call_command('sqlmigrate', 'api', '0052')` produces reviewable SQL; it does not execute schema changes. `RequestFactory` invokes the real protected dashboard view with an existing authorized account inside a read-only transaction; failure is caught and the transaction rolls back.

The script uses the same PostgreSQL client/active Django settings approach as the existing backup service, with literal subprocess arguments and the password only in the child environment. It creates a Windows directory accessible only to the current user, SYSTEM and Administrators before saving the SQL dump. It verifies pg_dump exit status, dump completion, size, table/data sections and SHA-256. Its aggregate JSON contains no credential, session token, response body or personal record contents. A separate private file stores table row counts/content hashes for later comparison; hashes are evidence of a snapshot, not a substitute for the backup.

`apply_0052.py` requires the explicit `--approved-0052` argument, the expected active target, exactly the one forward migration and a verified private backup checksum before enabling writes. `call_command('migrate', 'api', '0052_seller_delivery_setting', interactive=False)` applies that exact target through Django's normal migration lifecycle. The helper returns its connection to read-only mode afterward. This is an approved one-time operation, not a startup command; it refuses the plan once 0052 is already applied.

`fingerprints(ignore_new_migration=False)` reads original columns in their recorded order, converts complete rows to JSON, sorts row representations and returns table row-count/SHA-256 pairs. Calling it after migration with `True` omits only the new 0052 history row; projecting original columns also omits only the added seller field. Therefore, unchanged hashes verify original values, including users/auth, orders/payments, stock and permissions, without printing records. The new field and new history row are independently checked. Four actual active admins are then attached to `RequestFactory` requests for the existing protected dashboard view inside enforced read-only transactions; this does not create login sessions or reuse the user's submitted token.

```text
GET /admin-dashboard/ -> admin_dashboard_page -> SellerRequest queryset
 -> PostgreSQL SELECT includes seller_delivery_enabled -> missing-column error
Approved existing migration 0052 -> add missing column -> same query now renders dashboard
```

Annotated SQL: `ADD COLUMN seller_delivery_enabled boolean DEFAULT false NOT NULL` adds an opt-in setting whose initial value is disabled. The existing fulfillment-choice alteration is a SQL no-op; it records Django model state without changing stored fulfillment values. Do not manually add the column or fake the migration as a shortcut.

### 5. Backend / API behavior

Before migration the read-only Super Admin dashboard request reproduced the missing-column error. After migration, the actual protected dashboard view returned 200 under read-only transactions for all four active admin accounts across the three admin roles. Actual localhost HTTP GETs returned 200 for login, approved products (six) and facilities (three). No endpoint, RBAC, login, payment, inventory, Flutter or FastAPI business logic changed. The schema now supports the model field that the existing queries require. Authenticated dashboard checks invoked real Django views/templates under read-only transactions; no live browser login or physical-device flow was performed.

### 6. Database / migration impact

Applied only `api.0052_seller_delivery_setting`, adding one non-null boolean column with PostgreSQL/Python default false and one migration-history record. Django's normal migration lifecycle also ran its metadata/permission reconciliation. All 48 original table-content fingerprints matched; no original stored order fulfillment/payment values, product/inventory quantities, accounts or permissions changed. There is one existing seller request and zero delivery-enabled sellers. Exactly one 0052 history row exists and no migrations remain pending. The operation affected the shared hosted database explicitly approved by the user. No destructive migration, seed, reset, restore or database copy ran.

Refreshed backup used for the approved migration: `C:/Users/leste/.campushub-secrets/kamatera-before-0052-20261108T134443Z/campushub-before-0052.sql`, **405,014 bytes**, **48 table definitions / 48 data sections**, pg_dump exit 0 and completion marker verified. SHA-256: `db714e5d55f50276a8a35a64c95a502b57b74eec1edf0f69777f1f54938af2f0`. **Not restore-tested; media files are not included.** Private `preparation.json`, `pg_dump.stderr.log`, `table-fingerprints-before.json`, `immediate-before.json`, `after-original-columns.json`, `migration.log` and `result.json` are beside it. The timestamp is UTC; the work occurred November 8 in Asia/Singapore. The earlier 13:39 UTC preparation backup remains a historical checkpoint; the 13:44 UTC backup above is the refreshed pre-application backup.

### 7. Tests performed / safe practice

- Healthy tunnel reuse, real PostgreSQL login and identity verification: passed.
- Fresh Django database system check: passed; 48 tables/107 recorded migrations, consistent history, one pending migration and one missing model column.
- Direct and full Django-client product/facility GETs: 200, six products/three facilities.
- Read-only protected Super Admin dashboard request: reproduced the reported missing-column `ProgrammingError`.
- `sqlmigrate api 0052`: confirmed the single column-add SQL and fulfillment-choice SQL no-op; no schema executed.
- Full private pg_dump: completion/size/table-section/checksum checks passed; 48 baseline table fingerprints saved. No restore rehearsal or application regression suite run.
- Approved targeted migration: applied successfully; exactly one 0052 history row, no remaining pending migrations and the new setting is false for the existing seller request.
- Immediate before/after original-column comparison: **48/48 table-content fingerprints matched**, excluding only the intended new field/history row.
- Post-migration Django database system check: passed. Read-only dashboard view/template renders: **4/4 HTTP 200**, covering both Marketplace Admin accounts, Facilities Admin and Super Admin.
- Actual localhost login/products/facilities HTTP checks after migration: all 200. Ignored aggregate evidence: `scratch/reconnect-kamatera-20261108/{0052-result.json,0052-http.json}`. Documentation whitespace check passed.

Safe learning exercise: open the existing migration and find `AddField`, `model_name='sellerrequest'` and `db_default=False`; compare these with `SellerRequest.seller_delivery_enabled` in the model. Run the existing read-only `verify.py --active` helper and expect zero pending migrations/no missing model columns. Refresh the already-signed-in dashboard to verify the original missing-column error is gone. Do not rerun the one-time migration helper or submit seller/stock changes as part of this exercise. This demonstrates how a Python model field requires a matching database column.

### 8. Remaining limitations / troubleshooting

The reported schema error is resolved. No automated application suite, physical-device test, full browser workflow or backup restore rehearsal was run; the exact database/view/HTTP checks above were performed. The existing tunnel must remain connected and still needs its normal restart after a PC restart or session loss. No server source release was deployed; the schema update is shared with the hosted application, while its uploaded source remains separate. The earlier no-automatic-migration rule remains in force for future changes; this approval covered only 0052.

## Reconnected this PC to existing Kamatera PostgreSQL — November 8, 2026

**Result: this PC's Django and chat now connect to the existing Kamatera database, verified through their actual settings and localhost HTTP endpoints.** Open **http://127.0.0.1:8000/**. The remote service's private environment selects `core.settings_production` and the same `campushub` database/`campushub_app` role. No separate development/staging database was identified. After reviewing the read-only findings, the user explicitly instructed: “just connect to the to the kamatera”. This authorizes the shared-database selection, not migrations or test-data writes. Earlier dated reports below describe historical switches.

### 1. Cause / reason

Follow-up connection-refused incident on November 8: the tunnel error log recorded `client_loop: send disconnect: Connection reset`, the recorded SSH process had exited and no listener remained on PC port 15432. This confirms a dropped SSH session caused this incident; the available evidence does not identify why the network session reset. It does not establish a PostgreSQL outage or invalid credentials.

During recovery, the original helper also incorrectly refused to reuse the live tunnel: Windows TCP snapshots did not classify the forwarding endpoint as `Listen`, although a direct TCP connection and real Django queries succeeded. The exact reason for those inconsistent state snapshots is unknown. Replaced the state-only detection with endpoint/owner validation plus a TCP connection probe.

Before this switch, the active Django and chat `.env` files selected the separate PC database at `127.0.0.1:5432/campushub`. Existing code already supports Kamatera; no new provider integration is needed. The existing tunnel script and the saved private configuration from `C:/Users/leste/.campushub-secrets/before-local-development-20261021T140559Z/{django.env,chat.env}` identify the original online target. The similarly named repository backup `backend/backups/kamatera-switch-20261029/django.env` contains the pre-switch **local** settings and was not used as an online credential source. No credentials were guessed or printed.

### 2. Exact files changed / inspected anchors

| File / current line | Anchor | Action |
| --- | --- | --- |
| `backend/core/.env:10` | `DATABASE_URL` | Restored saved Django Kamatera URL on tunnel port 15432, including existing connection timeout. |
| `backend/chat_service/.env:1` | `DATABASE_URL` | Restored saved asyncpg Kamatera URL on the same tunnel. |
| `backend/core/core/settings.py:23`, `:167`, `:171` | `_load_dotenv`, `_database_url`, `dj_database_url.parse` | Existing environment loading and URL parsing verified; unchanged. |
| `backend/start_kamatera_db_tunnel.ps1:22`, `:30`, `:47`, `:85` | `Get-CampusHubTunnelListeners`, `Test-CampusHubTunnelConnection`, reuse/start checks | Recovery now checks the unconnected local endpoint, verified SSH owner and actual TCP acceptance rather than depending on `State=Listen`. Existing destination, key and strict host checking retained. |
| `scratch/reconnect-kamatera-20261108/verify.py:1` | Read-only verification helper | Added ignored local diagnostic code; no credentials embedded. |
| `scratch/reconnect-kamatera-20261108/connect.py:1` | Connection-only switch helper | Validates saved targets, restricts backup access and changes only database keys. |
| `docs/database-backup-neon.md:3` | This report | Added current evidence, migration impact and troubleshooting. |
| `CAMPUSHUB_CONTEXT.md:3` | Kamatera verification note | Added current result without replacing existing project history. |

Diagnostic JSON files are `scratch/reconnect-kamatera-20261108/{verification.json,connection-change.json,http-verification.json}`. These helpers and evidence are ignored local artifacts. Private `.env` files remain Git-ignored. Recovery changed the tunnel helper and documentation; no Django application, Flutter, model or migration source changed.

### 3. Changes made

For the follow-up tunnel recovery, reran `backend/start_kamatera_db_tunnel.ps1`, which started a verified new SSH endpoint on port 15432. Then updated its readiness/reuse detection after reproducing the false refusal above. The updated helper successfully reused the same verified SSH process twice without starting duplicates. No `.env`, database setting or application service restart was needed for this recovery. This guide and the leading context note record the recovery alongside the original reconnection work.

Started the existing hidden SSH helper with the saved dedicated key and strict host verification. The forwarding path is PC `127.0.0.1:15432` to Kamatera PostgreSQL `127.0.0.1:5432`. First verified the saved connection in a separate read-only process. After the user's shared-database confirmation, backed up both current `.env` files to `C:/Users/leste/.campushub-secrets/before-reconnect-kamatera-20261108T121126Z/`, restricting Windows access to the current user, SYSTEM and Administrators. Changed only `DATABASE_URL`; byte comparisons confirmed every other line was retained. Restarted only this checkout's verified local Django tree with its existing `0.0.0.0:8000` development/reload command and started local chat on `127.0.0.1:8001` with reload after checking that port was free. Launch metadata and logs are in that private backup folder. No remote deployment/configuration was changed and no push worker was started.

### 4. How it works / functions, inputs, outputs and data flow

`_load_dotenv(path)` reads key/value pairs but preserves values already present in the process environment. Django passes `DATABASE_URL` to `dj_database_url.parse`, producing the standard database settings. The diagnostic helper reads the original saved URL privately, verifies its expected loopback host, tunnel port and database, then sets it only in that process before `django.setup()`.

With `--active`, the helper instead reads the current `backend/core/.env`; this verified the completed switch. It sets PostgreSQL `default_transaction_read_only=on`, a statement timeout and a five-second connection timeout. It confirms `transaction_read_only = on`, reads table/column metadata and counts, calls Django's existing system check, and uses `MigrationExecutor` to inspect recorded versus source migrations. No migration execution method is called. `safe_error(error)` returns exception type, SQLSTATE and available table/column identifiers rather than credentials, raw exceptions or response contents. Output is a safe aggregate JSON report.

`connect.py:database_url(raw)` accepts private file bytes and extracts exactly one URL. Its switch checks both saved targets and matching database credentials, creates restricted backups, then replaces only each `DATABASE_URL` line while preserving all other bytes. It restores originals if either update fails. It executes no SQL. This one-time helper intentionally refuses a source already switched to port 15432; it is not a routine startup command.

Tunnel helper `Get-CampusHubTunnelListeners()` takes no input and returns port-15432 TCP entries without a remote peer (`RemotePort=0`, wildcard remote address). The caller still requires a loopback endpoint and `Test-CampusHubTunnelProcess(processInfo)` verifies its SSH executable, dedicated key, forwarding arguments and exact server. `Test-CampusHubTunnelConnection()` attempts a loopback TCP connection with a two-second timeout, returns a boolean and always disposes its socket. Startup accepts only the launched process's endpoint; reuse accepts only verified existing owners. This avoids trusting inconsistent state labels while retaining unknown-owner refusal. The connection probe opens/closes TCP only; it does not authenticate or execute SQL. For example, two successful invocations printing the same PID demonstrate reuse; only the Django read-only probe establishes PostgreSQL login/query success.

`RequestFactory` probes resolve the real URL/view; Django `Client` probes additionally run the middleware/request pipeline. Both invoke actual ORM/serializer reads against Kamatera inside read-only transactions that are rolled back. They do not send network requests to the existing port-8000 process. Example: `{"status": 200, "list_counts": {"products": 6}}` means the real approved-products response contained six records without printing their contents.

```text
Diagnostic Django process -> PC :15432 -> verified SSH -> existing Kamatera PostgreSQL
Running PC Django        -> PC :15432 -> same existing Kamatera database
Running PC chat          -> PC :15432 -> same database, messaging only
Flutter ProductService   -> HTTP Django /api/products/approved/ -> Django ORM -> PostgreSQL
FastAPI                   -> existing messaging-only service
```

### 5. Backend / API behavior

Against the online connection, both direct-view and full Django-client probes returned HTTP 200 for `/api/products/approved/` (six approved, available products) and `/api/facilities/` (three facilities). After restarting the local services, real localhost HTTP GETs also returned 200 for `/`, `/api/products/approved/` (six products), `/api/facilities/` (three facilities), `/api/mobile/services/` (one service) and chat `/health` (`status: ok`). A fresh async SQLAlchemy connection through chat's existing configuration independently confirmed the same `campushub` identity, saved role and client port 15432 using a read-only transaction. No route, serializer, authentication, permission, fulfillment or inventory behavior changed. This verifies these read endpoints and connection selection, not every authenticated marketplace workflow. Localhost submissions now affect shared Kamatera records; the separate PC database was not merged or copied.

Flutter `campushub/lib/module_app/services/product_service.dart:26`, `fetchApproved`, calls the Django HTTP API and converts its JSON to `ProductItem` objects. `campushub/lib/module_app/config/api_config.dart` selects API origins. A source search of `campushub/lib` and `pubspec.yaml` found no `DATABASE_URL`, PostgreSQL URL or PostgreSQL-port references. No database credential was copied into Flutter; no phone build/install or live device request was performed.

### 6. Database / migration impact

No schema or business-record writes, database creation/reset/copy, seed, restore, flush or migration application occurred. PostgreSQL enforced read-only verification. Found **48 tables, 107 recorded migrations, 15 products, one order, four web accounts, five mobile accounts, inventory, booking/payment tables and permission records**. All managed model tables exist. Migration history is consistent.

Pending: **`api.0052_seller_delivery_setting`**, from `backend/core/api/migrations/0052_seller_delivery_setting.py`. It changes the order fulfillment field's Django choices and adds `SellerRequest.seller_delivery_enabled` with Python/database default `False`. The online table currently lacks that column, so current seller-related code that selects it can fail even though the approved-product catalog succeeds. Applying it would change the shared hosted schema, expose the setting with an initial false value for existing sellers and require a table lock during the schema operation; it was **not applied**. No claim is made that every workflow is compatible with the current remote schema.

### 7. Tests performed / safe practice

- Saved-credential PostgreSQL login through the existing SSH tunnel: passed; actual database is `campushub`, role matches the saved configuration, server port 5432 and read-only mode is on.
- Django `check` with `database=['default']` through existing settings: passed.
- Table/column and migration-history inspection: completed; the one pending migration/missing column is reported above.
- Direct view and full Django-client GET checks: both endpoints passed against real online data.
- Read-only inspection of `/etc/campushub/django.env` confirmed the hosted production settings/database identity; credentials were not output.
- Actual localhost HTTP checks after the switch passed for login, products, facilities, mobile services and chat health; the async chat driver independently passed a read-only database identity query.
- Only the two `DATABASE_URL` lines changed, verified by byte comparison; previous values were backed up privately. Documentation whitespace checks passed.
- No application test suite, authenticated write workflow or physical-device check was run.
- Follow-up tunnel recovery: the new endpoint became ready, fresh read-only Django verification connected successfully, and actual localhost `/` and `/api/products/approved/` returned 200 with six catalog products. The updated helper was invoked twice and reused the same verified process both times. Recovery HTTP evidence is `scratch/reconnect-kamatera-20261108/tunnel-recovery-http.json`; no database writes or migrations were performed.

Safe practice exercise: from the project root run `backend/core/venv/Scripts/python.exe scratch/reconnect-kamatera-20261108/verify.py --active` while the existing tunnel is ready. Check `source: active Django .env`, `connected: true`, `transaction_read_only: on`, the `pending_migrations` list and API statuses in the aggregate JSON. This probes the active connection through a separate read-only process. Do not replace it with a migration, login, checkout or sample-data command. The recorded counts are a dated observation, not expected permanent totals.

### 8. Remaining limitations / troubleshooting

If `127.0.0.1:15432` reports **Connection refused**, first restore the existing tunnel from the project root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\backend\start_kamatera_db_tunnel.ps1
```

Expect a ready/reused verified listener message, then retry the failing page or existing pgAdmin connection. Port 15432 belongs to this PC's SSH forwarding; do not replace the URL with the server's public IP or open public PostgreSQL to work around a stopped tunnel. The helper starts/reuses one verified SSH process but does not automatically reconnect after that process exits. `ServerAliveInterval`/`ServerAliveCountMax` detect lost sessions; they do not restart them. No automatic startup task or persistent reconnect supervisor was installed. Its `current.json` and timestamped error logs are under `%LOCALAPPDATA%/CampusHub/kamatera-tunnel/`.

Safe recovery exercise: run the helper again while the verified tunnel is already healthy. Expect it to reuse the same listener rather than create a duplicate. Then run the read-only verification command in Section 7. If it refuses an unknown listener or reports SSH startup failure, inspect the indicated error log rather than terminating an unidentified process or changing credentials.

There were no remaining connection/authentication errors in the completed Django/chat checks. This is the shared hosted Kamatera database selected explicitly by the user, not a separately confirmed development/staging database. The pending seller-delivery migration remains unapplied. The tunnel depends on this PC and Internet access; rerun the existing tunnel script after restart/disconnection, preserving strict host verification. Settings edits require a fresh application process; existing process-level environment values take precedence over `.env`. To revert a future connection selection, restore only the private backup's database key, preserve other newer settings and restart local services; do not restore database tables. Some old scratch helpers mentioned in historical reports are absent; use this dated diagnostic helper for the checks above. Public website DNS, uploaded media and Flutter device reachability were not retested and are separate from PostgreSQL connectivity.

## Returned this PC to localhost — October 30, 2026

Current mode: open **http://127.0.0.1:8000/**. Both this PC's Django backend and chat service connect to **127.0.0.1:5432/campushub**, using the original saved local credentials. Local changes now affect the PC database. The hosted Kamatera deployment/database was not changed by this switch. This supersedes the online-database selection described below.

### 1. Cause / reason

The user requested “back to localhost.” Confirmed before changing settings: both local services selected port 15432, the SSH forwarding port for Kamatera. The original saved local settings selected port 5432, and a read-only connection confirmed that database was reachable. Its schema needed migrations 0050 and 0051 to support the current inventory code.

### 2. Exact files changed

| File / current line | Nearby anchor | Change |
| --- | --- | --- |
| `backend/core/.env:10` | `DATABASE_URL` | Restore only the saved Django localhost database URL; retain other current settings. |
| `backend/chat_service/.env:1` | `DATABASE_URL` | Restore only the saved asyncpg localhost URL; retain the existing chat signing settings. |
| `scratch/fifo-workflow-20261029/return_localhost.py:1` | `database_value`, `apply` branch | Validate targets, inspect the local migration plan, privately back up settings/database, stop this checkout's local app processes, restore the two URLs and apply only the two expected local migrations. |
| `scratch/fifo-workflow-20261029/verify_localhost.py:1` | `code`, `chat_code`, HTTP checks | Verify each actual database connection and read-only Inventory renders, then check the real localhost HTTP endpoints. |
| `docs/database-backup-neon.md:3` | `Returned this PC to localhost` | Record the current selection, checks, data flow and troubleshooting. |
| `CAMPUSHUB_CONTEXT.md:3` | `Current runtime: local PostgreSQL` | Preserve the current database choice above the historical Kamatera report. |

The original Django/chat connection values came from the restricted `backend/backups/kamatera-switch-20261029/` backup. Credentials and full connection URLs are intentionally omitted here.

### 3. Changes made

Only this PC's database-selection lines changed. Existing local Django/chat processes were stopped and restarted as hidden processes: Django on port 8000 and chat on port 8001. No remote service, remote data, role permission, application business logic, product quantity or Flutter API default was changed for the switch. Existing IDE launch configurations already use local development addresses.

### 4. How it works / functions and data flow

`database_value(path)` reads the one `DATABASE_URL` line from the original private settings. The switch validates its host, port and database before using it. Its `apply` branch first creates a local PostgreSQL dump and private settings snapshots. It then replaces only the current database lines, applies the checked schema updates to the PC database and reports safe host/port/count metadata.

```text
Browser / local Flutter build -> PC Django :8000 -> PC PostgreSQL :5432/campushub
Local chat requests           -> PC chat :8001  -> PC PostgreSQL :5432/campushub
```

Django's existing `core/settings.py:_load_dotenv` loads `backend/core/.env`; chat's `app/config.py:Settings` loads `backend/chat_service/.env`. Their running connections were verified independently, rather than assuming that an edited file changed an already running process. Example: port **5432** means the PC PostgreSQL server; port **15432** is the Kamatera tunnel and should no longer appear in either active local database setting.

### 5. Backend / API behavior

The existing APIs keep their routes, permissions and workflows. Verified responses: login `/` HTTP 200, `/api/products/approved/` HTTP 200 and chat `/health` HTTP 200. Stock Overview, Stock Movements and Stock Batches each rendered HTTP 200 using a real authorized local admin inside an enforced read-only transaction. The first verification script used the nonexistent `/api/products/` route, returned 404, and was corrected to the actual approved-products route; this was a probe error, not a production API change.

### 6. Database / migration impact

Before the local migrations, a full local dump and both previous settings files were saved in restricted `backend/backups/localhost-return-20261030/`. The dump is `localhost-before-switch-20261029T171152Z.sql` (UTC filename; October 30 in Asia/Singapore). Do not publish this private folder.

Applied existing migrations `0050_inventory_movement_notes` and `0051_hybrid_inventory` to **local PostgreSQL only**. No migrations remain pending. The original local data remains: **15 products, 344 available, 1 reserved and 14 existing batches**. Migration 0051 preserves FIFO for products that already have genuine batch history; it did not create those 14 batches or copy them from Kamatera. New products still default to Simple stock. The remote database was neither copied over the local one nor changed.

### 7. Tests performed / safe practice

- Read-only PostgreSQL checks confirmed `current_database() = campushub` and `inet_server_port() = 5432` for both Django and chat's async SQLAlchemy engine.
- Read-only reconciliation found no inventory errors and preserved the totals above; all three Inventory tabs rendered successfully.
- Local web/products/chat HTTP checks returned 200. Existing local migration plan is empty.
- Ran the existing `campushub/scripts/connect_android.py`: no single authorized physical phone was attached, so forwarding was safely skipped. No device was selected automatically.
- This was a configuration/runtime switch; no new business-logic test suite was needed or claimed. Detailed verification is privately recorded in `verification-result.json` beside the backup.

Safe practice: open the localhost login page without submitting any stock/order form. In a private terminal, check only the database host/port or PostgreSQL `SELECT current_database(), inet_server_port();`; expect `campushub` and `5432`. Never paste the connection URL or password into a screenshot, commit or chat. Restart local services after changing `.env`, because existing processes can keep their previous connection.

### 8. Remaining limitations / troubleshooting

Local and Kamatera records are separate and are not automatically synchronized. If a future launch still reaches Kamatera, check for a process-level `DATABASE_URL` override before editing application code; existing environment variables take precedence over `.env`. An APK explicitly built with an online `CAMPUSHUB_API_BASE_URL` needs a local development rebuild/relaunch to use the PC backend. No phone build/install was performed here, and no phone was connected for ADB verification. The earlier Kamatera public-hostname DNS issue is independent of this working localhost setup.

## Local servers reconnected to Kamatera - October 29, 2026

Current mode: open **http://127.0.0.1:8000/** on this PC. Django and local chat use the existing online `campushub` database through SSH. Changes submitted through localhost now affect shared Kamatera records. This supersedes the October 21 local-database configuration below. The separately hosted application source was not redeployed.

### 1. Cause / reason

The user clarified that “back to Kamatera run” means switching local servers from PC PostgreSQL to Kamatera. The private `.env` files selected PC port 5432. A read-only login verified the saved remote credential before either file changed. After switching, the actual approved-product endpoint returned HTTP 500: PostgreSQL reported missing `campushub_product.source_recommendation_id`. Confirmed Kamatera lacked migrations 0045 through 0049. The user explicitly approved a backup and those five migrations.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/.env` | 10 `DATABASE_URL` | Kamatera through `127.0.0.1:15432`; retain Django's five-second connection timeout. |
| `backend/chat_service/.env` | 1 `DATABASE_URL` | Same database using asyncpg, without a psycopg-only timeout parameter. |
| `scratch/switch_kamatera_database.py` | 13 `env_values`; 20 `main` | Ignored one-time connection switch, original-file backups and key comparison. |
| `scratch/verify_kamatera_database.py` | 10 `django_check`; 33 `chat_check` | Ignored read-only checks through actual application settings/drivers. |
| `scratch/backup_kamatera_before_migrations.py` | 14 `main` | Ignored backup helper guarded by the approved five-migration plan. |
| `docs/database-backup-neon.md` | 3 this report | Active mode, recovery, verification and learning guide. |
| `CAMPUSHUB_CONTEXT.md` | 3 current Kamatera note | Preserve the active database destination and result. |

Private originals, SQL backup, verification JSON, runtime metadata and service logs are in `backend/backups/kamatera-switch-20261029/`. Windows access is restricted to the user, SYSTEM and Administrators. That folder and `.env` files are Git-ignored. Passwords are not included here. Existing application settings, SSH helper, routes, models and migration source were not edited.

### 3. Changes made

Started existing `backend/start_kamatera_db_tunnel.ps1` using the dedicated saved key and strict known-host checking. Both `.env` before/after comparisons confirmed only `DATABASE_URL` changed. Restarted the verified local Django process tree, preserving `0.0.0.0:8000` and reload. Started local chat on `127.0.0.1:8001` with reload after confirming no existing listener. Hidden launches load fresh settings; logs and `runtime.json` are in the private directory above. No push worker was started.

After backup verification, applied existing `api.0045_bundle_recommendation_monitoring`, `0046_inventory_fifo`, `0047_fifo_receipt_movement`, `0048_order_fulfillment` and `0049_mobile_food_preferences`. No FIFO initialization/cutover command ran.

### 4. How it works: functions, inputs / outputs and data flow

Unchanged `backend/core/core/settings.py:23`, `_load_dotenv(path)`, accepts a file path and loads missing process environment keys. Line 167 reads `DATABASE_URL`; line 170 builds Django's connection through `dj_database_url.parse`. An existing process environment value takes precedence over the file, so launch commands cleared a shell-level database override.

Unchanged chat `app/config.py:8`, `Settings`, reads its `.env`; line 31 `get_settings()` caches it. `app/database.py:18` creates an engine from the URL, line 19 creates `SessionLocal`, and line 22 `get_db()` yields a request-scoped session. Fresh processes were required to discard cached local settings.

```text
Browser -> PC Django :8000 -> PC loopback :15432 -> SSH -> Kamatera PostgreSQL :5432
Local chat :8001           -> same tunnel and online database
```

Annotated example: in `127.0.0.1:15432 -> SSH -> 127.0.0.1:5432`, the first loopback address belongs to this PC; the second belongs to Kamatera. SQL correctly reports server port 5432 while Django's client configuration uses 15432. Reusing the existing tunnel avoids opening PostgreSQL publicly or duplicating connection logic.

The switch helper's `env_values(raw)` returns a key/value map for comparison; `main()` verifies database identity, saves exact original bytes and replaces only the two database keys, restoring originals if its update fails. The verification helper's `django_check()` reads actual database identity and pending migrations; `chat_check()` does the equivalent asynchronously and disposes its engine. Neither creates fixtures.

The backup helper requires the expected database/user/client port and exact five forward migrations. It runs `pg_dump` with literal arguments and the password in its child environment, then verifies exit code, completion marker, size, table/data sections and SHA-256. Its output is a private SQL file and verification JSON. The separate approved `manage.py migrate --noinput` command applied the schema afterward.

### 5. Backend / API behavior

Local login, approved products, facilities, mobile services and chat health now respond successfully using Kamatera. The confirmed missing-column catalog failure disappeared after migration. Existing routes, permissions and business rules remain intact; FastAPI remains messaging-only. No server application release or Flutter configuration/build/install/restart occurred.

The PC database was not merged/copied into Kamatera. Media still comes from local application paths; changing the database does not synchronize uploads or local-only records. Local and separately hosted requests now share online records.

### 6. Database / migration impact

Full pre-migration backup: `backend/backups/kamatera-switch-20261029/kamatera-before-migrations-20261029T121419Z.sql`, **368,967 bytes**, 42 table definitions and 42 data sections, `pg_dump` exit 0 and completion marker verified. SHA-256: `4f17d427c270b7ba4e407e15cd5977ff9fa695497b6520a37508b018e9bdec80`. **Not restore-tested; media is not included.**

The five approved migrations add bundle/FIFO/food-preference tables and product/order/inventory fields, indexes and constraints. Django also maintains migration/content-type/permission metadata. No database restore, credential change, sample products/orders/bookings or stock initialization occurred. These schema changes affect shared Kamatera. Final migration inspection found zero pending operations.

### 7. Tests performed

- Read-only saved-credential login succeeded before the switch; both actual application drivers afterward reported `campushub` / `campushub_app` through client port 15432.
- Only `DATABASE_URL` changed in each file; originals were privately backed up.
- SQL backup passed all completion/size/table/hash checks above before migrations.
- All five migrations reported `OK`; `migrate --check` exited 0; final migration plan had zero pending operations.
- Django `check --database default`: no issues.
- Final HTTP GET: `/`, `/api/products/approved/`, `/api/facilities/`, `/api/mobile/services/` on local Django and `/health` on local chat all returned 200.
- Earlier checks of nonexistent `/login/`, `/api/products/` and `/api/services/` returned 404; route inspection corrected those test URLs. The actual catalog-route 500 was separately confirmed and resolved as described above.
- No automated suite, phone workflow, authenticated order/booking submission or backup restore rehearsal ran for this configuration operation.

### 8. Remaining limitations, troubleshooting and safe practice

Localhost depends on this PC's running SSH helper and Internet connection. After PC restart, start the tunnel first, then the normal local Django/chat commands in the earlier report below. The tunnel script reuses only a verified matching listener, refuses unknown port owners and never kills processes. Do not start duplicate servers or blindly reuse saved PIDs.

If the database cannot connect, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\backend\start_kamatera_db_tunnel.ps1` from the root and inspect its reported SSH error log. Check shell-level `DATABASE_URL` overrides and restart application processes after settings changes. Keep host-key verification enabled. The one-time switch helper refuses an existing backup directory. Do not restore the pre-migration SQL merely to change connection mode.

Safe exercise: open `http://127.0.0.1:8000/` and `http://127.0.0.1:8001/health`; expect the normal login page and `{"status":"ok"}`. Run `backend/core/venv/Scripts/python.exe scratch/verify_kamatera_database.py django` from the root; expect client port 15432 and zero pending migrations. These are reads only. Avoid sample-order connectivity tests because localhost now writes shared records. To return to PC PostgreSQL later, restore only the backed-up database keys, preserve newer unrelated settings and restart both local services; switching connection does not require reversing online migrations.

---

## Returned PC development to localhost — October 21, 2026

### 1. Cause / reason

The user requested localhost after the online site loaded slowly. The PC's web/chat servers and SSH database tunnel were stopped, but its original PostgreSQL service and existing `campushub` database remained available. Verified the original local credential before selecting that database again. This step does not establish a provider outage.

### 2. Exact files changed / current anchors

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/core/.env` | 10 `DATABASE_URL` | Existing PC `campushub` on `127.0.0.1:5432`, original local login, connection timeout five seconds. |
| `backend/chat_service/.env` | 1 `DATABASE_URL` | Same PC database through the existing asyncpg driver; no unsupported timeout query parameter. |
| `docs/database-backup-neon.md` | 3 localhost report | Current mode, data flow, startup/debugging and verification. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest localhost note | Preserve the active local mode separately from online hosting. |

The `.env` files are private/ignored; actual passwords are not included here. Restricted pre-switch backups: `C:/Users/leste/.campushub-secrets/before-local-development-20261021T140559Z/{django.env,chat.env}`. Their Windows ACLs allow the current user, SYSTEM and Administrators. The original local credential came from the existing protected `kamatera-client-before-tunnel-20261020T103910203468Z/chat.env`; its local host/port/database and a real read-only login were checked first.

### 3. Changes made

Only `DATABASE_URL` changed in each active `.env`, verified by before/after key comparison. Existing loopback chat URLs, matching chat signing secrets and accepted localhost origins remained intact. No application-code change was needed. Started hidden local Django on `127.0.0.1:8000` with its development auto-reloader and Uvicorn chat on `127.0.0.1:8001` with reload, after checking that both ports were free. No process was killed/replaced. Logs and startup metadata are under `C:/Users/leste/.campushub-secrets/local-development/`. Initial launcher PIDs were 29840/25028; these are not permanent identities. No matching push worker was found running or started.

### 4. How it works: functions, inputs / outputs and data flow

Existing `core/settings.py:23`, `_load_dotenv(path)`, reads the PC `.env` without replacing an existing process environment value. At line 167, `DATABASE_URL` is passed to `dj_database_url.parse`, producing Django's standard `ENGINE`, `NAME`, `USER`, `PASSWORD`, `HOST` and `PORT` settings. Chat's `app/config.py`, `Settings`, reads its `.env`; `app/database.py` passes the asyncpg URL into `create_async_engine` and `SessionLocal`. New processes load the updated destinations; an already running process can retain old settings.

```text
Browser http://127.0.0.1:8000 -> PC Django -> PC PostgreSQL :5432 / campushub
Local chat :8001            -> PC FastAPI -> same PC PostgreSQL database
Online DuckDNS site        -> separate Kamatera services/database (unchanged)
```

Example: the database host remains `127.0.0.1`, but selecting port **5432** now reaches the PC's actual PostgreSQL listener. Port **15432** was the former SSH tunnel entrance. The current local flow no longer requires that tunnel. The shared settings/parser were reused to avoid duplicate database configuration logic.

### 5. Backend / API behavior

Develop at **http://127.0.0.1:8000/**. The local login, approved products, facilities and chat health endpoints respond successfully. Existing routes, permissions and business logic remain intact. Python edits can be picked up by the development reloader; refresh the local browser page to view template/static edits. Nginx is not required locally. PC edits do not automatically update the separate uploaded Kamatera release.

### 6. Database / migration impact

No restore, copy, schema migration, role/password change or intended application-record write occurred. The existing PC database had 15 products and 100 migration-history records when inspected. `migrate --check` found no pending migrations; nothing was applied. No synchronization with Kamatera was performed. Local edits now change only the PC database, while the online site continues to use its separate server database.

### 7. Verification actually performed

- Local PostgreSQL service running/listening on 5432; authenticated read confirmed `campushub`, server loopback and port 5432 before the switch.
- Both `.env` key comparisons: only `DATABASE_URL` changed; real passwords were not printed.
- Django `check --database default`: no issues. `migrate --check`: exit 0/no pending migrations.
- Fresh chat SQLAlchemy read confirmed local `campushub` on port 5432 after the switch.
- Real HTTP requests: local login 200 (~48 ms), approved products 200 (~238 ms), physical facilities 200 (~64 ms), chat health 200 (~36 ms). These are observed single-request timings, not guarantees.
- Matching local chat signing secrets, loopback chat destinations and both accepted local web origins verified without displaying secret values.
- No new automated test suite was written/run for this reversible configuration change. Real read-only database/HTTP checks were used. No authenticated browser or phone workflow was tested.

### 8. Startup, troubleshooting, limitations and safe practice

Both local services are **already running**. After restarting the PC, start Django in a Windows terminal:

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\backend\core
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

For chat, use a second terminal:

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\backend\chat_service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Do not start duplicates on occupied ports. Inspect `current.json` and verify a process's executable/arguments before identifying an existing hidden launcher; do not blindly kill a recorded PID. If the DB is unavailable, inspect Windows service `postgresql-x64-18`. If a new process still targets 15432, check for an overriding terminal `DATABASE_URL`: `_load_dotenv` intentionally preserves existing process variables. Use the private pre-switch copies only for a deliberate later return to the tunnel; do not overwrite unrelated newer settings.

The existing **online APK still uses Kamatera**. Editing PC `.env` does not switch an installed APK. Flutter development without the public API dart define retains the existing LAN configuration; a physical phone needs the existing ADB reverse setup or a LAN bind/IP. Phone `127.0.0.1` means the phone unless ADB reverse is configured. No phone rebuild/install/restart, online service restart/shutdown, or Nginx edit was performed here.

Safe exercise: open localhost, make a harmless local CSS change, refresh, revert it and refresh again. Verify that only the local page changes. Do not create/delete records just to test connectivity. `curl.exe http://127.0.0.1:8001/health` should return `{"status":"ok"}` without writing application data.

---

## Earlier Kamatera database configuration history

## Correction: Kamatera login is separate from PostgreSQL — October 20, 2026

This correction supersedes the password update recorded immediately below. The PostgreSQL account is back on its original generated password, not the password supplied for the Kamatera login.

### 1. Cause / reason

The user clarified that the supplied password was their Kamatera password. The assistant had mistakenly treated it as a request to change PostgreSQL authentication too. To correct that assumption, the previous generated `campushub_app` password was restored from its protected pre-change backup. Kamatera/SSH login credentials were never changed by either operation.

### 2. Exact files changed / anchors

- `backend/core/.env:10`, `DATABASE_URL`: restored only its PostgreSQL password component.
- `backend/chat_service/.env:1`, `DATABASE_URL`: restored only its PostgreSQL password component.
- `C:/Users/leste/.campushub-secrets/kamatera-postgresql.json`, `password`: restored the original generated database password.
- Server `/root/campushub-migration/database-connection.json`, `password`: same restoration in the private server record.
- `docs/database-backup-neon.md:3`, this correction; `CAMPUSHUB_CONTEXT.md:3`, latest correction note.

There was no edit to `settings.py` or chat `database.py`. Private before-correction backups are in `C:/Users/leste/.campushub-secrets/kamatera-db-password-correction-20261020T120535490777Z/` and a timestamp-matched root-only server backup. These are sensitive recovery files, not documents to share.

### 3. Changes made

Reused authorized SSH and PostgreSQL `ALTER ROLE` to restore the application database password. Verified authentication with the restored password before selecting it in the two private application URLs. Preserved current non-password URL components and unrelated environment settings rather than replacing entire files with older backups. Updated the private credential records consistently; no password is repeated in this report.

### 4. How it works: functions, inputs / outputs and data flow

The one-off correction read the original password from the protected `kamatera-password-before-20261020T120152564611Z/kamatera-postgresql.json` backup. It first checked that the current client files and server credential record still matched the last operation, to avoid replacing an independent password change. It reused `remote(code)` at `scratch/database-backup/copy_to_kamatera.py:26`, passed SQL on encrypted SSH stdin, and URL-encoded the restored password using `quote(..., safe='')`. Files were replaced with restricted permissions.

```text
Private pre-change database password
  -> guarded SSH ALTER ROLE campushub_app
  -> fresh PostgreSQL login check
  -> both private DATABASE_URL values + private credential records
  -> fresh Django and asyncpg read-only identity checks
```

An SSH/Kamatera login grants server/account access; the PostgreSQL login grants database access. Django's URL needs the PostgreSQL account password. These are separate credentials even though they access resources on the same server.

### 5. Backend / API behavior

Fresh Django and chat processes again use the original generated password for `campushub_app`. The short `dj_database_url.parse()` settings remain correct. No API, business logic or permissions were changed. No application or worker was restarted; any process that cached the temporary password still needs its next normal restart to read the corrected environment. The existing verified SSH tunnel was reused.

### 6. Database / migration impact

Only PostgreSQL role authentication was restored. No application rows, schema, migrations or grants were changed. No Kamatera console or SSH/root password was changed. The server key remains the SSH authentication method for the helper.

### 7. Verification actually performed

The pre-change credential backup was present and matched the expected database identity. Current client files matched the password being corrected. Current and restored direct PostgreSQL password logins succeeded at the appropriate steps. After correction, fresh Django and chat read-only queries both returned user `campushub_app` and database `campushub`. No full application suite or live write tests were run.

### 8. Limitations / troubleshooting / safe practice

Keep the generated database password in the private `.env`/credential records. Do not replace it with a Kamatera console/server password. If an already-running service reports authentication failure, use its normal restart to load the corrected values; avoid changing additional credentials to diagnose cached settings. The operation cannot reload another process's environment automatically.

Safe practice: locate `DATABASE_URL` in Django's `backend/core/.env` and identify the username `campushub_app`, without printing or sharing the password. Compare it with the SSH helper's `root` username to see the two separate accounts. Use the read-only database identity query from the connection section to verify which account Django actually uses. Do not restore old full files over newer unrelated settings.

---

## PostgreSQL application password updated — October 20, 2026

### 1. Cause / reason

The user requested using a supplied password. The application account previously had a generated PostgreSQL password. Updating only an `.env` value would have broken authentication, so the `campushub_app` PostgreSQL login and its private connection records were updated together. The supplied password is intentionally not reproduced in this guide or application source.

### 2. Exact files changed / anchors

- `backend/core/.env:10`, `DATABASE_URL`: updated only the database password component of Django's private connection URL.
- `backend/chat_service/.env:1`, `DATABASE_URL`: updated only the database password component of chat's existing asyncpg URL.
- `C:/Users/leste/.campushub-secrets/kamatera-postgresql.json`, `password`: private local credential record updated.
- Server `/root/campushub-migration/database-connection.json`, `password`: private server credential record updated.
- `docs/database-backup-neon.md:3`, this report; `CAMPUSHUB_CONTEXT.md:3`, latest password-change note.
- `settings.py` and chat `database.py` were not changed; their environment-based configuration remains valid.

Private local rollback copies were saved under `C:/Users/leste/.campushub-secrets/kamatera-password-before-20261020T120152564611Z/`. A timestamp-matched root-only credential backup and diagnostic log were saved under the server migration directory. These files contain secrets and must not be published or pasted into chat.

### 3. Changes made

Used authenticated SSH to update only the `campushub_app` database role's password with SCRAM-SHA-256 password storage, then authenticated through the existing SSH tunnel with the new password before selecting it in both application environment files. Updated both private credential records. The Kamatera SSH/root password was not changed. Active private local files and rollback directories have restricted Windows ACLs; server secret files were created under umask `077`.

### 4. How it works: functions, inputs / outputs and data flow

The one-off operation reused the existing `remote(code)` SSH helper (`scratch/database-backup/copy_to_kamatera.py:26`) and normal PostgreSQL `ALTER ROLE` authentication management. It passed the password through encrypted stdin, not SSH command-line arguments. `urllib.parse.urlsplit()` read each existing URL and `quote(password, safe='')` encoded special characters before `urlunsplit()` reconstructed the URL. In particular, an `@` inside a password must be encoded as `%40` so it cannot be mistaken for the separator before the host. Driver, username, database, port and query settings were preserved.

```text
Supplied password (in memory)
  -> authenticated SSH -> PostgreSQL ALTER ROLE campushub_app
  -> fresh PostgreSQL password login verification
  -> URL encoding -> Django .env + chat .env
  -> private credential records
  -> fresh Django + SQLAlchemy/asyncpg read-only connection checks
```

For a harmless example, `quote('example@value', safe='')` returns `example%40value`; this is URL encoding, not encryption. Keep the entire URL private. Django's existing parser converts it back into normal connection parameters; chat's existing asyncpg engine reads its corresponding URL. No additional database controller or login endpoint was introduced.

### 5. Backend / API behavior

Fresh Django and chat processes successfully authenticate as `campushub_app` to database `campushub`. Existing routes and business logic are unchanged. Already-running processes may cache the old password until their next normal restart; currently open PostgreSQL sessions are not forcibly disconnected by the password change. No Django, chat, phone or notification worker was stopped/restarted by this operation. The tunnel helper started a new verified SSH tunnel because the previous listener was no longer running; its initial observed PID for this operation was 13800, not a permanent identifier.

### 6. Database / migration impact

Only the PostgreSQL role's authentication password changed. No application records, tables, schemas, grants or migrations were changed, and no database restore was repeated. The local PostgreSQL account and server SSH/root password were unchanged.

### 7. Verification actually performed

- Before changes, both private URLs matched the existing credential record and the expected role/host/database.
- Fresh PostgreSQL password login succeeded after `ALTER ROLE` and before updating local application files.
- Fresh Django read-only query returned `campushub_app`, `campushub`, client port `15432`.
- Fresh chat SQLAlchemy/asyncpg read-only query returned `campushub_app`, `campushub`.
- Comparison with private backups confirmed that only `DATABASE_URL` changed in each `.env`; unrelated JWT, origins, Firebase and other settings were preserved.
- Both `.env` files remain ignored by Git. No full application regression suite or live API write test was run for this credential-only change.

### 8. Limitations / troubleshooting / safe practice

Use the existing short `dj_database_url.parse(...)` configuration in `settings.py`. If a running service later reports password authentication failure, let it load the changed environment during its normal restart and check for shell-level `DATABASE_URL` overrides. Do not put the supplied password into the tracked source or replace the URL's encoded password with an unescaped `@`. Do not rotate unrelated SSH or chat JWT credentials as a workaround for this database password.

Safe practice exercise: in a Python shell, try the harmless `quote('example@value', safe='')` example above, then `unquote()` the result and confirm the original example is returned. Do not print or practice with real credentials. The read-only database identity checks in the next section can verify the selected destination without exposing passwords.

Rollback requires restoring both the PostgreSQL role password and the corresponding private client records; restoring only a file would leave authentication inconsistent. Private backups are for deliberate recovery, not automatic reversal of later changes. Existing processes still need their own normal settings reload; no end-to-end app restart was claimed.

---

## Local PC connected to Kamatera over SSH — October 20, 2026

This section supersedes the earlier copy-only state below: the local configuration now selects the Kamatera database. Django/FastAPI are configured for running on the PC; no website deployment was performed.

### 1. Cause / reason

After the database copy, the user explicitly chose **Django on this PC, connected through an SSH tunnel**. Inspection confirmed that Django still hard-coded the local `postgres` connection and that chat's existing `DATABASE_URL` also selected the local database. Both configurations needed the same destination to keep Django-owned accounts and chat references consistent.

### 2. Exact files changed and code anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/core/settings.py` | 16 `ImproperlyConfigured`; 167 `_database_url`; 170 `DATABASES` | Replace the hard-coded local credentials with the already-installed `dj_database_url` parser and private environment configuration. |
| `backend/core/.env` | 10 `DATABASE_URL` | New private Django URL pointing to the local tunnel port; unrelated environment values retained. |
| `backend/chat_service/.env` | 1 `DATABASE_URL` | Existing asyncpg URL changed to the same tunnel/database/role; JWT and origin configuration retained. |
| `backend/start_kamatera_db_tunnel.ps1` | 13 `Test-CampusHubTunnelProcess`; 22 guarded startup; 53 `Start-Process` | New reusable tunnel helper; starts hidden, verifies existing listener ownership and refuses duplicates or unrelated listeners. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest local Kamatera connection note | Preserve the current configuration for future project work. |
| `docs/database-backup-neon.md` | 3 this section | Current eight-part report, data flow, startup, checks and rollback. |

Private rollback files were saved outside the repository under `C:/Users/leste/.campushub-secrets/kamatera-client-before-tunnel-20261020T103910203468Z/`: `django-settings.py`, `django.env`, and `chat.env`. They contain previous settings/secrets and have restricted user/SYSTEM/Administrators access. Both active `.env` files remain ignored by Git and their Windows ACLs were also restricted to those principals. No new dependency was installed. `backend/chat_service/app/database.py` did not need a change: it already reads the chat settings URL.

### 3. Changes made

Started one dedicated hidden OpenSSH process forwarding `127.0.0.1:15432` on the PC to `127.0.0.1:5432` on `74.113.234.180`. The actual initial PID was 17976; PIDs are temporary and must not be assumed current later. Public-key authentication, strict existing host-key checking, connection timeout, exit-on-forwarding-failure and SSH keepalives are enabled. PostgreSQL's public network configuration was not changed.

Django reads its private `DATABASE_URL` using the existing `_load_dotenv()` flow, then `dj_database_url.parse()`. The parsed dictionary supplies database `campushub`, user `campushub_app`, client host `127.0.0.1`, port `15432`, a 10-second connection timeout, a 60-second connection lifetime and connection health checks. Missing configuration raises a clear error rather than silently selecting a different database. Chat's existing URL uses its required `postgresql+asyncpg` scheme and the same credentials/host/port/database. Passwords are URL-encoded and were not printed.

### 4. How it works: functions, inputs / outputs and data flow

`Test-CampusHubTunnelProcess(processInfo)` accepts Windows process metadata and returns true only for the expected SSH executable, dedicated key, forwarding rule and server target. The startup script checks the listener and existing matching processes under a mutex, starts one helper only when necessary, and waits for its exact loopback listener. It reuses a matching live tunnel; an unrelated listener or a pending helper causes a refusal. No process is terminated by the script. It records metadata/logs under `%LOCALAPPDATA%/CampusHub/kamatera-tunnel/`; these do not contain database credentials.

`_load_dotenv(path)` is unchanged: it loads private `.env` values only if the process does not already define them. Therefore an externally set `DATABASE_URL` takes precedence. `dj_database_url.parse()` converts the Django URL to the standard `DATABASES['default']` dictionary. Chat's existing `get_settings()` and `create_async_engine()` continue to read its asyncpg URL. Each application then opens a normal PostgreSQL connection to the local tunnel; SSH carries that connection to the server.

```text
PC Django .env -> settings.py -> psycopg2 --------+
                                                |
PC chat .env -> get_settings() -> SQLAlchemy -----+-> 127.0.0.1:15432
                                                  -> encrypted SSH to Kamatera:22
                                                  -> server 127.0.0.1:5432/campushub
```

The tunnel is a separate process, not started by importing `settings.py`. A test or management command therefore cannot accidentally launch SSH just by reading settings. Django remains the business/auth source of truth; FastAPI remains chat-only.

### 5. Backend / API behavior

Newly started/reloaded Django and chat processes now use the remote database. Their existing routes, permissions, models, APIs and business rules are unchanged. Future writes through those processes go to Kamatera; local PostgreSQL remains a separate database. Media files still come from this PC's existing application directories because the application still runs here.

No Django, FastAPI, Flutter, phone or notification worker was explicitly stopped or relaunched. Editing `settings.py` can trigger Django's normal development auto-reloader; the change was explained before editing. A process that already cached its settings/connections, particularly chat or a notification worker, requires its next normal restart to pick up its changed environment. The verification below used fresh processes and does not prove that every pre-existing service has reloaded. Do not launch duplicate workers to solve that.

### 6. Database / migration impact

No new tables, records, schema changes or migrations were made during this connection change. Actual `manage.py migrate --plan` reported **No planned migration operations**. The verified destination still has 42 tables and 100 copied Django migration records. Changing the connection is not replication: new writes in one database are not copied to the other.

Do not run ordinary database-creating integration tests against the remote application database. `campushub_app` intentionally has no `CREATEDB` permission; use a separately configured local/isolated test database when running those suites.

### 7. Verification actually performed

- Tunnel startup succeeded; invoking the helper again reused PID 17976 and did not create another tunnel.
- Actual fresh Django connection, read-only transaction: database `campushub`, user `campushub_app`, configured client port `15432`, remote port `5432`, 42 tables, 100 migration records.
- `manage.py check --database default`: **System check identified no issues (0 silenced)**.
- `manage.py migrate --plan`: **No planned migration operations**; no migrate execution.
- Actual fresh chat SQLAlchemy/asyncpg connection, read-only transaction: database `campushub`, user `campushub_app`, 42 tables.
- Git ignore checks passed for both private `.env` files; scoped diff whitespace check passed.
- No live API write test, application restart, full regression suite or public website deployment was performed.

### 8. Startup, troubleshooting, rollback and safe practice

Before starting Django/chat after a PC restart or tunnel disconnect, run from the project root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\backend\start_kamatera_db_tunnel.ps1
```

Expected: **ready at 127.0.0.1:15432**. If already running, it reports reuse. The tunnel has no Windows startup task or automatic reconnection loop; after it exits, rerun the helper. Keep the PC online. After the tunnel is ready, start/reload Django/chat using your usual workflow. To verify Django without modifying application records:

```powershell
cd .\backend\core
.\venv\Scripts\python.exe manage.py check --database default
.\venv\Scripts\python.exe manage.py migrate --plan
```

Practice exercise: rerun the tunnel helper once. Confirm it reports the **same current PID**, then run the two read-only commands above. Do not assume PID 17976 remains valid after reboot.

If port 15432 is refused, confirm the helper is ready and inspect its reported SSH error log. An occupied port does not authorize stopping its process; the helper refuses unverified owners. If settings still select another server, check whether your shell or launch configuration defines `DATABASE_URL`, because external environment variables override `.env`. Existing chat/worker processes may still use cached settings until their normal restart. If SSH warns that the remote host key changed, verify that change through Kamatera rather than disabling host checks.

Rollback, if intentionally requested later: the private backup folder above contains the exact earlier Django settings and both `.env` files. Restore only the intended connection settings in your normal stopped/reload workflow; preserve unrelated changes made since this operation. Clear any shell-level `DATABASE_URL` override, then verify `current_database()`/`current_user()` before doing writes. Rollback changes only the selected connection; it does not merge new Kamatera records back into local PostgreSQL. The tunnel helper does not provide a stop action and never kills unidentified processes.

Implementation references: Django's [database connection settings](https://docs.djangoproject.com/en/6.0/ref/settings/#databases) and the existing dependency's [DATABASE_URL parsing](https://github.com/jazzband/dj-database-url#usage).

---

## Kamatera database copy completed — October 20, 2026

### 1. Cause / reason

The user requested connecting to the existing Singapore Kamatera server at `74.113.234.180` and copying the local PostgreSQL tables and records. pgAdmin is a database management application; PostgreSQL holds the actual data. The source is local `campushub`, PostgreSQL 18.6. The user completed public-key authorization and successfully logged in as root. Inspection confirmed Ubuntu 26.04.1 and no existing PostgreSQL installation. After installation, the destination contained only the default `postgres` database and no application roles, so creating a new `campushub` database did not replace an existing database.

### 2. Exact files changed

- `scratch/database-backup/prepare_kamatera_verification.py:14`, `prepare(path)`: new standalone helper derives restore checks from the existing SQL dump. It does not change application code or connect to either database.
- `scratch/database-backup/copy_to_kamatera.py:26`, `remote(code)`; line 39 `inspect()`; line 57 `copy_database()`: standalone SSH inspection, guarded transfer, new-database restore and verification. The entry point at line 192 defaults to inspection; mutation requires `--copy`.
- `docs/database-backup-neon.md:3`, this dated section: actual operation, data flow, connection instructions and remaining deployment work.
- New private artifacts are in ignored `backend/backups/`: `campushub_postgres_20261020_182111.sql`, `.verification.json`, `.sql.sha256`, `.restore-check.sql`, `.restore-manifest.json`, and `.kamatera-result.json`.
- Outside the repository, a dedicated SSH key pair was created at `C:/Users/leste/.ssh/id_ed25519_campushub_kamatera`; only its `.pub` file is intended for server authorization. The first SSH host key was recorded in Windows OpenSSH `known_hosts` using normal first-connection trust. No SSH authentication was bypassed.
- A new database password is saved privately in `C:/Users/leste/.campushub-secrets/kamatera-postgresql.json`. Its Windows ACL and the new private key's ACL permit the user, SYSTEM and Administrators only. Neither secret was printed in tool output or copied into this guide.
- On the server, new PostgreSQL 18 packages/data/configuration and `/root/campushub-migration/` were created. That directory is root-only mode `0700`; the dump and connection JSON are `0600`.

### 3. Changes made

Reused `backup_before_neon.py --create` and the existing `accounts.backup_service.create_backup('full')`. The new backup is 361,045 bytes, with 42 table definitions/data sections and a completion marker. SHA-256 is `bdfa0c26ab73897e92daeab51a62324d133b51724b2e5ee22c0a79c1ecb61ab9`. Existing exports were retained.

The helper validates the original backup checksum and rejects unexpected paths, incomplete or duplicate COPY sections, and existing output files. It then produces a metadata-only manifest and read-only SQL checks for exactly 42 tables, 1,798 rows across those tables, and 33 saved sequence states. Row counts are taken from the dump itself, so they refer to its snapshot rather than a later live database read.

Installed `postgresql-18` and `postgresql-client-18` from the server's configured Ubuntu repository, which provides matching PostgreSQL 18.6. Created a new nonsuperuser login `campushub_app` and a new database `campushub`. Transferred the SQL/check files through SCP, verified their SHA-256 values on the server, and restored with `psql --single-transaction` and `ON_ERROR_STOP=1`. Assigned all application tables/sequences and the public schema to `campushub_app`, removed public schema privileges, and validated the restore. PostgreSQL listens on `127.0.0.1:5432`; its cluster is active and enabled for system startup.

### 4. How it works: functions, inputs / outputs and data flow

`prepare(path)` accepts one existing verified SQL dump path. It reads that dump and its neighboring verification JSON, counts records inside PostgreSQL COPY blocks without displaying the records, and extracts saved sequence values. Its outputs are a manifest and SQL that raises an error if the destination has a different table count, any different per-table row count, or a different saved sequence value. It refuses COPY syntax outside the observed simple `public.table_name` format instead of guessing.

`remote(code)` sends a Python operation over authenticated SSH stdin and parses its metadata-only JSON result. SQL commands use argument lists or stdin to preserve quoting; database passwords never enter command-line arguments. `inspect()` reads database names, application roles, PostgreSQL version and listen settings without changing them. `copy_database()` checks local/remote checksums, expected version, localhost binding and absence of destination names before creating anything. A server-side file lock prevents overlapping transfers. Existing targets, local credential files and server copy logs cause a refusal rather than an overwrite. Failure leaves any newly created destination artifacts for explicit investigation; the utility never deletes a database or role as automatic recovery.

```text
Local Django database settings (unchanged)
  -> existing backup service -> private SQL snapshot + checksum
  -> prepare(path) -> private restore manifest + read-only checks
  -> authorized SSH/SCP -> server-side checksum validation
  -> new campushub database -> transactional restore -> application ownership
  -> read-only per-table/sequence checks -> real password login check
  -> private local and remote result files
```

For example, a check equivalent to `IF (SELECT count(*) FROM public.some_table) <> expected_count` aborts verification if rows are missing. Actual checks contain the real table names and snapshot counts; they contain no record values. Equal counts do not prove every field value is identical, so an end-to-end restore and integrity checks still matter.

### 5. Backend / API behavior

The new server PostgreSQL service was installed and started for this request. Existing local application login/API behavior, notification workers and database settings were unchanged. No Django or Flutter deployment was performed. The database password is for the new `campushub_app` PostgreSQL account; it is different from the server's root SSH password. The role cannot create databases or roles and is not a superuser. Root SSH was used only for this initial server administration and encrypted transfer. Passwords and private keys must not be pasted into chat.

### 6. Database / migration impact

The source database was read for export and was not modified. The destination now contains the copied schema, records, indexes, constraints and saved sequences. Its copied `django_migrations` table contains 100 records. These are restored records, not newly executed Django migrations; no `manage.py migrate` command was run. Uploaded media files are separate from database records and were not copied. This is a snapshot copy, not ongoing replication.

### 7. Tests / verification actually performed

- Authorized root SSH login succeeded after the user's terminal setup.
- Fresh existing-service `pg_dump`: exit 0, completion marker present, 42 tables/data sections, SHA-256 recorded.
- New helper executed successfully on that dump: 42 tables, 1,798 rows, 33 sequence states.
- Destination PostgreSQL 18.6 installed successfully; active cluster and startup enablement verified.
- Both transferred file checksums matched their local inputs.
- Actual transactional restore succeeded, then all 42 per-table row counts and all 33 sequence states matched the dump (1,798 total rows).
- All 42 application tables are owned by `campushub_app`; zero unvalidated constraints were reported.
- Actual TCP password login as `campushub_app` returned the expected database and 100 copied migration records; role superuser status is false.
- PostgreSQL listens on loopback only, not the public network. Server dump/credential permissions `0600` and directory permission `0700` were checked.
- Both new Python helpers compiled successfully; documentation whitespace checks and Git ignore checks for private artifacts passed.
- No application regression suite, live web deployment or pgAdmin GUI connection was claimed; those were not performed.

### 8. Remaining limitations / troubleshooting / safe practice

To view the copied database in Windows pgAdmin, register a **new server** named `CampusHub Kamatera`. In its **Connection** tab, use:

| Field | Value |
| --- | --- |
| Host name/address | `127.0.0.1` (the database host reached through SSH) |
| Port | `5432` |
| Maintenance database | `campushub` |
| Username | `campushub_app` |
| Password | Open the private JSON file above locally and use its `password` value; do not paste it into chat. |

In the **SSH Tunnel** tab enable tunneling, set tunnel host `74.113.234.180`, port `22`, username `root`, authentication **Identity file**, and identity file `C:/Users/leste/.ssh/id_ed25519_campushub_kamatera` (the private key, without `.pub`). The generated key has no passphrase, so a key passphrase is not required. These are pgAdmin's existing [server connection and SSH tunnel settings](https://www.pgadmin.org/docs/pgadmin4/latest/server_dialog.html). No public PostgreSQL firewall rule is needed. After Save, browse `Databases -> campushub -> Schemas -> public -> Tables`.

Read-only inspection from the project root:

```powershell
.\backend\core\venv\Scripts\python.exe .\scratch\database-backup\copy_to_kamatera.py
```

Expected: PostgreSQL 18.6, localhost binding, `campushub` present and `campushub_app` present. Do **not** rerun `--copy` expecting synchronization: it will refuse the existing destination. To verify the connection itself without opening an interactive shell:

```powershell
ssh -i "$env:USERPROFILE\.ssh\id_ed25519_campushub_kamatera" -o IdentitiesOnly=yes -o BatchMode=yes root@74.113.234.180 'id; cat /etc/os-release'
```

Expected: the remote user and operating-system metadata. Initial rejected password attempts did not prevent the later successful key authorization. An initial post-install inspection command also failed because Windows/OpenSSH split a quoted SQL argument; installation itself succeeded. The helper resolved this using Python subprocess argument lists/stdin, not a database authentication change. If access later fails, check the correct SSH identity/user and server/network state; do not disable host-key verification or expose PostgreSQL publicly.

Safe exercise: run the inspection command above and confirm that it reports the expected names without changing them. In pgAdmin Query Tool, `SELECT current_database(), current_user;` should return `campushub` and `campushub_app`. To count tables safely, use `SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';` and expect 42. These queries are read-only. Keep backups/keys/passwords private.

Remaining work is separate: deploy Django/FastAPI and static/media files, configure server-side application credentials, and connect the intended clients. Changes made to the local database after the backup snapshot are not automatically copied. No claim is made that the website or mobile app is already using Kamatera. When eventually deploying the app, verify pending migrations and configure notification/chat workers deliberately rather than launching duplicate services from this database operation.

---

# Earlier local backup before Neon

## 1. Cause / reason

On October 19, 2026, the user requested a database backup before any Neon configuration or transfer. The confirmed source is the existing local `campushub` PostgreSQL 18.6 database on `localhost`. No Neon connection has been configured or attempted in this operation.

The existing full-backup service was reused, rather than adding a second application backup implementation. This makes a plain SQL export compatible with the current Backup & Restore workflow. A database export includes database content, not uploaded media files stored on disk.

## 2. Exact files and code anchors

| File | Current line / nearby anchor | Purpose |
| --- | --- | --- |
| `scratch/database-backup/backup_before_neon.py` | 16 `ROOT`; 24 `main`; 107 entry point | New one-off runner: inspect the source, guard the local target, call the existing full-backup service, and verify the resulting file. |
| `backend/backups/.gitignore` | 1 private-export comment; 2 `*` | New folder rule keeps newly created database exports, checksums and reports out of Git. It does not untrack older already committed files. |
| `docs/database-backup-neon.md` | 1 title | This operation, data flow, verification, troubleshooting and practice guide. |
| `backend/core/accounts/backup_service.py` | 9 `BACKUP_DIR`; 13 `get_db_config`; 25 `create_backup` | Existing functions reused unchanged. |

New local output files in `backend/backups/`:

- `campushub_postgres_20261019_211959.sql`
- `campushub_postgres_20261019_211959.sql.sha256`
- `campushub_postgres_20261019_211959.verification.json`

Application source, environment configuration and models were not changed.

## 3. Changes made

The runner imports settings without calling `django.setup()` or starting the app, server or notification worker. It refuses to proceed unless the database is named `campushub` and its configured host is local. Its inspection connection is explicitly read-only. Running without `--create` only reports the database name, host, PostgreSQL version, database size and base-table count.

With `--create`, it calls `create_backup(backup_type="full")`. After successful `pg_dump`, it scans the local SQL file without displaying records, checks nonempty output and the dump completion marker, counts table definitions and data sections, and calculates SHA-256. The report and checksum are written as new files. Existing backups were not removed or overwritten.

## 4. How it works: functions, inputs and outputs

`get_db_config()` reads the current Django `DATABASES['default']` settings and returns connection parameters in memory. The password is passed privately to the existing service, never printed or placed in the verification report.

`main()` takes one optional flag, `--create`. Inspection queries return metadata only. `create_backup('full')` then runs the installed PostgreSQL `pg_dump` and returns a success/result dictionary. On success, the runner outputs a metadata-only JSON summary and creates the three local artifacts above. A failed service or content check exits without claiming a verified backup.

Data flow:

```text
Django settings -> existing get_db_config()
                -> local read-only metadata queries
                -> existing create_backup('full') -> pg_dump -> private .sql file
                -> completion/content checks + SHA-256 -> checksum + JSON report
```

Example: `--create` means "make a new full backup," while omitting that flag means "inspect only." No command in this runner restores data. `pg_dump` takes its own consistent database snapshot; the earlier metadata count is a separate read, not a shared exported snapshot. Changes made after that dump snapshot are not included.

## 5. Backend / API behavior

No API request, approval, seller/product/order/payment/booking change, or notification send was made. Existing sessions and running processes were left alone. The SQL file uses the existing `campushub_postgres_*.sql` filename pattern, so it can be found by the existing backup-list function.

## 6. Database / migration impact

This was an export only. No records, schema, migrations, connection settings or Neon data were changed. Database roles outside this database and media files are not backed up by this operation. A subsequent Neon transfer should be rehearsed against an empty isolated target, with ownership/permission differences handled deliberately. Do not test a restore against the current live database.

## 7. Verification performed

The actual backup completed at `2026-10-19T13:20:00.513529+00:00` (9:20 PM Philippine time):

| Check | Actual result |
| --- | --- |
| Source PostgreSQL / database | 18.6 / local `campushub` |
| Source database size | 13,080,255 bytes |
| Source base tables before dump | 42 |
| Existing full-backup service / pg_dump | Success, exit code 0 |
| SQL file size | 348,226 bytes (about 340 KiB) |
| SQL table definitions / data sections | 42 / 42 |
| PostgreSQL dump completion marker | Present |
| Independent PowerShell `Get-FileHash` comparison with report | Matched |
| SHA-256 | `4ac7a57bb02ee91e75460d25ad40a022ee1e59809366de34724ea2b5558f269b` |
| `git check-ignore` for all three new backup artifacts | All ignored |
| Restore into another database | Not performed |

The smaller SQL file size compared with the source database is expected: a logical dump describes schema and records rather than copying PostgreSQL's on-disk allocation and index pages. Size alone does not establish restorability.

## 8. Remaining limitations, troubleshooting and safe practice

No restore rehearsal has been performed, so these checks do not prove a successful end-to-end restore. Keep this backup private and retain a separate secure copy before any later migration. Media and application configuration need separate backup handling. The existing service has a 120-second timeout; this export completed within it. A failed or timed-out attempt can leave an incomplete file, which must not be treated as this verified output.

The first inline inspection attempt was blocked by sandbox access to the installed base Python; a subsequent inline command encountered PowerShell argument quoting. Neither reached the database. Running the saved file with approved execution then succeeded. No code workaround bypassed database authentication or permissions.

Safe practice from the project root: inspect without creating another backup:

```powershell
.\backend\core\venv\Scripts\python.exe .\scratch\database-backup\backup_before_neon.py
```

Expected output: metadata for local `campushub`, with no password or row values and no new `.sql` file. For an authorized later backup, the same runner accepts `--create` and produces a new timestamped file.

Exercise: verify this backup without restoring anything:

```powershell
Get-FileHash -LiteralPath .\backend\backups\campushub_postgres_20261019_211959.sql -Algorithm SHA256
```

Compare the returned hash with the value above or in the neighboring `.sql.sha256` file; letter case does not matter. A mismatch means this file is not byte-for-byte identical to the verified backup. This read-only exercise does not write to the database or start/restart CampusHub.
