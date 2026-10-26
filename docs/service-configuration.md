# CampusHub Services: Add/Edit configuration guide

## 1. Cause / reason and scope

The old Services editor reused the physical Facility controls, including booking mode, generic capacity, amenities and hourly pricing. The new service editor has its own fields, controller and authoritative validation while retaining the existing catalog shell, image uploader, records, routes, archive/restore and RBAC. Administrators manually create records; no Laboratory Food Analysis, BPP NC II or Lease service, official rate, analysis item or operating hour was seeded.

This guide documents the 2026-10-13 request in attachment `321217f8-745d-4453-8547-ec46eb8da02d`. It is a configuration feature, not a new service-transaction processing system.

## 2. Exact files changed, approximate current lines and code anchors

| File | Line / anchor | Change |
|---|---|---|
| `backend/core/modules/facilities/services/service_configuration.py` (new) | 12 choices; 26 `is_service`; 30 `service_configuration_choices`; 43 `service_pricing_label`; 36 `service_document_requirements`; 58 `validate_service_payload` | Service enums, true pricing summaries and validation on existing fields/JSON |
| `backend/core/modules/facilities/services/facility_configuration.py` | 190 `saved_service` | Dispatch explicit service forms/configured service updates to service validation; retain physical/legacy validation |
| `backend/core/modules/facilities/services/catalog.py` | 26 `service_labels` | Category and request labels use actual configured category/request codes, with legacy fallback |
| `backend/core/accounts/views.py` | 720 `admin_facility_page`; 740 service pricing; 811 service summary counts; 813 service choices | Shared catalog renders service choices, six-column values and real service-oriented counters |
| `backend/core/api/views.py` | 1405 `is_service, service_pricing_label`; 1421 `price_label` | Existing serialization uses actual service pricing summaries without a fake zero analysis price |
| `backend/core/modules/facilities/templates/facilities/partials/service_form.html` (new) | 1 `service-form-body` | Dedicated eight-section Add/Edit Service UI and conditional fields |
| `backend/core/modules/facilities/templates/facilities/partials/catalog_images.html` (new extraction) | 1 `facilityImagesSection` | Exact existing uploader markup shared by both editors, with six slots, preview and removal |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 162 service headers; 326 `service_form.html`; 330 `catalog_images.html`; 826 `serviceControls`; 1876 service save branch | Select the dedicated editor, reuse image/list actions, support Add/Edit/View and six-column AJAX rows |
| `backend/core/modules/facilities/static/facilities/js/service_form.js` (new) | 8 constructor; 30 `sync`; 65 `reset`; 74 `fill`; 106 `validate`; 118 `payload` | Service disclosure, restoration, validation and service-only payloads |
| `backend/core/modules/facilities/static/facilities/css/admin_services.css` | 35 `Service configuration is separate` | Scoped responsive fields/rows, navy/gold statuses and focus treatment; Pricing remains visible |
| `backend/core/modules/facilities/test_service_configuration.py` (new) | 18 test class; 145 partial update; 163 workflow document policy; 252 fixture export | Sixteen isolated tests plus actual-response editor fixtures, no production data |
| `backend/core/modules/facilities/test_service_navigation.py` | 48 catalog header assertions | Update existing navigation assertions to the final service terminology |
| `scratch/services-navigation/editor-check.cjs` (new) | 1 | Full intercepted Add/Edit/View browser review at four widths |
| `scratch/services-navigation/check.cjs` | 23 script loading; 45 headers | Existing Services/Service Requests review loads the new controller and expects final columns |
| `docs/service-configuration.md` (new) | 1 | This implementation, debugging and learning guide |
| `docs/sidebar-navigation-white-all.md` | current Services editor note near top, and Services description | Point the older navigation guide to this editor instead of the previous facility form |
| `CAMPUSHUB_CONTEXT.md` | latest `Services configuration` entry | Remember current scope, architecture and verified limits |

The model files, URL file and `service_views.py` were inspected, not modified. The existing `admin_services_page()` still delegates to the shared catalog shell with `services=True`; that shell now selects the separate Service form.

## 3. Changes made (all requested form/report topics)

The final form order is Service Images, Basic Information, Request Configuration, Pricing Configuration, Service Availability, Service-Specific Configuration, Requirements, Terms & Conditions. Both Add and Edit use this one form and **Cancel / Save Service**. View uses the same restored data with inputs, price-row controls, image-removal controls and Save disabled/hidden according to existing permissions.

Basic fields are Service Name, Service Category, optional Location, Status and Description, with service wording/placeholders. Categories are Laboratory, Training/Assessment, Leasing and Other. Other reveals a required trimmed custom category. New Status defaults to Active; the existing stored `available` code means Active in Services, while physical Facilities retain Open for Booking. Services shows Active / Temporarily Unavailable / Inactive. Legacy maintenance/reserved/occupied records are presented as temporarily unavailable, not as new selectable service statuses. Archive remains independent; Current Services means unarchived records, not only operationally active ones.

Facility booking mode, booking duration, generic min/max capacity, facility booking form, inspections, damage deposit, amenities/features, equipment and room/unit controls are absent from the Service form. Candidate Capacity appears only for Training/Assessment. No client, request ID, Job Order number, SOA number, OR number, applicant, sample-received data or certificate file is added to catalog configuration.

Request Configuration contains only Request Type, Payment Timing, Result/Output Type and Requires Approval. Job Order and SOA controls were removed in the refinement below; old internal compatibility values are retained and cannot be changed through this catalog API. A new form starts with blank request/payment/output choices. Category changes suggest request/output values while preserving explicit admin selections. Custom timing/output fields are required only while their respective Custom option is selected.

Pricing starts with Select pricing method, not Per Hour. Laboratory allows Per Analysis/Test, Fixed, Custom; Training/Assessment allows Per Candidate, Fixed, Custom; Leasing allows Per Month, Per Square Meter, Per Machine/Month, Fixed, Custom; Other supports all methods. Analysis names/descriptions/fees/active state are manually added rows in one pricing structure. There is no second analyses model/list. Fee/rate values must be finite, non-negative, within the existing monetary bound and use at most two decimals. Duplicate trimmed analysis names are rejected. Custom pricing requires its description; its amount is optional, and missing amount is not displayed as a fake zero charge.

Service Availability is an optional manual weekly configuration. Available days reveal required start/end clocks; unchecked days are Closed. Times must be ordered correctly, with at least one available day for a newly enabled configuration. An unchanged previously saved all-Closed week is preserved on Edit. New forms start unchecked with no saved schedule. No campus hours are filled automatically, and Lease does not require this configuration. Disabling it clears the owned active-hours setting on save. It is scheduling/processing configuration, not a new facility slot engine.

Only the selected category's Service-Specific Configuration appears. Laboratory has sample-acceptance and turnaround settings, with analysis/output references to their existing sections. Training/Assessment has assessment name, candidate capacity and required Scheduling Method (see the latest Training/Assessment refinement below). Leasing has configurable space-type choices and required custom text for Other. Its contract requirement follows workflow policy, not an editable checkbox (see the latest refinement below). No visible tabs let unrelated categories be configured together. Optional lease area/default-duration or candidate discount schemes were not invented where no implemented lease billing/discount workflow required them.

Requirements and Terms remain manual text, with submission/service placeholders and no saved example documents or rates. The list is **Service | Category | Pricing | Request Type | Status | Actions**, including after AJAX saves. It retains existing search, filters, pagination, View/Edit/Archive/Restore and active sidebar behavior. Counters use real registered/active/unavailable/inactive service records instead of room/unit or facility-booking wording.

## 4. Models, functions, inputs/outputs and data flow

### Existing storage reused

There is no separate Service model in this repository. Service resources use the existing `api.models.Facility` table; Service Requests use existing `Booking` records selected by `service_resources_q()`. `FacilityPayment` and existing transaction history remain unchanged. There are no dedicated Job Order/SOA models; physical booking transactions may hold Job Order metadata in their existing JSON sidecar. Saving catalog configuration creates none of these transactions or documents.

| Service concept | Existing storage |
|---|---|
| Name, category, custom category | `facility_name`, `facility_type`, `workflow_config.custom_facility_type` |
| Active/unavailable/inactive | existing `availability_status` codes, service-specific display labels |
| Request Type | `booking_mode`: service / assessment / lease; no booking-mode control is shown |
| Single configured rate/method | `rate`, `price_type`, using validated service method codes |
| Analysis/test rows and other new service flags | `workflow_config.service`, one versioned JSON object |
| Requires Approval | existing `workflow_config.requires_approval` |
| Candidate Capacity | existing `capacity`, only configured for Training/Assessment |
| Turnaround/assessment name | existing `turnaround_information` / `assessment_service_type` JSON keys |
| Weekly hours | existing `workflow_config.operating_hours`, same validated weekday format |
| Requirements/Terms/Images | existing fields and image persistence helper |

`service_configuration_choices()` returns the allowed UI dictionaries and category/method compatibility. These are options, not seeded records. `ServiceFormControls.sync()` uses selected values to show/disable the appropriate controls. Disabled/irrelevant fields are omitted by `payload(images)`. `fill(resource)` restores the actual saved record, including pricing rows and flags, while `reset()` prepares a blank Add form. `validate()` checks currently enabled required controls before a request; server validation remains authoritative.

The shared six-slot image controller and `persist_facility_images()` remain the same. Only the markup was extracted into a reusable partial; image processing, JPG/PNG/WebP acceptance, preview/removal and persisted image lists remain existing behavior. Saving an edit replaces its submitted pricing-row list instead of appending copies.

`validate_service_payload(data, facility=...)` takes a complete or partial service dictionary and optional actual existing model instance. It validates choices, strings, bools, rates, rows, capacity and optional hours, and returns the same cleaned field contract used by `_apply_facility_payload()`. New forms opt in with `catalog_kind="service"`; existing configured service records also dispatch correctly for partial API updates. Physical records cannot be converted through a Service payload. An unrelated service-looking JSON key on a physical record does not redirect its physical validator.

The validator merges omitted existing values for partial updates, then normalizes only settings relevant to the chosen category/method. Custom payment/output strings, analysis rows and category-specific fields disappear when their controlling choices no longer apply. Unowned existing top-level workflow settings and existing historical room/amenity data remain preserved rather than guessed or deleted. Old amenity-based analysis names are not auto-converted to priced rows with invented fees. An old unsupported pricing method prompts the admin to choose a method before saving and shows its existing rate for review; it does not silently default to hourly.

`service_pricing_label(resource)` returns a real amount/method, count of active analysis rates, or Custom pricing when no amount was specified. Analysis records retain the existing mandatory base rate field internally but the UI does not pretend that unused field is a zero service price. Custom partial updates retain the distinction between an unspecified amount and an explicitly entered zero.

Data flow: server choices + saved row metadata -> separate service form controller -> service-only payload + existing image sources -> existing protected create/update API -> service validator -> existing model/image/audit persistence -> serialized actual service -> six-column row/counter update. Failed saves keep the form and entered values; successful saves return to the list and show Service saved successfully. No local/offline fake service record is inserted after API failure.

Annotated learning example (conceptual, not a seed script):

```python
# A caller supplies actual admin-entered values, not official example prices.
cleaned = validate_service_payload(payload, facility=existing_service)
# cleaned['workflow_config']['service']['pricing_items'] is the one validated row list.
# _apply_facility_payload updates the existing identity; it does not create a request.
```

This separation was chosen to stop physical reservation rules leaking into Services without duplicating database models or an image/authorization subsystem.

## 5. Backend/API, Service Requests and RBAC

Existing routes are reused: `/admin-services/`, `/admin-service-requests/`, POST `/api/facilities/create/`, and POST/PUT/PATCH `/api/facilities/<id>/update/`. The web form uses the existing Django JSON endpoints; no new DRF/API version or FastAPI business logic was created. Server validation produces HTTP 400 with field errors; successful create/update retains the existing response envelope and actual record ID.

The Services pages still require existing facility-view/manage admin permissions; writes still require `accounts.can_manage_facilities`. Read-only roles cannot save through the API, and Marketplace Admin gains no permission. Existing archive/restore routes and role-based sidebar visibility remain. Images removed through an explicitly submitted empty image list clear correctly; omitted images in a partial update remain unchanged.

Existing Service Requests/history are not rewritten, split, duplicated or deleted. Their existing filtering/pagination and actual booking/payment statuses remain. Physical Facilities/Calendar/mobile reservation paths still exclude service resources; the new Other category is classified by its existing service request mode. Reports/analytics keep their existing actual transaction sources.

## 6. Database/migration impact

No model, table, column, field rename, migration or live-data seed/update was performed during implementation. New manually saved services use existing fields and JSON configuration. No client booking, approval transaction, Job Order, Statement of Account, official receipt, payment or certificate is generated by Add/Edit Service. The tests create temporary records only in the isolated Django test database.

## 7. Verification, debugging, commands and manual tests

Original implementation verification (before the refinements below):

- **244 Django tests passed** across service configuration/navigation, physical facility configuration/controls/archive, bookings/schedules/Calendar/mobile availability and dashboard/report regressions. After the final service/physical dispatch guard, the **20 focused Services tests passed again**.
- Twelve service tests cover required/conditional fields, category/method validity, finite money, one analysis structure/no duplication, optional validated hours, hidden-setting cleanup, partial updates and custom amount semantics, existing request history/images/identity, physical conversion guard, real service classification and write permissions.
- Service editor browser checks passed at **1440, 768, 390 and 320 px**: field order, no physical fields, category suggestions/manual flags, pricing rows, custom disclosures, hours, existing images/removal, repeated Edit, save/error behavior, final table columns and read-only field/buttons.
- Existing Services/Service Requests browser checks passed at **1440, 768 and 375 px**. Physical Facility editor browser checks passed at **1440, 768, 390 and 320 px**, preserving the shared image and physical form behavior. Desktop and phone Service screenshots were visually inspected.
- JavaScript syntax and changed tracked-file whitespace checks passed. Django system check was clean; migration dry run reported No changes detected.

During implementation, the reused weekly validator correctly rejected a test fixture missing Closed entries for all other weekdays; the fixture now supplies the actual seven-day format used by the UI. A review assertion initially stripped the letter s because of a harness string escape; that assertion was corrected. These were resolved test setup issues, not claimed production failures. Code inspection also prevented an unspecified custom amount becoming an explicit zero during partial updates; that scenario is tested.

Manual checks without automatically creating records:

1. Open Services > Add Service. Verify eight sections, no hourly default, no physical controls, empty name/rate/test rows/hours, Active status and Cancel / Save Service.
2. Choose Laboratory, Training/Assessment, Leasing and Other in turn. Verify appropriate fields/method choices and the required Other text. Request/output suggestions remain editable; neither Job Order nor SOA is an editable catalog setting.
3. Add an analysis row manually, remove it, try a blank name/fee. Try custom timing/output/pricing without descriptions. Required fields must be identified and invalid data rejected.
4. Enable weekly availability and select one day. No times should be preset; closing must follow opening. Leasing must save without forcing weekly hours.
5. Open an existing configured service in Edit and View. Verify actual images, category/custom text, flags, rows, rate, hours, specific settings and requirements/terms. Read-only View must prevent image/price-row edits and saving.
6. When intentionally saving real approved configuration, save once, reopen, and verify the same ID with no duplicate pricing rows. Service Requests counts/history must remain unchanged merely by saving the catalog.
7. Switch pricing/category and verify hidden old settings are not submitted. Simulate a failed API response in developer tools: form values remain and no fabricated list row is inserted.

If the old facility controls still appear, Ctrl+F5 and inspect assets `20261013-service-refinements`. If a field does not restore, inspect the row's workflow JSON and the `fill()` mapping, not just its visible label. If a save fails, inspect the existing API's `errors` object and controlling category/method; do not invent default prices to bypass validation. For an old record with unsupported pricing, explicitly select the correct method using approved current rates. A configuration flag alone does not mean the complete transaction procedure below has been implemented.

Commands from backend/core:

```powershell
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
venv/Scripts/python.exe manage.py test modules.facilities.test_service_configuration modules.facilities.test_service_navigation api.test_facility_rental_configuration --keepdb --noinput
# Optional isolated browser export:
$env:SERVICE_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/services-navigation'
$env:RENTAL_FORM_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/facility-rental-config'
venv/Scripts/python.exe manage.py test modules.facilities.test_service_configuration modules.facilities.test_service_navigation api.test_facility_rental_configuration --keepdb --noinput
# From project root:
node scratch/services-navigation/editor-check.cjs
node scratch/services-navigation/check.cjs
node scratch/facility-rental-config/check.cjs
```

No migration application is needed. Development Django normally reloads Python; static-file deployment should use the project's existing collectstatic process if applicable.

Safe practice: on a local branch, change only the Service Name placeholder in `service_form.html`, refresh Add Service, then open a physical Facility form and verify its placeholder did not change. Revert afterward. Next, use the isolated editor fixtures to inspect the captured `catalog_kind` and `workflow_config.service` payload. This teaches separating presentation, API data and persistence without adding practice records to production.

## 8. Remaining limitations

The source table is still Facility, and requests still use Booking; this task does not migrate those records into new models. Request/payment/output/sample settings and workflow document policy do not constitute an implementation of the full Food Analysis ISO, assessment registration/certification or lease application/billing workflow. Existing Service Requests remains its current real-record list/detail functionality. No official prices, student discounts, office assignments, results, certificates or operational slots are fabricated. Unsupported legacy pricing needs an explicit admin choice; old saved data is not automatically seeded or migrated. Native time inputs follow browser locale, and no physical-phone or deployed-production verification is claimed.

## 9. Add/Edit Service refinements (2026-10-13, 86c975af request)

### Cause / reason

Inspection confirmed two editable document checkboxes and a reset default of `none` for output. The category-change handler also replaced an intentional request/output selection. The shared weekly-hours helper accepts a seven-day Closed week, which is valid for some existing physical/saved configurations but must not become an accidental new Service schedule. Weekly availability was already unchecked on Add, and Request Type already had a blank option; these correct behaviors were retained and verified rather than reported as new fixes.

The existing database schema was inspected read-only using Django introspection. `campushub_facility` already contains `workflow_config`, `booking_mode`, prices, images and core fields. The model registry contains Facility, Booking, FacilityBookingRequest and FacilityPayment, with no dedicated Job Order or Statement of Account model. Service Requests currently has a real list and details dialog, not the proposed full document-processing tab workflow. No such tabs were removed or fabricated by this task.

### Exact files, current lines and nearby anchors

Paths are relative to the project root. These are the files changed for this refinement, separately from the broader original implementation above.

| File | Line / anchor | Added, changed or removed |
|---|---|---|
| `backend/core/modules/facilities/templates/facilities/partials/service_form.html` | 13 `serviceRequestHeading`; 17 `serviceOutputType`; 33 `serviceAvailabilityEnabled` | Remove both document checkboxes; blank output placeholder; balanced Request/Payment then Output/Approval rows; requested availability helper |
| `backend/core/modules/facilities/static/facilities/js/service_form.js` | 14 category handler; 65 `reset`; 74 `fill`; 106 `validate`; 118 `payload` | Preserve explicit choices, blank new output, restore saved choices/hours, omit document switches, client weekly validation |
| `backend/core/modules/facilities/services/service_configuration.py` | 36 `service_document_requirements`; 58 `validate_service_payload`; 113 output; 116 compatibility preservation; 171 `saved_enabled` | Workflow-derived new internal document defaults; ignore document input on catalog updates; preserve old values; distinguish unspecified output; Service-only weekly rule |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 16 service CSS and 588 service JS assets | Cache version `20261013-service-refinements` |
| `backend/core/modules/facilities/test_service_configuration.py` | 102 availability; 145 partial updates; 163 document policy; 177 retained history; 199 blank output; 215 Closed-week compatibility | Test authoritative rules, history preservation and new/old defaults in isolated test DB |
| `scratch/services-navigation/editor-check.cjs` | 38 new-form assertions; search `No editable Job Order policy` and `Unchanged explicit saved Closed week` | Update four-width browser checks, actual Edit hours, request/output intent and omitted fields |
| `docs/service-configuration.md` | this section, `Add/Edit Service refinements` | Current implementation report, debugging and beginner exercise |
| `CAMPUSHUB_CONTEXT.md` | final `Service form refinements` entry | Remember the current form rules and verified scope |

No CSS layout rules, models, routes, RBAC rules, Service Requests templates/views, document transaction handlers or physical Facility validators were changed in this refinement.

### Changes made: all requested report points

1. **Models reused:** existing Facility fields/JSON and existing Booking, FacilityBookingRequest and FacilityPayment. No duplicate Service, Request, Job Order or SOA model.
2. **Job Order checkbox:** removed entirely, including JavaScript lookup and outgoing payload field. It is not a hidden editable input.
3. **SOA checkbox:** removed in the same way. Existing stored `service.soa_required` compatibility data remains untouched on edits.
4. **Job Order functionality:** existing transaction code and saved metadata are untouched. The server policy helper identifies Laboratory and Training/Assessment registrations as requiring Job Order; Lease/Other do not inherit that requirement from stale admin flags.
5. **SOA functionality:** existing data is preserved. Laboratory workflow policy requires SOA. This catalog change does not create a billing document or implement an absent Service Requests document editor.
6. **Request Type:** Add starts at Select request type. Selecting a category suggests the matching value; an explicit selection is kept on later category changes. A blank request type cannot save because backend validation rejects it.
7. **Result/Output:** Add starts at Select result / output type. Blank is stored as unspecified (`""`), distinct from an explicitly selected None (`"none"`). Custom still requires nonblank trimmed description, including server validation.
8. **Payment Timing:** remains blank initially; Custom reveals its required description. No service-wide timing is forced.
9. **Requires Approval:** remains configurable with the requested helper. Catalog saves do not create approval transactions.
10. **Weekly default:** remains unchecked for new services. Days are hidden/disabled, no clocks are required, and no fake seven-day Closed schedule is saved when disabled.
11. **Conditional UI:** only the selected category's configuration is shown. The existing Other, Custom and pricing disclosures remain. All eight sections, manual pricing rows, image handling, Requirements and Terms are retained.
12. **Weekly validation:** both client and server require at least one available day when enabling a new schedule and start before end. An unchanged explicitly saved enabled all-Closed week may be retained during Edit; changing a previously open schedule to all Closed must instead disable weekly availability.
13. **Backend validation:** blank optional output is accepted without converting it to None; document input is ignored, with policy-derived values used for new compatibility settings and stored values retained on existing records. Invalid required/custom choices still produce HTTP 400 without partial saves.
14. **Edit:** actual saved images, name, category, status, request, output, approval, payment, rows/rates, hours, category fields, requirements and terms are restored. Missing output stays blank; actual None stays None. Repeated edits replace pricing rows rather than append copies.
15. **Migrations:** none. No schema or production record edits were run. No seed data or fake transactions were added.
16. **Commands:** hard-refresh the Services page with Ctrl+F5. No `migrate` is needed; restart the development server only if it did not reload the Python code. Verification commands are below.

### Functions, inputs/outputs and data flow

`ServiceFormControls.reset()` clears the form and the two selection-intent flags. `fill(resource)` accepts actual saved row data, restores values and marks nonblank saved request/output as intentional. The category handler suggests values only while those flags are false. Clearing a selection returns it to suggestion behavior. This prevents a category change silently discarding the admin's choice.

`validate()` reads enabled inputs. For weekly hours it finds checked days, checks ordered clocks and focuses the relevant invalid control. `payload(images)` returns the same service dictionary and existing image sources as before, without `job_order_required` or `soa_required`. Disabled weekly configuration supplies no hours.

`validate_service_payload(data, facility=...)` merges actual saved values for partial edits, then validates required/custom fields and hours. It calls the existing `validate_weekly_hours()` for format/time checks and adds the Service-specific positive-day condition. The shared physical Facility schedule behavior is unchanged.

`service_document_requirements(category, request_type)` is a pure function: actual category/request codes go in; workflow requirement booleans come out. It makes no DB queries and creates no documents. It is the policy source for new internal compatibility defaults; saved old switches are retained as history, not editable policy. Future Service Request processing should call this helper rather than trust those legacy switches. **The current Service Request dialog does not yet implement or consume a complete document-processing workflow.**

```python
# Conceptual example using existing workflow codes; not a record-seeding script.
requirements = service_document_requirements("food_analysis", "service")
# requirements == {"job_order_required": True, "soa_required": True, "contract_required": False}
# This determines workflow requirements; it does not issue a JO or SOA.
```

Data flow: existing saved row + server options -> form reset/fill -> explicit choices and conditional validation -> payload without document switches -> existing protected catalog API -> Service validator -> existing Facility fields/JSON/image persistence -> actual saved response/list row. Existing Booking/history/paid transactions remain separate. This approach avoids a destructive migration or a duplicate availability/document subsystem.

### Backend / API and database impact

Existing create/update endpoints and response envelopes remain. A forged catalog request trying to change document switches is ignored for these keys; other supported settings are validated normally. Stored internal document booleans on an existing service remain unchanged, including across category changes. New compatible values come from the workflow helper, never the browser. No service documents are generated when catalog configuration is saved.

No new permission, endpoint, table, column, migration or production-data update. Public/mobile/physical reservation paths, scheduling conflict checks, reports, recorded payments and existing document actions are unchanged. DB introspection was read-only; test fixture writes occurred only in the separate Django test database.

### Tests performed

- **24 focused Service tests passed**, followed by **248 regression tests passed** across Services, physical configuration/archive, reservations, Calendar, transaction workflow, mobile booking, dashboard periods/rankings/utilization/revenue.
- Tests verify forged switches cannot alter catalog document settings; omitted fields preserve history; existing request JSON with document metadata is unchanged; no catalog save creates bookings/payments/request sidecars. They also verify blank/None output distinction, required Request Type, Custom whitespace validation, weekly positive-day rules and unchanged saved Closed-week edits.
- Service editor Chrome checks passed at **1440 / 768 / 390 / 320 px**, including initial placeholders, absent switches, category suggestions versus explicit choices, optional hours/time errors, saved open/Closed weeks, repeated Edit, actual image restoration/removal, intercepted save/error behavior and read-only access.
- Services and Service Requests checks passed at **1440 / 768 / 375 px**. Physical Facility form regression checks passed at **1440 / 768 / 390 / 320 px**.
- JavaScript syntax, Django system checks and whitespace checks passed. `makemigrations --check --dry-run` returned No changes detected. Screenshots were inspected; isolated fixture pages do not resolve every live header/sidebar image URL.

Commands from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
venv/Scripts/python.exe manage.py test modules.facilities.test_service_configuration modules.facilities.test_service_navigation --keepdb --noinput
```

To export fresh isolated fixtures and review the editor (requires the existing local QA dependencies):

```powershell
$env:SERVICE_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/services-navigation'
venv/Scripts/python.exe manage.py test modules.facilities.test_service_configuration modules.facilities.test_service_navigation --keepdb --noinput
# From project root:
node scratch/services-navigation/editor-check.cjs
```

### Manual testing and debugging

1. Open Add Service after Ctrl+F5: Category, Request Type, Payment Timing, Output and Pricing show Select placeholders; availability is off; neither document checkbox exists.
2. Choose each category and check its suggested request/output. Explicitly choose None or another allowed request type, then change category: intentional selections remain. Custom descriptions and Other category/type cannot be whitespace-only.
3. Enable availability with no days and attempt Save: choose a day or disable the feature. Select a day: clocks appear without presets. End before/equal Start is rejected. Disable hours: no clocks are required.
4. Edit an existing service and compare actual saved values. An unchanged enabled all-Closed week is retained; a new such configuration is rejected. Verify pricing rows/images survive Edit/View and repeated saves do not duplicate them.
5. For deliberate configuration saves, confirm the same record ID and unchanged Service Requests/history. Use a read-only account to verify View remains available and catalog writes remain denied.

Confirmed causes are the old reset/category code and lack of a Service-only positive-day rule. If the old checkboxes still appear, inspect the loaded `20261013-service-refinements` asset and cached HTML before blaming database data. If an Edit has old false document switches in JSON, that is retained compatibility history: do not alter transaction history to fix the visible form. If enabled hours are rejected, inspect all seven weekday keys and clocks in the HTTP 400 `errors.operating_hours` response. Missing document-processing tabs are an existing workflow limitation, not caused by removing the checkboxes.

Safe learning exercise: on a local branch, change only the availability helper text in `service_form.html` line 33, refresh Services and verify the physical Facility form did not change. Revert the wording afterward. Next inspect the browser review's captured payload: `workflow_config.service` should contain payment/output/availability but no editable document switches. Run the focused tests to verify presentation changes did not alter history or validation. Do not experiment by altering production bookings or pricing.

### Remaining limitations

This is the requested form refinement, not a full Laboratory/Assessment/Lease transaction implementation. Service Requests still lacks dedicated JO/SOA/payment/results processing tabs; no claim is made that those absent screens became functional. Existing physical Job Order handlers, saved request JSON, documents and payments remain. Unknown/custom service document requirements need their actual workflow defined before extending the policy helper; no official pricing or document numbers are inferred. Native time widgets follow browser locale. No physical-phone or deployed-production test was performed.

## 10. Service Availability matches Operating Schedule (2026-10-13)

### 1. Cause / reason

Service Availability used its own three-column row, native time inputs and an inline Available/Closed label. The user requested the same UI as physical Facilities' Operating Schedule. Inspection confirmed that Operating Schedule already has reusable weekday/Closed styles and 15-minute AM/PM dropdown options. This is a presentation change; the optional weekly configuration and Service validation rules remain.

### 2. Exact files changed, current lines and anchors

| File (relative to project root) | Line / nearby anchor | Change |
|---|---|---|
| `backend/core/modules/facilities/static/facilities/js/facility_form_controls.js` | 4 `operatingScheduleUi`; 29 `CampusHubOperatingSchedule`; 94 `timeSelect`; 98 `setTime` | Extract the existing dropdown builder/restorer into a shared display helper; physical controls delegate to it |
| `backend/core/modules/facilities/static/facilities/js/service_form.js` | 10 `facility-hours-row`; 16 `CampusHubOperatingSchedule.timeSelect`; 43 `sync`; 86 `fill` | Reuse weekday/Closed markup, Opening/Closing dropdowns, shared restoration and change-error clearing |
| `backend/core/modules/facilities/templates/facilities/partials/service_form.html` | 34 `serviceWeeklyHours` | Use the existing `facility-hours` class and named schedule group |
| `backend/core/modules/facilities/static/facilities/css/admin_services.css` | 45 `.service-analysis-row`; 50 phone grid rule | Remove the old `service-hours-row` styling so existing Operating Schedule CSS controls the layout |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 16 service CSS; 590 physical controls; 591 service controller | Load the shared helper before the Service controller; cache versions `20261013-shared-schedule-ui` and `20261013-service-schedule` |
| `scratch/services-navigation/editor-check.cjs` | search `Operating Schedule dropdown reused`, `Actual non-quarter-hour saved start preserved` | Browser checks for shared styling, AM/PM, Closed disclosure, exact saved times and outgoing values |
| `docs/service-configuration.md` | this section | Implementation, testing, debugging and learning guide |
| `CAMPUSHUB_CONTEXT.md` | final `Service Availability UI` entry | Remember the current display and verification |

The reused `facility_form_controls.css` rules were inspected and remain unchanged: `.facility-hours`, `.facility-hours-row`, `.facility-check`, `.facility-hours-times`, `.facility-hours-time-label`, `.facility-hours-closed`.

### 3. Changes made

Weekday names and checkboxes now match Operating Schedule. Unchecked days show a separate Closed label. Checking a day reveals Opening Time and Closing Time, each starting at Select time with no preset clocks. Dropdowns display AM/PM and retain HH:MM values. The same compact width, dividers, spacing and responsive two-time-field row are reused. Configure weekly availability still starts unchecked and must be explicitly enabled; Add/Edit/View and current saved values remain supported.

### 4. How it works: functions, inputs/outputs and data flow

`CampusHubOperatingSchedule.timeSelect(label)` takes an accessible label and returns a native select containing a blank option plus quarter-hour options. For example, the option text is `1:00 PM`, but its value is `13:00`. `setTime(select, savedValue)` restores an exact saved HH:MM value. If it is not one of the quarter-hour choices, it adds that exact option with an AM/PM label instead of rounding it. The original physical `timeSelect()` / `setTime()` methods delegate to this helper, so the two forms share one option source.

The Service constructor creates existing Operating Schedule CSS classes and attaches the shared dropdowns to each day. `sync()` controls visibility/disabled/required states. `fill()` passes actual saved clocks to the shared restorer. `validate()` and `payload()` continue reading the same `data-service-start` / `data-service-end` controls; no payload fields or formulas changed. Input/change events clear an old field error once the user corrects it.

```javascript
const field = CampusHubOperatingSchedule.timeSelect('Monday opening time');
CampusHubOperatingSchedule.setTime(field, '08:10');
// Shows 8:10 AM, retains value "08:10"; never changes it to 08:15.
```

Data flow: saved weekly JSON -> Service `fill()` -> shared dropdown restorer -> admin selection -> existing validation -> existing `operating_hours` JSON payload. Closed days remain `null`. This reuse was chosen to avoid a second time-option formatter or changing backend availability calculations just to match the UI.

### 5. Backend / API behavior

Unchanged existing catalog routes, permissions and server validation. Enabled new configurations still need at least one available day with opening before closing; unchanged explicitly saved Closed weeks retain their existing exception. Disabled weekly configuration still submits no active hours. Booking availability, mobile endpoints and transaction workflows are untouched.

### 6. Database / migration impact

No model, schema, migration, seed or production-data changes. Displayed AM/PM text is not written into saved clock values. Existing non-quarter-hour boundaries remain exact.

### 7. Tests performed, manual checks and debugging

- **81 Django tests passed** across Service configuration/navigation, physical form controls and rental configuration; system check clean.
- Service editor browser checks passed at **1440, 768, 390 and 320 px**: reused class names/dropdowns, AM/PM labels, no preset time, Closed disclosure, time-order errors and clearing, exact `08:10` Edit restoration/submission, saved Closed weeks, permissions, image/pricing/save regressions and no page overflow.
- Physical Facility editor regression checks passed at the same four widths. Both changed JavaScript files passed syntax checks; changed tracked-file whitespace checks passed.
- Desktop and phone Service Availability screenshots were inspected using isolated fixtures and intercepted saves. No live records were added for screenshots.

Manual verification: Ctrl+F5, open Services > Add Service and enable Configure weekly availability. Verify seven unchecked days show Closed. Check Monday; select 8:00 AM and 5:00 PM. Try an end time before the opening time, correct it, then uncheck the day. Open an existing service with saved hours and verify the actual times; View must disable changes. Open a physical Facility form and compare the weekday layout.

If the controls still show native time inputs, check the `20261013-service-schedule` JS cache version. If `CampusHubOperatingSchedule` is undefined, check that `facility_form_controls.js` with `20261013-shared-schedule-ui` loads before `service_form.js`; do not add another duplicate formatter. If an old `08:10` becomes blank, inspect `fill()`'s `setTime()` call before changing stored data. If an HTTP 400 occurs, inspect the existing server `errors.operating_hours` response; AM/PM is only option text, and values must remain HH:MM.

Safe practice exercise: on a local branch, change only one Service opening-time caption, refresh and verify the physical caption is unchanged. Revert afterward. Then inspect an existing dropdown option in browser developer tools: compare `textContent` (AM/PM) with `value` (HH:MM). This teaches the difference between display and stored data without editing production inventory, prices or reservations.

### 8. Remaining limitations

New time choices use the same 15-minute increments as Operating Schedule; existing saved finer times are retained exactly. Dropdown menus themselves use browser-native rendering, while their labels consistently use AM/PM. The shared UI does not implement Service Request document processing or a new capacity engine. No physical-phone/deployed-production verification was performed.

## 11. Training/Assessment Scheduling Method (2026-10-13)

This implements the identical requests in attachments `9ec8d05b` and `0f02e82d`. The eight-section Service form and Operating Schedule-style weekly availability remain.

### 1. Cause / reason

The visible Schedule Required checkbox did not explain how a client's assessment date would be assigned, and was easy to confuse with Configure weekly availability. These represent different concepts: weekly hours describe normal operation; Scheduling Method describes how a Service Request receives its appointment/session. A boolean cannot tell us whether an existing service used a specific session or an admin-assigned schedule, so no migration guesses that choice.

Inspection confirmed Services still uses existing Facility fields/JSON, Service Requests uses existing Booking records and its current list/details view, and Facilities Calendar explicitly excludes `service_resources_q()`. No independent service-session assignment engine or schedule model was found to integrate. Current Service Requests behavior is preserved; this task adds catalog configuration only.

### 2. Exact files changed / current lines / nearby anchors

| File, relative to project root | Approximate current line / anchor | Change |
|---|---|---|
| `backend/core/modules/facilities/templates/facilities/partials/service_form.html` | 45 `serviceCandidateCapacity`; 46 `serviceSchedulingMethod` | Remove checkbox; add required conditional dropdown/helper beneath paired Name/Capacity; positive whole-number capacity hint |
| `backend/core/modules/facilities/static/facilities/js/service_form.js` | 60 conditional `required`; 99 `serviceSchedulingMethod` in `fill`; 143 `payload` | Blank Add, actual saved Edit value, hide/disable/clear outside Training, omit legacy checkbox input |
| `backend/core/modules/facilities/services/service_configuration.py` | 13 `SCHEDULING_METHODS`; 35 UI choices; 67 `capacity_submitted`; 187 training branch; 208 compatibility history | Authoritative choices/required validation, optional positive capacity, saved legacy flag preservation |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 16 CSS and 591 Service JS | Cache version `20261013-service-scheduling-method` |
| `backend/core/modules/facilities/test_service_configuration.py` | 255 `training_payload`; 262 required method; 281 capacity; 291 independence; 310 legacy; 324 category changes; 340 fixture export | Real isolated API tests and actual training-editor fixtures; adjust existing valid training cases to supply an explicit choice |
| `scratch/services-navigation/editor-check.cjs` | search `Training scheduling required`, `Actual API-created training fixture`, `Missing method blocked` | Responsive Add/Edit/conditional validation/payload checks using actual test-rendered pages |
| `docs/service-configuration.md` | this section | Current report, debugging, functions/data flow and beginner practice |
| `CAMPUSHUB_CONTEXT.md` | final `Training Scheduling Method` entry | Remember the current requirement and compatibility limits |

No models, URLs, physical Facility validators, physical schedule UI, Service Request views, Calendar queries, reports or permissions were changed for this refinement.

### 3. Changes made: requested implementation report

1. **Existing model reused:** `Facility.workflow_config.service.scheduling_method`, plus existing `Facility.capacity` for Candidate Capacity. No new Service or Schedule model.
2. **Schedule Required removed:** absent from the visible form, JS checkbox lookups and outgoing browser payload. Existing saved `schedule_required` is retained internally as historical compatibility data.
3. **Scheduling Method options:** blank Select scheduling method, Specific Date / Schedule (`specific_date`), Admin-Assigned Schedule (`admin_assigned`), No Scheduled Appointment (`none`). The blank placeholder is not a valid saved training method.
4. **Frontend conditional behavior:** only Training/Assessment shows/enables/requires the dropdown. Leaving that category clears its hidden choice and omits it from the payload. Laboratory, Leasing and Other do not validate or save a stale method.
5. **Backend validation:** the Service validator requires an allowed method for Training/Assessment. Non-string, missing, blank and unknown choices fail with HTTP 400 and `errors.scheduling_method`; JavaScript is not the only check. Other categories ignore stale input and drop the active method.
6. **Add Service:** method starts blank even after choosing Training/Assessment; the existing category suggestions for Request Type/Output do not invent a Scheduling Method.
7. **Edit Service:** actual saved method is restored, including explicit No Scheduled Appointment. Partial updates retain it when omitted. An older record lacking the field remains unconfigured and needs an explicit selection on catalog save; its old checkbox does not silently become Specific/Admin-Assigned.
8. **Weekly availability:** existing off/on, available/Closed, AM/PM, exact saved clocks and validation remain independent. Changing Scheduling Method does not set hours or create a Booking. Existing unchanged saved Closed-week compatibility remains.
9. **Candidate Capacity:** optional; if entered, a positive whole number up to the existing one-million bound. Empty/omitted means unconfigured. Negative, zero, fractional, boolean and nonfinite values are rejected. The existing nonnullable integer uses zero internally for unconfigured capacity; that is not a fabricated number of available candidates. Omitted capacity on partial edits preserves real saved capacity.
10. **Layout:** Assessment / Training Name left, Candidate Capacity right, full-width Scheduling Method below with the exact requested helper. Certification/result note stays. Phone stacking and existing CampusHub styling are reused.
11. **Service Requests integration:** saves update catalog configuration only, retaining existing request/payment/document history. No session dates, appointment rows or approval transactions are created. No service schedules are added to Facilities Calendar.
12. **Migrations:** none. No live-data seeding, BPP record, automatic historical rewrite or schema change.
13. **Commands:** Ctrl+F5 to refresh the form; restart Django only if it did not reload changed Python. No `migrate` needed. Test commands appear below.

### 4. How it works: functions, inputs/outputs, data flow

`SCHEDULING_METHODS` contains the three actual option codes and display labels. `service_configuration_choices()` returns that dictionary with the existing choices to the template. These are allowed settings, not hardcoded services or schedules.

`ServiceFormControls.sync()` checks the selected category, sets the dropdown's `required` state and clears it outside Training. `reset()` clears it for a new service. `fill(resource)` reads the actual saved service JSON; a missing field remains blank. `validate()` checks the enabled required field and native number constraints. `payload(images)` includes `scheduling_method` only for Training and does not submit `schedule_required`.

`validate_service_payload(data, facility=...)` merges existing settings for partial updates and uses the existing `choice()` and `number()` helpers. Training requires one method and an optional positive capacity. New internal compatibility flags are derived from whether the chosen method needs an appointment; saved old flags are preserved for history and are not the source of scheduling policy. On another category, active training name/capacity/method are removed, while historical compatibility flags remain.

```python
# Conceptual configuration example; does not insert records or assign dates.
service_settings = {"scheduling_method": "admin_assigned"}
# Weekly hours are separate workflow_config.operating_hours settings.
# A later request handler must read the method, not infer it from weekly hours.
```

Data flow: server option dictionary + actual saved row -> conditional Training fields -> browser validation -> existing catalog create/update endpoint -> Service validator -> existing Facility fields/JSON -> serialized actual record -> existing list/Edit restoration. There is no new API endpoint, parallel availability engine or request creation step.

This approach avoids guessing an enum from an ambiguous old boolean, duplicating scheduling storage or using ordinary processing hours as a client's actual appointment. Future authorized Service Request scheduling should use the method explicitly; its full assignment workflow is outside this catalog-only task.

### 5. Backend / API behavior

Existing protected create/update routes and response envelopes remain. The current Service editor submits `catalog_kind="service"`; configured version-one services also use the Service validator on partial edits, so omitting the browser marker does not bypass validation on those existing records. Historical generic Facility API compatibility remains a separate existing contract for unconfigured legacy resources; this task does not rewrite all legacy callers or physical Facility rules.

Saved canonical training records cannot have their method cleared through catalog updates. Stored missing/invalid old values require an explicit supported selection. Category changes ignore stale method input instead of producing Laboratory/Lease validation errors. Existing RBAC denies unauthorized writes; no permissions were expanded.

### 6. Database / migration impact

No new model, table, migration, column or destructive data cleanup. Actual catalog saves write the enum into the existing JSON and capacity into the existing integer. Existing old checkbox values, transaction IDs, bookings, payments and document metadata are preserved. Fixtures used only the isolated Django test database; production records were not changed for testing.

### 7. Verification, manual tests and debugging

- **29 focused Service tests passed**, then **253 regression tests passed** across Services, physical configuration/archive, reservations, Calendar, transaction workflow, mobile booking and dashboard/revenue/utilization reports.
- Added tests cover all three methods, blank/malformed required inputs, positive/optional capacity, partial Edit, independent hours, no transaction creation, no physical Calendar inclusion, stale category cleanup and preserved legacy checkbox values.
- Service editor browser checks passed at **1440, 768, 390 and 320 px**, including actual API-created training fixture restoration, missing method/zero/fractional capacity rejection, blank optional capacity, hidden-method cleanup, weekly independence, saved payload and fresh Add reset. Desktop and phone screenshots were visually inspected.
- Services/Service Requests checks passed at **1440, 768 and 375 px**; physical Facility form regression checks passed at **1440, 768, 390 and 320 px**. No browser JS errors or page overflow were found.
- During resume after the interrupted turn, the first test attempt found a missing enum import because the application patch was not present while test changes were present. The application patch was reapplied and verified on disk before the passing runs. This was resolved incomplete-edit state, not a claimed production bug.
- Migration dry run returned No changes detected; Django system checks and JS syntax checks were clean.

Manual checks:

1. Add Service -> Training/Assessment: Name/Capacity paired, Scheduling Method below at Select scheduling method. No Schedule Required checkbox. Weekly availability stays off.
2. Try Save without a method; it must be blocked. Choose each option in turn. Try blank capacity (valid), 1 (valid), 0, negative and fractional values (invalid).
3. Enable weekly hours and select a day/time; chosen method remains unchanged. Disable weekly hours; method remains unchanged and no fake hours are submitted.
4. Change to Laboratory or Leasing; method disappears and cannot block saving. Switch back to Training; method starts blank, requiring a fresh intentional selection.
5. Edit an actually configured training service; compare saved method/capacity/hours. Open an older unconfigured record and explicitly choose a method before saving. View/read-only permissions remain enforced.
6. For intentional approved configuration saves, verify the same service identity and unchanged Service Requests/history. Facilities Calendar must still exclude that service.

Commands from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
venv/Scripts/python.exe manage.py test modules.facilities.test_service_configuration modules.facilities.test_service_navigation --keepdb --noinput
# Optional fresh isolated browser fixtures:
$env:SERVICE_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/services-navigation'
venv/Scripts/python.exe manage.py test modules.facilities.test_service_configuration modules.facilities.test_service_navigation --keepdb --noinput
# From project root:
node scratch/services-navigation/editor-check.cjs
```

If the old checkbox still appears, inspect cached HTML and the `20261013-service-scheduling-method` JS version before modifying DB values. If an Edit is blank, check actual `workflow_config.service.scheduling_method`: the old true/false flag cannot identify which scheduling method was intended. If API saves fail, inspect `errors.scheduling_method` or `errors.candidate_capacity`. An entered zero is invalid; leaving capacity blank uses the existing unconfigured sentinel. For historical compatibility flags that disagree with the method, use the enum for new workflow decisions and preserve history rather than mass-editing old requests.

Safe practice: on a local branch, change only the Scheduling Method helper wording in `service_form.html` line 46. Verify it appears only for Training and that Laboratory/Leasing remain unchanged, then revert. Inspect a captured payload and distinguish `service.scheduling_method` (assignment rule) from `operating_hours` (normal operating hours). Run focused tests before attempting a behavior change. Do not create practice sessions or alter production request dates.

### 8. Remaining limitations

This stores/validates the requested scheduling configuration; it does not implement a complete Service Requests session picker or admin schedule-assignment engine. Those screens remain their existing real-record list/details behavior. No new Calendar, appointment status, pricing or official BPP session is invented. Older services without a method need an explicit selection when edited, with no automatic inference from legacy checkbox history. No physical-phone/deployed-production test is claimed.

## 12. Sample Submission Required label (2026-10-13)

1. **Reason:** the user requested clearer checkbox wording for Laboratory Services.
2. **Exact files changed:** `backend/core/modules/facilities/templates/facilities/partials/service_form.html`, line 39, anchor `serviceSampleAcceptance`; this documentation section. No other application file changed for this rename.
3. **Change:** visible Sample Acceptance Required becomes Sample Submission Required. The existing native checkbox supplies the tick; no second decorative checkbox symbol is added.
4. **How it works:** the label is display text. Existing `ServiceFormControls.fill()` reads `workflow_config.service.sample_acceptance_required` to restore its checked state, and `payload()` reads the same checkbox ID to submit that existing boolean. Keeping the ID/key preserves actual saved data and avoids unnecessary field migration.
5. **Backend/API:** unchanged existing Service validator, routes, permissions and boolean behavior. The label does not add a sample-intake transaction or alter inspection/acceptance requirements.
6. **Database/migrations:** none; no production records updated, no new field or seed data.
7. **Verification:** the actual Django partial was rendered with its current choices; assertions confirmed the new text, absence of the old label, and unchanged checkbox ID/type. No full regression or browser suite was rerun for this text-only change.
8. **Limitations:** this is a label rename, not a new sample-submission workflow. Manual check: Ctrl+F5, select Laboratory Service in Add/Edit, and verify the new label and actual saved checked state. If the old text remains, refresh cached HTML before editing database values.

Safe learning exercise: on a local branch, inspect line 39 and compare the visible words after the input element with its `id`. Change only the words, render/refresh, then revert. This teaches how to improve labels without breaking JavaScript bindings or stored settings.

## 13. Leasing contract policy and editable category suggestions (2026-10-13)

### 1. Cause / reason

The Leasing section still exposed Contract Required as an editable checkbox. The user clarified that the contract is part of the official Leasing workflow. It must follow that workflow rather than a browser switch. Inspection also confirmed that explicit Request Type/Result selections are already preserved by category suggestions and that weekly availability already starts off and remains independent of Training Scheduling Method. Those correct behaviors were verified, not replaced.

### 2. Exact files changed, current lines and anchors

| File, relative to project root | Current line / nearby anchor | Change |
|---|---|---|
| `backend/core/modules/facilities/templates/facilities/partials/service_form.html` | 49 `Lease Space Types`; 51 `serviceOtherLease` | Remove the Contract Required checkbox immediately after the custom lease-space field |
| `backend/core/modules/facilities/static/facilities/js/service_form.js` | 104 `serviceSampleAcceptance` in `fill`; 144 Leasing payload | Remove old contract-checkbox restoration and outgoing input; retain editable suggestions at lines 25-29 |
| `backend/core/modules/facilities/services/service_configuration.py` | 38 `service_document_requirements`; 42 contract rule; 120 compatibility defaults | Derive Leasing contract requirement through the existing document-policy helper; remove `flag("contract_required")` from lease-specific validation |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 16 CSS; 591 Service JS | Cache version `20261013-service-contract-policy` |
| `backend/core/modules/facilities/test_service_configuration.py` | 166 document-policy assertions; 255 `test_lease_contract_policy_is_server_owned_and_legacy_history_is_preserved` | Test forged switches, effective policy, editable output and history preservation |
| `scratch/services-navigation/editor-check.cjs` | search `Contract switch removed entirely`, `Suggested output stays editable`, `No editable contract policy in payload` | Browser verification of no checkbox/payload setting, editable suggestions and optional hours |
| `docs/service-configuration.md` | this section | Report, functions/data flow, debugging and learning exercise |
| `CAMPUSHUB_CONTEXT.md` | final `Leasing contract policy` entry | Remember the current scope and test results |

No model, route, CSS layout rule, permission, actual transaction handler or physical Facility logic changed for this refinement.

### 3. Changes made

Contract Required is removed completely from Add/Edit/View markup and JavaScript; no hidden editable input replaces it. `service_document_requirements()` now includes `contract_required=True` for Leasing and False for other categories. New internal compatibility defaults come from this helper, never from posted admin input. Existing saved internal values are retained as history, including an older false value; future transaction processing must use effective workflow policy rather than treat that legacy switch as permission to skip a Leasing contract.

Category suggestions remain editable: Laboratory suggests Service Request / Certificate of Analysis, Training suggests Assessment Registration / Assessment Result, and Leasing suggests Lease Application / Contract of Lease. Explicit admin/saved choices remain selected when category changes. An editable Result/Output selection such as None or Custom does not remove the official workflow's contract requirement.

Service Availability remains optional normal operating hours. It does not assign a client's BPP appointment. Training Scheduling Method remains its separate required field; actual appointment assignment belongs to the Service Request transaction.

### 4. How it works: functions, inputs/outputs and data flow

`service_document_requirements(category, request_type)` takes existing category/request codes and returns three booleans: Job Order, SOA and Contract requirements. Its contract rule depends on the Leasing category, independently of editable output/request suggestions. It performs no database writes or document creation.

`validate_service_payload()` uses that helper for new compatibility defaults and retains existing stored values on Edit. It no longer reads `contract_required` from posted lease settings. `fill()` restores the actual form controls without looking up a removed checkbox. `payload(images)` submits lease-space choices/custom text without a contract switch. Existing flags controlling suggestion intent preserve intentional selections.

```python
# Policy lookup only: no lease transaction is created.
required = service_document_requirements("lease_space", "lease")
assert required["contract_required"] is True
# Read workflow policy for required documents, not an old saved checkbox value.
```

Data flow: category + editable form choices -> payload without document switches -> existing Service validator -> existing Facility fields/JSON -> actual saved response. Document requirement lookup remains a pure workflow rule. Actual requests, contracts, payments and appointment dates remain separate records/processes. Reusing this helper avoids a duplicate policy field or destructive migration.

### 5. Backend / API behavior

Existing catalog create/update endpoints and RBAC remain. Submitted `contract_required=False`, malformed or null values cannot turn off Leasing policy. New Leasing settings store policy-derived True; old saved switches remain compatible history and are not overwritten by catalog input. Request/output choices are still validated against their allowed options and remain editable. No actual contract, Job Order, SOA, approval, payment or booking is generated by saving the service.

### 6. Database / migration impact

No model/table/column/migration or production data update. Existing saved service/request history remains. The JSON key is reused internally; there is no duplicate contract-required field. No BPP/session/lease records or rates were seeded.

### 7. Tests performed and manual verification

- **254 Django regression tests passed** across Service configuration/navigation, physical Facility configuration/archive, reservations, Calendar, transaction workflow, mobile booking and dashboard/report aggregates. The new contract test verifies posted switches are ignored, policy requires the contract, explicit output None remains editable, old false switches remain stored history and no new transactions appear.
- Service editor checks passed at **1440, 768, 390 and 320 px**, covering absent contract checkbox, omitted contract payload setting, editable Leasing suggestions, manual choices retained across category changes, optional weekly hours, Training method independence and existing Edit/View/save/error behavior.
- JavaScript syntax and Django system checks passed. Migration dry run reported No changes detected. No full deployed-production or physical-phone check was performed.

Manual steps: Ctrl+F5, choose Leasing in Add Service and verify there is no Contract Required checkbox. Verify suggested Request Type and Output can be changed. Leave weekly availability off and complete valid price/basic fields; catalog save should work without creating a client request. Reopen an existing service and check actual selections/images/space types. For Training, toggle weekly availability and verify its chosen Scheduling Method is unchanged.

If an old checkbox remains, inspect the `20261013-service-contract-policy` asset and cached HTML before changing DB data. If a saved false internal switch appears in JSON, it is retained history; effective contract policy comes from the helper. If category suggestions overwrite an explicit choice, inspect the request/output change events and intent flags, not the backend document policy. Missing contract-processing screens are the existing transaction limitation below.

Safe practice: on a local branch, inspect the three returned booleans in `service_document_requirements()` for Laboratory, Training and Leasing without saving any records. Then inspect an isolated browser payload and confirm no `contract_required` input is submitted. This teaches the difference between a workflow requirement, editable presentation settings and historical compatibility data. Do not change real request documents for practice.

### 8. Remaining limitations

This removes the catalog switch and centralizes policy; it does not implement a complete Lease Application/Contract transaction editor or BPP schedule-assignment screen. Existing Service Requests is still its real-record list/details implementation. Old compatibility booleans may differ from effective policy and must not govern new transaction requirements. No automatic signed contract, appointment, document number or payment is fabricated.
