# PostgreSQL backups and server transfers

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
