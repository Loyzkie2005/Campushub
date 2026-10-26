# CampusHub dashboard Improvement #5: System Status

## Chat timeout recovery — 2026-10-06 (current behavior)

The original report below describes the initial feature. This update documents the pasted terminal error and its fix; later status-color guides remain authoritative for colors.

### 1. Cause / Reason

Confirmed from the pasted output: the chat `/health` request timed out while Django still served the dashboard and dashboard API successfully. At inspection time, nothing was listening on port 8001. The dashboard caught the connection exception correctly but logged it with `exc_info=True`, printing a long traceback on every attempted check. This was an offline health result, not an uncaught dashboard crash. The unrelated broken marketplace layout is explained in [the layout recovery guide](top-products-sample-photo-layout.md).

We started the existing configured FastAPI service in the background using its own virtual environment. Its startup completed, port 8001 was listening, and Django's actual `chat_service_status()` returned `online`. This supports the service being unavailable at inspection time; it does not establish why the earlier process stopped.

### 2. Exact Files Changed

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_health.py` | 61 `except (HTTPError, URLError, ...)` | Expected transport failures log one safe warning with the exception class, without a traceback or private exception message. |
| `backend/core/modules/reports/test_dashboard_health.py` | 52 `test_chat_http_error_timeout_and_bad_json_are_isolated`; 58 `logs.records` | Existing failure test now verifies one warning, no traceback and no private details in logs as well as API output. |
| `docs/dashboard-system-status-5.md` | This update | Cause, service startup instructions, function/data-flow explanation and checks. |

Runtime logs for the background service are in `scratch/dashboard-global-review/chat-recovery.out.log` and `chat-recovery.err.log`. Service startup did not modify application configuration files.

### 3. Changes Made

An expected connection failure now logs a concise message such as `Dashboard chat health endpoint is unavailable (URLError).` The dashboard continues showing Unavailable until a real health response verifies Online. Unexpected malformed-response failures keep their existing diagnostic handling. The 1.5-second network timeout remains in place.

### 4. How It Works

`chat_service_status()` at line 41 takes no arguments. It reads the server-controlled `CHAT_SERVICE_HTTP_URL`, sends a small read-only request to `/health`, validates the JSON, and returns a dictionary with `status`, safe `message` and actual `checked_at` time. Valid `{"status":"ok"}` returns Online; timeout/refusal/HTTP failures return Unavailable. The function does not start the service automatically or send any chat messages.

Data flow: System Status browser script → authorized Django dashboard health endpoint → `build_system_status()` → `chat_service_status()` → FastAPI `/health` → verified status dictionary → browser label. Changing the logger alters terminal diagnostics, not the status calculation.

```python
except (HTTPError, URLError, TimeoutError, ConnectionError, OSError) as error:
    # The class tells us which kind of failure occurred without exposing its details.
    logger.warning("Dashboard chat health endpoint is unavailable (%s).", type(error).__name__)
    return _state("unavailable", "Real-time messaging is currently unavailable.")
```

This keeps an actionable warning while avoiding repeated traceback noise for an expected offline dependency. It does not hide an actual health failure.

### 5. Backend / API Behavior

The existing authorized `GET /api/admin/dashboard/?system_status_only=1` contract and RBAC remain unchanged. Health-only responses still complete even when chat is offline. Django remains the main backend; FastAPI remains chat-only. The current live function probe returned Online after starting FastAPI.

### 6. Database / Migration Impact

None. No models, credentials, `.env` settings or migration files changed. No live order/product/chat records were inserted or deleted. Starting `/health` and running the read-only Django probe did not run schema migrations or send messages. Automated tests used the separate Django test database.

### 7. Tests Performed

- All six existing `ServiceHealthTests` passed, including validated JSON, short timeout, offline transport failures, malformed responses and invalid configuration. The updated failure assertions verify sanitized output and traceback-free expected warnings.
- The marketplace fixture/export test passed in the same run: seven targeted Django tests total. Django system checks reported no issues.
- Live check: FastAPI startup completed; a port 8001 listener existed; the actual Django `chat_service_status()` returned `online` with its real check timestamp.

Manual troubleshooting:

1. Run Django in `backend/core` as usual. Django's port 8000 does not start FastAPI's port 8001.
2. Check chat directly in PowerShell: `Invoke-RestMethod http://127.0.0.1:8001/health`. Expected result: `status: ok`.
3. If the service is not running, open a second terminal and use the existing configured environment:

   ```powershell
   cd C:\Users\leste\Desktop\CAMPUSHUB\backend\chat_service
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001
   ```

   Keep that terminal open. Do not launch another instance if port 8001 is already in use. For local-only development, `--host 127.0.0.1` is sufficient; the current existing LAN/mobile configuration uses `0.0.0.0`.

4. Refresh the dashboard to request a new verified System Status check. If direct health works but Django still says Unavailable, check the configured `CHAT_SERVICE_HTTP_URL` origin and service logs. Do not copy secrets into reports.

Safe learning exercise: run only the existing isolated failure test from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_health.ServiceHealthTests.test_chat_http_error_timeout_and_bad_json_are_isolated --keepdb --noinput
```

The test substitutes a timeout through `patch()`, checks the Unavailable result and inspects the captured log. This lets you learn failure handling without stopping your live service or changing production settings.

### 8. Remaining Limitations

The background service started for this session is not a Windows startup service and will not automatically survive a reboot. `/health` verifies that FastAPI responds; it does not prove chat database access, WebSocket delivery or end-to-end messaging. No live messages were sent. A future stopped/unreachable service will honestly show Unavailable and log the concise warning again.

---

System Status now monitors real service state through the existing Super Admin dashboard API. The hardcoded Database Online label and vague Manage Settings action are removed. Database, Chat Service and Backup share a compact white surface, with three columns when space permits and a vertical layout on narrow screens. Open Backup is the only service action.

## Cause / reason

Database previously displayed Connected/Online without a check. Chat previously accepted any successful HTTP response, without validating the FastAPI health body. Backup displayed only an Open link. These could imply healthy services without supporting evidence.

## Exact files changed

Approximate current line numbers and nearby anchors:

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/reports/dashboard_health.py` | 29 `database_status`; 41 `chat_service_status`; 78 `backup_status`; 125 `build_system_status` | New lightweight, read-only probes and sanitized response objects. |
| `backend/core/modules/reports/views.py` | 1591 `system_status_only` | Authorized health-only branch in the existing dashboard API. |
| `backend/core/accounts/backup_service.py` | 247 `get_auto_backup_config` | Optional `strict=True` reports unreadable/malformed preferences to the health probe. Existing callers retain their fallback behavior. |
| `backend/templates/dashboard/partials/system_status.html` | 1 heading; 4 `dashboardSystemStatus` | New three-service markup, accessible status text, metadata and Open Backup. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 17 CSS; 181 partial include; 589 JS | Include scoped assets and replace the old static section. |
| `backend/static/components/css/admin_system_status.css` | 1 `#dashboardSystemStatus`; container rule | Scoped compact layout, semantic dots/text, readable subtitles, responsive stacking and focus styles. |
| `backend/static/components/js/admin_system_status.js` | 14 `render`; 44 `checkSystemStatus`; 72 refresh listeners | Load/refresh checks, real timestamps, unknown/error states, race protection and timeout. |
| `backend/static/components/js/admin_dashboard.js` | After `applyFacilityUtilizationBars()` | Remove the obsolete browser-to-FastAPI HTTP-only status check. Chart behavior remains unchanged. |
| `backend/core/modules/reports/test_dashboard_health.py` | `ServiceHealthTests` / `BackupHealthTests` | Probe, failure, source, authorization and isolation tests using mocks and temporary backup files. |
| `backend/core/modules/reports/test_dashboard_periods.py` | `test_global_dashboard_markup_and_review_artifact` | Assert unknown initial states, new section/script and removal of hardcoded labels/action. |
| `docs/dashboard-system-status-5.md` | This report | Implementation, verification, limitations and manual checks. |

Review helpers and screenshots are in `scratch/dashboard-global-review/`: `check-system-status.cjs`, `prepare-system-visual.cjs`, `verify-system-visual.cjs`, and `system-desktop.png`, `system-mobile.png`, `system-failed.png`. Their HTML/JSON comes from isolated test records; it does not supply application statuses.

## Changes made / how it works

The server-rendered section starts at **Unknown / Not checked yet**, then JavaScript checks the services once after the page loads. Nothing starts at Online or Healthy by default. Each row has a navy decorative SVG icon, service name, textual status, explanation and an actual last-checked time. Backup also shows the last available completed-file timestamp when known.

Green indicates Online/Healthy; gold dots with navy text indicate Warning/Degraded/No Backup Available; red indicates Unavailable/Failed; muted text/dots indicate Unknown. The full card remains white. Status meaning is always present as text.

No additional large Refresh control or continuous polling is added. Existing global Refresh and dashboard Retry request both dashboard data and service health. Historical date selections/grouping changes do not issue extra health checks. Health loading switches to Unknown with Checking service status, so a previous green status is not presented as a new verification.

## Backend / API behavior

Existing route: `admin_dashboard_api`, `GET /api/admin/dashboard/?system_status_only=1`.

This mode returns a `system_status` object with `database`, `chat_service`, and `backup`, each containing `status`, safe explanatory `message`, and `checked_at`. Backup adds nullable `last_successful_backup`. Normal KPI/analytics requests keep their existing behavior and query count. This is a separate lightweight mode on the same endpoint, allowing checks to finish independently when analytics fail.

The existing Super Admin authentication, active-user check, dashboard access check, GET-only behavior, and no-cache response headers apply. Unauthenticated requests receive 401; other roles receive 403; POST receives 405. Health data is not made public.

### Database

Uses the configured Django database connection and a single **`SELECT 1`**. Online requires the expected result. Connection exceptions produce Unavailable and are logged server-side. An unexpected result is Unknown. No table scans, credentials, hostname, connection string or raw exception text are returned.

### Chat Service

Reuses FastAPI's existing **`GET /health`** endpoint. Django checks the server-configured `CHAT_SERVICE_HTTP_URL`; it does not derive a destination from the requesting browser's host or query parameters. There is no new FastAPI endpoint and no change to messaging logic.

- Timeout: **1.5 seconds**.
- Response body read limit: **4 KiB**.
- HTTP 200 with JSON `status=ok`: Online.
- An explicit `status=degraded`: Degraded, if the service ever reports it.
- Timeout, refusal or unsuccessful HTTP response: Unavailable.
- Invalid configuration, malformed/unexpected JSON or oversized body: Unknown.

This avoids cross-origin browser health requests and validates the service's actual health contract. Chat failures are logged server-side and do not fail the whole dashboard.

### Backup source and definitions

Reuses the existing Backup & Restore implementation:

1. Matching `campushub_*.sql` files under its existing `BACKUP_DIR`.
2. File modification timestamp and file size, following that module's **nonempty file = Completed; empty file = Failed** rule.
3. The newest existing `AccountActivity` record for admin `activity_type=system_backup`, module `Backup & Restore`.
4. Existing automatic-backup preferences, including their current defaults if no settings file exists.

Only file metadata is read. A single directory pass retains the latest file and latest completed file; one limited ORM query retrieves the newest attempt's result/time. File contents and full activity history are not loaded or returned. Restore activity is excluded.

| State | Rule |
| --- | --- |
| Healthy | A completed backup file exists, no newer known failure supersedes it, and it is within the enabled frequency preference; disabled automatic preferences are stated explicitly. |
| Warning | The last completed file is older than the enabled daily/weekly/monthly preference. |
| Failed | A failed recorded attempt is at or after the last completed file, or the latest file is empty/marked failed by existing rules. The previous completed-file time remains visible if it exists. |
| No Backup Available | No completed backup file exists and no current failure takes precedence. A success log alone cannot imply a still-available file. |
| Unknown | Files, attempt records or required schedule preferences cannot be verified. Known completed-file metadata may still be shown alongside Unknown. |

Age limits are one day, seven days, or one calendar month after the completed file, with month-end dates clamped appropriately. They describe freshness relative to saved preferences, not proof that a scheduler ran. No timestamps are invented from filenames or frontend time.

Open Backup uses the existing `admin_backup_page` (`/admin-backup/`). Creating, downloading, deleting and restoring backups retain their existing behavior and permissions. Health checks do not initiate backups or restores.

## Error / unknown states and refresh

Each backend probe handles its own failure. A Chat outage therefore still allows Database and Backup results. The health-only branch does not compute marketplace/facility analytics.

The browser allows **5 seconds** for the status request, aborts superseded requests, and ignores stale responses. If Django cannot be reached, authentication fails, the request times out, or data is absent, the displayed service state is Unknown with Unable to verify service status. Previous green states and current-check timestamps are cleared. Other dashboard data and its existing Retry flow remain independent.

Exact timestamps use the dashboard's **Asia/Manila** display timezone. Checked-at values represent actual completed probe attempts, including unavailable outcomes; the browser does not manufacture Last checked times.

## Database / migration impact

No schema, model, migration, production record or saved preference changes. Existing PostgreSQL configuration and FastAPI code are unchanged. The backup-config helper's optional strict argument preserves the behavior of its existing callers.

## Tests performed

- **65 Django tests passed:** `modules.reports.test_dashboard_health`, `modules.reports.test_dashboard_periods`, `modules.reports.test_sales_overview`, and `accounts.tests.DedicatedDomainDashboardTests`.
- Covered minimal database query/result and failure sanitization; chat health-body validation, HTTP failures, timeout, invalid JSON/configuration and body limit; real temporary-file timestamps; backup freshness/preferences, calendar months, disabled preferences, zero-size files, recorded failures/recovery, removed files, unrelated restore records, unreadable sources, invalid config, and bounded latest-attempt query.
- Authorization and independent status-only behavior passed while analytics were configured to fail in the test.
- `check-system-status.cjs` passed initial checks, timestamps, all displayed semantic states, global Refresh/Retry integration, authentication parameter preservation, partial health failure, analytics failure, superseded responses, client timeout and sole Open Backup action.
- Existing `check-controls.cjs` and `check-attention.cjs` passed. JavaScript syntax, CSS parsing and scoped `git diff --check` passed.
- Offline Chrome screenshots were inspected together for desktop, narrow and failed states. Measurements confirmed three columns at 1536px/960px content widths and one column at 342px within a 390px frame; no horizontal overflow. The narrow frame check is not a physical mobile-device test. Offline screenshots use existing fallback fonts; the application keeps its Montserrat setup.
- The design detector used its limited regex fallback. It was supplemented with actual CSS parsing, DOM checks and browser measurements.
- **Read-only live probe on Oct 04, 2026 at about 4:56 PM Manila:** Database Online, Chat Service Online, Backup Warning. Latest completed backup-file metadata: **Aug 12, 2026 at 3:26 PM Manila**, older than the daily preference. No backup was created or restored for this probe.

## How to manually test each status

Use development/test data for failure scenarios; do not damage current backup files or stop a production database for verification.

| Service / state | Check |
| --- | --- |
| Database Online | Open the Super Admin dashboard with PostgreSQL running. Verify Online, explanatory text and an actual Last checked time. Click global Refresh and verify the time updates. |
| Database Unavailable | Run the isolated `ServiceHealthTests.test_database_errors_are_unavailable_without_disclosing_exceptions` test to exercise the connection failure. A failure after authorization should produce Unavailable without raw details. During a complete database outage, authentication may prevent the endpoint from running; an already-open page then shows Unknown instead. |
| Chat Online | Run the existing FastAPI messaging service and verify `/health` returns its normal `status=ok`. Refresh the dashboard and verify Online. |
| Chat Unavailable | In a development environment, stop only the chat service or configure an unreachable test service address, then Refresh. Verify Unavailable while KPI loading and Database status continue to work. Restart and Refresh to recover. |
| Chat Unknown / Degraded | Use the isolated health tests or a development health stub returning invalid JSON/unexpected status, or explicitly `status=degraded`. Verify Unknown/Degraded without falsely marking Online. |
| Backup Healthy | On a test installation, create a successful backup with the existing Backup & Restore page. Refresh the dashboard and check its actual last completed-file timestamp and Healthy result within the configured frequency. |
| Backup Warning | Use an isolated backup directory with a completed file older than the configured daily/weekly/monthly interval. `test_saved_frequency_and_disabled_preference` exercises this without touching live backups. Verify Warning; compare with saved frequency preferences. |
| Backup Failed | Use the isolated `test_latest_zero_size_or_logged_failed_attempt_is_failed` fixture. It checks a newer empty file and a recorded failed attempt, while preserving the previous completed backup time. Follow with a newer successful file/record to verify recovery. |
| No Backup Available | Use an empty isolated backup directory and `test_empty_directory_has_no_successful_backup`. Verify No Backup Available and no fabricated timestamp. |
| Backup Unknown | Use `test_invalid_config_or_unreadable_sources_are_unknown` for permission errors, unavailable attempt records or malformed preferences. Verify Unknown rather than Healthy or a fabricated zero. |
| Browser/network Unknown | With the page already open, use browser offline/network failure simulation and click Refresh. Verify service states become Unknown; restore connectivity and click Refresh/Retry to check again. |

Also resize to a narrow window and tab to Open Backup. Verify readable status/subtitle, vertical stacking, focus indication and the existing backup route. Manage Settings should no longer appear in System Status.

## Remaining limitations

- FastAPI `/health` currently proves the HTTP process/health handler responds. It does not test chat database access, WebSocket delivery or every messaging dependency. The UI wording reflects that health-endpoint check.
- Backup completion follows the existing module's nonempty-file rule. It does not validate dump integrity or prove successful restoration. Existing legacy files may lack corresponding success audit records; their timestamps are filesystem modification times.
- The repository persists automatic-backup preferences but no scheduling worker was found in the inspected implementation. Freshness uses those preferences; Healthy does not attest that automated scheduling works, or that a file is a full rather than scoped backup.
- Database health inherits the configured driver's connection behavior. The tiny query is not a database load/performance assessment. If authentication itself cannot read PostgreSQL, the authorized endpoint may be unreachable and the browser correctly shows Unknown.
- No connected authenticated interactive browser was available. Function-level live probes, isolated API tests and actual-script/CSS offline Chrome checks were performed. No server restart, service interruption or production backup operation was performed.
