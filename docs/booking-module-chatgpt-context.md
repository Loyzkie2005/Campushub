# CampusHub Bookings: reusable project context

## Job Order preview missing-cache-setting fix — October 26, 2026

### 1. Cause / reason

The visible **Unable to load Job Order. Please retry.** message came from the preview's non-success HTTP handling. `job_order_docx.py:prepared_documents()` directly accessed `settings.JOB_ORDER_PDF_CACHE_DIR`, but the running development configuration did not define that setting. This raised `AttributeError` before PDF conversion. The endpoint handles expected `BookingSlipPDFError`, not this configuration access error, so the browser received a generic failed load. LibreOffice was installed and correctly discovered; it was not the cause. Existing preview unit tests supplied the setting explicitly, leaving the normal unset configuration untested.

### 2. Exact files changed / current code anchors

| Exact file | Current line / anchor | Change |
|---|---|---|
| `backend/core/modules/facilities/services/job_order_docx.py` | 208 `prepared_documents`; 210 `directory = getattr(...)` | Treat the cache location as optional; preserve an explicit location or fall back to `Path(settings.BASE_DIR) / '.cache' / 'job-order-pdfs'`. |
| `backend/core/modules/facilities/test_job_order_preview.py` | `test_optional_cache_setting_can_be_absent_and_pdf_remains_reusable` | Remove the setting inside an isolated settings context, verify PDF generation, clear memory cache and verify persistent reuse without reconversion. |
| `docs/booking-module-chatgpt-context.md` | This report | Record confirmed cause, paths, functions/data flow, actual checks and recovery instructions. |
| `CAMPUSHUB_CONTEXT.md` | Latest entry | Persist the corrected optional-setting behavior and evidence reference. |

No route, template, JavaScript, permission, document field, booking/payment state, converter installation, environment configuration or migration changed. Existing unrelated edits were preserved. Original source copies and verification scripts/logs are under `scratch/job-order-cache-fix/`.

### 3. Changes made

The persistent cache now works without requiring a new server setting. Its default is outside public media/static paths, under the existing ignored `backend/core/.cache/` directory. The existing private cache timeout/entry limit, DOCX-content hash, conversion lock, memory cache, permission-checked endpoint and private response headers remain unchanged. An explicitly configured cache directory still wins. Existing handling for an unwritable disk cache still allows normal conversion and memory reuse.

### 4. How it works — functions, inputs/outputs and data flow

The browser's existing preview fetches the authorized `documents/job-order/?format=pdf&inline=1` route. `document()` verifies booking access and availability, then `job_order_data()` reads the saved draft. `job_order_pdf(data)` fills the retained official Word template, hashes the complete DOCX, checks memory/private disk cache, converts through the already installed local LibreOffice when needed, and returns PDF bytes. `prepared_documents()` supplies the existing `FileBasedCache`; its only changed input behavior is the missing-setting fallback.

Annotated example: with no `JOB_ORDER_PDF_CACHE_DIR`, the cache uses `<BASE_DIR>/.cache/job-order-pdfs`; with an explicit private path it continues to use that path. The same saved DOCX content reuses its PDF even after the memory cache is cleared. Different saved fields/template content still produce a different hash, so no unrelated or stale document is substituted.

The preview error state itself was not changed. Its existing Retry action makes a fresh request after the failed state is discarded. Print/Export continue to use the same authorized generated document; Word export retains its existing path and does not depend on PDF conversion.

### 5. Backend / API behavior

The correction prevents the confirmed unexpected configuration exception and restores a valid PDF response. Existing permission checks, approval/draft availability, file contents, MIME types, private/no-store headers, read-only preview behavior and PDF/DOCX exports remain. No signatures, payment, final approval, receiving dates or official document fields are invented. No new endpoint or duplicate Job Order is created.

### 6. Database / migration impact

None. The actual saved draft for **BK-2026-2786ED550F1C4A57** was checked through the existing permission-checked document view inside PostgreSQL `SET TRANSACTION READ ONLY`. Its saved draft JSON fingerprint matched before/after. No lazy draft initialization was permitted for this check: the verifier selected an already saved Job Order and asserted its existence first. All twelve protected marketplace/inventory table fingerprints matched. AccountActivity increased from 418 to 419 rows during verification; the new event is `login_success` in Authentication, and it was preserved. The document verifier cannot write that event because its transaction is read-only. PDF cache files are private generated artifacts, not new database records; no schema/activation/environment change occurred.

### 7. Tests performed — actual results

- **7 focused preview tests passed in 0.274s**, including missing optional configuration, unchanged/changed content, template changes, persistent cache reuse, unwritable cache, concurrency and failed-conversion retry. The initial PowerShell stderr pipeline displayed a NativeCommandError wrapper even though Python's test summary was OK; the subsequent Python runner captured stdout/stderr and process failure correctly.
- **93 preview/booking-workflow regression tests passed in 67.081s** using Django's disposable PostgreSQL test database and a separate temporary PDF cache. These include real installed-converter PDF/DOCX checks plus existing authorization and workflow regressions.
- Exact saved working draft check: **HTTP 200**, `application/pdf`, **172,226 bytes**, **one readable page**, `private, no-store`, inline disposition. The explicit cache setting remained absent, proving the default path worked. Saved Job Order details remained unchanged under read-only transaction enforcement. No personal document fields were printed into verification logs.
- Django system check passed with no issues. Changed Python syntax and scoped added-line whitespace were checked. Browser-session control was unavailable in this session, so the exact user's already-open tab was not clicked; the actual document view/PDF was verified, and its existing retry client was inspected.

Evidence: `scratch/job-order-cache-fix/regression-tests.txt`, `live-read-results.json`, `database-before.json`, `database-after.json` and `validation-summary.json`. Reproduce safely with `backend/core/venv/Scripts/python.exe scratch/job-order-cache-fix/run-tests.py`; its cache is temporary and database records are isolated. `live-read-check.py` reads an existing saved draft only, enforces a read-only transaction and reports PDF metadata rather than client contents.

### 8. Remaining limits / troubleshooting / safe practice

Reload the booking or click the existing **Retry** button to discard the previous failed request. Django's normal development autoreloader loads the Python fix; deployments with non-reloading workers require their normal application restart. LibreOffice remains a required local converter, and this fix does not bypass document eligibility/authentication or repair an unrelated converter/template error. Expected converter failures continue to return their existing controlled message and preserve Word access.

If the same generic message persists, inspect the document request's HTTP status and server exception instead of changing the booking. A missing/unwritable explicit directory, unavailable converter, expired session or invalid Word template is a different failure and should be diagnosed separately. Do not approve, recreate or edit a real booking to repair a preview problem.

Safe practice exercise: run the isolated missing-setting regression, clear only its test memory cache and confirm conversion happens once. Then reopen the already eligible saved Job Order and use Retry; verify the draft values remain unchanged. Do not modify production document fields, permissions, payments or booking decisions for testing.

Checked against the current source on October 20, 2026. Paste or attach this file in a new ChatGPT conversation. This is an explanation of the existing implementation, not permission to replace it or invent missing features.

## Modern Facility Details Mobile UI Redesign — October 20, 2026

### 1. Cause and reason
- The user requested a modern, professional, visually polished mobile UI redesign of the `Facility Details` screen (`FacilityDetailsScreen`) with 8 structured sections (Top app bar with Back + centered `Facility Details` + right bookmark/favorite icon; Hero image carousel with indicator dots and photo counter; Main info card with facility name, `Open for Booking` soft green badge, campus/category text, and two compact Capacity and Rate cards; About section card; 2-column Amenities grid with line icons and labels; Availability preview section with time slot chip-cards and `View Schedule` action; Rules & Guidelines bullet card; and Bottom sticky action bar with `Message Admin` and `Book Now`).
- Previously, `FacilityDetailsScreen` rendered loose unframed sections, hardcoded `'1/5'` on a non-scrollable single image (`FacilityItem` ignored `json['images']`), used narrow `76dp` unequal-height `Wrap` boxes for Amenities, and `BookingScaffold`'s `ThemeData` copy omitted `fontFamily: 'Poppins'` on `BookingButton` text styles and lacked a `Roboto` currency fallback for `₱`, causing button text and the Peso glyph to render as missing-glyph boxes in headless captures.

### 2. Exact files changed and anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/models/facility_item.dart` | 24 `this.images = const []`; 48 `rawImages = json['images']`; 155 `allImageUrls` | Parse `json['images']` from Django's `serialize_facility` payload and resolve all uploaded facility gallery URLs in `allImageUrls` before falling back to `imageUrl`. |
| `campushub/lib/module_app/widgets/facilities/booking_widgets.dart` | 25 `bookingMoneyText`; 113 `BookingStatusBadge(showDot)`; 199 `BookingScaffold`; 336 `BookingButton(icon)` | Added `bookingMoneyText` (`Roboto` `₱` glyph + `Poppins` amount), status dot support on `BookingStatusBadge`, `Poppins` text theme inheritance, bordered `38x38` leading Back button, top-bordered sticky bottom bar with subtle shadow in `BookingScaffold`, and optional `icon` + `horizontal: 12` padding in `BookingButton`. |
| `campushub/lib/module_app/screens/facility_details_screen.dart` | 22 `_FacilityDetailsScreenState`; 115 `build`; 488 `_FacilityHeroGallery`; 626 `_FacilitySurfaceCard`; 672 `_FactCard`; 728 `_AmenityGridItem`; 766 `_TimeSlotChipCard` | Redesigned `FacilityDetailsScreen` into 8 cohesive card-based sections with an interactive `PageView.builder` hero gallery (`_FacilityHeroGallery`), `_FacilitySurfaceCard` containers, 2-column `IntrinsicHeight` equal-height `_AmenityGridItem` grid, interactive `_TimeSlotChipCard` rows with `View Schedule`, check-badge bullet rules, and icon-enhanced `Message Admin` + `Book Now` sticky actions. |
| `campushub/test/facility_booking_flow_test.dart` | 46 `ensureVisible`; 156 `FacilityDetailsScreen renders card sections...` | Added widget test verifying all redesigned `FacilityDetailsScreen` cards, bookmark toggle, 2-column amenities, schedule preview, rules, and sticky actions; ensured slot scroll visibility before tap at `1.3x` text scale. |
| `campushub/test/capture_facility_screens_test.dart` | 15 `_MockupCoveredCourtService`; 40 `_loadCoveredCourtPhotoDataUrls`; 123 `coveredCourtMockup` | Configured isolated test capture harness to render both full-scroll (`1_facility_details_full.png`) and phone viewport (`1_facility_details.png`) mockups using the real uploaded USTP Oroquieta Covered Court photos (`covered_court_CAMFACIL20261013F13A_1..5.jpg`). |

### 3. Functions, inputs/outputs, and data flow
- `FacilityItem.fromJson(Map<String, dynamic> json)` reads `json['images']` (`List<String>`) alongside `json['image_url']`. `facility.allImageUrls` resolves each relative `/media/...` path against `ApiConfig.effectiveBaseUrl` and returns the ordered list of gallery URLs.
- `_FacilityDetailsScreenState._galleryImages` reads `facility.allImageUrls` and feeds `_FacilityHeroGallery`, which renders a swipeable `PageView.builder`, gold/white animated indicator dots (`AnimatedContainer`), category pill, and live `${currentIndex + 1}/${images.length}` counter badge.
- `_FacilityDetailsScreenState.build` renders the 8 sections inside `BookingScaffold`, dynamically consuming `facility.name`, `facility.status`, `FacilityItem.campusName`, `_categoryText`, `facility.capacity`, `facility.rate` (`bookingMoneyText`), `facility.description`, `facility.amenities`, `_slots` (`widget.service.slots(facility.id, DateTime.now())`), and `_parsedRules` (`facility.termsConditions`).

### 4. Verification and safe practice exercise
- **Verification**: `dart format` (0 issues), `dart analyze` (`No issues found!`), and `flutter test --no-pub test/facility_booking_flow_test.dart test/capture_facility_screens_test.dart` (**6 / 6 tests passed** with zero warnings). High-fidelity screenshots (`1_facility_details_full.png` and `1_facility_details.png`) were generated and visually verified.
- **Safe practice exercise**: In `campushub/lib/module_app/screens/facility_details_screen.dart` inside `_AmenityGridItem` (line 728), temporarily change `borderRadius: BorderRadius.circular(11)` to `BorderRadius.circular(16)` and run `C:\flutter\bin\flutter.bat test --no-pub test/capture_facility_screens_test.dart` from `campushub` to inspect the updated amenity tile rounding in `scratch/screenshots/1_facility_details_full.png`, then restore `11` and rerun.

## Mobile form update October 20 2026

### 1 Cause and reason

The user asked to update the mobile booking form after clarifying that the selected facility and entered booking details should determine the Job Order request. Existing submission already saves the needed requester, schedule, event/purpose, attendees and requirements. The form did not explain the automatic document behavior or show the system-selected service. This update reuses those inputs and the existing post-approval draft workflow instead of creating another customer Job Order form.

### 2 Exact files changed and anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/job_order.py` | 20 `default_job_order_service`; 42 `add_job_order_draft` | Extract the existing type-to-service mapping into one shared helper and reuse it when preparing the real draft. |
| `backend/core/api/views.py` | 1453 `serialize_facility`; 1468 `job_order_service` | Add a safe public service label to existing serialized facility data. No new endpoint. |
| `campushub/lib/module_app/models/facility_item.dart` | 30 optional constructor field; 77 JSON parser; 102 `jobOrderService` | Read the backend label, defaulting to empty for older/missing data. No Flutter-side category mapping. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 197 `_jobOrderRequest`; 462 Details; 556 Review | Show one read-only service/explanation component in both existing steps. Inputs, schedule preview, review and submission remain in the existing screen. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 149 `test_mobile_job_order_service_matches_generated_draft_and_ignores_client_override` | Check serializer/helper mapping, service exclusion, real mobile Pending -> authorized approval -> draft, copied request details and ignored client overrides. |
| `campushub/test/facility_booking_flow_test.dart` | request/review/submission test; missing-server-mapping test | Check both summary locations, retained values, no client document/category write, honest fallback and existing conflict/large-text behavior. |
| `campushub/test/fixtures/facility_booking_fixture.dart` | `testFacility` | Add the expected API service label to an isolated fixture; fix a pre-existing brace lint exposed by formatting. Never used by the application. |
| `campushub/test/capture_facility_screens_test.dart` | font setup and Details capture | Load actual bundled Poppins/Material icons and optional SDK Roboto for readable headless previews; wait for scrolling before selecting the real checkbox, assert selection and return to top for the new summary capture. |
| `scratch/facility-dashboard/verify_mobile_job_order_form.py` | test runner | Eight targeted checks on the existing local isolated QA database; refuses non-local hosts. |
| `docs/booking-module-chatgpt-context.md` and `CAMPUSHUB_CONTEXT.md` | this section/latest note | Preserve the implemented scope and verification separately from proposed policy/service extensions. |

### 3 Changes made

Details and Review show **Job Order Request** with the backend's actual service label and a short explanation: after approval the system prepares a draft using the existing booking information; facilities staff review and complete official fields. There is no customer selector for service category, request number, approval, signature or document status.

The shared backend mapping remains Covered Court/Function Hall -> Facility Rental, Hostel -> Hotel Accommodation. Unknown types and service resources return an empty label. The mobile fallback says **Service to be confirmed by Facilities Admin** instead of guessing from a facility name or hardcoding a category in Flutter. Existing nonmapped physical bookings can still receive their existing draft with service selection left for staff.

### 4 Functions inputs outputs and data flow

`default_job_order_service(facility)` accepts an existing Facility object and returns the mapped service string or an empty string. It excludes service types/modes. `serialize_facility(facility)` publishes that string as `job_order_service`; `FacilityItem.fromJson` stores it as `jobOrderService`; `_jobOrderRequest()` reads it and renders a non-editable summary.

```text
Actual facility.type/mode -> shared Django mapping
 -> existing facility JSON.job_order_service -> FacilityItem.jobOrderService
 -> Details and Review read-only Job Order Request

Existing form fields -> authenticated mobile booking POST
 -> existing Pending booking and sidecar
 -> authorized staff approval -> existing add_job_order_draft()
 -> SAME mapping + saved purpose/schedule/requirements -> existing draft
```

The request still sends the existing fields and idempotency key, not `job_order` or `job_order_service`. The backend does not trust customer-supplied document/category fields; the regression test supplies a false Laboratory Analysis override and confirms approval still produces Facility Rental. The draft is not created merely by displaying the card, and no signature/payment/approval is invented.

### 5 Backend and API behavior

Only the additive facility JSON label is new. Existing public facility list, authenticated booking create/detail, authorization, quote/conflict/capacity checks, staff approval, privacy filtering and draft/backfill logic are retained. The shared helper adds no database query. A duplicate service mapping in Flutter would drift from document generation, which is why the label comes from Django.

### 6 Database and migration impact

No new models, columns, migrations, dependencies or live data writes. Existing Booking and FacilityBookingRequest JSON continue storing the real request/draft. Test data is isolated in `test_campushub_facility_dashboard_refine`; no real customer request was submitted.

### 7 Tests and verification

- Eight targeted Django tests passed; system checks clean. Coverage includes mapping/serialization, real mobile approval-to-draft, privacy, Pending restrictions, existing draft reuse/backfill and category mapping.
- Four mobile flow tests plus one headless capture test passed in the final combined run. The form still validates, preserves values on back navigation, rejects conflicting slots, submits once and retains its request key. Missing labels do not trigger name-based inference.
- Final five-file Dart analysis passed with no issues, including the capture helper. Formatting reported zero changes; scoped whitespace checks passed.
- Final fixture screenshots of Details and Review were inspected with readable fonts. Initial preview output used Flutter's test placeholder font and emitted a checkbox hit warning; the preview helper was corrected to load real fonts, wait for scrolling and assert the chosen checkbox. These were QA-harness issues, not evidence of an app font/upload/backend failure.
- No phone app run/reload/restart/build/install, server restart or worker action was performed. Live device verification remains pending.

Safe checks from the Flutter folder: `C:/flutter/bin/flutter.bat test --no-pub test/facility_booking_flow_test.dart`. The scratch Python runner uses the named local test database only. Headless screenshots are isolated fixtures and must never be imported into runtime UI as sample content.

### 8 Limitations troubleshooting and safe practice

The current mobile customer reservation form remains slot-based. Although Django maps Hostel documents, this update does not implement a new mobile room/stay booking form, service submission, Job Order download route, refund processing or the full proposed lifecycle. Staff official fields still require review.

An already-loaded catalog object or older backend can lack the new label; the form shows the honest fallback. Refresh the facility catalog against the updated Django code to receive `job_order_service`. Do not add a hardcoded Flutter mapping to conceal a missing API field. No automatic server/app restart was performed; deploy/use the updated source through the user's normal workflow.

Safe learning exercise: inspect a real facility list response without editing records and find `job_order_service`. Open that facility's mobile booking form, advance to Details, compare the read-only service, enter a draft request and visit Review. Navigate back to confirm values remain, then leave without submitting. On an isolated QA record only, approve the booking through the existing staff action and verify its Job Order service and copied requirements match. Do not approve or create a real booking just for practice.

## Policy and service procedure alignment added October 20 2026

The user subsequently supplied a proposed end-to-end workflow for Covered Court, Function Hall, Hostel, Food Analysis, BPP NC II Assessment and Lease/Commercial Space. Treat this as the desired operational direction, separately from the already implemented behavior described below. The following evidence was reviewed:

- `C:/Users/leste/Downloads/Approved_Policy_Rental_of_Facilities_and_Spaces_in_USTP_Oroquieta.pdf`: extracted all 50 PDF pages; visually inspected relevant policy pages, including PDF pages 35, 38 and 39 (printed policy pages 5, 8 and 9 of 17).
- `C:/Users/leste/Downloads/Facilities Services-20261019T184027Z-1-001.zip`: inventoried 19 JPG photographs and two videos. Reviewed contact sheets and enlarged procedure photographs for Covered Court, Hostel/Function Hall, Food Analysis, BPP and lease application, plus the Job Order form. Videos were not reviewed; some photographed pages are rotated or less legible, so do not claim every detail of all procedures was verified.
- `C:/Users/leste/Downloads/CampusHub_CHAPTER-1-3-manuscript.docx`: extracted document paragraphs for scope/context. The scope describes manual payments and internet-dependent operation. The manuscript is project scope evidence, not authority to override the approved policy or automatically assign financial/approval powers.

### Facility workflows

Covered Court and Function Hall share this operational backbone:

```text
Request -> availability/capacity/compliance evaluation -> approve or reject
Approved branch -> booking recorded / reservation slip issued
 -> applicable system-prepared Job Order record reviewed by staff
 -> cashier payment of applicable rental/deposit/charges -> OR recorded
 -> Reserved / Confirmed -> pre-use coordination/inspection -> actual use
 -> post-use inspection -> documented damage/additional charges if any
 -> deposit settlement/refund evidence if applicable -> completion -> feedback
Rejected branch -> record decision/reason -> notify client; do not continue to use/payment steps
```

Hostel follows an accommodation-specific branch:

```text
Accommodation request -> room availability/evaluation -> approve or reject
Approved branch -> room assignment/recorded reservation
 -> accommodation slip and applicable Job Order -> cashier payment -> OR recorded
 -> confirmed stay -> pre-use coordination/room inspection -> check-in
 -> stay -> check-out -> post-use room inspection
 -> applicable damage/deposit settlement -> completion -> feedback
```

Room assignment can be prepared earlier, but the Hostel/Function Hall procedure also places room/setup coordination before use. The user's proposed hostel list omitted explicit pre-use coordination; the procedure includes it. Do not claim check-in/out actions are already separately recorded merely because the reservation has check-in/out dates.

Use **Approved / Awaiting Payment** for the pre-payment customer-facing stage. The procedures can call issuance of the reservation slip a reservation confirmation, but CampusHub's final **Reserved / Confirmed** display label is already tied to approved, fully settled bookings. Avoid two indistinguishable Confirmed labels.

The policy provides deposits for specific resources and says the remaining deposit is refunded following post-event inspection. Use actual configured amounts and recorded charges; do not invent a deposit for every facility. The Function Hall policy explicitly states full payment two days before the event. The photographed Hostel/Function Hall procedure contains a 48-hour payment phrase; confirm its intended deadline before adding a new automatic cancellation/deadline rule. Collecting Officer/Cashiering processes real refunds; a decision note alone is not evidence that money was returned.

The physical-facility procedures explicitly describe pre-use and post-use inspections. This confirms their operational importance. It does **not** establish that a missed pre-use inspection must be fabricated retrospectively or must permanently prevent completion after the event. The current missed-pre-use warning behavior below remains unchanged. Any new policy exception/escalation handling must be explicitly designed and recorded rather than silently changing past booking data.

### Food Analysis workflow

The photographed `DPM-USTP-Oro-BEU-004` explains sample integrity verification, Job Order request preparation, checking pending work/reagents/materials, BEU approval or non-acceptance, analysis, billing, cashier payment and release of results. Use this sequence:

```text
Inquiry/service request -> physical sample submission/integrity verification
 -> reject unsuitable sample OR prepare Job Order request
 -> lab resource/workload/schedule check -> BEU approve or decline request
Approved branch -> laboratory analysis -> analysis completed
 -> Statement of Account -> cashier payment -> OR recorded/presented
 -> Certificate of Analysis prepared/released -> completion -> feedback
```

Job Order preparation begins before final request approval; the form/procedure does not mean the system may approve a sample or laboratory job automatically. Results Ready and Certificate Prepared can be useful application milestones, but should be marked only from actual lab records. Preserve the document's payment-after-analysis sequence; do not force facility rental's payment-before-use flow onto Food Analysis. The procedure lists preparation/release after payment; if results are prepared earlier internally, public release still needs the required payment/OR check.

### BPP NC II workflow

The photographed `DPM-USTP-Oro-BEU-005` lists registration/evaluation, checking facility and assessor availability, assessment/payment, kitchen preparation, competency assessment, results and feedback. Notes require prerequisite verification, an available TESDA-accredited assessor, candidate orientation/safety briefing, and existing assessment records.

```text
Registration/requirements -> evaluate/approve or decline
 -> confirm facility AND accredited assessor schedule
 -> applicable Job Order/billing documents -> cashier payment -> OR recorded
 -> orientation/safety and pre-assessment readiness
 -> competency assessment -> assessment records/results
 -> authorized result/certification processing -> completion -> feedback
```

The procedure lists Statement of Account among its forms/evidence. Support it according to the actual service configuration rather than hiding all BPP billing by assumption. CampusHub may track and release authorized results; it must not claim to automatically award TESDA certification when staff click Completed.

### Lease workflow

The photographed lease procedure supports letter of intent/requirements, recommendation, notification and the application-to-contract/operation/renewal or termination scope. The policy requires written lease/concession terms and appropriate operating permits.

```text
Letter of intent/application + documents -> verification/evaluation
 -> recommendation -> approval/rejection and recorded notice
Approved branch -> lease terms/contract preparation and authorized signing
 -> notarization only when required by the approved agreement/process
 -> billing/payments/required permits/start conditions
 -> active lease -> monitoring -> renewal / expiry / termination
```

Do not use the hourly booking completion lifecycle for a continuing lease. Notarization is conditional in the user's proposal; a blanket notarization requirement was not established by the reviewed material. Contract execution, activation, recurring billing and permits are real-world records, not facts that follow automatically from application approval.

### System generated documents versus authorized decisions

For existing eligible physical bookings, `job_order.py:add_job_order_draft()` creates a draft after booking approval and preselects Facility Rental for Covered Court/Function Hall or Hotel Accommodation for Hostel. It copies known booking values without overwriting an existing Job Order. The official form includes staff verification/approval fields. Automated preparation must never generate signatures, approve a job or assert payment.

Food Analysis and BPP require their own service-stage preparation/approval rules. The current physical-booking draft helper excludes service resources; do not describe its mapping as an already implemented service workflow. Lease primarily uses its own agreement documents, not a generic facility rental Job Order by default.

### Mobile presentation and implementation order

The user's detailed chains are operational milestones, not a requirement to create a screen/tab/database status for every arrow. Proposed mobile customer sections are Summary, Progress, Documents, Payments and Feedback, with authorized safe inspection/settlement summaries where useful. Preserve the existing six admin detail tabs.

1. Correct existing mobile data presentation first: real approval timestamps; no invented Under Review event; Reserved requires approved plus paid; show backend-eligible cancellation even for approved records; Completed milestone.
2. Reuse existing system-prepared documents with an owner-authorized read-only mobile route. Do not expose internal staff notes or reuse unrestricted admin URLs.
3. Add explicit check-in/out, documented settlement/refund evidence and feedback records only where missing and after defining their staff actions/inputs. Do not infer them from dates or decision notes.
4. Extend service-specific backends/forms independently for samples/results, assessment and lease. The current mobile service catalog is read-only; the complete proposed service lifecycle is not already implemented.

Staff record decisions/evidence; Django validates permissions/transitions and prepares documents; mobile displays recorded state and the customer's permitted next action. Physical use, sample checks, inspection, refunds, signatures and certification must not be marked done merely because a scheduled date passed.

### Review verification and safe exercise

This addendum changes documentation only. No booking/service records, code, APIs, migrations or tests were changed/run for this review. The policy text was extracted and relevant pages visually checked; the DOCX was read for textual scope, not audited for rendered layout. Two archived videos and some less-legible photographed details remain unverified.

For practice, take an existing booking in view-only mode and label each visible milestone as recorded, calculated or missing. Compare one recorded OR with Payment, then check which real inspection/settlement event supports completion. Cancel the exercise without saving anything. This reveals the gap between a proposed workflow and a stored event without inventing history.

## 1. Purpose and boundaries

CampusHub is USTP Oroquieta's campus marketplace, facilities booking and services system. Django is the source of truth for bookings, availability, prices, payments, documents, permissions and audit records. Flutter consumes Django APIs. FastAPI is for chat only.

Facilities, Bookings, Calendar and Services are related but different:

- **Facilities** configures actual physical spaces, operating schedules, prices, room units, deposits and required inspections.
- **Bookings** manages individual client reservations and their approval, payment, documents, inspection and completion.
- **Calendar** displays reservations and unavailable schedules such as classes, maintenance and official campus use.
- **Services** handles specialized service resources. Food Analysis, assessment and lease workflows must not be treated as ordinary physical-space reservations. Food Analysis has its separate ISO sample/checklist/job-order/billing/result-release procedure.

Facility operational states are Open for Booking, Temporarily Unavailable, Under Maintenance and Inactive. Open for Booking does not mean every time slot is free.

## 2. Bookings list page

The existing page is `/admin-bookings/`.

### KPI cards

| Card | Current calculation |
| --- | --- |
| Total Bookings | Count within the chosen current/archived/all record scope. |
| Pending Approval | Records whose stored booking status is Pending. |
| Upcoming / Reserved | Approved, fully paid reservations whose timed use/stay has not ended, using existing room checkout configuration. This can include ongoing use; it is not exactly the same measure as the dashboard's future-starting reservation count. |
| Unpaid | Approved bookings that are not fully settled. Pending applications are not included in this payment KPI. |

Clicking a KPI filters the list through the existing shared backend definition. KPIs are calculated before the list's search/status/facility filters, within its selected record scope.

### Search, filters and table

Search covers saved booking identity/requester/facility information. Existing filters include Booking Status, Facility and Record Status (Current, Archived or All). The backend paginates at 20 records and orders recent submissions first. The frontend also matches its rendered rows; do not build a second search system.

The table shows Booking ID, Requester, Facility, Room/Unit, Date, Time/Stay, Total Cost, Payment Status, Booking Status, Submitted date/time and Actions. Missing room data is not invented. The three-dot action menu is based on the server's allowed actions, saved documents and inspection phase.

### Actions placement

Add Reservation and Manage Facility Schedule sit in the Booking Requests header, subject to existing permissions. The separate Quick Actions heading/container was removed. Add Reservation was removed from the Facility Admin dashboard and remains in Bookings. The existing action-query compatibility handler still exists; do not re-add the dashboard shortcut unless requested.

## 3. Add Reservation

This is the existing dialog for staff creating a reservation on behalf of a client. It does not create a second booking system.

1. Select an actual configured facility.
2. Select CampusHub User or Walk-in / External Client. Existing users are searched; walk-in information is entered through the existing client workflow.
3. Enter client name, organization/office, contact, email and address where applicable.
4. Provide the facility-specific schedule:
   - Slot/event booking: date, configured slot when applicable, start and end time.
   - Accommodation: check-in/out dates, configured check-in/out times, room/unit where required, adults/children and eligible configured shared-rate handling.
5. Enter participants/guests, purpose, notes, actual configured fees and applicable discount information. Eligibility discounts require the existing verification information.
6. The existing quote/availability preview checks operating days/hours, dates, capacity, room constraints and conflicting use. It displays the real rental/discount/fees/deposit/total breakdown.
7. Save revalidates on the server. A previously displayed quote does not bypass validation.

Staff who also have booking-approval permission create an Approved reservation with approval metadata; other authorized creators produce Pending reservations. Do not claim every staff reservation always starts Pending. Mobile creation has its own existing authenticated endpoint and must retain its existing rules.

Facility-specific rules are configuration-driven. For example, an operating-day rejection must reflect the saved schedule, not a hardcoded universal Thursday rule. Deposits must come from actual facility/quote configuration.

## 4. Booking statuses and payment status

| Status / label | Meaning |
| --- | --- |
| Pending Approval | Awaiting the authorized approval decision. |
| Approved | Approved booking that is not yet fully paid. |
| Reserved / Confirmed | Display label for an Approved booking whose recorded paid amount covers its total. The stored booking status remains Approved. |
| Completed | Authorized staff completed the booking after the readiness checks passed. Schedule ending alone does not automatically mark it Completed. |
| Cancelled | Reservation cancelled under the existing schedule-start policy, with reason/actor/time retained. |
| Rejected | Pending request rejected by authorized staff, with reason/actor/time retained. |

Payment is separate from booking status. Current list/detail payment labels are Paid or Unpaid; historical partial amounts can contribute to paid totals and outstanding balances, but the current Record Payment action **does not accept new partial payments**. It requires the entire outstanding amount. Do not document a Partially Paid workflow as implemented merely because it was discussed previously.

## 5. Booking Details: exact six tabs

The existing full page is `/admin-bookings/<booking_id>/`. It is not a separate modal-only booking system. Tab links use the existing page/controller and can open the relevant section.

| Visible tab | Internal key | Responsibility |
| --- | --- | --- |
| Overview | `Overview` | Booking facts, price breakdown, approval, notes, cancellation information and completion readiness. |
| Booking Slip | `BookingForm` | Existing official slip, print/PDF and permitted booking edits. |
| Job Order | `JobOrder` | Existing BEU job-order draft/editor, preview and exports. |
| Payment | `Payment` | Amounts, actual cashier/OR records, receipt attachments and authorized recording. |
| Inspection | `Inspection` | Personnel assignment, pre/post-use inspection and applicable damage/deposit resolution. |
| Activity | `Activity` | Existing booking audit history. |

There is no seventh standalone Documents tab. Supporting files are associated with their existing Booking Slip, Payment or Inspection sections.

### Overview

Shows booking/requester/facility, room when applicable, booking source, date/stay/time, participants/guests, purpose, current/archived visibility, pricing method and quote components, paid amount, remaining balance, approval/submission information and notes.

Available actions depend on actual status and server permissions: Approve, Reject, Edit, Cancel under More Actions, and Complete Booking when ready. Approval reruns availability validation, excluding only the booking being approved. It does not blindly accept a previously free slot.

The general edit action is restricted to Pending/Approved bookings with no paid amount and the existing required grants. Paid bookings are not freely editable through this form. A cancelled booking is read-only even if an old UI button or direct API request is attempted.

### Completion Readiness

The backend's single `completion_readiness()` definition powers the checklist, disabled-button reason, allowed action and final completion validation.

Main requirements:

- Booking is Approved.
- Scheduled use has ended with a valid recorded end/checkout time.
- Payment is settled under the current payment summary.
- Required post-use inspection is completed.
- Damage/deposit resolution is recorded and confirmed when an actual deposit or recorded issue exists.

A recorded inspection requires condition, inspector and inspection time. If a required pre-use inspection was missed and the schedule has ended, show **Pre-use inspection was not recorded.** as a warning. It does not count as a remaining blocking requirement in the current implementation. No retrospective pre-use inspection is offered.

The UI shows actual remaining requirement count/reason, then Ready for completion once satisfied. Complete Booking stays disabled until eligible. When damage/deposit handling applies, completion also asks staff to confirm the issues are resolved. Completing saves Completed status plus actor/time, preserves payments/documents/audit records and removes the completion action.

Known implementation edge: the current payment summary requires a recorded paid entry to report Paid. Do not assume a zero-cost booking automatically bypasses settlement; this guide does not change that behavior.

### Booking Slip

Generated from the saved reservation and applicable facility form configuration. It displays the official rental/accommodation/general slip information, booking details and recorded values. Staff can print or export PDF. A slip is not an Official Receipt and does not itself establish payment or approval.

Edit Booking Slip reuses the booking edit action, not a disconnected copy of the document. It appears only when the backend permits editing. Cancelled bookings retain view/print/export access but no edit action. Do not remove working edit controls from eligible unpaid active bookings.

### Job Order

The existing BEU JOB ORDER Request is a separate document from the Booking Slip and from the cashier's OR. Eligible approved physical bookings receive a draft filled from saved booking/client information. Existing eligible historical bookings can receive a missing draft through the existing idempotent backfill helper. No fake request number, signature or approval should be invented.

The editor includes request number, saved date, service selection/other service, gender preference, turnaround time, details/specifics, items and received/required timestamps. The preview supports existing printing and PDF/DOCX exports. The current document is labelled Draft; do not invent a separate signed/final approval lifecycle.

Pending bookings show that Job Order becomes available after approval. An existing generated document remains historical evidence after cancellation/completion. Edit Job Order is available only while the server permits it; cancelled bookings cannot modify it. This document is not a mandatory completion requirement in the current checklist.

### Payment

Sections: Payment Summary; Payment Record Details; Payment History when multiple records exist; Receipt Attachment; Payment Actions when allowed.

- Summary: original total, actual amount paid, remaining balance and payment status.
- Record details: OR number, method, payment date/time, recorded/verified-by staff and notes.
- Multiple saved records can be selected from history. Missing legacy values show Not recorded rather than invented values.
- Existing private receipt attachments can be viewed/downloaded through authorized routes.

Record Payment is for an Approved, unpaid booking and requires the existing payment-recording permission. Current method is **Cash**, recording an actual cashier payment. The amount must be positive and exactly equal to the outstanding balance. An OR number is required and duplicate paid OR numbers are rejected. A future payment timestamp is rejected. Receipt attachment is optional with existing PDF/image validation and the current 1 MB limit.

The system records an existing real payment; it does not collect money online, generate the cashier's legal OR, issue refunds or erase prior financial records. Fully settling an Approved booking changes its display label to Reserved / Confirmed. Cancellation retains payment history; refund handling remains separate.

### Inspection

Contains Personnel In-Charge plus separate Pre-Use Inspection and Post-Use Inspection sections. Inspectors are real active authorized staff with the existing management permission and eligible role; ordinary users/marketplace-only roles are not inspectors. Changing assigned personnel does not silently replace the inspector on an existing inspection.

**Pre-use:** offered only for an Approved booking whose configuration requires it, before scheduled use begins. Records inspector, date/time, condition, existing damage/issues, remarks and optional evidence. Its recorded inspection time must also precede use.

**Post-use:** available after scheduled use ends when required by configuration or needed for actual deposit/issue review. Records inspector, date/time, condition, explicit Damage Found Yes/No, required damage description when Yes, remarks and optional evidence. Inspection time cannot precede the end of use.

Condition choices: Good Condition, Minor Issues, Damaged, Requires Maintenance and Other; Other requires an explanation. Previous free-text inspections remain readable without being silently rewritten.

Damage/deposit decision and resolution confirmation apply only to an actual recorded deposit or issue. Issues include recorded damage and relevant saved missing-item/overtime information. Free-text decision alone does not prove resolution: staff must confirm it. A facility without deposit/damage issues must not receive a fabricated resolution requirement. Identical inspection saves do not manufacture duplicate change events.

Saved inspections show a concise summary, expandable View Details with recorder/creation/update information, relevant historical fields and authorized report/evidence links.

### Activity

Displays existing booking events with time, actor, role, action and result. Events include creation/auto-approval, approval/rejection, edits, payment, job-order changes, inspection, personnel assignment, applicable damage/resolution events, completion, cancellation, archive and restore.

The detail payload currently reads the latest 50 matching booking audit entries. This is a display limit, not deletion of older history. Completion and cancellation must preserve the audit log.

## 6. Cancellation, archiving and historical access

Cancellation is permitted for Pending or Approved bookings only **before a valid scheduled start**. This current implementation applies the start-time guard to Pending too. Payment does not decide cancellation eligibility: approved paid/legacy partially paid bookings can still be cancelled before use begins, retaining financial history.

It is not permitted after use starts/ends or once Completed, Cancelled or Rejected. Missing/invalid start information blocks cancellation rather than guessing. Reason is required; actor and time are saved.

Cancelled bookings become read-only. No reservation/slip/job-order/payment/inspection/completion writes are allowed. Existing documents, payments, inspections, cancellation facts and Activity remain readable subject to permissions. Archive and Restore only change record visibility; Restore does not reactivate the reservation or change Cancelled status. Archiving is not permanent deletion. The current archive/restore workflow is specifically for cancelled bookings.

## 7. Calendar and unavailable schedules

The existing `/admin-calendar/` page includes month navigation, Today, Facility and Event Type filters, actual reservation/hold entries, an upcoming list and event details. It distinguishes reservations from class/academic schedules, maintenance, official campus use, administrative holds and other configured blocks. Room units and overnight stays must retain their existing semantics.

Manage Facility Schedule adds unavailable time, not a customer booking/payment. The existing editor supports configured dates/times, all-day/repeating schedules and applicable attachment support. Cancelled/rejected bookings do not appear as active calendar reservations; historical completed use can remain visible. The booking validator and calendar projection must reuse existing rules rather than maintaining a separate availability source.

## 8. Developer source map and data flow

Approximate current lines; search the named function/ID after edits.

| File | Anchor | Responsibility |
| --- | --- | --- |
| `backend/core/core/urls.py` | 141; 208-219 | Existing Bookings/Calendar pages and booking API/document routes. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 88 `bk-bookings-list-header` | Booking list, filters and retained form triggers. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 36-49 `data-bk-tab` | The six tab buttons and panels. |
| `backend/core/modules/facilities/templates/facilities/partials/booking_forms.html` | 1 `bkReservationModal`; 78 schedule dialog | Existing create/edit forms. |
| `backend/static/components/js/admin_bookings.js` | `loadBookingPage`, `showMoreActions` | List API/filter/pagination and permitted action destinations. |
| `backend/static/components/js/admin_booking_workflow.js` | `renderOverview`, `renderPayment`, `renderInspections`, `editor`, `submit` | Detail rendering, tab changes and existing action forms. |
| `backend/static/components/js/admin_booking_forms.js` | `loadFacility`, `show`, reservation submit | Existing dynamic reservation configuration/quote/form. |
| `backend/core/modules/facilities/admin_booking_views.py` | 151 `create`; `preview`; `audit` | Authorized create/quote/schedule handlers and existing audit entries. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 42 `list_data`; 118 `detail_data`; 203 `update` | Scoped payloads, permissions, locked updates and private documents. |
| `backend/core/modules/facilities/services/booking_workflow.py` | 57 `paid_summary`; 113 `status_label`; 130 `allowed_actions`; 242 `cancellation_readiness`; 296 `completion_readiness`; 339 `transition` | Shared state rules and action validation. |
| `backend/core/modules/facilities/services/inspections.py` | `authorized_inspectors`, `validate_condition`, `same_inspection` | Staff eligibility, condition validation and no-op detection. |
| `backend/core/modules/facilities/services/job_order.py` | `add_job_order_draft`, `ensure_job_order_draft` | Existing draft generation/backfill and document presentation. |
| `backend/core/modules/facilities/services/booking_slip.py` | `booking_slip_data` | Saved booking to official slip presentation. |
| `backend/core/modules/facilities/services/calendar.py` | `calendar_events` | Read-only calendar projection of stored records. |

The existing `Booking` record holds the core reservation/status/total. Its `FacilityBookingRequest` sidecar stores JSON details such as quote/configuration snapshots, client facts, approval, job order, inspections, document metadata, completion and archive state. `FacilityPayment` stores payment entries. `AccountActivity` stores audit entries. Reuse them; do not create competing booking/payment/history models.

Annotated action example:

```text
Staff clicks Complete Booking
 -> existing JavaScript submits action=complete to the booking update URL
 -> Django verifies authentication, permission and current record
 -> locks/rechecks readiness and any required issue confirmation
 -> saves Completed + completion actor/time
 -> appends existing audit event
 -> refreshes the same detail payload and tabs
```

Allowed actions are enforced server-side, not just by hidden buttons. The quote/workflow snapshot preserves applicable saved booking rules rather than silently applying every later facility configuration change.

## 9. Instructions for the next ChatGPT conversation

Read this document and inspect current code before proposing changes. Follow the user's latest corrections over older context entries. Preserve the six tabs and existing navigation/permissions. Do not confuse booking status with payment or archive status. Do not fabricate ORs, deposits, approvals, ratings, records or required inspections. Do not add online payments or merge Food Analysis into ordinary booking. Do not remove eligible slip/job-order editing or restore editing on cancelled bookings.

Web retains its configured typography; mobile UI uses Poppins, SugarPie for its wordmark and Montserrat for identity. Brand palette is navy #1A1851, gold #FCB315 and white/light neutrals. Do not restart/install the mobile app or server merely to explain or edit documentation.

## 10. Verification, limitations and safe exercise

This document was checked by reading current templates, JavaScript controllers, Django workflow/permission/document handlers, calendar projection and URL definitions. No new runtime test was run for this documentation-only task. Prior test results in feature guides should not be described as newly run tests.

No application behavior, API, database records or schema was changed by creating this guide. It is a dated snapshot; future code can supersede it. Known limits include binary Paid/Unpaid presentation, no new partial-payment recording, no integrated refunds, no separate finalized/signed Job Order stage, and the zero-cost settlement edge described above.

Safe learning exercise: open an existing booking and visit all six tabs without saving. Compare Overview total/paid/balance with Payment, inspect the slip and Job Order labels, note whether inspections are available for the actual schedule, and read Activity. On a cancelled record confirm documents remain viewable and mutation controls are absent. Do not approve, pay, inspect, cancel or complete real records merely to demonstrate the UI. If something differs, check the source-map anchors and existing permission/stage rules before changing code.
