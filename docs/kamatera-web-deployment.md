# CampusHub Kamatera web deployment

## Phone catalog images fixed on the server — October 20, 2026

### 1. Cause / reason

Confirmed: catalog JSON sent the phone `/media/...` image URLs, and those files existed under `/srv/campushub/shared/media`. Production Django has `DEBUG=False`; its old URL configuration only appended the development media handler when debug was enabled. Nginx deliberately had no unrestricted media alias. Consequently `/media/upload/products/fyfyfu_53.jpg` and the Covered Court image returned 404, although the existing `/api/products/53/image/` endpoint could read that same product image successfully. The blank catalog pictures were a missing production route, not missing copies of these files or a confirmed Flutter rendering problem.

### 2. Exact files changed / current anchors

| File | Line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/core/media_views.py` | 22 `_media_path`; 39 `_variant_images`; 51 `_is_visible`; 77 `catalog_image` | Normalize stored URLs, check database image visibility and stream only the permitted raster file. |
| `backend/core/core/urls_production.py` | 9 `urlpatterns` | Add the existing `/media/<path>` URL shape before all existing application routes, only for production. |
| `backend/core/core/settings_production.py` | 31 `ROOT_URLCONF` | Select the production route wrapper. PC development settings remain unchanged. |
| `backend/core/core/test_media_views.py` | 16 `CatalogImageTests`; 48–105 test anchors | Eight real-ORM tests against an isolated database and temporary JPEG files. |
| `scratch/database-backup/deploy_catalog_media.py` | 17 `deploy`; 69 test creation guard; 101 activation after tests | Stage checked source, prepare/remove an isolated test database, and activate only after tests pass. |
| `docs/kamatera-web-deployment.md` | 3 image-fix report | Actual cause, functions, deployment, verification and recovery. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest image-fix note | Preserve completed server state and remaining limits. |

Server copies of the four `core/` files above were deployed with checksums recorded in ignored `backend/backups/kamatera-media-deploy-result.json`. Original production settings were saved privately at `/root/campushub-migration/settings-production-before-media-20261020T141215Z.py`. The passing test log is `/root/campushub-migration/media-test-20261020T141215Z.log`. Only `campushub-django` was restarted; Nginx and chat remained active. No `.env` or Nginx configuration changed.

### 3. Changes made

The production media adapter reuses `image_visible_product_queryset(request.user)` instead of introducing a second product approval policy. It permits exact gallery/variant image references belonging to visible products, gallery images of non-archived facilities/services matching the existing public facility catalog, and seller avatar paths already exposed by visible marketplace listings. Pending/rejected/archived product images are not made public simply because their files exist. Product administrators retain their existing scoped image access through the same helper.

Only the known product, facility and seller-avatar image namespaces are eligible. Unreferenced files, private booking/document directories, non-raster extensions, traversal and symlinks are rejected. Images are served with explicit content type, `nosniff`, and `private, no-store` so approval/archive changes are checked again instead of treating uploaded files as permanently public. No broad filesystem alias was added.

### 4. How it works: functions, inputs / outputs and data flow

`_media_path(value)` accepts a stored URL/path and returns a normalized relative media path or `None`. It does not fetch external URLs and rejects ambiguous/traversal components. `_variant_images(value)` walks the existing customization JSON to find image values. `_is_visible(request, path)` uses the existing product visibility queryset, exact normalized gallery/variant path comparison, the public non-archived facility predicate, or a visible product's seller-photo reference. A basename filter narrows database candidates, but access is granted only after an exact path match; matching a filename fragment alone is insufficient.

`catalog_image(request, image_path)` accepts GET/HEAD, verifies the raster extension and visibility, resolves the target inside `MEDIA_ROOT`, refuses symlinks/outside targets, then returns `FileResponse`. A missing, unreferenced or unauthorized file returns 404. The production URL wrapper imports all existing application routes and adds this one adapter without replacing the existing product-image API.

```text
Phone GET https://campushub-ch.duckdns.org/media/upload/products/fyfyfu_53.jpg
  -> existing Nginx Django proxy
  -> core.urls_production
  -> catalog_image: exact image reference + existing product approval visibility
  -> /srv/campushub/shared/media/upload/products/fyfyfu_53.jpg
  -> image/jpeg response
```

`deploy()` uses the existing dedicated SSH connection, checks original production settings against the expected previous hash, and refuses unknown existing target files. It stages new files separately. Test setup copies only live schema and migration metadata into a uniquely named `test_campushub_media_...` database, not live user/order/product data. Fixture images/records are created there only. The test process is configured to that database explicitly, and the helper drops that exact verified temporary database in `finally`, including after a test failure. After a passing run it backs up settings, copies checked source, and restarts the known Django unit.

### 5. Backend / API behavior

Existing image URLs now work without changing the mobile response contract or rebuilding the APK. Product approval, seller permissions, booking rules and existing APIs remain intact. Actual live checks enumerated image fields from approved products, facilities and services, fetched each unique local image URL, and verified its bytes with Pillow. The check did not create records or submit credentials.

This route intentionally does not publish arbitrary private/non-seller profile photos or a mobile seller's unpublished product images without their appropriate authorized request. Blank placeholders for records with no saved image remain expected; no substitute photo or fabricated image was added.

### 6. Database / migration impact

No live migration, schema, credential, approval status or application record changed. Production database access was read-only for schema/migration-metadata copying and public catalog checks. Two disposable test runs used separate temporary test databases, both removed by the guarded helper. Django's test-runner text says it preserves the test database with `keepdb`; the outer helper then explicitly removes that database, so the isolated fixtures do not remain online.

### 7. Verification actually performed

- Python compilation succeeded for all five Python files involved in this change.
- Eight integration tests passed on the Linux server using its real PostgreSQL schema in an isolated database. They cover gallery/variant bytes, private unpublished/archived images, authorized product-admin access, denial for an ordinary authenticated user, facility archive visibility, public seller avatars, unreferenced/private documents, traversal and symlink escape. The Django system check reported no issues.
- The initial test run failed because the test explicitly closed a streaming response after the Django test client's iterator had already closed it; that triggered connection cleanup inside `TestCase`'s transaction. Removed that redundant test-only close and reran successfully. No failed staging run was activated.
- Live public check: **20 unique catalog image URLs checked; 20 returned valid image bytes; zero failures**. Results are in ignored `backend/backups/kamatera-public-image-check.json`.
- Live negative checks for `/media/bookings/private.jpg`, `/media/upload/products/not-a-saved-image.jpg` and `/media/private.env` returned 404. Scoped whitespace checks passed.
- Deployed file hashes were recorded; Django, chat and Nginx reported `active` after activation. No phone screenshot/runtime inspection or authenticated mobile photo-upload workflow is claimed.

### 8. How to test, limitations and safe practice

Close and reopen CampusHub on the phone, then refresh Marketplace, Facilities and Services. This clears stale in-memory failed image loads. **No additional APK is required for this server image fix**; the existing online APK already requests these URLs. A phone still running an older LAN-only APK must first install the previously provided `campushub-online.apk` as Update.

Safe exercise: open `https://campushub-ch.duckdns.org/media/upload/products/fyfyfu_53.jpg` in a browser and confirm a real product image appears. Then open `https://campushub-ch.duckdns.org/media/upload/products/not-a-saved-image.jpg`; expect 404. This demonstrates why merely knowing a filename is not permission to publish it. These GET requests do not write application data. If a specific image is still blank, compare the API's exact saved path, its database visibility and the actual file under shared media before changing permissions. Do not enable `DEBUG=True` or a blanket public `/media/` alias as a workaround.

The first-time deploy helper refuses existing deployed files on a repeat invocation; do not bypass its guards. For recovery, inspect the recorded checksums and private production-settings backup first. Existing private profile/unpublished seller-image presentation, future missing uploads, SMTP/FCM and real phone end-to-end workflows remain separate concerns; the verified outcome here is delivery of all currently published catalog image references.

---

## Earlier mobile APK configuration step (catalog image delivery is resolved above)

## Mobile APK connection update — October 20, 2026

### 1. Cause / reason

The user reported that mobile could not load Marketplace and other data after the website was deployed. Confirmed source cause: `ApiConfig` still selected PC/LAN addresses on port 8000, and chat used a separate port 8001. Public HTTPS API checks returned real records: 13 approved products, 2 physical facilities and 1 service. The existing installed APK's binary/runtime was not inspected, so its exact current endpoint is inferred from the previous configuration rather than directly observed on the phone.

An existing installed APK does not change when the PC's Dart source or Django `.env` changes. It needs a newly built APK with the public API address. The phone calls Django; it must never receive the PostgreSQL database password.

### 2. Exact files changed / current anchors

| File | Current line / code anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/config/api_config.dart` | 7 `publicBaseUrl`; 13 `_readPublicBaseUrl()` | Optional compile-time HTTPS origin, validated without including credential values in an error. |
| Same file | 61 `recordWorkingBaseUrl`; 75 `baseUrl`; 79 `chatHttpUrl`; 92 `chatWebSocketUrl`; 111 `serverBaseUrls` | Reuse the shared configuration for online API and same-origin chat; keep online requests pinned to the configured server. |
| `campushub/lib/module_app/services/product_service.dart` | 100 `connectionMessage` | Online connection failures give internet/retry guidance; LAN builds keep existing PC guidance. |
| `campushub/lib/module_app/services/facility_service.dart` | 51 result `message` | Same build-appropriate connection guidance for facilities. |
| `campushub/lib/module_app/services/auth_service.dart` | 285 result `message` | Same build-appropriate connection guidance for authentication. |
| `campushub/test/api_config_test.dart` | 8 local group; 40 online group | Preserve the two LAN checks and add four online request/routing tests. |
| `docs/kamatera-web-deployment.md` | 3 mobile report | Explain cause, build/install steps, data flow and tests. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest mobile note | Preserve the actual mobile configuration/build state. |

### 3. Changes made

Added `--dart-define=CAMPUSHUB_API_BASE_URL=https://campushub-ch.duckdns.org` support in the existing shared `ApiConfig`. No duplicate API service, product controller or search system was created. Builds without that define retain the current PC/LAN behavior. Builds with it use one validated HTTPS origin and cannot switch remembered server state to an unrelated host or silently fall back to a private PC address after an error. Chat uses HTTPS `/chat` and WSS `/chat/ws` on the public origin, matching the deployed Nginx routing. No UI layout, API payload or product/booking logic changed.

### 4. How it works: functions, inputs / outputs and data flow

`_readPublicBaseUrl()` receives the build-time string, checks HTTPS plus a hostname, rejects credentials, paths other than `/`, query strings and fragments, and returns its normalized origin. An invalid nonempty define raises a configuration error instead of silently selecting LAN. `baseUrl` chooses that origin, or the existing PC URL when the define is absent. `serverBaseUrls` returns exactly one destination in online mode. Existing product, facility, service, order, seller and authentication code already consumes that shared configuration.

`recordWorkingBaseUrl(candidate)` still remembers successful LAN candidates during local development. In online mode it accepts only the configured origin, preventing unrelated successful/test responses from changing the destination used for authenticated requests. `chatHttpUrl` and `chatWebSocketUrl` select the existing proxy path prefix rather than public ports 8000/8001.

```text
Online APK build-time URL
  -> existing ApiConfig
  -> existing mobile product/facility/service/authentication requests
  -> https://campushub-ch.duckdns.org/api/...
  -> Nginx -> Django on Kamatera -> PostgreSQL on Kamatera

Chat: https://campushub-ch.duckdns.org/chat
      wss://campushub-ch.duckdns.org/chat/ws

PC Django .env DATABASE_URL -> PostgreSQL through the PC SSH tunnel
                             (this does not configure an installed APK)
```

Example: `ApiConfig.serverBaseUrls` becomes `['https://campushub-ch.duckdns.org']`, and the existing product loader requests `/api/products/approved/` from that address. Keeping the choice in one place avoids separate conflicting product, facility and chat settings.

### 5. Backend / API behavior

Backend code, server configuration and permissions were not changed by this mobile update. Actual public catalog requests returned HTTP 200/JSON. No credentials were submitted, no orders/bookings/products were created, no chat message was sent, and no live test data was inserted. Local unit tests used mock responses only. The new APK still needs a phone installation and real login/catalog check before claiming phone end-to-end success.

### 6. Database / migration impact

None. No migration, database password, `.env`, schema or application record changed. The APK contains the public API origin, not the PostgreSQL connection string. The server remains responsible for database access and permissions.

### 7. Verification actually performed

- Scoped analysis of all five changed Dart files: no issues.
- Default/LAN configuration plus existing product loading/model, service catalog, profile photo and facility booking tests: 28 passed; four online-only tests skipped deliberately in that run.
- With the online dart define: four online tests passed; two LAN-only tests skipped deliberately. Checks cover API/auth/chat destinations, remembered-host isolation, a mocked request through the existing product loader, and an offline failure with no PC fallback.
- Public read-only APIs returned HTTP 200: approved products (13), facilities filtered to physical resources (2), services (1), and chat health. No fabricated data was added.
- One existing product-image endpoint sampled during diagnosis returned 404. That does not explain failure to load the catalog JSON; images remain a separate deployment concern. No claim that all thumbnails work is made.
- Release APK build succeeded in 284.9 seconds. Named artifact: `campushub/build/app/outputs/flutter-apk/campushub-online.apk`, 63,262,231 bytes (about 60.3 MiB), SHA-256 `b454608fc15d057fdda24882115f806b8a4957a34922bd5a0beef5ef0f050c6c`. ZIP CRC validation passed; all three compiled `libapp.so` files (arm64-v8a, armeabi-v7a, x86_64) contain the intended HTTPS origin. Android `apksigner verify --verbose` succeeded with APK Signature Scheme v2 and one signer. The build emitted SDK-tool version/deprecated-API warnings but exited successfully. No phone installation or app restart has been performed.

### 8. Build, installation, limitations and safe practice

Run in **Windows CMD/PowerShell**, not inside `.env`:

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\campushub
flutter build apk --release --dart-define=CAMPUSHUB_API_BASE_URL=https://campushub-ch.duckdns.org
```

Flutter's output is `build/app/outputs/flutter-apk/app-release.apk`. The verified, separately named copy to install is **`C:\Users\leste\Desktop\CAMPUSHUB\campushub\build\app\outputs\flutter-apk\campushub-online.apk`**. Transfer that APK to the phone and choose **Update** for the existing CampusHub app. Do not uninstall or clear app data as the first troubleshooting step. If installation reports a signature/version conflict, inspect the existing app/build identity first. This project currently signs release builds with its existing development/debug signing configuration; this is a testing APK, not a completed Play Store signing setup. See the [official Flutter Android build guide](https://docs.flutter.dev/deployment/android).

After updating, open CampusHub with internet available and retry Marketplace, Facilities and Services. Sign in again if the old session is rejected: server signing keys differ from the earlier local environment. Do not send passwords here. To verify independence from your PC, use the phone's mobile data and leave the PC Django development server stopped. The new public build should still fetch catalog data. The installed APK itself has not been checked on a phone in this step, and production images, email and FCM remain separate unfinished deployment work.

Safe practice exercise: run `flutter test --no-pub --dart-define=CAMPUSHUB_API_BASE_URL=https://campushub-ch.duckdns.org test/api_config_test.dart` from the Flutter folder. Expect four passed online checks and two deliberately skipped LAN checks. Then run `flutter test --no-pub test/api_config_test.dart` without the define; expect two passed LAN checks and four skipped online checks. These mocked tests do not write to the online database. A normal local `flutter run` without the public define still uses the existing LAN configuration; use the same define explicitly when you want that development run to target Kamatera.

---

## Public HTTPS website enabled — October 20, 2026

**Current address: https://campushub-ch.duckdns.org/**. The login page, its five directly referenced static assets, the approved-products API and chat health endpoint passed public HTTPS checks. Django, chat and Nginx run on Kamatera independently of the PC. Authenticated workflows, uploaded media, production email, push delivery and a public-address mobile build still need verification/configuration; this is not a claim that every feature has passed end-to-end testing.

### 1. Cause / reason

The previous private services listened only on server loopback. The initial certificate request for `campushub-ch-online.duckdns.org` failed with DNS `NXDOMAIN`. Cloudflare, Google and DuckDNS authoritative servers confirmed that old name did not exist. The user then clarified that the current name is `campushub-ch.duckdns.org`; both public resolvers returned `74.113.234.180`. This was a renamed hostname, not a confirmed Django, database, firewall or CSS problem.

### 2. Exact files changed / current anchors

| File | Line / code anchor | Purpose |
| --- | --- | --- |
| `backend/deployment/campushub-nginx.conf` | 3 `log_format`; 6 `map`; 11 HTTP server; 28 HTTPS server | Public reverse proxy, certificate paths, static files and WebSocket upgrade handling. |
| `backend/deployment/campushub-nginx.conf` | 44 `/static/`; 60 `/chat/`; 74 `/` | Route collected assets, FastAPI chat and existing Django views to their existing destinations. |
| `scratch/database-backup/configure_public_https.py` | 20 `configure`; 53 DNS guard; 69 `activate`; 95 certificate request; 101 `environment_updates`; 146 final activation | Guarded server setup using the existing dedicated SSH key. |
| `docs/kamatera-web-deployment.md` | 3 current HTTPS report | Current address, exact behavior, checks, recovery guidance and learning exercise. |
| `CAMPUSHUB_CONTEXT.md` | 3 public HTTPS note | Preserve the actual deployment state and renamed domain. |

Server changes: installed distribution packages `certbot` and `python3-certbot-nginx`; created `/etc/nginx/sites-available/campushub` and its enabled symlink; issued the domain certificate under `/etc/letsencrypt/live/campushub-ch.duckdns.org/`; created `/etc/letsencrypt/renewal-hooks/deploy/campushub-nginx`; enabled `certbot.timer`. Only `CAMPUSHUB_PUBLIC_BASE_URL` in `/etc/campushub/django.env` and `ALLOWED_ORIGINS` in `/etc/campushub/chat.env` changed to the new HTTPS origin. Root-only pre-change backups are in `/root/campushub-migration/`. The successful Nginx backup is `nginx-before-https-20261020T133117Z.tar.gz`. No local `.env` changed.

### 3. Changes made

Added HTTP-to-HTTPS redirection, a valid Let's Encrypt certificate, TLS 1.2/1.3, a 50 MiB request-body limit matching the existing Django upload limit, and a static-file alias pointing only to collected public static assets. The access-log format records the URI path without query parameters or referrers, avoiding normal access-log disclosure of admin tab tokens. This is not a claim that every possible application/error log has been audited.

Nginx overwrites the forwarded scheme/address and sends the exact configured host. `/chat/` strips its prefix before forwarding to existing FastAPI routes and supports WebSocket upgrades; `/` forwards to existing Django. The production environment origin updates automatically update Django host/origin settings and its chat URL bridge. Restarted only the two known server application services to load these origin changes; Nginx was reloaded after successful configuration validation. The PC's development servers, database tunnel and phone app were not restarted.

### 4. How it works: functions, inputs / outputs and data flow

`configure()` reads the local Nginx configuration, checks the public DNS address, and uses the existing authenticated SSH helper. It refuses unknown existing site contents, enabled links, renewal hooks or service-origin values. It accepts the known old HTTP-only bootstrap because the user renamed the domain. A private Nginx archive is saved before changes. `activate(text)` writes the intended site and runs `nginx -t` before reload; syntax failure restores the prior site bytes/link instead of loading invalid configuration.

The temporary HTTP-only bootstrap exposes the ACME certificate challenge path and returns 404 elsewhere. Certbot proves control of the actual domain through that path. After issuance, only the two expected origin values are updated with private backups; the script checks private Django/chat responses, then activates the HTTPS site. The certificate account was registered without an email address; renewal is automated, but there is no account contact email configured for notices. The deploy hook validates and reloads Nginx after renewal so it serves the renewed certificate.

```text
Browser: https://campushub-ch.duckdns.org
  -> DNS: 74.113.234.180
  -> Nginx HTTPS :443
       /static/... -> /srv/campushub/shared/static/...
       /chat/...   -> FastAPI on 127.0.0.1:8001 (prefix stripped)
       /chat/ws    -> existing /ws, with WebSocket upgrade headers
       other URLs -> Django/Gunicorn on 127.0.0.1:8000
                         -> PostgreSQL on server loopback :5432
```

For example, `/chat/health` becomes upstream `/health` and returns `{"status":"ok"}`. This approach keeps Django business logic and existing authorization intact and exposes only the public proxy, rather than opening the application/database listener ports. Nginx is the public entry point; `0.0.0.0` is a listening-address setting, not the website address to enter in a browser.

### 5. Backend / API behavior

Existing routes, views and permissions are reused. Public GET `/` returns the CampusHub login page; `/api/products/approved/` returns the existing JSON response; `/chat/health` returns status ok. HTTP redirects to the exact HTTPS hostname. WSS reaches the existing chat endpoint, which still rejects unauthenticated sessions after its timeout and rejects an untrusted Origin. No login credentials were submitted and no chat message was sent to a person during these checks.

There is deliberately no broad `/media/` filesystem alias. Raw upload URLs may currently return 404 with production `DEBUG=False`; product/document visibility needs a separate production-media review before any alias or adapter is added. Do not expose private booking documents or pending/rejected product files to make images appear.

### 6. Database / migration impact

No schema, role, database password, migration or intentional application-record write was performed. Existing PostgreSQL remains private on server loopback. Environment changes affected only the public hostname/origin. The live approved-products GET was a read-only application request; no sample records were added. A later user login can naturally create its normal session/audit records.

### 7. Verification actually performed

- Local helper compilation succeeded. The full final Nginx syntax was checked with a temporary test certificate that was not installed or publicly served; the actual deployed certificate/site also passed `nginx -t`.
- A temporary ACME probe file returned HTTP 200 with the expected contents from the PC using the server IP and intended Host header, then was removed after verifying its contents.
- Actual certificate issued for `campushub-ch.duckdns.org`, valid through January 18, 2027. Local and deployed configuration SHA-256 matched: `326afab70ba57b62f81989429e05820b3862667d4cececfb1e8b08f2b41e50ea`.
- Public trusted HTTPS login HTTP 200, CampusHub branding, and all five directly referenced local static assets HTTP 200 with expected image/CSS/JavaScript content types. HSTS was `max-age=3600`. The login GET issued no cookies; that request therefore did not verify cookie flags. Secure session/CSRF cookie settings remain enabled in production.
- Public approved-products API HTTP 200/JSON; public chat health HTTP 200/status ok; HTTP root redirect 301 to the new HTTPS root.
- Public WebSocket upgrades succeeded (101): allowed-origin unauthenticated connection closed with 1008 / Authentication timeout; untrusted-origin connection closed with 1008 / Origin not allowed. No authenticated messaging test is claimed.
- Nginx, Django and chat reported `active`; certificate-renewal timer reported `active`. `certbot renew --dry-run --run-deploy-hooks --cert-name campushub-ch.duckdns.org` exited 0: all simulated renewals succeeded, and the deploy hook validated/reloaded Nginx. Certbot labeled Nginx's successful syntax-check messages as hook "error output" because Nginx writes those messages to stderr; the check and renewal succeeded. Certbot's built-in random delay accounted for the initial wait.
- Compared each private server environment with its private pre-change backup: only its expected public-origin key differed, and both files retained mode 0600. A fresh Django read through SSH connected to database `campushub` on server loopback port 5432.
- The first certificate request failed for the obsolete domain; no successful certificate for that obsolete domain is claimed. No Flutter build/install or complete authenticated browser workflow was tested in this step.

### 8. Next steps, limitations and safe practice

Open **https://campushub-ch.duckdns.org/** in any browser. This runs on Kamatera; the PC's development server is not required. Sign in with an existing admin account to exercise the actual dashboard. Source edits on the PC do not automatically update the uploaded release. The Flutter API configuration still uses its LAN addresses and requires an explicit public HTTPS/WSS option and build before claiming the installed app works independently of the PC. Production SMTP/FCM credentials, a deliberate push-worker transition and authorized uploaded-media delivery are still pending; do not start duplicate workers.

Safe exercise in **Windows CMD**, not inside `.env`:

```bat
nslookup campushub-ch.duckdns.org
curl.exe -I https://campushub-ch.duckdns.org/
curl.exe https://campushub-ch.duckdns.org/chat/health
```

Expect `74.113.234.180`, HTTP 200, and `{"status":"ok"}`. These only check DNS/public routing and health, not every authenticated feature. If the domain changes again, stop and update DNS plus the known service origins/certificate/Nginx configuration together. Never bypass certificate validation with `-k` as the normal solution. For Nginx failure inspect `nginx -t` and the root-only pre-change archive before recovery; do not overwrite an unknown configuration. For a backend startup failure inspect its systemd journal privately and redact credentials before sharing. The helper's DNS guard now refuses issuance when DNS is absent/wrong, preventing pointless repeated ACME requests.

The Nginx proxy and WebSocket behavior follows the [official Nginx proxy reference](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) and [WebSocket documentation](https://nginx.org/en/docs/http/websocket.html); certificate challenge/renewal behavior follows the [Certbot user guide](https://eff-certbot.readthedocs.io/en/stable/using.html).

---

## Earlier private-services setup (superseded by the public HTTPS state above)

## Private production services configured — October 20, 2026

**Current state:** Django and chat run successfully on server loopback ports 8000/8001 as systemd services. Public Nginx routing and HTTPS are **not yet configured**. The older source-only state further below records the earlier staging step.

### 1. Cause / reason

After the user completed dependency installation, inspection confirmed the Linux environments contained Django 6.1.2, Gunicorn 26.2.0, FastAPI 0.152.0 and Uvicorn 0.54.0. The existing settings were for PC development (`DEBUG=True`, permissive origins) and the web chat bridge forcibly replaced public addresses with HTTP/WS on port 8001. This step prepares separate production settings and private persistent services without changing the user's PC database configuration or publishing an unfinished site.

### 2. Exact files changed / code anchors

| File | Current anchor | Change |
| --- | --- | --- |
| `backend/core/core/settings_production.py` | 12 `_required`; 25 `SECRET_KEY`; 30 `DEBUG`; 48 `STATIC_ROOT` | New explicitly selected server settings, private secrets, exact HTTPS origin, secure cookies/proxy settings and persistent static/media paths. |
| `backend/core/modules/messages/views.py` | 14 `_chat_service_config` | Preserve explicitly configured public HTTPS/WSS URLs; continue rewriting loopback defaults for LAN development only. |
| `backend/core/modules/messages/tests.py` | 10 `ChatServiceConfigTests` | Three database-free URL tests, alongside the existing two token tests. |
| `backend/deployment/campushub-django.service` | `ExecStart` | Django/Gunicorn service with two workers, bound only to server loopback. |
| `backend/deployment/campushub-chat.service` | `ExecStart` | Chat/Uvicorn service with one worker to preserve its existing in-memory WebSocket manager. |
| `scratch/database-backup/configure_private_web_services.py` | 25 `configure`; 160 entry point | Guarded first-time source patching, private server environment generation, permissions, checks, static collection and service startup. |
| `docs/kamatera-web-deployment.md` | 3 current report | Actual deployment state, data flow, tests, limitations and next commands. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest private-services note | Preserve state for future work. |

New server-only files: `/etc/campushub/django.env`, `/etc/campushub/chat.env`, the corresponding `/etc/systemd/system/campushub-*.service` units, `/srv/campushub/shared/{static,media,backups,cache}`, and a `backend/backups` link into shared backups. The setup log is `/root/campushub-migration/private-web-setup.log`. Local metadata is saved in ignored `backend/backups/kamatera-private-web-setup-result.json`. Private values are deliberately absent from source/docs/output.

### 3. Changes made

Created a dedicated system account `campushub`. Source remains root-owned and read-only to that service account; shared upload/backup/cache directories provide intended write access. Copied the uploaded media into the persistent shared media directory. Created fresh server-specific Django and chat signing secrets and matching chat configuration. Database settings use the existing separate PostgreSQL `campushub_app` credential on server port `5432`; no PC `.env` or PostgreSQL password changed. Server environment files are root-only, read by systemd before dropping service privileges.

Production settings require a valid HTTPS origin, disable debug/permissive CORS, enable secure cookies and HTTPS proxy recognition, and use the shared static/media paths. The domain is `campushub-ch-online.duckdns.org`. Services are enabled for boot and listen only on `127.0.0.1:8000`/`127.0.0.1:8001`. Neither application port was publicly opened. No notification worker was started; FCM is disabled in this new server environment until its separate credential/worker transition is configured.

### 4. How it works: functions, inputs / outputs and data flow

`settings_production._required(name)` reads a required private environment value and raises a configuration error for missing values. It never includes their contents in the error. The production module imports existing application settings and overrides only deployment-specific settings. Local development still selects `core.settings`; the new Django service selects `core.settings_production` explicitly.

`_chat_service_config(request)` parses the request host and configured URLs. It rewrites only loopback service URLs for a browser on another LAN device. Explicit public HTTPS and WSS URLs remain intact, including their `/chat` path prefix. This reuses the existing token/contact endpoints and adds no duplicate chat route or authentication system.

`configure()` reads the staged release manifest to verify existing source files before replacing the known chat helper/test and adding new production files. It refuses an existing first-time environment directory or unit rather than overwriting unknown production setup. Authenticated SSH carries source only; fresh signing keys are generated on the server. Existing private server PostgreSQL credentials are read there and URL-encoded. Management commands run under `campushub` with the new environment, not as the PostgreSQL superuser. After successful checks, tests and static collection, systemd starts the services.

```text
Root-only server django.env -> systemd -> Gunicorn -> core.settings_production
Root-only server chat.env   -> systemd -> Uvicorn  -> existing FastAPI chat
                               |                       |
                        server loopback 8000      server loopback 8001
                               +---- PostgreSQL on server loopback 5432

Public Nginx/HTTPS: pending (not routed to these services yet)
```

### 5. Backend / API behavior

Server private GET `/` renders the existing CampusHub login page (HTTP 200). Server chat GET `/health` returns HTTP 200 and `{"status":"ok"}`. API/auth/business permissions are unchanged. A public client cannot reach these loopback application listeners directly; the website is not yet online through HTTPS. Source chat compatibility tests also passed locally. No explicit PC Django/chat/phone/worker restart was performed; Django's own development auto-reloader can naturally notice the changed Python view file.

### 6. Database / migration impact

`migrate --check` succeeded; no migration was applied. There was no database restore, role/password/grant change, or intended application-record write. The live database is reused. Static collection and media copying are filesystem operations, not database migrations. Server signing secrets differ from local development, so public clients must authenticate to the server once that destination is enabled.

### 7. Verification actually performed

- Five existing/new chat tests passed on the PC and on the Linux server without creating a test database.
- Server `check --database default` succeeded; `migrate --check` found no pending migrations; `collectstatic --noinput` completed.
- `check --deploy` reported two deliberate remaining warnings: `security.W005` (HSTS include-subdomains disabled) and `security.W021` (preload disabled). HSTS begins with a one-hour duration; this first deployment does not make a preload/subdomain-wide commitment.
- Both systemd units passed `systemd-analyze verify`, were enabled, and subsequently reported `active`.
- Actual loopback HTTP requests with the intended host/HTTPS proxy header: Django login HTTP 200, expected branding present; chat health HTTP 200/status ok.
- Scoped whitespace checks passed; the first read-only package-inspection attempt failed due to its command construction and was replaced with successful `pip show` inspection. It made no server changes.
- No public TLS, public login, media delivery, authenticated WebSocket, SMTP, FCM delivery or mobile end-to-end verification is claimed at this stage.

### 8. Next step, limitations and safe practice

Inside the **server SSH terminal**, the next user-guided command is:

```bash
apt install -y certbot python3-certbot-nginx
```

This installs certificate tools only; the command was not executed by this private-services step. Do not run a guessed certificate command against Nginx's default site. The next stage must configure the hostname/reverse proxy and HTTPS together, validate Nginx, preserve WebSocket forwarding and use the shared static directory. Raw uploaded product/document URLs need their existing visibility rules preserved; no broad unauthenticated media alias has been enabled. Production email credentials and a deliberate notification-worker transition are also still pending. Flutter still needs a public HTTPS/WSS connection option before an online APK can be verified.

Safe read-only exercise on the server:

```bash
systemctl is-active campushub-django campushub-chat
curl -fsS http://127.0.0.1:8001/health
```

Expect two `active` lines and `{"status":"ok"}`. These are server-terminal commands, not `.env` contents. The Django private listener requires the configured Host and HTTPS proxy headers for a valid production request; a request to bare localhost can be rejected/redirected by design. Use the deployment log/systemd journal for a startup error, redact secrets before sharing output, and do not edit the service environment to use the Kamatera login password. The first-time setup helper refuses reruns because its environment/source now exist; an intentional update/recovery must inspect current state first.

---

## Earlier source/media staging step

## 1. Cause / reason and current state

The user wants the Django website/API and Flutter app backend accessible online without their PC's development server. The database was copied and the PC's SSH database connection was configured earlier; those steps alone do not host the website. The user created `campushub-ch-online.duckdns.org`, pointed it to `74.113.234.180`, and installed Nginx and Python venv tools on the Ubuntu 26.04.1 server. This step packages and uploads the existing backend/media for deployment.

**Current state: source/media staged and verified; Django/chat are not yet running on Kamatera and public HTTPS is not configured.** The active Nginx listener on port 80 is not evidence that CampusHub has been deployed.

## 2. Exact files changed and code anchors

| File | Line / nearby anchor | Purpose |
| --- | --- | --- |
| `scratch/database-backup/package_backend_release.py` | 23 `include_file(path)`; 44 `make_release()` | Build a private archive of existing backend source/media with explicit exclusions and hashes. |
| `scratch/database-backup/upload_backend_release.py` | 19 `upload(manifest_path)`; 97 CLI entry point | Guarded SSH/SCP upload, safe extraction, per-file verification and first-release link creation; requires `--upload`. |
| `docs/kamatera-web-deployment.md` | 1 title | Deployment-stage report, data flow, exact next steps, troubleshooting and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest deployment staging note | Preserve the true deployment state for future work. |

New ignored private artifacts in `backend/backups/`:

- `campushub-backend-20261020T130206925430Z.tar.gz`
- `campushub-backend-20261020T130206925430Z.manifest.json`
- `campushub-backend-20261020T130206925430Z.upload-result.json`

New server paths:

- `/root/campushub-migration/campushub-backend-20261020T130206925430Z.tar.gz`: private uploaded archive.
- `/srv/campushub/releases/campushub-backend-20261020T130206925430Z/backend`: verified extracted source/media, beneath a root-only staging directory.
- `/srv/campushub/current`: symlink to that first release; does not start or publish it.
- `/root/campushub-migration/campushub-backend-20261020T130206925430Z.stage-result.json`: metadata-only result.

No existing application source, settings, environment values, business logic, permissions or API implementation were modified in this staging step.

## 3. Changes made

Verified actual DNS resolution to the Kamatera IP, Nginx `active`, Python 3.14.4, and an empty `/srv/campushub` destination. Packaged 629 backend files, including 69 media files, into a 51,935,878-byte compressed archive (about 49.5 MiB). The SHA-256 was `40c1a3d7fff717736ff3eb50bfcb352e3aaffe05271474d200ffa0be3ea32a47`.

The package excludes local `.env` variants except the nonactive `.env.example` template, Windows `venv`/`.venv`, Python caches, Git directories, backup directories, SQL/SQLite files, log files, private key extensions, `gmail_local.py`, recognizable service-account filenames, and JSON objects containing a service-account type or `private_key`. Symlinks are excluded. These filters prevent copying the observed local private configuration; they are not a claim that arbitrary source files have undergone a complete secret audit. Production settings and fresh private server credentials still need deliberate configuration.

Uploaded over the existing authorized SSH key/SCP connection, checked the archive hash on the server, validated member names/types, safely extracted the first release, and verified each of its 629 file hashes against the archive manifest. Created the `current` link only after verification. No existing destination/current link was replaced.

## 4. How it works: functions, inputs / outputs and data flow

`include_file(path)` returns whether an existing regular file belongs in the deployment package, applying the exclusions above. JSON inspection is limited to detecting a service-account object; no credential values are printed.

`make_release()` walks the backend while pruning excluded directories, writes a new timestamped tar archive inside the ignored backup directory, normalizes archive file ownership/modes, and reads the resulting archive to calculate each entry's hash and byte size. It checks required Django/chat source files and writes a private manifest. It never starts an app or connects to the database.

`upload(manifest_path)` accepts only a manifest from that private directory with the expected timestamped release-name pattern. It verifies the local archive hash, reuses `copy_to_kamatera.remote()` for SSH inspection, and refuses existing first-release destinations, archives or current links. SCP transfers the archive; a server-side file lock prevents overlapping extraction. Every archive entry must be a regular file under `backend/`, with no absolute or parent-traversal path. Python's `data` extraction filter adds its normal path protections. Each extracted file's hash is checked before a first `current` symlink is created. A failure does not delete or overwrite an existing release as recovery.

```text
Existing backend source + media on PC
  -> include_file() exclusions
  -> new private .tar.gz + per-file manifest
  -> authenticated SCP to root-only server staging
  -> archive checksum + safe member checks
  -> versioned release extraction + 629 per-file checks
  -> /srv/campushub/current (source location only)
```

Example: `backend/core/.env` is excluded, while `backend/core/manage.py` is required. This means the Linux server needs its own private environment configuration before Django can run. Its database connection will use server port `5432`, not the PC tunnel's `15432`. The Windows virtual environments are excluded because they must be recreated for Linux.

## 5. Backend / API behavior

None of the application processes was started or restarted. Nginx was installed by the user and verified active; its site configuration was not changed here. Django remains the business/auth source of truth and FastAPI remains chat-only. The running PC setup and SSH database tunnel were left alone. No Flutter build/install/run or API-base change was made. The domain may currently display Nginx's default page, which is not the CampusHub application.

## 6. Database / migration impact

No database restore, schema migration, role/password change or application-data write was performed. The copied media files are actual existing uploads, transferred privately with the source. The staging archive should not be placed in a public web directory. Existing database details and the database-password correction are recorded in `docs/database-backup-neon.md`.

## 7. Verification actually performed

- Actual hostname lookup: `campushub-ch-online.duckdns.org` -> `74.113.234.180`.
- SSH inspection: Nginx active and listening on port 80; Python 3.14.4; target initially empty; approximately 35 GiB free.
- Package: 629 files, 69 media files, archive SHA-256 recorded above.
- Encrypted upload completed; remote archive SHA-256 and every extracted file hash matched.
- First release/current link created successfully; staging result explicitly records `app_started=false` and `public_site_configured=false`.
- Both helper scripts passed Python compilation; private archive/manifest/result are ignored by Git.
- No production settings check, installed app dependency verification, service startup, HTTPS certificate, public login, WebSocket or mobile end-to-end test has yet been performed.

## 8. Remaining steps, troubleshooting and practice

Next, inside the **server SSH terminal**, install separate Linux environments:

```bash
mkdir -p /srv/campushub/venvs
python3 -m venv /srv/campushub/venvs/django
/srv/campushub/venvs/django/bin/python -m pip install --upgrade pip
/srv/campushub/venvs/django/bin/python -m pip install -r /srv/campushub/current/backend/core/requirements.txt gunicorn

python3 -m venv /srv/campushub/venvs/chat
/srv/campushub/venvs/chat/bin/python -m pip install --upgrade pip
/srv/campushub/venvs/chat/bin/python -m pip install -r /srv/campushub/current/backend/chat_service/requirements.txt
```

These next commands were documented but **not run in this staging step**. A dependency installation failure must be addressed before running the app; share the first error without environment values or secrets. Production configuration still needs `DEBUG=False`, private secret keys/credentials, correct allowed domain/origins and static/media handling. Do not start the copied development settings directly as a public service. Existing web chat configuration currently rewrites nonloopback requests to plain HTTP/WS on port 8001, and Flutter currently assumes LAN URLs/ports; those must be adapted for public HTTPS before claiming working online chat/mobile. Review existing media authorization before publishing a broad media directory.

Later stages: configure private server environment, run production checks and any genuinely pending migrations after review, collect static files, configure dedicated service accounts/systemd services, configure Nginx for Django and chat WebSockets, issue HTTPS, update mobile connection configuration, and verify login/media/chat/notifications. Do not start duplicate PC/server notification workers against the same database during the transition.

Safe practice exercise on the server:

```bash
readlink -f /srv/campushub/current
test -f /srv/campushub/current/backend/core/manage.py && printf 'Django source present\n'
test -f /srv/campushub/current/backend/chat_service/app/main.py && printf 'Chat source present\n'
```

Expected: the timestamped release path and both presence messages. This reads files without starting Django, changing PostgreSQL, or exposing secrets. The upload helper deliberately refuses to rerun over this first-release link; an update/promotion workflow must be designed before deploying later source changes. Keep this guide's current-state statement accurate as each later stage is actually verified.
