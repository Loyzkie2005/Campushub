# Reusable Add/Edit Facility configuration

Updated: 2026-10-13. Scope: the existing Facilities catalog form, its shared configuration validator, and truthful list/quote formatting. The sidebar and booking transaction workflow were not redesigned.

## 1. Cause / reason

The previous form locked physical booking modes to facility classifications and had only a simple rate/price-type pair. It could not describe base-duration charges, capacity ranges, deposits or configurable fees. Its row editor read numbers from display text; a complex pricing summary must never become the stored base rate. Edit also supplied `1` when rooms/units were absent. Both value-reading problems are corrected.

Confirmed during browser verification: the square Back button style wrapped Add Fee/Remove text, and the existing catalog/header could overflow narrow screens. Dedicated fee button styling and scoped responsive rules address those issues.

## 2. Exact files changed and anchors

Paths below are relative to the repository root. Lines are current approximate starting points; search the named anchor if later edits move them.

| File | Line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/api/models.py` | 380 hostel label; 434 `custom_facility_type`; 440 `get_facility_type_display` | Display-only label change and a property/resolver reading the existing workflow JSON; no new column. |
| `backend/core/modules/facilities/services/rental_configuration.py` | 6 `PRICING_METHODS`; 24 `validate_discount_rules`; 61 `number`; 83 `validate_rental_options`; 163 `capacity_label`; 173 `pricing_label`; 190 `slot_base_amount` | Helpers for configuration validation, display and the existing mobile rental quote. |
| `backend/core/modules/facilities/services/facility_configuration.py` | 141 `facility_form_configuration`; 182 `validate_facility_payload`; 345 `owned` settings | Extend the existing validator, support editable physical modes, preserve omitted saved fields, clean irrelevant settings. |
| `backend/core/modules/facilities/services/mobile_booking.py` | 76 `rental_quote` | Call the shared pricing helper; reject incomplete/unsupported automatic quotes rather than guessing. |
| `backend/core/api/views.py` | 1400 `serialize_facility` | Return backend-generated capacity/pricing labels alongside raw values. Existing create/update validation paths reuse the extended validator. |
| `backend/core/accounts/views.py` | 720 `admin_facility_page`; 737 `capacity_display` | Build the same labels for initial server-rendered table rows. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 163 `data-rate`; 457 `facilityBookingMode`; 469 `rental_rules`; 534 `rental_pricing`; 906 `syncFacilityFormType`; 1414 `resetFacilityForm`; 1467 `getFacilityFromRow`; 1567 `fillFacilityFormFromRow`; 1902 save listener | Reuse the existing form, reorganize sections, load actual saved values, keep raw rate separate from display text and collect new settings. |
| `backend/core/modules/facilities/templates/facilities/partials/rental_rules.html` | 1 `data-rental-field="rules"` | Four rule toggles, booking form selector and rooms information. |
| `backend/core/modules/facilities/templates/facilities/partials/rental_pricing.html` | 1 `base_duration`; 26 `facilityAddFee` | Conditional pricing/deposit inputs and an initially empty flexible fee list. |
| `backend/core/modules/facilities/static/facilities/js/rental_form_controls.js` | 34 `configure`; 70 `sync`; 97 `setWorkflow`; 128 `addDiscount`; 168 `getWorkflow`; 182 `validate` | UI controller for field visibility, suggestions, saved values, fees/discounts and browser validation. |
| `backend/core/modules/facilities/static/facilities/js/facility_form_controls.js` | 127 `setWorkflow`; 153 `syncMinimum`; 160 `getMinimumDuration`; 184 `validate` | Keep untouched legacy schedule text, configure a custom minimum and accept deliberate closed schedules. |
| `backend/core/modules/facilities/static/facilities/css/facility_form_controls.css` | 91 `.facility-config-heading`; 96 `.facility-fee-action`; 100 scoped catalog rules | Compact sections/rules/fees and responsive form/list/header fixes. |
| `backend/core/api/test_facility_rental_configuration.py` | 21 `RentalConfigurationValidationTests`; 183 discount tests; 255 `FacilityRentalAPITests`; 362 discount edit test | Validation, API round-trip, permissions, custom display, discounts and no-auto-record tests; optional isolated browser fixtures. |
| `backend/core/api/test_facility_form_controls.py` | 46 `test_all_closed_schedule_does_not_invent_operating_hours` | Update schedule expectations to the deliberate closed state. |
| `backend/core/api/tests.py` | 100 `FacilityConfigurationTests`; 178 unsupported price assertion | Replace obsolete locked physical-mode expectations with unsupported-mode/price rejection. |
| `CAMPUSHUB_CONTEXT.md` | final entry `Reusable Facilities configuration (2026-10-13)` | Preserve the current architecture and implementation boundaries. |
| `docs/facility-configuration.md` | this guide | Explain code, data flow, checks, limitations and a safe practice exercise. |

Diagnostic scripts, fixtures, screenshots and logs are under `scratch/facility-rental-config/`, with test/browser logs beside that folder. The existing `scratch/services-navigation/check.cjs` browser harness also loads the new shared controller. These artifacts are for verification, not application routes or production seed scripts.

## 3. Changes made

- Facility name/location/rates start empty. Type has a placeholder and includes Other. Selecting a type suggests a physical mode and pricing method; it does not save a record.
- Physical facilities allow Slot-Based or Room / Stay-Based. Daily is a pricing method, not a newly invented booking engine. Existing service classifications retain their separate workflow rules.
- Maximum capacity reuses `Facility.capacity`; optional minimum is stored in the existing workflow JSON. List labels show a range or a single maximum. Existing rooms/unit counts remain unit labels.
- Rules store approval, pre-use inspection, post-use inspection and damage-deposit applicability. Booking form type stores rental, accommodation or general configuration.
- Pricing offers per hour, base duration plus additional hour, day, person, person/night, night, fixed rate and custom. Existing `session` is the stored value for Fixed Rate; existing service/monthly pricing stays supported for service resources.
- Deposit fields appear only when enabled. Flexible fee rows have name, amount, charging basis, active flag and Remove. No example fee is saved automatically.
- Room mode reveals existing room metadata and the configure-after-saving message. It does not create rooms. Slot mode retains minimum duration controls; predefined slot records keep their existing behavior.
- Images retain the existing six slots, preview/removal and existing-file loading. Amenities, editable requirements and terms remain in the same form.
- Unknown saved workflow keys survive unrelated edits. Known irrelevant keys are discarded when mode/method/deposit settings change. Hidden controls are disabled, and the backend independently enforces the cleaned configuration.

## 4. How it works: functions, inputs, outputs and data flow

This page already uses an HTML/JavaScript form posting JSON, rather than a Django ModelForm. No duplicate form framework or stock/payment model was introduced.

```text
Facility database row
  -> admin_facility_page -> table raw values + readable labels
  -> fillFacilityFormFromRow -> setWorkflow(actual saved settings)
Admin edits visible fields
  -> sync/configure disclose applicable inputs
  -> getWorkflow + existing image/schedule/amenity collectors
  -> existing create/update endpoint
  -> validate_facility_payload -> validate_rental_options
  -> existing _apply_facility_payload -> Facility.save
  -> serialize_facility -> replace/update table row
```

`number(value, field, errors, ...)` returns an integer/Decimal or `None` and writes a field-specific error. It does not strip arbitrary characters: `30â€“50` is not a valid single capacity value. Decimal arithmetic prevents floating-point money errors. Boolean, nonfinite, negative, oversized and overly precise values are rejected.

`validate_rental_options` receives workflow settings plus the validated mode, rate, method and maximum capacity. It returns only applicable rental settings and adds errors to the shared dictionary. `validate_facility_payload` raises `ValidationError` before the API writes a Facility if any configuration errors exist.

`capacity_label(facility)` and `pricing_label(facility)` accept the real model and return display strings. The numeric rate remains separately available as `data-rate`/API `rate`, so formatting is never parsed back into financial data.

`FacilityRentalControls.sync()` hides/disables irrelevant controls. `setWorkflow()` fills actual settings, preserving `0` and `false` with nullish defaults. `getWorkflow()` returns the currently applicable JSON. Client checks improve feedback; they do not replace Django validation.

Example configuration shape below is explanatory only; no seed runs it:

```json
{
  "capacity_min": 30,
  "requires_approval": true,
  "requires_pre_use_inspection": true,
  "requires_post_use_inspection": false,
  "damage_deposit_applicable": true,
  "booking_form_type": "rental",
  "pricing": {"base_duration": "4", "additional_hour_rate": "500"},
  "damage_deposit": {"type": "percentage", "value": "40"},
  "additional_fees": []
}
```

Here `capacity_min` complements the existing maximum; money/duration JSON values use decimal strings; `pricing` only belongs to base/custom methods; deposit configuration only exists when enabled. Empty fees means no invented charges.

`slot_base_amount(facility, hours)` is called by the existing mobile rental quote after its slot/status/minimum-duration checks. Supported base amounts are:

```text
Per hour: rate Ã— valid hours
Fixed rate: rate
Base duration: base rate + max(valid hours âˆ’ base duration, 0) Ã— additional hourly rate
```

Additional hours are proportional, not silently rounded up. The final amount is rounded to two decimal places. Day/person/night/custom methods and active deposit/fee configurations require an admin quote in this slot endpoint; it fails clearly rather than generating an incomplete amount.

## 5. Backend / API behavior and validation

Reuse existing routes (defined in `backend/core/core/urls.py`, approximately 129 and 189):

- `GET /admin-facility/`: existing catalog page.
- `POST /api/facilities/create/`: existing permission-protected manual create.
- `POST`, `PUT` or `PATCH /api/facilities/<id>/update/`: existing edit; omitted fields preserve actual saved values.

These existing endpoints are Django JSON views. No new DRF endpoint, new page or duplicate permissions were added. Existing server-side facility management permissions remain authoritative.

Validation includes required name/type/location, name/location lengths, supported mode/method, nonnegative whole capacities, minimum â‰¤ maximum, rates with at most two decimal places, base duration > 0 and â‰¤ 24 hours, required extra-hour rate, custom description, strict Boolean rules, deposit type/value, percentage â‰¤ 100, fee shape/name/unit/amount, room time format, seven-day schedule validity and opening < closing.

An empty/all-closed schedule is valid configuration and does not invent availability. Unchanged unparseable legacy schedule text is preserved on Edit; the existing availability reader fails closed until an admin configures valid hours. Malformed newly submitted text is rejected.

## 6. Database / migration impact

No new model, database column, migration, seed command or data migration was added/applied. Reuse `Facility` in `backend/core/api/models.py:352`: `capacity` (398), `rate` (399), `price_type` (400), `booking_mode` (401), and existing `workflow_config` (408). The custom-type extension below updates a choice label and adds read/display methods in the model file, with no new database fields. Existing Room/Booking/FacilityPayment models remain unchanged.

The additional settings are validated keys inside existing JSON. The live Facility row fingerprint and related counts matched the pre-task snapshot: **1 facility, 0 rooms, 0 bookings, 0 payments**, unchanged. Example records only ran in Django's separate test database. Browser save requests were intercepted and did not reach production.

## 7. Tests performed and manual checks

Executed successfully:

- 60 Django tests covering the new configuration, existing schedules, mobile rental bookings, Services routing, archive behavior and selected permissions.
- `manage.py check`: no issues.
- `manage.py makemigrations --check --dry-run`: no changes detected.
- `node --check` for both form controllers; targeted `git diff --check`.
- Isolated real-template browser checks at 1440/768/390/320 px: blank Add, required inputs, disclosure, collected payloads, saved View/Edit values, existing image retention, no page/field overflow and no JavaScript exceptions.
- Six Services/Service Requests browser cases at 1440/768/375 px: existing shared editor/navigation remains compatible.
- Visually inspected desktop/phone form screenshots. The fixture values in those images are test values, not live facilities.

Run the test suite from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test api.test_facility_rental_configuration api.test_facility_form_controls api.tests.FacilityConfigurationTests api.test_mobile_facility_booking modules.facilities.test_service_navigation api.test_facilities_archive accounts.tests.DomainAnalyticsPermissionTests --keepdb --noinput
venv/Scripts/python.exe manage.py check
```

For your existing local server, restart it if needed and hard-refresh the page (Ctrl+F5). No migration or seed command is required by this change:

```powershell
venv/Scripts/python.exe manage.py runserver
```

Manual checks in a disposable test environment:

1. Open Add Facility: no name, rate, official schedule, amenities, deposit or fee rows should be filled. Select Other and manually choose slot/room mode.
2. Select base-duration pricing: enter a base rate, duration and extra rate. Try an empty duration or negative amount: saving must fail.
3. Set minimum above maximum, enabled Monday closing before opening, or a deposit above 100%: verify rejection.
4. Switch base pricing to hourly and turn off deposit: verify hidden settings are not retained after save/reopen.
5. Select room mode: hourly-specific duration disappears, room information appears, and saving creates no room/booking/payment records automatically.
6. Reopen an existing record; edit only Description. Check that actual rate, images, capacity, relevant pricing/rules/fees and unknown saved JSON settings remain.
7. Check View is read-only, Add is reset after leaving Edit, image remove/preview, search, filters, pagination and archive/restore. Confirm a user without facility management permission cannot create/update through the endpoint.

## 8. Remaining limitations and debugging

- Approval/inspection/deposit/form-type settings are configuration for later transactions. Saving them does not create an inspection, select a new reservation screen, collect a deposit or auto-approve a booking. Existing mobile requests still start Pending, even if Requires Approval is unchecked.
- Only existing slot/room physical modes are offered. A new daily/custom booking engine and room management shortcut were not invented. Accommodation transactions and room-specific rate handling remain their existing implementation; configured rates do not automatically overwrite Room records.
- The mobile slot quote supports hourly/fixed/base-duration pricing. Complex charges and other methods need the complete admin quotation workflow before automatic mobile checkout can support them.
- Existing image persistence and transaction endpoints were reused, not comprehensively rewritten. Browser verification covered saved-image retention; it did not perform live file uploads or real payments. The listed tests are targeted regression checks, not proof every system flow has been tested.

| Symptom | Check / cause / action |
| --- | --- |
| New fields do not appear | Hard-refresh; inspect Network for `rental_form_controls.js` and `facility_form_controls.css`. Current template asset versions are `20261013-discount-rules`. |
| API returns 400 | Inspect response `errors`, then find the field in `validate_facility_payload` or `validate_rental_options`. Do not remove validation to make an invalid payload save. |
| Rate looks concatenated | Compare numeric `data-rate`/response `rate` with display `price_label`. The editor must read raw rate; never strip numbers from the entire summary. |
| Quote requires Facilities Admin | Check configured method, active fees and deposit; complex quotes deliberately cannot use a misleading hourly fallback. |
| No selectable slots | Check enabled weekday hours, existing slots, operational status and booking conflicts. Closed/unconfigured hours mean no invented slots. |
| Old schedule does not convert | Legacy text is ambiguous. Edit the Mondayâ€“Sunday controls explicitly; an unrelated description edit preserves it. |
| Service fields disappear unexpectedly | Inspect saved facility type/mode and existing Services classification. Do not move service workflows into ordinary physical bookings to bypass validation. |

Safe practice: locate the helper sentence under `facilityRoomsNotice` in `rental_rules.html`, change only its wording, then reload Add and switch slot â†’ room â†’ slot. Verify the message only appears for room mode and no request is sent before Save. Restore the wording and run the configuration tests above. This teaches template editing and progressive disclosure without changing database logic.

For a logic exercise, extend an existing validation test to check a deposit boundary (100% accepted, 100.01% rejected), then run only `api.test_facility_rental_configuration`. Tests use isolated data; leave production records alone.

## Amenity choice update â€” 2026-10-13

- **Reason/change:** Remove Basketball Court from the built-in amenity choices, as requested. A court is already represented by the facility type/name.
- **Files/anchor:** `backend/core/modules/facilities/services/facility_configuration.py:150`, the `amenities` list inside `facility_form_configuration()`, and this guide.
- **How it works:** `facility_form_configuration()` takes no arguments and returns JSON-safe form configuration. The template sends its `amenities` list to `FacilityFormControls.setAmenities(selected)` (`facility_form_controls.js:101`). That function combines standard choices with actual saved values, then builds the checkboxes. Only the standard choice list changed.
- **Backend/API:** Existing validation, custom amenities and saved amenity values remain supported. No endpoint or permission changed.
- **Database/migrations:** No database records changed; no migration needed.
- **Verification:** Executed a configuration assertion confirming Basketball Court is absent and Bleachers remains; all 10 `api.test_facility_form_controls` tests passed.
- **Limitation/debugging:** An existing facility that already saved Basketball Court can still show it when editing, because saved values are intentionally preserved. It is no longer offered on blank Add. Refresh the page if the old standard choice remains visible.
- **Safe practice:** Open Add Facility and inspect the amenities without saving. Confirm Basketball Court is absent and the remaining choices still appear. Trace the list from `facility_form_configuration()` to `setAmenities()` before changing another standard label; renaming a choice does not rename existing database values.

## Other / custom facility type â€” 2026-10-13

### 1. Cause / reason

Other previously had no separate classification text. The requested behavior is to describe a future rentable space without copying its facility name or changing its internal booking classification. Hostel Accommodation also needed the clearer human label Hostel / Room Accommodation.

### 2. Exact files changed and current anchors

| File | Approximate line / anchor | Added or changed |
| --- | --- | --- |
| `backend/core/api/models.py` | 380 `TYPE_CHOICES`; 434 `custom_facility_type`; 440 `get_facility_type_display` | Preserve `hostel`/`other` codes; update hostel label; read custom text from existing JSON and resolve the display label. |
| `backend/core/modules/facilities/services/facility_configuration.py` | 65 hostel configuration label; 276 `if facility_type == "other"`; 339 `owned` | Authoritative custom-text validation and removal of stale values for predefined types. |
| `backend/core/api/views.py` | 1410 `facility_type_label`; 1411 `custom_facility_type` | Expose resolved label and editable custom text using the shared model methods. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 162 custom data attribute; 201 table label; 426 custom input; 1139 hostel label; 1919 form value; 2013 JSON payload | Add the field directly below Type, load saved values, display resolved labels and send custom text separately from Name. Static asset versions were advanced to `20261013-custom-type`. |
| `backend/core/modules/facilities/static/facilities/js/rental_form_controls.js` | 60 `sync`; 86 `setWorkflow`; 127 `validate` | Show/require the custom field for Other; clear/disable it otherwise; load saved text and reject blank/whitespace input. |
| `backend/core/modules/facilities/static/facilities/css/facility_form_controls.css` | 92 `.facility-custom-type` | Add the existing 16px spacing rhythm beneath Type; no page/sidebar redesign. |
| `backend/core/api/test_facility_rental_configuration.py` | 136 custom validation tests; 247 API/table/report test | Cover required text, malformed values, name/code separation, label resolution, saved values, clearing and legacy partial updates. Existing Other test fixtures now provide explicit custom text. |
| `CAMPUSHUB_CONTEXT.md` | final `Other / custom facility type (2026-10-13)` entry | Record current architecture and compatibility behavior. |
| `docs/facility-configuration.md` | this section | Learning explanation, debugging, verification and manual steps. |

The existing browser harness `scratch/facility-rental-config/check.cjs` was extended for this feature. Logs are `scratch/facility-custom-type-tests.log`, `scratch/facility-custom-type-browser.log` and `scratch/facility-custom-type-services-browser.log`; `type-1440.png` and `type-390.png` are isolated test screenshots.

### 3. Changes made

The physical dropdown is Select type, Covered Court, Function Hall, Hostel / Room Accommodation, Other. Name remains a separate manually entered field. Selecting Other reveals an initially empty Specify Facility Type input directly below the dropdown. Selecting a predefined type clears/disables the input; the backend independently removes custom text from the saved configuration.

The table shows the custom text alone, such as Open Grounds, rather than Other - Open Grounds. View/Edit still selects the internal Other choice and displays its saved custom text underneath. The Other filter still matches the underlying `other` classification, including rows displaying custom labels.

### 4. How it works: inputs, outputs and data flow

```text
Name input --------------------> Facility.facility_name
Type select -------------------> Facility.facility_type (existing internal code)
Specify Facility Type input ---> API custom_facility_type
  -> validate_facility_payload -> workflow_config["custom_facility_type"]
  -> Facility.custom_facility_type property
  -> get_facility_type_display() -> table / API label / existing reports
```

`Facility.custom_facility_type` is a Python read property, not another database column. It returns trimmed string text only when the stored classification is `other`; otherwise it returns an empty string. `get_facility_type_display()` returns that custom text if present, or the predefined label. Neither method writes records or performs extra queries.

The API accepts the custom string separately from `name`. Validation trims it, requires it on new Other records/type changes or explicit Other edits, limits it to 120 characters, and rejects non-text values, angle brackets, control/invisible format characters and text without a letter/number. Predefined types ignore stale custom input. The cleaned JSON is written through the existing `_apply_facility_payload`; no second persistence path was created.

The existing HTML/JavaScript JSON form is reused; no Django ModelForm class exists for this editor and none was duplicated. `sync()` controls visibility/required/disabled states; `setWorkflow()` reads actual saved text; `validate()` improves immediate blank-input feedback. Django still rejects invalid direct API submissions.

An unsaved learning example, not a seed:

```python
facility = Facility(
    facility_name="Campus Events Ground",  # The displayed name remains independent.
    facility_type=Facility.TYPE_OTHER,      # Internal routing/filter code stays other.
    workflow_config={"custom_facility_type": "Open Grounds"},
)
print(facility.get_facility_type_display())  # Open Grounds; no save() was called.
```

Using existing JSON avoids adding another field to this unmanaged PostgreSQL model for one configuration label. To query custom text in a future feature, use the JSON key, not an ORM filter on the Python property. Current classification filters remain unchanged.

### 5. Backend / API behavior

The same create/update/list routes and permission checks are used. Responses contain `facility_type` (code), `custom_facility_type` (editable text) and `facility_type_label` (resolved display). Existing report code already calls `get_facility_type_display()`, so it receives custom text without new report queries. Mobile facility data already reads the API label. Booking/calendar selectors that display actual facility names continue to do so; no extra column or booking workflow was added. Structured backup/export data retains internal codes and the configuration JSON.

For compatibility, an existing Other record with no custom value can still receive an unrelated partial API update that omits the new key. It remains honestly labeled Other. Explicit blank custom text is rejected, and the current full Edit form requires an admin to supply its real classification. No existing record was backfilled with an invented type.

### 6. Database / migration impact

No new database column, FacilityType model, migration or seed was created/applied. The existing `workflow_config` JSON field stores custom text; the `hostel` internal value is unchanged. The model changes only a label and Python property/display methods. `makemigrations --check --dry-run` reported no changes. The live facility fingerprint and counts remained unchanged: 1 facility, 0 rooms, 0 bookings, 0 payments.

### 7. Verification results and manual checks

Executed: **66 Django tests passed**, including six new custom-type tests and the existing form/booking/archive/Services/RBAC checks; Django system checks passed; migration check reported no changes; controller syntax and targeted whitespace checks passed. Four browser widths (1440/768/390/320) passed required-field, whitespace, separate name/code/text, hide/clear, saved View/Edit, retained image/configuration and overflow/error checks. Six Services/Service Requests browser cases also passed. All examples were isolated test records; browser save requests were intercepted. Desktop and phone screenshots were visually inspected.

Manual checks in a disposable test environment:

1. Open Add; verify the five dropdown entries and empty name. Other reveals an empty required custom field.
2. Try a blank/space-only custom value; saving must be blocked. Submit an invalid direct API request and confirm a 400 field error with no inserted facility.
3. Manually save a valid Other facility with different name and custom type. Check the Type column shows only the custom text, the filter still uses Other, and reopening Edit restores both separate values.
4. Change Other to a predefined type; confirm the input clears/hides, and the saved workflow no longer has the custom key. Check images, pricing, rules, amenities and schedule remain applicable and intact.
5. Open View and confirm custom text is read-only. For Hostel, confirm the label changed while its code remains `hostel` and suggested mode remains Room / Stay-Based.
6. Confirm existing reports display the resolved type and users without facility management permission cannot save. Refresh/restart the local Django server if necessary; no migration command is required by this change.

### 8. Debugging, limitations and safe practice

- If the field stays hidden on Other, hard-refresh and verify the new `rental_form_controls.js?v=20261013-custom-type` loads. Inspect the selected value: it should be `other`, not the facility name.
- If the API rejects the text, inspect `errors.custom_facility_type` and the validation block around line 276. Do not weaken validation to accept malformed text.
- If a legacy record shows Other, no actual custom type was saved. Enter its real type manually; never copy its name automatically or backfill examples.
- Saved custom labels do not become new global dropdown options or new booking engines. Their underlying classification remains Other; booking modes keep the existing configurable behavior.
- No production upload, payment or device checkout was performed. Verification is targeted regression coverage, not a claim that every application flow has been tested.

Safe practice: run the unsaved model example above in `manage.py shell`, change only the name, and verify the type label remains Open Grounds. Then change only the workflow custom text and verify the name is unchanged. Do not call `save()`. Run `venv/Scripts/python.exe manage.py test api.test_facility_rental_configuration --keepdb --noinput` from `backend/core` to verify the authoritative rules with isolated test data.

## Physical facility form finalization and discount rules â€” 2026-10-13

This section is the current implementation report. Earlier sections describe preceding changes; current anchors and behavior below take precedence where defaults changed.

### 1. Cause / reason

The existing reusable form already supported physical classifications, custom Other text, capacity ranges, pricing, deposits, optional fees, schedules and images. Remaining gaps were an eagerly selected booking form, no discount-rule editor, no new custom minimum-duration input, and missing inspection suggestions. Saved edit values must not be replaced by Add defaults.

### 2. Exact files changed

| File | Approximate line / anchor | Current change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/rental_configuration.py` | 16 `FORM_DEFAULTS`; 24 `validate_discount_rules`; 83 `validate_rental_options`; 210 active-rule quote guard | Shared suggestion metadata, authoritative discount validation and a safe boundary for quotes needing eligibility review. |
| `backend/core/modules/facilities/services/facility_configuration.py` | 149 form defaults; 151 discount choices; 156 amenities; 217 Other mode validation; 345 owned JSON keys | Export metadata, add Fans/Stage as unselected choices, require an applicable mode for Other and reuse the existing JSON validator. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 483 `facilityCustomDurationField`; 511 service-only conditional; 528 Pricing & Discounts; 542 discount partial; 1644 read-only buttons; 1946 minimum collector | Add custom minimum, reorder pricing, organize headings, omit service transaction configuration from the physical form and safely collect existing fields. Asset version: `20261013-discount-rules`. |
| `backend/core/modules/facilities/templates/facilities/partials/rental_discounts.html` | 1 `data-rental-field="discounts"` | New compact Discount Rules rows/Add button, with no preset rules. |
| `backend/core/modules/facilities/templates/facilities/partials/rental_rules.html` | 16 rooms information | Match the requested Rooms / Units wording; no auto-created rooms. |
| `backend/core/modules/facilities/static/facilities/js/rental_form_controls.js` | 20 booking-form placeholder; 34 `configure`; 97 `setWorkflow`; 128 `addDiscount`; 156 `syncDiscount`; 168 `getWorkflow` | Suggest Add defaults after selection, preserve saved values, build/validate/collect discount rows and keep them out of Services. |
| `backend/core/modules/facilities/static/facilities/js/facility_form_controls.js` | 127 saved minimum; 153 `syncMinimum`; 160 `getMinimumDuration` | Show a Custom Duration input in minutes, load nonstandard saved durations and omit it for room/predefined-slot modes. |
| `backend/core/modules/facilities/static/facilities/css/facility_form_controls.css` | 96 `.facility-discount-row`; 107 responsive rules | Match existing compact rows, with six desktop columns and stacked narrow-screen fields. |
| `backend/core/api/test_facility_rental_configuration.py` | 183 discount round-trip; 196 invalid rules; 212 quote boundary; 220 suggestions; 242 custom minutes; 362 API edit | Seven additional test methods; fixture export uses only isolated test data. |
| `docs/facility-configuration.md` | this section | Current learning guide, debugging and verification. |
| `CAMPUSHUB_CONTEXT.md` | final `Physical facility configuration finalization` entry | Preserve current behavior and boundaries. |

Diagnostic harnesses `scratch/facility-rental-config/check.cjs` and `scratch/services-navigation/check.cjs` were updated. Logs are `scratch/facility-discount-rules-tests.log`, `scratch/facility-discount-rules-browser.log` and `scratch/facility-discount-rules-services-browser.log`.

### 3. Changes made

- Blank Add starts with Select type, Select booking mode, Select booking form, No minimum, no selected amenities, no rates, no schedule, and no fee/discount rows. No name/type copying or record creation occurs on selection.
- Covered Court/Function Hall suggest slot mode and the rental slip; Hostel suggests room mode and the accommodation slip. Approval and pre/post inspections are suggested Yes for new predefined facilities. The admin can change them. Other requires manual mode/form selection and custom type text.
- Edit uses actual saved form, rules, fees, discounts, duration, pricing, images, schedule and other configuration. Explicit saved `false` values remain false; changing only Description does not restore suggested inspection defaults.
- Pricing Method now precedes its applicable rate fields under Pricing & Discounts. Deposit, optional fees, Discount Rules, operating schedule, amenities and Requirements & Terms follow in the requested order.
- Discount rows contain Eligible Client Type, Discount Type, Discount Value, Applies To, Active and Remove. Custom application reveals a required explanation. No percentages/amounts are preset. Normal rental scopes do not silently include deposits, fees or refunds.
- Custom minimum uses whole minutes (1â€“1,440), collected as e.g. `47 minutes` and validated by the existing duration parser. Stored values remain decimal hours, and Edit restores the actual custom minute count. Room mode and existing predefined slots hide/disable it.
- Service-specific assessment/area/turnaround inputs are not rendered in the physical form. Existing Services pages retain them; discount groups remain hidden there. No Supported Activities section or service types were added to physical choices. Basketball Court remains absent from standard amenities; Fans and Stage are unselected choices.

### 4. Functions, inputs/outputs and data flow

```text
Existing metadata constants -> facility_form_configuration -> template JSON
  -> configure(type, preserve) suggests defaults only when selecting a type
Saved workflow JSON -> setWorkflow -> actual values/checkbox states/discount rows
Admin changes fields -> sync/syncDiscount/syncMinimum -> relevant enabled inputs
Save -> getWorkflow + getMinimumDuration -> existing API JSON payload
  -> validate_facility_payload -> validate_rental_options -> validate_discount_rules
  -> existing _apply_facility_payload -> existing Facility.workflow_config
```

`validate_discount_rules(rules, price_type, errors)` accepts the submitted rule list and pricing method. It returns a clean list and adds field-specific errors to the existing error dictionary; it does not save, determine eligibility or calculate a discount. `number()` is reused for decimal safety instead of creating another money parser.

`configure()` receives the selected type and a preserve flag. An explicit type selection suggests the form/mode/inspections. The edit loader subsequently calls `setWorkflow()` with saved data, preserving zero and false values. `addDiscount()` creates labeled DOM controls; `syncDiscount()` manages percentage limits, custom application and compatible scope checks; `getWorkflow()` returns their values. No client-side billing calculation is introduced.

Example rule shape for learning only, not a seed:

```json
{
  "eligible_client_type": "student",
  "discount_type": "percentage",
  "discount_value": "10",
  "applies_to": "rental_fee",
  "active": false
}
```

The value is a decimal string; `active: false` preserves an inactive rule for later admin review. A custom scope additionally stores `custom_scope` text. All rules live in the existing `workflow_config.discount_rules` list. The list starts empty and does not create a separate model.

### 5. Backend / API and validation

Reuse the existing Django JSON create/update/list endpoints and server-side permissions. No new ModelForm, API route, View class or duplicate Facility/pricing service was created. Existing serialization already returns the workflow JSON, including saved rules.

Validate at most 30 rules, allowed client/type/scope values, required nonnegative finite amounts with at most two decimal places, percentages â‰¤100, strict Boolean Active, and required plain-text custom application (â‰¤200 characters). Base Rate/Additional Hour Rate scopes require base-duration pricing. A pricing change that conflicts with a saved scope requires the admin to adjust the rule; values are not silently reassigned. A hidden custom explanation is removed when a normal scope is selected.

New Other configurations require explicit mode and booking form selection. Supported predefined types receive suggested form defaults when an older client omits the key. Legacy unrelated partial updates can preserve missing form configuration; explicit blank values are rejected. Existing capacity, name/custom-type, rates, deposit, schedule, image and minimum validation remain authoritative.

The shared `slot_base_amount()` continues hourly/fixed/base-duration calculation. An active discount rule requires a complete Facilities Admin quote because client eligibility is not yet verified by that endpoint. Inactive rules do not change normal prices. No discount is automatically deducted from rental, deposits, additional fees or refunds, and the API never trusts a browser-computed total.

### 6. Models, relationships and migrations

Reuse the existing unmanaged `api.models.Facility`, its `rate`, `price_type`, `booking_mode`, `capacity`, image fields and existing JSON configuration. No model/database field or relationship was added/changed for this finalization. No migration, seed or production write was performed. The new discount key is inside existing JSON. Room, Booking, FacilityPayment and historical records are unchanged.

Read-only verification matched the pre-task facility fingerprint and counts: 1 facility, 0 rooms, 0 bookings, 0 payments. Test examples lived only in Django's separate test database; browser save calls were intercepted. Selecting types or clicking Add Rule cannot create facilities or transactions.

### 7. Tests performed and manual testing

Final targeted suite: **73 tests passed** for configuration, discounts, defaults, custom durations, saved edits, schedules, booking behavior, catalog separation, archive and permissions. System check passed; migration check found no changes; both controllers passed syntax checks and targeted diff whitespace checks.

Four physical-form browser cases passed at 1440/768/390/320 px: blank Add, type/form/inspection suggestions, manual override, Other, percentage validation, custom scope clearing, rule removal, custom minimum, saved inactive rules/false inspection flags, read-only View, images and no overflow/JavaScript exceptions. Six Services/Service Requests cases passed at 1440/768/375 px, including hidden physical discounts. Desktop/phone screenshots were inspected.

One initial Services harness attempt queried markup before navigation completed. It now waits for the actual rendered Services section. A separate check caught an incorrect service-body class name in the new UI guard; the guard now uses the existing `service-catalog` class. Both final browser runs passed. These are confirmed verification issues, not evidence that the live sidebar failed.

From `backend/core`, rerun the same tests using the command in the main testing section above. No migration command is required by this feature. Restart the local server if needed with `venv/Scripts/python.exe manage.py runserver`, then hard-refresh.

Manual checks in a disposable test environment:

1. Open blank Add; confirm no selected booking form, sample fees/discounts, amenities or official rates/schedule.
2. Select each predefined type and inspect its suggested mode/form/inspection toggles. Override them, change only grouping/mode, and verify your choices remain. Other requires custom text, mode and form.
3. Add a rule; leave it incomplete or enter 101% and confirm saving is blocked. Select Custom application, enter approved text, then change to Rental Fee and confirm hidden text clears.
4. Save valid configuration, reopen Edit and verify every discount field and Active flag. Change only Description and verify all pricing/rules/images/hours persist; remove a rule and confirm it stays removed after reopening.
5. Select Custom minimum, enter 47 minutes and reopen after saving. Switch to room mode and confirm the minimum is omitted and no rooms are generated.
6. Check View is read-only, Archive preserves historical records, filters/pagination still work, Services stays separate and an unauthorized Marketplace Admin cannot save facilities.

### 8. Limitations, debugging and practice

Only existing physical slot/room booking engines are offered. Daily and Custom pricing are supported configuration; new daily/custom reservation engines were not invented. Rules/inspection/deposit/form selection configure later transactions; they do not create inspections, automatically approve requests, verify family/student eligibility or collect money here. Active discounts/complex charges require an admin quote. Existing mobile requests remain Pending. Live uploads/payments or physical-phone checkout were not performed by these tests.

| Symptom | What to inspect |
| --- | --- |
| Booking form already selected on blank Add | Verify fresh `20261013-discount-rules` assets; trace `resetFacilityForm` and `configure` with an empty type. |
| Saved inspection flag changed to Yes | Check actual JSON and `setWorkflow`; defaults must not replace explicit false. |
| Discount cannot save | Read `discount_rules.<index>` errors; check percentage range, selections, pricing scope and required custom explanation. |
| Custom duration appears invalid | Use whole minutes between 1 and 1,440. Inspect `getMinimumDuration()` output and existing `duration_hours()`; do not send the literal `custom` as a duration. |
| Discount appears on Services | Check the existing `body.service-catalog` class and `configure()` physical guard; do not add another workflow/type model. |
| Automatic mobile quote stops | Active discounts need verified eligibility/admin quotation. Do not silently ignore rules or invent customer proof. |

Safe practice: open Add and create an incomplete discount row without saving; fill its controls, switch Custom â†’ Rental Fee, and inspect how the extra input hides and clears. Remove the row and confirm no request was sent. For a code exercise, extend the existing percentage-boundary test to cover 0% and 100%, then run only `api.test_facility_rental_configuration`. Explain the expected accepted/rejected values before editing the validator; tests use isolated data and need no production seeding.

## Facility Features and Available Equipment â€” 2026-10-13

Historical implementation, superseded by **Simplified Facility Features and Fees** below. Equipment-specific files described here have been removed; use the latest section for current code and behavior.

### 1. Cause / reason

Confirmed: the physical editor used one Amenities checklist for permanent characteristics and movable items. Its generic fee placeholder suggested Chair Rental. Other text was appended to the amenities list without identifying it for Edit restoration. This made equipment pricing ambiguous and reopened custom features as arbitrary checklist entries.

Inspection of Facility/Room/Booking/FacilityPayment, module migrations, routes and live database found no equipment model/table or transaction foreign key. Existing `Facility.amenities` and `Facility.workflow_config` already support list/structured configuration. Add/Edit submits JSON through JavaScript and `validate_facility_payload`, not a separate Django Form class. Reuse these fields and views rather than duplicate models, forms or pricing engines.

### 2. Exact files and nearby anchors

Paths below are relative to `backend/core/` unless shown otherwise. Lines are approximate; search anchors after future edits.

| File | Line / anchor | Change |
| --- | --- | --- |
| `modules/facilities/services/equipment_configuration.py` | 8 FEATURES, 26 validate_equipment, 77 validate_features | New choices and authoritative configuration/duplicate-charge validators. |
| `modules/facilities/services/facility_configuration.py` | 156 choices, 285 validate_features, 362 validate_equipment | Connect cleaning to the existing physical payload validator; preserve omitted saved configuration. |
| `modules/facilities/services/rental_configuration.py` | 208 slot_base_amount equipment guard | Active paid equipment requires an admin quote rather than silently omitting charges. |
| `modules/facilities/templates/facilities/pages/admin_facility.html` | 453 Description, 549 Features, 557 equipment include; 904 controller, 1620 load, 1650 View, 1946 payload | Rename/reorder sections, facility-only wording, Add/Edit/View/save wiring; asset version 20261013-equipment. |
| `modules/facilities/templates/facilities/partials/equipment.html` | 1 facilityEquipmentSection | New compact manually configured section below Features. |
| `modules/facilities/templates/facilities/partials/rental_pricing.html` | 24 non-equipment helper | Explain general fees versus equipment pricing. |
| `modules/facilities/static/facilities/js/facility_form_controls.js` | 97 syncOther, 106 setAmenities, 128 renderLegacyInclusions, 147 getFeatureWorkflow | Restore/clear Other, separate and explicitly remove old inclusion labels. |
| `modules/facilities/static/facilities/js/equipment_form_controls.js` | 3 class, 11 setWorkflow, 18 addRow, 46 syncRow, 60 getWorkflow | New labeled row builder, disclosure and JSON collector. |
| `modules/facilities/static/facilities/js/rental_form_controls.js` | 117 fee placeholder | Remove the Chair Rental suggestion from general fees. |
| `modules/facilities/static/facilities/css/facility_form_controls.css` | 98 equipment grid, 111 responsive rules | Four desktop columns, two intermediate, one small-screen column; existing navy/light styling. |
| `api/test_facility_rental_configuration.py` | 22 validation tests, 367 API history test, fixture export near 499 | Cover valid/invalid rows, duplicates, Other, edits/removal, images/history and rendered fixtures. |
| `../../docs/facility-configuration.md` | 396 this report | Functions, verification, limitations, troubleshooting and practice. |
| `../../CAMPUSHUB_CONTEXT.md` | final features/equipment remembrance | Preserve current behavior for future tasks. |

Verification-only changes: `scratch/facility-rental-config/check.cjs` and `scratch/services-navigation/check.cjs` load the new controller and check test-rendered pages; logs/screenshots in scratch are not production assets. Reused unchanged anchors: `api/models.py:404` amenities and `:408` workflow_config; `api/views.py:1400` serialize, `:1443` apply, `:1472` create, `:1535` update. URLs, migrations, booking/calendar views and relationships unchanged.

### 3. Changes made

- Physical Amenities â†’ **Facility Features**: Bleachers, Restrooms, Parking Area, Lighting, Air Conditioning, Fans, Stage and separate Other. No new Chairs/Tables/Sound System/Projector/Bedding/Basketball Court feature choices.
- Other shows **Specify Other Feature \***, with blank `Enter facility feature` placeholder; saved text/checkbox restore. Unchecking clears text and sends `other_feature: null`.
- **Available Equipment** supports name, quantity, Included in Rental, Additional Fee, amount/basis, custom basis explanation, Active and Remove. No type-based examples or automatically populated rows.
- General fees have non-equipment helper text. Physical Description says `Describe the facility or space`; Requirements is facility-only. Services retains its existing amenity choices/editor and does not render Equipment. No Supported Activities section.
- Order: Images/Basic â†’ Booking Configuration â†’ Pricing & Discounts â†’ Operating Schedule â†’ Facility Features â†’ Available Equipment â†’ Requirements & Terms.
- Old movable amenity labels appear separately as **Saved legacy inclusions** under Equipment and survive unrelated edits. Manually configure correct equipment quantities/fees, then explicitly remove the old label if replacing it. No data is guessed.

### 4. Functions, inputs/outputs and data flow

1. Existing view renders configuration choices and real saved facility rows. `FacilityFormControls.setWorkflow()` reads Other; `setAmenities()` separates custom text and legacy inclusions from standard choices. `getAmenities()` returns selected text plus old inclusions not explicitly removed. Keeping actual custom text in amenities preserves existing mobile/feature displays.
2. `FacilityEquipmentControls.setWorkflow(workflow)` rebuilds saved rows once. `addRow(item)` builds labeled inputs; `syncRow(row)` shows fee controls only when charged and clears/disables irrelevant values. `getWorkflow()` outputs `{equipment: [...]}`, converting Yes/No controls to real JSON booleans. Browser validation is feedback; Django remains authoritative.
3. Existing Save handler sends fields/images and merged JSON to the protected endpoint. `validate_facility_payload(data, facility=existing)` merges omitted data with saved values, then validates features/equipment.
4. `validate_features(amenities, raw, existing, errors)` returns cleaned list/custom text. Non-null Other is required, trimmed, meaningful plain text, at most 200 characters. Blank/space-only values fail. Null removes the previously identified custom feature; hidden stale text cannot persist.
5. `validate_equipment(rows, general_fees, errors)` outputs a cleaned array while collecting errors. At most 50 rows; name required/plain text/up to 150; quantity required whole number 0â€“2,147,483,647; flags must be booleans. Included + Fee is rejected because partial charging is not implemented. Charged rows require non-negative finite money with at most two decimal places and a valid basis. Custom requires explanatory text up to 200. Uncharged rows omit all fee details even if directly submitted stale values are invalid.
6. `charge_identity(name)` normalizes case, simple plurals and rental/fee/charge words. Chair, Chairs, Chair Rental and Rental of Chairs match; matching general fees and duplicate equipment names fail. This detects simple labels, not arbitrary synonyms.
7. Existing `_apply_facility_payload` saves the existing Facility; `serialize_facility` returns the saved JSON. Explicit arrays replace old arrays; omitted arrays survive partial edits; `[]` removes equipment configuration. No booking/payment/stock writes occur in these validators.

Annotated test-only example (manual input, never seeded):

```json
{
  "amenities": ["Fans", "Access Ramp"],
  "workflow_config": {
    "other_feature": "Access Ramp",
    "equipment": [{
      "name": "Chair", "quantity_available": 12,
      "is_included": false, "has_additional_fee": true,
      "fee_amount": "10.00", "charging_basis": "item", "is_active": true
    }],
    "additional_fees": [{"name": "Cleaning", "amount": "50.00", "unit": "booking", "active": true}]
  }
}
```

The feature is general/built-in text. Chair pricing stays on the equipment row; Cleaning stays separate. A general fee named Chair Rental would return HTTP 400. Amount strings preserve decimal precision; quantity is an integer. JSON was chosen because these are existing facility settings without transaction references, not a new equipment inventory system.

### 5. Backend / API behavior

Reuse `POST /api/facilities/create/` and `/api/facilities/<id>/update/`. Login and `accounts.can_manage_facilities` unchanged. Invalid data returns existing HTTP 400 `error`/`errors` before saving; existing workflow_config responses expose configuration. No duplicate endpoint or service processing added.

Shared `slot_base_amount` retains existing hourly/fixed/base math. Active equipment with an additional fee requires a complete Facilities Admin quote: booking checkout does not yet select/price equipment. Free/included or inactive equipment alone does not alter standard rental pricing. Configuration does not automatically bill/reserve/decrement equipment or create invoice lines.

### 6. Database / migration impact

No model, field, foreign key or migration added. **FacilityEquipment model not added**: reuse existing JSON because transactions do not reference equipment rows. Use Active = No to retain a disabled configuration; Remove deletes only that configuration, never historical bookings/payments. If transactions later reference equipment, add appropriate relations/immutable quote snapshots in that task before allowing historical references to be removed.

No production examples or record updates. Read-only live fingerprint unchanged: one facility, zero rooms/bookings/payments. Legacy inclusions are preserved without inventing equipment quantities or migrating live data.

### 7. Tests performed / how to verify

- **79 Django tests passed.** New validation/API tests cover rows, quantity/money/flags, duplicates, custom feature restoration/clearing, partial edits, removal and no automatic records. Completed booking/payment history is created only in the isolated test DB and remains unchanged through Edit/Remove; images preserved. Existing mobile booking, Archive, Services and domain/RBAC regression tests passed.
- Physical Chrome checks passed at **1440/768/390/320 px**: empty Add, exact feature choices, Other feedback/restoration, saved equipment/false Active, View read-only, blank-row feedback, fee/custom-basis disclosure/clearing, legacy preservation/removal, no overflow or JavaScript exceptions. Saves intercepted; no live writes. Desktop/phone equipment screenshots inspected.
- Six Services/Service Requests browser cases passed at 1440/768/375. Django check clean; migration dry run reports No changes detected; JavaScript syntax checks clean; live fingerprint unchanged.

Run from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test api.test_facility_rental_configuration api.test_facility_form_controls api.tests.FacilityConfigurationTests api.test_mobile_facility_booking modules.facilities.test_service_navigation api.test_facilities_archive accounts.tests.DomainAnalyticsPermissionTests --keepdb --noinput
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

Manual checks in a disposable environment: confirm Add equipment starts empty; check Other then try spaces; configure free/included and paid equipment; try Included + Fee or a matching generic fee and confirm rejection. Save/reopen Edit/View, change only Description and verify configuration/images/history; disable/remove a row and reopen. Check Services, Bookings/Calendar and unauthorized writes. Restart the development server if necessary; Ctrl+F5 reloads static assets. No migration command required.

### 8. Limitations, debugging and practice

Equipment quantities are configuration, not live allocation/stock monitoring. No equipment checkout/payment/invoice workflow added. Duplicate protection catches simple names, not synonyms like PA System versus Sound System; review charges manually. Old arbitrary custom amenity strings remain preserved choices until deliberately converted to Other; movable labels remain separate legacy inclusions. Older clients using amenities remain compatible.

| Symptom | Code/data to inspect |
| --- | --- |
| Old label/missing equipment controls | Ctrl+F5; check 20261013-equipment assets, new script response and console. |
| Other not restored | Inspect workflow_config.other_feature â†’ setWorkflow â†’ setAmenities. Do not copy facility names or guess data. |
| Equipment save rejected | Read errors.equipment.<index>.<field>; name, whole quantity, booleans, money/basis and Included/Fee contradiction. |
| Chair Rental rejected | Keep chair pricing in its equipment row; remove the matching general fee. |
| Old Chairs label still visible | Intentional legacy notice. Manually configure accurate equipment, then Remove label when appropriate. |
| Hidden fee reappears | Trace syncRow disabled controls â†’ getWorkflow filtering â†’ backend cleaned JSON. |
| Mobile automatic quote unavailable | Active paid equipment requires an admin quote until equipment selection/pricing is implemented. |

Safe practice without saving production data: open Add, add a row, toggle Additional Fee Yes/No, observe required fields and stale values clearing, remove the row and return to the list. Code exercise: add a validation-test case for quantity `2.5` or differently cased Chair Rental, run only `RentalConfigurationValidationTests`, and explain the expected error before changing the validator. Follow input â†’ validator â†’ cleaned configuration â†’ response when learning independent changes.

## Simplified Facility Features and Fees â€” 2026-10-13

This is the current implementation, superseding the earlier separate Equipment design. Features now mean **anything physically provided**, including movable items. Extra costs belong in Optional Additional Fees.

### 1. Cause / reason

The latest request intentionally simplifies the previous configuration. Confirmed in code: Equipment had a separate row builder, validator, partial and CSS; generic fees rejected equipment names. Requirements was always submitted by the editor, so simply deleting its input would have sent an empty string and erased saved text. The shared template also serves Services, whose existing requirements must stay intact.

Inspected the existing Facility fields, Room/Booking/FacilityPayment relationships, validator, view/serializer, scripts, CSS, URLs, migration index and database table names. There is no separate FacilityEquipment model/table. Add/Edit uses a JSON payload validator, not a Django Form class. The safe change is to remove unused equipment controls, reuse amenities/fees and omit the removed Requirements field from physical writes.

### 2. Exact files changed, current lines and anchors

Paths are relative to `backend/core/`. Lines are approximate; search the anchor after future edits.

| File | Line / anchor | What changed and why |
| --- | --- | --- |
| `modules/facilities/services/feature_configuration.py` | 4 FEATURES, 8 plain_text, 14 validate_features | Added focused feature helper; retains Other validation from the removed equipment helper and adds movable provided-item choices. |
| `modules/facilities/services/equipment_configuration.py` | removed | Removed equipment creation/quantity/fee validation and the feature-versus-fee conflict rule. Feature validation moved to the helper above. |
| `modules/facilities/services/facility_configuration.py` | 156 form choices, 280 equipment payload rejection, 285 Other validation, 352 owned keys | Remove equipment choices/validation. Preserve old stored JSON on unrelated edits; no new equipment rows accepted. |
| `modules/facilities/services/rental_configuration.py` | 18 FEE_UNITS, 149 fee cleaning, 161 custom_basis; 217 legacy quote guard | Add Per Item/Fixed/Custom, validate fee names/money/custom details, retain older unit-code compatibility and pricing safeguards. |
| `modules/facilities/templates/facilities/pages/admin_facility.html` | 549 Features, 557 Services-only Requirements, 566 Terms; 1954 local historical text, 2040 omission | Remove physical Equipment/Requirements and controller wiring. Keep Terms and omit Requirements in physical API requests. Asset version 20261013-simple-features. |
| `modules/facilities/templates/facilities/partials/equipment.html` | removed | No separate Equipment section or example rows. |
| `modules/facilities/templates/facilities/partials/rental_pricing.html` | 24 helper text | Allow additional charges for provided features/items and facility use. |
| `modules/facilities/static/facilities/js/equipment_form_controls.js` | removed | Remove Equipment row creation/collection and its script import. |
| `modules/facilities/static/facilities/js/facility_form_controls.js` | 105 setAmenities, 131 getFeatureWorkflow | Movable items become ordinary choices again; remove legacy-equipment notice/buttons, retain custom Other restoration/clearing. |
| `modules/facilities/static/facilities/js/rental_form_controls.js` | 114 addFee, 134 syncFee, getWorkflow near 190 | Blank fee name/amount/basis, required indicators, conditional Custom explanation and hidden-field omission. |
| `modules/facilities/static/facilities/css/facility_form_controls.css` | 97 fee-custom rule, responsive rules near 107 | Remove equipment-only CSS; span custom fee explanation across the existing row grid. |
| `api/test_facility_rental_configuration.py` | 22 feature/fee tests, 70 legacy preservation, 361 API history/requirements, 495 fixture export | Replace obsolete equipment-management tests with current feature/fee behavior, preserve history/images/old text and verify removed UI. |

Also updated this guide (`docs/facility-configuration.md`, this section) and the final remembrance in `CAMPUSHUB_CONTEXT.md`. Verification-only changes: `scratch/facility-rental-config/check.cjs` and `scratch/services-navigation/check.cjs`; logs/screenshots remain scratch artifacts. No unrelated project cleanup.

Unchanged reuse anchors: `api/models.py:404` amenities, `:406` requirements, `:407` terms_conditions, `:408` workflow_config; `api/views.py:1400` serialize_facility, `:1443` _apply_facility_payload, `:1472` facilities_create, `:1535` facilities_update; `core/urls.py:189` create and `:190` update. No new views, URLs or Django Form classes.

### 3. Changes made

- Facility Features contains Bleachers, Restrooms, Parking Area, Lighting, Air Conditioning, Fans, Stage, Chairs, Tables, Sound System, Projector, Microphone, Bedding and Pickleball Net, plus the separate Other checkbox. Basketball Court is not a predefined choice. Existing saved custom feature strings remain readable/preserved.
- Other still reveals **Specify Other Feature \*** with blank `Enter facility feature`, restores saved text/checkbox on Edit/View, and clears when unchecked. Backend rejects whitespace-only text.
- Removed physical Equipment and Requirements controls. Terms placeholder is exactly `Enter terms and conditions for facility use`; Description stays `Describe the facility or space`. Services retains its own Requirements field and editor.
- Lower section order: **Operating Schedule â†’ Facility Features â†’ Terms & Conditions**. Images/Basic, booking configuration, pricing/deposits/discounts and schedule remain in their existing order. No Supported Activities or service workflow added.
- Optional fees permit provided-item charges such as Chair Rental alongside Chairs as a feature. Rows use Fee Name, Amount, Basis and Active. Basis choices: Per Item, Per Hour, Per Booking, Per Day, Per Night, Per Person, Fixed, Custom. Custom reveals a required explanation so the charge basis is explicit. No fee examples are saved automatically.

### 4. Functions, inputs/outputs and data flow

1. `facility_form_configuration()` publishes real supported choices. `FacilityFormControls.setAmenities(selected)` renders standard and saved feature strings; Other remains separately identified by `workflow_config.other_feature`. `getAmenities()` returns selected text; `getFeatureWorkflow()` returns the trimmed custom value or null when unchecked.
2. `FacilityRentalControls.addFee(fee)` builds existing compact fee rows. Existing `unit` values restore as Per Item without rewriting their code. New rows use `item`; no amount/name/basis examples prefill. `syncFee(row)` shows, enables and requires custom_basis only for Custom; switching away clears/disables it. `getWorkflow()` filters disabled fields and returns an explicit additional_fees array.
3. The normal Save handler sends real form values to the same endpoint. Physical requests omit `requirements` entirely. Local row state keeps the old hidden historical text; Services still submits its editable Requirements normally.
4. `validate_facility_payload(data, facility=existing)` merges omitted existing fields before cleaning. It calls `validate_features` and the shared rental validator, and preserves unowned existing JSON. Explicit new equipment configuration is rejected, while old stored equipment metadata remains untouched when omitted.
5. `validate_features(amenities, raw, existing, errors)` validates required trimmed plain Other text up to 200 characters, returns actual custom text in amenities, and removes the previous custom text when cleared. `plain_text` rejects non-text, markup/control characters, blank and meaningless punctuation-only input.
6. `validate_rental_options` cleans fee rows: list at most 30, meaningful name up to 150, required non-negative finite money with at most two decimal places, supported basis and real boolean Active. Custom explanation must be meaningful plain text up to 200. Other bases omit stale custom_basis. There is no comparison rejecting feature names against fees.
7. Existing `_apply_facility_payload` writes cleaned fields; `serialize_facility` returns actual saved amenities/workflow/terms. Omitted fee arrays preserve old rows; explicit arrays replace them; `[]` removes fee configuration without accumulating duplicates. No booking/payment or equipment inventory rows are created.

Annotated test-only example:

```json
{
  "amenities": ["Chairs", "Lighting", "Access Ramp"],
  "workflow_config": {
    "other_feature": "Access Ramp",
    "additional_fees": [{"name": "Chair Rental", "amount": "10.00", "unit": "item", "active": true}]
  },
  "terms_conditions": "Manually entered facility terms"
}
```

Chairs answers what is provided; Chair Rental answers what costs extra. There is no equipment row. `requirements` is absent, which means preserve saved requirements on Edit rather than overwrite it with an empty string. Decimal amount strings avoid binary floating-point money errors. This example is not seeded or applied to production.

### 5. Backend / API behavior

Existing create/update endpoints, login and `accounts.can_manage_facilities` enforcement unchanged. Invalid feature/fee settings return HTTP 400 with existing error/errors shape before a write. A submitted workflow_config.equipment key receives a clear error to use Features/Fees instead. Existing old metadata is preserved on partial edits; no automatic conversion into fees/features invents amounts or quantities.

The shared rate/quote engine is not duplicated. Active additional fees, deposits or discounts still need a complete admin quote; these controls configure charges, not equipment selection or automatic invoicing. The legacy active-paid-equipment quote guard remains only to avoid underquoting older saved records. Review any such old configuration manually; do not erase it or automatically charge it twice. Standard simple hourly/fixed/base quotes and current Pending mobile booking behavior remain.

### 6. Database / migration impact

No model/field/schema change and no migration. Keep Facility.requirements in storage for old records/Services; remove only the physical input. No FacilityEquipment model/table is created. Old workflow equipment JSON is preserved for compatibility/history without offering new equipment management. No facilities, rooms, bookings or payments seeded or changed in the live database; read-only fingerprint unchanged: one facility, zero rooms/bookings/payments.

### 7. Tests performed and commands

- **79 targeted Django tests passed**, covering feature + fee validity, all bases/legacy unit, custom basis cleanup, invalid rows, Other, omitted requirements, image preservation, existing completed booking/payment history and old JSON. Existing config/mobile booking/Archive/Services/domain-RBAC regression tests passed.
- Four physical Chrome widths **1440/768/390/320** passed: exact blank-Add choices, no Equipment/Requirements, Terms wording, custom feature and fee feedback/clearing, restored saved configuration, read-only View, requirements omission, no horizontal overflow or JavaScript errors. Saves intercepted; browser tests did not write production data.
- Six Services/Service Requests checks at 1440/768/375 passed. Desktop/phone lower-form screenshots inspected. Django check clean; migration dry run No changes detected; JS syntax and diff whitespace checks clean.
- One initial test failure was an encoding error introduced in test text through a PowerShell-to-Python pipe: peso/en dash became question marks. Corrected that test through apply_patch and reran the suite successfully. This was not a facility pricing failure. Preserve UTF-8 when editing Unicode text.

Run from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test api.test_facility_rental_configuration api.test_facility_form_controls api.tests.FacilityConfigurationTests api.test_mobile_facility_booking modules.facilities.test_service_navigation api.test_facilities_archive accounts.tests.DomainAnalyticsPermissionTests --keepdb --noinput
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

No migration command is needed. Restart the development server if necessary; Ctrl+F5 loads `20261013-simple-features` assets.

Manual checks in a disposable environment: open Add and inspect the final section order; select Chairs and add Chair Rental with an actual Per Item amount; save/reopen Edit/View. Check Other blank/space rejection and restoration; uncheck and confirm stale text disappears. Switch a fee Custom â†’ Per Booking and inspect clearing, save/edit/remove fees, verify Terms/images/schedule/pricing/discounts persist. Confirm old Requirements/booking/payment records remain stored, Services still shows its Requirements and unauthorized writes are denied.

### 8. Limitations, debugging and practice

Only current slot/room booking engines are offered. Daily/Custom pricing does not introduce a new booking-mode engine. Automatic fee application, discount eligibility, deposit collection and new service workflows remain outside this form task. Old equipment metadata is not automatically migrated or made editable; manually review old active charge configurations before using them for billing.

| Symptom | Inspect / fix |
| --- | --- |
| Old Equipment or Requirements input remains | Ctrl+F5, check template service_catalog context and asset version; do not remove Services requirements. |
| Removed Requirements text became blank | Inspect request body: physical writes must omit requirements, not send an empty string. Trace existing merge then _apply_facility_payload. |
| Chair Rental is rejected as equipment | Remove stale equipment_configuration imports/cached assets; current feature/fee names are independent. Inspect the actual field error. |
| Custom fee cannot save | Enter its required explanation; check additional_fees.<index>.custom_basis and amount/basis/name errors. |
| Custom text remains after changing fee basis | Trace syncFee â†’ disabled-field filtering â†’ backend cleaned JSON. |
| Old unit fee appears differently | The old unit code is accepted and displayed Per Item; new fee rows use item. No data migration required. |
| Automatic quote requires admin review | Inspect active fees/deposits/discounts or preserved legacy paid-equipment metadata. Do not bypass the quote guard. |

Safe exercise without saving live data: add a fee, choose Custom, type its explanation, switch to Per Booking and inspect that the explanation clears. Remove the row and return to the list. Code exercise: extend test_fee_bases_custom_explanation_and_stale_clearing with a second amount/basis, explain the expected cleaned dictionary, then run RentalConfigurationValidationTests. Learn the distinction between an omitted field (preserve it) and an explicit empty value (clear it); verify request JSON before changing persistence code.

## Explicit pricing selection and conditional form controls â€” 2026-10-13

This update keeps the simplified checklist/fees structure and renames the physical checklist **Equipment / Additional Requirements**. The label does not introduce equipment quantities, a new requirements field or another model.

### 1. Cause / reason

Confirmed: `configure()` selected each type's default pricing, `normalizePriceType()` converted blank/unknown values to hour, and Django also used a default when a method was missing. Together these could silently save hourly pricing. The main form uses a two-column grid; Booking Mode plus Minimum occupied its first row, leaving Maximum alone on the next. Fee/discount lists already started empty; Other/type/deposit/day visibility already worked and was retained rather than duplicated.

### 2. Exact changed files, current lines and anchors

Paths relative to `backend/core/`; search anchors if later edits move lines.

| File | Line / anchor | Change |
| --- | --- | --- |
| `modules/facilities/static/facilities/js/rental_form_controls.js` | 46 pricing options in configure, 59 required rate, 89 sync | Placeholder/required pricing; no physical automatic selection; hide rate until a method is chosen; restore real saved selections. |
| `modules/facilities/services/facility_configuration.py` | 232 price_type in validate_facility_payload | Require an explicit method for physical writes; keep existing Services defaults and omitted Edit-value preservation. |
| `modules/facilities/templates/facilities/pages/admin_facility.html` | 461 capacity wrapper, 551 checklist heading, 934 dynamic label, 1162 normalizePriceType | Pair capacities, rename the heading, remove blank/unknown-to-hour normalization; asset version 20261013-explicit-pricing. |
| `modules/facilities/static/facilities/css/facility_form_controls.css` | 51 schedule label, 94 capacity grid, 111 mobile rule | Visible time captions; two-column capacity pair, stacked below 577 px for readability. |
| `modules/facilities/static/facilities/js/facility_form_controls.js` | 40 Opening/Closing Time labels | Wrap existing time selectors in visible labels; retain same values, aria labels, schedule parser and visibility logic. |
| `modules/facilities/templates/facilities/partials/rental_pricing.html` | 14 Deposit Type, 18 Deposit Value | Shorter deposit labels, existing conditional reveal/validation unchanged. |
| `api/test_facility_rental_configuration.py` | 22 explicit-method test, 412 heading assertion, invalid-save test nearby | Reject missing/blank/space-only methods, preserve saved Fixed pricing on unrelated Edit, verify atomic API rejection and renamed UI. |

Also updated this guide and final `CAMPUSHUB_CONTEXT.md` remembrance. Verification-only harness `scratch/facility-rental-config/check.cjs` adds checks for blank pricing, hidden rate, capacity alignment and labeled opening/closing controls. Existing Services harness was run unchanged. Scratch logs/images are verification artifacts.

### 3. Changes / current behavior

- Physical Add starts with **Select pricing method**. Selecting a facility type does not automatically select hourly/nightly pricing. Saved Edit pricing restores; changing booking mode preserves an explicit selected method.
- Select a method to reveal its rate/base/custom fields. Clearing the method hides the rate and blocks saving. The browser normalizer preserves blank/unknown as blank; Django independently rejects it.
- Fees and discounts start with their Add buttons only; no blank active rows are generated. Manually added incomplete rows must be completed or removed, rather than silently discarded. Existing saved rows still load on Edit/View.
- Minimum/Maximum Capacity sit beside each other on desktop/tablet and stack on small phones. The grouping applies to physical Facilities only; Services keeps its layout.
- Checklist heading is **Equipment / Additional Requirements**, retaining the same amenities/Other data. Other still reveals **Specify Other Feature \***; Other facility type reveals **Specify Facility Type \***.
- Damage Deposit reveals **Deposit Type \*** and **Deposit Value \*** when checked. Enabled days reveal labeled **Opening Time** / **Closing Time** controls; closed days hide/disable them.

### 4. Functions, inputs/outputs and data flow

`FacilityRentalControls.configure(type, config, {preserve})` reads the current selection, rebuilds supported options with a blank physical placeholder, and restores only a valid explicit choice when preserving. `sync()` inspects that method/checkboxes and enables only relevant controls. Native required-field feedback helps the user; backend validation remains authoritative.

`normalizePriceType(value)` returns a recognized internal code or an empty string. It never turns a missing choice into hour. The existing Save handler sends `price_type` through the same API; `validate_facility_payload` merges stored Edit fields first, so omitted price_type preserves the actual saved method. A new physical request missing a method or explicitly sending blank receives HTTP 400. Services retains its existing supported default behavior.

Example: new physical payload `{"price_type":"","rate":"500"}` is rejected, even if a rate exists. Explicit `{"price_type":"hour","rate":"500"}` uses the existing hourly calculation. An unrelated Edit `{"description":"Updated text"}` preserves its saved Fixed/Hourly/etc. method. Examples demonstrate cleaning only and are not seeded.

`FacilityFormControls.buildSchedule()` adds captions around the existing selectors; `syncDay(row)` still toggles visibility/disabled/required based on the day checkbox. No duplicate schedule model or parser. Existing `setWorkflow` restores actual fees/discounts/deposit/schedule, and existing collectors omit disabled stale fields.

### 5. Backend / API behavior

Same protected create/update routes and RBAC; no new API or pricing engine. Physical creation clients must now provide a valid price_type. Explicit blank is invalid on Edit; omission preserves stored data. Existing monetary, capacity, Other, deposit, fee/discount and opening-before-closing validation remains in Django. No service workflow, automatic approvals, additional-charge billing or payment logic changed.

### 6. Database / migration impact

No model/field/migration changes or production writes. Checklist still uses Facility.amenities and workflow_config.other_feature; no new equipment inventory/document requirements field. Existing Requirements history and legacy JSON preservation remain. Live fingerprint/counts unchanged: one facility, zero rooms/bookings/payments.

### 7. Tests and manual checks

**80 targeted Django tests passed.** Four physical browser widths (1440/768/390/320) passed explicit blank choice/hidden rate, zero fee/discount rows, capacity alignment above 576 px, blank-save prevention, type/feature/deposit/day disclosure, saved View/Edit values, no overflow/JS errors. Six Services/Service Requests browser cases passed. Browser saves intercepted; API examples only in the isolated test database. Capacity screenshot visually inspected. System check, migration dry run and JavaScript syntax/whitespace checks clean.

From `backend/core`, run the existing test command in the previous section, or the focused `venv/Scripts/python.exe manage.py test api.test_facility_rental_configuration --keepdb --noinput`. No migrate command required. Ctrl+F5 loads the changed static assets.

Manual checks: open Add and verify placeholder/empty lists; choose a type and confirm pricing is still blank; choose hourly/base/custom and inspect fields; select Other type/feature and try spaces; enable/disable deposit and a day; save valid settings in a disposable environment and reopen Edit/View. Confirm real saved pricing/rows/false flags/images persist and unauthorized writes remain denied.

### 8. Limitations, debugging and learning exercise

Existing slot/room engines and admin-quote rules remain. This is a checklist-label/layout/selection change, not new equipment allocation or documentary-requirements workflow. All newly added incomplete fee/discount rows are intentionally validated. No live uploads/payments or phone booking checkout performed.

If pricing still shows Per Hour on blank Add, check 20261013-explicit-pricing assets and trace reset â†’ configure â†’ normalizePriceType, then inspect outgoing JSON. If Maximum drops to another row on desktop, inspect the shared capacity wrapper; below 577 px stacking is intentional. If conditional fields fail to reveal, inspect checked state and sync/syncDay rather than adding another state field. Missing method errors come from Django price_type validation; supply the actual intended method instead of restoring a silent fallback.

Safe practice: without saving live data, choose and clear a method and observe the disabled rate; add/remove a fee and toggle a closed day. For a code exercise, extend test_physical_pricing_requires_an_explicit_method with an unsupported code, predict the price_type error, and run the focused test class. Explain why omission preserves Edit data while explicit blank must fail; do not change model defaults to bypass form validation.

## Final physical facility configuration â€” 2026-10-13

This section supersedes earlier heading, scope and booking-mode examples. The final lower form is **Operating Schedule â†’ Facility Features â†’ Terms & Conditions**. There is no Equipment / Additional Requirements section or separate equipment/requirements management.

### 1. Cause / reason

The latest request restores the Facility Features name, adds configurable individual/shared accommodation pricing and makes discount scopes depend on the selected pricing method. Inspection confirmed existing Facility.rate and workflow_config.pricing can store this without new columns. Booking has a room identifier/dates but the current implemented quote flow does not provide verified per-room guest allocations; mobile rental_quote handles slot requests. Therefore configuration must not infer shared-room eligibility from an overall booking guest count.

The browser Edit check found a confirmed issue: saved optional room count was represented as string 0, while its input has min=1. That blocked saving even though no rooms were configured. The editor now displays blank for unconfigured/non-positive counts and retains positive counts. No room records are created.

### 2. Exact files changed and current anchors

Paths relative to `backend/core/`; line numbers are approximate.

| File | Line / nearby anchor | Change |
| --- | --- | --- |
| `modules/facilities/services/rental_configuration.py` | 22 DISCOUNT_SCOPES, 23 DISCOUNT_SCOPE_METHODS, 32 validate_discount_rules; 137 shared pricing; 211 pricing_label | Add authoritative per-method scope map, individual/partner scopes, Decimal shared-rate and whole occupancy validation, truthful saved rate labels. |
| `modules/facilities/services/facility_configuration.py` | 16 mode labels, 157 discount_scopes_by_method, 223 supported modes, 246 visible fields | Publish the same scope map to JS; accept Daily/Custom configuration; hourly minimum applies only to Slot-Based. |
| `modules/facilities/static/facilities/js/rental_form_controls.js` | 12 shared inputs, 43 modes, 86 disclosure, 111 restore, 184 scopes, 204 getWorkflow | Conditional shared tier controls/required occupancy, saved Edit restoration, dynamic scope options and targeted JSON collection. |
| `modules/facilities/templates/facilities/partials/rental_pricing.html` | 13 facilityPartnerRate, 19 facilityPartnerOccupancy | Add optional shared rate and conditional occupancy controls, with same-room helper; existing grid/style reused. |
| `modules/facilities/templates/facilities/pages/admin_facility.html` | 475 duration options, 547 Facility Features, 1604 optional units | Restore heading, offer No minimum/1/2/4 hours/Custom, fix blank optional room count; version 20261013-final-facility. |
| `api/test_facility_rental_configuration.py` | 22 shared round trip, 37 invalid tiers, 47 scope matrix, 62 modes; 564 accommodation API | New tier/scope/mode/API preservation tests; adapt prior invalid-mode case and heading assertion. |
| `api/tests.py` | 169 test_incompatible_booking_mode_is_rejected | Update the existing error expectation for the expanded physical mode options. |

Also update this guide and CAMPUSHUB_CONTEXT.md. Verification harness `scratch/facility-rental-config/check.cjs` covers new configuration and saved-tier Edit restoration; its modified browser fixture is isolated and never saved live. Scratch logs/screenshots are verification artifacts. No CSS changes this step; use the existing responsive form grid.

Unchanged models/relations: Facility.rate, price_type, booking_mode, amenities, workflow_config, images and historical requirements; Room, Booking and FacilityPayment. Same serializer/apply/create/update views and protected routes (`api/views.py` anchors serialize_facility/_apply_facility_payload/facilities_create/facilities_update). No separate Django Form class, new view, URL, model or migration.

### 3. Changes / final behavior

- Facility types remain Select type/Covered Court/Function Hall/Hostel / Room Accommodation/Other; Other uses a required trimmed custom type. No service type or automatic name/type copying.
- Booking Mode offers Slot-Based, Room / Stay-Based, Daily and Custom. Existing predefined type suggestions and editable approval/inspection/form mappings remain. Other is manually selected. Daily/Custom are configuration options, not newly implemented booking engines.
- Slot minimum choices start at No minimum, then 1/2/4 hours/Custom. Earlier saved durations such as 30 minutes restore through Custom with the same value. Room/Daily/Custom hide and omit hourly minimum. No rooms are generated.
- Pricing stays Select pricing method until chosen. Existing hour/base/day/person/night/fixed/custom fields remain. Person / Night uses **Standard / Individual Rate** (existing Facility.rate), optional **Partner / Shared Room Rate**, and **Partner Occupancy Required** when a shared rate is entered. No values or guest counts prefill.
- Shared rate must be finite non-negative money with at most two decimal places; required occupancy is a whole number at least 2. Same-room occupancy is the rule; separate rooms cannot qualify merely because total guests equals that number. This editor does not calculate/automatically apply eligibility.
- Optional fee/discount lists start empty. Fees remain outside the primary rental rate and may charge for provided items. No equipment/requirements models or sections. No example fees/discounts/rates are seeded.
- The final Facility Features checklist/Other text and Terms reuse saved data. Images/previews/removal/max-six count and existing JPG/PNG/WEBP behavior retained. Services retains its own fields/editor/requirements separately.

### 4. Functions and data flow

`FacilityRentalControls.sync()` reads price_type and partner input. It reveals the shared rate for person_night and requires the occupancy only if a shared rate is present. `setWorkflow()` restores both from pricing JSON, including zero money values and actual saved rule Active flags. `getWorkflow()` sends the shared pair only for person_night; changing methods omits stale tier fields. Existing Facility.rate remains the individual rate; do not introduce another standard-rate field.

The existing API validator merges omitted Edit fields, then `validate_rental_options()` cleans pricing and calls `validate_discount_rules(..., pricing=cleaned_pricing)`. Occupancy without a shared rate is ignored; a shared rate without valid occupancy fails. Switching to another method removes owned irrelevant pricing keys. Explicit arrays replace fees/rules without creating duplicate rows. Existing serializer returns this JSON for Edit/View.

DISCOUNT_SCOPE_METHODS is the single authoritative option map. `facility_form_configuration()` emits it for the browser; `syncDiscount()` rebuilds the selectable scope list. An incompatible previously selected scope stays visibly invalid rather than silently becoming another scope. Django rejects it independently. Partner scope is disabled/rejected until a partner rate exists, including a deliberately entered zero rate. Custom reveals **Custom Discount Scope \*** with the requested explanatory placeholder and clears when another scope is selected.

| Pricing method | Allowed discount scopes |
| --- | --- |
| Per Hour / Day / Person / Night / Fixed | Rental Fee, Entire Rental Rate, Custom |
| Base Duration + Additional Hour | Base Rate, Additional Hour Rate, Entire Rental Rate, Custom |
| Per Person / Per Night | Individual Rate, Partner / Shared Room Rate, Entire Rental Rate, Custom |
| Custom pricing | Entire Rental Rate, Custom |

Example test-only configuration:

```json
{
  "facility_type": "hostel",
  "mode": "room",
  "price_type": "person_night",
  "rate": "800",
  "workflow_config": {
    "pricing": {"partner_rate": "500", "partner_occupancy_required": 2},
    "booking_form_type": "accommodation"
  }
}
```

These are test inputs, not official rates or seeded records. Interpretation: rate is per person/night individually; partner rate requires the configured occupancy sharing one room. Two guests in separate rooms do not establish that condition. Actual application needs a verified room assignment/per-room guest count and an admin quote in the current workflow. No automatic calculation from a client-supplied global guest count is added.

### 5. Backend / API behavior

Reuse the current protected facility create/update endpoints and RBAC. Django validates selected mode/method, rate/tier/occupancy, method-specific discount scope, capacity, enabled deposit, features/Other, and operating hours before saving. Invalid data uses the existing HTTP 400 field-error response. No duplicate pricing engine or new service workflow.

Existing simple slot pricing stays unchanged. Mobile rental_quote rejects Room/Daily/Custom modes as a different request process, and slot_base_amount refuses person_night automated pricing. Active deposits/fees/discounts keep existing admin-quote safeguards. Discount configuration does not automatically discount deposits, unrelated fees or refunds. Calendar/admin schedule creation remains its existing workflow, not a newly promised accommodation/daily engine.

### 6. Database / migrations

No model/field/migration changes. Shared tier keys live in existing workflow_config.pricing; individual amount stays in existing rate. Model booking_mode is an existing text field, so Daily/Custom do not require a schema migration. No facility/room/booking/payment samples or production updates. Read-only live fingerprint/counts unchanged: one facility, zero rooms/bookings/payments. Historical requirements and legacy JSON remain preserved.

### 7. Verification and commands

**85 targeted Django tests passed.** New tests cover shared tiers/invalid money/occupancy, every pricing-method scope combination, partner scope without a rate, Daily/Custom ignoring hourly minimum, API round-trip/cleanup and no generated related records. Existing mobile, Archive, Services and domain/RBAC tests passed. Two previous test expectations assumed Daily was invalid or used the old mode error string; updated them for the new configuration options.

Four physical Chrome widths (1440/768/390/320) passed explicit selection, no seeded rows, dynamic scopes, tiers/conditional occupancy, Daily/Custom, old View/Edit controls, and saved accommodation JSON restoration/submission. This caught and verified the optional room-count fix. Six Services/Service Requests cases at 1440/768/375 passed. Saves intercepted; only isolated test fixtures changed. Desktop/phone tier screenshots inspected; no horizontal overflow or JS errors.

System check and migration dry run clean. JavaScript syntax/whitespace checks clean. Re-render test fixtures after inline template JS changes; otherwise an old fixture can still execute the previous editor code.

Run from backend/core:

```powershell
venv/Scripts/python.exe manage.py test api.test_facility_rental_configuration api.test_facility_form_controls api.tests.FacilityConfigurationTests api.test_mobile_facility_booking modules.facilities.test_service_navigation api.test_facilities_archive accounts.tests.DomainAnalyticsPermissionTests --keepdb --noinput
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

No migrate command required. Restart server if needed and Ctrl+F5 for 20261013-final-facility assets. Manual test in a disposable environment: select Hostel/Room/Person-Night; enter approved individual/shared rates and occupancy; reject missing/one/fractional occupancy; save/reopen Edit/View and verify settings. Check scopes for each pricing method, incompatible scope rejection, Custom text cleanup, optional shared-rate removal and method switching. Verify blank room count stays blank, positive saved counts remain, and images/terms/schedule/fees/false flags/history persist. Check Services/Calendar/Bookings routes and unauthorized access.

### 8. Remaining limitations, debugging and learning

This completes facility configuration, not verified room-allocation billing, equipment inventory, auto discount eligibility or new Daily/Custom processing. Admin review remains necessary for those quotes. A previously saved scope incompatible with the selected pricing method must be corrected explicitly; do not silently map it or alter stored history.

| Symptom | What to inspect |
| --- | --- |
| Old Equipment / Additional Requirements heading | Ctrl+F5; verify final-facility assets and both static/dynamic heading assignments. |
| Shared rate not restoring | Check pricing.partner_rate / partner_occupancy_required â†’ setWorkflow â†’ sync, not a duplicated parent rate. |
| Room Edit blocked with no room count | Inspect facilityUnits validity; unconfigured string 0 must display blank. Do not create rooms to bypass this error. |
| Partner discount disabled | Enter a valid shared rate first; check occupancy and scope. A legitimate zero rate must not be mistaken for missing. |
| Scope fails after pricing change | Select a supported scope from the authoritative map; do not rename it silently. |
| Custom scope text persists while hidden | Trace syncDiscount â†’ disabled-field filtering â†’ backend scope cleaning. |
| Saved 30-minute minimum shows Custom | Intentional preservation of a saved duration no longer offered as a preset; the number remains 30 minutes. |
| Mobile Room/Daily/Custom quote unavailable | These need their appropriate admin-assisted process; do not substitute hourly calculations or infer sharing from guest totals. |

Safe practice without saving live data: change pricing methods, inspect scope choices, enter/clear a shared rate and observe occupancy disclosure, then cancel. Code exercise: add an occupancy-invalid case (for example 1.5) or a partner-scope-without-rate subcase to the validation tests, predict its error, and run the test class. Follow individual rate â†’ shared criteria â†’ cleaned JSON â†’ Edit restoration. Before implementing any future shared billing, require verified per-room guest allocation and test one room versus separate rooms independently.

## Facility Type renamed to Category â€” 2026-10-13

### 1. Cause / reason
The user requested Category as the visible name for physical facility classification. The form, table and filter previously used Facility Type / Type / All Types. This is a terminology change, not a change to which facilities exist or how reservations work.

### 2. Exact files and current code anchors
| File | Line | Nearby anchor / change |
| --- | --- | --- |
| backend/core/modules/facilities/templates/facilities/pages/admin_facility.html | 101 | facilityTypeFilter: accessible category filter label and All Categories. |
| Same template | 148 | facility-col-type: physical table heading Category; Services remains Service Type. |
| Same template | 419 | facilityType: Category *, Select category; facilityCustomType at 427 uses Specify Category * / Enter category. Shared Add/Edit/View form. |
| Same template | 15 | Asset version 20261013-facility-category, also script includes at 665â€“666, reloads current validation script. |
| backend/core/modules/facilities/static/facilities/js/rental_form_controls.js | 214 | validate(): physical Other uses Specify Category required message; service wording retained. |
| backend/core/modules/facilities/services/facility_configuration.py | 288 | category_label in validate_facility_payload(): custom-category errors match the physical form; required_label at 301. |
| backend/core/api/test_facility_rental_configuration.py | 273 | Existing custom-type-required test expects Specify Category. |
| scratch/facility-rental-config/check.cjs | 36 | Existing browser dropdown assertion expects Select category; isolated QA only. |
| CAMPUSHUB_CONTEXT.md | Final entry | Records the rename and storage compatibility. |
| docs/facility-configuration.md | This section | Current explanation, verification and learning guide. |

### 3. Changes made
Physical facilities now display Category consistently in the table, category filter and form. Other reveals Specify Category *. Service Type, Room Type, Pricing Method and booking modes retain their separate meanings. No layout or category choice codes were changed.

### 4. How it works: functions, inputs, outputs and data flow
Django renders admin_facility.html with service_catalog indicating which page is open. Template conditions produce Category for physical facilities and retain Service Type for Services. The shared form handles Add, Edit and View, so the label is reused across those states.

FacilityRentalControls.validate() reads visible, enabled inputs and returns whether native validation accepts them. It now selects the physical category wording for an empty Other description. validate_facility_payload(data, facility) receives submitted data and an optional existing record; it validates/merges values and returns cleaned data, or raises ValidationError. Only its custom-category message wording changed, not its acceptance rules.

Annotated example (existing schema, no record is created by this example):

```json
{
  "facility_type": "other",
  "custom_facility_type": "Open Grounds"
}
```

The user sees Category = Other and Specify Category = Open Grounds. The browser still sends facility_type/custom_facility_type. Django stores the existing code and custom text using the existing field/workflow JSON. The table displays the saved classification. Keeping these identifiers avoids breaking APIs, Edit restoration and filters for a simple label change.

### 5. Backend / API behavior
Create/update routes, payload keys, validation rules, permissions, pricing and booking logic are unchanged. The custom-category required/plain-text errors now match the physical form. Service wording remains conditional. Internal function names and model fields retain type terminology intentionally; this does not introduce a new category model.

### 6. Database / migration impact
None. No fields were renamed or added, no migration was generated, and no production records were modified. The browser verification intercepted saves; Django tests used the isolated test database.

### 7. Tests performed and manual verification
- Ran 63 existing Django tests covering rental configuration, form controls, facility configuration and Services navigation: all passed; system check found no issues. Log: scratch/facility-category-tests.log.
- Ran existing headless Chrome form checks at 1440, 768, 390 and 320 pixels: all passed, including the renamed placeholder, saved Edit/View, validation and overflow checks. Log: scratch/facility-category-browser.log.
- node --check passed for rental_form_controls.js. git diff --check produced no errors; Git emitted existing line-ending warnings.

Manual check: reload Facilities with Ctrl+F5; confirm Category in the table, All Categories in the filter, and Category * in Add. Choose Other; confirm Specify Category *. Leave it empty and try validation, then cancel without saving. Open an existing facility in View/Edit to confirm the same terminology and its saved selection. Open Services and confirm Service Type remains unchanged.

### 8. Remaining limitations and debugging
This changes the physical web Facilities UI terminology. Internal API/model identifiers and unrelated mobile/service screens are not renamed. It does not create or migrate category records. If an old browser label remains, reload with Ctrl+F5 and inspect the template version 20261013-facility-category. If a filter stops working after a local edit, check that option values and facilityTypeFilter/facilityType IDs were not renamed with the visible text.

Safe practice exercise: locate the Category label at line 419 and the facilityType select below it. Identify which part is user-facing text and which part is the existing identifier. In a local unsaved experiment, edit only the supporting placeholder, refresh to observe it, then restore it. Verify existing selections still use codes such as covered_court/hostel/other. Do not change database field names merely to change a label.

## Final Facility categories, list alignment and requested record cleanup â€” 2026-10-13

This section supersedes the shorter Category terminology section above. It implements the attached final name/category specification and the subsequent request to remove Covered Court from the active list and correct its capacity.

### 1. Cause / reason
- The physical facility name and category both used names such as Covered Court. A specific display name and a broader category should be distinct.
- Confirmed from a read-only database query: the existing Covered Court maximum capacity was actually 300500, with no capacity_min. This was not a missing dash in the formatter. The user confirmed minimum 300 / maximum 500.
- Confirmed in CSS/browser checks: an older overflow: visible !important rule and negative responsive-container margins allowed table content to escape the card. Longer category/pricing text and mismatched alignments made columns harder to scan. A category filter also exceeded the 320px phone viewport because of its intrinsic width.
- The physical Rooms / Units KPI previously combined declared rooms_units with actual Room counts. Declared counts must not invent accommodation inventory.

### 2. Exact files changed, current lines and anchors
| File | Current line / anchor | What changed |
| --- | --- | --- |
| backend/core/modules/facilities/services/facility_configuration.py | 40, 54: FACILITY_TYPE_CONFIG | Court / Sports Facility and Hall / Function Space display labels; codes/default suggestions retained. |
| Same file | 288, 301: category_label / required_label | Physical Other errors say Specify Facility Category; same trim/plain-text validation. |
| backend/core/api/models.py | 440: get_facility_type_display | Reads category labels from the existing shared configuration; custom Other text remains first priority. No field definitions or stored choices changed. |
| backend/core/accounts/views.py | 735: configured_room_count annotation; 749: room_records; 807â€“808: context | Counts real rooms efficiently, physical KPI counts active Room / Stay-Based resources only, dropdown uses shared display labels. Services keeps its existing unit summary behavior. |
| backend/core/api/views.py | 1406: serialize_facility; 1423: configured_room_count; 1466: facilities_list | Returns actual room count alongside existing JSON keys; public list annotates counts in one query. |
| backend/core/modules/facilities/services/rental_configuration.py | 188: capacity_label; 206: pricing_label | Actual room summary or saved capacity range; summaries for saved pricing methods, explicit fixed/person/night labels and short safe custom notes. |
| backend/core/modules/facilities/templates/facilities/pages/admin_facility.html | 148â€“151: table headings; 168: room-count data; 415â€“431: basic form | Final columns and Facility Name / Display Name, Facility Category, custom category and short helper. Shared Add/Edit/View form. |
| Same template | 979: facilitySummaryContribution; 1141: formatFacilityType; 1495/1526/1974: roomCount | Browser uses actual room counts for KPI adjustments; category label resolves from the same backend configuration after save. |
| Same template | 1456: row menu; 15: asset version | Fixed-position action dropdown config for dynamically rendered rows; latest CSS cache version 20261013-facility-columns. |
| backend/core/modules/facilities/static/facilities/js/rental_form_controls.js | 214: validate | Visible Other required message matches Facility Category. |
| backend/core/modules/facilities/static/facilities/css/facility_form_controls.css | 120: summary wrapping; 129: containment; 142: column widths; 161: mobile filters | Header/body alignments match; table stays inside its card, all eight columns fit the 1440px review, smaller screens scroll locally. No new palette or cards. |
| backend/templates/partials/facility_row_menu.html | 11: data-bs-config | Existing Bootstrap dropdown uses fixed Popper positioning on physical Facilities so the scrolling container does not clip actions. Services unchanged. |
| backend/core/api/test_facility_rental_configuration.py | 180: pricing summaries; 392: category compatibility; 410: room/KPI counts | Updated label expectations and meaningful regression tests for existing-code preservation, true room counts and one-query public list. |
| scratch/facility-rental-config/check.cjs | 30 onward: list checks | Isolated browser QA now checks headings, alignments, desktop fit, containment and visible dropdowns; existing form tests retained. |
| scratch/facility-rental-config/archive_requested_court.py | 1: guarded one-time operation | User-requested live capacity correction and existing protected archive route; local pre-change backup and preservation assertions. Not application code. |
| docs/facility-configuration.md / CAMPUSHUB_CONTEXT.md | This section / final entry | Current report, debugging guidance and project remembrance. |

### 3. Changes made and existing functionality preserved
Final physical list: Facility | Category | Capacity / Units | Rate | Pricing Method | Status | Booking Mode | Actions.

Facility names stay independent and editable. covered_court displays Court / Sports Facility; function_hall displays Hall / Function Space; hostel remains Hostel / Room Accommodation. Other displays only the trimmed custom category. No service types were added to physical categories. Category filter values use the same stored codes; search still uses row text including name, category/custom category and location. Status/mode/archive filters, pagination, primary image, View/Edit/Archive/Restore and Recent Activities remain in place.

Name/category/pricing text is left-aligned; rate values are right-aligned; capacity/status/booking mode/actions are centered. Matching header/body classes prevent misaligned column titles. Longer summaries wrap inside their column. Physical table width shares total 100%, with a 1080px minimum inside a scrolling container. Only the table scrolls on a phone; the whole page does not overflow. The action dropdown stays accessible outside the clipped table region.

Category selection continues to suggest Slot-Based + rental booking form for court/hall, Room / Stay-Based + accommodation form for hostel, and explicit admin selection for Other. Pricing still starts Select pricing method and is not inferred as hourly. Saved Edit/View selections are restored using existing codes.

### 4. How it works: functions, inputs/outputs and data flow
FACILITY_TYPE_CONFIG maps stored codes to labels and existing form suggestions. get_facility_type_display() takes a Facility instance and returns custom Other text or the shared label. The form choices, server-rendered rows, API label, report resolver and browser formatFacilityType now agree.

admin_facility_page() selects the existing physical/service resources, then annotates configured_room_count with Count('rooms'). This gives each facility its actual number of related Room records without a query per list row. The physical KPI separately counts actual rooms belonging to active Room / Stay-Based facilities. Court/hall slot resources and archived facilities do not inflate that active KPI. No rooms are created.

capacity_label(facility) returns actual rooms, optionally followed by saved facility capacity, when Room / Stay-Based has configured Room records. Without records it falls back to the saved minimum/maximum capacity. Services keeps its existing configured-unit behavior. Example: capacity=500 and workflow_config.capacity_min=300 produce 300â€“500 pax. Merely entering rooms_units=6 does not create or imply six rooms.

pricing_label(facility) reads Facility.rate, price_type and existing workflow_config.pricing. It returns a display string only, not a billing calculation. Base-plus-extra uses saved base_duration/additional_hour_rate; person/night includes the optional shared rate and same-room occupancy criterion; fixed rate is explicitly fixed. Custom notes are shortened to 80 characters when plain and safely configured, otherwise Custom quote. Missing/unknown pricing shows Pricing needs review instead of assuming hourly. Template escaping and browser escapeHtml retain text safety.

serialize_facility() returns existing JSON plus configured_room_count. Public facilities_list() annotates first, so serializing the list remains one database query. Single create/update responses can count that one facility's rooms. The browser retains raw rooms_units for Edit while using roomCount for KPI changes, preventing a declared count from increasing inventory after save/archive/restore.

Annotated configuration example (explanatory only, no seed):

```json
{
  "name": "Specific Campus Hall",
  "facility_type": "function_hall",
  "capacity": 500,
  "workflow_config": {"capacity_min": 300}
}
```

The name stays Specific Campus Hall. Category displays Hall / Function Space. Capacity displays 300â€“500 pax. Changing the label never renames the database field or overwrites the facility name.

### 5. Backend / API behavior
Existing models, routes, permissions and booking/calendar logic are reused. facility_type/custom_facility_type remain internal keys; get_facility_type_display and facility_type_label now expose broader physical labels. configured_room_count is an additive response key. Protected create/update/archive/restore routes remain unchanged. Image storage, historical booking links and pricing calculation guards are preserved. Services remains separate with its current fields and routes.

### 6. Database / migration impact and requested cleanup
No schema migration. makemigrations --check --dry-run reported No changes detected. No facilities or rooms were seeded.

The user specifically requested removal of the existing Covered Court value and confirmed 300â€“500 capacity. The reviewed record CAMFACIL20260914562E was archived through the existing permission-protected archive view using an active authorized manager. Only maximum capacity=500, existing workflow_config.capacity_min=300, is_archived=True and updated_at changed. Every other Facility field, all other workflow JSON keys, image data and related Room/Booking/Payment counts were verified unchanged inside the transaction. The record remains recoverable with Archived Facilities â†’ Restore Facility. Active facility count is now 0 because this was the only active facility.

Local pre-change backup: scratch/facility-rental-config/requested-court-before.json. The guarded operation script refuses to rerun against the already archived/corrected record. Do not run it as part of Django startup or migrations. Earlier unchanged-live-fingerprint results in this guide are historical; this task intentionally changed the reviewed record as authorized.

### 7. Tests performed, debugging and manual test steps
- 88 targeted Django tests passed in 6.993 seconds across rental configuration, structured form controls, facility configuration, mobile booking, Services navigation, archive/history and domain permissions. Log: scratch/facility-columns-tests.log.
- Four physical Chrome reviews passed at 1440/768/390/320px: final headings, consistent alignment, desktop fit, card containment, local scrolling, accessible action dropdowns, saved Edit/View, pricing/discounts/Other and no JS errors. All browser saves were intercepted. Screenshots list-1440.png and list-320.png were visually inspected. Log: scratch/facility-columns-browser.log.
- Six Services/Service Requests browser cases passed at 1440/768/375px; physical controls did not leak into Services. Log: scratch/facility-columns-services-browser.log.
- Django system check, migration dry-run, JavaScript syntax and scoped git diff --check passed.
- Live cleanup assertions confirmed archive/capacity and preservation; subsequent read-only verification confirmed archived=True, minimum 300/maximum 500, active count 0 and unchanged related counts (all 0).

Debugging findings: initial new tests failed because the isolated category fixture lacked required Location and the logged-in public request included two session/user queries. The fixture now has a real test location, and the one-query public-list assertion uses a logged-out client. This fixed test assumptions without weakening production validation. The new browser list check then caught a 320px intrinsic filter-width overflow; min-width:0/max-width:100% fixes it. Visual inspection caught negative table margins; margin:0 and matching width contain the table. Fixed dropdown positioning was verified by hit-testing its actual visible menu.

Manual verification:
1. Reload Facilities with Ctrl+F5. Active Facilities should show no active Covered Court row.
2. Select Archived Facilities. Covered Court should remain inspectable with its saved image, Court / Sports Facility and 300â€“500 pax. Do not Restore unless you intend to reactivate it.
3. Open Add Facility, confirm final name/category labels and broad choices. Select each category to check booking-mode/form suggestions; pricing should stay an explicit choice. Cancel without saving.
4. Inspect View/Edit of the archived row. Verify name, images, rate/method and other configuration are preserved; cancel.
5. Test category/search/status/booking-mode/archive filters and pagination with your actual configured records. A custom Other category should show its text alone.
6. On a phone/tablet, scroll the table to Actions, open More, and confirm the menu is visible. The page itself should remain within the viewport.
7. For accommodation, verify actual Room records produce a room summary/KPI; an entered rooms_units value alone must not. Check Services/Bookings/Calendar still open normally.

Commands: restart the Django development server only if it is not auto-reloading, then Ctrl+F5. No migrate command is required. From backend/core, manage.py check and manage.py test api.test_facility_rental_configuration --keepdb --noinput provide focused verification using your venv interpreter.

### 8. Remaining limitations and safe learning practice
This is a physical Facilities web form/list update and display-label mapping, not a new accommodation booking/billing engine. Shared-rate billing still requires verified same-room allocation/admin review. Mobile/API consumers keep the same codes; consumers using the returned label receive the new broader names. Small screens intentionally scroll the compact eight-column table. Existing Recent Activities remains a record-based summary, not a newly introduced durable audit-history system.

Practice without changing data: inspect the facility-col-rate header and cell, then locate their shared CSS rule at line 145. Temporarily change text-align:right to center in browser DevTools and observe that both move together; reset it. Next trace function_hall â†’ FACILITY_TYPE_CONFIG label â†’ dropdown â†’ get_facility_type_display â†’ table. This demonstrates the difference between a stored identifier and visible text. For a safe code exercise, add an additional pricing_label assertion in the isolated test class, predict its output, and run that class; do not add hardcoded example values to application queries.

## Facilities final actions and real Recent Activities â€” 2026-10-13

This section implements the latest final Facilities-list request. It supersedes the previous record-based Recent Activities limitation and the earlier room-KPI restriction to Room / Stay-Based resources.

### 1. Cause / reason
The eight table columns, broad categories, capacity formatter, saved pricing summaries, images and compact alignment were already implemented and were retained. The remaining confirmed issues were:
- Archived rows offered only Restore, while the requested physical menu needs Edit Facility and Reactivate Facility.
- Re-rendering a saved row used the active menu unconditionally. Enabling archived Edit without preserving archive state would incorrectly change its menu and KPI totals.
- Recent Activities inferred Added/Updated from Facility timestamps and mixed in bookings. Browser initialization could also generate relative Today/days-ago entries from calendar records. These are not reliable administrative audit events.
- Search and status-filter wording differed from the final specification.

### 2. Exact files changed, current lines and nearby anchors
| File | Current line / anchor | Change |
| --- | --- | --- |
| backend/core/modules/facilities/services/activity.py | 8: EVENTS; 21: facility_snapshot; 40: record_facility_activity | New domain helper reusing existing AccountActivity/log_account_activity, not a new audit model. Detect actual saved changes and record one event per successful action. |
| Same file | 66: facility_activity_row_data; 74: facility_activity_row; 81: recent_facility_activities | Safe short messages, actual timestamps, eight newest physical facility events in a bounded query. |
| backend/core/api/views.py | 1â€“2: helper import; 1408/1428: serializer | Reuse the audit helper; count actual Room records regardless of a physical facility's booking mode; additive is_archived in serialized response. |
| Same file | 1509â€“1518: create transaction; 1550â€“1560: update snapshot/transaction | Write facility and audit together; return a safe activity summary. Failed/no-change edits produce no successful event. Existing image flow retained. |
| Same file | 1587â€“1592: archive; 1603â€“1608: restore | Lock the record, change state only when needed, reuse existing archive/reactivation routes and log once. Repeated requests return activity=null. |
| backend/core/accounts/views.py | 748â€“749: room_records | Physical KPI counts actual Room records on all active physical facilities. A court/hall increases this count only if real related rooms exist; manually entered rooms_units does not. |
| Same file | 752: Services-only old summary; 798â€“799: physical summary | Physical page reads existing audit records only; Services retains its separate current summary. |
| backend/templates/partials/facility_row_menu.html | 18â€“33: Edit / Reactivate | Initial server-rendered archived physical menu shows Edit and Reactivate; active menu keeps Edit/Archive. Eye handles View separately. |
| backend/core/modules/facilities/templates/facilities/pages/admin_facility.html | 97/111: filter labels; 254: activity subtitle | Search facilities..., All Statuses, Latest facility activities. Other filters/table structure unchanged. |
| Same template | 615/624/629: Reactivate modal | Physical wording confirms saved status/configuration is preserved; reactivation does not automatically change maintenance to Open for Booking. |
| Same template | 979: facilitySummaryContribution; 1511/1536/1589/1987: isArchived | Archived Edit remains archived, keeps its correct menu, and contributes zero to active KPIs. Actual room count is reused. |
| Same template | 1324: addFacilityActivity; 1351: addFacilityAuditActivity; 1363: initializeFacilityActivities | Stop calendar-derived rows on physical Facilities. Add only a safe summary returned by a successful backend write, with its recorded timestamp and an eight-row limit. |
| Same template | 1460: getRowMenuHtml; 2070/2131/2160: success handlers | Dynamic menus match initial HTML; create/update/archive/reactivate prepend actual returned events. Services' existing behavior retained. |
| backend/core/api/test_facility_rental_configuration.py | 393: audit workflow; 428: bounds/failure rollback; 463: actual-room KPI; 688: isolated export | Regression tests for real events, no-op/idempotent calls, unrelated activity exclusion, rollback, eight-entry limit and existing record/room logic. |
| scratch/facility-rental-config/check.cjs | Final archive/edit/reactivate review block | Browser uses real responses from the isolated Django test DB; all browser saves remain intercepted. |
| docs/facility-configuration.md / CAMPUSHUB_CONTEXT.md | This section / final entry | Current code explanation, debugging, verification, limitations and learning exercise. |

The unchanged table/capacity/rate helpers remain documented above: rental_configuration.py capacity_label at 188, pricing_label at 206; template table headings at 148â€“153; category mapping in FACILITY_TYPE_CONFIG and Facility.get_facility_type_display. No extra information columns, large cards, charts or colors were added. No CSS changes were needed for this step; the current containment/alignment is reused.

### 3. Changes made
Physical active menu: Eye â†’ View; More â†’ Edit Facility, Archive Facility.
Physical archived menu: Eye â†’ View; More â†’ Edit Facility, Reactivate Facility.
The existing /restore/ endpoint remains the internal route. No View duplication, Bookings, Calendar, Inspection, Payment or Job Order actions were added. No existing room/unit management page was found in the URLs/templates, so Manage Rooms / Units was not added and no new page was created.

The final filters read Search facilities..., All Categories, All Statuses, All Booking Modes, Active Facilities and Add Facility. Category codes, custom Other text, name/location search, filter combinations and five-row pagination remain unchanged.

Recent Activities now contains successful physical-facility administrative events only, newest first, up to eight. Each row shows the existing icon, a short named action, its small type description and actual date/time. It does not display actor credentials, raw metadata, internal IDs or connection information. Those existing detailed audit screens remain governed by their own permissions and safe formatter.

### 4. How it works: inputs, outputs and data flow
facility_snapshot(facility) takes the saved Facility and captures relevant owned fields into status/pricing/schedule/features/rooms/details groups. It does not copy a request body. record_facility_activity(request, facility, action=..., before=...) compares that snapshot after a validated write, or receives an actual add/archive/reactivate action. A single changed group produces its specific event; multiple groups produce Facility Updated with changed_sections in the existing audit metadata. Unchanged saves produce no event.

The helper reuses AccountActivity from accounts/models.py and log_account_activity from accounts/activity_logging.py. The existing logger records the actual administrator/role, timestamp and connection details and strips credentials from metadata. This helper adds only facility_id, a snapshot of facility_name, changed section names and the safe status label when relevant. No second audit table or duplicate logger is created.

Create/update operations wrap the database write and audit insert in transaction.atomic. Audit failure rolls the database change back rather than returning a saved facility without its audit. Archive/reactivate lock the row with select_for_update and check its existing state, preventing duplicate archive/reactivate entries. Existing permissions protect every endpoint. The normal validation and image-persistence flow is reused.

facility_activity_row(event) returns only kind/title/description/occurred_at for the compact UI. JsonResponse serializes the actual datetime. The browser's addFacilityAuditActivity displays this response only after success, escapes its text, formats its timestamp and trims the list to eight. Failed responses and activity=null add nothing. No guessed Today / days-ago timestamps are used for physical activity.

On reload, recent_facility_activities(physical_ids) filters AccountActivity by module Facilities, successful result, known facility action codes and IDs in the current physical catalog. It orders by created_at and primary key descending and limits eight in SQL. The existing Services classification excludes service resources from this ID scope, including legacy service booking modes. Marketplace actions and booking/request events cannot enter the summary.

Annotated data-flow example (conceptual only; not a seeded event):

```text
Admin saves a status change
  -> existing validation accepts Under Maintenance
  -> Facility write + AccountActivity write commit together
  -> facility_status_changed records the real actor and facility
  -> API returns a safe title: '<saved name> status changed to Under Maintenance.'
  -> current UI prepends it; reload reads the same audit record
```

Archived Edit uses additive is_archived from the API and the row's saved state. renderFacilityRow preserves data-is-archived and constructs that state's menu. facilitySummaryContribution returns zero for an archived facility. Reactivation changes its state before calculating the new contribution, so active counts recover correctly. The physical room KPI now counts actual Room rows on any active physical facility; declaring a number in rooms_units cannot invent inventory.

### 5. Backend / API behavior
Existing create/update/archive/restore routes and RBAC remain. Responses now add activity (safe summary or null), and serialized facilities include is_archived. Existing keys, category codes and display resolvers are retained. Approved/pending booking logic, calendar, prices, history, images and Services routing are unchanged. The existing User Monitoring activity formatter already resolves metadata.facility_id to an affected Facility, so detailed audit presentation reuses that implementation.

The helper logs future administrative actions through these APIs. It skips Services resources entirely. No transaction/request events are fabricated from facility timestamps. The summary is read-only; loading a page does not write an audit row.

### 6. Database / migration impact
No models/fields were added or renamed; no migration was generated. Existing AccountActivity stores future real actions. No facilities, rooms or events were seeded into the live database. Test examples are isolated test-database records only.

Read-only live verification confirmed Covered Court remains archived with 300â€“500 pax, and the new facility audit-event/summary counts are both 0. Its older archive happened before this logging hook existed; it was deliberately not backfilled as a newly observed event. An honest empty Recent Activities state is expected until a real future action occurs. The prior authorized archived record and its history were not modified in this task.

### 7. Tests performed and debugging
- 110 targeted Django tests passed in 13.703 seconds, covering the facility configuration/form helpers, mobile booking, Services separation, archive/history, permissions and existing activity-detail APIs. System check found no issues. Log: scratch/facility-audit-tests.log.
- New regression tests prove actual add/status/pricing/archive/reactivate events, no events on unchanged/repeated/invalid requests, exclusion of Marketplace/services/bookings, eight-entry limit, archived Edit preservation and rollback if audit persistence fails.
- Four physical browser cases passed at 1440/768/390/320px, including final table/alignment, scroll/menu visibility, existing form behavior and new archive â†’ archived Edit â†’ reactivate flow. The active KPI remains zero during archived Edit and returns after reactivation. UI events use exported real Django test responses; all saves are intercepted. Log: scratch/facility-audit-browser.log.
- Six Services/Service Requests browser cases passed at 1440/768/375px. Log: scratch/facility-audit-services-browser.log.
- Migration dry-run reported No changes detected. Scoped git diff --check passed. The desktop screenshot was visually inspected; the existing table/card style and compact activity rows remain consistent.
- An initial test command referenced a non-existent accounts.test_activity_details module. The valid accounts.test_activity_api module was located and the full targeted command rerun successfully; the import error was a test-command mistake, not an application failure.

Manual verification:
1. Ctrl+F5 on Facilities. Confirm the exact eight columns and final filter text.
2. Select Archived Facilities. Eye opens View; More shows Edit Facility and Reactivate Facility, with no extra transaction links.
3. Edit an archived record only when an actual change is intended. It must stay archived; active KPIs must remain unchanged; its real successful update should appear in Recent Activities.
4. Reactivate only when intended. Confirm its saved operational status remains (e.g. maintenance stays maintenance), menu switches to Edit/Archive, and active KPIs update.
5. On a real active facility, change only status or price, save, and reload. Confirm one real named Status change or Pricing update row survives reload.
6. Submit an invalid form or save unchanged data. Confirm no fabricated successful audit row. Check search by name/category/custom category/location and combined filters/pagination.
7. Open Services, Bookings and Calendar. Service/request/booking actions must not appear in physical Facilities Recent Activities. No new Manage Rooms route is present.

Commands: no migration needed for this change. Restart the Django development server if it is not auto-reloading and use Ctrl+F5 (asset version 20261013-facility-audit). From backend/core, run venv/Scripts/python.exe manage.py check or the focused manage.py test api.test_facility_rental_configuration accounts.test_activity_api --keepdb --noinput command.

### 8. Remaining limitations and learning practice
Historical actions without existing audit records are not reconstructed from timestamps. Direct database/model edits outside these admin APIs do not automatically generate these events. There is no room-management screen to link yet; room-configuration fields use the existing form and actual Room records determine counts. Multiple changed sections produce one concise Facility Updated event; changed section names remain in audit metadata. Existing media-file processing is unchanged; transaction guarantees here cover database facility/audit records.

Safe practice: in View, compare an archived row's menu with its data-is-archived attribute using browser DevTools without saving. Trace is_archived from serialize_facility â†’ finishUI â†’ renderFacilityRow â†’ getRowMenuHtml and facilitySummaryContribution. Then read facility_snapshot and predict which group changes if only rate changes. Add an isolated test for features-only or schedule-only changes and assert its event code; run the test class, not a live database seed. To debug a missing summary row, inspect module/result/activity_type/facility scope in the test database; never insert a fake event merely to make the UI non-empty.

## Facilities List heading and labeled filters â€” 2026-10-13

### 1. Cause / reason
The user requested removing the Active/Archived dropdown and adding a heading/filter structure like Products. Products already has a Products List heading, supporting description and labels above filter fields. The physical Facilities toolbar previously used unlabeled inline controls and the archive selector.

### 2. Exact files changed, current lines and anchors
| File | Line / anchor | Change |
| --- | --- | --- |
| backend/core/modules/facilities/templates/facilities/pages/admin_facility.html | 90â€“95: facility-list-heading | Facilities List heading and short supporting description inside the existing list card. |
| Same template | 97â€“137: facility-filter-field | Associated Search, Category, Status and Booking Mode labels above existing controls; existing IDs/options retained. |
| Same template | 139â€“146: service_catalog archive condition | Archive-state dropdown now renders only on Services, not physical Facilities. |
| Same template | 15: CSS cache version | 20261013-facility-filters forces the current layout to reload. |
| backend/core/modules/facilities/static/facilities/css/facility_form_controls.css | 168: Products-style filters block | Scoped heading typography, labeled grid, 44px controls, desktop/tablet/phone layout. Existing palette and list/table style reused. |
| scratch/facility-rental-config/check.cjs | Startup label checks and final archive case | Existing isolated review checks heading/labels, absent archive selector, and default active filtering after Archive. |
| docs/facility-configuration.md / CAMPUSHUB_CONTEXT.md | This section / final entry | Current explanation, tests, troubleshooting and practice. |

### 3. Changes made
Physical Facilities now has Facilities List with Review, filter, and manage campus facilities. Each filter has a visible label connected to its input/select. Add Facility stays at the end of the filter row. The Active/Archived/All Facilities dropdown is removed from this page. Services keeps its existing controls.

The existing desktop toolbar becomes a grid: wider Search, Category, Status, Booking Mode, Add. At tablet width fields wrap into two columns; on a small phone they stack into one column. Controls align along the bottom of their labels, avoiding uneven positions. No extra card, table column, record or page was added.

### 4. How it works: functions, inputs/outputs and data flow
Django receives service_catalog from admin_facility_page and conditionally renders the physical heading/labels or the existing Services controls. A label's for attribute points to the existing control ID; clicking the label focuses that control. Its value and change listener remain the same.

Example:

```html
<label for="facilityTypeFilter">Category</label>
```

This changes presentation only. The same facilityTypeFilter select still sends its selected stored code into the existing getMatchedFacilityRows function.

getMatchedFacilityRows reads search/category/status/booking-mode and the optional archive selector. Existing code at line 1021 uses facilityArchiveFilter?.value || 'active'. With no physical archive selector, it defaults to active and excludes data-is-archived rows. The existing listener at 1119 uses optional chaining, so a missing selector causes no JavaScript error. Services still has the selector and its prior behavior.

applyFacilityFilters continues to combine conditions, reset/clamp pagination, hide unmatched rows and update the count/footer. Archive still updates the row flag and active KPI values; the row disappears from the active list. No new archive calculation or backend filtering logic was duplicated.

### 5. Backend / API behavior
No backend, model, permission, endpoint or audit changes in this step. Existing Add/Edit/View/Archive/Reactivate APIs remain. Search/filter IDs and pagination are reused. The physical list defaults to active records; Services archive filtering is unchanged. Existing facility rows and audit history remain stored.

### 6. Database / migration impact
None. No live data was deleted, changed or seeded. No schema change or migration. This is a template/CSS update; isolated tests use their own test database.

### 7. Tests performed and manual verification
- 52 existing Django tests passed in 2.958 seconds for facility rental configuration and Services navigation, including authentic HTML exports. System check found no issues. Log: scratch/facility-filter-header-tests.log.
- Four physical Chrome cases passed at 1440/768/390/320px: new heading and associated labels, absent archive dropdown, table fit/containment, no page overflow, existing form/Edit/View behavior and archived-row exclusion after a successful mocked Archive. Saves are intercepted and responses come from the isolated Django test DB. Log: scratch/facility-filter-header-browser.log.
- Six Services/Service Requests cases passed at 1440/768/375px; existing controls and layout preserved. Log: scratch/facility-filter-header-services-browser.log.
- Browser harness syntax and scoped git diff --check passed. Desktop and 320px screenshots were visually inspected.

Manual steps: Ctrl+F5 on Facilities. Confirm Facilities List and the four filter labels, with no Active/Archived dropdown. Search by facility name/location/category and combine category/status/booking-mode filters; check matching count and pagination. Open Add and cancel. On a phone confirm fields stack without page overflow and the table scrolls locally. Open Services and confirm its archive selector remains.

### 8. Remaining limitations and safe practice
Archived physical records are no longer selectable through a dropdown on this list. They remain in the database and existing protected reactivation APIs remain; this step does not add another archived-record navigation control. This implements removing the selector, not deleting the saved Covered Court record. No migration command is needed; refresh with Ctrl+F5.

Practice: click Category's label and confirm focus moves to its select. In DevTools, temporarily change the heading text and reset it; notice that data/filter results do not change. Then trace select value â†’ getMatchedFacilityRows â†’ applyFacilityFilters â†’ pagination. To debug a missing row, inspect its data-is-archived flag and selected category/status/mode before modifying backend data. Keep control IDs stable when changing labels, since existing listeners depend on them.

## Facilities Recent Activities: performer, icons and centralized history â€” 2026-10-13

### 1. Cause / reason
The existing physical-only audit summary already reused AccountActivity, but omitted the performer, used one calendar icon for every row, combined discount changes with pricing, and treated booking configuration as generic details. It showed eight entries and had only a generic empty message. The current-ID filter also hid an actual historical reactivation event after its facility row disappeared. The new request calls for a small management summary and a permission-aware link to existing detailed history.

### 2. Exact files changed and current anchors
| File | Current line / anchor | Change |
| --- | --- | --- |
| backend/core/modules/facilities/services/activity.py | 10: FACILITY_ACTIVITY_LIMIT; 11: ICON_PATHS; 20: EVENTS | Five-entry limit, trusted small SVG paths, clearer labels and separate discount/booking event codes. Existing codes/history retained. |
| Same file | 35: facility_snapshot; 60: record_facility_activity | Compare discount and booking configuration independently; new events include resource_kind=physical in existing audit metadata. |
| Same file | 87: facility_activity_row_data; 96: facility_activity_row | Return action-specific icon, recorded performer, readable message/type and one server-local time label. No sensitive fields. |
| Same file | 109: recent_facility_activities | Bounded newest-first query preserves known physical history even without the target Facility; excludes explicit Services metadata and currently configured service IDs. |
| backend/core/accounts/views.py | 799: summary call; 819: can_view_facility_activity_history | Read existing history; show View All only for a Super Admin who can access the existing User Monitoring page. No permission granted. |
| Same file | 1542â€“1544: activity_module_filter; 1581: context | Existing detailed activity table supports module=Facilities after its existing scope/date/user filters. Charts and session overview remain unchanged. |
| backend/core/modules/facilities/templates/facilities/pages/admin_facility.html | 271: View All; 277â€“288: rows/empty state | Small icons, type/performer, actual date/time and requested two-line empty state. Existing white card reused. |
| Same template | 1368â€“1377: addFacilityAuditActivity | Live success responses render the same fields/icons and trim five rows. Decorative icon is hidden from screen readers; text is escaped. |
| Same template | 15: asset version | 20261013-facility-activity-widget reloads the new scoped styles. |
| backend/core/modules/facilities/static/facilities/css/facility_form_controls.css | 221: widget styling block | Compact Montserrat rows, restrained navy icons/text, subtle separators, no shadow; time moves below text on small screens. |
| backend/core/modules/user_management/templates/user_management/pages/admin_user_monitoring.html | 117: hidden module field; 229â€“231: log section | Preserve Facilities filter on form submission; link anchor and Facilities Activity Log heading on the existing page. |
| backend/core/api/test_facility_rental_configuration.py | 393/408/442: new regression cases; 752: isolated export | Historical preservation, source separation, performer/privacy, specialized events, history filtering/RBAC, empty rendering and real test response exports. |
| scratch/facility-rental-config/check.cjs | Widget checks/screenshots | Existing isolated browser review checks performers, distinct icons, five-row limit, populated/empty layouts and actual API summaries. |
| docs/facility-configuration.md / CAMPUSHUB_CONTEXT.md | This section / final entry | Current functions/data flow, verified behavior, debugging and safe practice. |

### 3. Changes made
The widget shows up to five actual facility-management events, newest first. Each row has a small action-specific icon, a short named message, type plus recorded performer, and date/time. Add uses plus; Update/features/rooms use pencil; status uses refresh; pricing/discount uses money; schedule/booking uses calendar; Archive uses archive; Reactivate uses check.

Discount-only edits now say discount rules updated, and booking-rule/form/mode-only edits say booking configuration updated. Schedule messages say operating schedule updated. Multiple changed groups still produce one concise Facility Updated event, with changed section names in the existing audit metadata. No duplicate events are inserted merely to fill the widget.

Empty state: No recent facility activity. The supporting sentence was removed on 2026-10-13 at the user's request. The widget has no pagination, technical record IDs, raw metadata, IP/browser/device details, credentials or tokens.

### 4. How it works: functions, inputs/outputs and data flow
facility_snapshot receives a saved Facility and groups its relevant fields into status/pricing/discount/booking/schedule/features/rooms/details. record_facility_activity receives the existing request, saved facility and prior snapshot or actual action; it detects real changes, skips Services, and calls the existing log_account_activity. Existing atomic write hooks and unchanged/failed/idempotent behavior remain intact.

facility_activity_row reads the existing audit record, not the latest user profile. It uses the recorded full_name, then a usable recorded username, otherwise System. A numeric-only identifier is not displayed as a person's name. This avoids inventing a performer and preserves the name recorded when the action happened. The server formats created_at in the configured local timezone; both rendered rows and live API updates use the same time_label.

The safe output contains only kind/title/description/icon_path/occurred_at/performed_by/time_label. SVG paths come from the fixed ICON_PATHS dictionary, never a submitted form value. Template escaping and escapeHtml protect rendered text/attributes. The existing API routes automatically include these fields through their existing activity formatter; no new endpoint or logging model is introduced.

recent_facility_activities uses a service-ID lookup plus a bounded audit query. It filters module Facilities, successful results and the known facility-management event codes, excludes service IDs and explicit nonphysical classifications, orders created_at/primary key descending, and limits five. New records have physical classification in metadata. Older known physical event codes remain readable from their snapshots when the target row is gone. No old records are rewritten or backdated.

Annotated flow (explanation only):

```text
A real discount-only save
  -> existing validator cleans discount_rules
  -> snapshot comparison detects discount group
  -> existing AccountActivity records facility_discount_updated + actual actor
  -> formatter returns saved-name message, Discount Rules Update, performer and time
  -> widget displays it immediately; reload reads the same record
```

### 5. Backend / API and View All behavior
AccountActivity and log_account_activity are reused. Facility CRUD, images, status/booking logic, filters, table pagination and Services remain unchanged. The summary is read-only and cannot create/delete audit events.

View All Activity opens /admin-user-monitoring/?module=Facilities#recent-user-activity. The existing page retains its period and support-scope rules and its normal paginated detailed activity table. The module filter narrows that table after existing filtering, and a hidden field preserves it when the monitoring form submits. The heading becomes Facilities Activity Log for that filtered state; session/KPI/chart calculations are not redefined.

Existing central monitoring only admits Super Admin or scoped Marketplace support roles. The Facilities-page link is therefore shown only when the viewer is Super Admin and has can_view_user_monitoring. A Facilities Admin does not gain monitoring permissions or a new history page. Detailed history still uses the existing safe formatter and access controls.

### 6. Database / migration impact
No model or schema change; no migration. Future actual events gain two specific event codes and physical scope metadata in the existing JSON field. Historical records are preserved as stored; their display labels can become clearer without altering the saved audit event.

No live facilities or activities were seeded, deleted or updated by this task. Read-only inspection found no current Facility rows but one existing Covered Court reactivation event. The updated widget now returns that same historical event, and the audit count remains one. It does not recreate the missing facility or invent its deletion history.

### 7. Tests performed and debugging
- 127 targeted Django tests passed in 18.941 seconds, covering facility configuration/forms/mobile/archive/Services/RBAC, existing activity APIs and User Monitoring. System check found no issues. Log: scratch/facility-activity-widget-tests.log.
- Regression cases verify separate discount/booking/schedule/feature events, recorded actor and System fallback, safe output keys, five-entry limit, preserved missing-target history, Services exclusion, View All permissions/module filter, no history mutation and empty-state text.
- Four physical Chrome cases passed at 1440/768/390/320px, including actual actor/type/date rows, at least three distinct icons, empty and populated states, current forms/filter/table behaviors and safe live update rendering. Browser saves are intercepted; example responses come from isolated Django test records. Log: scratch/facility-activity-widget-browser.log.
- Six Services/Service Requests cases passed at 1440/768/375px. Log: scratch/facility-activity-widget-services-browser.log.
- Migration dry-run reported No changes detected. Scoped diff checks passed. The populated desktop widget and phone empty state were visually reviewed.

Debugging: a verification lookup of the old Covered Court ID failed because that Facility row was no longer present. A read-only audit inspection confirmed a real existing reactivation record. This exposed the previous live-ID-only filter's history omission; the regression test now proves a missing target does not erase its audit summary and an explicit service record cannot leak in. During browser QA, an archive modal overlay obscured an empty-state screenshot. The overlay remained after the intercepted request reported success, so timing alone was not a confirmed cause. The harness isolates the empty-widget markup from unrelated overlays for visual review; no application modal implementation was changed. Phone inspection also found inherited ellipsis hid parts of long messages and performer names; the scoped widget CSS now wraps both in full.

Manual test steps:
1. Ctrl+F5 on Facilities. Confirm compact action-specific icons and Type â€¢ Performer below each real message.
2. Verify the date/time matches the stored action and the widget never exceeds five rows. Check the phone layout puts the time below the message/type.
3. Make an intended valid change only: status, discount, pricing, schedule or booking configuration. Save and reload; confirm a real corresponding event and performer. Unchanged/invalid saves must not produce fake success entries.
4. As Super Admin, open View All Activity. Confirm the existing User Monitoring Facilities Activity Log and filtered module values; change its period and confirm Facilities remains selected. Clear Filters returns to the existing general monitoring view.
5. As Facilities Admin, confirm the widget still works and a forbidden monitoring link is not shown; direct monitoring access remains governed by existing RBAC.
6. In an isolated test database with no facility events, confirm the single empty-state line. Do not clear production audit records to test emptiness.
7. Open Services/Bookings/Calendar and confirm their activities are not mixed into this compact widget.

Commands: refresh with Ctrl+F5; restart Django only if development auto-reload is off. No migrate command is needed. From backend/core, focused verification is venv/Scripts/python.exe manage.py test api.test_facility_rental_configuration accounts.test_activity_api accounts.test_monitoring --keepdb --noinput.

### 8. Remaining limitations and learning practice
The summary depends on actual existing audit records. It does not infer old actions from updated_at or fabricate history for missing logs. Direct database edits outside the existing write hooks do not automatically become events. Legacy physical events rely on their established module/action-code provenance; explicit classification is stored for new writes. Detailed View All history retains the monitoring page's current date filter, so older events may require changing the period.

Safe practice: trace performed_by from the recorded full_name through facility_activity_row into the template and addFacilityAuditActivity. Then inspect EVENTS and identify the key for a discount-only change. Add an isolated test that changes only requires_pre_use_inspection and predicts facility_booking_config_updated; run the test class and verify its actor and safe keys. Do not insert fake production events to populate the widget. To debug an absent entry, inspect module/result/event code/scope and the central date filter before changing data or permissions.

## Admin-assisted reservations and structured facility blocks â€” 2026-10-13

This section implements attachment c81db6b4-3c9a-4c7f-a976-f41ead268523 and the explicit request to remove the secondary Facilities activity empty-state sentence. It supersedes the old generic Add Reservation / Upload Schedule behavior. It does not change the Services workflow.

### 1. Cause / reason

Confirmed from the old code: the admin reservation endpoint saved total_amount=0, free-text Reserved By and generic date/time fields. It checked overlapping bookings but did not enforce operating hours, capacity, pricing or configured approval requirements. The Upload Image control was never included in its request, so it did not persist an attachment. Blocks were represented by prefixed Booking.purpose values and were counted as customer bookings by some analytics queries. On phones, the long header breadcrumb pushed the notification/profile controls outside the viewport; responsive browser inspection confirmed this cause.

The fix reuses Booking, Facility, Room, FacilityPayment, FacilityBookingRequest, AccountActivity and existing permissions. No separate reservation, calendar, schedule-status or availability model was added. Existing schedule Booking records are retained; no duplicate occurrences or historical backfill are inserted.

### 2. Exact files changed, current lines and anchors

Lines are approximate navigation points in the current files. Search the anchor if later edits shift them.

| File | Line | Nearby anchor | Change / purpose |
| --- | ---: | --- | --- |
| backend/core/modules/facilities/admin_booking_views.py | 26 | access | New protected API transport and action-specific RBAC. |
| Same file | 63 | options / clients | Real configured form/rooms and bounded active-client search, including full names. |
| Same file | 99 | preview / create | Read-only quote preview and transactional core Booking creation. |
| Same file | 154 | save_schedule | Validate, conflict-check and save a single block plus JSON recurrence. |
| Same file | 190 | schedules / calendar | Existing block history and bounded Calendar aggregation endpoint. |
| Same file | 216 | schedule_update / attachment | Edit/cancel without deleting history; private attachment download. |
| backend/core/modules/facilities/services/admin_reservations.py | 34 | client_details | Existing account or walk-in details, contact/email/purpose validation. |
| Same file | 59 | reservation_quote | Slot/stay validation, room assignment and actual itemized pricing. |
| backend/core/modules/facilities/services/schedules.py | 18 | schedule_blocks_q | One classification predicate reused by customer-booking queries. |
| Same file | 34 | schedule_days | Expand recurrence for display/checking; no occurrence writes. |
| Same file | 48 | validate_schedule | Allowed block types, ranges, weekly days, all-day and Other validation. |
| Same file | 77 | validated_attachment | Bounded private image/PDF reference stored in existing JSON. |
| backend/core/modules/facilities/services/mobile_booking.py | 33 | conflicting_bookings | Shared legacy/new/recurring/stay/room overlap query. |
| Same file | 51 | slot_status | Operating periods also enforced before an admin quote. |
| backend/core/modules/facilities/services/rental_configuration.py | 239 | slot_base_amount | Reuse hourly/base-duration/fixed calculations; retain existing mobile adjustment guards. |
| backend/core/modules/facilities/services/activity.py | 21 | facility_block_added | Reuse actual facility audit summary for add/update/cancel events. |
| backend/core/api/models.py | 578 | FacilityBookingRequest | Clarify docstring only: existing sidecar now also holds admin origin/schedule metadata. |
| backend/core/api/views.py | 1626 | _serialize_booking_event | Public display fields, source, quote, stay range and protected attachment link. |
| Same file | 1672 | bookings_create | Existing URL delegates to the new protected transport. |
| backend/core/core/urls.py | 196 | admin_booking_preview | Add options/client/preview/block/attachment/month-calendar routes. |
| backend/core/accounts/views.py | 842 | _booking_display_fields | Recognize additional block prefixes without rewriting old data. |
| Same file | 869 | _bookings_calendar_events | Aggregate bookings and expanded block dates from saved records. |
| Same file | 1126 | _booking_request_rows | Keep Room/Unit; customer table excludes blocks and includes source/quote/stay range in details. |
| Same file | 1180 | admin_bookings_page | Supply schedule permission for action/form visibility. |
| backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html | 146 | Manage Facility Schedule | Rename action, keep eleven columns and include shared form partial; version changed assets. |
| backend/core/modules/facilities/templates/facilities/partials/booking_forms.html | 2 | bkReservationModal | New conditional client, slot/stay, room, discount/fee and quote fields in the existing modal style. |
| Same file | 43 | bkUploadModal | Structured schedule form, history, edit/cancel, optional attachment. |
| backend/static/components/js/admin_booking_forms.js | 72 | bkResFacility change | Load actual configuration and disclose only relevant controls. |
| Same file | 112 | reservationData / bkCheckAvailability | Read inputs, preview on server, invalidate stale quotes and submit actual fields. |
| Same file | 146 | loadBlocks | Render actual history and edit/cancel/save actions. |
| backend/static/components/js/admin_bookings.js | 66 | loadCalendarMonth | Fetch the displayed month; keep existing Calendar and details rendering. |
| Same file | 153 | openModal / closeModal | Keyboard focus restoration and background-scroll containment. Remove obsolete creation/upload helpers. |
| backend/static/components/css/admin_booking.css | 1808 | bk-admin-form-grid | Existing compact two-column desktop forms, single-column phones, restrained quote rows. |
| Same file | 1836 | campushub-bookings-page | Scoped phone header wrapping and contained table scrolling. |
| backend/core/modules/reports/dashboard_bookings.py | 25 | upcoming_reservations | Shared block exclusion in upcoming/ranking/overview queries. |
| backend/core/modules/reports/dashboard_periods.py | 185 | bookings aggregate | Do not count facility blocks as submitted customer bookings. |
| backend/core/modules/reports/dashboard_utilization.py | 90 | schedule_days | Recurring blocks reduce usable hours/room-nights without becoming usage. |
| backend/core/modules/reports/views.py | 335 | exclude(schedule_blocks_q()) | Reuse classification in booking totals/history across existing dashboards. |
| backend/core/modules/reports/reporting.py | 270 | Booking.objects.exclude | Customer booking reports exclude schedule blocks. |
| backend/core/modules/facilities/templates/facilities/pages/admin_facility.html | 288 | facility-activity-empty | Remove only the requested secondary sentence; keep the main message and Services empty state. |
| backend/core/modules/facilities/test_admin_reservations.py | 22 | AdminReservationTests | Isolated workflow/regression tests and optional real test-rendered browser fixtures. |
| backend/core/api/test_mobile_facility_booking.py | 119 | Academic class | Existing collision test supplies the newly required block description. |
| backend/core/modules/facilities/test_service_navigation.py | 101 | test_service_cannot_be_created_as_normal_reservation | Update physical success fixture to satisfy actual future booking/client rules; service rejection retained. |
| backend/core/api/test_facility_rental_configuration.py | 411 | assertNotContains | Existing empty-state assertion now verifies sentence removal. |
| scratch/admin-reservations/check.cjs | 1 | Real Django test-rendered pages | Isolated Chrome checks, intercept every request, no production saves. |
| scratch/facility-rental-config/check.cjs | 250 | facility-activity-empty span | Existing browser expectation now checks that the secondary span is absent. |
| docs/facility-configuration.md | This section | Admin-assisted reservations | Explanation, debugging, data flow, checks and learning practice. |
| CAMPUSHUB_CONTEXT.md | Final entry | Admin-assisted reservations | Remember accepted behavior and remaining limits. |

### 3. Changes made / final UI

Add Reservation remains a manual client booking action. It begins with Facility and Reserved For / Client, offers active CampusHub client search (name/student ID/email/username) or a walk-in without creating an account, and loads the selected facility's actual form label. Slot fields and room/stay fields are distinct. Room choices come only from real Room rows. Guests/adults/children must agree; shared rate explicitly means occupants in the selected same room.

Manage Facility Schedule replaces Upload Schedule. It shows real existing blocks and allows New Block, Edit and Cancel Block. Supported new types are Class / Academic Schedule, Official Campus Use, Maintenance, Administrative Hold / Unavailable and Other. Other requires specification. Reservation and Assessment are not selectable new block types; legacy records remain readable and continue blocking where appropriate. Services is not added to the physical selector.

Single-date and date-range blocks support daily periods or weekly selected weekdays, with a maximum one-year range. An all-day block uses actual full-day boundaries. Supporting Attachment is optional; PNG/JPEG/WebP/PDF up to 1 MB is accepted and checked by the backend. Its bytes live in the existing private JSON sidecar and download requires schedule permission. No public media file or unprotected URL is created. Uploading a reference alone, without structured dates, cannot create a block.

The eleven existing booking columns remain, including Room/Unit. Booking source and quote breakdown are in Details rather than an extra column. Current facility empty-state text is only No recent facility activity.

### 4. Functions, inputs/outputs and data flow

`client_details(data)` reads a selected CampusHubUser or walk-in input. It returns `(user_or_none, validated_details)`. A walk-in uses the existing nullable Booking.user and does not insert a new user. Recorded client details are kept in FacilityBookingRequest.details.

`reservation_quote(facility, data)` reads saved Facility pricing/workflow, actual Room data and the shared availability functions. It returns `(booking_field_values, itemized_quote)` and performs no writes. Slot requests use configured slots or valid sub-periods inside operating hours where no fixed slots are saved. They must satisfy the existing duration rules; explicit saved slots retain their established semantics. Stays use real room assignments, positive nights and guest capacity. The selected room's availability is checked without treating another room's booking as whole-facility occupancy. Facility-wide blocks still prevent every room.

`slot_base_amount` remains the common hourly/base-duration/fixed calculator. Admin quoting opts into handling configured adjustments separately; the mobile quote's existing safe guards remain. Other supported formulas use saved Facility.rate and price_type:

- Hourly: rate x actual hours.
- Base duration: saved base rate + max(hours - base_duration, 0) x saved additional-hour rate.
- Fixed/session: saved rate once.
- Per day: saved rate x stay nights (or one selected slot date).
- Per night: saved rate x nights.
- Per person/night: selected individual/shared rate x guests x nights.
- Per person: saved rate x guests.
- Discount: selected saved active rule applied only to its supported rental/base/additional/individual/shared scope. Explicit verified eligibility is required. No automatically inferred student/family discount.
- Fees: saved active fee amount x applicable hours/days/nights/guests/booking or explicitly selected item quantities. Custom bases and incompatible configurations fail safely.
- Deposit: saved fixed amount, or configured percent of net rental. It is separate from rental/fees and is not discounted as an unrelated charge.
- Booking total: net rental + applicable fees + refundable deposit.

`preview` validates client + availability + pricing and returns the quote without saving. Any form change invalidates the displayed quote; stale async responses cannot re-enable Save. `create` locks the Facility row inside transaction.atomic, repeats all checks, compares the submitted quote and writes one Booking plus its existing JSON sidecar and actual audit event. All admin/mobile creates lock the same Facility, preventing parallel overlapping accepted submissions. A live concurrent two-client stress test was not run; this locking design is covered by conflict-after-preview tests.

`requires_approval=True` (also the legacy default) creates Pending. Explicit configured False creates Approved. Submitted arbitrary status/total fields do not override this. Pending continues to hold capacity under the existing mobile workflow; Rejected/Cancelled release it. No new Confirmed status is invented.

`validate_schedule(data)` validates authoritative dates/times and recurrence. `schedule_days(booking, first, last)` yields matching dates, creating no database records. `save_schedule` checks overlaps under the same Facility lock and saves one prefixed Booking plus `{source: 'schedule', schedule: ...}` JSON. Edit keeps the same ID; Cancel sets the existing Cancelled status. Cancelled blocks remain in history. Unchanged saves/idempotent cancellations do not add fictitious audit events.

`conflicting_bookings` handles legacy one-day blocks, new recurring blocks, ordinary reservations and room stays. It returns a QuerySet, allowing existing `.exists()` checks in mobile code and safe exclusions during block editing. The mobile availability, quote and final submit endpoints all use it; Flutter already requests availability from Django. No second Flutter availability engine is introduced.

`_bookings_calendar_events(first, last)` aggregates the saved records. Weekly and multi-day events are expanded only for display. The month endpoint limits requested ranges to 62 days; the client requests a new month on navigation. Calendar displays reservations plus academic/official/maintenance/hold/Other blocks. Rejected/Cancelled records do not block or display as active calendar events. The initial page payload covers the current month onward for the next year; navigating older/later months requests their real data.

`schedule_blocks_q()` prevents actual schedule blocks from inflating customer booking totals, rankings, upcoming reservations and exported booking histories. Legacy Assessment records for a Service are not misclassified as physical blocks. Utilization includes recurring block dates in its denominator exclusions, without counting them as usage; legacy maintenance stay dates still work.

Real schedule changes reuse log_account_activity and the existing facility summary. Reservation creation logs in Facility Bookings, keeping it separate from facility-management events. Existing payment records, receipt processing, images, Facilities archive/edit/reactivate, Services and RBAC stores are not replaced.

Annotated example from the isolated test fixture (not seeded into production):

```python
# Saved test facility: PHP 500/hour. Actual requested duration: four hours.
fields, quote = reservation_quote(saved_facility, request_data)
# fields carries date/start/end, or the selected room/stay dates.
# quote['total_amount'] is '2000.00' for this configuration without adjustments.
# Preview only returns this result. Final create repeats validation under a lock.
```

### 5. Backend / API behavior and commands

Existing create route: `POST /api/bookings/create/`.
New protected routes: `GET /api/bookings/clients/?q=...`, `GET /api/bookings/facilities/<id>/options/`, `POST /api/bookings/preview/`, `GET /api/facility-schedules/`, `POST /api/facility-schedules/<id>/update/`, `GET /api/facility-schedules/<id>/attachment/`, `GET /api/facility-calendar/?start=YYYY-MM-DD&end=YYYY-MM-DD`.

Reservation/client/quote actions require existing admin authority and can_book_facilities. Normal user booking capability alone cannot search clients or use these admin APIs. Suspended/inactive accounts are refused through the existing admin-access helper. Block management/download requires can_manage_schedules. Calendar data requires schedule or booking-view access. UI visibility mirrors permissions, but all APIs enforce permissions independently. POSTs retain Django session CSRF validation. Invalid/conflicting input returns safe human messages (400 or schedule conflict 409); there is no silent admin override. Existing bearer-authenticated mobile endpoints remain compatible.

Refresh Bookings/Calendar/Facilities with Ctrl+F5. Restart Django only if auto-reload is disabled. No migrate command is required for these changes.

### 6. Database / migration impact

No schema migration, duplicate model, room creation, seed, historical rewrite, facility deletion or production booking/schedule write was performed. A read-only check confirmed the existing campushub_facility_booking_request table is present. On future authorized saves, JSON details use existing source/quote/schedule/attachment keys alongside core Booking data. Model changes are only a docstring. Supporting attachments are deliberately capped and private; a separate scalable document store would need its own scoped feature if volume grows.

### 7. Verification, manual checks and debugging

Final verification: 189 targeted Django tests passed in 44.676 seconds (booking/mobile/Services, facility form/configuration, periods, overview, rankings, upcoming, utilization and revenue). After the final admin-access guard was strengthened, all 20 admin-reservation tests passed in 1.012 seconds, including refusal of client search/preview/create for ordinary users who only have the normal booking capability. Headless Chrome passed the two forms at 1440, 768, 390 and 320 pixels (eight rendered scenes), with every request intercepted and no live writes; screenshots were inspected. The existing Facilities form/widget browser case also passed at 390 pixels and confirms the removed secondary empty-state span. JavaScript syntax checks, Django system checks, makemigrations --check --dry-run (No changes detected) and scoped git diff --check completed cleanly. A real Android phone session and simultaneous-user stress test were not run. Earlier 35 workflow tests passed; the first wider run found a legacy maintenance-room-night regression, now fixed by preserving check-in/out handling before recurrence handling. An unrelated existing reports test expects Marketplace Admin monitoring to return 403, while current support-scoped monitoring returns 200. Its old assertion was left unchanged; this booking task does not alter monitoring access.

Manual tests (use intended real changes or an isolated test database):
1. Open Facilities > Bookings with appropriate permissions. Verify Add Reservation and Manage Facility Schedule, and the retained eleven table columns.
2. Select a saved slot facility; search/select a real client. Check the form label, contact details, participant count and configured slots. Check Availability, review the itemized total, then deliberately change a field: Save must become disabled until preview is repeated.
3. Attempt an outside-hours request, over-capacity group or closed/archived facility. Confirm no booking is inserted.
4. Save an intended valid reservation. Confirm one core Booking, actual saved quote, correct requester/origin, approval policy and audit event. It should be visible to the selected user's existing mobile booking list where supported.
5. For a configured accommodation with real rooms, select room A and a stay range. A conflicting room A stay must fail; an available room B can succeed. No rooms configured must display no invented choices and refuse an unassigned room.
6. Add a weekly academic block with a date range and selected weekdays. Check a later repeated date in mobile availability and Calendar; confirm one block record, not one record per occurrence. Non-selected weekdays/expired dates remain free when no other conflicts apply.
7. Attach an allowed file as reference. Confirm authenticated download and that dates/times alone determine the blocked periods. Invalid/oversized attachments or missing structured dates must not save.
8. Edit or cancel a block. Confirm changes affect Calendar/mobile availability after refresh and history remains. Re-save unchanged fields or repeat cancellation: no extra action event.
9. Confirm Reservation and Assessment are absent from new block types, Services cannot be reserved through the physical form, and unprivileged users cannot call the APIs directly.
10. Verify Most Booked, Upcoming, Booking Overview and booking report counts exclude blocks; utilization deducts real recurring blocked capacity. Existing payments/revenue remain based on the established recorded-payment logic.
11. In an empty isolated facility-activity fixture, verify only No recent facility activity. appears.

Debugging: inspect Network first. A 403 on POST can mean CSRF/access failure; do not disable CSRF to fix it. A 400 may indicate missing client contact, invalid dates/counts, unsafe pricing or no configured rooms. A 409 means a schedule overlap; change the period rather than bypass validation. If mobile reports class/maintenance/reserved, inspect the matching actual Booking and its sidecar recurrence. If Calendar seems stale, refresh or navigate the month to request current server events. If an old record has no sidecar source, Details honestly shows Not recorded rather than guessing Admin/Mobile. Custom pricing, custom fees/discount scopes and legacy paid equipment need configuration/approved quoting rather than arbitrary totals.

### 8. Remaining limitations and safe practice

Daily/Custom reservation processing remains unavailable until its request process is configured; the form does not silently invent a workflow or price. Room stays require actual Room rows; no room editor or automatic room generation is added. The current Flutter accommodation screen still uses the existing contact-admin process; this work improves manual accommodation and shares backend conflict checks, but does not build a new mobile stay form. Configured check-in/out times are displayed and kept as metadata; arbitrary arrival/departure-time overrides are not introduced. No overnight time-slot, recurrence exception, bulk schedule import, payment collection/deposit-refund ledger, new approval interface or permission override is created. Custom bases fail safely. This preserves existing boundaries instead of pretending unsupported pricing is automatic.

Safe learning exercise: in an isolated test database, trace one preview request from reservationData -> preview -> client_details / reservation_quote -> slot_status / conflicting_bookings -> itemized response. Change only the test fixture's hourly rate and predict the four-hour result. Run `venv/Scripts/python.exe manage.py test modules.facilities.test_admin_reservations.AdminReservationTests.test_manual_quote_and_core_record_reuse --keepdb --noinput` from backend/core and check the expected result; restore the fixture afterward. Then trace a recurring block through schedule_days and Calendar and verify Booking.objects.count remains one for its occurrences. Never seed or clear production records to practice.


Reproducible focused suite (PowerShell, backend/core):

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_admin_reservations api.test_mobile_facility_booking modules.facilities.test_service_navigation api.test_facility_rental_configuration api.test_facility_form_controls modules.reports.test_dashboard_periods modules.reports.test_dashboard_bookings modules.reports.test_most_booked_facilities modules.reports.test_upcoming_reservations modules.reports.test_dashboard_utilization modules.reports.test_facility_revenue --keepdb --noinput
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

The earlier 203-test broader run also executed modules.reports.tests. Its remaining unrelated failing assertion is `MarketplaceAnalyticsTests.test_marketplace_admin_cannot_open_user_monitoring_even_if_permission_is_added` at modules/reports/tests.py:413. It expects 403; current accounts/views.py:1235 explicitly permits scoped Marketplace Admin monitoring, returning 200. Booking edits do not modify that function. Do not reinterpret this as a booking failure or change permissions merely to satisfy an outdated expectation; reconcile that test with the separately authorized monitoring workflow.

## Automatic Add Reservation flow â€” 2026-10-13

This section implements attachment 997facc3-be85-4ec2-8dbd-d35860dde1d6 and supersedes the manual Check Availability step in the preceding guide. Use this section for the current reservation modal.

### 1. Cause / reason

Confirmed causes: the previous modal depended on clicking Check Availability, used separate search and client-selection controls, combined availability and price output, and immediately reloaded after save. That required extra steps and hid the success/details action. It also made schedule-only checks wait for client information even though a client name is not necessary to detect a blocked time.

The existing CampusHubUser model has first/last name, identifiers, email and contact_number, but no organization or address columns. Therefore name/contact/email are filled from the selected real account; organization remains editable and blank when no stored value exists. No organization is guessed from a Program or past booking. Walk-in address is optional by default; an actual saved workflow_config.requires_client_address=True requirement is enforced when present. The existing facility form has no address-required editor control, so this change does not silently impose an institutional rule or add a duplicate profile field.

### 2. Exact changed files, current lines and anchors

| File | Approximate line | Anchor | Change |
| --- | ---: | --- | --- |
| backend/core/modules/facilities/templates/facilities/partials/booking_forms.html | 2 | bkReservationModal | Wider existing-style form with Facility, Client Information, Reservation Schedule and Booking Information sections. |
| Same file | 15 | Client Type / Search Client | Replace Reserved For / Client and two controls with one native searchable autocomplete plus an internal selected-account ID. |
| Same file | 27 | Reservation Schedule | Slot/stay-specific fields, contextual Purpose/Participants/Guests labels, actual configured times/rooms only. |
| Same file | 58 | bkQuoteResult / bkCostSummary | Separate automatic availability and six-row calculated summary; footer contains only Cancel and Save Reservation. |
| backend/static/components/js/admin_booking_forms.js | 40 | invalidate | Disable Save, hide obsolete cost, abort old requests and debounce automatic re-checking. |
| Same file | 53 | clientMode / selectClient | Toggle walk-in/profile fields and fill actual name/email/contact; clear the previous person's details on a switch. |
| Same file | 91 | bkResFacility change | Load real configuration, conditional address/times/rooms and saved pricing/fee/discount controls. |
| Same file | 152 | scheduleComplete / requiredFieldsComplete | Schedule readiness is separate from final client/form readiness. |
| Same file | 166 | checkAutomatically | Call existing preview route automatically; ignore late responses, display a real availability result, render calculated costs only for valid complete input. |
| Same file | 187 | submit handler | Final server save, prevent repeated submissions, update table and show success/details without page reload. |
| backend/core/modules/facilities/services/admin_reservations.py | 17 | ReservationUnavailable | Distinguish schedule/capacity failure from incomplete client/pricing configuration. |
| Same file | 38 | client_details | Validate explicit client type, optional address/notes, and a saved address requirement; never create a user. |
| Same file | 74 | reservation_schedule | Extract existing slot/stay/status/capacity/conflict checks for schedule-only preview and the quote/save flow. |
| Same file | 146 | reservation_quote | Reuse the existing pricing calculations and schedule helper; add rental_total and normalized guest counts to the calculated result. |
| backend/core/modules/facilities/services/mobile_booking.py | 88 | conflict_description | Describe an already-found conflict with a safe type/time message; no IDs/client details or second conflict query engine. |
| backend/core/modules/facilities/admin_booking_views.py | 84 | clients | Return real autocomplete data; organization is honestly empty because the user model lacks that field. |
| Same file | 104 | preview | availability_only gives a read-only schedule result; complete preview validates client and price, separating price errors from schedule availability. |
| Same file | 127 | create | Retain final Facility lock/revalidation, real total, Pending/Approved configuration, existing Booking/sidecar/audit; return actual room display for table update. |
| Same file | 177 | booking_slip | New protected read-only saved booking form, using recorded client/room/schedule/quote and confirmed payments. |
| backend/static/components/js/admin_bookings.js | 378 | bkBookingSlipLink | Link Details to its saved form. |
| Same file | 391 | campushub:reservation-created / campushub:booking-details | Reuse existing table/details renderers after successful save. |
| backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html | 84 | bkReservationSuccess | Small success row with View Booking Details, not a new large card. |
| Same file | 179 | bkBookingSlipLink | View Booking Form navigation; updated CSS/JS version tokens. |
| backend/core/modules/facilities/templates/facilities/pages/booking_slip.html | 1 | bk-saved-slip | Prefilled, printable configured booking slip; no second form entry or new transaction records. |
| backend/core/modules/facilities/mobile_views.py | 47 | _serialize / check_in_date | Additive stay dates and correct date fallback for linked manual accommodation history; slot dates remain unchanged. |
| backend/core/core/urls.py | 197 | admin_booking_slip | Register /admin-bookings/<id>/slip/; existing create/preview URLs remain. |
| backend/static/components/css/admin_booking.css | 1846 | bk-reservation-dialog | 900px maximum desktop modal, existing internal scroll, responsive form/results, compact success row and print-only slip styles. |
| Same file | 1869 | sticky modal footer | Keep only the two reservation actions visible while scrolling. |
| backend/core/modules/facilities/test_admin_reservations.py | 68 | test_schedule_preview_without_client | Schedule-only/no-write and final-save bypass prevention. |
| Same file | 82 | test_pricing_failure_keeps_schedule_availability_honest | Free schedule with an unsupported price cannot enable Save or falsely claim a conflict. |
| Same file | 91 | test_client_type_address_and_notes | Type validation, required-address configuration and actual saved notes/address. |
| Same file | 102 | test_saved_slip_is_prefilled_and_protected | Saved label/data, authorized readers, failed/paid payment balances and unauthenticated refusal. |
| Same file | 224 | test_stay_preview_and_optional_adult_count | Room-specific schedule-only check and normalized adults/children. |
| Same file | 313 | test_export_browser_fixtures | Isolated real Django HTML/JSON fixtures for populated/empty room configurations and saved slip. |
| scratch/admin-reservations/check.cjs | 1 | Real Django test-rendered pages | Updated browser checks for automatic checks, native autocomplete, late responses, errors, save/details/slip and responsive rendering. All requests intercepted. |
| docs/facility-configuration.md | This section | Automatic Add Reservation flow | Current behavior, functions/data flow, causes, verification, troubleshooting and safe learning practice. |
| CAMPUSHUB_CONTEXT.md | Last entry | Automatic Add Reservation | Preserve accepted scope and limitations for subsequent work. |

### 3. Changes made / required attachment report

1. The changed folders/files and current anchors are listed above; existing unrelated code was preserved.
2. The same core Booking model and FacilityBookingRequest JSON sidecar are reused; no ManualReservation model exists.
3. Existing configured_slots, slot_status and conflicting_bookings remain authoritative for slots, legacy/recurring blocks and actual room stays. reservation_schedule extracts those existing checks rather than creating another engine.
4. Check Availability is removed. Only Cancel and Save Reservation remain in the reservation footer; schedule-management actions are unchanged.
5. Automatic checks run after a 300ms pause when the selected mode's real schedule is complete. A schedule can be checked without client/counts; no quote or record is created at that stage.
6. Client Type options are CampusHub User and Walk-in / External Client. They are separate from the selected person's identity.
7. Search Client is one native input/datalist autocomplete. The selected ID is internal, validated by Django and never used as visible technical text. Stored full name/contact/email fill automatically; missing contact can be safely entered for the reservation.
8. Walk-in client details reuse nullable Booking.user and existing JSON details. They do not insert a CampusHub user. Address and notes are stored only as reservation details, not profile master data.
9. Slot mode shows Date, Start/End, Participants and Purpose; fixed configured slots also expose their real slot selector. Changing dates clears old times before new options load.
10. Stay mode shows Check-in/out dates, actual saved check-in/out times when configured, Guests, Adults/Children and Purpose of Stay. Room/Unit appears only for real configured Room rows. No rooms means a clear configuration message and Save remains disabled; no whole-facility accommodation stock is invented.
11. Reservation Cost Summary shows Base Rental, Discount, Additional Fees, Rental Total, Damage Deposit and Amount Due. Rental Total is net rental plus fees; Amount Due includes the separate refundable deposit.
12. Saved pricing, explicitly verified active discounts, fee quantities and deposit calculation are reused. No arbitrary total input, guessed eligibility or new fee definitions are introduced. Shared person/night rate still requires the configured number of guests in the same selected room.
13. Requires Approval still produces Pending unless the facility explicitly disables approval, in which case it uses existing Approved. No new status names or silent overrides are added.
14. Booking source remains the existing details.source=admin; linked accounts see the existing user booking history. Walk-ins have no fabricated account/history owner.
15. Backend final save still locks the Facility in transaction.atomic, validates client/fields/capacity/availability/pricing again, verifies the submitted quote and writes actual audit records. availability_only never bypasses these checks on create.
16. After success, the actual API record is inserted into the existing table, and a small success message offers View Booking Details. Details includes View Booking Form. Calendar and availability continue reading the saved Booking, not duplicate rows.
17. The saved slip uses the quote's recorded form label, with the current configured label only as a fallback for older records. Court/hall use Facilities and Spaces Rental Booking Slip; accommodation uses Room Accommodation Booking Slip through existing FORM_TYPES/FORM_DEFAULTS. No OR or Job Order input is added to Add Reservation.
18. The saved form is protected by existing admin authority and booking read/manage/approve/payment/book permissions. It contains no editable inputs. Its current Amount Due subtracts only recorded paid FacilityPayment amounts and safely clamps overpayment to zero; failed/unpaid entries do not reduce the balance. No receipt/payment/refund is written by this view.
19. No migration, duplicated model, production reservation seed, automatic room generation or live record rewrite is involved.
20. Commands and manual verification are below; no migrate command is needed.

### 4. Functions, inputs/outputs and data flow

`reservationData()` reads the currently selected client type/ID and visible schedule/contact/count/fee fields. It returns a request object without locally computing any rental amount. `invalidate()` clears the accepted quote and Save state immediately, increments a revision, aborts the old preview and schedules another check. `scheduleComplete()` tests mode-specific schedule readiness; `requiredFieldsComplete()` separately checks browser validity and requires a selected real CampusHub account ID when Client Type is CampusHub User.

`checkAutomatically()` sends the existing preview endpoint `availability_only=True` while client information is incomplete. Django returns only `{available: True}` on a valid free schedule; there is no guessed price. Once complete, it requests a fully validated quote. The revision prevents old results from restoring Save after a time/room/client/quantity change, even if a request could not be aborted. A price/client failure can explicitly report that the schedule is free while keeping costs hidden and Save disabled. A real schedule failure returns available=False and a safe reason. Network failures also leave Save disabled; changing a field/reopening the form initiates another check.

`reservation_schedule(facility, data, check_capacity=...)` takes the actual saved facility plus requested schedule. It returns Booking field values and a context (room, duration/nights and validated counts/form). A schedule-only preview does not pretend unknown participants are zero or quote an amount. `reservation_quote` consumes the same helper, then the previous saved-pricing formulas. `client_details` enforces an explicit client type when supplied while retaining existing callers' compatibility; selected users must still be active and not suspended. Blank optional adult count is derived from entered Guests minus Children, with at least one adult required; the normalized real counts are retained on save.

`create` is the final authority. Its existing lock/recheck makes a successful preview advisory, not a guarantee that remains valid after another booking is inserted. The UI never repeats a POST automatically. Successful response data is passed to the existing table and details renderer through local DOM events. There is one Booking, one sidecar and one actual creation audit event.

`booking_slip` reads that record and its JSON metadata, real assigned room and paid transaction sum. It returns a protected HTML view using the saved official form label and values; its Print Booking Form button opens the browser's normal print dialog. The view does not create a second booking/form record, collect payment, approve the booking, or claim that an institutional signed form has been completed.

Annotated example (isolated test fixture, not a production seed):

```python
# Schedule complete, client not selected yet: no quote and no writes.
reservation_schedule(saved_facility, schedule_data, check_capacity=False)
# The API returns {"available": True} only when these real rules pass.

# Client, counts and requested configuration are now complete.
fields, quote = reservation_quote(saved_facility, complete_data)
# rental_total = rental_amount + fee_amount, calculated by Django.
# total_amount = rental_total + separately calculated deposit_amount.
# Final save calls the same validation again inside its existing transaction.
```

### 5. Backend / API behavior

Existing authenticated/CSRF-protected `POST /api/bookings/preview/` supports the schedule-only flag and complete quote. No new availability engine or duplicate pricing endpoint is added. Full preview failures distinguish schedule availability from client/pricing completion. The existing create endpoint never trusts the flag, caller total/status or a stale UI quote.

The new GET route `/admin-bookings/<id>/slip/` is read-only, private/no-store and rejects schedule blocks/Services records. Existing RBAC is checked server-side, including for direct requests. The usual Calendar API, mobile availability/quote/create/cancel routes, recorded payment workflow, Services, facility archiving and dashboard analytics remain in their existing scope. Mobile history serialization adds check_in_date/check_out_date and uses the real check-in date when no slot booking_date exists; existing slot fields stay compatible. This does not introduce a new Flutter accommodation form.

### 6. Database / migration impact

No model/schema changes. Source, address, notes, normalized guests and quote data use the existing FacilityBookingRequest.details JSON. No duplicate user/address/organization columns, fake client records or seed reservations. No live database writes were made during implementation or UI review; backend fixtures are isolated test records, and browser requests are intercepted. Django migration check reports No changes detected.

### 7. Tests, manual checks and troubleshooting

Verification: 195 targeted Django tests passed in 33.045 seconds, covering admin/mobile/Services, facility configuration/form controls, dashboard periods, booking overview/rankings/upcoming, utilization and revenue. After the final slip/read-permission/payment-balance and mobile stay-date additions, all 37 admin-reservation/mobile tests passed in 1.672 seconds. Headless Chrome passed automatic reservation, schedule and saved-slip flows at 1440, 768, 390 and 320 pixels; all requests were intercepted and any save response came from an actual isolated test record. Checks include removal of the manual button, schedule-only preview, selected-profile fill, six cost rows, conflict/price states, invalidation, delayed old responses, actual save/table/details link, walk-in clearing, absent/present real rooms and printable form containment. Populated desktop, phone cost/footer and saved-form screenshots were visually inspected. JavaScript syntax, Django system checks, migration dry-run (No changes detected) and scoped diff checks passed. Prior code inspection and targeted tests confirm mobile/admin use the existing shared conflict and transaction paths. No physical Android device or live simultaneous-client stress test was run.

Manual checks:
1. Ctrl+F5 on Facilities > Bookings, then Add Reservation. Confirm Facility first, Client Type, a single Search Client autocomplete and only Cancel/Save in the footer.
2. Choose a real slot facility and complete date/time before choosing the client. Availability should appear automatically, with no cost and disabled Save. Select a matching real account, complete counts/purpose and missing contact if needed; the calculated summary should appear and Save enable.
3. Change a time, room, quantity or client rapidly. Old cost must disappear immediately, Save disable, and only the latest completed request may re-enable it. Blocked, closed, outside-hours or invalid-capacity schedules must fail.
4. Switch to Walk-in. Confirm the previous person's profile fields clear, manual name/contact become required, address is optional unless a saved facility requirement exists, and no account is created.
5. For a configured stay facility, verify actual Room choices, configured check-in/out times, Guests and Purpose of Stay. With no Room rows, the selector is hidden and no reservation can be saved. Do not create fake room records to bypass this.
6. Save an intended valid booking. Confirm persistent success, one new table record, correct pending/approval behavior and View Booking Details. Open View Booking Form and verify saved client/schedule/room/price; printing must not request the same data again. Verify existing user history and Calendar after refresh.
7. Confirm a normal user with booking capability cannot call the admin preview/client/slip APIs, and POST without CSRF fails. Check authorized readers can view their permitted saved transaction form.

Debugging: an unmatched typed name is not a selected account. Choose a suggestion; do not manually assign an ID. Empty saved contact must be filled with the actual client contact. Availability with an incomplete price means the time is free but the pricing/client configuration still needs attention; it is not permission to save. Custom quote methods/scopes remain guarded because the current project has no approved custom-quote workflow; never replace the server calculation with a typed arbitrary total. If Save remains disabled, check visible required fields and the Network preview response. A final-save conflict means another real record/configuration changed after preview; adjust/recheck rather than bypassing backend rules. Native datalist suggestion appearance varies by browser; it preserves keyboard selection without a second dropdown.

### 8. Remaining limitations and safe learning exercise

Organization/address cannot be autofilled from nonexistent user profile columns. The existing facility editor does not configure an address-required rule; default optional behavior is honest, and a real saved requires_client_address flag is supported without inventing a universal requirement. Custom/Daily workflows that lacked an approved calculable process remain guarded; existing individual/shared, fee and deposit rules are preserved. The prefilled printable form is generated from saved data; institutional signatures, document numbering, Job Orders, collection/receipt entry and deposit refunds remain separate unimplemented/previous workflows rather than fake fields in this modal. Mobile accommodation still uses its existing contact-admin process; no new Flutter stay form was added.

Safe exercise: in the isolated browser fixture, change one time after a successful quote and observe invalidate -> preview -> checkAutomatically. Predict why the old revision cannot enable Save, then verify with the existing late-response browser assertion. In the isolated Django tests, change the hourly fixture rate, predict the four-hour total, and run test_manual_quote_and_core_record_reuse. Restore the fixture and confirm the test again. Practice on tests, not by seeding or deleting production reservations.


Current commands (PowerShell from backend/core):

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_admin_reservations api.test_mobile_facility_booking --keepdb --noinput
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

To export isolated real test-rendered browser fixtures, set BOOKING_REVIEW_DIR to the project's scratch/admin-reservations directory before running the fixture-export test; then run `node scratch/admin-reservations/check.cjs` from the project root. The harness never sends live saves. No deploy, migration or database-cleanup command is required. The earlier unrelated Marketplace Admin monitoring assertion remains outside this task and was not modified; the focused suite here passes.

## Add Reservation layout and placeholders - 2026-10-13

### 1. Cause / reason

Confirmed in the template: Facility appeared both as a section legend and a field label; section legends had no bottom spacing; most text fields had no input hints; Client Type automatically selected CampusHub User. The time fields flowed as Date/Start, then End alone on the next row. These were presentation issues, not missing backend booking rules.

### 2. Exact files and current anchors

| File | Current line | Nearby code anchor | Change |
| --- | --- | --- | --- |
| `backend/core/modules/facilities/templates/facilities/partials/booking_forms.html` | 8 | First `bk-reservation-section` | Remove duplicate Facility legend; retain the associated required field label. |
| Same template | 14 | `bkClientTypeField`, `bkClientFields` | Blank required Select client type option; conditional client details; descriptive text placeholders. |
| Same template | 33 | Start Time / End Time | Keep the two time fields in their own paired grid row. |
| Same template | 48 | `bkAttendees`, `bkResPurpose`, `bkResNotes` | Participant, purpose, adult and optional note hints. |
| `backend/static/components/js/admin_booking_forms.js` | 48 | `addressControl()` | Address visibility/requirement respects a selected client type and actual configuration. |
| Same JavaScript | 54 | `clientMode()` | Reveal/enable applicable fields, restore Name/Contact requirements, clear prior selection and stale search responses, switch name hint. |
| Same JavaScript | 104 | Empty `bkFormLabel` / `bkScheduleHint` | Restore initial hints when clearing a facility; switch Participants/Purpose hints to Guests/Purpose of Stay for room mode at lines 128-130. |
| `backend/static/components/css/admin_booking.css` | 1848 | `.bk-reservation-section legend` | Separate headings from labels, readable 13px labels/14px inputs, navy placeholder contrast, visually disabled Save, hide empty helper/fee gaps. |
| Same stylesheet | 1858 | `.bk-reservation-results:has(...)` | Availability uses full width until a real cost summary appears. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 14, 195 | `20261013-reservation-placeholders` | Refresh stylesheet/form-controller cache versions. |
| `scratch/admin-reservations/check.cjs` | 33, 78, 89 | Client type starts / Clearing type / Clearing facility assertions | Adapt the existing isolated browser review for the explicit client choice and reset behavior. |
| `docs/facility-configuration.md` | This section | Add Reservation layout and placeholders | Implementation, debugging and learning guide. |
| `CAMPUSHUB_CONTEXT.md` | Final entry | Reservation layout and placeholders | Preserve the current form behavior for future work. |

### 3. Changes made

The order is Facility, Client Information, Reservation Schedule, Booking Information, then Availability and the existing calculated cost summary. No new visible mini-cards were added. The existing two-column grid collapses to one column below 560px. Full Name/Organization and Contact/Email remain paired on desktop; Start/End also stay paired. Search Client appears only for CampusHub User. Client details wait for an explicit client type; Walk-in reveals editable information, while existing users keep the real search/autofill workflow.

Placeholders explain what to enter without inserting sample values. Associated visible labels remain in place. Room-mode hints use Guests and Purpose of Stay. Native date/time controls keep their browser-provided format hints, because custom placeholders are not consistently supported for these input types.

### 4. How it works: functions, inputs/outputs and data flow

The template supplies empty inputs and select prompts. `clientMode()` reads the selected value (`existing`, `walkin` or blank) and changes only the form state: it reveals the appropriate groups, clears the old identity/contact fields and enables required Name/Contact validation for a selected type. `disclose(groupId, shown, required)` updates hidden/disabled flags; after enabling the client group, the controller restores the individual mandatory fields so optional email/organization do not accidentally become required. Incrementing `searchRevision` discards an in-flight autocomplete result from the previous client type.

`addressControl()` reads client type and the existing facility configuration flag; it shows an address only when applicable. The facility-change handler resets old labels/hints before fetching actual options, then adjusts guest/purpose hints for the returned booking mode. Clearing the facility restores the initial schedule instruction and hides the schedule fields.

`reservationData()` (line 158) still builds the same API request from real entered values. `requiredFieldsComplete()` (line 172) uses native `checkValidity()`, so the blank required Client Type prevents a full quote/save. `checkAutomatically()` (line 181) still checks a complete schedule without client information using availability-only preview, then obtains a real full quote once required information is complete. A placeholder is not an input value and is never sent as a name, quantity or purpose.

Annotated example:

```javascript
// Initial client type is an empty value, not a saved account selection.
disclose('bkClientFields', false); // Hidden controls are disabled too.
// After CampusHub User or Walk-in is chosen, required fields are restored.
el('bkResName').required = chosen;
el('bkResContact').required = chosen;
// A hint tells the user what to enter; it does not populate a quantity.
el('bkAttendees').placeholder = room ? 'Enter number of guests' : 'Enter number of participants';
```

This approach reuses the existing grid, disclosures and validation rather than adding another form or copying booking logic.

### 5. Backend / API behavior

No backend/API changes. Existing real facility/client lookup, availability preview, pricing, transaction locking, final validation, approval rules, Calendar/table update and saved booking form continue to use their existing endpoints. The required blank client-type prompt is a frontend choice; the existing backend already validates explicit client types on full preview/create. Schedule-only preview remains possible before choosing a client. RBAC, Services and mobile behavior are unchanged.

### 6. Database / migration impact

No model, migration, seed, production booking or facility record was changed. Browser review uses exported isolated Django test records and intercepts requests; its successful save response does not write a live booking.

### 7. Tests performed and manual verification

For this update: all 25 `modules.facilities.test_admin_reservations` tests passed (1.312 seconds); Django reported no system-check issues. `node --check backend/static/components/js/admin_booking_forms.js` passed. The existing headless Chrome review passed at 1440, 768, 390 and 320px, including explicit blank client choice, native required validation, profile selection, walk-in/blank resets, room-mode hints, facility reset, automatic preview, conflict/pricing failures, stale response protection, quote/save/table/details and saved-slip flows. Screenshots were inspected for desktop and phone spacing. Earlier larger suite results above belong to the previous implementation; they were not rerun for this presentation update.

Manual steps:

1. Refresh Bookings with Ctrl+F5, then open Add Reservation. Confirm one Facility label, Select facility and Select client type, separated headings, and a visibly disabled Save.
2. Choose a real facility and complete its schedule. Availability can check before client selection; Save remains disabled.
3. Select CampusHub User, search/select a real active account and confirm real profile autofill. Complete the required fields and verify the calculated cost summary.
4. Switch to Walk-in. Confirm the previous account identity/details clear, editable name/contact hints appear and Search Client disappears. Switching back to the blank choice hides/disables client details and invalidates Save.
5. With a configured room facility, check Guests/Purpose of Stay hints and paired check-in/out fields. Clear Facility and check that the initial schedule instruction returns.
6. Check desktop and a 320-390px viewport: labels stay visible, inputs fit, Start/End pair on desktop and stack on phones. Scroll to the footer to verify Cancel and Save remain accessible.

Troubleshooting: an old form with no Select client type usually means cached assets or an old rendered page; hard refresh and check the cache version at template lines 14/195. If fields remain hidden after a type selection, inspect the console and confirm both `bkClientFields` and the current form script are present. If Save remains disabled, check required fields, an actual matching account ID for CampusHub User and the availability/pricing result; do not remove validation to force Save.

Safe practice exercise: change only the Additional Notes placeholder at template line 55 to another short instruction. Refresh and confirm the visible label remains and the textarea value is still blank. Inspect an intercepted fixture preview to verify no placeholder sentence appears in `notes`. Restore the text and run `node scratch/admin-reservations/check.cjs`. This teaches the difference between a display hint and submitted data without creating production records.

### 8. Remaining limitations

Native date/time format hints and autocomplete popup appearance vary by browser. The full-width Availability rule uses modern CSS `:has()`; older browsers retain the previous two-column layout. Organization has no account-profile source and stays editable/blank. Existing unsupported custom pricing safeguards remain; this update does not add new reservation modes. No physical Android, live booking save or concurrency stress test was performed for this form presentation change.

## Facilities Bookings transaction workflow - 2026-10-13

This section supersedes the earlier manual-approval and discount-label behavior. It implements the request in attachment `862e657b-f817-44ca-8a7d-a7f798d6f466`. No new Booking, Facility, Payment, Calendar, Job Order or audit model was created.

### 1. Cause / reason

Confirmed inspection findings: the shared availability, room inventory, configured pricing, admin/mobile creation, schedules and printable slip already existed. Admin creation still followed the facility's requires_approval flag instead of the creator's approval permission. The table had only an eye action, an arbitrary 300-row cap without server pagination, short ambiguous status headers, and latest-payment-based status. There were no booking transaction write endpoints for approval, cashier payment, Job Order, inspection or supporting documents. The existing JSON sidecar can hold structured workflow data, so duplicating transaction tables was unnecessary. Mobile returned the entire sidecar, which would expose internal verification/documents if those new keys were added unchanged.

### 2. Exact files / current lines / anchors

| File | Approximate current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/booking_workflow.py` | 28 `save_details`, 37 `paid_summary`, 62 `allowed_actions`, 148 `transition`, 263 `public_client_details` | New helpers on existing models: state/permission checks, real payment totals, approval/Job Order/inspection/document metadata and client-safe serialization. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 28 `physical_bookings`, 39 `list_data`, 96 `detail`, 123 `update`, 169 `document_values`, 224 `pdf_response` | New protected transaction/list/document transport; atomic writes, paginated real rows, private document downloads, PDF output. |
| `backend/core/modules/facilities/admin_booking_views.py` | 104 `preview`, 156 `workflow_snapshot`, 161 `may_approve` | Authorized exact-record edit preview, permission-based manual auto-approval, recorded approver/time, actual row response and audit events. |
| `backend/core/modules/facilities/services/admin_reservations.py` | 74 `reservation_schedule`, 146 `reservation_quote`, 175 `verification_method` | Reuse pricing/availability while excluding only an authorized edited booking; validate structured discount verification. |
| `backend/core/modules/facilities/services/mobile_booking.py` | 33 `conflicting_bookings`, 53 `slot_status`, 81 `schedule_payload`, 103 `rental_quote` | Optional exact-booking exclusion for admin edit; default mobile behavior unchanged; service-based resources rejected by ordinary physical reservation pricing. |
| `backend/core/modules/facilities/mobile_views.py` | 39 `_serialize`, 77 `availability`, 137 `bookings`, 244 `slip` | Keep mobile Pending; source/workflow snapshots and real submission/cancellation audit; hide staff metadata; owned approved PDF access; physical history boundary. |
| `backend/core/accounts/views.py` | 1126 `_booking_request_rows`, 1145 `booking_requests` | First 20 real rows using shared serialization; full total for paging. |
| `backend/core/core/urls.py` | 198 `admin_booking_list`, 199 `admin_booking_update`, 202 `mobile_booking_slip`, 206 `admin_booking_detail` | Reuse existing routes and add transaction/document routes. Specific clients/options routes precede the generic booking ID route. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 109 table headings, 134 `bk-pagination`, 175 `bk-transaction-tabs` | Explicit Payment Status / Booking Status / Time-Stay, pagination, conditional tabs inside existing Details modal; asset version `20261013-booking-workflow`. |
| `backend/core/modules/facilities/templates/facilities/partials/booking_forms.html` | 57 `bkDiscountReasonField` | Eligibility Verification, real method choices, conditional Other and optional notes. |
| `backend/core/modules/facilities/templates/facilities/pages/booking_slip.html` | 36 Print button | Add authenticated Export PDF beside the existing prefilled printable form. |
| `backend/core/modules/facilities/templates/facilities/pages/booking_document.html` | 1 | New read-only printable document view using stored data, with PDF link. |
| `backend/static/components/js/admin_bookings.js` | 61 `loadBookingPage`, 406 `booking-opened`, 436 `showMoreActions` | Bounded server paging/filter requests, eye + contextual three-dot actions, real record reconciliation after writes. |
| `backend/static/components/js/admin_booking_forms.js` | 109 `loadFacility`, 168 `verificationControls`, 242 `edit-reservation` | Reuse the Add Reservation form for authorized unpaid edits; structured verification and invalidated quote/save state. |
| `backend/static/components/js/admin_booking_workflow.js` | 43 `render`, 74 `load`, 95 `editor`, 135 `submit` | New transaction tab controller, existing-record summaries and protected action forms; keyboard tab navigation, loading/retry/error states. |
| `backend/static/components/css/admin_booking.css` | 1877 `.bk-more-menu`, 1881 `.bk-transaction-tabs` | Scoped navy/gold/white actions, tabs, compact records, contained menu and responsive paging. |
| `campushub/lib/module_app/screens/facilities/facility_booking_status_screen.dart` | 228 status badge, 462 saved form label, 494 stay dates | Display real status labels and configured form title; avoid fake court times for stays. |
| `campushub/lib/module_app/widgets/facilities/booking_widgets.dart` | 79 `BookingStatusBadge` | Optional display label preserves existing status code logic. |
| `backend/core/modules/facilities/test_admin_reservations.py` | 63 approved expectation, fixture exporter near 315 | Update the superseded manual Pending expectation and export real isolated list/detail fixtures. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 20 `BookingWorkflowTests` | 17 transition/security/state/real-document/fixture cases. |
| `scratch/admin-reservations/check.cjs`, `workflow-check.cjs` | Fetch interception / four widths | Existing reservation review plus new transaction review; all writes intercepted. |
| This guide; `CAMPUSHUB_CONTEXT.md` | This section / final entry | Current behavior, debugging, test evidence and safe learning exercise. |

The original source models remain `api.models.Booking` (line 521), `FacilityBookingRequest` (578), `FacilityPayment` (592), Facility and Room. The facilities module model exports still reuse them. `settings.py`, auth token format, unrelated products/orders and sidebar were not changed.

### 3. Changes made: requested 24-point implementation report

1. Files are listed above; line numbers are approximate current locations and searchable anchors survive later edits.
2. Existing generated BK IDs and Booking records are preserved; the Job Order uses one structured `details.job_order`, not a second sellable booking or sidebar module.
3. `details.source=admin/mobile` records new origins. UI maps admin to Admin / Walk-in, mobile to Mobile App, unknown legacy origins to Not recorded. Unknown data is not fabricated or backfilled.
4. Manual reservations become Approved only when the actual authenticated admin has `accounts.can_approve_bookings`. `details.approval.by/at` records that actual person/time. Without it, manual creation stays Pending even if the facility's older requires_approval flag is false.
5. Mobile requests still start Pending, display Pending Approval and require a real authorized approve/reject transition. Payment remains separate.
6. The table keeps all eleven requested columns and real room/date/stay data. Paid totals use all actual paid records, not the newest failed/unpaid entry. Pagination is 20 rows; search/status/facility filters run on the server and cannot hide older pages behind the old 300-row cap.
7. Eye opens Details; the three-dot menu shows only state- and permission-appropriate actions. Paid/completed/cancelled/rejected records cannot be re-edited through Add Reservation. Final server checks also reject forbidden direct calls.
8. Add Reservation retains its ordered sections, real autocomplete/walk-ins, configured fees/deposit/rooms and automatic checks. Edit reuses that form, keeps the same facility and ID, preserves source/approval history and recalculates actual costs. It requires both booking management and booking creation capabilities because it reuses the protected reservation form.
9. `conflicting_bookings`, `slot_status`, `reservation_schedule` and `reservation_quote` remain the shared engine. Edit excludes only the authorized current record, never another booking. Approval revalidates the requested operating period/capacity/room and overlapping blocks.
10. Manage Facility Schedule remains separate from actual client reservations. Existing structured blocks and recurrence remain in their current storage and are excluded from client transaction lists. No duplicate schedule or Calendar rows are inserted.
11. The existing Details modal now has Overview, Booking Form, Job Order, Payment, conditionally Inspection, Documents and Activity. No SOA tab is invented for ordinary physical bookings.
12. Booking Form reuses the existing saved official-form title and data; HTML Print and generated PDF use actual values. Client-owned approved/completed bookings have a private mobile PDF endpoint. Exact approved BEU visual layout is not certified by this implementation; see limitations.
13. Job Order saves structured number/date/request/specifics/items/optional received-required times/turnaround/gender preference and actual staff names. Update preserves its number and original filled-out staff. Existing booking/client/schedule information is prefilled or read directly. `job_order_stage=request` is honored when present in real workflow configuration; otherwise creation is available after approval. There is no hard-coded court/hostel trigger or new facility editor control for that key.
14. Payment requires Approved + Unpaid, actual Cash method, full remaining amount, cashier-issued OR number and real payment date/time. Partial payments are not introduced. A payment creates an existing FacilityPayment row; caller-supplied Paid/status flags have no setter. Same-booking retries cannot duplicate payments; PostgreSQL receipt-name advisory locking also serializes cross-facility duplicate OR checks.
15. Actual paid totals plus the existing Approved code display Reserved / Confirmed. The database/mobile status remains approved for compatibility; Pending/Approved/Completed/Rejected/Cancelled codes are unchanged. No fake reserved column or redundant status field is added.
16. Inspection uses saved required-pre/post workflow flags, selected real active booking-management personnel, condition/cleanliness/damage/items/overtime/remarks/date and optional evidence. Post-use recording and completion validate the actual reservation end. Required inspections gate completion.
17. Deposit/refund decisions can be recorded after a required post-use inspection with an actual deposit. They do not change paid transactions, issue a refund or claim Refunded without a cash-refund workflow/record.
18. Documents lists only actual booking/Job Order/inspection reports, receipt attachments and manually recorded supporting documents. Files use the existing validated private JSON attachment representation, bounded to 1 MB each; no public media URL or service certificate is invented.
19. Existing AccountActivity/log_account_activity stores real submitted/manual/auto-approved/approved/rejected/updated/payment/reserved/inspection/completed/cancelled/document events. Failed writes roll back audit too. Old unlogged history remains honestly empty.
20. Calendar continues reading the same actual bookings and structured schedule sources. Updating/cancelling a booking changes its existing source; availability releases cancelled/rejected records using the existing conflict rules.
21. Server checks admin authority and the relevant existing view/book/manage/approve/payment permission. Viewing a document does not grant a write permission. Mobile PDF requires the existing bearer authentication and exact booking owner. Internal Job Orders/inspection/evidence/staff payment metadata are excluded from mobile JSON.
22. No migrations, model/schema change, seeding or production-record rewrite. The existing sidecar JSON owns the added workflow data; no duplicate payment/Job Order/audit model.
23. Existing Flutter request validation, conflict/review/submission and status-code branching remain; display labels and stay/form presentation are additive. The native View Booking Slip screen remains. Mobile PDF download API is ready, but no new in-app PDF viewer/download dependency was introduced.
24. Refresh web with Ctrl+F5; restart Django if it was not reloading new URL/view files; rebuild/restart Flutter for its display changes. Commands and verification below. No migrate or production cleanup command is required.

### 4. How it works: functions, inputs/outputs and data flow

Read flow: page -> `_booking_request_rows(request.user)` -> `physical_bookings()` -> `row_set()` -> `booking_row()`. One bounded group of actual rooms is queried for the page and payments are prefetched. `paid_summary(booking)` returns payment_status, paid_amount and remaining amount from paid FacilityPayment records. `status_label` maps Approved + fully paid to Reserved / Confirmed without changing the saved code. `allowed_actions(booking,user)` returns a list of permitted operation names; it performs no writes. The Details GET adds the existing JSON values, actual receipt history, real documents and a bounded audit history.

Write flow: action form -> CSRF/session-authenticated POST update -> existing permission check -> transaction -> Facility lock then Booking lock -> `transition()` or reused reservation edit validation -> original record/sidecar/payment write -> existing audit -> shared actual row response. The table reconciles that row and reloads the current server page. Another user changing a record invalidates stale actions at the final server check. The transaction editor preserves entered information on a failed request and shows the returned error; a retry does not silently resubmit a successful payment.

`save_details` updates the existing one-to-one sidecar, retaining its request key for retry/identity compatibility. Approval/staff snapshots use actual names/IDs/times. Job Order and inspection content are structured JSON; supporting images/PDFs are evidence only, not the source of availability or a substitute for the structured fields. `document_values()` returns escaped label/value data read from those records; `pdf_response()` uses installed ReportLab to make an A4 PDF. HTML/PDF reads do not create or approve transactions. `public_client_details()` is an allowlist that returns reservation/client costs, not the new internal administrative documents.

Annotated example:

```python
# Presentation is derived from actual payment records, not a toggle.
summary = paid_summary(booking)
# Example shape: {"payment_status": "paid", "paid_amount": "2000.00", "amount_due": "0.00"}
# These example amounts describe an isolated test record, not a production seed.
label = status_label(booking, summary)
# approved + fully paid -> "Reserved / Confirmed"; booking.status stays "approved".
actions = allowed_actions(booking, logged_in_admin)
# The API calls this again under the record lock before it accepts a write.
```

This choice avoids status/total drift, a second availability engine and a second payment or approval source of truth. JSON reuse requires structured validation and privacy filtering, which are provided at the write/read boundaries.

### 5. Backend / API behavior

Existing create/preview/client/options/schedule/Calendar routes remain. Added `GET /api/bookings/` provides paginated physical requests; `GET /api/bookings/<id>/` gives guarded transaction details; `POST /api/bookings/<id>/update/` validates an explicit supported action. Private `/documents/<kind>/` returns read-only printable HTML or `?format=pdf`, and `/attachments/<key>/` downloads only a recorded validated file. Responses are private/no-store for documents/detail. The specific `/clients/` URL remains before the generic `<id>/` pattern; that ordering was corrected during verification.

`GET /api/mobile/bookings/<id>/slip/` returns an owned approved/completed booking PDF through existing bearer authentication. The mobile date/slot/quote/create/cancel contracts and status codes remain; ordinary physical booking history/pricing now excludes service-based resources and blocks rather than treating Food Analysis/Training/Lease as ordinary physical reservations. Services remains in its existing module. No authentication engine, new JWT implementation, OR generator, payment gateway or SOA workflow was added.

### 6. Database / migration impact

No changes to models/migrations, and makemigrations --check --dry-run reported No changes detected. Only isolated test records were written during implementation. The application will write real Booking, FacilityPayment, FacilityBookingRequest JSON and AccountActivity records when an authorized user actually submits an operation. Attachments are private bounded JSON data, not new public files. PyMuPDF was installed in the existing virtual environment for QA rendering only; runtime PDF generation uses the already-declared ReportLab dependency.

### 7. Tests, manual checks and troubleshooting

Verification for this feature: 202 targeted Django tests passed, including the 17 new workflow cases and existing admin/mobile/configuration/Services/dashboard booking/utilization/revenue cases. Following final payment-minute precision, verification-length, document rendering and pagination refinements, all 54 reservation/mobile/workflow tests passed. One final document fixture/export test passed after PDF heading styling. Django system checks were clean; migration check reported no changes. JavaScript syntax checks passed.

Headless Chrome passed existing automatic reservation/schedule/printable-slip behavior at 1440, 768, 390 and 320px. A separate four-width transaction review verified eye/more actions, no second Approve for authorized manual records, mandatory payment fields, real receipt/paid state, table refresh, Job Order/PDF links, audit display, conditional absent Inspection and viewport containment. Browser writes were intercepted, not live saves. Two generated fixture PDFs were text-extracted, rendered with PyMuPDF and visually inspected: actual client/facility data, readable labels, contained A4 layout. Flutter analyze on the two changed files found no issues; the three existing facility_booking_flow_test.dart widget tests passed.

Manual verification:

1. With an authorized Facilities/Super Admin, create a real future reservation through the UI. Confirm Approved + Unpaid, actual Approved By/At and no repeat Approve action. With a custom book-only admin, verify Pending Approval instead.
2. Submit a normal mobile request: confirm Pending Approval + Unpaid. Approve/reject it from authorized Bookings actions; check Calendar/availability afterward.
3. Approved + Unpaid -> Payment -> Record Payment. Verify blank OR, wrong/partial amount, invalid date, duplicate OR and missing permission cannot save. Enter actual cashier details; confirm one payment, Paid + Reserved / Confirmed and the real activity entries. Retry must not create another payment.
4. Open Job Order, save actual relevant details, then edit: its number/booking identity must remain. View/Print/Export PDF and check real client/schedule values. No SOA, payment gateway or generated OR should appear.
5. For a facility configured with inspection requirements, verify only applicable inspection sections. Select actual authorized staff, enter findings/date/evidence; post-use must wait until the reservation ends. Required inspections and paid state must gate completion.
6. Upload a real small valid PDF/photo as supporting evidence. Confirm the protected download works for a booking reader and is denied after logout. Confirm internal evidence/documents do not appear in mobile JSON.
7. Edit an active unpaid reservation, keeping its ID/facility. Confirm it does not conflict with itself but still detects another booking/block. Paid/completed/cancelled/rejected requests must not expose or accept editing.
8. Search/filter an older booking beyond the first page and use Next/Previous. Add/update a record and confirm the current page/total reconciles from actual backend data.
9. Verify phone and enlarged-text Flutter flow plus 320px web scrolling; keyboard Tab/Escape and tab arrows/Home/End remain usable. No physical-device result is claimed by automated checks.

Troubleshooting confirmed during implementation: the generic booking URL initially captured clients as an ID; place literal clients/options routes first. Stored Python TimeField values include seconds but the existing parse_time expects HH:MM; approval now formats those values before passing them to the shared helper. Native datetime-local inputs have minute precision, so payment submission compares against the booking's creation minute instead of incorrectly rejecting a payment entered in the same minute. Invalid structured method/Other verification is blocked; legacy free-text API callers remain compatible.

If actions disappear unexpectedly, inspect current paid/status values and the actual assigned permissions, not the role name alone. If Inspection is missing, check the saved workflow snapshot rather than inventing inspection records. If a free schedule is unavailable during Edit, confirm the authorized current booking ID reached the preview; do not exclude all bookings to suppress a conflict. On API failure, the tab provides Retry and no new payment/state is fabricated. If a PDF/document is missing, first verify it was actually recorded and that the request is authenticated and owned/authorized.

Safe practice exercise: in `test_booking_workflow.py`, add one assertion to `test_paid_state_derived_and_retry_cannot_duplicate_payment` that Record Payment is absent after the first successful real test payment. Predict the result from `allowed_actions`, run that single isolated test, then inspect `paid_summary` and explain why setting the display text cannot alter a payment record. For a UI-only exercise, change one Job Order field label in `editor()` without changing its `name`; rerun the intercepted transaction browser review and inspect its POST keys. Restore the label afterward. Never practice by deleting production bookings/payments.

Commands from backend/core:

```powershell
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations api.test_mobile_facility_booking --keepdb --noinput
```

From project root after exporting the isolated fixtures with BOOKING_REVIEW_DIR as described earlier:

```powershell
node scratch/admin-reservations/check.cjs
node scratch/admin-reservations/workflow-check.cjs
```

From campushub:

```powershell
flutter analyze lib/module_app/screens/facilities/facility_booking_status_screen.dart lib/module_app/widgets/facilities/booking_widgets.dart
flutter test test/facility_booking_flow_test.dart
```

### 8. Remaining limitations

The approved BEU Job Order source file/layout was not supplied or verified from an authoritative public source. Generated forms use the requested fields and institutional styling; they are not claimed to reproduce an approved official form exactly. Office sign-off/actual cashier OR issuance remain external. No automatic SOA, actual deposit refund/disbursement, Refunded payment toggle, signed clearance, electronic signature or new lab/assessment/leasing workflow was invented. Refund decisions are recorded findings only.

Current inspector choices use active users with existing booking-management permission, not a new personnel registry. The optional job_order_stage key is honored when configured; a dedicated facility-editor control is not added. Custom/unsupported pricing safeguards still require a configured process. No automatic historical approval/Job Order backfill; older amounts/origins/staff not recorded stay honestly unassigned. PDF links need authentication; Flutter's existing native slip screen remains and no extra in-app PDF download package is introduced. No physical Android, production booking/payment, simultaneous-client stress test or institutional form acceptance test was performed. Tests verify behavior but do not promise that no future code/configuration change can break it.

## Booking actions, restored colors and 12-hour times - 2026-10-13

### 1. Cause / reason

The user explicitly requested one three-dot row action instead of a separate eye, restoration of the previous colors, and 12-hour booking times with Calendar left unchanged. This supersedes the prior eye-plus-menu and navy-only table status styling for this specific page. Confirmed causes: renderAllBookings emitted two action buttons, the last stylesheet rules replaced the existing semantic colors, and the raw Calendar formatter was also used for Bookings.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/static/components/js/admin_bookings.js` | 116 `formatBookingTimeRange`, 370 Time / Stay cell, 382 `openBookingDetails`, 443 `showMoreActions` | Separate 12-hour booking formatter; remove eye markup; always one menu with View Booking Details first; route one details/action event. |
| `backend/static/components/js/admin_booking_workflow.js` | 47 Overview Time | Reuse the exposed booking formatter in loaded transaction details. |
| `backend/static/components/js/admin_booking_forms.js` | 5 `timeLabel`, 129 form summary, 133 configured stay times | Show configured read-only check-in/out times and hints in AM/PM. |
| `backend/static/components/css/admin_booking.css` | Existing status rules at 1644; transaction styling near 1893 | Remove the two final navy/gold table overrides, revealing the existing approved/paid green, pending gold, cancelled/rejected/unpaid red and completed blue styles. |
| `backend/core/modules/facilities/services/booking_workflow.py` | 28 `time_label` | Read-only Django 12-hour formatting for actual time values. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 178 document Time row | Format printable Job Order/inspection/slip PDF time ranges using the shared display helper. |
| `backend/core/modules/facilities/admin_booking_views.py` | 204 helper import; 220 slip context | Add formatted actual check-in/out display values. |
| `backend/core/modules/facilities/templates/facilities/pages/booking_slip.html` | 18 Check-in / Check-out | Render those labels without changing saved metadata. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 14, 214-216 assets | Bump affected assets to `20261013-booking-actions-time`. |
| `backend/core/modules/facilities/test_booking_workflow.py` | Job Order HTML assertion / fixture exporter | Assert the printed 12-hour range and export actual read-only role responses for UI review. |
| `scratch/admin-reservations/workflow-check.cjs` / `check.cjs` | Row actions/colors/time assertions; Calendar check; room hint assertion | Verify single menu, actual read-only View, restored computed colors, AM/PM, midnight/noon and unchanged Calendar time. |
| This guide / `CAMPUSHUB_CONTEXT.md` | Current section / last entry | Preserve the requested behavior and learning notes. |

### 3. Changes made

Every visible booking row has exactly one three-dot button. View Booking Details is the first item, including for viewers and completed/read-only records with no write actions. Other items continue to come from the existing server-provided permission/state list. Removing the eye does not remove access to Details. The menu uses the existing modal and opens only one read/action event, avoiding the previous duplicate details fetch for menu operations.

Existing status colors are restored only by removing the overrides; no new color definitions or status meanings were invented. Explicit current user instructions authorize this restoration despite the broader navy-only brand preference in the project reference. All booking display ranges use 12-hour text, for example 1:00 PM - 5:00 PM. Calendar grid and Upcoming on Calendar keep the existing HH:MM text. Native schedule-entry inputs and stored/API values are not converted into AM/PM strings.

### 4. How it works / functions and data flow

`formatBookingTimeRange(start,end)` accepts stored/API time strings, validates hour/minute components and returns a display string. Hour 0 becomes 12 AM, hour 12 becomes 12 PM and hour 13 becomes 1 PM. It does not change the original values. `window.CampusHubBookings.formatTimeRange` exposes this small UI helper to the transaction and reservation controllers, so they do not copy its formatting logic. The original `formatTimeRange()` still serves Calendar exclusively.

`showMoreActions(trigger,booking)` constructs View plus the booking's actual permitted actions. Choosing View calls `openBookingDetails(booking)`; choosing an operation calls it with the existing operation name. The modal's protected API load and backend checks remain the same. `time_label(value)` takes a Python TimeField value or an existing configured HH:MM string and returns Django's g:i A presentation for documents. The original booking time is still what availability, editing and pricing consume.

Annotated example:

```javascript
// Read-only output: does not modify start_time or the API payload.
CampusHubBookings.formatTimeRange('13:00', '17:00');
// -> '1:00 PM - 5:00 PM' (the interface uses a typographic range separator).
CampusHubBookings.formatTimeRange('00:00', '12:00');
// -> midnight and noon: 12:00 AM - 12:00 PM.
```

### 5. Backend / API behavior

No endpoint, permission, payment, approval, availability or Calendar data logic changed. The backend additions are presentation helpers/context values only. Actual permitted write actions still come from allowed_actions and are rechecked under the same transaction locks. View in the menu is read access, not a new write capability.

### 6. Database / migration impact

No migration, schema change, seed or production write. TimeField/JSON schedule values remain unchanged. Tests/exported UI fixtures use the isolated test database; browser writes remain intercepted.

### 7. Tests performed / debugging / manual verification

For this update, all 54 workflow/admin/mobile tests passed in 2.935 seconds; Django system checks were clean. All three affected JavaScript syntax checks passed. Both browser reviews passed at 1440, 768, 390 and 320px. New checks verify no separate eye, exactly one row button, View first, View-only menu for an actual read-only role, Details access, existing green/red computed status colors, table and Details AM/PM, correct midnight/noon and Calendar's unchanged 13:00 - 15:00 display. Existing automatic reservation, room hints, save/table refresh, payment, audit and document-link flows still passed. The Job Order HTML test verifies 1:00 PM to 5:00 PM. Broader 202-test results above belong to the previous workflow implementation, not a new run for this presentation update.

Manual checks: hard refresh Bookings; confirm the sole three-dot button opens View Booking Details first. Check an approved/unpaid record for the original colors. Open Details and compare the table's AM/PM range with its Overview range. Check a configured stay's read-only times and printed form. Open Calendar and confirm it still shows its earlier 24-hour range. Sign in with a booking-view-only role and verify View remains available while write actions do not appear.

Troubleshooting: stale double icons or navy badges usually mean cached CSS/JS; check asset version `20261013-booking-actions-time` and Ctrl+F5. An empty View modal/error still requires valid read permission and a real record; do not add write permissions to fix reading. Incorrect noon/midnight usually comes from confusing hour 0 with 12 or using a Date object that shifts timezone; the helper formats clock components directly. Do not submit the AM/PM label back into the existing HH:MM API fields.

Safe practice exercise: in the browser console, call the helper with 09:15/12:30 and predict 9:15 AM/12:30 PM before checking it. Then inspect the actual form's start/end input values and confirm they are still HH:MM. Changing only the View menu label should not change its data-menu-action=view key; rerun the existing intercepted browser check to prove routing still works. Practice on local fixtures, not production booking times.

### 8. Remaining limitations

Native time/date-time input widgets follow browser/OS locale; their stored values remain HH:MM as required by the existing API. This update formats read-only web booking displays and documents; it does not replace native controls, change Calendar time presentation or restyle unrelated modules/mobile badges. Earlier institutional-form/refund limitations remain unchanged. No physical-phone or production booking test was performed for this display update.

## Bookings KPI cards - 2026-10-13

Implements attachment `dd2a6688-d10c-4563-b1cb-4763bc2846e6` using the existing physical Bookings scope, five saved status codes and FacilityPayment records.

### 1. Cause / reason

Bookings had no authoritative summary cards. The old JavaScript still contained unused counts derived from the current table page; those cannot represent an entire booking history and were removed. The new four counters come from the database, including records beyond page one. Their click filters share the same backend conditions as their counts.

Confirmed related bug found by the stay/legacy tests: negating a JSON source=schedule comparison excluded existing metadata with a missing source key because SQL treats that comparison as unknown, not false. `schedule_blocks_q()` now identifies actual schedule-source IDs through a subquery; missing source keys no longer remove normal reservations. Existing prefix-based block recognition remains. This is a shared scope correction, not invented legacy data or a second schedule engine.

### 2. Exact files / current line anchors

| File | Approximate current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/booking_workflow.py` | 58 `payment_summary_query`, 68 `booking_kpi_conditions`, 82 `booking_kpi_query`, 94 `booking_kpis`, 101 `filter_booking_kpi` | Shared paid-state annotations, end-date/time conditions, one four-count aggregate and identical KPI table filtering. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 39 `list_data` | Compute full scoped counts once and apply the selected KPI to the existing searched/paginated rows. Return additive kpis JSON. |
| `backend/core/accounts/views.py` | 1137 `admin_bookings_page`, 1141 `page_data` | Reuse list_data for initial rows/counts/page and retain initial search/facility selection. |
| `backend/core/modules/facilities/services/schedules.py` | 18 `schedule_blocks_q` | Explicit schedule-source ID subquery avoids SQL NULL exclusion of legacy metadata. |
| `backend/core/modules/facilities/templates/facilities/partials/booking_kpis.html` | 1 `bkBookingKpis` | Exactly four real-count cards with existing-style SVGs, labels/helper text and accessible filter buttons. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 81 partial include, 135 `bkPageSummary`, 14/215 asset versions | Place cards below the header and above the table/Quick Actions row; accurate initial pagination; assets 20261013-booking-kpis. |
| `backend/static/components/css/admin_booking.css` | 1895 `.bk-kpi-grid` | Facilities-style white cards, navy numbers, small navy/gold icon containers, restrained border/shadow; responsive four/two/one columns. |
| `backend/static/components/js/admin_bookings.js` | 60 `kpiGrid`, 62 `selectKpi`, 78 `loadBookingPage` | Send KPI filter, preserve search/facility, refresh database counts after actions, loading state, restore last accepted selection on failure; remove old page-derived counters. |
| `backend/core/modules/facilities/test_booking_workflow.py` | KPI tests near 203; fixture exporter | Six real-database KPI cases and actual filtered list fixtures for browser review. |
| `scratch/admin-reservations/workflow-check.cjs` | KPI counts/click/grid assertions | Four-width review using actual isolated exported backend responses. |
| This guide / `CAMPUSHUB_CONTEXT.md` | Current section / last entry | Current rules, debugging evidence, verification and learning exercise. |

### 3. Changes made: 15-point requested report

1. Files/current searchable anchors are listed above. No unrelated page, sidebar, model or mobile UI redesign.
2. Exactly four cards: Total Bookings, Pending Approval, Upcoming / Reserved, Unpaid. No extra Paid/Rejected/Cancelled/Completed/Approved card.
3. Counts and filters reuse `physical_bookings()`, the same authorized table scope excluding Services and schedule blocks. Historical physical reservations remain relevant even if cancelled/rejected/completed; Total is history, not just actionable requests.
4. Payment state uses the existing paid FacilityPayment status and actual amount totals. Existing Booking, Payment, Room and JSON fields remain the source of truth.
5. One filtered Count aggregation returns all four counters. Correlated payment sum/existence subqueries avoid multiplying booking rows when several payments exist. No all-history Python loop, HTML count or JavaScript-derived KPI value.
6. Total Bookings counts every physical client booking in this authorized scope; helper All facility reservations.
7. Pending Approval counts actual pending status, including user/mobile and any permission-limited manual request still awaiting review. Auto-approved manual records are approved and excluded; helper Requires admin review.
8. Upcoming / Reserved requires approved + a paid record + paid sum at least total_amount, and an end that has not passed. It safely maps the existing approved code to Reserved / Confirmed instead of inventing a saved reserved status; helper Confirmed future bookings.
9. Unpaid requires approved and not fully paid under the existing paid_summary semantics. Pending/rejected/cancelled/completed requests are not actionable payment counts; helper Awaiting payment / OR. Legacy partial totals still leave a balance, but this feature does not enable a new partial-payment workflow.
10. Cards click through the existing list API: Pending also selects the native pending dropdown; Upcoming and Unpaid add their shared KPI condition. Total clears KPI/status restrictions. Search and selected facility remain. Changing the native status dropdown clears the KPI slice to avoid contradictory hidden conditions; pagination restarts at one for changed filters.
11. Page/API permissions are unchanged. Super/Facilities Admin and custom readers see exactly the existing table scope; ordinary/mobile users and unauthorized Marketplace roles receive no new totals access.
12. Existing search/status/facility/pagination remain. Initial page parameters now use the same list_data implementation as AJAX rather than filtering only the first unfiltered page in the browser.
13. JavaScript only sends filters and renders backend numbers. Subsequent writes/payment changes refresh the current page and counters. aria-pressed/aria-busy expose selected/loading state; errors retain last actual data and restore the accepted KPI/status selection, never fabricate zero counts.
14. No migration, schema change, seed, fake record or production database rewrite. Empty database produces four actual zero counts and keeps the cards visible.
15. Hard refresh Ctrl+F5; restart Django only if new helpers are not reloading. No migrate command. Verification commands are below.

### 4. Functions, inputs/outputs and data flow

`payment_summary_query(records)` accepts the existing scoped Booking queryset and adds has_paid plus paid_total. The correlated payment subquery sums only payment_status=paid; failed/unpaid rows cannot change the paid total. Exists distinguishes a zero-cost booking with no actual payment record from one with a recorded zero-amount paid transaction, matching the current workflow.

`booking_kpi_query(records)` also adds the effective checkout clock. It prefers saved request check_out_time; otherwise it respects the workflow snapshot or, for older records without a snapshot, the actual facility configuration. Missing configured time follows the existing reservation_end midnight fallback. Same-day malformed clock strings are not treated as a confirmed active stay.

`booking_kpi_conditions(now)` returns the pending/upcoming/unpaid Q conditions. Django timezone.localtime derives the day and current local clock. Slot reservations today compare end_time, not start_time, so a started but unfinished booking remains upcoming/active. Stays compare checkout date and, on checkout day, its configured clock. Equality at the end boundary is ended. Completed/rejected/cancelled statuses never enter Upcoming or Unpaid.

`booking_kpis(records,now)` uses those annotations/conditions in one aggregate and returns integer keys total/pending/upcoming/unpaid. `filter_booking_kpi(records,key,now)` applies the exact same conditions to rows. `list_data` first computes counts across the full authorized physical scope, then applies KPI/search/status/facility filters and the existing 20-row paginator. KPI totals therefore describe authorized history, not the current search subset or page. The same captured now is passed to counts and filtering within one request.

Read flow: authorized page or GET /api/bookings/ -> list_data -> shared scope/annotations -> counts + filtered page -> template or JSON -> card values/table. Write flow remains unchanged; after a real operation the existing table controller reloads its current list and renders the returned counters. Calendar does not render these cards, and mobile endpoints do not receive this web-only KPI payload.

Annotated example:

```python
scope = physical_bookings()              # Excludes Services and actual schedule blocks.
totals = booking_kpis(scope, now)         # Four counts in one aggregate SQL statement.
rows = filter_booking_kpi(scope, 'unpaid', now)
# rows: approved reservations whose actual paid records do not fully cover total_amount.
# totals are backend-derived integers; the browser never sums its visible table rows.
```

This approach makes card counts and click results agree while preserving separate Booking and Payment statuses. It also avoids payment joins counting the same booking multiple times.

### 5. Backend / API behavior

GET /api/bookings/ keeps its existing paginated fields and adds kpis. Optional kpi values pending/upcoming/unpaid filter rows; blank/unknown values safely use the ordinary list. Existing q/status/facility/page parameters still compose normally. No new endpoint, permission, authentication engine, booking lifecycle, receipt/payment method or availability calculation was introduced. The shared missing-source scope fix also lets existing legacy physical records appear correctly in the existing readers that use schedule_blocks_q.

### 6. Database / migration impact

No models/migrations changed; makemigrations --check --dry-run reported No changes detected. The application computes totals at read time; it does not persist or seed KPI values. Only isolated test records and intercepted browser responses were used for verification.

### 7. Verification, manual testing and troubleshooting

For this update all 208 targeted Django tests passed in 30.331 seconds: workflow/admin/mobile, facility configuration, Services, dashboard dates/bookings/rankings/upcoming/utilization/revenue. The six new KPI cases cover empty data and one-query aggregation; status/source/payment matrices; multiple/failed/partial payments; active versus ended slots/stays; legacy configuration/snapshot times; missing source keys; search/facility/pagination; denied roles and read-only access; and zero-price/recorded-payment semantics. JavaScript syntax, Django system and diff checks passed. Migration check reported no changes.

Both headless Chrome reviews passed at 1440/768/390/320px. KPI checks verified exactly four cards, real server counts, manual Approved+Unpaid mapping, four/two/one responsive columns, Pending/Unpaid/Total clicks, retained facility filter, empty pending results and count refresh after actual fixture payment. Existing menu/View/colors/12-hour time/Calendar/schedule/reservation/save/details/receipt flows still passed. Desktop and 320px KPI screenshots were visually inspected. Browser writes were intercepted, never production saves. No new physical-device/Flutter widget test is claimed because Flutter code was not changed for these web cards.

Manual steps:

1. Refresh Bookings and confirm the four cards are below its title, above the table, with the exact requested labels/helpers. Check a small viewport for wrapping without hidden cards.
2. Use an actual approved unpaid manual reservation: it should count in Total and Unpaid, not Pending. A mobile Pending request counts in Total and Pending, not Unpaid/Upcoming.
3. After recording its real valid cashier payment, check Unpaid decreases and Upcoming increases only if the approved reservation has not ended.
4. Compare a currently active paid slot/stay with an ended one. Active remains Upcoming even if its start is past; end boundary/past completed/cancelled/rejected do not count.
5. Click a card, enter a search and choose a facility; use Next/Previous. Total clears KPI/status while preserving search/facility. Confirm counts remain full authorized-scope totals and table rows reflect current filters.
6. Compare against Services/Service Requests and Manage Facility Schedule: those records must not inflate physical Booking totals. Verify a read-only permitted account sees totals but no write actions; an unauthorized role cannot request totals directly.
7. On an empty isolated database, all four values remain visible as zero and the table retains its empty state. On a failed network request, an error appears and prior actual counts remain rather than changing to zero.

Troubleshooting: stale/missing cards usually indicate old template/CSS/JS; check asset version 20261013-booking-kpis. An Upcoming count of zero can be correct for approved but unpaid records: Approved is not the fully paid Reserved display state. Inspect actual paid records, outstanding total and end time before changing conditions. If multiple payments inflate a total, check that payment_summary_query uses a subquery rather than a joined Count. If legacy records vanish, check the missing-source-key regression in schedule_blocks_q; do not mark every missing source as a schedule or seed replacement records. Cards and visible row totals intentionally differ under search/pagination; compare the API kpis with the complete authorized scope, not HTML row count.

Safe practice exercise: modify only one card's helper text in booking_kpis.html, refresh, and verify all four backend keys/counts remain unchanged. Then in the isolated KPI matrix test change one approved test booking from unpaid to a real paid transaction, predict its Unpaid/Upcoming result from its end date and rerun that single test. Do not change a CSS label or insert fake production values to manipulate a count.

```powershell
# From backend/core:
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations api.test_mobile_facility_booking --keepdb --noinput
# From project root after isolated fixture export as documented above:
node scratch/admin-reservations/workflow-check.cjs
node scratch/admin-reservations/check.cjs
```

### 8. Remaining limitations

Same-day legacy bookings without a usable end time cannot be certified as Upcoming; future dated slots/stays remain identifiable from their real dates. Unknown/malformed configured checkout clocks are excluded on the checkout day instead of inventing a time. Counts are request-time snapshots, refreshed on list/filter/page/actions; there is no new push notification or auto-refresh timer. Existing facility-specific office scoping is unchanged; the module currently uses its existing authorized physical queryset. Native input appearance, approved institutional form matching and cash-refund limitations from earlier sections remain unchanged.


## Facility Calendar: shared filters and event details (2026-10-13)

### 1. Cause / reason

Confirmed from the existing code: event-type buttons filtered only Upcoming, not the month grid; there was no facility filter or Today button; calendar events were non-interactive; initial Calendar loading expanded a year; Upcoming reused that dataset, included already-ended events, and lacked a general calendar empty state. Official Campus Use and Administrative Hold were combined in the legend despite being separate saved types. This update improves the existing month view rather than creating a second reservation system.

### 2. Exact files changed, current lines and nearby anchors

Line numbers are approximate and current at this update. Use the anchor in your editor to find a function after later edits.

| Folder/file | Line | Nearby code anchor | What changed |
|---|---:|---|---|
| `backend/core/modules/facilities/services/calendar.py` (new) | 15, 20, 79 | `calendar_facilities`, `calendar_events`, `calendar_data` | Read-only event projection, bounded dates, room/payment batching, shared filters and five upcoming events |
| `backend/core/accounts/views.py` | 869, 1117, 1151 | `_bookings_calendar_events`, `admin_bookings_page`, `admin_calendar_page` | Shared projection wrapper; remove unused Bookings calendar query/payload; render bounded Calendar data and protect page access |
| `backend/core/modules/facilities/admin_booking_views.py` | 272, 328 | `calendar`, `attachment` | Validate range/type/facility; return both panels; authenticated read-only evidence access and private no-store responses |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 29, 166, 173, 229 | `bkFacilityCalendar`, `bkCalendarDetails`, `bkCalendarData` | Facility Calendar title, Today, labeled filters, split legend, event modal and existing schedule form; no reservation form or KPI on Calendar |
| `backend/static/components/js/admin_facility_calendar.js` (new) | 20, 46, 51, 74 | `openDetails`, `eventButton`, `render`, `load` | One dedicated Calendar controller; shared filtering, event buttons, More, details, errors/retry and server-date Today |
| `backend/static/components/js/admin_bookings.js` | 168, 304 | `renderAllBookings`, `DOMContentLoaded` | Remove obsolete Calendar rendering from the Bookings controller; support an actual booking deep link; retain table, pagination, actions and modal closing |
| `backend/static/components/js/admin_booking_forms.js` | 272, 288, 299 | `refreshSchedule`, `editBlock`, `campushub:calendar-schedule` | Reuse editor for selected block or empty date; preserve original effective date and ID; refresh Calendar filters/month after successful save/cancel |
| `backend/static/components/css/admin_booking.css` | 1910 | `Facility Calendar: scope presentation changes` | Navy/gold/neutral event distinctions, dashed pending state, toolbar, focus rings and contained small-screen grid scrolling |
| `backend/templates/partials/admin_sidebar.html` | 133 | `can_manage_schedules or perms.accounts.can_view_bookings` | Calendar is visible for existing authorized booking readers as well as schedule managers; editing remains separate |
| `backend/core/modules/facilities/test_calendar.py` (new) | 53, 102, 121, 149, 165 | `test_status_payment...`, `test_room_stay...`, `test_validation...`, `test_readonly_attachment...`, `test_export...` | Ten isolated Calendar tests and real test-database browser exports |
| `backend/core/modules/facilities/test_service_navigation.py` | 55 | `calendar.context["calendar_data"]` | Check physical/service separation against the Calendar's actual new payload instead of an unused Bookings payload |
| `scratch/admin-reservations/calendar-check.cjs` (new) | 1 | `Real Django test-rendered pages` | Intercepted browser review using actual Django test exports, never live writes |
| `scratch/admin-reservations/workflow-check.cjs` | 88 | `deepLink` | Verify booking deep links and load the new Calendar controller in the existing review |
| `docs/facility-configuration.md` | 1918 | `Facility Calendar: shared filters` | This implementation, debugging and learning guide |
| `CAMPUSHUB_CONTEXT.md` | end | `Facility Calendar (2026-10-13` | Persist current behavior for future changes |

Models and URL files were inspected, not modified. Existing routes remain in `backend/core/core/urls.py` at 132-133 and 207-210.

### 3. Changes made (requested Calendar report)

- Title is **Facility Calendar**; existing month arrows, month/year, right panel and legend remain. Today returns to the server's current month without clearing facility/type filters.
- Facility choices come from real unarchived, non-inactive physical facilities. Maintenance/unavailable facilities remain selectable because their schedules can still need inspection. Services are excluded.
- Event Type has All Events, Reservations, Class / Academic Schedule, Maintenance, Official Campus Use, Administrative Hold and Other. The same server parameters control both panels.
- Each cell identifies the actual facility, type, time/status and room when available. Requester details appear only in the compact details modal, not tiny cells. The first two events are visible; **+N more** opens all events for that date.
- Reservations show real ID, requester, status, payment and actual room/stay. **View Booking Details** opens `/admin-bookings/?q=<actual-id>&booking=<actual-id>` and loads the existing protected transaction modal, not a new page.
- Schedule details show saved title, occurrence date, original effective date, recurrence, status and protected supporting attachment. Managers get **View / Edit Schedule**; read-only roles do not get edit controls.
- Empty dates offer an explicit plus button that opens the existing Manage Facility Schedule form with the date (and selected facility) prefilled. Nothing is created until the user completes the form and saves successfully.
- Upcoming shows at most five matching events in the next 30 days, ordered by occurrence date/time. Completed and ended occurrences are excluded. Ongoing stays/blocks remain current until their actual end; a stay appears once, not once per occupied night.
- Empty text is **No upcoming calendar events.** Loading/error/retry states do not pretend failure means zero events. Old results clear when a new filter request starts, and a revision counter prevents an older response overwriting newer filters.
- Legend separates Official Campus Use and Administrative Hold. Navy, gold, neutral fills/borders and readable labels distinguish types; Pending Reservation has a dashed gold treatment.
- Calendar now uses AM/PM labels following the 12-hour update below; Bookings keeps its existing AM/PM presentation. All-day blocks display **All Day** and do not expose their stored internal full-day clock bounds as a fake time range.
- The full week scrolls inside the card at narrow widths with a scroll hint; the page itself stays contained. Upcoming moves below Calendar through the existing responsive columns. Keyboard buttons, focus rings, Escape, focus trap and focus return use existing modal behavior.

### 4. How it works: models, functions, inputs/outputs and data flow

**Existing records reused:** `api.models.Booking` stores both reservations and legacy schedule blocks; `FacilityBookingRequest.details.schedule` supplies structured block type, effective-until, weekdays, repeat and all-day settings. There is no separate Calendar model. `Facility` supplies actual names and classification; `Room` supplies actual room names; `FacilityPayment` supplies recorded payment status. No uploaded image is interpreted as a schedule.

`calendar_events(first, last, facility_id, event_type, now)` accepts Python dates and optional existing filter values, queries overlapping bookings/stays/recurring schedules, and returns JSON-ready occurrences. `select_related` loads the facility, requester and existing sidecar together; `prefetch_related("payments")` and one room query avoid per-event queries. A ten-booking room fixture takes **three queries** for this projection.

`calendar_data(...)` returns `{events, upcoming, today, start, end, upcoming_end}`. `events` is for the requested visible range. `upcoming` uses today through 30 days independently, so browsing a past month does not erase future events. If one queried range already contains the upcoming horizon, it is reused. Django timezone-aware comparisons remove ended events safely.

`load()` sends the selected month, facility and type to the existing API. `render()` places the returned occurrences in their cells and renders the same response's Upcoming list. `openDetails()` only reads returned structured fields. `editBlock(row)` fills the existing editor from that selected source record; `refreshSchedule()` reloads current Calendar filters after a successful existing write API operation. Backend validation, facility locking, conflict checking and existing audit logging remain authoritative.

Annotated example (not production seed data):

```python
# Input: the visible month and an actual selected facility ID.
result = calendar_data(first, last, facility_id=selected_id, event_type="maintenance")
# Output: only maintenance occurrences for that facility in both lists.
month_rows = result["events"]
next_rows = result["upcoming"]  # maximum five, independently bounded to the next 30 days
```

A weekly schedule with one saved Booking ID can produce several different occurrence `key` values (`id:date`) without creating another database row. Editing a later occurrence uses `first_date`, not that occurrence's date, so the original recurring schedule is not silently moved. A room stay expands from real check-in through the night before checkout; actual configured/saved clocks are used when present, and absent clocks are not invented for display.

This approach was chosen because Calendar is a read-only projection of the same records used by Admin Add Reservation, Manage Facility Schedule and mobile availability, not a second availability engine.

### 5. Backend / API behavior, status policy and RBAC

- Existing GET `/api/facility-calendar/?start=YYYY-MM-DD&end=YYYY-MM-DD&facility=<id>&type=<type>` validates dates and limits a request to 62 days. It queries the visible range plus the independent short Upcoming horizon, not unlimited history.
- Pending reservations stay visible as **Pending Reservation** because existing `conflicting_bookings()` also holds pending slots. Approved unpaid reservations show Approved; fully recorded paid approved reservations reuse `status_label()` to show Reserved / Confirmed. No invented reserved database status.
- Cancelled/rejected records are excluded. Completed reservations are displayed only after their actual end and never in Upcoming. Existing schedule status codes are reused; cancelled/rejected/closed blocks are not active events. No extra active/inactive field was introduced.
- Room IDs are resolved in bulk and checked against their owning facility. Room labels describe that reservation; they do not imply all rooms are occupied. The underlying room-aware conflict engine is unchanged.
- Both page/API require authenticated admin authority and existing schedule-management or booking-view permission. Marketplace Admin receives no permission grant. Schedule create/update/cancel still require `can_manage_schedules`; hiding buttons is not the security control.
- Supporting attachments use the existing protected endpoint. Authorized Calendar readers can download them; anonymous/non-authorized roles cannot. Calendar JSON and attachments use private/no-store caching.
- Existing booking actions, order pages, other pagination and mobile bearer/API logic are unchanged. The Bookings page no longer does an unused Calendar query; its KPI/list source remains the same. The older Facilities catalog preview retains its existing horizon through the compatibility wrapper.

### 6. Database / migration impact

No model/table/column/migration added. No Calendar rows, duplicate Bookings, copied recurrence records, generated rooms or production seed data. This implementation did not write to live facility/booking/payment records. Automated fixtures are temporary records in Django's isolated test database; browser requests are intercepted.

### 7. Tests performed, debugging and manual verification

Confirmed verification for this update:

- **218 Django tests passed**, covering Calendar plus existing booking workflows, admin reservations, mobile availability, facility configuration, physical/service navigation and dashboard/report regressions.
- Ten Calendar tests cover status/payment handling, both filters, independent sorted/limited Upcoming, ended events, recurrence/all-day, room batching, historical completion, bounds/RBAC, real facility options/empty data, private read-only attachments and fixture export.
- Calendar, booking transaction, and reservation/schedule browser reviews passed at **1440, 768, 390 and 320 px**. Calendar review verifies Today, More, actual details, original recurrence edit date, room stays, no tiny-cell requester, errors/retry, filter-preserving refresh and read-only UI. Transaction review also verifies the actual booking deep link. Desktop and phone Calendar screenshots were visually inspected.
- JavaScript syntax checks passed; Django system check reported no issues; migration dry run reported **No changes detected**; changed tracked-file whitespace checks passed.

During implementation, tests caught a wrong ORM field name (`status` instead of existing Facility `availability_status`), which was corrected. An old navigation test read the removed unused Bookings calendar context; it now verifies the actual Calendar payload and still checks physical/service separation. An isolated browser stub initially failed to parse its object return; the stub was corrected. These are resolved implementation/test issues, not claims about failures in the user's live records.

Manual checks using your existing records:

1. Open Facilities > Calendar and hard-refresh. Verify Facility Calendar, Today, two labeled filters and no KPI cards.
2. Select a physical facility and Maintenance; both panels must agree. Try Official Campus Use and Administrative Hold independently.
3. Use arrows to browse another month, then Today. Filters should stay selected; the month returns to the current server date.
4. Click a real reservation, verify its ID/status/payment/room, then View Booking Details. The existing transaction modal should open for that exact record.
5. Click a recurring block on a later occurrence. View/Edit should keep its original effective-from date and existing ID. Close without saving while only reviewing.
6. Click an empty date's plus; verify date/facility prefill and no record created merely by opening the form.
7. Check a real all-day block and room stay. All Day must replace synthetic clock bounds; only the actual saved room is named.
8. A period/type with no matches must show No upcoming calendar events. Simulate a failed API request in browser developer tools and verify Retry, not fake empty totals.
9. Test an authorized read-only admin and Marketplace Admin. Read-only can view; edit APIs remain denied; Marketplace without facility permissions cannot enter Calendar.

If filters appear unchanged, first hard-refresh (`Ctrl+F5`); assets use `20261013-facility-calendar`. In browser Network, inspect the GET `facility` and `type` parameters and both response arrays. If there are no events, inspect the actual source date/status/type before changing code: cancelled/rejected and Services are intentionally excluded; Upcoming is only the next 30 days. If edit is missing, check the existing role's permission rather than removing backend checks. Missing rooms/times should remain missing, not be filled with example values.

Commands (development server normally reloads Python; no migration required):

```powershell
# From backend/core:
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
venv/Scripts/python.exe manage.py test modules.facilities.test_calendar modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations api.test_mobile_facility_booking --keepdb --noinput
# Optional isolated browser fixture export, then review from project root:
$env:BOOKING_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/admin-reservations'
venv/Scripts/python.exe manage.py test modules.facilities.test_calendar modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations --keepdb --noinput
# Change working directory back to project root before these:
node scratch/admin-reservations/calendar-check.cjs
node scratch/admin-reservations/workflow-check.cjs
node scratch/admin-reservations/check.cjs
```

Safe practice: on a local branch, change only `len(upcoming) == 5` in `calendar_data()` to three and update the two Calendar test expectations that currently assert five results. Run `modules.facilities.test_calendar` and inspect the isolated fixture panel. Verify that the month still contains all occurrences while Upcoming has at most three. Revert your practice edits afterward; do not create production bookings to practice pagination.

### 8. Remaining limitations

Upcoming intentionally looks forward 30 days and includes still-current occurrences until their real end; it is not a list of all future years. Two events fit in a cell; More exposes the others. At narrow widths the readable week scrolls within the card. Results refresh on navigation/filter/retry/successful schedule actions, not through a new push/polling service. There is no new institutional-office scoping rule beyond the project's existing permissions. Existing catalog preview behavior, mobile booking rules, native time-input locale and document/form limitations from earlier sections remain. No physical-phone or deployed-production verification is claimed.


## Calendar 12-hour display follow-up (2026-10-13)

### 1. Cause / reason

The previous Calendar deliberately retained 24-hour display. The user's new instruction replaces that preference: show 12-hour AM/PM in Calendar. This is a presentation change, not a scheduling calculation fix.

### 2. Exact files changed

| File | Current line | Nearby anchor | Change |
|---|---:|---|---|
| `backend/static/components/js/admin_facility_calendar.js` | 15 | `const timeLabel` | Reuse `CampusHubBookings.formatTimeRange` for event/stay clocks |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 229 | `admin_facility_calendar.js` | New asset version `20261013-calendar-12hour` |
| `scratch/admin-reservations/calendar-check.cjs` | 36 | `Calendar uses AM/PM` | Browser expectations for grid, Upcoming, midnight/noon and actual stay clocks |
| `scratch/admin-reservations/workflow-check.cjs` | 101 | `Calendar uses 12-hour range` | Existing transaction review now expects Calendar AM/PM |
| `docs/facility-configuration.md` | 2049 | `Calendar 12-hour display follow-up` | Current behavior, verification and this learning guide |
| `CAMPUSHUB_CONTEXT.md` | end | `Calendar 12-hour follow-up` | Record that the earlier 24-hour preference is superseded |

The existing formatter is defined in `backend/static/components/js/admin_bookings.js` at 87 and exposed at 97. That file was inspected and reused, not changed for this follow-up.

### 3. Changes made

Calendar cells, hover titles, the More list, Upcoming on Calendar and Event Details now show times such as `1:00 PM - 3:00 PM` (with the existing range separator). Accommodation dates remain real dates, with actual check-in/out clocks formatted as AM/PM. All Day and missing-time behavior stay clear; no example clocks are added.

### 4. How it works / learning example

`timeLabel(row)` takes a real event from the existing Calendar JSON and returns display text. All-day events return `All Day` first. Other events pass `row.start` and `row.end` to the existing formatter; stays combine their real dates with the formatted clocks. All event UI locations already call this one function, so one change updates them consistently.

The shared formatter reads the hour/minute, validates them, uses `hour % 12 || 12` for the displayed hour, and selects AM before noon or PM from noon onward. It returns a string and never modifies `row` or saves anything. Reusing it keeps Calendar and Bookings consistent without duplicating time conversion code.

```javascript
// Input is still the actual API clock format.
CampusHubBookings.formatTimeRange('13:00', '15:00');
// Display output: 1:00 PM to 3:00 PM, separated by the existing range dash.
// Midnight 00:00 becomes 12:00 AM; noon 12:00 becomes 12:00 PM.
```

### 5. Backend / API behavior

No endpoint, serializer, availability rule, sorting rule, timezone, payment logic or permission change. API clocks still use HH:MM; the browser converts them only for display. Existing `admin_bookings.js` loads before the Calendar script and supplies the shared formatter.

### 6. Database / migration impact

No model/field/migration or saved time change. No live records were edited or seeded. No migration command is required.

### 7. Tests performed / troubleshooting / manual check

JavaScript syntax check passed. Calendar and transaction browser reviews passed at 1440, 768, 390 and 320 px, covering actual rendered grid and Upcoming AM/PM text, midnight/noon, actual accommodation clocks in details, All Day, shared filters and the existing transaction behavior. Template whitespace check passed. Backend suites were not rerun for this display-only follow-up; their previous results above refer to the preceding Calendar implementation.

Manual check: hard-refresh Facilities > Calendar, find an existing afternoon reservation, verify AM/PM in the cell/hover, Upcoming and Event Details; verify a real all-day block still says All Day. If the old format persists, use Ctrl+F5 and inspect the loaded Calendar script version (`20261013-calendar-12hour`). Do not change database clocks to AM/PM strings to repair display.

Safe practice: in browser developer tools on this page, call `CampusHubBookings.formatTimeRange('08:30', '17:00')` and verify 8:30 AM to 5:00 PM. Then test midnight/noon as shown above. These calls only return text and make no requests or database writes.

### 8. Remaining limitations

Native time-input controls in Manage Facility Schedule follow the browser/device locale. This update controls read-only labels in the Facilities > Calendar page; it does not force a native input's clock picker or change the separate older catalog preview.


## Manage Facility Schedule: clean new/edit form (2026-10-13)

### 1. Cause / reason

Confirmed cause: opening the modal always fetched a list of up to 300 existing schedules, including cancelled history, above the form. The footer also exposed New Block, Close and Save Block. New forms could retain previously edited values. The user's request is one clean schedule form with Cancel and Save Schedule, and a selected-record summary only while editing.

### 2. Exact files changed and nearby anchors

| File | Approximate current line | Anchor | Added/changed/removed |
|---|---:|---|---|
| `backend/core/modules/facilities/templates/facilities/partials/booking_forms.html` | 79, 80, 99 | helper text, `bkScheduleSummary`, footer | New helper wording, hidden edit-only summary, remove New Block and use Cancel / Save Schedule |
| `backend/static/components/js/admin_booking_forms.js` | 272, 280, 287, 308, 331 | `resetSchedule`, `refreshSchedule`, `editBlock`, `campushub:calendar-schedule` | Reset new entries, selected edit summary, preserve cancellation through that summary, remove automatic history query, close/notify/refresh after save |
| `backend/static/components/js/admin_bookings.js` | 97 | `window.CampusHubBookings` | Expose existing `showToast` as `notify`, reusing the current feedback style |
| `backend/core/modules/facilities/admin_booking_views.py` | 183, 242, 315 | creation response, overlap error, cancelled schedule error | Schedule success message and plain schedule wording; no change to save/conflict/locking rules |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 14, 227-230 | script/link asset versions | Cache version `20261013-schedule-form`; Calendar's existing 12-hour version remains |
| `backend/core/modules/facilities/test_admin_reservations.py` | 159, 329 | `test_weekly_block...`, `schedule-saved.json` | Verify logical schedule identity/no client/payment/job order and export actual test API response |
| `scratch/admin-reservations/check.cjs` | 90 | new/edit form checks | Verify labels, no history query, selected summary, clean reopening, conditional fields, actual fixture save response and success feedback |
| `docs/facility-configuration.md` | 2106 | `Manage Facility Schedule: clean new/edit form` | This report, troubleshooting and learning guide |
| `CAMPUSHUB_CONTEXT.md` | end | `Schedule form cleanup` | Preserve this behavior for future work |

Models, availability services, Calendar controller, URLs and CSS were inspected and reused without being modified for this cleanup.

### 3. Changes made / final form behavior

- Title stays Manage Facility Schedule. Helper: **Add unavailable schedules for classes, maintenance, or official use.**
- Footer has only **Cancel** and **Save Schedule**. New Block is removed from the template and JavaScript; resetting is an internal function, not another admin button.
- New entry opens with blank fields, editable facility and no unrelated old/cancelled schedule summary. It makes no history-list request and creates nothing just by opening.
- Editing from Calendar > Event Details > View / Edit Schedule restores only that actual record's fields and shows **Editing Schedule** with its facility, description, effective dates and status. The actual ID is retained, and the facility stays locked. Editing a later recurring occurrence retains the original effective date.
- The selected active edit summary retains **Cancel Schedule** as the existing cancellation operation, with confirmation and retained history. Footer Cancel simply closes the form; these are different operations.
- All existing fields and optional attachments remain. Only the existing class, official, maintenance, hold and other schedule types are accepted; Reservation/Assessment are excluded. No new Custom recurrence option or status field was invented.
- Successful Save Schedule closes the modal and shows **Facility schedule saved successfully.** through the existing toast. Calendar refreshes its current month/filters immediately. Reopening starts a fresh form. Booking-list pagination is not reset by a full-page reload.

### 4. How it works: functions, inputs/outputs, data flow

`resetSchedule()` has no input. It resets the HTML form, clears `bkBlockId`, unlocks facility selection, clears attachment/error text, hides and empties the edit summary, and reapplies existing conditional controls. It does not call a save API.

`editBlock(row)` accepts a real structured schedule event from Calendar. It fills the existing fields and ID, displays only that row's summary and wires its cancellation button to the existing protected update route. User-provided summary text is HTML-escaped. It does not infer dates or availability from free text or an attachment.

`refreshSchedule(message)` takes success text, closes the existing modal, dispatches the existing `campushub:calendar-refresh` event and calls the existing toast via `CampusHubBookings.notify`. On Calendar the event triggers a fresh authoritative GET with current filters. On Bookings there is no Calendar grid to refresh; later Add Reservation/mobile availability calls query the same saved source records.

Data flow: open new -> reset form -> complete fields -> existing schedule create API -> server validation/lock/conflict check -> one logical schedule saved -> existing audit -> success/close/Calendar reload. Edit uses the existing ID/update API rather than creating another record. Errors keep the form open with the entered data and re-enable Save Schedule.

Annotated example:

```javascript
resetSchedule(); // Clears UI state only; no database request.
// A real selected Calendar event arrives through the existing event listener.
editBlock(row);  // Retains row.id and the original effective-from date.
// The submit handler uses update when bkBlockId exists; otherwise create.
```

This approach separates create/edit UI state explicitly while reusing the existing form and authoritative backend workflow.

### 5. Backend / API behavior, validation and availability

Reuse `validate_schedule()`, `schedule_days()`, `save_schedule()`, `conflicting_bookings()` and existing RBAC. Date end defaults to start when blank; reversed ranges, zero/reversed times, missing Other description, invalid types/weekly days and invalid attachments are rejected server-side. Weekly recurrence is one saved rule with display/checking occurrences, not copied rows. All Day disables manual time inputs and uses the existing normalized full-day interval internally; Calendar still displays All Day, not artificial clock labels. Attachment formats stay PNG/JPEG/WebP/PDF, up to 1 MB, supporting evidence only.

Save still uses POST `/api/bookings/create/` with a non-reservation schedule type; edit/cancel still uses `/api/facility-schedules/<actual-id>/update/`. Server-side `can_manage_schedules`, physical-resource validation, facility locks, conflict detection and audit are preserved. Cancelled/rejected records are excluded by the shared availability checker and Calendar, and history remains stored. No second availability calculation or new customer booking workflow was introduced.

**Existing storage clarification:** this project has no separate FacilitySchedule model. Its existing schedule records share the `Booking` table and use an SC-prefixed ID plus `FacilityBookingRequest.details.source="schedule"` and structured schedule metadata. This cleanup preserves that architecture rather than adding a duplicate model. Therefore saving does insert/update a physical row in the shared table, but it is a logical schedule, not a customer Reservation: new schedules have no client, zero charge, no payment or job order, and are excluded from normal Booking Requests/KPIs. A literal requirement to never use the Booking table would require a separate coordinated data-model/availability migration, which this UI cleanup does not perform.

### 6. Database / migration impact

No schema/model/migration change or live record modification/seeding during implementation. Existing schedule storage and recurrence/audit history remain. The test fixtures use the isolated Django test database; browser POST requests are intercepted and never reach production.

### 7. Tests performed, troubleshooting and manual verification

- **70 targeted Django tests passed** for admin reservations/schedules, Calendar, booking transactions and mobile availability. Existing recurrence, edit/cancel/history, Other/all-day, attachment privacy, conflict and permission tests remain passing. Added assertions confirm the schedule success message and no customer/client/payment/job-order artifacts.
- One isolated browser export test also passed to export the actual schedule create response used by UI review.
- Reservation/schedule, Calendar and transaction reviews passed at **1440, 768, 390 and 320 px**. Checks include only two footer buttons, no New Block, no new-form history query, selected edit summary, ID/description reset on reopen, restored facility selection, conditional fields, modal fit, success-close/feedback and phone toast bounds. Phone schedule form was visually inspected.
- JavaScript syntax and changed tracked-file whitespace checks passed; Django system check clean; migration dry run: No changes detected. No claim of physical-phone deployment testing.

Manual checks:

1. Hard-refresh Bookings and open Manage Facility Schedule. Expect a blank form, no old/cancelled summary, and Cancel / Save Schedule.
2. Close/reopen after filling fields, without saving. Prior field values must clear and no record should have been created.
3. Open an existing schedule through Calendar details. Only its summary should appear, with actual ID/effective range. Close, then open a new schedule: summary and ID must be cleared.
4. Try Other without its required specification, a reversed end date and reversed/identical times; the backend must reject invalid submissions. All Day disables clock inputs; Weekly reveals weekdays.
5. When intentionally creating a real schedule, save once, verify the exact success toast, correct Calendar event type and shared Admin/mobile unavailability. Do not create production test rows merely to practice the form.
6. If cancelling a real schedule is intended, use its edit summary's Cancel Schedule; verify history remains while availability and Calendar stop treating it as active.

Debugging: stale buttons usually mean cached form JavaScript/template; Ctrl+F5 and inspect asset version `20261013-schedule-form`. For a wrong edit summary, inspect the selected event ID and `bkBlockId`; do not create a new record as a workaround. Validation/conflict errors should stay visible in `bkScheduleResult`. A save does not appear on Calendar if its actual dates/facility/type are outside the current filter; inspect the source record and response before assuming failure.

Commands, from backend/core:

```powershell
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py test modules.facilities.test_admin_reservations modules.facilities.test_calendar modules.facilities.test_booking_workflow api.test_mobile_facility_booking --keepdb --noinput
# No migration needed. Optional isolated fixture export for browser review:
$env:BOOKING_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/admin-reservations'
venv/Scripts/python.exe manage.py test modules.facilities.test_admin_reservations modules.facilities.test_calendar modules.facilities.test_booking_workflow --keepdb --noinput
# From project root:
node scratch/admin-reservations/check.cjs
node scratch/admin-reservations/calendar-check.cjs
node scratch/admin-reservations/workflow-check.cjs
```

Safe practice: on a local branch, change the helper sentence in `booking_forms.html`, refresh, and confirm the footer still has only Cancel / Save Schedule. Open/close a new form and check Network: opening must not POST or load historical schedules. Revert the wording afterward. This teaches presentation edits and checking for unwanted data side effects without creating database records.

### 8. Remaining limitations

The existing shared Booking-table storage remains as explained above; no separate schedule model was added. Editing/cancelling is reached through Calendar event details rather than an unrelated historical list inside a new form. Recurrence remains Does not repeat / Weekly, with the existing one-year bound. Native clock inputs follow device locale. Calendar refresh is request-based, and already-open external mobile screens refresh through their existing API behavior, not a newly added push service.

## Bookings: remove Job Order controls and generated links (2026-10-13)

This supersedes earlier Job Order menu/tab instructions for physical Bookings. Historical records and Laboratory Service document requirements remain.

### 1. Cause / reason

Confirmed by inspection: the template declared a Job Order tab/panel, `showMoreActions()` rendered the API's `job_order` action, and `render()` displayed its saved data and generated links. Removing only a menu label would leave other controls available or an undefined label. The user requested removal from Bookings and Documents.

### 2. Exact files changed and current anchors

Paths are relative to project root; lines refer to this update's final source.

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 189 `bk-transaction-tabs`; 208 `bkPanelDocuments`; 225 scripts | Removed Job Order tab/panel; refreshed asset versions. |
| `backend/static/components/js/admin_bookings.js` | 282 `showMoreActions`; 286 `Object.hasOwn` | Removed Job Order label and filtered unsupported UI actions. |
| `backend/static/components/js/admin_booking_workflow.js` | 9 `titles`; 43 `render`; 68 document filter; 72 `load`; 93 `editor` | Removed Job Order renderer/editor/loading; filtered generated link and guarded stale actions. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 138 historical Job Order test; 299 export test | Template assertions alongside retained exports; isolated supporting-upload fixture. |
| `scratch/admin-reservations/workflow-check.cjs` | 55 menu assertion; 80 historical fixture check | Browser checks for removal, retained documents and stale-event handling. |
| `docs/facility-configuration.md` | this section | Implementation, learning and debugging guide. |
| `CAMPUSHUB_CONTEXT.md` | `Bookings Job Order UI removal` | Current presentation/data boundary. |

### 3. Changes made

Removed Create/View Job Order from the three-dot menu, its Details tab/panel, editor fields and generated Documents HTML/PDF links. Other tabs/actions and existing layout remain. The filter matches the generated endpoint, not the title: real supporting uploads named Job Order and audit history remain visible.

### 4. How it works: functions and data flow

`showMoreActions(trigger, booking)` receives an API row and outputs the visible menu. `Object.hasOwn(labels, action)` requires a supported UI label, excluding the legacy action without changing permissions.

`load(id, nextAction, kind)` fetches the existing detail API and clears only retained panels. `render()` receives real booking details/documents and updates those panels. It filters the document display list before building links, without mutating stored records. `editor(action, kind)` checks the supported titles map, so an old Job Order custom event cannot open a removed editor.

```javascript
documents.filter(doc =>
    !doc.url?.split('?')[0].endsWith('/documents/job-order/')
);
// Generated route: excluded; /attachments/<id>/ upload: retained.
// filter() returns a new display array. It does not delete records.
```

Flow: existing API -> supported menu -> existing Details modal -> actual documents -> filtered links. Payment/edit/inspection still use existing backend validators. Endpoint matching avoids hiding unrelated uploads that happen to share a title.

### 5. Backend / API behavior

No backend production code changed. Protected Job Order update/HTML/PDF endpoints remain compatible with history. RBAC, CSRF, payments, conflict checks and Services policies remain. UI removal does not revoke API permission; that would be a separate authorization change.

### 6. Database / migration impact

No model/field/migration change or live database write. Existing `FacilityBookingRequest.details.job_order`, documents and audit records remain. Fixtures use the isolated Django test database; browser POSTs are intercepted.

### 7. Tests performed, manual checks and debugging

- **70 targeted Django tests passed** for admin reservations, Calendar, booking workflow and mobile facility booking, including historical exports/privacy, permissions and updated template assertions. System check: no issues.
- **Chrome browser checks passed at 1440, 768, 390 and 320 px**: no Job Order menu/tab/panel/generated link, historical data retained, Booking Form PDF and same-title supporting upload retained, stale action ignored, payment/read-only workflows working, no JavaScript exceptions. Calendar 12-hour checks passed in the same harness.
- Changed JavaScript syntax and scoped tracked-file whitespace checks passed.

From `backend/core`:

```powershell
$env:BOOKING_REVIEW_DIR='C:/Users/leste/Desktop/CAMPUSHUB/scratch/admin-reservations'
venv/Scripts/python.exe manage.py test modules.facilities.test_admin_reservations modules.facilities.test_calendar modules.facilities.test_booking_workflow api.test_mobile_facility_booking --keepdb --noinput
# Then from project root:
node scratch/admin-reservations/workflow-check.cjs
```

Manual test: Ctrl+F5 Bookings; inspect three-dot menu, View Booking Details and Documents on a booking with historical Job Order data. Expect no generated Job Order controls, with Booking Form, Payment, uploads and Activity retained. Confirm read-only View still opens.

Debugging: stale controls usually indicate cached scripts; verify `20261013-booking-documents`. If Details fails, inspect Console/detail GET and ensure removed-panel lookups were not reintroduced. Historical audit text or a real uploaded document with that name is retained content, not the removed generated control.

Safe practice: on a local branch, trace one document's `url` from the API response into `render()` using DevTools. Predict whether the route passes the filter, then verify in Documents without submitting a form. This teaches API-to-UI data flow without changing records.

### 8. Remaining limitations

This is a Bookings UI change; protected historical APIs and Laboratory Service requirements remain. Supporting uploads/audits are not erased. Chrome tests simulate phone widths; no deployed physical-phone testing was claimed.

## Bookings menu shortcuts and shared green alerts - 2026-10-14

Inspection, Documents and Record Payment are removed from the three-dot dropdown at backend/static/components/js/admin_bookings.js:284. The existing Details tabs, protected APIs, records, payment and mandatory inspection workflow remain. Booking creation/edit/status/schedule success now appears in the shared top-right admin feedback component after actual API acceptance. This user explicitly requested pale-green success alerts across all web admin pages; failures stay amber/neutral. See [Shared admin action alerts](admin-action-alerts.md) for the full eight-part report, exact files/current lines/anchors, functions/data flow, testing, debugging and safe practice. No database/migration change or live test writes. Assets 20261014-shared-alerts / 20261014-booking-alerts; Ctrl+F5.

## Facilities list footer at the container bottom - 2026-10-14

### 1. Cause / reason

The existing `.facility-table-panel` has a 500px minimum height. Its footer previously followed the table in normal document flow, leaving unused card space below the count and pagination. The requested arrangement puts that space above the footer.

### 2. Exact files changed

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/static/facilities/css/facility_form_controls.css` | 168, `Keep the physical list footer` | Physical Facilities card uses a vertical flex layout; footer consumes remaining space above it. Pagination stays right aligned and wraps within the card. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 15, `20261014-facility-footer` | Updated stylesheet version so browsers request the new layout. Existing footer markup remains at 268, `facilityTableFooter`. |
| `CAMPUSHUB_CONTEXT.md` | Final Facilities footer paragraph | Records the requested arrangement and verification. |
| `docs/facility-configuration.md` | This section | Learning, debugging, and verification guide. |

### 3. Changes made

The result count stays on the left and page controls stay on the right at the bottom of the existing Facilities List card. Pagination can wrap on narrow screens. Selectors exclude `body.service-catalog`, so this change is limited to physical Facilities. The existing minimum height, table columns, filters, Recent Activities and horizontal table scrolling remain.

### 4. How it works

Django renders authorized facility records into existing table rows. Unchanged `applyFacilityFilters()` at template line 990 takes the search/category/status/mode filters and current page, hides nonmatching rows, writes the result count and calls `renderFacilityPagination()` at line 954. That function takes the matching row count and creates the existing page buttons. A button updates the current page and runs the same filter function. No-results filtering hides the footer.

CSS then lays out the resulting elements: `display: flex; flex-direction: column` stacks the card contents; `margin-top: auto` on the footer absorbs unused vertical space. This avoids absolute positioning, which could overlap taller tables. The footer is already outside `.table-responsive`, so horizontal table scrolling cannot move the count or buttons. Pagination's `max-width: 100%`, wrapping and end alignment keep buttons within the available width.

Annotated example: with two matched records, existing JavaScript produces `Showing 1 to 2 of 2 facilities`. The CSS changes its position only; it does not change the number 2 or create records.

### 5. Backend / API behavior

No backend or API changes. Existing authorization, filtering inputs, five-row pagination and facility data remain in use.

### 6. Database / migration impact

None. No model, migration, live record, booking or stock changes. Browser checks cloned fixture rows only inside an isolated browser page; no data was saved.

### 7. Tests performed and manual verification

Passed isolated Chrome layout checks at 1440, 768, 390 and 320px using `node scratch/facility-rental-config/footer-check.cjs`. Verified the footer touches the card bottom, two-row count, 12-row paging to page 3, filter reset to page 1, hidden no-results footer, independent horizontal table scrolling and no viewport overflow. Desktop screenshot was visually inspected. Django `manage.py check` found no issues; targeted `git diff --check` passed. No Django regression suite was run for this CSS-only layout change.

The first browser pass caught pagination overflowing the card at 320px with multiple pages. Wrapping fixes that confirmed layout issue; the final four-width run passed. A separate initial QA script reused a top-level variable name; that harness error was corrected without changing application logic.

Manual test: hard refresh Facilities with Ctrl+F5, check the count at the bottom-left and pagination at the bottom-right. Search for a real facility, then a nonexistent name; the latter should hide the footer. Clear search, navigate another page if available, and test a narrow browser window. Only the table should scroll horizontally.

Troubleshooting: if the footer still follows the rows, confirm the browser loaded `facility_form_controls.css?v=20261014-facility-footer`, inspect the card's computed `display: flex` and footer's `margin-top: auto`. If the count is incorrect, inspect filter inputs and `applyFacilityFilters()` rather than changing CSS. If there are no matches, a hidden footer is expected.

Safe practice exercise: in browser DevTools only, temporarily change the card's `min-height` from 500px to 600px. Predict that the footer moves down while rows stay near the top; verify visually, then refresh to discard the experiment. This demonstrates how auto margins distribute free space without editing saved records.

### 8. Remaining limitations

This is a container-bottom footer, not a fixed footer at the bottom of the browser window. Long lists/cards scroll normally. Phone-width checks used desktop Chrome emulation, not a physical phone. Services intentionally retains its existing layout.

## Booking Requests: full-width sections and single-line values - 2026-10-14

### 1. Cause / reason

Confirmed from the existing code and supplied screenshot: the Bookings branch used Bootstrap's `col-xl-9` table beside a `col-xl-3` Quick Actions card. Eleven columns shared that reduced space. The table also used fixed layout, percentage widths, and `overflow-wrap: anywhere`, which split booking IDs, dates and times across lines. Hidden overflow prevented useful scrolling at some desktop widths.

### 2. Exact files changed

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 14, `20261014-booking-list-layout`; 85, `bk-bookings-content`; 87, `bkQuickActionsTitle`; 110, `bk-booking-filter-field`; 139, `Booking requests table` | New section arrangement, labeled filters, keyboard-accessible table scroll region, asset version. |
| `backend/static/components/css/admin_booking.css` | 1448, `Full-width booking list` through the following responsive rules | Full-width layout, compact horizontal actions, filter grid, complete single-line table values, column alignment and responsive wrapping. |
| `docs/facility-configuration.md` | This section | Explanation, debugging and manual verification. |
| `CAMPUSHUB_CONTEXT.md` | Final Booking Requests layout paragraph | Preserve this arrangement for future work. |

### 3. Changes made

The page order is KPIs, Quick Actions, then the full-width Booking Requests card. Quick Actions remains compact, with its existing buttons on the right on wide screens and stacked on phones. The card contains its heading/description, Search / Booking Status / Facility labels above their controls, the existing eleven-column table, and pagination below it.

All normal table headers and values stay on a single line without shortening saved IDs or dates. Currency is right aligned with tabular numerals. Room/unit, payment status, booking status and actions are centered; descriptive columns are left aligned. Table text is 13px with 12px headers. Existing status colors, icons and three-dot menu are preserved. The honest empty state can wrap. The Calendar-only branch retains its previous layout.

### 4. How it works: functions, inputs, outputs and data flow

No application JavaScript functions were added or changed. Django renders the existing authorized booking JSON, filter values, facility options, KPI partial and permission flags. The template moves the existing `bkOpenReservationBtn` and `bkOpenUploadBtn` IDs rather than creating duplicate buttons. The same listeners continue to open the existing forms. The Quick Actions strip is omitted when neither existing permission permits an action.

Unchanged `loadBookingPage(page)` at `backend/static/components/js/admin_bookings.js:57` takes the page number and current search/status/facility/KPI controls, calls `GET /api/bookings/`, and receives authorized rows, totals and pagination flags. It accepts the latest request result, updates the existing KPI/row state, then calls `renderAllBookings()` at line 168. That function filters the available row data, escapes values and writes the same eleven cells or the existing empty message. Existing time formatting still converts display values to AM/PM; stored/API times remain unchanged.

The new CSS changes layout only: `minmax(0, 1fr)` lets the card shrink to the available viewport width; automatic table layout sizes columns from their actual contents. Scoped rules override the older percentage column widths. `white-space: nowrap` keeps cell text on one line. `overflow-x: auto` on the named, focusable table region makes complete wide values accessible without enlarging the whole page. Filters use three columns on desktop, search above two selects below 900px, and a single column below 620px.

Annotated example: a saved time range such as `7:00 AM â€“ 5:00 PM` keeps its complete text. The browser scrolls the table when that value and the other ten columns cannot fit; no booking time is changed to force a fit.

### 5. Backend / API behavior

Existing booking routes, pagination, permissions, status transitions, payment/inspection rules and database-derived values are unchanged. Calendar, reservation/schedule forms, shared alerts and transaction detail tabs still use their existing controllers and APIs. No fake booking records were added to the live database.

### 6. Database / migration impact

None. No model, migration, stock, payment or saved booking changes. Export tests use the isolated Django test database; browser requests are intercepted with exported test fixtures.

### 7. Tests performed and manual steps

- Two existing fixture/render tests passed: `AdminReservationTests.test_export_browser_fixtures` and `BookingWorkflowTests.test_export_transaction_review`, with `BOOKING_REVIEW_DIR` pointing to `scratch/admin-reservations` and `--keepdb --noinput`.
- `node scratch/admin-reservations/workflow-check.cjs` passed at 1920, 1440, 768, 390 and 320px. Checks cover full-width action/list ordering, unique buttons, visible filter labels, all eleven columns, single-line values, keyboard-focusable internal scrolling, contained page width, existing KPI/filter results, three-dot actions, details, payment, read-only workflow and Calendar time formatting. The final run followed the CSS specificity adjustment that prevents older column-width rules from winning.
- `node scratch/admin-reservations/check.cjs` passed at 1440, 768, 390 and 320px, retaining reservation availability/quote checks, automatic creation, saved slip, schedule form and shared success-alert behavior.
- Django `manage.py check` found no issues; scoped `git diff --check` passed. The desktop layout screenshot was visually inspected. Full backend regression suites were not repeated for this presentation-only change.

Manual steps: Ctrl+F5 on Bookings; confirm KPIs remain above Quick Actions and the table takes the full width. Check the complete booking ID, requester, facility, date, AM/PM time, cost and submitted date on one line. Search and select a status/facility, then reset them and check pagination. On a narrow window, focus the table region and scroll right to Actions; open the three-dot menu and View Booking Details. Check Add Reservation and Manage Facility Schedule still open their existing forms. Visit Calendar to verify its layout remains intact. Use a test environment for any save/payment action.

Troubleshooting: check the loaded CSS query version is `20261014-booking-list-layout`. If text still wraps, inspect computed `white-space`, `overflow-wrap` and `table-layout` inside `.bk-bookings-content`; rules from old cached CSS may be winning. If the page itself overflows, inspect the card's grid track and `.bk-bookings-table-wrap` scroll width, rather than hiding the entire page overflow. Missing Quick Actions can be expected for a view-only account; do not bypass permissions to make a button visible.

Safe practice exercise: in DevTools only, turn off `white-space: nowrap` on one date cell. Predict how the row height changes, then restore it. Next focus the scroll region and use the arrow keys to reach Actions. Refresh to discard the temporary experiment. This teaches the difference between data formatting and browser layout without editing a booking.

### 8. Remaining limitations

A wide eleven-column table requires internal horizontal scrolling at smaller widths or with long real names/IDs. Values remain complete rather than being truncated. Phone-width browser checks are not physical-device tests. The isolated screenshots do not load every live profile/logo image; those assets were outside this change. The separate mobile connectivity question was not fixed by changing this web layout.

## Contextual Record Payment and external Official Receipt details - 2026-10-14

### 1. Cause / reason

The backend already had safe facility payment recording and a Payment tab editor. A previous explicit request removed Record Payment and Job Order from the table menu. The latest request supersedes that presentation decision: restore contextual Record Payment, Job Order where the existing workflow permits it, and read-only payment/document/history destinations. No unsafe Mark Paid or Set Paid action was found in the current booking controllers/templates.

The existing amount validator allowed zero because it also serves other nonnegative monetary values. Payment recording now adds a dedicated greater-than-zero check, without changing the shared validator's behavior elsewhere. The editor lacked the authenticated recorder display and the Payment tab did not link the private receipt attachment.

### 2. Exact files changed and anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/static/components/js/admin_bookings.js` | 284, `const labels`; 302, `const order` | Contextual menu, Record Payment, Payment Details and existing tab destinations; no Inspection mutation shortcut. |
| `backend/static/components/js/admin_booking_workflow.js` | 62, `bkPanelPayment`; 65, `bkTabJobOrder`; 90, `destinations`; 103, `function editor`; 116, `Record the Official Receipt`; 167, `await load(bookingId` | Recorder, actual quote breakdown, positive amount input, receipt link, applicable Job Order tab/editor, direct read navigation and refreshed Payment Details. |
| `backend/core/modules/facilities/services/booking_workflow.py` | 247, `if amount <= 0` | Reject zero recorded payments; reuse all existing state/payment/OR/date/permission/lock logic. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 111, `payments = []`; 119, `receipt_attachment`; 125, `recording_user`; 174, `Payment recorded successfully` | Safe receipt metadata/private link, authenticated recorder, exact payment success message. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 198, `bkTabJobOrder`; 213, `bkPanelJobOrder`; 233/236, `20261014-booking-payment` | Conditional Job Order tab/panel and updated main/workflow JS assets. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 137, `test_job_order_is_structured_and_updates_one_record`; 299, `test_payment_positive_amount_required_and_terminal_states_rejected`; 318, `test_payment_recorder_and_private_receipt_details_are_authoritative`; 345, `test_cashier_permission_is_independent_of_manage_and_approve`; 358, `test_accommodation_payment_uses_saved_quote_including_deposit` | Current UI expectation plus payment validation, private proof, authoritative actor, independent permission and accommodation tests. Existing fixture export now includes a real test receipt attachment. |
| `docs/facility-configuration.md` | This section | Implementation report, functions/data flow, test results, debugging and practice. |
| `CAMPUSHUB_CONTEXT.md` | Final contextual payment paragraph | Preserve latest decisions and remaining limitations. |

Unchanged models reused: `backend/core/api/models.py:521` Booking, line 578 FacilityBookingRequest and line 592 FacilityPayment. No duplicate Booking, Payment, OR or audit model.

### 3. Changes made: contextual actions and fields

| Current state | Menu behavior |
| --- | --- |
| Pending Approval | View Booking; Approve/Reject/Edit/Cancel only when existing permissions permit. No Record Payment or Job Order shortcut. Existing request-stage Job Order support can remain inside Details if configured. |
| Approved + Unpaid | View Booking; View/Create Job Order when existing action permits or view saved Job Order; Record Payment with payment permission; permitted Edit/Cancel. |
| Paid / Reserved / Confirmed | View Booking, Payment Details, applicable Job Order, Booking Slip, Documents and permitted Cancel/Complete. No repeat Record Payment. Completion still validates end time and required inspections. |
| Completed | View Booking, Payment Details, saved Job Order if present, Booking Slip, Documents and Activity. |
| Rejected / Cancelled | View Booking and Activity. No payment recording. |

Read-only shortcuts open existing Details tabs, never new pages or write endpoints. Controls continue to use server-supplied allowed actions. The full-width table and separate payment/booking columns are retained.

Record Payment opens the existing booking modal with a Record Payment title and proper form: Cash Payment Method (read-only), Amount Due (read-only), Amount Paid, Official Receipt No., Date Paid, authenticated Recorded / Verified By (read-only), optional Notes, optional Receipt Attachment, Cancel and Confirm Payment. Amount Paid starts at the actual outstanding amount; it is never a hardcoded price. Date Paid uses current local date/time, not the reservation date. The form explains that the Cashiering/authorized collecting office issues the OR and CampusHub only records it.

The existing saved quote is displayed separately as Base Rental/Accommodation, Discount, Additional Fees, Rental/Accommodation Total and Damage Deposit when those keys are present. No stay duration, guest count, rate or total is recalculated in the payment editor. The Payment tab shows existing status, amount due/paid, method, OR, paid date/time, actual saved recorder, notes and a private attachment link, or Not attached. Job Order uses the existing structured sidecar and existing authorized create/update/document routes; it does not issue an OR.

### 4. How it works: functions, inputs, outputs and data flow

1. `booking_row()` and `allowed_actions()` in the existing workflow service derive payment amounts and allowed mutations from real Booking/FacilityPayment records and permission codes. `showMoreActions()` in admin_bookings.js consumes these rows, chooses state-appropriate items and routes their clicks through the existing `openBookingDetails()` events.
2. `detail(request, booking_id)` requires existing read access and looks up a physical booking, excluding service transactions and schedule blocks. It returns booking state, sanitized sidecar details, payments, permitted actions, documents and history. The additive `recording_user` comes from `actor(request.user)` only for someone with the existing payment permission. `receipt_attachment` contains the safe name and existing protected URL, never embedded file bytes.
3. The workflow controller's `load(id, nextAction)` fetches that detail and `render()` writes escaped values into the existing tabs. A read destination selects its tab; a mutation goes to `editor(action)`, which checks the freshly retrieved allowed actions before constructing the form.
4. `submit()` sends the same JSON POST to `/api/bookings/<id>/update/`, with CSRF and session credentials. FileReader supplies bounded optional evidence. Browser read-only controls are convenience only: the server ignores submitted Amount Due/recorder as authorities.
5. `update()` checks `can_record_facility_payment`, locks Facility then Booking inside a transaction and calls `transition()`. `transition()` rechecks current state/actions, positive finite money with at most two decimals, Cash, full outstanding amount, OR and payment date/time. It creates the existing FacilityPayment, saves method/actor/notes/evidence under existing `payment_records`, and emits the existing audit event. A failure rolls the transaction back.
6. The accepted response returns the refreshed booking and `Payment recorded successfully.` Existing UI events update the table and reload authoritative KPIs/pagination; Details reloads directly into Payment Details. Shared pale-green success alerts appear after acceptance. No manual page reload is required after recording payment.

Formulas reused:

```python
paid = sum(valid_paid_payment.paid_amount)  # Existing FacilityPayment rows.
due = max(booking.total_amount - paid, 0)  # Server calculation, never form input.
# Normal recording requires amount > 0 AND amount == due.
# An approved booking with sufficient recorded paid amounts displays Reserved / Confirmed.
```

This preserves stored `Booking.status='approved'`; Reserved / Confirmed is the existing derived label. Payment remains in FacilityPayment, not a new combined status field. Required inspections still gate completion. Historical partially recorded payments, if already present, retain the existing sum/outstanding calculation; this change adds no partial-payment UI or new installment architecture.

### 5. Backend / API, OR, RBAC and audit behavior

The existing permission is `accounts.can_record_facility_payment`, independent of role-name matching, booking management or approval. Super/Facilities users need their existing grants; a custom authorized cashier can record without gaining Cancel/Approve. Unauthorized users get 403; unauthenticated access gets 401. CSRF protection remains. A nonexistent booking is 404. Pending, rejected, cancelled, completed and fully paid bookings reject normal payment recording.

Existing full-payment validation rejects partial/overpayments, negative/nonfinite/overprecision amounts, blank OR, missing/invalid/future date/time, unsupported method and payment dates before submission. New zero-payment rejection also applies when the quote is zero. Forged Amount Due/recorder fields do not override the server total/current actor.

Duplicate protection is reused: same-booking locks serialize changes, fully paid state blocks retries, and a case-insensitive paid-OR check rejects an OR already in use. Existing PostgreSQL transaction advisory locks serialize the same OR across facilities. No new uniqueness field/table was created and no new concurrency stress test is claimed.

OR number/paid amount/paid time are structured existing FacilityPayment fields. Cash method, current actor ID/name, notes and bounded supporting evidence use the existing FacilityBookingRequest JSON sidecar because FacilityPayment has no method/recorder/attachment columns. The saved actor ID is a reference snapshot, not a newly added foreign key. Authorized receipt downloads use `/api/bookings/<id>/attachments/<payment-id>/`, private/no-store and nosniff. Existing PDF/PNG/JPEG/WEBP content validation and 1MB limit remain. CampusHub neither generates nor issues Official Receipts.

Existing AccountActivity records `facility_payment_recorded` and `booking_reserved` inside the same transaction with actor, time, booking/facility references and success result. No duplicate audit system or redundant new OR audit stream was added. Job Order audits remain `job_order_created`/`job_order_updated` in the same log.

### 6. Database / migration and compatibility

No migrations or schema changes; `makemigrations --check --dry-run` reported No changes detected. Existing payment/booking records are not rewritten. Existing paid rows with incomplete historical evidence display Not recorded rather than inventing metadata. Booking creation, manual auto-approval, mobile pending approval, saved slot/stay quote, room inventory, completion gates and report routes remain in their current architecture. No Flutter/FastAPI changes or production test bookings/payments.

### 7. Tests, commands, debugging and practice

Passed **74 unique focused Django tests across runs**: a 72-test booking/workflow/reservation/Calendar/mobile suite followed by the two new custom-cashier/accommodation tests. The existing fixture export was rerun successfully after adding test receipt evidence; it is not counted as an additional unique test. Four new test methods cover invalid/zero money and terminal states, current actor/private receipt/forged inputs, independent cashier permission, and room-stay quote/deposit preservation. The old Job Order absence assertions were updated to the latest explicit requirement; existing create/update/permissions/document tests remain.

`node scratch/admin-reservations/workflow-check.cjs` passed five Chrome widths (1920/1440/768/390/320), including direct contextual Record Payment, required OR, positive amount input, read-only current recorder/due, modal/table bounds, paid refresh, Payment Details shortcut, receipt link, applicable Job Order/editor/documents, read-only destinations, deep links and Calendar AM/PM. `payment-state-check.cjs` passed seven local menu scenarios: Pending, Approved/Unpaid, Approved/Paid, Completed, Rejected, Cancelled and view-only Unpaid. It also checks that stale payment actions do not expose Record Payment in pending/terminal/paid states. Browser POSTs are intercepted; no live payments were made. Phone-width payment screenshot was visually inspected. Both application JS files passed `node --check`; Django system check was clean and scoped whitespace checks passed.

No migration command is needed. For development, run the existing server from `backend/core`, then Ctrl+F5 on Bookings to load `20261014-booking-payment`. To rerun the backend coverage:

```powershell
cd C:\Users\leste\Desktop\CAMPUSHUB\backend\core
venv\Scripts\python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
```

Manual test in an isolated test environment: create an authorized admin reservation and confirm Approved + Unpaid immediately shows Record Payment without a second approval. Enter the real test cashier OR, full due amount and payment date; confirm Paid + Reserved / Confirmed, updated KPIs, success toast and Payment Details. Try missing OR/date, partial/overpayment and a repeat payment; each must fail. Use a view-only or ungranted custom account to verify no recording option and backend 403. Test a mobile-created Pending booking, approve it with an authorized account, then record its payment. Repeat for a room stay and compare its saved quote/deposit before/after. Review a saved Job Order and private receipt without altering records.

Troubleshooting: a missing Record Payment can be correct for Pending/terminal/fully paid state or a missing payment grant. Inspect returned `booking.actions` and real payment status before changing role grants. If the table menu is stale, verify both JS cache versions and use Ctrl+F5. If the recorder reads Not recorded, inspect `recording_user` and the current grant; do not type a replacement administrator name. An invalid OR/amount/date error is a backend rejection, not a reason to bypass validation. A paid historical row without evidence needs an authorized correction workflow, not fabricated date/OR/actor values.

Safe practice: on a local test branch, add an invalid-amount case such as `2000.001` to `test_payment_positive_amount_required_and_terminal_states_rejected`, predict HTTP 400 and zero payment rows, then run that single test. Next trace the response `payment_status` into the table badge and `status_label` into the Booking Status cell. This teaches backend validation and API-to-UI data flow without editing live payments.

### 8. Remaining limitations and requested report checklist

Existing FacilityPayment choices are Unpaid/Paid/Failed; there is no refund architecture/status. Refunded, online gateways and refund accounting were not invented. Zero-cost bookings cannot use this positive-payment form; no free-waiver workflow was requested. Damage deposit stays distinct in the saved/displayed quote, while the existing revenue helper still sums recorded collections including deposits; this task does not redesign that accounting/report behavior. Physical phone/deployed testing and a new concurrency stress test were not performed.

Requested 19-point report mapping: (1-3) file/line/anchor table above; (4-5) existing FacilityPayment/Booking models reused; (6) contextual Record Payment restored; (7) no Mark Paid found; (8) modal field list in Section 3; (9) positive amount added and existing validation reused; (10) separate Paid/derived Reserved mapping; (11) existing lock/state/OR duplicate guards; (12) external OR recording only; (13) existing permission code; (14) existing audit; (15) Payment tab/private receipt refresh; (16) mobile/manual and room tests; (17) no migration; (18) actual test results above; (19) existing server + hard refresh, optional test command above.

## Booking footer: Showing range and numbered arrow controls - 2026-10-14

### 1. Cause / reason

The existing footer said Page 1 of 1 and used Previous/Next text buttons. It also always used the plural booking requests for a total of one. The latest request changes this presentation to a Showing range and numbered pages between left/right arrows, using actual server pagination.

### 2. Exact files changed

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/booking_workflow_views.py` | 57, `start_index` / `end_index` | Return the existing Django Paginator's real row indices. |
| `backend/core/accounts/views.py` | 1130, `booking_start` / `booking_end` | Pass those same indices into the initial page context. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 162, `bkPageSummary`; 164-166, existing arrow IDs and `bkPageNumbers`; 14/240, `20261014-booking-pagination` | Showing wording, singular/plural, accessible arrow labels, numbered-button seed and asset versions. |
| `backend/static/components/js/admin_bookings.js` | 57, `renderBookingPagination`; 81, page-number click listener; 85, existing `loadBookingPage`; 98, pagination refresh | Build numbered controls and update range/current page after real API results. |
| `backend/static/components/css/admin_booking.css` | 1540, `bk-pagination-controls`; 1547, `bk-page-button` | Compact navy/white round controls, active page, focus/disabled states, phone wrapping and 44px phone targets. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 270, `test_kpi_filter_preserves_search_facility_and_pagination` | Verify real second-page, filtered single result and empty row indices. |
| `docs/facility-configuration.md`, `CAMPUSHUB_CONTEXT.md` | This section / final pagination paragraph | Learning and verification notes. |

### 3. Changes made

One record shows `Showing 1 to 1 of 1 booking request` with `â€¹ 1 â€º`. Two records show `Showing 1 to 2 of 2 booking requests`. A real second page can show `Showing 21 to 24 of 24 booking requests` with page 2 active. Empty results show `Showing 0 to 0 of 0 booking requests`; both arrows are disabled.

Previous/Next words were removed from visible buttons. Their accessible names remain Previous page / Next page for assistive technology. Current page uses navy/white and `aria-current="page"`. Footer count remains left and controls right, wrapping inside the card when space is limited. Large page sets use first/last/current/neighbor numbers and ellipses rather than hundreds of buttons.

### 4. Functions, inputs/outputs and data flow

`list_data(params, user)` already filters authorized bookings and constructs `Paginator(records, 20)`. Its selected Page supplies `start_index()` and `end_index()`, so the frontend does not copy the backend's page-size calculation. Those integers are added to the existing response. `admin_bookings_page()` passes them into initial context; the template produces the correct summary even before JavaScript runs.

`renderBookingPagination(data)` takes the real total, row indices and navigation flags, using current page/page-count state. It writes the singular/plural summary with textContent, builds at most five numeric buttons plus needed ellipses, sets the active page and disables boundary arrows. It runs once from server-rendered data attributes and again after accepted `loadBookingPage(page)` results. The latter still preserves search, status, facility and selected KPI in the same GET request; existing request revision protection remains.

The page-number click listener passes that button's page to `loadBookingPage()` and ignores a click on the current page. Existing arrow IDs/listeners stay in place, so their navigation behavior is reused. The CSS page-number wrapper uses display: contents so its button children participate in the footer's existing wrapping layout; the wrapper has no separate semantic role.

Annotated example: with 24 matching records and page 2, Django returns start_index 21 and end_index 24. The renderer formats those values directly, producing `Showing 21 to 24 of 24 booking requests`. No new booking rows or fake counts are created.

### 5. Backend / API behavior

Only additive read-response/context fields were introduced. Existing page size, filters, permissions, booking/payment mutations, mobile behavior and row sorting remain. No new endpoint, duplicate pagination backend, payment action or audit event was added for page changes.

### 6. Database / migration impact

None. No models/migrations or live booking/payment changes. Browser pagination scenarios use intercepted responses in a local fixture page, not database inserts.

### 7. Verification, manual steps, debugging and practice

Three existing Django tests passed across the final successful runs: two fixture/render exports and the enhanced real paginator/filter test. The first invocation mistyped the paginator test method name; the actual method was then run successfully. This was a command selection error, not an application failure.

`node scratch/admin-reservations/pagination-check.cjs` passed at 1440, 768, 390 and 320px: initial singular count, visible arrow/number text, current-page ARIA, numbered page GET, next/previous, last page, bounded number window, empty result and contained phone layout. The phone-width footer was visually inspected after making screenshot scrolling immediate. The existing booking/payment workflow harness also passed five widths, including paid refresh, menus, details and Calendar. JavaScript syntax, Django system check and scoped whitespace checks passed. No full Django suite was repeated for this pagination change.

Manual steps: Ctrl+F5 on Bookings, check Showing wording and `â€¹ 1 â€º` for your current record. With actual multiple pages, click a number and each arrow and confirm row range/current highlight. Apply search/status/facility/KPI filters; they should still reset to page 1. Search a nonexistent name and confirm zero range/disabled arrows. On a narrow window, controls must wrap inside the card. Keyboard users can focus the arrow/number buttons and hear their page labels.

Troubleshooting: verify main JS and CSS use `20261014-booking-pagination`. If the count is wrong, inspect GET /api/bookings/ row indices/total and active filters; do not hardcode 1 or 2 in the template. Missing indices can indicate an old running server response or old exported fixture. If no second page exists, a disabled right arrow is expected. For a very large result set, omitted page numbers are represented by ellipses; first/last and current neighbors remain reachable.

Safe practice: on a local test branch, inspect the paginator test's 24 records. Predict the row indices for page 2, then run `test_kpi_filter_preserves_search_facility_and_pagination` to verify 21-24. In DevTools, inspect `aria-current="page"` on the current numeric button. This connects backend indices with visible pagination without editing live records.

### 8. Remaining limitations

Multiple controls can wrap on narrow phone layouts; the table retains its independent horizontal scroll. Phone-width checks used Chrome emulation rather than a physical device. The existing development server must reload the updated Python context/response code, and cached browser assets need a hard refresh.

## Payment datetime-local: Philippine timezone and black action dots - 2026-10-14

### 1. Root cause / reason

Confirmed: `core/settings.py` used `TIME_ZONE='UTC'`, while the Record Payment form sent the datetime-local input unchanged. That input has no timezone offset. The shared `timestamp()` helper made naive input aware using the active/default Django timezone. Thus October 14 at 13:00 Philippine local time could be treated as 13:00 UTC (21:00 Manila), producing a false future rejection.

The previous frontend default also depended on the browser timezone, so a browser outside the Philippines could populate a different local clock. A generic parse/future error message obscured the difference between malformed input and a future instant. A separate before-booking-submission date restriction could reject an external receipt recorded before manual booking entry; the user explicitly required past/current payment times to be accepted, so that date-only restriction was removed.

### 2. Exact files changed

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/core/settings.py` | 200, `TIME_ZONE`; 204, unchanged `USE_TZ` | Default Asia/Manila; timezone-aware storage remains enabled. |
| `backend/core/modules/facilities/services/booking_workflow.py` | 166, `timestamp`; 264, `paid_at = timestamp` | Reuse one parser, interpret naive input in the CampusHub default, preserve explicit offsets, separate parse/future errors, exact payment future wording, remove before-submission date restriction. |
| `backend/static/components/js/admin_booking_workflow.js` | 7, `date`; 8, `localDateTime`; 120, Philippine-time help; 124, `paid_at`; 133/139, existing Job Order/inspection inputs | Replace browser-clock default with shared Philippine display/input formatter; reuse it for saved aware transaction timestamps. |
| `backend/static/components/css/admin_booking.css` | 1803, `color: #000000` inside `.bk-view-booking` | Booking three-dot action uses black; its SVG already inherits currentColor. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 14/243, `20261014-booking-timezone` | Refresh changed CSS/workflow JS assets. Main booking pagination JS remains its existing version. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 363, `test_payment_philippine_past_current_future_times`; 383, `test_shared_timestamp_preserves_offsets_and_uses_campus_default` | Frozen-clock past/current/future payment endpoint tests, UTC/+08:00 equivalence, activated-zone independence and malformed input test. |
| `docs/facility-configuration.md`, `CAMPUSHUB_CONTEXT.md` | This section / final Philippine payment-time paragraph | Preserve cause, data flow, verification, debugging and practice. |

### 3. Changes made

CampusHub now defaults to Asia/Manila, with USE_TZ=True. Payment date/time at or before the server's current instant is accepted when the existing booking/amount/OR/permission requirements pass. A future payment date/time returns exactly `Payment date and time cannot be in the future.` A malformed date returns `Enter a valid payment date/time.` rather than incorrectly calling it future.

The form continues using datetime-local. Its default and displayed transaction dates explicitly use Philippine time even when the browser is set to UTC or another country. One shared frontend formatter replaces localNow; existing aware Job Order/inspection values reuse it rather than slicing an offset timestamp into a misleading local input. Booking/payment statuses, Cash/full-payment/OR fields, permissions, duplicate checks, audit events, quote and deposit calculations remain.

Only the Booking Requests three-dot icon color changes to black. Its existing menu, click handlers and contextual actions remain; other modules' action styling is outside this change.

### 4. Functions, inputs/outputs and data flow

`localDateTime(value=new Date())` takes a current/saved instant, formats it using Intl.DateTimeFormat with `timeZone: Asia/Manila` and 24-hour input fields, and returns a datetime-local string such as `2026-10-14T13:00`. It has no offset because that is the HTML input format. The visible helper tells the operator that the input means Philippine time. The existing `date(value)` display formatter also explicitly uses Asia/Manila.

`submit()` still sends that value as paid_at to the same protected update endpoint. The existing `timestamp(value, label, future_message=None)` parses ISO input once. If naive, it uses `timezone.get_default_timezone()` (now Manila) rather than a per-request activated zone. If already aware with Z/+08:00 or another explicit offset, it preserves the instant and does not attach another offset. It compares the resulting aware datetime to `timezone.now()`. Parse errors and future errors are separate paths. The optional message lets Payment use the requested wording without adding another date parser or changing other transition rules.

`transition()` retains all non-date payment checks and saves that aware instant to the existing FacilityPayment.paid_at. PostgreSQL/Django can store/return the same instant in UTC under USE_TZ; UTC storage is correct. Only interpreting an offset-free Philippine clock as UTC was wrong. A saved payment response is then displayed in Philippine time by the existing Payment tab.

Annotated example with a frozen clock:

| Input / current time | Actual UTC instant | Outcome |
| --- | --- | --- |
| Input Oct 14, 2026 13:00 Manila | 05:00 UTC | Accepted when now is 14:00 Manila / 06:00 UTC. |
| Input 14:00 Manila | 06:00 UTC | Accepted at the exact current time. |
| Input 14:01 Manila | 06:01 UTC | Rejected as future when now is 14:00 Manila. |

### 5. Backend / API behavior

Same authenticated, CSRF-protected payment endpoint and existing permission `can_record_facility_payment`. Pending/terminal/already-paid state, invalid/full amount and duplicate OR guards are unchanged. The only payment chronology rule now compares with the current time, per the user request; an otherwise valid older cashier receipt need not be later than the database Booking creation timestamp. No extra payment/status/OR records or fake success path were introduced.

Changing TIME_ZONE is a project-wide default, so existing local-date helpers and template display defaults now use Philippine time. Date-based reports were checked alongside booking workflows. Explicit-aware timestamps remain the same instants.

### 6. Database / migration impact and commands

No model/schema changes, migration or historical timestamp rewrite. `makemigrations --check --dry-run` reported No changes detected. No live booking/payment was submitted during verification.

Reload/restart the existing Django development server to apply settings, then Ctrl+F5 on Bookings for new browser assets. If restarting manually, stop the current development server with Ctrl+C before running the existing `venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000` from backend/core; do not start a second process on the occupied port. No migrate command is needed for this fix.

### 7. Tests, manual verification, debugging and practice

Passed 76 booking/workflow/reservation/Calendar/mobile tests, including two new datetime methods. A second run passed 77 checks covering dashboard periods, booking analytics, facility revenue, sales overview and the tightened shared-parser test. That parser test appears in both runs, so **152 unique Django tests passed**. The API tests freeze now at Oct 14 06:00 UTC / 14:00 Manila, accept local past/exact-current, reject future with exact wording, and confirm saved UTC instants. Helper tests cover naive local, explicit +08:00, Z and an activated UTC request zone, plus malformed text.

The final workflow browser harness passed five widths (1920/1440/768/390/320) with browser timezone overrides UTC, America/New_York and Asia/Manila. It independently checks the paid_at default against UTC+8, verifies black three-dot computed color, and retains contextual payment/paid refresh/permissions/detail/document/Calendar checks. Browser requests are intercepted; no live cashier payments. Application JS syntax, Django system checks, migration dry-run and scoped whitespace checks passed.

Manual test in an isolated environment: open an Approved/Unpaid booking with the correct permission, enter a real test OR/full amount and a past Philippine date/time, then confirm accepted Paid/Reserved output and the saved Payment tab date. Test a different booking with current time, then another with a future time and check the exact rejection. Set the browser timezone outside the Philippines; the default must still be Philippine time. Confirm action dots are black and other actions/statuses still behave normally.

Troubleshooting: check the actual running Django settings, not only the edited file: TIME_ZONE must be Asia/Manila and USE_TZ True. In DevTools, datetime-local submission should contain the intended Philippine clock with no Z appended by the form. Explicit Z means a UTC instant, not a Philippine local clock; do not add/remove offsets manually. Inspect an aware stored paid_at instant and convert with timezone.localtime before deciding whether it is wrong. If a valid time still looks future, inspect server/browser clock accuracy and current settings/cache versions. Bad state/OR/amount/permission errors remain valid rejections independent of time.

Safe practice: change only the frozen future test value from 14:01 to 14:00 on a local branch, predict acceptance at the exact frozen current instant, and update the expected result before running that test. Restore the original test afterward. Independently compute 13:00 Manila minus eight hours as 05:00 UTC and compare with saved paid_at. This teaches the difference between a wall-clock input and an aware instant without editing production data.

### 8. Remaining limitations

Existing timestamps that were previously recorded with the wrong interpretation are not shifted automatically; correction requires original receipt evidence. Server clock accuracy still matters. Phone-width/browser timezone checks are not a physical-phone/deployed verification. Asia/Manila is the CampusHub default across the project; this task does not redesign other modules' custom formatting or historical data.

## Automatic booking slip by Facility Category - 2026-10-14

### 1. Cause / reason

The project already had FORM_DEFAULTS and official form labels, but Add/Edit treated them as suggestions. Its manual Booking Form Type dropdown could override a Court/Hall with an accommodation/general form, and multiple booking/slip readers preferred the override. The new requirement makes known physical categories authoritative while preserving historical booking data and explicit Other configuration.

### 2. Exact files changed

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/rental_configuration.py` | 20 `booking_form_for_category`; 28 `booking_slip_label`; 130-135 form validation | Shared canonical mapping and historical snapshot-first labels; Add/Edit validator calls the same resolver. |
| `backend/core/modules/facilities/static/facilities/js/rental_form_controls.js` | 9 `formDisplay`; 84 `syncBookingForm`; 105 method; 126 saved form assignment | Read-only known form, automatic category changes, explicit Other choice and correct Edit loading. |
| `backend/core/modules/facilities/templates/facilities/partials/rental_rules.html` | 11-14 `facilityBookingFormDisplay` | Booking Form label/output/helper; legacy select remains hidden/disabled except Other. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 592 `20261014-auto-booking-slip` | Updated controller asset version. |
| `backend/core/modules/facilities/services/admin_reservations.py` | 14 import; 83 resolver | New admin quotes/bookings use the category's correct form label. |
| `backend/core/modules/facilities/admin_booking_views.py` | 73-75 options label; 203 import; 219 slip label | Same mapping for options and historical-safe View/Print title. Removed now-unused local config variable. |
| `backend/core/modules/facilities/mobile_views.py` | 168-170 resolver | Existing mobile booking creation snapshots the same correct label. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 193-194 slip label | PDF/print document title uses the same history-aware helper. |
| `backend/core/api/test_facility_rental_configuration.py` | 379 `test_mapped_categories_ignore_manual_booking_form_overrides`; 397 `test_other_keeps_explicit_form_and_historical_label_wins` | Known mappings, tampering, partial/category edits, Other and snapshot fallback. |
| `backend/core/modules/facilities/test_admin_reservations.py` | 126 `test_category_assigns_new_slip_and_saved_history_survives_reclassification` | New quote/detail/options label, saved-history preservation and real PDF response after category change. |
| `docs/facility-configuration.md`, `CAMPUSHUB_CONTEXT.md` | This section / final automatic slip paragraph | Learning, debugging, verification and current decisions. |

### 3. UI changes and category mapping

| Facility Category / stored code | Automatically assigned form |
| --- | --- |
| Court / Sports Facility (`covered_court`) | Facilities and Spaces Rental Booking Slip |
| Hall / Function Space (`function_hall`) | Facilities and Spaces Rental Booking Slip |
| Hostel / Room Accommodation (`hostel`) | Room Accommodation Booking Slip |
| Other (`other`) | Existing explicit Rental / Accommodation / Custom-General choice; required for a new Other facility. |

Known categories show a noneditable Booking Form output with `Automatically assigned based on Facility Category.` The official name wraps within existing form styling on phones. No selectable form dropdown is visible for these categories. Changing category in Add/Edit immediately replaces the label and compatibility value. The facility name is not used to infer the form: a Mock Hotel must use the Hostel/Room Accommodation category for the accommodation mapping.

Other retains the existing form choices because the category alone does not identify an official form. The label then targets the visible select and help explains the explicit choice. Existing saved Other choices are loaded. Existing View remains read-only. Category/pricing/mode/inspection disclosure rules remain the existing controls; no additional client slip entry screen is introduced.

### 4. Functions, inputs/outputs and data flow

`booking_form_for_category(facility_type, workflow=None)` takes the stored category code and existing workflow JSON, returns the canonical form code, or raises ValidationError for an invalid explicit Other form. It reuses FORM_DEFAULTS/FORM_TYPES rather than duplicating their mapping. The existing `validate_rental_options()` calls it when saving: known-category overrides, including mismatched/malformed manual values, are ignored and normalized to the category's code. Other still validates an explicit existing choice. Older unconfigured Other records retain the existing unrelated-partial-edit allowance; read fallback remains General where appropriate.

The existing backend form configuration sends `booking_form_defaults` and `booking_form_types` to the page. `FacilityRentalControls.syncBookingForm()` consumes that same map, writes the output and compatibility select value, toggles the select only for Other and adjusts required/disabled/helper/label state. `setWorkflow()` loads the automatic code for known categories before any saved override; Other loads its real saved choice. `getWorkflow()` still sends the existing `booking_form_type` key. The server is authoritative even if someone unhides the select or crafts a POST.

Admin `reservation_schedule()` and mobile booking creation call the shared resolver, and new quote data saves the resulting official `form_label`. The Booking Details API consumes the same saved quote. View/Print and PDF still read the saved Booking, client, schedule, guests, totals and sidecar data; the client does not fill another form manually.

`booking_slip_label(facility, quote=None, workflow_snapshot=None)` is the single historical presentation helper. It prefers: (1) the saved quote's form_label; (2) a valid saved workflow_snapshot.booking_form_type; (3) current category/config mapping when no saved form evidence exists. Invalid legacy configuration keeps the existing generic Booking Slip print fallback. It does not change any record or recalculate prices. Both existing HTML slip and PDF document title call this helper.

Annotated example: a Covered Court with an old saved `booking_form_type: accommodation` now resolves new reservations to `rental` and displays the Rental Booking Slip automatically. A previously saved booking with its own form_label keeps that label even if its facility is later reclassified. Saving the facility normalizes only its current configuration; it does not rewrite old booking snapshots.

### 5. Backend / API behavior

Existing Facility create/update APIs and permissions remain. They retain the same workflow_config field and enforce the canonical form mapping independently of JavaScript. Existing quote/options/mobile endpoints share the resolver. Existing View/Print/Export PDF and protected document routes remain; this task changes only the form choice/title resolution. Service catalog logic remains separate; no service is converted into a physical booking. Pricing, payment, approval, inspection gates, OR, user/client data and availability logic were not redesigned.

### 6. Database / migration impact

No new fields/models or migrations. workflow_config.booking_form_type remains for compatibility, as do booking quote/snapshot fields. Existing live facilities/bookings were not bulk rewritten and no example records were inserted. Individual authorized Facility saves normalize the current known-category value. Migration dry-run reported No changes detected.

### 7. Tests, manual steps, debugging and practice

124 focused Django tests passed across facility configuration, admin reservations, booking/payment workflows, mobile bookings and Services navigation. Three added methods cover automatic mapping/tampered overrides, Other/history priority, and real new-booking/details/HTML/PDF history behavior. Two targeted tests were rerun after the malformed-snapshot guard/detail assertion; all 32 validation tests passed after final shared-resolver integration. These reruns are not counted as extra unique tests.

Four existing full Add/Edit/View form browser runs passed at 1440/768/390/320px with updated expectations for locked known forms. Four additional `automatic-slip-check.cjs` runs passed Edit category switches Court/Hostel/Hall, hidden dropdown via computed CSS, actual read-only labels, Other requirement, saved Other/View behavior and contained phone title. Browser save requests are intercepted; real fixture records exist only in the test database. The phone-width automatic slip output was visually inspected. JS syntax, Django system check, scoped whitespace and migration dry-run checks passed.

Manual steps: reload Django if autoreload is disabled, then Ctrl+F5 on Facilities. Add/select Court and Hall: expect the Rental output with no form dropdown. Select Hostel: expect Accommodation. Edit an existing known-category facility with an old conflicting choice: display must still follow category. Switch its category before saving and check the label updates. For Other, select an applicable existing form and verify a missing choice prevents normal new save. Create a test reservation from saved real configuration in an isolated environment, then View/Print/Export PDF; check saved client/schedule/quote values and title. Reclassify the facility in the test environment and verify the previous booking's saved form remains. Check Services and payment/approval controls remain normal.

Troubleshooting: if a dropdown remains for Court/Hall/Hostel, check controller asset version `20261014-auto-booking-slip`, the actual stored category code and `syncBookingForm()`. A facility named Mock Hotel but categorized Other legitimately requires an explicit choice; fix the category rather than hardcoding names. If an old booking still uses its original form label, that is intentional history preservation. If a new quote is wrong, inspect the category/resolver before changing the booking record. Missing room/rate/availability configuration still needs its existing setup; assigning a form does not fabricate those values.

Safe practice: on a local test branch, add another supplied invalid form value to `test_mapped_categories_ignore_manual_booking_form_overrides`, predict canonical Rental/Accommodation output and run the validation class. Then inspect the browser's server-provided booking_form_defaults map and trace it into the read-only output. Use test data only; do not rewrite historical labels to make a display assertion pass.

### 8. Remaining limitations

Other requires an explicit choice for new facilities and retains legacy compatibility behavior. Historical bookings keep their saved form evidence; if no saved label/type exists, only current configuration is available for fallback. Browser phone widths are simulated, not physical-phone verification. No new official custom form, pricing workflow, room stock or approval process was added.

## Full-page Booking Details - 2026-10-14

### 1. Cause / reason

Booking Details had accumulated six workflow areas plus a separate Documents tab inside one modal. Scrolling, editing and document access now need a dedicated workspace. This change replaces the main detail modal with a page, while retaining the existing models, shared data, permission checks, private documents and small action forms. No production reservations or payments were created by verification.

### 2. Exact files changed and current anchors

| Folder / file | Approximate current line / nearby anchor | Change and reason |
| --- | --- | --- |
| `backend/core/core/urls.py` | 204 `admin_booking_details_page` | New named page route `/admin-bookings/<booking_id>/`; existing slip/API/PDF routes retained. |
| `backend/core/accounts/views.py` | 1121 `if request.GET.get('booking')` | Protected legacy list deep links redirect to the new page and preserve the existing per-tab authentication token. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 75 `documents_for`; 105 `detail_data`; 137 `detail`; 148 `detail_page` | Add file section metadata; reuse one detail payload for API and page; enforce existing read access and physical-booking lookup; private/no-store responses. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 22 `bkBookingDetailPage`; 33 tablist; 59 `bkBookingActionModal`; 68 `bkBookingDetailData` | New page, back link, ID/statuses, six accessible tabs, existing reservation editor include, small action modal and safe server JSON seed. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 177 `booking_forms.html`; 197-199 controller scripts | Entire old detail modal and its Documents tab removed; retain list/Calendar/forms, load workflow controller only on the detail page, refresh asset versions. |
| `backend/static/components/js/admin_bookings.js` | 120 `CampusHubBookings`; 241 `openBookingDetails`; 251-260 event handlers; 278 `showMoreActions` | Reuse shared modal/time/alert helpers; View/context actions navigate to page/tab/action with the current tab token. Stop trying to refresh list elements on the detail page. Remove separate Documents menu shortcut. |
| `backend/static/components/js/admin_booking_workflow.js` | 5 page guard; 32 `tab`; 57 `render`; 109 `load`; 130 `editor`; 181 `submit`; 204 seed | Existing transaction controller now fills a page, preserves its editors/actions and refreshes after accepted saves. Keep reload errors/Retry visible even after a successful write. |
| `backend/static/components/js/admin_booking_forms.js` | 244 `campushub:edit-reservation` | Remove obsolete detail-modal close call; existing reservation modal still loads the selected booking and performs the existing save flow. |
| `backend/static/components/js/admin_facility_calendar.js` | 44 `View Booking Details` | Calendar event detail link opens the same new page. Calendar event summary remains a small modal. |
| `backend/static/components/css/admin_booking.css` | 7 full-page workspace comment; 25 `bk-activity-scroll`; 29 `bk-action-dialog` | Scoped compact page/header/status/card styles, 44px tab targets, focus/skip-link support, phone wrapping and local activity-table scrolling. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 413 `test_full_detail_page_reuses_api_payload_and_protects_access`; 444 file grouping test; 469 token test; 487 fixture exporter | Verify shared payload, route/status/access, no main modal/Documents tab, real private document responses, tab authentication/CSRF and isolated browser fixtures. Existing Job Order rendering assertions now target the page. Tests assert that Django supplied a template context before indexing it, so missing context fails clearly and optional-context typing is narrowed. |
| `docs/facility-configuration.md`; `CAMPUSHUB_CONTEXT.md` | This section / final full-page paragraph | Current behavior, learning, debugging, checks and limitations. |

Browser review helpers are in `scratch/admin-reservations/detail-page-check.cjs` and the updated `calendar-check.cjs`. They use Django test-rendered fixtures and mocked requests, not application sample rows or live writes. Current lines above are anchors for this change; earlier dated sections document their earlier line positions.

### 3. Changes made / tabs and document handling

Bookings List -> three-dot menu -> View Booking Details now opens the page. Existing contextual actions open the relevant tab or a permitted small action dialog. Legacy `/admin-bookings/?booking=<id>` links redirect rather than opening a modal. Back to Bookings returns to the existing list route. No new list Eye button was added; the current three-dot design is preserved.

The page has Booking Details, Booking ID and separate Booking Status/Payment Status, followed by Overview, Booking Form, Job Order, Payment, Inspection and Activity. Tabs support arrows/Home/End, selected-state semantics and keyboard focus. Phone layout wraps tabs and stacks detail cells; wide activity data scrolls inside its own focusable region.

Overview shows real requester, facility, optional room/unit, source, dates/stay, applicable time, participants/guests, purpose/notes, approval actor/time, statuses and saved cost breakdown. Booking Form uses the existing historical-safe official form resolver and retains View/Print/Export PDF. Payment shows original due, paid amount, balance, status and existing records, method, OR, date, actor, notes and private receipt. Inspection retains configured/saved pre/post records, findings, personnel, date, damage, remarks, attachments and generated reports. Activity uses the existing audit records including actor, role, date/time and result; labels use the saved action code with fallback to existing action text.

There is no separate Documents tab. `documents_for()` adds a section to its existing flat list, so old API consumers still receive the list:

| Existing file source | Page section |
| --- | --- |
| Generated official reservation slip | Booking Form |
| Generated Job Order | Job Order |
| Generated pre/post inspection report and inspection attachment | Inspection, beside its pre/post record |
| Payment receipt attachment | Payment, beside the payment record |
| Legacy general supporting uploads without a typed workflow owner | Booking Form -> Supporting Documents |

Generic uploads keep their titles and protected URLs; filenames are not guessed into a workflow type. This avoids losing an older supporting upload named Job Order. Receipt links already shown in payment records are not duplicated in an extra file list.

Approve, Reject, Cancel, Complete, Record Payment and Record Inspection use the small action modal. Job Order completion/editing and supporting upload inputs are inline in the page. The existing Edit Reservation form remains a separate editor modal. The main Booking Details view never opens a modal.

### 4. How it works / functions and data flow

`detail_data(request, booking)` takes an already-authorized request and the selected booking, then returns the existing booking row, sanitized sidecar details, paid records, permitted actions, inspection personnel, documents and audit events. It does not perform a new payment or booking calculation. Both `detail()` (JSON API) and `detail_page()` (HTML page) call `read_access()` and the same `physical_bookings()` lookup before using this helper. The helper is shared to keep totals, permissions and tabs consistent rather than copying a second detail implementation.

The page stores that payload using Django `json_script`, which escapes unsafe HTML in stored text. The controller parses it, then `render()` writes escaped text into the appropriate panels. Initial rendering therefore does not need another detail GET. `tab(name)` closes an unsaved action editor, updates selected/tabindex values and exposes only its corresponding panel. Invalid tab names fall back to Overview.

`editor(action, kind)` consumes the API's allowed action list. It builds the existing inputs for a small dialog or inline editor; the Edit action dispatches the existing reservation-editor event. `submit()` validates fields/attachment size, calls the unchanged protected update endpoint, announces success only after acceptance, and reloads the detail endpoint. `load()` returns whether that refresh succeeded; a failed refresh leaves its real error and Retry button visible. Old actions cannot be submitted through this controller while refreshed data is unavailable.

For example, the server supplies a document like:

```python
# Additive presentation metadata; the existing private URL is unchanged.
{'title': 'Job Order', 'section': 'JobOrder', 'url': existing_private_url}
```

The browser filters the shared list by `section`, so that link appears in Job Order. The file itself remains served through the original permission-protected endpoint; adding a section does not grant access.

Job Order has no separate stored lifecycle field in the current sidecar. The UI derives its presentation label from existing data: missing required Service Requested -> Draft; populated field without an approval stamp -> Completed; populated field with the existing approved_by stamp -> Approved. A missing Job Order shows an honest empty state. This does not introduce a new independent Job Order approval workflow or permission. Existing backend validation/approval stamps remain unchanged.

### 5. Backend / API behavior, routes and RBAC

New: GET `/admin-bookings/<booking_id>/`, named `admin_booking_details_page`. Retained: GET `/api/bookings/<booking_id>/`, POST `/api/bookings/<booking_id>/update/`, `/admin-bookings/<booking_id>/slip/`, existing generated HTML/PDF and private attachment routes. Legacy `?booking=` redirects to the new named page, carrying `__at` when present. Frontend navigation uses the existing `CampusHubAdminSession.urlWithToken()` and the existing fetch wrapper for authenticated requests; back/file links use the existing shared link interceptor.

Existing `READ_PERMISSIONS`, `has_permission()`, `allowed_actions()`, `access()` and transition/locks/CSRF enforcement remain authoritative. A view-only user can read the page/files but receives no mutation controls. An ungranted admin is forbidden, an unauthenticated request unauthorized, and unknown/service/schedule-block IDs are excluded by the same physical-booking lookup. Permission-hidden controls are only presentation; the unchanged update API still rejects bypass attempts.

Additive API fields are `booking.booking_form_label`, `documents[].section`, inspection document `kind`, and `activity[].code`. Existing payload fields, status codes, payment logic, order of audit entries and last-50 audit limit remain. Private details are marked `Cache-Control: private, no-store`. Attachment bytes are not embedded in the detail payload.

### 6. Database / migration impact

No model, database field, stored status, migration, historical reservation rewrite or live record update. Booking, FacilityPayment, FacilityBookingRequest sidecar, quote/workflow snapshots and AccountActivity are reused. `manage.py makemigrations --check --dry-run` reported No changes detected. Do not run a migration for this UI change. Reload the existing Django process as needed and use Ctrl+F5 so the new `20261014-booking-detail-page` assets are loaded.

### 7. Tests, manual verification, debugging and practice

**Executed results:** 80 Django booking workflow/reservation/Calendar/mobile tests passed. The new tests verify page/API payload equality, all six tabs and removed markup, view-only/denied/logged-out responses, excluded service IDs, generated/private file responses, sanitized attachments, real per-tab authentication on page/API/legacy redirect and CSRF rejection without changing the booking. Existing payment, edit, approval and inspection transition tests passed. The fixture exporter was rerun after adding real Edit options/slot fixtures; that is a repeated test, not an additional unique test.

Chrome browser review passed four widths (1440, 768, 390, 320) for list-to-page navigation, real session-script token propagation, keyboard tabs, existing Edit prefill, Job Order inline editor, inspection evidence/editor, payment required OR/Philippine-time default, successful mocked payment refresh, cancellation reason dialog, Escape/Cancel, paid receipt/activity, read-only access and page bounds. The 320px case also simulates a failed detail reload after a successful payment and confirms Retry restores the page. Four Calendar browser cases passed filters/events/room times/empty/error/permissions and the new direct detail link. Browser requests were mocked with actual test fixtures; no real payments or production bookings were modified. Desktop/phone detail screenshots were visually inspected. Application JS syntax, Django system checks, migration dry-run and scoped Git whitespace checks passed.

Commands (from `backend/core` unless indicated):

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
# From the repository root, after exporting BOOKING_REVIEW_DIR fixtures:
node scratch/admin-reservations/detail-page-check.cjs
node scratch/admin-reservations/calendar-check.cjs
```

Manual checks in a test environment:

1. Open Bookings -> three-dot -> View Booking Details. Confirm the URL, normal page scrolling, back link, ID/statuses and six tabs; no main detail modal or Documents tab.
2. Open an old `?booking=<id>` link while signed in through a tab token. Confirm redirect and that the same authorized account remains active.
3. Check Court/Hall and accommodation records. Confirm correct official slip, optional room/guest/stay values, saved pricing and historical form behavior. Open View/Print and Export PDF.
4. Create/edit an applicable Job Order using real test fields; confirm existing document generation and its saved presentation label.
5. Record a test payment with the proper permission, real test OR and past/current Philippine time. Confirm balance/status/receipt and Activity update; duplicate/future/unauthorized requests must still fail.
6. Record permitted pre/post inspections with a test attachment; open the evidence and generated report from Inspection. Confirm completion prerequisites remain enforced.
7. Open a booking with older general uploads. Confirm every file is still accessible under Supporting Documents; payment/inspection files are in their own tabs.
8. Sign in with view-only and no-booking-access accounts, check actual routes, and test keyboard/phone-width layout. Only authorized actions may appear or succeed.
9. Simulate a failed detail GET after saving in an isolated browser test. Confirm actual success feedback plus the visible refresh error/Retry, rather than a false refreshed view.

Troubleshooting: a main modal still appearing usually means an old JS/template cache; inspect the script versions and hard refresh. A 403 is an access check, not necessarily a missing page: inspect the current account's real grants and tab token. A 404 may be an unknown ID, service request or schedule block intentionally excluded from physical booking details. A missing file should be checked in the response's documents list and section, then its original private endpoint; do not expose attachments publicly to fix access. A tab with no applicable records should have a truthful empty message. After a successful write plus refresh failure, use Retry before attempting another transaction; backend duplicate/state protection remains active.

Safe practice: on a local branch, open a test booking with `?tab=Payment`, then change only a nonfunctional tab helper sentence and its focused browser assertion. Verify it appears only on the detail page, keyboard selection still works and the API payload/totals are unchanged. Restore the wording afterward. Trace one private receipt from sidecar -> `detail_data()` -> Payment link -> protected attachment view, explaining each permission boundary before changing any code.

### 8. Remaining limitations

Verification uses isolated Django data and Chrome device widths, not a physical phone or deployed end-to-end cashier transaction. Existing Job Order stamps do not constitute a newly implemented independent approval lifecycle. Legacy untyped supporting uploads cannot be confidently reassigned by title and remain under Booking Form. Existing last-50 activity and authorized-personnel list bounds are retained. This task does not add refunds, new booking/payment statuses, new document storage, or a new Job Order approval permission. The Back link returns to the normal Bookings list; preserving an arbitrary list search/page in the URL is not added.

## Official digital booking slip inside Booking Details - 2026-10-14

### 1. Cause / reason and inspected references

The Booking Form tab showed only a title and links. The old standalone slip had a generic CampusHub header and omitted mobile event names, selected equipment, signatories and receipt details; the PDF used a separate flat generic table. The two pasted requests have identical SHA-256 hashes. The supplied photographs show the eight-section Facilities and Spaces Rental Booking Slip, including facility/equipment checkboxes and physical signature lines. They are layout references, not authority to prefill the staff names visible in surrounding photographed documents.

This update uses that official section structure with existing saved booking data, one shared read-only content helper and the existing protected document routes. The admin does not retype mobile data, and no second booking or slip record is created.

### 2. Exact files changed and current anchors

| Folder / file | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/booking_slip.py` (new) | 19 `local_stamp`; 32 `peso`; 43 `booking_slip_data`; 135 `slip_values` | Shared read-only document content, saved-field mapping, Philippine timestamps, real payment summary/receipts, category/equipment selections and recorded signatories. |
| `backend/core/modules/facilities/templates/facilities/partials/official_booking_slip.html` (new) | 1 `bk-official-slip`; 9 section loop; 11 signatory block | Institutional header, booking metadata, eight rental sections, accessible noninteractive choices and physical signature/date lines. Shared by embedded and standalone HTML. |
| `backend/core/modules/facilities/templates/facilities/pages/booking_slip.html` | 5 stylesheet; 7 `bk-slip-toolbar`; 8 shared include | Replace generic output with the shared document; only document actions/content on the standalone page. Keep shared tab-auth script for private links. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 14 `booking_slip.css`; 74 workflow script version | Load the shared document styles and refreshed controller. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 129 `slip_html`; 217 `document_values`; 264 `pdf_response`; 335 `document` | Detail payload adds escaped server-rendered preview; slip HTML and PDF consume shared data; extend existing ReportLab renderer with institutional sections. Job Order/inspection PDF branch remains unchanged. |
| `backend/core/modules/facilities/admin_booking_views.py` | 196 `booking_slip` | Delegate old print URL to the existing protected document view so HTML/PDF content and access do not diverge. |
| `backend/static/components/js/admin_booking_workflow.js` | 84 `officialDoc`; 85-88 Booking Form renderer | Form Status/booking origin, Print Booking Slip/Export PDF, full saved-data preview and existing Supporting Documents/actions. Refresh after accepted transactions uses the same preview field. |
| `backend/static/components/css/booking_slip.css` (new) | 2 document styles; 36 phone layout; 43 `@page`; 44 print rules | White/navy institutional paper, restrained borders, responsive fields/signatories, wide long-text fields, A4-only document printing and hidden surrounding dashboard/actions. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 487 mobile/role mapping test; 531 payments/escaping/access; 555 categories/accommodation/history | Actual mobile submission, saved-cost preservation, shared role output, PDF text, empty fields, private access, category checks, accommodation preservation and isolated review exports. |
| `backend/core/modules/facilities/test_admin_reservations.py` | 102 `test_saved_slip_is_prefilled_and_protected` | Assert real displayed formatted balances instead of the removed presentation-only context key. Failed payments still excluded. |
| `docs/facility-configuration.md`; `CAMPUSHUB_CONTEXT.md` | This section / final official slip paragraph | Mapping, learning/debugging, verified checks and current limits. |

The existing scratch `detail-page-check.cjs` now reviews the embedded official preview plus standalone/embedded print at four widths. Review HTML/JSON/PDF/PNG files are test fixtures under `scratch/admin-reservations`, not sample application data or client documents. No route declaration, model or migration file changed.

### 3. Booking Form tab changes and field mappings

The tab shows Booking Form, its historical-safe official slip title, Form Status: Generated, Generated from Booking: the actual ID, Print Booking Slip and Export PDF. Generated is a presentation state: rendering an existing booking produces a document, not a new saved transaction. Print opens the existing standalone printable document; its Print button invokes the browser print dialog. The complete slip is embedded below the actions. Supporting uploads remain accessible afterward.

| Slip value | Existing source / handling |
| --- | --- |
| Booking No.; Date Requested; Booking Status | Booking.pk, created_at rendered in Asia/Manila, existing booking_row status label. |
| Requestor name | Sidecar full_name, then existing requester display resolver. |
| Organization, address, phone, email | Existing sidecar fields; phone/email may fall back to the actual linked client profile. No invented address. |
| Event/activity name; purpose; participants | Sidecar event_name, purpose and attendees from mobile/admin; legacy purpose uses the existing row resolver. Missing event name stays Not recorded. |
| Facility and Court/Hall/Other selections | Current linked facility/category; its name comes from the existing serializer. Not inferred from a hardcoded name. |
| Event date, start/end and duration | Stored Booking date/time; existing 12-hour helper; duration from the positive stored time difference. No assumed operating duration. |
| Chairs/Tables/Sound System/Projector/Others | Only membership in saved additional_requirements; other_requirements and notes are the saved text. Configured facility amenities are not mistaken for requested equipment. |
| Base/additional/discount/rental/deposit | Existing saved quote keys, never the facility's latest rate. A missing historical key is Not recorded, not a fabricated zero. |
| Total amount; remaining balance | Stored Booking.total_amount and canonical booking_row/paid_summary balance. |
| Payment status; paid amount | Canonical paid_summary; only FacilityPayment.PAYMENT_PAID contributes. Partial payment still uses existing Unpaid status until full due is covered. |
| OR, receipt amount, date paid | Each existing paid FacilityPayment record's official_receipt_no, paid_amount and paid_at, in deterministic creation/ID order. Blank OR/date stays Not recorded; failed/unpaid records are excluded. |

Accommodation keeps Room Accommodation Booking Slip and actual check-in/out, optional configured saved clocks, room/unit, guests/adults/children and nights. It is not changed into the Court/Hall rental form. Other/custom bookings retain their existing title and applicable schedule content. Historical form titles remain governed by the previously implemented saved quote/workflow resolver.

### 4. Signatory/personnel mapping and how the functions work

Requested By uses the saved client printed name and actual linked account type/role when available; an external booking without a linked account is a Client. Approved By uses the existing approval.by snapshot, with the booking approval audit role when available and the existing admin's current role as a fallback. No individual name is hardcoded and no approval is performed by document rendering.

Inspection confirmed that Facility has no personnel-in-charge/reviewer assignment field. Therefore Reviewed By displays Not recorded with the Personnel In-charge role label. The creator, payment recorder and inspection personnel are not silently treated as reviewers. Requested/Reviewed/Approved blocks all preserve Signature / Date lines for physical signing. Printed names are not presented as digital signatures.

`booking_slip_data(booking, row=None)` takes a saved Booking and optionally its already-built booking row. It reads the existing sidecar and quote, then returns institutional labels, metadata, ordered sections/fields/choices and three signatories. Passing the row from detail_data avoids repeating the room/status/payment-summary serialization. It does not save, reprice, reserve stock, approve or modify records. `local_stamp()` accepts stored aware timestamps (or existing naive legacy values interpreted with the Campus default) and returns Philippine display text. `peso()` formats a recorded amount as PHP with grouping/two decimals; missing/nonfinite values produce Not recorded. Long fields receive a wide presentation flag; content is not truncated.

`slip_values()` flattens this structure only for the existing document-values compatibility interface. The current `pdf_response(..., slip=...)` instead lays out the same ordered sections, choices and signatories using the existing ReportLab exporter. Non-slip documents continue through its original generic branch. This extends the exporter rather than adding a second payment/slip content implementation.

The shared Django partial automatically escapes all client text. `detail_data()` renders it into the additive `booking_form_html` field. The page's json_script safely transports it and the existing controller inserts that server-generated markup. Stored script-like text remains visible as text. After payment/edit/approval succeeds, the normal detail refresh includes newly rendered slip content from the same records. No browser quote calculation or manual duplicate form is introduced.

Annotated example:

```python
# Existing saved mobile sidecar, shown here as an isolated learning example:
# details['additional_requirements'] == ['Chairs', 'Sound System']
# The helper turns membership into presentation choices, not new equipment data.
choice = {'label': 'Chairs', 'checked': 'Chairs' in details['additional_requirements']}
# The HTML partial shows a check and accessible Selected text;
# PDF uses [x] for the same boolean. No inventory/booking write happens here.
```

### 5. Backend/API, Print/PDF and RBAC behavior

Existing URLs are preserved: `/admin-bookings/<id>/slip/`, `/api/bookings/<id>/documents/slip/` and its `?format=pdf`, plus the full details route. The old print wrapper now delegates to `document()`, which reuses read_access and physical_bookings. No public attachment route, parallel slip table, permission bypass or new API endpoint. The detail API adds only `booking_form_html`; existing fields/statuses/private files and mutation workflows remain. Responses retain private/no-store.

Super Admin and Facilities Admin use the identical shared partial and content helper; tests compare their preview HTML. Any other existing role with booking read permission retains its existing read/print access. Mutation buttons remain governed by the unchanged allowed-actions API. Print/PDF do not grant a new approval, payment or digital-signature capability.

The standalone page contains only the document and its print/export actions. CSS hides actions on paper. Printing the embedded details page also reveals only the official slip, hides sidebar/header/tab navigation and supporting-action UI, removes dashboard viewport minimum heights, and keeps A4 margins. Both browser print paths and the existing ReportLab export were checked at A4 size. Normal rental and accommodation examples fit one page; lengthy notes can continue to further pages. Browser and ReportLab have different font metrics/checkmark rendering, but use the same section order and saved content. PDF uses PHP text to avoid missing currency-symbol glyphs in the existing built-in font.

### 6. Database / migration impact

No migration, model/threshold/status field, duplicate Booking/Payment/Job Order, historical repricing or production write. No new persisted slip record. One booking renders one current official slip from that booking and its payment history; exporting does not insert a copy in the database. `makemigrations --check --dry-run` reported No changes detected. Reload/hard-refresh the existing page for assets version `20261014-official-slip`; no migrate command is needed.

### 7. Tests performed, manual steps, debugging and learning practice

83 Django tests passed across booking workflow, admin reservations, Calendar and mobile booking. Three new meaningful methods cover an actual bearer-authenticated mobile booking -> slip, current-rate changes without saved-cost changes, Super/Facilities identical preview, receipt/approval roles, escaped script-like input, long PDF notes, view-only/logged-out access, Court/Hall selection, actual accommodation and missing legacy quote fields. Existing transitions, document routes, payment eligibility, CSRF and date/status checks passed. Four focused tests were rerun after reusing the already-built row and passed; repeated tests are not counted as additional unique tests.

Chrome review passed at 1440/768/390/320px: eight embedded rental sections, real mobile event/requester/selected requirements, physical lines, no editable slip inputs, correct links, viewport containment, existing tab/Edit/payment/inspection/read-only refresh behavior and post-payment document refresh. Standalone and embedded browser print were exported at all four widths; text checks confirmed the slip fields and absence of dashboard/actions, with standard output one A4 page on both paths. ReportLab normal rental and accommodation PDFs were one A4 page; a 350-word note example was two pages. PDF text and boundary checks plus rendered PNG inspection verified readable fields, selections, signatures and no clipping. Existing MuPDF/PyMuPDF rendered the files because Poppler was unavailable; pypdf checked extracted content. No live booking or cashier transaction was submitted by browser review. JS syntax, Django system check, migration dry-run and scoped whitespace checks passed.

Commands from backend/core:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
# Set BOOKING_REVIEW_DIR to the repository's scratch/admin-reservations path to export test fixtures.
# From the repository root:
node scratch/admin-reservations/detail-page-check.cjs
```

Manual checks in a test environment:

1. Submit a real test mobile Court/Hall booking with event name, contact info, time, requirements and notes. Open its Booking Details -> Booking Form as Facilities Admin, then Super Admin. Confirm identical saved content and selected choices without retyping.
2. Change the facility's current rate after booking. Confirm slip total/breakdown still match the saved booking quote. Missing legacy breakdown fields must not acquire a new quote.
3. Check Unpaid with no OR/date, then record a test payment through the existing authorized workflow. Confirm paid amount, OR/date, balance and approval data refresh in the embedded slip and export.
4. Open Print Booking Slip, use Print, and Export PDF. Also test Ctrl+P from Details. Confirm only the document, its header, sections and physical signature lines print; no sidebar/actions. Check long notes and phone-width preview.
5. Check a room-accommodation booking and an older unconfigured booking. Confirm correct preserved form title and honest missing values. Verify read-only and denied access at actual URLs.

Troubleshooting: a links-only tab usually means old controller assets; Ctrl+F5 and inspect `booking_form_html` in the authorized detail response. Missing mobile data should be traced to FacilityBookingRequest.details, not retyped into another slip record. A missing quote field means historical data was never recorded; investigate its original flow, do not recalculate at today's rate. A missing reviewer or logo is the confirmed absence described below, not an API failure. A second print page may be valid long content; for short examples inspect print CSS versions and scoped dashboard font/min-height overrides. Wrong dates require checking the aware paid_at/created_at instant and Asia/Manila formatting, not shifting database times. Role/403 errors should be checked against actual grants and per-tab token; never remove read_access to make the PDF work.

Safe practice: on a local branch, change one visible slip label in the helper (for example Contact Number capitalization), update a focused output assertion, then verify embedded HTML, print and PDF all use the same wording. Restore it afterward. Trace one requirement from Flutter payload -> mobile _details validation -> sidecar -> booking_slip_data -> partial/PDF checkbox, explaining why configured amenities and requested equipment must remain different. Never alter production receipt data for practice.

### 8. Remaining limitations / confirmed missing configuration

No official USTP logo asset was found in the application asset paths. Existing logos are CampusHub marks; the frontend file named logo.jpg is not a university logo. The university text header is used, with no invented seal or duplicated asset. The shared partial has a logo slot for a verified existing official asset, but it remains empty until that asset is supplied/identified.

There is no facility reviewer/personnel assignment field, so Reviewed By cannot be populated honestly. This change does not add assignment management or digital signatures. Mobile currently does not collect an address; older admin bookings may not have an event_name. Those gaps display Not recorded. Existing category choices use the current linked facility category because historical category/name snapshots are not available, while the official form title and pricing remain snapshot-based. The existing admin role fallback is current role if an approval-role audit snapshot is unavailable. Physical printer/deployed-mobile verification remains manual. No new official form code/revision, staff identity or legally approved digital-signature claim is invented from the reference photographs.

## Paper reference positions and left-aligned rental slip - 2026-10-14

### 1. Cause / reason

The previous preview was an A4-width block with horizontal auto margins, so a wide Booking Form panel left unnecessary empty space before it. Its field/signature grids also used two/three columns. The newly supplied photograph and request require the rental paper's vertical order, a left-positioned preview, a centered institutional header within the paper, and fewer official-paper fields. This section supersedes the earlier rental layout/accounting/signatory mapping; accommodation keeps its separate room/stay layout and data.

### 2. Exact files changed and current anchors

| File | Current line / nearby anchor | Reason / behavior |
| --- | --- | --- |
| `backend/static/components/css/booking_slip.css` | 2 `.bk-official-slip`; 28 toolbar; 36 rental-paper modifier; 64 print rules | Remove horizontal auto margins, keep buttons left, explicit left body/centered header, vertical rental rows/choices/signatories, readable phone wrapping and paper-only print overrides. |
| `backend/core/modules/facilities/templates/facilities/partials/official_booking_slip.html` | 1 `bk-official-slip--rental`; 8 metadata; 12 `bk-signatory-fields`; 16 choices | Date of Request; rental paper has no Booking Status field; sequential Signature/Name/Date blocks and saved selections, with no extra rental footer. |
| `backend/core/modules/facilities/services/booking_slip.py` | 43 `booking_slip_data`; 65 rental sections; 96 Rental Fees; 108 configured signatories; 135 payment fields | Reference labels/order; only official fee/payment fields; signed actor remains separate; saved charges/receipt data remain authoritative. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 264 `pdf_response`, rental branch | Stack rental PDF fields, checkboxes and approval blocks using shared content; remove rental-only status/extras/footer; keep non-rental/Job Order/inspection paths. |
| `backend/core/core/settings.py` | 208 `BOOKING_SLIP_SIGNATORIES` | Environment-editable official reviewer/approver metadata, separate from the admin who records a booking approval. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 14 stylesheet; 74 controller version | Cache version `20261014-paper-slip-position`. |
| `backend/core/modules/facilities/templates/facilities/pages/booking_slip.html` | 5 stylesheet version | Same refreshed shared paper styles for standalone print. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 487/531/555 existing slip tests; 580 paper-finance test; 598 official-signatory test | Updated expected paper labels, preserved room/history/mobile values and tests for excluded accounting fields/configuration/actual finance. |
| `backend/core/modules/facilities/test_admin_reservations.py` | 102 saved-slip test | Balance assertions now read the existing API, because balance no longer belongs on the official rental slip. |
| `docs/facility-configuration.md`, `CAMPUSHUB_CONTEXT.md` | This section / latest paper-position paragraph | Current decisions, functions, data flow, verification and limitations. |

The existing scratch browser harness now checks left-edge alignment, centered header, vertical client/signature order, six physical blank signing lines and absence of accounting-only fields, in addition to the retained workflow checks. No new URL/view model or duplicate document pipeline.

### 3. CSS/layout and official section changes

The preview starts at the Booking Form panel's left edge, sharing its existing 20px card inset on desktop and 14px on phones. Its maximum A4 width is retained, so unused space is to its right. Print/Export actions remain above it and left aligned. Only the university/campus/slip header is centered inside the document. Actual form fields, choices and signature content are left aligned.

Rental body uses one vertical sequence:

1. Client / Requestor Information: Name, Organization/Office, Address, Contact, Email.
2. Event Information: Name of Event/Activity, Nature of Event (saved purpose), expected participants.
3. Facility Requested: Covered Court, Hotel Function Hall, Others; actual saved facility category selects the corresponding choice.
4. Schedule of Use: Event Date, Start Time, End Time. Remove computed Duration from the paper.
5. Equipment / Additional Requirements: Sound System, Projector, Tables and Chairs, Stage, Extension Cords, Others; preserve actual specified other text and saved notes.
6. Rental Fees: Facility Fee, Equipment Fee, Other Charges, Total Amount.
7. Approval: Requested, Reviewed, Approved in vertical blocks, each with blank Signature and Date lines and recorded/configured printed Name. Director designation is under its printed name.
8. Payment Details: Official Receipt No., Date Paid, Amount Paid, from existing paid records.

The combined Tables and Chairs choice is checked when either saved component is requested; a Chairs only/Tables only annotation prevents claiming the client requested both. Stage/Extension Cords are not guessed from free text or amenities. The current mobile picker still accepts its existing choices; those new paper options remain unchecked unless explicitly present in saved metadata. No booking submission validation was widened in this layout task.

Remove Booking Status, Remaining Balance, Payment Status, Damage Deposit, Receipt Amount, discount/rental accounting rows and the extra generated-document footer from the rental paper. Those financial/workflow values stay in Overview/Payment and their existing API. Accommodation retains its prior fields/roles/layout and honest empty values.

### 4. Functions, mapping and data flow

`booking_slip_data(booking, row=None)` still reads the existing Booking, sidecar quote/requirements and canonical payment summary. Its rental branch now returns the official paper's section names and one-column field order. The rental CSS modifier controls positioning; the shared partial and existing ReportLab function consume the same sections. It is a presentation change, not a new quote, payment or approval transaction.

Facility Fee uses saved quote rental_amount (net rental after an existing discount), falling back to saved base_amount for older/mobile quotes. Other Charges uses saved fee_amount. Equipment Fee remains Not recorded because the existing quote does not classify equipment charges separately; it is not fabricated or duplicated out of generic fees. Total Amount on the Rental Fees paper uses the saved rental_total when present, which excludes the separately held damage deposit; legacy quotes without it use the existing stored booking total. Overview still shows the full stored booking due and deposit breakdown. Amount Paid remains the actual receipt amount, even when a recorded collection includes deposit. No current facility rate is used and no financial record is altered.

The shared signature configuration is consumed only by the rental paper. The actual admin's saved approval actor/date remains in Overview/Activity. Requested By is the saved requester. Reviewed By uses a configured printed reviewer name (default missing) under the reference's Campus Admin / Facility In-Charge label. Approved By uses the configured official name/designation. Empty configuration shows Not recorded. A mistaken Super Admin designation is suppressed as Not recorded rather than displayed as the institutional role. This does not grant authority or assert a digital/physical signature; all signing/date lines stay blank.

`pdf_response(..., slip=...)` stacks the rental labels/values and each checkbox; it stacks the three signatories with distinct Signature/Name/Date rows. Non-rental rendering retains the earlier paired fields/signatories. Long text wraps and can create continuation pages; no truncation is used to force a page count.

Annotated layout example:

```css
/* The document's outside position is separate from its inside header alignment. */
.bk-official-slip { margin: 16px 0; text-align: left; }
.bk-official-header { text-align: center; }
/* The panel already supplies the desktop 20px inset. No second large left margin. */
```

### 5. Backend/API, configuration and print behavior

No routes, RBAC, booking/payment statuses or mutation rules changed. The existing authorized detail payload continues to carry the shared rendered preview. Actual balances, paid summary, recorded approval actor and payment/inspection editors remain the existing logic. Only official-paper presentation changed. Protected print/PDF/private-document behavior remains private/no-store.

`BOOKING_SLIP_SIGNATORIES` in settings uses these optional local `.env` keys:

```text
BOOKING_SLIP_REVIEWER_NAME=
BOOKING_SLIP_REVIEWER_TITLE=Campus Admin / Facility In-Charge
BOOKING_SLIP_APPROVER_NAME=Dr. Glorimer L. Clarin
BOOKING_SLIP_APPROVER_TITLE=Acting Campus Director
```

The approver defaults above are supplied by the user's official reference, not inferred from the logged-in account. Changing these keys and restarting the existing Django process changes the printed metadata; it does not create a user, permission grant or booking approval. The reviewer title is retained in configuration/data; the printed rental heading uses the official reference's generic reviewer designation. No administrator-management UI or per-facility personnel assignment is added. Do not paste an entire .env into a debugging report because it may contain unrelated secrets.

Preview typography remains readable. Print has scoped compact spacing and A4 margins, hides the surrounding admin shell/actions, clears dashboard viewport heights and sidebar width/margin rules, and resets rental print typography so dashboard styles do not disturb paper order. Print Booking Slip opens the existing standalone page; Export PDF uses the existing exporter. The final verification records below describe both print paths accurately.

### 6. Database / migration impact

No migration, schema change, duplicate booking/payment data or production write. Existing settings/environment configuration is enough for official printed signatories; the existing audit still identifies the real approving admin. Changing printed configuration is not a historical approval correction. `makemigrations --check --dry-run` reported No changes detected. Reload the existing Django process for settings and Ctrl+F5 for the new asset version; no migrate command is needed.

### 7. Tests, manual verification, debugging and safe practice

85 Django tests passed across workflow/admin reservations/Calendar/mobile booking. The two new methods cover official field removal while full due/payment/deposit remain correct in the API, and configurable institutional signatories independent of the recorded actor. They test blank configuration and rejection of Super Admin as printed designation. A 63-test workflow/reservation run passed after helper/renderer refinements; repeated PDF/signatory tests also passed. Repeated runs are not counted as extra unique tests. System check, migration dry-run, Python syntax and scoped whitespace checks passed.

Chrome checks passed at 1440/768/390/320px for preview-left-edge equality, centered internal header, vertical fields/approval blocks, blank signature/date lines, excluded accounting text, exact saved mobile values and retained tabs/Edit/payment/inspection/read-only/refresh behavior. Browser requests used isolated Django fixtures and mocks, not live payments. Standard exported rental PDF was one A4 page; the long-note case was two. The standalone browser print was one A4 page. Both standalone and embedded browser print were one A4 page at all four widths after resetting the inherited dashboard heading line-height and sidebar/body print dimensions. Rendered PDF/print PNGs and desktop/phone preview were inspected rather than relying only on extracted text.

Commands from backend/core:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
# From repository root, after test fixture export:
node scratch/admin-reservations/detail-page-check.cjs
```

Manual test: open Booking Details -> Booking Form on a wide screen. The paper's left border must align with the tab content/action area, while its header remains centered. Scroll through all eight sections and compare their vertical order with the photo. Check an actual Chairs-only booking and a Hall booking. Print/export a short and long booking, verify paper-only content, then confirm Overview/Payment still show the full due, remaining balance and actual approving account. In a test environment, change the configured official name and confirm only the printed signatory changes. Inspect phone widths and view-only permissions.

Troubleshooting: if the document is still centered, inspect margin-left/right and the cache version. If it returns to paired fields, check for the rental modifier and correct historical form title. If Equipment Fee is missing, inspect saved quote taxonomy; do not guess from a charge name or copy the same amount into two fee categories. If paper total differs from collected due, check the saved rental_total versus refundable deposit in Overview. If approver is wrong, inspect the four configuration keys, not the currently logged-in account. A second page for long text is valid; for short output check inherited dashboard heading spacing/sidebar print offsets before reducing readable fonts. Never remove permissions to fix export access.

Safe exercise: on a local branch use `override_settings` to set a fictional test-only director, then verify paper HTML/PDF show that name while API approved_by still identifies the actual test admin. Restore the override and rerun the focused signatory test. Separately toggle horizontal auto margins only in DevTools and observe the difference between outside document positioning and inside header alignment; do not save that experiment to production CSS.

### 8. Remaining limitations

No official USTP logo asset or assigned reviewer record was discovered; the existing text header and missing reviewer are retained until configured. The paper's named director/designation are configurable user-supplied defaults, not a independently verified current appointment or proof of a signature. Config changes apply to subsequently rendered old bookings as well because printed institutional signatories are not historically snapshotted. Current quote data cannot separate Equipment Fee from generic additional charges. Stage/Extension Cords selection in mobile is not newly implemented. Existing current-category versus historical title behavior remains. Physical-printer/deployed-device verification is still manual.


Final verification: rental print CSS was consolidated without changing its computed layout; all four full-page browser cases passed again. All eight standalone/embedded browser exports were one A4 page with no dashboard/actions/accounting-only text. Normal exported PDF remained one page and long notes two. Final rendered paper, desktop/phone preview and print images were inspected.


## Rental slip title, field lines and document actions - 2026-10-14

### 1. Cause / reason

The user requested a centered red rental-slip title, no section divider rules, value lines immediately after colons, no visible Name/Signature labels, removal of Supporting Documents, and compact Print/Export PDF icon actions above the preview. Previously rental fields used a fixed 38% label column, creating empty space between short labels and their underlines. The admin shell also forces heading colors to navy with !important; browser verification confirmed this overrode a normal red declaration. A narrowly scoped important declaration now honors the explicit red-title request without recoloring other admin headings.

### 2. Exact files changed and current anchors

| File | Approximate line | Nearby anchor / purpose |
| --- | --- | --- |
| `backend/static/components/css/booking_slip.css` | 28, 41, 62, 99 | `.bk-slip-toolbar`, rental modifier, phone and print rules: icon buttons, red title, no heading rules, natural-width label/value layout |
| `backend/static/components/js/admin_booking_workflow.js` | 84 | `const officialDoc` / `bkPanelBookingForm.innerHTML`: Print and Export PDF icons; remove Supporting Documents heading/list/upload button |
| `backend/core/modules/facilities/templates/facilities/partials/official_booking_slip.html` | 12 | `bk-official-signatories`: retain signing line, actual name, designation and Date; omit visible Name/Signature labels |
| `backend/core/modules/facilities/templates/facilities/pages/booking_slip.html` | 5, 7 | shared CSS version and `Document actions`: same Print/Export PDF styling on standalone page |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 14, 74 | shared CSS/workflow script cache keys `20261014-slip-polish` |
| `backend/core/modules/facilities/booking_workflow_views.py` | 280, 283, 289, 314, 334 | `SlipBody`, `SlipTitle`, `rental_field`, `signature_lines`: matching rental PDF layout |
| `backend/core/modules/facilities/test_booking_workflow.py` | 487, 519 | `test_official_slip_maps_mobile_saved_data_and_shared_roles`: verify actual names survive removal of field labels in HTML/PDF |
| `scratch/admin-reservations/detail-page-check.cjs` | 81, 109 | isolated browser QA: removed supporting UI, red title, no rules, colon spacing, icons, 44px targets and print exports |
| `docs/facility-configuration.md` | 3039 | this learning/debugging guide |
| `CAMPUSHUB_CONTEXT.md` | end | preserve current implementation guidance |

Line numbers refer to this implementation; search the named anchor if later edits move them.

### 3. Changes made

The rental paper remains aligned at the left of the tab content, with its title centered inside the paper. Only its title uses red `#B42318`, explicitly requested by the user. Header/section rules are removed; value underlines and physical signing/date lines remain. Visible Name and Signature labels are removed from the rental approval blocks, while saved/configured names remain. The unrelated accommodation signature layout remains unchanged.

Print uses navy with white text and a printer icon. Export PDF uses a white background, navy outline/text and download icon. Both sit together above the preview, wrap on narrow screens, have visible labels, decorative SVGs hidden from assistive technology, gold focus outlines and 44px minimum height. The standalone page uses the same CSS. Actions never print on the document itself.

Supporting Documents, its empty message and Add Supporting Document button are removed from Booking Form. Previously saved generic uploads are not deleted. Payment receipts and inspection/Job Order files continue in their existing tabs.

### 4. How it works: functions, inputs/outputs and data flow

`booking_slip_data(booking, row=...)` is unchanged: saved booking, request metadata, quote and real payment records produce the structured slip dictionary. Django's shared partial renders that dictionary into escaped HTML for both the protected print page and API `booking_form_html`. The workflow controller's existing `render()` reads the API payload and inserts the preview plus document action links. Its input is the authorized detail payload; its output is tab content, not a new database record.

The rental CSS now uses flex rows: the label takes its natural width and the underlined value takes remaining space after a 4px gap. At phone widths the label is limited to 45% to prevent long labels squeezing values into one-character columns. Printing restores unrestricted label width on A4.

`pdf_response(..., slip=...)` still creates the existing ReportLab download. Its local `rental_field(label, value)` measures the label with `stringWidth`, creates one two-cell row and draws an underline beneath only the value cell. Input: escaped label/value text from the shared dictionary. Output: a ReportLab table flowable. Separate label widths keep the underline immediately after each colon rather than using one wide fixed column. Rental `SlipBody.spaceBefore=0` prevents inherited paragraph spacing from pushing a normal slip onto a second page; each heading/signatory supplies its own intended spacing. Long notes may continue naturally.

Annotated example: `rental_field('Contact Number:', saved_contact)` measures the real label, then puts the saved number in the remaining underlined cell. It does not validate or change the contact number. Similarly, removing `<dt>Name</dt>` only changes presentation; `signatory.name` is still rendered and existing approval actors remain in Overview/Activity.

### 5. Backend / API behavior

Existing HTML print/PDF URLs, server-side read permissions, token handling, saved quote/payment logic, client input escaping, and private no-store responses are reused. The document payload still contains existing attachment metadata and private attachment routes remain protected. This update removes their generic Supporting Documents presentation; it does not introduce a replacement upload workflow or delete historical evidence. Print in Booking Details opens the existing printable page; its Print button opens the browser print dialog. Export PDF downloads through the existing authorized route.

### 6. Database / migration impact

No model/field/schema changes, migrations, data cleanup or live-record writes. No migration command is needed. Refresh with Ctrl+F5 to load updated assets; reload/restart Django only if the existing development server is not automatically reloading Python changes.

### 7. Tests performed and how to test

- Ran the 85-test booking workflow/admin reservation/calendar/mobile facility booking suite: passed. Log: `scratch/slip-polish-tests.log`.
- After correcting PDF spacing and measured-label padding, reran three HTML/PDF/mobile/accommodation regression tests: passed.
- Ran isolated Chrome workflow and slip checks at 1440, 768, 390 and 320px, using actual Django test fixtures and mocked writes. Verified roles/actions, payment refresh, receipt/inspection links, no Supporting Documents UI, red centered title, no section rules, label spacing, icons, navy primary action, 44px targets and no page overflow.
- Checked normal rental PDF, long-note PDF and accommodation PDF using PyMuPDF: one, two and one pages respectively. All eight browser exports (standalone/embedded at four widths) contained one A4 page. Checked red title color and absence of removed labels/supporting UI; inspected rendered PDF and desktop/phone preview images.
- JavaScript syntax (`node --check`), Django system check and targeted `git diff --check` passed.

From `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
venv/Scripts/python.exe manage.py check
```

Manual verification: open a real rental Booking Details -> Booking Form, confirm title/colons/approval names and missing supporting area. Open Print, inspect A4 preview and print only the document. Export PDF and compare its same eight sections and values. Check a Hostel record keeps its accommodation slip. Confirm Overview and Payment still show the actual financial/approval information and private receipt links. Test phone width and keyboard focus on both actions.

Troubleshooting: old action wording usually means stale CSS/JS; check cache version and Ctrl+F5. A navy rental title means the scoped override or rental modifier is missing. Short PDF unexpectedly becoming two pages: check inherited ParagraphStyle `spaceBefore` and label text wrapping, not booking amounts. A colon on its own PDF line means measured label width lacks padding; preserve the small extra width beyond `stringWidth`. Long notes going to page two are valid. Historical generic uploads are intentionally not listed here now; do not assume they were deleted or bypass permissions to retrieve them.

Safe practice exercise: in a local branch, change only the toolbar gap from 10px to 12px. Inspect both standalone and embedded toolbars at 390px with keyboard focus, and confirm print output hides the toolbar. Revert the experiment. This demonstrates how shared CSS affects two views without changing business logic or data.

### 8. Remaining limitations

No physical-printer or deployed-phone transaction test was performed. The existing reviewer/logo/equipment-fee data gaps and historical signatory-snapshot limitations from the preceding guide remain. Generic supporting uploads are preserved in backend storage but intentionally have no list/upload control in Booking Form now. Browser printing and ReportLab use different font/render engines, so line breaks can differ while values and section order remain consistent.


## Center the paper preview - 2026-10-14

1. **Cause / reason:** Latest user request replaces the previous left-positioned preview. `.bk-official-slip` had `margin: 16px 0`, so spare horizontal space was all on the right.
2. **Exact files changed:** `backend/static/components/css/booking_slip.css:2`, anchor `.bk-official-slip`; `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html:14` and `booking_slip.html:5`, shared stylesheet version; `scratch/admin-reservations/detail-page-check.cjs:108`, center-position assertion; this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Set screen paper margin to `16px auto`. Update the shared CSS cache key to `20261014-slip-centered`. Print/Export PDF controls retain their existing placement above the preview. Contents and title styling stay as previously configured.
4. **How it works:** Existing `booking_slip_data` output still passes through the shared HTML partial. CSS receives the resulting article and gives equal automatic left/right margins whenever its parent is wider than the 210mm maximum. For example, a parent 1100px wide and paper about 794px wide gives approximately 153px of space on each side. At small widths the paper fills the available parent width. This centers the whole article without centering its labels/data. The print rule still sets width 100% and margin 0.
5. **Backend / API behavior:** No changed Python functions, data calculations, routes, permissions or saved values; this is a stylesheet/template-cache update.
6. **Database / migration impact:** None. No migration, database command or live-record writes.
7. **Tests performed:** Existing isolated Chrome checks passed at 1440, 768, 390 and 320px, including a new geometric assertion that the paper and Booking Form panel share the same horizontal center. Reviewed the desktop screenshot. All eight standalone/embedded browser print exports remained one A4 page. Targeted whitespace check passed. Backend test suite was not rerun for this CSS-only adjustment. Manual test: Ctrl+F5, open Booking Details -> Booking Form, check equal side margins on desktop, then inspect phone width and print preview. Debugging: if still left aligned, check the stylesheet cache version and computed margin; distinguish article alignment from internal `text-align`. Safe exercise: temporarily toggle `margin: 16px 0` versus `16px auto` in DevTools, compare side margins, then reload to restore the saved centered design.
8. **Remaining limitations:** Browser checks used test fixtures; physical printer/deployed-phone verification remains manual. Existing missing data and uploaded-document behavior are unaffected.


## Lengthwise / A4 portrait paper - 2026-10-14

1. **Cause / reason:** The user requested lengthwise size after centering. A4 portrait (210 x 297mm) is the existing official export paper format; the screen article previously had a maximum width but no paper aspect ratio.
2. **Exact files changed:** `backend/static/components/css/booking_slip.css:2` (`.bk-official-slip`), line 67 (`@page`) and line 82 (print article override); `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html:14` and `booking_slip.html:5` (CSS cache `20261014-slip-portrait`); `scratch/admin-reservations/detail-page-check.cjs:110` (portrait assertions); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Screen paper width 100%, maximum 210mm, aspect ratio 210 / 297 and existing centered margins. Explicit `@page size: A4 portrait`. Print resets article aspect ratio to auto to prevent extra blank pages.
4. **How it works / data flow:** The same saved booking -> `booking_slip_data` -> shared HTML partial pipeline supplies the article. CSS computes its preferred portrait height from available width; content can expand beyond that height rather than being cut off. Example: a 420px-wide sheet prefers 594px height, while longer content can make it taller. The A4 width cap applies on desktop; phones scale to their available content width. Browser printing independently lays out content on physical A4 portrait pages. No Python function or input/output contract changes.
5. **Backend / API behavior:** No new route, permission, payment, booking or PDF business logic. Existing ReportLab export already uses A4 and remains unchanged.
6. **Database / migration impact:** No schema/migration/data-write changes or database commands.
7. **Tests performed:** Existing isolated Chrome workflow/UI checks passed at 1440/768/390/320px, including centered geometry, computed A4 aspect ratio and content-safe portrait height. Eight embedded/standalone print outputs verified as one page each, approximately 595.28 x 841.89pt (A4 portrait). Rendered final print image visually reviewed; targeted whitespace check passed. Backend tests were not rerun for this CSS-only sizing change. Manual check: Ctrl+F5, open Booking Form, resize the browser, then Print and choose A4 portrait. Troubleshooting: if old size persists inspect asset version; if content looks taller than 297mm onscreen, it is expanding to accommodate content. Never add a fixed height with hidden overflow to force a fit. If blank print pages appear, verify the print aspect-ratio reset. Safe practice exercise: in DevTools temporarily set aspect ratio to 1 / 1 on a short test document, observe the paper shape, then reload to restore A4 portrait. Compare print preview to confirm screen sizing and page layout are separate rules.
8. **Remaining limitations:** Preview height may exceed A4 proportions for long text; physical printed output still follows A4 page boundaries. Printer settings can override browser orientation/paper size. Physical printer/deployed-phone verification remains manual.


## Shorter rental-slip field lines - 2026-10-15

1. **Cause / reason:** User requested shorter lines beside each field. Previously value underlines filled all remaining horizontal space, reaching near the paper edge. This update interprets lines as the field underlines and physical signing/date lines.
2. **Exact files changed:** `backend/static/components/css/booking_slip.css:52` (`90mm` value cap), line 60 (`55mm` blank-line cap); `backend/core/modules/facilities/booking_workflow_views.py:279,293,316` (`mm`, `value_width`, `signing_line`); `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html:14` and `booking_slip.html:5` (CSS cache `20261015-slip-short-lines`); `scratch/admin-reservations/detail-page-check.cjs:110` (geometric line-width checks); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Rental value underlines are capped at 90mm instead of filling the page. Signing/date blanks cap at 55mm. Existing centered A4 portrait paper, label-colon positioning, red title, buttons and data remain. On narrow screens lines shrink with their available space.
4. **How it works / functions and data flow:** Existing booking -> `booking_slip_data` -> shared HTML partial is unchanged. CSS caps the rendered value `<dd>` width and lets long values wrap. Existing `pdf_response` local `rental_field(label,value)` now caps its value column at 90mm, while preserving naturally measured label width. `hAlign='LEFT'` keeps shortened rows next to their label instead of centering each row. `splitInRow=1` permits a long value paragraph to continue across PDF pages rather than overflowing an unsplittable table row. Its inputs are the shared escaped label/value strings; its output is a ReportLab flowable, not saved data. PDF signing/date underscore lines are shortened to approximately the same 55mm width. Example: the Contact Number label is measured first; the actual saved number occupies an underlined value column no wider than 90mm. These millimeter constants specify visual lengths, not fake booking values.
5. **Backend / API behavior:** Only PDF presentation changes on the existing protected export route. Saved quotes, payments, booking status, approval actors, URLs, access checks and attachment storage are unchanged. No new APIs or duplicate calculation functions.
6. **Database / migration impact:** None. No models, migrations, database commands or live-record writes. Ctrl+F5 reloads the new stylesheet; normal Django development autoreload loads the PDF renderer change.
7. **Tests performed:** Three existing HTML/PDF regression tests passed: mobile saved-field/role mapping, real payment/history/escaping/access, and accommodation/missing-history behavior. Normal rental PDF remained one A4 page; long notes two; accommodation one. Existing isolated Chrome checks passed at 1440/768/390/320px, including shortened line limits, centered portrait shape, actions and workflow. Eight standalone/embedded browser print outputs remained one portrait A4 page each. Inspected the normal and both long-note PDF pages, desktop preview and final embedded print image. Targeted whitespace checks passed. No broader backend suite was rerun for this presentation update.

Manual verification: Ctrl+F5 -> Booking Details -> Booking Form. Confirm shorter lines start after their labels, actual text remains visible, and signing/date lines are shorter. Check Print and Export PDF, then a booking with long notes and a Hostel booking. To rerun focused tests from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow.BookingWorkflowTests.test_official_slip_maps_mobile_saved_data_and_shared_roles modules.facilities.test_booking_workflow.BookingWorkflowTests.test_official_slip_payment_history_signatures_escaping_and_access modules.facilities.test_booking_workflow.BookingWorkflowTests.test_official_slip_category_accommodation_and_missing_history --keepdb --noinput
```

Troubleshooting: unchanged full-length lines usually mean an old CSS cache/version or missing rental modifier. PDF still wide: inspect `value_width` in `rental_field`; do not alter saved booking values. Longer notes can legitimately need more pages after reducing line width. Do not add overflow-hidden or a fixed row height to conceal content.

Safe practice exercise: in DevTools temporarily change 90mm to 100mm, observe only field underlines growing, and reload to restore 90mm. If deliberately making the change permanent on a local branch, update the PDF width consistently and verify normal and long-note exports before using it.

8. **Remaining limitations:** Physical printer/deployed-phone verification remains manual. Browser and PDF font engines can produce different wrapping. Existing data gaps and historical-document limitations remain unchanged.


## One Others checkbox with write-in line; Requested By labels - 2026-10-15

1. **Cause / reason:** Facility Requested and Equipment / Additional Requirements rendered an Others checkbox and a separate Others field, repeating the label. User requested a single checkbox plus line, and Requested By followed by a colon, Signature and Name. This latest instruction restores those labels only in Requested By, superseding their earlier removal there.
2. **Exact files changed / anchors:** `backend/core/modules/facilities/services/booking_slip.py:56` (`section` combines Other text and checkbox), line 174 (`slip_values` retains write-in descriptions); `backend/core/modules/facilities/templates/facilities/partials/official_booking_slip.html:12,16` (Requested By fields and checkbox/write-in rendering); `backend/static/components/css/booking_slip.css:54,59,123` (`bk-choice-value`, name-width cap and print line height); `backend/core/modules/facilities/booking_workflow_views.py:318,334` (Requested By PDF labels and choice/write-in loop); `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html:14` and `booking_slip.html:5` (cache `20261015-slip-other-requester`); `backend/core/modules/facilities/test_booking_workflow.py:519,544` (HTML/PDF assertions and Other facility regression); `scratch/admin-reservations/detail-page-check.cjs:104,119` (single write-in controls/requester labels); this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Each applicable section now contains one Others checkbox and short underlined description area. Actual saved custom requirements or facility name appear on that same line. An unchecked option without a saved description gets a blank write-in line; selected but missing data remains Not recorded. The Requested By heading reads `Requested By:` and contains `Signature:`, `Name:` (actual requester) and `Date:`. Reviewed By and Approved By retain the previous unlabeled signing/name layout. Centered A4 portrait, red title, shorter lines and Print/Export PDF remain.
4. **How it works / functions and data flow:** `booking_slip_data` still reads existing booking metadata/quote/payment data. Its local `section(title, fields, choices)` finds a matching Others field, transfers the description into the Others choice as `write_in=True` and `value`, and removes the duplicate field from the presentation dictionary. Inputs: already prepared section fields and choice flags. Output: one normalized section. Saved database records are not modified. The shared Django partial displays the checked state and escaped description together; `.bk-choice-value` supplies the 90mm maximum underline. Existing `pdf_response` renders write-in choices through its existing `rental_field`, keeping the same saved value and short line. Requested By is formatted independently of actual approval actors. Compatibility `slip_values` continues reporting choice selection, and adds section-qualified Other details keys so descriptions are not lost or overwritten by another section.

Annotated example: saved `additional_requirements=['Others']`, `other_requirements='Extension cable'` becomes `{label: 'Others', checked: True, write_in: True, value: 'Extension cable'}`. HTML/PDF show one checked Others line with Extension cable, without another Others label. This is a display normalization, not a new request field or database status.

5. **Backend / API behavior:** Existing authorized document/print/PDF/detail routes and private access controls are reused. `booking_form_html` reflects the normalized shared layout. No changes to pricing, payments, approval actions, client validation or upload storage. `slip_values` Other details keys are additive compatibility output; unchanged choice flags remain available. HTML/PDF text remains escaped.
6. **Database / migration impact:** No models, migrations, new status fields, database cleanup or live writes. Ctrl+F5 refreshes new CSS; existing Django development autoreload loads helper/PDF changes.
7. **Tests performed:** Final 86-test workflow/admin reservation/calendar/mobile booking suite passed; log `scratch/slip-other-requester-tests.log`. Tests verify one Others choice per applicable section, absence of duplicate field labels, preservation of Extension cable and actual Other-facility name, restored requester labels in HTML/PDF, role/access boundaries, payment/history and accommodation behavior. The new test fixture was corrected to use the real `Facility.facility_name` field; an arbitrary `.name` attribute is not persisted by Django. Four isolated Chrome widths (1440/768/390/320px) passed requester/choice layout and existing workflow checks. All eight browser print outputs remained one A4 page; normal PDF one, long notes two, accommodation one. Final normal/PDF and browser print renderings were inspected; targeted whitespace check passed.

Manual test: Ctrl+F5 -> rental Booking Details -> Booking Form. Inspect Facility Requested and Equipment: one Others checkbox each, with line, and saved text where applicable. Inspect Requested By for colon, Signature, actual Name and Date. Compare Print and Export PDF. Test an Other-category rental facility and a known Court/Hall; confirm current facility-name behavior and no invented alternative name. Check a Hostel record retains its separate accommodation layout. From `backend/core`, rerun:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
```

Troubleshooting: duplicates usually mean old server HTML or a separate field still being rendered outside the normalized helper. Missing Other text: inspect saved other_requirements and choice.value, not UI placeholders. A selected option without recorded text must not be given invented content. When writing fixtures, inspect the model and use facility_name; assigning a nonexistent Python attribute does not update a database column. Clear stale styles via Ctrl+F5/cache key rather than deleting saved documents.

Safe practice exercise: in an isolated test fixture, change `other_requirements` from Extension cable to Extension cable and adapters. Rerun the mobile slip test with matching expected value and verify that only the single write-in description changes in HTML/PDF. Revert the fixture afterward. Never change production booking metadata for a design test.

8. **Remaining limitations:** Physical printer/deployed-phone validation remains manual. Facility category/name are still taken from the existing current facility logic where no historical field snapshot exists; no snapshot migration was introduced. Existing reviewer/logo/equipment-fee data gaps remain. A blank signature line is a space for physical signing, not proof of an electronic signature.


## Reviewer labels, inline approver and rental-note removal - 2026-10-15

1. **Cause / reason:** User requested Reviewed By (Campus Admin / Facility In-Charge) with a colon and Signature/Name/Date fields, Approved By with its actual configured name a small distance after the colon, no line above that name, and no Additional Notes on the rental slip. This supersedes the previous unlabeled reviewer/stacked approver layout.
2. **Exact files changed / anchors:** `backend/core/modules/facilities/templates/facilities/partials/official_booking_slip.html:12-26` (rental signatory branches); `backend/static/components/css/booking_slip.css:63` (`bk-approved-heading`, three-character gap); `backend/core/modules/facilities/services/booking_slip.py:85` (rental equipment fields omit notes); `backend/core/modules/facilities/booking_workflow_views.py:316-330` (PDF approver table and reviewer labels); `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html:14` and `booking_slip.html:5` (CSS cache `20261015-slip-approval-layout`); `backend/core/modules/facilities/test_booking_workflow.py`, anchor `test_official_slip_payment_history_signatures_escaping_and_access` (note removal/storage preservation and long equipment description); `scratch/admin-reservations/detail-page-check.cjs`, anchors `Reviewer fields labeled` / `Approver name beside colon with no top line`; this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Requested By retains Signature/Name/Date. Reviewed By now uses the same labeled fields and a colon after its heading. Approved By has a colon, configured director name on the same row with a small gap, designation aligned below the name, and existing Date field below. Its old blank signing line above the name is removed. Additional Notes is omitted only from the rental paper, including the entered text. Centered portrait paper, title, Others write-in, short lines, payment data and document actions remain.
4. **How it works / functions and data flow:** `booking_slip_data` still accepts a saved booking and returns its shared presentation dictionary. Rental equipment fields now contain only existing Other description; the saved `details['notes']` is not deleted. Other accommodation templates retain their current notes fields. The shared HTML partial branches on rental versus accommodation and Approved By versus requester/reviewer. `.bk-approved-heading` uses two CSS grid columns, a `3ch` gap and a second-row designation; it wraps long names without clipping. The existing PDF renderer uses a two-column left-aligned table: heading in column one, escaped configured name and designation in column two. Column-one width measures its label plus three spaces, preserving the requested small separation. Other rental signatories use the existing `rental_field('Name:', actual_name)` and blank signing/date lines. No duplication of booking, approval or payment calculations.

Example: configured approver name Dr. Glorimer L. Clarin remains the same input; the output moves from a separate paragraph under a line to `Approved By:   Dr. Glorimer L. Clarin`. This changes presentation, not who approved a booking. Additional Notes previously read from metadata still appear through the existing Overview data flow; they are simply absent from rental `sections` and its HTML/PDF output.

5. **Backend / API behavior:** Existing protected routes, permissions, saved financial snapshots, actual audit actor, uploaded data and statuses remain. The API's generated `booking_form_html` shows the new layout; saved notes remain in metadata/Overview. No new endpoint or independently generated document data.
6. **Database / migration impact:** None. No model changes, migration, live writes or deletion of notes. Ctrl+F5 refreshes the CSS. Django development autoreload loads helper/PDF changes.
7. **Tests performed:** All 86 workflow/admin reservation/calendar/mobile booking tests passed; log `scratch/slip-approval-layout-tests.log`. Existing history/escaping test verifies notes remain saved but are absent from rental HTML/PDF, reviewer/approver colons and long Other equipment text remain. Four isolated Chrome widths passed reviewer Signature/Name/Date, inline approver/no top line, no Additional Notes, five remaining blank lines and existing workflow checks. All eight browser print outputs were one A4 portrait page. Normal PDF one page; long equipment description two; accommodation one. Rendered normal, both long PDF pages and browser print were inspected; targeted whitespace check passed.

Manual test: Ctrl+F5 -> Booking Details -> Booking Form. Check Requested/Reviewed blocks and Approved By name placement. Confirm there is no line above the director name, designation/date remain, and Additional Notes plus its entered text do not appear. Compare Print/Export PDF, then inspect Overview to confirm saved notes remain. Verify a Hostel record retains its separate accommodation form. Rerun from `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
```

Troubleshooting: old layout usually means stale CSS/server-rendered HTML; inspect cache key and reload. Missing reviewer name still means configuration is absent, not that the current admin should be guessed. If notes disappear from Overview too, inspect original metadata rather than recreating text. Do not change actual approval actor or saved records to solve a printed-name layout issue.

Safe practice exercise: temporarily change `.bk-approved-heading` column-gap from 3ch to 2ch in DevTools, compare spacing, then reload to restore 3ch. Verify the designation follows the name column and long names remain visible at phone width. For a permanent experiment on a local branch, update the equivalent measured PDF gap and compare exports before merging.

8. **Remaining limitations:** Physical printer/deployed-phone verification remains manual. Browser character-width gaps and PDF spaces vary with fonts. Existing configured reviewer/logo/equipment-fee gaps and signatory history limitations remain. The printed name is not an electronic signature or a change to approval authority.


### Follow-up: move the approver name two lines down - 2026-10-15

1. **Cause / reason:** Latest user request moves Dr. Clarin's name two lines down from the Approved By heading, overriding the preceding inline arrangement.
2. **Exact files changed:** `backend/static/components/css/booking_slip.css:63-65`, anchors `.bk-approved-heading` and `.bk-signatory-name`; `backend/core/modules/facilities/booking_workflow_views.py:320`, Approved By table cell; `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html:14` and `booking_slip.html:5`, stylesheet cache `20261015-slip-approver-spacing`; `scratch/admin-reservations/detail-page-check.cjs`, anchor `Approver name moved two lines down`; this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Keep Approved By at the top, place the configured name two text lines lower in its existing name column, and keep designation/date below. No top signature line is restored.
4. **How it works / functions and data flow:** Existing saved booking/configuration -> `booking_slip_data` -> shared HTML/PDF pipeline remains. CSS grid aligns cells at their starts and adds `padding-top: 2lh` to the name. The `lh` unit follows the name's computed line height. The existing PDF table name cell contains a Spacer of `2 * document_body.leading` followed by the escaped name Paragraph; for rental leading 10.5pt this is 21pt. Inputs and returned booking payload are unchanged. Using layout spacing instead of empty text lines keeps names visible and designation/date flowing naturally.
5. **Backend / API behavior:** PDF presentation only; no route, permission, payment, approval actor, field-value or API-contract changes. Existing configurable approver name is reused.
6. **Database / migration impact:** None; no migrations, database commands or live writes. Ctrl+F5 refreshes CSS.
7. **Tests performed:** Three existing mobile/role/HTML/PDF, payment/history/escaping/access and accommodation regression tests passed. Four Chrome widths passed the two-line spacing assertion and existing UI/workflow checks. Eight browser print exports remained one A4 page. Normal PDF one page; long equipment text two; accommodation one. Final normal and long PDF approval layout and browser print were visually inspected; targeted whitespace check passed. Broader backend tests were not repeated for this spacing-only change. Manual verification: refresh, open Booking Form, confirm the name below Approved By with two-line spacing and designation/date below, then compare Print/Export PDF. Troubleshooting: inspect computed paddingTop and lineHeight if spacing looks wrong; stale assets should use the updated cache key. Safe exercise: toggle 2lh to 1lh in DevTools, observe the name move one line upward while the heading stays in place, then reload to restore 2lh. For a permanent local experiment, adjust the corresponding PDF Spacer consistently and rerun the three slip tests.
8. **Remaining limitations:** Browser and PDF line heights differ with fonts; two lines are measured in each renderer's text metrics. Physical printer/deployed-phone verification remains manual.


### Follow-up: PHILIPPINES alone on header row two - 2026-10-15

1. **Cause / reason:** User requests PHILIPPINES alone on the second university header row. The prior shared header split before OF SOUTHERN instead.
2. **Exact files changed:** `backend/core/modules/facilities/services/booking_slip.py:14`, anchor `INSTITUTION`; `backend/core/modules/facilities/test_booking_workflow.py:514,518`, HTML/PDF header checks; `scratch/admin-reservations/detail-page-check.cjs`, anchor `Philippines alone in second header row`; this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Header row one becomes UNIVERSITY OF SCIENCE AND TECHNOLOGY OF SOUTHERN; row two becomes PHILIPPINES. Existing centering/type style is reused for rental and accommodation slips.
4. **How it works / functions and data flow:** The unchanged `booking_slip_data(booking)` returns `institution=INSTITUTION` as two text strings. The existing shared HTML partial loops those strings with a br between them. The existing PDF renderer joins the same escaped strings using br markup in its centered header Paragraph. Changing the common tuple updates preview/standalone print/export together without duplicate header text. Input is a saved booking plus static institutional identity; output remains the same presentation dictionary. Example: the second tuple element PHILIPPINES maps directly to the second explicit header row.
5. **Backend / API behavior:** Only generated header wording/line break changes. Booking/payment/pricing/status/permissions/routes/data are unaffected; no new endpoint or logic.
6. **Database / migration impact:** None; no migration or data writes. Reload the page; Django development autoreload loads the helper change. No CSS cache bump is needed because no CSS changed.
7. **Tests performed:** Three existing HTML/PDF/mobile/history/access/accommodation tests passed. Added assertions for the HTML break and the first two PDF text lines; PDF extraction whitespace is stripped before comparing to avoid a false failure from leading spaces. Four isolated Chrome widths passed the explicit two-row header assertion and existing UI/workflow checks. All eight browser prints remained one A4 page; normal PDF one, long equipment two, accommodation one. Normal PDF and browser print renderings were visually reviewed; targeted whitespace check passed. Broader backend tests were not repeated for this header-only edit. Manual verification: refresh Booking Form, check the university header, open Print/Export PDF and compare the same break. Troubleshooting: old text means old server-generated HTML; check the helper constant and reload/restart the development server if needed, not database records. Safe practice exercise: inspect the shared partial loop and identify which tuple element produces each row; verify the matching PDF header code joins the same data rather than manually editing separate copies.
8. **Remaining limitations:** On very narrow phone previews, the longer first row may wrap naturally to preserve legibility; PHILIPPINES retains its own explicit row. Printed A4 output was verified with two university rows. Physical-printer/deployed-phone verification remains manual.


### Follow-up: approver date without underline; colon aligned to designation - 2026-10-15

1. **Cause / reason:** User requested removal of the Approved By Date underline and horizontal alignment of its colon with the A in Acting Campus Director. Previously its date used the same underlined row as other signatories.
2. **Exact files changed:** `backend/core/modules/facilities/templates/facilities/partials/official_booking_slip.html:16-22` (approver date inside name/designation grid; requester/reviewer date retained); `backend/static/components/css/booking_slip.css:67-68` (`bk-approved-date-label/value`); `backend/core/modules/facilities/booking_workflow_views.py:278,318-331` (`TA_RIGHT`, third approver table row, date only appended separately for other signatories); `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html:14` and `booking_slip.html:5` (CSS cache `20261015-slip-approver-date`); `scratch/admin-reservations/detail-page-check.cjs`, anchor `Approver date has no underline and colon aligns with designation`; this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Approved By date has Date text and a colon, with no blank underline. Its colon starts in the same column as the designation. Requester and reviewer keep their Signature/Name/Date lines. Configured approver name remains two lines down.
4. **How it works / functions and data flow:** Shared saved booking/configuration -> `booking_slip_data` -> HTML/PDF pipeline remains. The approver HTML grid places Date in column one, right aligned, and its colon in column two, exactly the designation column. The colon has no border styling or blank-line class. Existing PDF `pdf_response` uses the same approver table: a right-aligned Date paragraph in column one and plain colon in column two. The separate underscore date row is now emitted only for requester/reviewer. Inputs/output data contracts stay unchanged. Example: Acting Campus Director and the colon below both start at column two's left edge, so changing the first column's width moves them together rather than requiring guessed space characters.
5. **Backend / API behavior:** Document presentation only. No changed date validation, saved payment dates, actual approval timestamps, roles, routes or permissions. Printed date remains a blank physical-entry area; no date is invented.
6. **Database / migration impact:** None. No migrations, database commands or live writes. Ctrl+F5 loads the updated CSS; normal development autoreload loads the PDF renderer changes.
7. **Tests performed:** Three existing HTML/PDF/mobile/history/access/accommodation regression tests passed. Four isolated Chrome widths passed the colon/role horizontal-coordinate assertion, no approver underline, four remaining signing/date blanks and existing layout/workflow checks. Eight browser prints remained one A4 page; normal PDF one, long equipment two, accommodation one. Normal PDF/browser print and long PDF approver layout visually reviewed; targeted whitespace check passed. The broader backend suite was not repeated for this presentation change. Manual check: refresh Booking Form, inspect Approved By Date against Acting Campus Director, then compare Print/Export PDF and the still-underlined requester/reviewer dates. Troubleshooting: if the colon is misplaced, inspect the grid/table column instead of inserting spaces into stored names. If the line remains, check old CSS/generated HTML and the removed approver blank-line class. Safe exercise: inspect both the designation and colon elements in DevTools and compare their bounding-box left coordinates; temporarily change grid column-gap and observe them moving together, then reload to restore the saved spacing.
8. **Remaining limitations:** Browser and PDF fonts can differ in visible spacing before the colon, while the colon uses the same designation column. Physical printer/deployed-phone checks remain manual.


### Follow-up: compact Date: label beside aligned colon - 2026-10-15

1. **Cause / reason:** User clarified Date: should read together, rather than placing Date after the colon. The approver grid's 3ch column gap previously separated the word from its aligned colon.
2. **Exact files changed:** `backend/static/components/css/booking_slip.css:67`, anchor `.bk-approved-heading .bk-approved-date-label`; `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html:14` and `booking_slip.html:5`, stylesheet cache `20261015-slip-date-compact`; `scratch/admin-reservations/detail-page-check.cjs`, anchor `Date directly beside colon`; this guide and `CAMPUSHUB_CONTEXT.md`.
3. **Changes made:** Move the right-aligned Date label across the 3ch gap so it touches its existing colon. The colon remains aligned to Acting Campus Director and the approver date remains without an underline. Other signatories and name spacing stay unchanged.
4. **How it works / data flow:** Existing booking -> `booking_slip_data` -> shared HTML still produces separate label/colon elements. CSS adds `margin-right: -3ch` to the label only, compensating for the grid gap without moving the colon/designation column. For example, a 21px column gap is canceled by a -21px right margin, making the label's right edge meet the colon's left edge. The specific selector overrides general paragraph margins. No Python function, input/output contract or stored text changes. Existing ReportLab already prints Date and colon directly adjacent, so its renderer needs no edit.
5. **Backend / API behavior:** Unchanged; only screen/browser print CSS and its cache references change. No new routes, permissions, timestamp logic or data calculations.
6. **Database / migration impact:** None. No migrations or live writes. Ctrl+F5 reloads the updated stylesheet.
7. **Tests performed:** Four isolated Chrome widths (1440/768/390/320px) passed a geometric assertion that Date's right edge meets the colon's left edge, plus the existing designation alignment/no-line/workflow checks. All eight browser print exports remained one A4 page. Final browser print rendering visually reviewed; targeted whitespace check passed. Backend suite was not rerun for this CSS-only adjustment. Manual check: refresh Booking Form and inspect Approved By Date:, then compare Print/Export PDF. Troubleshooting: old gap means stale CSS/cache or a paragraph margin overriding the specific selector. Safe practice exercise: toggle margin-right between 0 and -3ch in DevTools, observe the label move while the colon remains fixed, then reload to restore the saved compact label.
8. **Remaining limitations:** Physical printer/deployed-phone checks remain manual. If future design changes the grid gap, its label compensation must change to the same amount; verify left/right coordinates rather than guessing spaces.


## Booking Slip labels and section spacing matched to Section 7 - 2026-10-15

### 1. Cause / reason

User requests Booking Form renamed to Booking Slip. The pending spacing clarification was answered: sections other than Section 7 should use the same compact spacing as Section 7. Rental body rows inherited 6px top/bottom padding, plus grid gaps, while requester/reviewer rows had no such padding. This caused noticeably different row density.

### 2. Exact files changed / anchors

| File | Current approximate line | Anchor / change |
| --- | --- | --- |
| `backend/static/components/css/booking_slip.css` | 46-56, 120-132 | Rental body/meta rows and choices: no extra padding/gaps; reference heights 20px screen / 15px print |
| `backend/static/components/js/admin_booking_workflow.js` | 85 | `bkPanelBookingForm.innerHTML`: Booking Slip heading/fallback; Slip Status |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 14, 36, 74 | Booking Slip tab; shared CSS/workflow cache `20261015-slip-section-spacing` |
| `backend/core/modules/facilities/templates/facilities/pages/booking_slip.html` | 5 | Shared CSS cache version |
| `backend/core/modules/facilities/templates/facilities/partials/rental_rules.html` | 11 | Add/Edit Facility display field label Booking Slip |
| `backend/core/modules/facilities/booking_workflow_views.py` | 77 | `documents_for`: generated document display title Booking Slip |
| `backend/core/modules/facilities/test_booking_workflow.py` | 419-420 | Full detail test verifies new tab/document title with existing payload/routes |
| `scratch/admin-reservations/detail-page-check.cjs` | anchors `Renamed tab`, `Body row height matches Requested By` | Existing isolated browser checks extended for wording/spacing |
| `docs/facility-configuration.md` / `CAMPUSHUB_CONTEXT.md` | latest section / end | Learning guide and current project context |

### 3. Changes made

Visible detail tab, panel heading, fallback label, generated-document link title and facility configuration field now say Booking Slip. Supporting status text reads Slip Status: Generated. Internal BookingForm tab/section IDs, booking_form_* payload keys and routes are retained so existing links/workflow remain compatible.

Rental sections 1-6 and 8 use compact body row spacing matching the requester/reviewer reference in Section 7: remove inherited vertical cell padding and grid gaps; screen minimum row height 20px and print minimum 15px. Checkbox rows use the same compact height. Section 7 signatories, two-line approver-name offset, Date: alignment/no underline, heading/campus/title, selected Other text, financial values, and document actions remain. Long text may increase a row's height instead of being clipped.

### 4. How it works / functions and data flow

Existing booking -> `detail_data` -> JSON seed/API -> workflow `render()` still supplies BookingForm data to the same tab/panel elements. Only its visible heading/status strings change. `documents_for(booking)` still returns the same existing URL/section/PDF URL metadata; the generated document's display title is now Booking Slip. Its inputs remain a saved booking; output structure is unchanged apart from that display string.

The shared rental_rules template labels the existing read-only/select field as Booking Slip without changing IDs or booking category mapping. Existing `booking_slip_data` still builds saved sections for the shared preview and PDF. CSS rules scoped to the rental paper override generic document cell padding, so a short field row has the same height as Requested By's Signature row. Example: previously a 20px value plus 6px padding on each side gave a 32px row; padding 0 restores 20px. Print uses 15px minimum matching Section 7's current print lines. The ReportLab PDF body was already compact and its renderer is unchanged.

### 5. Backend / API behavior

No duplicate booking/slip generation, new routes, permission changes or business calculations. Document metadata title changes from Booking Form to Booking Slip; internal section remains BookingForm. Existing official/historical document titles and general-form configuration values are retained for compatibility rather than rewriting stored snapshots. Actual rental/accommodation titles already use Booking Slip. No UI state or saved notes are discarded.

### 6. Database / migration impact

None. No models, migration, database commands or live-record writes. Ctrl+F5 loads the updated CSS/JS; Django development autoreload handles the document display-title update.

### 7. Tests performed / manual verification

All 86 workflow/admin reservation/calendar/mobile booking tests passed; log `scratch/slip-section-spacing-tests.log`. Full detail test checks new tab and document title while existing payload/access checks remain. Four isolated Chrome widths (1440/768/390/320px) passed renamed tab/panel/status assertions, no body padding, desktop row-height equality to Requested By and existing workflow/print checks. Phone multiline content can grow naturally. All eight browser print exports remained one A4 portrait page; final desktop preview and embedded print were inspected. JavaScript syntax and targeted whitespace checks passed.

Manual test: Ctrl+F5 -> Bookings -> View -> Booking Slip. Check label/status/actions, compact fields/checkboxes in sections 1-6 and 8, and unchanged Section 7. Print/export a real booking, inspect dates/quotes and Other text. Open Add/Edit Facility and check the Booking Slip field still maps correctly when changing category. Confirm old tab query links continue working.

From `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
```

Troubleshooting: old generic headings/status text usually mean stale JavaScript/cache; inspect `20261015-slip-section-spacing`. Uneven short field height: check computed padding and row gap on the rental modifier, not database values. Do not rename internal IDs/section keys merely to rename a tab, because existing action-to-tab routing uses them. Longer rows are expected when values wrap.

Safe practice exercise: temporarily restore 6px padding on a rental body row in DevTools and compare its height with the Signature row in Section 7. Reload to restore the compact design. Separately inspect the renamed tab and observe its unchanged `data-bk-tab=BookingForm`; this illustrates separation of user-facing wording from stable routing identifiers.

### 8. Remaining limitations

Physical printer/deployed-phone verification remains manual. Existing historical/generic official document titles are not bulk renamed, and current data gaps remain. Browser/PDF font metrics can differ; content and protected workflows are reused. Long content is intentionally allowed to wrap or continue to another printed page.


## Native browser Print and matching Chrome PDF export - 2026-10-15

### 1. Cause / reason

Print in Booking Details was a link opening a separate page, requiring another click to open the browser print dialog. Export PDF constructed a separate ReportLab version of the slip, so fonts, spacing, checkbox shapes and field positions could diverge from the browser's HTML/CSS. The user requested native Chrome printing and the same design/layout for export. A single template/stylesheet and rendering engine removes that divergence. Intent's localized-change guidance applies: preserve the established workflow and fix this specific interaction/output mismatch.

### 2. Exact files changed / nearby anchors

| File | Approximate current line | Anchor / purpose |
| --- | --- | --- |
| `backend/static/components/js/admin_booking_workflow.js` | 86, 202 | `data-bk-print-slip`, page click handler: real Print button directly calls window.print |
| `backend/static/components/css/booking_slip.css` | 30-35, 83-105 | Button styling/focus/disabled state; white print canvas and isolated document typography |
| `backend/core/modules/facilities/services/booking_slip_pdf.py` | 17, 39, 51 | `browser_binary`, `booking_slip_pdf`, disposable rendering directory |
| `backend/core/modules/facilities/booking_workflow_views.py` | 265, 315 | `pdf_response` delegates slip export; `document` handles renderer failure with private HTTP 503 |
| `backend/core/core/settings.py` | 207 | Optional `BOOKING_PDF_BROWSER_BINARY` environment setting |
| `backend/core/modules/facilities/templates/facilities/pages/booking_slip.html` | 5-9 | `pdf_render` mode inlines trusted CSS and omits toolbar/session script while reusing shared slip partial |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 14, 74 | CSS/controller cache `20261015-chrome-slip-print` |
| `backend/core/modules/facilities/test_booking_workflow.py` | 489, 499 | Missing-browser, timeout, invalid-output and cleanup regressions |
| `scratch/admin-reservations/detail-page-check.cjs` | anchor `Print opens native dialog directly without navigation` | Existing isolated browser workflow/print checks |
| `docs/facility-configuration.md`, `CAMPUSHUB_CONTEXT.md` | latest section / end | Explanation, deployment/debugging/tests and preserved project guidance |

### 3. Changes made

Booking Slip Print is now a button that immediately opens the current browser's native print dialog. In Chrome, this is Chrome's print preview. The slip-only print CSS still hides dashboard navigation/actions and shows only the official document. A missing preview disables Print rather than printing an empty page. Export PDF still downloads through the same authorized existing URL and preserves its filename/private response headers.

Slip exports now use installed Chrome/Chromium to print the exact shared HTML/CSS. The old duplicated ReportLab slip layout was removed. Job Order and inspection PDF generation retain their existing ReportLab path. Print-only styles normalize Arial/heading weight, white canvas, field spacing and hidden accessibility descriptions so global admin styles or remote font loading cannot alter one output path. Screen layout, centered portrait paper, red title, section content and approval fields remain.

### 4. How it works / functions, inputs, outputs and data flow

Print: authorized detail payload -> existing workflow render -> button -> delegated `window.print()` -> browser reads shared `@media print` rules. No API write, new tab, new booking or custom print dialog is created.

Export: existing private document route -> existing `booking_slip_data(booking)` -> `pdf_response(..., slip=...)` -> new `booking_slip_pdf(slip)` -> same booking_slip.html/shared official partial and application-owned booking_slip.css -> hidden Chrome -> PDF bytes -> existing attachment response. The shared helper still supplies actual saved booking/payment data and escapes client text.

`browser_binary()` returns an explicitly configured valid executable, a Chrome/Chromium executable found on PATH, or standard Windows Chrome installation paths. It raises `BookingSlipPDFError` if unavailable. `booking_slip_pdf(slip)` accepts the existing presentation dictionary and returns PDF bytes. It loads the local stylesheet with Django static finders, renders a script-free, toolbar-free HTML page, creates a separate temporary Chrome profile, runs headless Chrome with a 30-second limit, verifies the PDF signature and cleans up its disposable files. It does not navigate back through an authenticated HTTP URL or reuse the user's logged-in profile. Only application-owned CSS uses the template's safe filter; client text still uses normal Django escaping.

Annotated example: `booking_slip_pdf(slip)` renders the same `slip['sections']` already seen in the preview. Updating a field's spacing in booking_slip.css therefore updates browser printing and PDF export together, instead of requiring a second ReportLab table change. The `pdf_render=True` template flag changes asset/toolbar loading only, not booking values.

Chrome's headless mode uses the browser engine without displaying an interactive window; see the [official Chrome Headless documentation](https://developer.chrome.com/docs/automation-and-testing/headless). This application uses that existing browser for rendering; it does not move Django booking logic into a browser service.

### 5. Backend / API behavior

Read permissions, physical-booking scope, HTML/print/PDF routes, session/tab-token behavior, saved quotes/payments, approval/inspection actions and activity logs remain. The successful export response remains application/pdf with attachment disposition and private no-store cache policy. A missing browser, timeout or invalid output returns private HTTP 503 with an explanatory error, rather than pretending to download a successful PDF or silently switching to a different layout. The HTML print page remains available when server-side export is unavailable. Other workflow document routes/ReportLab logic are unchanged.

### 6. Database / migration and deployment impact

No schema, migration, booking mutation, historical-data rewrite or extra Python package is needed. Chrome is already installed on this Windows machine and was used in real export tests. For deployment, the Django server must have Chrome or Chromium available to its service account. Auto-detection covers PATH/common Windows paths. If necessary configure an absolute executable path in the server environment:

```dotenv
BOOKING_PDF_BROWSER_BINARY=C:/Program Files/Google/Chrome/Application/chrome.exe
```

Restart/reload Django after changing the environment setting; Ctrl+F5 loads the updated CSS/JS. Keep the local shared stylesheet available through Django static finders. No migration command is required. Headless operation keeps the browser's default sandbox; this change does not disable it globally.

### 7. Tests performed / manual test steps

- Ran all 88 booking workflow/admin reservation/calendar/mobile booking tests: passed. Log `scratch/chrome-slip-tests.log`. Real tests exercised installed Chrome and existing role/history/mobile/accommodation data; additional tests covered missing executable, rendering timeout, invalid PDF output, temporary cleanup and unchanged booking data.
- Four isolated Chrome widths (1440/768/390/320px) passed direct native Print-call/no-navigation assertions and existing full-page/workflow/spacing checks. Native print dialog itself was intercepted in the automated harness; generated Chrome print PDFs were real.
- All eight standalone/embedded Chrome print outputs were one A4 portrait page. Compared the real server-exported normal rental PDF against each: identical words, word coordinates and rasterized pixel components (zero differences) for this fixture. Final print/export images were inspected.
- Long equipment text exported across two pages, retaining all 350 test words; accommodation exported one page. Both were rendered and visually inspected. JavaScript syntax, Django system checks and targeted whitespace checks passed.
- A QA image comparison initially read image buffers repeatedly and was stopped; its corrected version reads each buffer once. This was a verification-script issue, not an application failure. A small inherited dashboard background was found during parity checks and corrected with a white print canvas.

From `backend/core`:

```powershell
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
venv/Scripts/python.exe manage.py check
```

Manual check: Ctrl+F5 -> Booking Details -> Booking Slip -> Print. Chrome should open its native preview immediately while the page remains in place. Choose A4, portrait, scale 100%, normal CSS/default margins. The spacing/header follow-up below now suppresses Chrome's own headers/footers using page padding. Cancel and confirm the page is usable. Export PDF and compare the same data, approval block, lines, color and section order. Test view-only permissions, Hostel, long text and access-denied users. For a staging-only failure check, set an invalid browser path, confirm export returns the honest error while the printable HTML remains accessible, then restore the setting.

Troubleshooting: opening a separate tab means stale controller JS; check `20261015-chrome-slip-print`. A different layout suggests stale CSS, admin styles leaking into print, remote fonts, or browser dialog scale/paper/header settings. HTTP 503: check executable configuration, service-account execution permissions, stylesheet availability and timeout; do not change booking/payment data or disable permissions. Keep user-entered text escaped and never substitute user-uploaded CSS into the PDF template.

Safe practice exercise: on a local branch adjust one shared field underline from 90mm to 85mm, print and export the same test booking, and compare both outputs. Restore 90mm and rerun the focused slip test. This demonstrates how one shared template/stylesheet prevents output drift. Do not modify actual payment records for a visual test.

### 8. Remaining limitations

Parity was verified for one normal rental fixture using the installed Chrome version, with additional long-content/accommodation export checks. Other browser versions, user print-dialog settings, fonts on another server, physical printers and deployed phones still require manual verification. Each server-side export launches a short-lived Chrome process, so high concurrent export volume may need bounded worker scheduling later. Server Chrome/Chromium is a real deployment dependency; exports report failure honestly when unavailable. The native dialog belongs to the browser currently in use; the page cannot force another browser's UI or choose its destination/printer for the user. Existing reviewer/logo/equipment-fee and historical printed-name limitations remain.


## Print/PDF breathing room and browser header removal - 2026-10-15

### 1. Cause / reason

The rental print rules squeezed fields/signatures into 15px rows and sections into 3px gaps. The user requested more spacing in both outputs. The unwanted date/time, CampusHub page title, local URL and page count came from Chrome's print headers/footers, not saved booking fields. Removing booking dates or the page title would not solve that cause. Chrome adds its own metadata when page margins leave room; see the [official Chrome page-margin documentation](https://developer.chrome.com/blog/print-margins).

Confirmed by rendering the same fixture with browser headers enabled: 12mm margins produced the browser metadata; zero margins with 12mm page padding suppressed it and kept the document inset. Padding belongs inside the page box and repeats on subsequent pages. This replaces the earlier need to manually disable Headers and footers for normal Chrome/default CSS printing.

### 2. Exact files changed / current line anchors

| File | Approximate current line | Nearby code anchor / change |
| --- | --- | --- |
| `backend/static/components/css/booking_slip.css` | 81-83 | `@page`: A4 portrait, margin 0, padding 12mm |
| Same stylesheet | 91-93 | `Normal document flow`: remove dashboard flex layout during printing only |
| Same stylesheet | 124, 134-144 | `Give the rental paper`: roomier field/signature/choice rows and section spacing |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 14 | CSS cache `20261015-slip-print-spacing` |
| `backend/core/modules/facilities/templates/facilities/pages/booking_slip.html` | 5 | Same CSS cache for standalone HTML printing |
| `scratch/admin-reservations/detail-page-check.cjs` | 148, 155-157 | Real embedded/standalone PDFs with `displayHeaderFooter:true`; print spacing assertions |
| `scratch/admin-reservations/slip-print-check.py` | 13, 29 | PDF parity, no browser metadata, per-page bounds and all long text retained |
| `docs/facility-configuration.md`, `CAMPUSHUB_CONTEXT.md` | this section / end | Implementation, learning, troubleshooting and verified results |

### 3. Changes made

Print/PDF field and signature rows increase from 15px to 17px, checkbox/write-in rows to 16px, section gaps from 3px to 6px, heading gaps from 1px to 2px, and approval-block gaps from 6px to 8px. Screen preview spacing is retained. Page margins become zero while page padding remains 12mm on all four sides, preventing Chrome's browser metadata from appearing without moving content to the physical paper edge.

Verification found a trailing blank second page only when the roomier slip was printed inside the dashboard. The shell's flex layout caused that pagination difference. The print-only main wrapper now uses ordinary block flow and removes flex sizing on the content. The extra blank page disappears; this does not hide or clip actual slip content. No fixed page height or overflow clipping was added.

### 4. How it works / functions, inputs, outputs and data flow

There are no new application functions. Existing `booking_slip_data(booking)` accepts the saved booking and creates the presentation dictionary. Existing workflow `render()` inserts the shared official-slip HTML into Booking Details. Print calls `window.print()`, which applies `@page` and `@media print` from booking_slip.css. Existing `booking_slip_pdf(slip)` receives the same presentation dictionary, renders the same template with local CSS, and returns Chrome-generated PDF bytes. Its existing `--no-pdf-header-footer` flag is retained as export protection.

Data flow: saved booking/payment -> shared slip helper/partial -> screen preview -> browser print CSS; or the same helper/partial/CSS -> headless Chrome -> PDF download. CSS changes geometry, not data. The actual Date of Request, event schedule, payment date, booking number, signature fields and saved names remain. Browser timestamp/title/URL/page-number metadata is suppressed separately.

Annotated example:

```css
@page {
  size: A4 portrait; /* Same lengthwise paper for browser and export. */
  margin: 0;         /* No margin region for Chrome's automatic header/footer. */
  padding: 12mm;     /* Keep content away from the edge on EVERY page. */
}
```

For reading/writing space, `min-height: 17px` is a minimum, not a fixed height: a long saved value can wrap and grow. Section `break-inside: avoid` helps keep sections together when possible; large sections can still flow across pages.

### 5. Backend / API behavior

Existing private print/PDF routes, filenames, read permissions, tab tokens, payment/status logic, HTML escaping and export-error behavior remain. This is a stylesheet/template-cache change; no new endpoint, payment/date calculation, approval rule or inventory logic was introduced. Browser page metadata is not stripped from saved records because it was never part of those records.

### 6. Database / migration impact

No model, database write or migration. No new package or environment setting. Existing server-side Chrome dependency remains. Ctrl+F5 refreshes the detail page CSS; a production deployment using collected static files should deploy/collect the updated stylesheet through its usual process. No migration command is needed.

### 7. Tests performed, troubleshooting and safe practice

- Three focused Django official-slip tests passed using the installed Chrome exporter: mobile saved data/roles, payment/history/escaping/access, category/accommodation/missing history. Django system check reported no issues. Log: `scratch/slip-print-spacing-tests.log`.
- Four browser widths (1440/768/390/320px) passed existing navigation/workflow/read-only checks and new 17px field/6px section assertions. Log: `scratch/slip-print-spacing-browser.log`.
- Sixteen real browser PDFs (embedded and standalone, header/footer enabled and disabled, at each width) matched the server-exported normal rental PDF: identical content, word positions and rendered pixels, one A4 page, no browser URL/title/page-count metadata. `slip-print-check.py` checks these outputs.
- Normal rental and accommodation outputs each had one page; long equipment content had two. All 350 long test words were retained; every page's text stayed inside the 12mm inset. Normal rental and the second long-content page were rendered and visually reviewed. The updated normal rental ends around 802pt, within the A4 printable content area.
- JavaScript/Python QA syntax, UTF-8/trailing-whitespace checks for changed application/QA files and targeted `git diff --check` passed.
- Initial test logging used a wrong relative output path; the command did not run. Correcting it to the workspace scratch folder produced the passing results above. Initial PDF parity verification caught the dashboard-only blank page, which was fixed and all browser/parity checks rerun. These were observed verification issues, not guessed causes.

Manual verification: Ctrl+F5, open a real permitted booking -> Booking Slip -> Print. Keep A4, portrait, scale 100%, default/CSS margins. Check the paper has roomier lines and no browser timestamp, CampusHub page title, URL or page number. Cancel, then Export PDF and compare. Confirm actual event/payment dates remain. Repeat for an accommodation booking and a long saved value; continued pages must have the same edge inset.

Reproduce the automated fixture checks from the workspace root after generating the existing test fixtures:

```powershell
node scratch/admin-reservations/detail-page-check.cjs
backend/core/venv/Scripts/python.exe scratch/admin-reservations/slip-print-check.py
```

Troubleshooting: unchanged spacing -> inspect CSS version `20261015-slip-print-spacing`, hard-refresh and deploy the latest static file. Browser metadata reappears -> confirm the @page rule loaded; restore default/CSS margins rather than custom print-dialog margins, or turn off Chrome's Headers and footers. A blank extra page -> inspect print display/flex rules on the dashboard wrappers instead of hiding overflowing content. Missing real payment dates/data -> inspect the existing helper/input data; do not remove those fields to address browser metadata.

Safe practice exercise: on a local branch change only rental field min-height from 17px to 18px, print/export the same isolated fixture, and observe whether the document needs another page. Check all data is retained and compare both outputs. Restore 17px and rerun the browser/PDF checks. This teaches that spacing affects pagination, and one shared CSS file keeps both renderers consistent. Never edit live payments to test a layout.

### 8. Remaining limitations

Verified with installed Chrome and the current shared templates, not a physical printer. Other browser engines/versions may interpret page padding differently; custom paper, scaling or margin overrides can alter output. A user can disable browser Headers and footers explicitly if their settings/browser override the CSS. Long real content is allowed to require more pages; the system does not force every possible booking onto one page. Existing deployment-browser, historical-data/logo/reviewer and export-concurrency limitations remain as described above.

## BEU Job Order reference form and shared Print/PDF (October 17, 2026)

### 1. Cause / reason

The user supplied `Propose_FM-USTP-ORO-BEU-01-Job Order Request.docx` and explicitly chose to update the existing CampusHub Job Order form and Print/PDF layout to match it. Confirmed inspection: Job Order already lived in `FacilityBookingRequest.details.job_order`, the editor used free-text fields, and documents used a generic label/value list plus a separate ReportLab layout. The supplied reference instead has a university/document-control header, bordered client/service fields, service checkboxes, an items/received/required table, and four physical sign-off columns.

The DOCX was read as a design reference, not as an independent instruction to change transaction workflows. Its OOXML table structure, labels, Letter page dimensions and embedded university logo were inspected. A read-only hidden Word rendering attempt stalled and its newly launched automation helper was stopped; no user Word instance was closed. Consequently there is no claim of a pixel comparison against a Word-rendered source. The implemented HTML/PDF outputs themselves were rendered, inspected and compared as described below. The original DOCX was not edited.

### 2. Exact files changed and current anchors

Line numbers below are approximate and current for this update; search the anchor if earlier changes move them.

| File | Line / nearby anchor | Change and purpose |
| --- | --- | --- |
| `backend/core/modules/facilities/services/job_order.py` | 13 `SERVICE_CHOICES`, 18 `service_selection`, 27 `validated_selection`, 42 `job_order_data`, 69 `client_data`, 78 `job_order_form_data` | One set of reference choices, server validation, legacy write-in mapping, and read-only client/document presentation. |
| `backend/core/modules/facilities/services/booking_workflow.py` | 272 `elif action == 'job_order'` | Accept selected services in existing JSON; retain legacy submissions and generated identity/staff data; normalize required datetime to the CampusHub timezone. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 130 `job_order_data`, 138 `job_order_html`, 259 `pdf_response`, 293 `document` | Add the server-rendered preview/form choices to the existing detail payload; dispatch the existing private Job Order URL to the reference template/exporter. Remove the unused generic Job Order field-list branch. |
| `backend/core/modules/facilities/services/booking_slip_pdf.py` | 39 `booking_slip_pdf`, 44 `job_order_pdf`, 52 `html_document_pdf` | Extract the existing Chrome rendering routine so both documents reuse it with their own HTML/CSS. Keep booking-slip output and inspection ReportLab behavior. |
| `backend/core/modules/facilities/templates/facilities/partials/official_job_order.html` | 1 `beu-job-order` | Reference header, client fields, selected services, items/dates and physical signature area. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 1 `{% load static %}`, 7 `beu-job-toolbar` | Standalone document with Print and Export PDF actions; the same partial is used in the Booking Details tab. |
| `backend/static/components/css/job_order.css` | 2 `.beu-job-order`, 41 `.beu-service-options`, 60 `@page beu-job-order` | Navy/white screen preview, compact labeled editor, responsive behavior, and isolated Letter print rules with a 10mm inset. |
| `backend/static/assets/img/ustp-job-order-logo.png` | Binary asset | University logo extracted unchanged from `word/media/image15.png` in the supplied reference; not generated. |
| `backend/static/components/js/admin_booking_workflow.js` | 93 `bkPanelJobOrder`, 151 `action==='job_order'`, 202 `getAll('service_types')` | Reference form labels, existing client information, service checkbox array, optional gender selection, Manila prefill, preview and retained staff metadata. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 15 `job_order.css`, 75 `admin_booking_workflow.js` | Load scoped stylesheet and refresh version to `20261017-beu-job-order`. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 139 `test_job_order_is_structured...`, 160-257 `test_*job_order*` | Preserve/update the existing expectation and test selections, legacy edits, escaping, dates, private exports, error handling and continuation pages. |
| `scratch/job-order-reference/check.cjs`, `scratch/job-order-reference/check_pdf.py` | Browser/PDF QA entry points | Isolated test fixtures, four viewport sizes, mocked writes, print/export parity and text-bound checks; not application code or production data. |
| `docs/facility-configuration.md`, `CAMPUSHUB_CONTEXT.md` | This section / latest BEU entry | Implementation explanation, verification, troubleshooting and project continuity. |

### 3. Changes made

The editor now shows the generated request number/date, read-only saved client name/address/phone/email, optional Gender Preference, six Job or Service Requested checkboxes, an optional other-service write-in, Turnaround Time, Details / Specifics, Item (s), and the two received/required datetime inputs. Visible labels remain associated with their controls. It does not copy client edits into a second profile; correct booking client information through the existing booking editor.

The source choices are Equipment Rental, Facility Rental, Hotel Accommodation, Training Center, Laboratory Analysis, and BPP NCII Assessment. They describe a recorded Job Order; checking one does not reclassify the booking or start a different service workflow. Laboratory Analysis sits beside Turnaround time; BPP NCII Assessment sits beside the write-in line, matching the reference arrangement.

The paper uses the university logo/header, document code `FM-USTP-ORO-BEU-01`, revision `00`, and the reference's table/sign-off structure. Effective Date stays blank because the supplied form has no effective date. Page No. identifies the first form page as `1`; it does not falsely assert `1 of 1` when long content continues. Screen uses navy/white; paper uses black/white. Source paper dimensions are US Letter, portrait. Normal data fits one page; long content flows onto continuation pages with repeated item headings.

Filled-out by / Assisted by / Verified by / Approved by have physical signing space and the reference's Client / Administrative Aide / Personnel In-charge / BEU Manager role labels. These signing lines stay blank. Existing system actors remain visible separately as Recorded By, Assisted By, Verified By and Booking Approved By. A booking approver is not automatically declared the BEU Manager and no digital signature is invented.

### 4. How it works and beginner example

`job_order_form_data(booking, row=...)` takes the existing Booking and optional precomputed row and returns client values and valid dropdown/checkbox choices. `client_data` uses saved booking contact details, falling back to the existing linked CampusHub user where supported. Missing address remains blank.

`validated_selection(data)` takes the submitted checkbox list and write-in text. It rejects unknown values, a non-list payload, an empty request and an oversized combined request. It removes duplicate choices, orders choices consistently with the reference, and returns the selected list plus the existing `service_requested` summary. Gender must be one of the defined choices; an unchanged historical non-standard value can still be preserved. Legacy clients posting only `service_requested` remain supported.

For example, this input:

```python
{"service_types": ["Facility Rental", "Equipment Rental"], "service_other": ""}
```

produces these keys inside the existing `details.job_order` object:

```python
{
    "service_types": ["Equipment Rental", "Facility Rental"],  # reference order
    "service_other": "",
    "service_requested": "Equipment Rental; Facility Rental",  # compatible old key
}
```

The locked existing `transition()` function saves this object, preserving its generated number, original date and original recorded-by snapshot. Existing staff/audit behavior remains. Received time reuses `timestamp()` and its existing not-future rule. Required time may be future; an offset-free `datetime-local` value receives the default Asia/Manila timezone, while an explicit offset is retained. The browser uses the shared Manila formatter rather than slicing UTC timestamps into local inputs.

`service_selection(record)` handles old records conservatively: an exact official label can be selected; other old free text appears in the checked write-in area without guessing which service was intended. Rendering does not rewrite old records.

`job_order_data(booking)` reads existing metadata and returns display fields, selected options and formatted datetimes. It embeds only the trusted local university asset as a data URL. `detail_data()` renders `official_job_order.html` into the authenticated `job_order_html` response, and the tab displays it. Django escapes saved text, so a client's `<script>` stays visible text rather than executable markup.

Print opens the existing protected Job Order document route and calls Chrome's normal `window.print()`. Export PDF uses `job_order_pdf()` -> `html_document_pdf()`: render the same partial with inline application-owned CSS, print using an isolated temporary Chrome profile, validate PDF output and clean up temporary files. Sharing one HTML/CSS layout prevents a second PDF-only template from drifting. Named `@page beu-job-order` rules prevent the new Letter size from overriding the existing A4 booking slip. Page padding keeps the inset on continuation pages and suppresses Chrome date/title/URL margins.

### 5. Backend / API behavior

Existing routes are unchanged:

- `GET /api/bookings/<booking_id>/` adds `job_order_form` and, if recorded, `job_order_html` to the existing protected detail response.
- `POST /api/bookings/<booking_id>/update/`, action `job_order`, accepts the new choices using existing management permission, CSRF, state checks, Facility/Booking locks and audit.
- `GET /api/bookings/<booking_id>/documents/job-order/` opens the reference HTML; `?format=pdf` exports it.

All existing physical-booking scope/read permissions/tab-token rules remain. Missing Job Order is still an honest validation error. Export failure returns private HTTP 503 with a useful Job Order error; it does not change the saved record and HTML remains available for Print. No new endpoint or duplicate logging/approval/payment system was created. Mobile does not receive internal Job Order metadata. No live bookings, accounts, payments or documents were created during development checks.

### 6. Database / migration impact

No model, field, table or migration was added. New optional service selection keys live in the existing JSON sidecar. Existing Job Order numbering, dates and historical free-text data remain. No new dependency or configuration is needed on this workstation. Export reuses the existing Chrome/Chromium dependency and optional `BOOKING_PDF_BROWSER_BINARY`; deploy the new static assets (existing `collectstatic` process if used) and hard-refresh the detail page.

### 7. Tests performed and how to test

- **94 targeted Django tests passed** across `modules.facilities.test_booking_workflow`, `modules.facilities.test_admin_reservations`, `modules.facilities.test_calendar` and `api.test_mobile_facility_booking`. This includes six added Job Order cases and the updated legacy case, real isolated writes, no partial invalid saves, number preservation, script escaping, offset-aware required time, private PDF/read access and export failure. Existing payment, availability, approvals, inspection, CSRF, Calendar and mobile checks passed in that run.
- After the final print-page padding refinement, **two focused PDF tests passed again**: standard Letter output and long content continuation. The normal fixture was one page, and all 45 item lines were retained across two pages in the long fixture.
- Real headless Chrome passed **1440, 768, 390 and 320px** preview/editor checks, six labeled service controls, selected values, read-only client data, empty-selection error/recovery, actual submitted checkbox arrays, Manila prefill under a New York browser timezone, and no page-level horizontal overflow. Browser saves were intercepted; the backend tests exercised real test-database writes.
- Eight browser Print PDFs (four widths, browser headers/footers on and off) matched the Export PDF's text, positions and rendered pixels. Standard and long PDFs were checked for page insets, clipping, missing items and browser URL/title/token leakage; all checks passed. The standard output and all final continuation pages were rendered and visually inspected.
- Django system checks, `makemigrations --check --dry-run` (No changes detected), Python compile, JavaScript syntax, UTF-8/trailing-whitespace checks for the 12 changed code/QA files and targeted git whitespace checks passed. Full project-wide testing is not claimed.

Reproduce from `backend/core`:

```powershell
$env:JOB_ORDER_REVIEW_DIR = 'C:/Users/leste/Desktop/CAMPUSHUB/scratch/job-order-reference'
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
```

From the project root, the generated fixtures support:

```powershell
node scratch/job-order-reference/check.cjs
backend/core/venv/Scripts/python.exe scratch/job-order-reference/check_pdf.py
```

Manual steps: hard-refresh -> Bookings -> View an eligible booking -> Job Order -> Create/Edit. Confirm client information matches the saved booking. Select the actual services and optional gender, enter specifics/items/real received and required times, and Save. Reopen to check values and unchanged request number. Use View / Print Job Order -> Print and Export PDF; compare the fields, checkbox positions, signatures, paper size and absence of browser metadata. Confirm missing address/signatures are not fabricated. Repeat with a historical free-text Job Order and an authorized read-only administrator; read-only users must have no edit action. Perform transaction checks on a test booking, not an actual client's transaction.

Troubleshooting: old editor/layout -> inspect asset version `20261017-beu-job-order`, restart the development server if necessary, hard-refresh and deploy static files. No services selected -> choose at least one service or enter the write-in; both browser and backend errors preserve the existing record. Wrong client values -> inspect booking metadata and the linked account before editing through the existing booking editor. Offset time on an old record -> inspect its stored ISO string; do not bulk-shift historical data. Export 503 -> confirm Chrome configuration and that `job_order.css` was deployed; use protected HTML Print while correcting the server configuration. Lost text -> inspect page-break CSS rather than adding `overflow:hidden` or a fixed-height text box.

Safe practice exercise: on a branch, change only the visible editor label `Item (s)` to `Items requested`, keeping the input name `items`. Run the existing Job Order tests and browser check, inspect the POST key and verify paper/PDF still use the reference label and the same saved data. Restore the label afterward. This teaches the difference between UI labels, JSON field names and document presentation without modifying real transactions.

### 8. Remaining limitations

This updates the existing booking Job Order; it does not implement a new laboratory intake, assessment registration, leasing, SOA, cashier or service-approval workflow. Existing Job Order status still derives from saved service text/booking approval metadata; it is not a new BEU approval lifecycle. Physical office signatures and institutional acceptance remain external. The source logo is a small raster image; no replacement university asset was invented. The effective date is unspecified, and long content may require additional pages. The proposed reference's official approval/version should be confirmed by the office before treating it as a formally issued institutional template.

Client/contact values come from existing booking/account records; this change does not freeze a historical signed-document snapshot. Existing historical records are not rewritten. Print parity was verified with installed Chrome, not every browser or a physical printer; custom paper/margin/scaling settings can change output. The existing synchronous Chrome export still depends on the deployment's browser availability and capacity. No production saves, physical Android session or live office acceptance test was performed.

## Job Order automatic draft and document-first tab (October 17, 2026)

This section supersedes the earlier manual Create/Edit Job Order and Letter-paper presentation. It implements attachment `d8354089-d455-4903-9e65-4d6fbdf306e7` and the user's instruction to use the template to generate the Job Order.

### 1. Cause / reason

Confirmed inspection: the supplied template partial already existed, but Job Orders were still created manually through `job_order` actions. The main tab used general workflow metadata and the inline `View/Create Job Order` editor. No missing document was prepared automatically for approved or completed bookings. Booking approval was also incorrectly used to derive a visible Approved Job Order status, although it did not represent a BEU document approval. The previous reference-paper implementation used Letter size; the new explicit request requires A4 and the reference caption `1 of 1`.

The main tab now uses a read-only document preview with a separate Edit Draft modal. The existing template, JSON sidecar, document routes and Chrome PDF renderer are reused. A missing Job Order is prepared from actual booking data; no new Job Order model or approval workflow was added.

### 2. Exact files changed and current anchors

| File | Approximate current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/job_order.py` | 23 `draft_eligible`, 32 `add_job_order_draft`, 82 `ensure_job_order_draft`, 105 `refresh_unedited_draft`, 120 `job_order_available`, 149 `job_order_data` | Eligibility, automatic draft content, locked legacy backfill, refresh of untouched source text, honest blanks and existing reference presentation. |
| `backend/core/modules/facilities/admin_booking_views.py` | 174 `add_job_order_draft` | Prepare the draft inside the existing approved manual-reservation creation transaction. |
| `backend/core/modules/facilities/services/booking_workflow.py` | 137 `if approved`, 271 `action == 'job_order'`, 336 `add_job_order_draft` | Pending cannot edit a Job Order; approved transitions prepare missing drafts; editable office number and longer known specifics/items reuse existing validation. Legacy service text remains compatible. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 77 `job_order_available`, 109 `ensure_job_order_draft`, 142 `job_order_status`, 214 `refresh_unedited_draft`, 311 Job Order document branch | Prepare/backfill only after access checks; return Draft/preview; update untouched generated content after booking edits; protect direct HTML/PDF access for Pending. |
| `backend/static/components/js/admin_booking_workflow.js` | 17 `Edit Draft`, 93 `bkPanelJobOrder`, 150 Job Order editor, 177 `small`, 210 focus restoration, 220 `beforeprint` | Document-first heading/actions, modal-only editing, no repeated client inputs, post-save preview/focus, Escape/Tab behavior, and active-document printing. |
| `backend/static/components/js/admin_bookings.js` | 244 `const tabs`, 281 `job_order: 'Job Order'` | List Job Order action opens the preview tab instead of the editor; remove View/Create wording. |
| `backend/static/components/css/job_order.css` | 2 `.beu-job-order`, 22 checkbox pseudo-element, 46 `.beu-job-panel-heading`, 64 `@page beu-job-order`, 65 print rules | A4 preview/print, compact action header, selection of only Job Order during embedded printing, isolated print fonts/weights/line height and deterministic check marks. |
| `backend/core/modules/facilities/templates/facilities/partials/official_job_order.html` | 9 document-control values | Reuse the supplied-template reproduction; change the requested page caption to `1 of 1`. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 15 stylesheet, 73-75 scripts | Refresh assets to `20261017-job-order-draft`. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 197-199 scripts | Refresh shared list/Calendar assets after the list action changes. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 5 stylesheet | Refresh the same standalone document stylesheet. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 187 invalid update, 213 A4 export, 294 onward automatic-draft cases, 451 evidence-privacy assertion | Add and update real isolated transition, backfill, source-refresh, long-text, permission and rendering tests/fixtures. |
| `scratch/job-order-draft/check.cjs`, `scratch/job-order-draft/check_pdf.py` | QA entry points | Test real rendered fixtures with intercepted browser writes, modal behavior and print/export comparisons. |
| `docs/facility-configuration.md`, `CAMPUSHUB_CONTEXT.md` | This section / latest automatic-draft entry | Current behavior, code/data-flow explanation, debugging, evidence and safe practice. |

### 3. Changes made and requested report points

The old View/Create Job Order form is removed from the main tab. There is no Create Job Order or Generate Job Order button. The main view has Job Order, USTP Oroquieta Business Enterprise Unit / JOB ORDER Request, Job Order Status: Draft, Generated from Booking, Edit Draft (only when allowed), Print and Export PDF above `official_job_order.html`. It has no data-entry controls inside the tab itself.

The existing source template remains the document structure: university header, `FM-USTP-ORO-BEU-01`, revision `00`, unspecified effective date, page caption `1 of 1`, client/contact fields, gender and service options, specifics, items/received/required dates and four physical sign-off columns. The latest request explicitly changes output to A4. Unknown office number, address, turnaround, received/required dates and signatures stay blank. An automatic preparation timestamp is not substituted for a specimen-received time or a physical signature.

Auto-filled fields use the saved booking requester/contact/email, existing booking address (there is no general CampusHubUser address field), actual document preparation date, facility category and known reservation details. New Court/Hall drafts select only Facility Rental; new Hostel drafts select only Hotel Accommodation. Unknown physical categories remain unselected until a real service is recorded. Existing recorded selections/free text are preserved, not reclassified by the new mapping.

Details / Specifics includes only known Facility, Activity, Purpose, Schedule or Stay, Room / Unit, Participants/Guests and Additional Requirements. Item(s) can use saved requirements; absent values stay blank. Gender is not inferred from a name or photo. No sample office number or fabricated staff designation is used.

Edit Draft opens the existing small-action modal, not the tab's inline editor. Administrative controls include office Job Order Request No., optional gender, service choices/write-in, turnaround, specifics, items and received/required times; document date is read-only. Known client information is not re-entered. Current staff/audit snapshots remain real authenticated actors; BEU sign-off lines remain physical. A completed booking remains viewable and printable without enabling a completed-booking edit action. After save the modal closes, the actual detail response refreshes the preview, and focus returns to Edit Draft. Escape cancels and keyboard focus remains inside the open editor.

### 4. How it works and data flow

`draft_eligible(booking, details)` is a pure check over the current booking status and existing facility/source classification. It accepts Approved and Completed physical reservations. It excludes Pending, Rejected, Cancelled, Services and schedule blocks from new draft preparation. Reserved / Confirmed remains the existing display of an Approved paid booking; it needs no invented stored status.

`add_job_order_draft(booking, details)` receives the real Booking and an existing metadata dictionary. If eligible and no Job Order exists, it adds one `details.job_order` dictionary and returns True. Otherwise it returns False and keeps existing content. It sets document_status=draft, auto_generated, real prepared_at/date, known service mapping and booking-specific text. Unknown fields are empty strings. Callers already inside reservation-create/approve/update transactions save through the existing sidecar. Preparing a document never changes the booking/payment status or implies BEU approval.

`ensure_job_order_draft(booking)` handles existing records. After view permission and physical-booking lookup have succeeded, it checks for a missing eligible draft. If needed, it opens a transaction, locks the Booking row, rereads and locks the existing sidecar, checks again, and merges only the missing Job Order. It preserves request_key and unrelated quote, payment, inspection and client data. A genuinely legacy booking without a sidecar receives one existing FacilityBookingRequest row, not another Booking. A repeated view finds the saved draft and performs no second preparation/write. The parent row lock serializes concurrent missing-draft reads and transaction edits.

This is an automatic lazy backfill when the authorized detail or Job Order HTML/PDF is opened. It does not run a production-wide migration or an unsolicited bulk rewrite. **Authorized GET reads of a missing eligible document can now persist that derived draft**, as explicitly requested. This does not grant the reader general booking-management permission; manual editing still uses existing server-side management/CSRF/state checks.

`refresh_unedited_draft(booking, details)` runs inside the existing booking-edit transaction. It refreshes generated service/specifics/items when a draft is auto-generated and has never been manually saved. Its original date/prepared_at/number remain. Once an administrator has edited the draft (`updated_at` exists), or if it is a historical non-generated document, its text is preserved during later booking edits.

`job_order_available(booking)` prevents Pending from exposing a Job Order preview or document route. It permits recorded terminal history to remain readable; new Cancelled/Rejected drafts are not created. `job_order_data()` formats the saved draft for the existing shared template. Missing or unparsable dates do not produce Not recorded inside the paper. Historical NULL optional fields remain blank; string-form legacy requirements remain a single recorded requirement rather than being split into characters.

Annotated example of a newly prepared Court draft:

```python
{
    "number": "",                    # office number unknown; keep the line blank
    "document_status": "draft",     # booking approval is not BEU sign-off
    "auto_generated": True,
    "service_types": ["Facility Rental"],  # from the existing category code
    "service_requested": "Facility Rental",  # retain the compatible backend key
    "specifics": "Facility: <saved name>\nPurpose: <saved purpose>...",
    "received_at": "",              # never invent sample receipt time
    "required_at": "",
}
```

The diagram in words is: existing approved Booking -> existing sidecar draft -> `job_order_data` -> shared `official_job_order.html` -> read-only tab / standalone Print / existing Chrome Export PDF. Edit Draft -> existing protected POST -> existing locked transaction/audit -> same preview. There is one stored document and one layout.

Specifics and Item(s) allow up to 12,000 characters through the existing `text()` helper and matching textarea limits, because combining several valid saved booking fields can exceed the former 2,000-character limit. This avoids generating a draft that cannot be saved unchanged. Other input limits remain; the optional office number is bounded to 100 characters. Legacy free-text service submissions still update the checkbox/write-in presentation correctly.

### 5. Backend / API and Print/PDF behavior

No URL or new API was introduced. Existing create and approval calls prepare the draft within their current transactions. `GET /api/bookings/<id>/` and the full detail page ensure missing eligible drafts and return `job_order_html`, existing form choices and the additive `job_order_status` label. Direct `GET /api/bookings/<id>/documents/job-order/` also ensures a missing eligible draft; Pending returns a validation error for HTML and PDF. Anonymous and out-of-scope requests are rejected before backfill. Mobile's existing public-data allowlist continues excluding internal Job Orders.

The table's Job Order action now navigates to `?tab=JobOrder`. Edit Draft still posts action=job_order to `/api/bookings/<id>/update/`; it does not create another document or change payment/availability rules. The optional old job_order_stage=request configuration no longer enables Pending editing; the latest explicit approval gate takes precedence. Stored configuration is retained for compatibility.

Print uses Chrome's normal `window.print()`. `beforeprint` selects the visible Job Order and `afterprint` restores normal view. Scoped print rules hide sidebar, navigation, tabs, modal/buttons and all metadata above the paper. Booking Slip continues using its existing print path. Both documents keep their own page rules.

Export PDF continues using `job_order_pdf()` -> the existing shared `html_document_pdf()` Chrome routine; the exporter code was reused without modification in this change. It prints the same partial and CSS as the preview. Its temporary browser profile, trusted local asset, no-network content, private/no-store result, filename and failure behavior remain. Header/footer margins are suppressed with the existing page-padding approach.

Observed print debugging found real CSS interference: admin_layout's important Roboto fonts/500-weight table headings, dashboard paragraph line height and Bootstrap pseudo-element border sizing changed embedded output. Job Order print CSS now isolates Arial, black text, exact heading/cell weights, paragraph line height and checkmark box sizing. These are scoped to the document; the admin design system was not changed. Final embedded and standalone outputs match the exporter.

### 6. Database / migration impact

No schema/model/migration/new dependency is needed. Existing records gain optional draft JSON only when automatically eligible in a normal transaction or opened with permission. Existing saved Job Orders, request keys and unrelated historical metadata are not overwritten. No production bookings or payments were opened/saved during development verification; fixtures use Django's isolated test database. The existing Chrome installation/BOOKING_PDF_BROWSER_BINARY requirement remains.

Deploy the changed files/static assets, restart Django as appropriate and Ctrl+F5. Production static deployments should follow their existing collectstatic process. No special backfill command is required: existing eligible bookings prepare the draft on first authorized open.

### 7. Tests performed and manual steps

- **102 targeted Django tests passed** in `modules.facilities.test_booking_workflow`, `modules.facilities.test_admin_reservations`, `modules.facilities.test_calendar` and `api.test_mobile_facility_booking`. Eight added cases cover automatic creation, untouched-versus-manually-edited refresh, long valid booking fields, Pending even with legacy stage configuration, idempotent sidecar-preserving backfill, Completed access, exact category mappings and historical/permission/service boundaries. Existing Job Order validation/export tests were updated for an already prepared draft and explicit A4 output. Existing booking, payment, inspections, Calendar, availability, CSRF and mobile checks passed. After the final historical-NULL handling, three focused mapping/backfill/long-text cases passed again.
- The evidence-privacy test now checks absence of actual attachment payload/JSON data keys instead of rejecting the substring data anywhere: an official university `data:image` asset in the newly automatic preview is public template content, not leaked private evidence. Legacy service-text testing caught an old automatic checkbox list masking a new free-text edit; that compatibility issue was corrected and rerun.
- Real headless Chrome passed **1440, 768, 390 and 320px**: preview first/no inputs in the tab, modal-only Edit Draft, genuine test fixture values, Manila dates under a New York viewer timezone, empty-selection errors/recovery, submitted arrays, save -> refreshed document, Escape/focus restoration, Pending unavailable, read-only access and no page-level horizontal overflow. Browser writes are intercepted, while Django tests perform real isolated database writes.
- **20 Print/PDF comparisons passed**: standalone and embedded Print with browser headers/footers on/off at four widths (16), plus untouched automatic-draft embedded Print at four widths (4). Text, positions and rendered pixels matched the corresponding Export PDF. No CampusHub UI, URL, tab token or browser title was printed.
- Standard and untouched auto-filled drafts each fit one A4 page. All 45 long fixture item lines remain across two pages with repeated item headings. Final standard/automatic/long PDFs were rendered and every page visually inspected; text-bound checks found no clipping.
- Django system checks and migration dry-run passed (No changes detected). Python/JavaScript syntax, UTF-8/trailing-whitespace checks on 14 changed code/QA files and targeted git whitespace checks passed. No whole-project, physical-printer or production-office acceptance claim is made.

Reproduce from `backend/core`:

```powershell
$env:JOB_ORDER_REVIEW_DIR = 'C:/Users/leste/Desktop/CAMPUSHUB/scratch/job-order-draft'
venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
venv/Scripts/python.exe manage.py check
venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

From the project root after generating those isolated fixtures:

```powershell
node scratch/job-order-draft/check.cjs
backend/core/venv/Scripts/python.exe scratch/job-order-draft/check_pdf.py
```

Manual steps on test records:

1. Open an Approved Court booking -> Job Order. Expect Draft, its booking ID, only Facility Rental selected, actual known client/schedule data, blank office number and the paper preview. There must be no Create/Generate button or inline input form.
2. Repeat for a Hall and Hostel. Expect Facility Rental / Hotel Accommodation respectively; no unrelated selected service.
3. Open an old Approved and Completed booking without Job Order data. Reopen and verify the same draft/prepared_at is retained, unrelated metadata is unchanged, and Completed has no edit action. A Pending booking must have no preview/print/edit access, even by direct document URL.
4. Edit Draft as an authorized manager. Complete an actual office number/known administrative fields, save, and confirm the modal closes on the refreshed preview. Cancel/Escape must discard unsaved changes. A view-only admin must not gain Edit Draft.
5. Print from the tab and standalone page; Export PDF. Check A4 portrait, only the paper, blanks instead of unknown placeholders, and no CampusHub controls. Compare output; repeat a long test value to check continuation pages without cropped text.
6. Edit a reservation whose draft is untouched: known generated purpose/schedule should refresh. After manually editing its draft, later reservation edits must not overwrite the office text.

Troubleshooting: old View/Create wording or inline editor -> check asset version `20261017-job-order-draft`, deploy shared list/detail scripts, restart/reload Django and hard-refresh. Missing draft -> inspect real status, physical/service classification and existing sidecar; do not force Pending to Approved to obtain a document. Incorrect checkbox -> inspect stored facility_type and whether the document was historically recorded, rather than matching a facility name substring. Repeated creation -> check parent Booking locking and the second missing-record check; do not add duplicate models or manual create buttons. Export failure -> inspect existing Chrome configuration; saved draft remains intact and HTML Print remains available. Shifted font/checkboxes -> check document-scoped print rules rather than changing global admin typography. Wrong historical times or signatories -> verify source evidence before correction; do not guess or infer them.

Safe practice exercise: in a local branch, change only the visible `Edit Draft` label to `Edit Job Order Draft`, preserving the backend action value `job_order`. Predict which server function runs, generate the isolated fixtures, inspect the browser POST action and verify the saved JSON remains the same. Update the scratch UI assertion for the temporary label, run it, then restore both changes. This teaches that user-facing wording, action identifiers, stored JSON and document output are separate concerns. Never use a real client booking as a practice record.

### 8. Remaining limitations

Draft status is a document preparation label, not a new BEU approval/signature lifecycle. Office sign-off, effective date confirmation and institutional acceptance remain external; none is fabricated from a booking approver. The reference's requested `1 of 1` is its fixed form-page caption; exceptionally long contents can still continue onto extra PDF pages. The source's small raster logo and the earlier source-render limitations remain.

Backfill is deliberately lazy on authorized document/detail access, not an immediate rewrite of every historical record. Known client data still comes from existing booking/account storage; this is not a frozen signed-document archive. Manual draft text is preserved when source reservations change, so office staff should review it after later booking edits. Existing Services/food-analysis/assessment/leasing processes are not changed. Export depends on installed Chrome and was verified with that browser, not every printer or custom print-dialog override. Full production concurrency/office/mobile-device acceptance was not performed.



## Job Order from the original Word template (October 17, 2026)

This section supersedes the hand-built HTML Job Order layout described above. The original supplied Word file is now the layout source. Booking Slip, payment, approval and inspection workflows keep their existing behavior.

### 1. Cause and reason

Confirmed: the previous Job Order partial recreated the supplied Word form with HTML tables and separate CSS. Matching the original required maintaining two layouts. The replacement fills a copy of the actual DOCX and converts that copy to PDF for browser preview and printing. The original reference is unchanged. A DOCX is a ZIP of XML, images and formatting files; changing a few XML text slots preserves the rest of the document.

### 2. Exact files, current lines and anchors

All paths below are relative to the project root. Lines refer to this implementation; use the nearby anchor if later edits move them.

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/document_templates/job_order_request.docx` | Binary; original reference | New application-owned copy of the supplied official template. |
| `backend/core/modules/facilities/services/job_order_docx.py` | 18 `TEMPLATE`; 31 `fill_paragraph`; 66 `check_drawing`; 87 `job_order_docx`; 179 `office_binary`; 198 `job_order_pdf` | New in-place Word filling and private local conversion. |
| `backend/core/modules/facilities/services/job_order.py` | 146 `job_order_data` | Keep saved data formatting; remove the old separate HTML logo/data URL dependency. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 134 `job_url`; 266 `pdf_response`; 320 DOCX branch | Return document URLs instead of manual form HTML; serve protected Word/PDF. |
| `backend/core/modules/facilities/services/booking_slip_pdf.py` | 39 `booking_slip_pdf`; 44 `html_document_pdf` | Remove the Job Order HTML renderer; keep Booking Slip Chrome output. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 6 stylesheet; 9 action toolbar; 13 preview | Standalone native PDF viewer with Print, Export PDF and Download Word. |
| `backend/core/modules/facilities/templates/facilities/partials/official_job_order.html` | Removed | Retire the recreated official HTML tables. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 75 `job_order_preview.js` | Load shared viewer before the booking workflow script; update cache versions. |
| `backend/static/components/js/admin_booking_workflow.js` | 32 `tab`; 59 `CampusHubJobOrder.dispose`; 94 `jobDoc`; 219 Print handler | Load preview only on Job Order tab; preserve Edit Draft; refresh and release previous PDF after save. |
| `backend/static/components/js/job_order_preview.js` | 5 `dispose`; 9 `load`; 44 `print` | Authenticated PDF fetch, Blob iframe, loading/error/Retry, native PDF Print and cleanup. |
| `backend/static/components/css/job_order.css` | 1 viewer rules; 13 `.beu-service-options` | Style viewer/editor controls only; no second paper/table design. |
| `backend/core/core/settings.py` | 209 `JOB_ORDER_OFFICE_BINARY` | Optional environment-based server converter path. |
| `backend/core/requirements.txt` | 11 `lxml>=6,<7` | Preserve source XML namespaces and drawing compatibility markup. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 216 `test_job_order_fills_original_package_and_private_downloads`; 260 PDF test; 307 long-content test; 327 conversion-failure test | Verify actual DOCX, private routes, editable slots, retained package bytes and native conversion. |
| `docs/facility-configuration.md` | This section | Current explanation, setup, results, debugging and practice. |
| `CAMPUSHUB_CONTEXT.md` | Final Word-template entry | Persist the current design authority and data flow. |

### 3. Changes made

The generated DOCX keeps all original ZIP entries and copies every entry except `word/document.xml` byte-for-byte, including styles, relationships, university header images and drawings. The source SHA-256 is `4554630B580E8A78D5F16BD07862BF4002A777040A8A61ED1C3B04CF53F4FC06`; the application asset matches it.

Existing blank cells receive the saved request date, client name/address/phone/email, specifics, items, received/required dates, turnaround and other service. The existing number placeholder receives the saved office number. Existing drawing boxes receive check marks in DrawingML and VML fallback; they are not replaced with HTML checkboxes. Unknown information stays blank. The four physical signature cells stay blank; a recorded application actor does not fabricate a signed official form.

Only the generated copy uses A4 portrait, following the earlier explicit paper-size request; the source is Letter. The title keeps its original two-line wording but removes overly narrow indents so saved numbers fit. Filled paragraphs can grow, the original static page-count text becomes PAGE/NUMPAGES fields, and long rows may continue rather than losing saved text. Original table grids, source spacing and assets remain. The source includes an extra empty gender rectangle; it is preserved without inventing a fourth gender option.

### 4. Functions, inputs, outputs and data flow

1. Existing authorized detail/document views obtain a real booking and keep the approved-draft rules.
2. `job_order_data(booking)` formats saved client and sidecar values, including Philippine local date/time. It returns plain presentation values, not another model or document record.
3. `job_order_docx(data)` opens the retained template, uses direct row/cell slots and returns DOCX bytes. `fill_paragraph` escapes values through XML text nodes and retains paragraph/run styles; `check_drawing` marks the existing shape corresponding to the saved selection. The current template has no fillable Word content controls, so these explicit slots are necessary.
4. `office_binary()` resolves the optional configured converter or known server-local LibreOffice paths. It does not launch the user's interactive Word instance.
5. `job_order_pdf(data)` writes the filled DOCX to a private temporary directory and runs local LibreOffice with a separate disposable profile. It reads the resulting PDF bytes, checks the PDF signature, and deletes the temporary directory. The server cache reuses the same filled document for five minutes; a change to document bytes changes its hash/key. All file routes still recheck access before serving cached output.
6. The detail API provides `job_order_document` URLs, not `job_order_html`. The shared viewer fetches the PDF through the existing admin-session fetch wrapper, so tab authentication is retained. It builds a Blob iframe only after Job Order is selected, disables Print during preparation, and offers Retry and Download Word on conversion failure. Rerender/page exit aborts pending requests and revokes old Blob URLs.
7. Print targets the PDF iframe's native print method. Export PDF downloads the same converted document; Download Word returns the filled DOCX. No online converter or public uploaded document is used.

Small annotated example:

```python
# Conceptual flow: the real route has already checked access and loaded booking.
values = job_order_data(booking)  # Input: saved reservation. Output: plain field values.
word_bytes = job_order_docx(values)  # Patch a copy; leave the source file unchanged.
pdf_bytes = job_order_pdf(values)  # Convert that Word layout locally for preview/Print.
```

Explicit slots were chosen because the official reference uses irregular merged cells and drawing-based boxes. Recreating the table from scratch or sending browser HTML through another PDF renderer would reintroduce the layout duplication the user asked to remove.

### 5. Backend and API behavior

Existing `/api/bookings/<booking_id>/documents/job-order/` remains the entry point:

- Default GET: private viewer wrapper.
- `?format=docx`: DOCX attachment, official MIME type.
- `?format=pdf`: PDF attachment.
- `?format=pdf&inline=1`: same PDF bytes inline, `X-Frame-Options: SAMEORIGIN`.

File responses are private/no-store with no-sniff. PDF setup/conversion errors return honest JSON 503; they do not fabricate a zero-value document or alter booking data. Download Word remains independent of LibreOffice. Pending bookings cannot obtain Job Orders; anonymous and service-workflow reads retain existing rejection/scope checks. Saved terminal history and read-only access are retained. No permission or payment/status transition changed.

### 6. Database, dependencies and deployment

No model/schema change, migration or live example data. Existing approved-draft preparation remains in the existing booking sidecar; this change does not add document tables. The source DOCX stays in the application package, not in public static/media storage.

`lxml` 6.1.3 was installed in this project's venv and recorded in requirements. An official, signature-verified LibreOffice 26.2.6 Windows distribution was extracted as a user-local converter at `%LOCALAPPDATA%/CampusHub/tools/program/soffice.com`. It was not registered as the default Office application. No online document service is needed.

On another server, install the requirements and provision LibreOffice; set `JOB_ORDER_OFFICE_BINARY` to its executable if autodetection does not find it. Restart Django after environment/dependency changes. Keep the template asset in deployments, and hard-refresh to load asset version `20261017-docx-template`. No database migration command is required.

### 7. Verification and manual tests

Executed: 103 targeted Django tests passed across `modules.facilities.test_booking_workflow`, `modules.facilities.test_admin_reservations`, `modules.facilities.test_calendar`, and `api.test_mobile_facility_booking` using `--keepdb --noinput`. This includes the real LibreOffice PDF path, byte preservation of every other DOCX part, saved client fields/choices, private Word/PDF/inline responses, original blank signatures, pending/anonymous/scope checks, A4 output, conversion failure with Word still available, and complete long-content continuation.

A final Word-format audit found a duplicated bold run property in the inserted Specifics text. The filler now updates the existing bold property instead of adding a duplicate; the package/private-download and real A4 export tests were rerun after that correction (2 tests passed). This keeps the original label bold and the saved text normal without invalid duplicate run properties. Both changed JavaScript files passed Node syntax checking. A local Chrome fixture harness passed at 1440, 768, 390 and 320 pixels: authenticated lazy PDF fetch, native Blob iframe, no recreated tables, Edit Draft validation/save/preview refresh, Print-button routing, conversion error/Retry, pending/read-only behavior, standalone viewer and no page overflow. The harness uses isolated database-generated fixtures and a mock network; it does not create production records.

The supplied reference and filled DOCX were rendered; the packaged `render_docx.py` completed successfully using the selected bundled Python/Poppler and native Windows LibreOffice. Original, populated, automatic and both long-content PDF pages were visually inspected. Short fixtures remain one A4 page; the 45-item fixture continues across two pages, retains Item 44 and signatures, and shows `1 of 2` in the original document-control position. Test documents are under `scratch/job-order-docx/`, not production data.

Manual checks:

1. Open an approved existing reservation > Job Order. Confirm loading resolves to the actual Word-template layout. Other tabs should not start PDF conversion.
2. Edit Draft, change an allowed saved field and save. Confirm the preview reloads; Download Word and Export PDF show that saved value. Verify the reference file was not changed.
3. Use Print. Confirm the PDF print view, paper size and real printer settings. Try Open PDF if the browser does not embed PDFs.
4. Sign out or use an unauthorized account; direct document URLs must not expose the files. Check Pending remains unavailable and a view-only reader has no Edit Draft.
5. In an isolated test environment, configure a nonexistent office binary; confirm an honest error/Retry, while Word download still succeeds. Restore the setting afterwards.

### 8. Limitations, debugging and learning practice

- The full repository test suite, a physical printer/interactive print dialog and an Android device were not tested in this change. Chrome verification checked the Print control's PDF target; it did not claim physical printing succeeded.
- Browser PDF plugins control toolbar/zoom/printing and can vary; the Open PDF fallback and Word download remain available. LibreOffice may have small rendering differences from Microsoft Word. A changed server font set can alter wrapping; keep expected fonts installed and visually review official output before deployment.
- A substantially different replacement DOCX needs a reviewed slot map. Do not swap in an unrelated form and assume the same row/drawing IDs work. The original letterhead is body artwork on the first page; long continuations do not invent a repeated new letterhead.
- Conversion can take several seconds on its first call. Missing binary -> inspect `JOB_ORDER_OFFICE_BINARY`, server-account access and the installed tool path. 503 after conversion -> check converter availability, fonts, temporary-directory access and timeout. Do not remove RBAC to fix document access.
- Preview access fails but the file exists -> check the real admin tab session, network response status and Content-Type. A login HTML response must not be treated as a valid PDF. The browser wrapper fetches with authentication instead of putting a secret in a public iframe URL.
- If only appearance changed, compare the source hash and `word/document.xml` slots before changing pricing, booking or payment code. Source reference instructions and old sample field contents are not new application commands.

Safe practice exercise: on a development/test booking, change only Details / Specifics in Edit Draft. Predict its destination (main table row 9), save, download Word and PDF and compare that cell. Verify the same client/reservation/status and blank physical signatures remain. Then run `manage.py test modules.facilities.test_booking_workflow --keepdb --noinput` and restore your test field. For layout experiments, copy the template to `scratch/`; never edit the authoritative asset or production data as a practice step.


## Job Order plain paper display and Export menu (October 17, 2026)

This supersedes only the embedded browser PDF viewer in the previous Word-template section. The retained DOCX and its filled PDF remain the authoritative document; the screen now shows the paper without Chrome's dark toolbar, thumbnails or scrolling frame.

### 1. Cause and reason

Confirmed: the previous Blob iframe loaded Chrome's built-in PDF application. Its dark toolbar and thumbnail panel belong to the browser, so the surrounding CampusHub stylesheet cannot reliably turn them into plain paper. Instead of rebuilding the official form, the screen now paints pages from the same generated PDF using locally hosted PDF.js. Mozilla documents this page-to-canvas approach in its [official examples](https://mozilla.github.io/pdf.js/examples/).

### 2. Exact files and current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/static/components/js/job_order_preview.js` | 4 `assets`; 7 `pdfLibrary`; 14 `release`; 21 `load`; 81 `print`; 94 `exportMenu` | Replace visible PDF iframe with plain PDF page canvases; shared two-format Export dropdown; retain Print and cleanup. |
| `backend/static/components/css/job_order.css` | 5 `.beu-job-preview`; 7 `.beu-job-paper`; 11 `.beu-job-export`; 33 mobile rules | Center white paper at up to 794 CSS pixels, scale down on narrow screens, space multiple pages and style the compact Export menu. |
| `backend/static/components/js/admin_booking_workflow.js` | 94 `jobDoc` and following Job Order toolbar | Replace separate Export PDF / Download Word buttons with one shared Export menu. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 10 `data-job-export`; 15 viewer script | Use the same Export menu on the standalone document page; update asset version. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 15 stylesheet; 75 viewer script | Refresh affected asset versions to `20261017-job-paper`. |
| `backend/static/vendor/pdfjs/6.4.299/` | `build/pdf.mjs`, `build/pdf.worker.mjs`, `standard_fonts/`, `wasm/`, `LICENSE`, `package.json` | Add 33 local distribution/runtime/license files, approximately 5.44 MB, without a CDN dependency. |
| `docs/facility-configuration.md` | This section | Record the final behavior, tests, dependency and debugging guidance. |
| `CAMPUSHUB_CONTEXT.md` | Final plain-paper entry | Persist the current screen/export behavior. |

The PDF.js distribution was downloaded from the official npm package `pdfjs-dist@6.4.299`; its archive was checked against npm's published SHA-512 integrity before selecting files. The official [release](https://github.com/mozilla/pdf.js/releases/tag/v6.4.299) and included Apache-2.0/dependency licenses are retained. Source maps, the full sample viewer, Node canvas packages and unrelated tooling are not needed by this browser-only subset.

### 3. Changes made

- Display white document pages only: no visible iframe, browser toolbar, thumbnail sidebar, zoom strip or preview helper paragraph.
- Keep the source form's actual layout, text and check marks by rendering the generated PDF, not by constructing replacement HTML tables.
- Keep Edit Draft and Print. Replace the two separate file buttons with Export, containing PDF (.pdf) and Word (.docx).
- Use native details/summary disclosure with visible focus; Escape returns focus to Export, outside click closes it, and selecting a format closes it. Mobile menu alignment stays inside the content area.
- Keep loading, honest conversion/access errors and Retry. Unknown client information and physical signature cells remain governed by the original Word filling rules.

### 4. Functions, inputs, outputs and data flow

`pdfLibrary()` imports the pinned local renderer only when a document is requested and points its worker/font/WASM paths at the same local static directory. `load(host)` receives the existing private PDF URL, fetches it through the existing admin-session wrapper and checks its status and Content-Type. It hands the bytes to PDF.js, renders every page sequentially, and builds a centered white paper section for each canvas. A visually hidden plain-text copy supports reading by assistive technology. The canvas is not an alternate form calculation or data source.

The screen scales the document to the available width; rendering at up to twice the CSS resolution keeps text clear on dense displays. The saved file bytes remain separate from the painted screen. `release()` aborts requests, cancels/destroys PDF rendering, removes any print iframe and releases Blob URLs. Existing tab/save rerenders call `dispose()` first, so older document resources do not remain active. Returning from browser history reloads a visible document as needed.

`exportMenu(pdfUrl, docxUrl)` builds one shared control from existing protected download URLs. Both embedded and standalone pages reuse it. `print(host)` uses the original PDF Blob in a hidden print iframe created only when Print is requested; the normal page never embeds the dark PDF application. Repeated clicks wait for that frame to load rather than printing a not-yet-loaded frame.

Annotated flow:

```javascript
// Input: the existing permission-checked PDF URL from Django.
CampusHubJobOrder.load(document.querySelector('[data-job-preview]'));
// Output: white page canvases from that PDF, with no recreated form tables.
// Export links still request the original protected format=pdf or format=docx route.
```

This approach was chosen because changing iframe styling cannot reliably remove browser-owned controls, while PDF page rendering preserves the actual DOCX-derived form.

### 5. Backend and API behavior

No backend view, route, permission, model, booking/payment status or document calculation changed in this step. The same protected `format=pdf`, inline PDF and `format=docx` routes remain. Admin tab authentication still travels through the existing fetch wrapper and export-link handler. Static renderer assets are public application code; private booking documents are not moved into static storage or uploaded to another service.

### 6. Database and deployment impact

No migration, database rewrite, production fixture, new Python package or server-side Node runtime requirement. Keep existing local LibreOffice and lxml from the preceding implementation. Deploy the new `backend/static/vendor/pdfjs/6.4.299/` assets through the usual static-file process. Serve `.mjs` as JavaScript and `.wasm` as `application/wasm`; Python's current MIME mapping was verified. Hard-refresh the document page to load `20261017-job-paper`.

### 7. Tests performed and manual checks

Executed three existing Django tests: `test_official_job_order_pdf_is_a4_and_private`, `test_job_order_fills_original_package_and_private_downloads` and `test_job_order_pdf_failure_preserves_record_and_word_access`; all passed. These exercise the real converter, protected downloads/package preservation, and conversion failure with Word still available. This UI change did not require duplicate unit tests for the same backend calculations.

Both changed JavaScript files passed Node syntax checks. Chrome checks passed at 1440, 768, 390 and 320 pixels, using the actual locally hosted PDF.js module/worker and real test-generated PDFs. Verified: lazy authenticated fetching, white canvases with no visible PDF iframe or recreated tables, Export's two existing format URLs, retained tab-token handling, Escape/outside/selection closure and focus, Print-button routing, Edit Draft/save/refresh, error/Retry, Pending and read-only behavior, standalone viewer, no page overflow, and two-page rendering retaining the last recorded item. Desktop/mobile screenshots were inspected and mobile menu alignment was corrected. Additional focused standalone-menu checks passed at 390 and 320 pixels, keeping its right-aligned Export options inside the viewport. Fixtures were isolated, not inserted into production.

Manual checks:

1. Open an approved Booking Details > Job Order. Confirm the form is centered white paper, with no dark viewer/sidebar.
2. Open Export, choose PDF, then Word. Both should download the saved document; neither should create a new booking or change its status.
3. Use keyboard Enter/Space to open Export and Tab to its options; Escape should close it and return focus to Export. Click elsewhere to close it.
4. Save an allowed Edit Draft change and confirm the paper refreshes. Check a long test document displays every page.
5. Use Print to check the native print dialog and your actual printer settings.

### 8. Limitations, debugging and safe practice

Physical printing, screen-reader hardware, Android hardware and other browser engines were not tested. The browser checks simulate phone-sized web viewports, not the Flutter application. Canvas text is not directly selectable on screen; use the PDF/Word export for full document text selection or editing. The actual file and official form content remain unchanged.

If paper fails to display, check for a 404 or wrong MIME type on the pinned local `.mjs`, worker, font or WASM assets; deploy the complete retained subset rather than weakening permissions. Export remains available during a renderer failure. A PDF 401 means the admin tab session needs renewal; a PDF 503 still points to the existing server converter/template checks. Do not restore the dark browser viewer as a fake successful page or rebuild the form in HTML.

Safe practice: in a local development copy, temporarily change `.beu-job-pages` gap from 24px to 32px and open a two-page test document. Verify only the on-screen space between papers changes; exported PDF page positions must remain unchanged. Restore the CSS value afterwards. This teaches the separation between screen presentation and the authoritative Word/PDF layout without editing production records.


## Payment tab sections, compact record table and private receipts (October 17, 2026)

This updates the Payment tab presentation described in the earlier contextual-payment guide. The latest refinement replaces the open record grid with a compact bordered table. Existing booking/pricing totals, payment validation, payment storage and audit transitions remain authoritative.

### 1. Cause and reason

Confirmed: the old renderer repeated Amount Paid and raw payment Status beneath the summary, mixed receipt links into the record grid, and showed no section headings. The existing attachment route also always forced a download, so merely naming a link View Receipt would not provide a true viewing action. This change separates the information and adds a restricted inline option to the existing private route.

Latest confirmed layout issue: after that separation, Payment Record Details still used a spacious two-column field grid. Five short record values did not need that much whitespace. Only its presentation is changed to a semantic two-column table; the four summary values, saved financial records and backend rules are preserved.

### 2. Exact changed files, current lines and nearby anchors

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/static/components/js/admin_booking_workflow.js` | 61 `paymentValue`; 65 `paymentRecordTable`; 72 `renderPayment`; 176 `original_amount_due`; 249 `paymentRecord` | Latest change: five escaped table rows, clean missing-value display and explicit Payment Status labels. Existing summary, record selection, dates, receipts and form behavior are reused. |
| `backend/static/components/css/admin_booking.css` | 29 `Payment groups`; 38 `.bk-payment-record`; 69 responsive table rules | Latest change: compact bordered record table, 32% desktop label column, wrapped values and stacked label/value rows at widths up to 768px. Summary styling remains unchanged. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 101/130 `view_url`; 354 `attachment`; 367 `inline` | Add safe receipt-view URLs and permit inline delivery only for supported receipt types belonging to the booking. |
| `backend/core/modules/facilities/services/schedules.py` | 78 `PRIVATE_ATTACHMENT_TYPES`; 93 image branch | Reuse one file-type allowlist for existing validation and safe inline viewing; upload rules remain the same. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 13 stylesheet; 72 workflow script | Payment table asset version was `20261017-payment-table`; the later Overview update now versions these shared assets as `20261017-booking-overview`. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 648 `test_payment_receipt_view_download_and_history_are_private`; 701 `test_receipt_inline_rejects_legacy_active_content` | New real-data regression tests for private view/download, unchanged totals/audit counts, historical records and unsafe legacy attachment types. |
| `docs/facility-configuration.md` | This section | Implementation, formulas, data flow, debugging, results and practice. |
| `CAMPUSHUB_CONTEXT.md` | Final Payment tab entry | Preserve the current interface and workflow boundaries. |

The compact-table refinement changes only the JavaScript, CSS and template asset versions listed above, plus this guide and the context entry. The Python views, shared attachment allowlist and test additions in the table belong to the preceding Payment section/private-receipt implementation; they were reused unchanged in this refinement.

Unchanged models/helpers reused: `backend/core/api/models.py:521` Booking, `:578` FacilityBookingRequest and `:592` FacilityPayment; `services/booking_workflow.py:50` paid_summary, `:123` allowed_actions and `:211` transition. Existing `read_access`, `physical_bookings`, attachment storage, actor snapshots and audit helpers remain in use. No second payment model, receipt store or calculation service was introduced.

### 3. UI sections and removed duplication

Payment Summary contains exactly Original Amount Due, Amount Paid, Remaining Balance and a Payment Status badge. It retains the existing 2 x 2 desktop layout and mobile behavior. Paid uses navy/white; Unpaid uses a restrained gold treatment.

Payment Record Details now has a bordered table headed Payment Detail / Information. Its five rows are Official Receipt No., Payment Method, Date Paid, Recorded / Verified By and Notes. Values wrap, Notes preserves line breaks, and compact 8px vertical padding replaces the open field grid. At widths up to 768px each row stacks its label above its value without page overflow. The column headings remain in the document for assistive technology, and row headers use `scope="row"`. No new card or decorative color is added.

Payment Record Details shows actual selected saved values. A single successful payment does not repeat Amount Paid or its status here. With several records, or a failed record, a compact Payment Status / Recorded Amount context identifies that transaction without changing the booking summary. History also uses the explicit Payment Status heading. Empty optional metadata and the literal placeholders `null`, `NoneType` and `-` display as Not recorded, or None for Notes; a genuinely recorded `N/A` value is preserved. These are display fallbacks, not database repairs.

Receipt Attachment has the exact absent message `No receipt attachment uploaded.` Supported files offer View Receipt and Download Receipt, with the actual filename. Existing extra stored payment documents are retained and duplicates are filtered by their actual URLs.

Payment Actions appears only when the existing backend `booking.actions` permits Record Payment. The current payment form remains, including its existing cash method, outstanding Amount Due, payment amount, OR, Philippine local date, authenticated recorder, notes and optional receipt. An additional read-only Original Amount Due shows the real booking charge separately from the outstanding balance. The backend does not trust either posted display amount or a posted recorder.

There is no paid Edit Payment, standalone receipt replacement/upload, refund, print-record or export-payment button because those correction/report actions are not implemented in this workflow. Receipt upload remains part of Record Payment. The Booking Slip, Job Order, Inspection and Activity tabs retain their existing behavior.

### 4. Functions, inputs/outputs and data flow

The existing authorized detail endpoint returns a booking row from `booking_row` / `paid_summary`, real FacilityPayment rows, and safe receipt metadata from existing sidecar JSON. The browser does not subtract or sum payment amounts again.

- `date(value, options)` retains the old default for other sections. `paymentDate(value)` supplies only display options: short month, date/year, 12-hour time and Asia/Manila. It does not reinterpret or save a timestamp.
- `dl(values, className)` still produces the original details grid for other sections. The Payment record no longer uses that grid; unrelated tab layout is unchanged.
- `paymentValue(value, fallback)` accepts a saved optional value and returns its trimmed text or a display fallback. It is used for record fields and optional history metadata, never for computing amounts or changing stored records.
- `paymentRecordTable(fields)` accepts the five label/value pairs and returns the scoped table markup. It escapes both labels and values before interpolation. Semantic row headers keep each value associated with its label; scoped CSS changes presentation at the tablet breakpoint without duplicating the data.
- `renderPayment(paymentId)` takes the current authorized payload, selects that actual payment ID or the newest returned record, and renders the four summary values, five record fields, receipt section and allowed action. A history table is created only when more than one real payment row exists.
- Clicking a history receipt-number button changes only the selected details/receipt. It updates `aria-pressed` and restores focus; it does not send a payment update or create an activity record.
- `receiptLinks(file)` consumes existing file name/download URL plus the server-provided optional `view_url`. It never reconstructs file content or creates storage.
- The existing attachment view checks access and the current physical booking before finding the saved file. `?inline=1` applies only when its key is in that booking's payment records and the MIME type belongs to `PRIVATE_ATTACHMENT_TYPES`. Other requests keep attachment delivery.

Safe read-only example in the authenticated Booking Details browser console:

```javascript
const saved = JSON.parse(document.getElementById('bkBookingDetailData').textContent);
// Read the server's three distinct amounts; do not recompute or overwrite them.
console.log(saved.booking.total_amount, saved.booking.paid_amount, saved.booking.amount_due);
```

The approach keeps business rules in Django and gives the UI one job: organize and format already-authorized data. A read-only input improves clarity; server-side validation is what protects the charge.

Annotated display example: a saved `notes: null` enters `paymentValue(selected.notes, 'None')`, producing the text None. `paymentRecordTable` escapes that text and places it in the Notes row. A saved note containing `<script>` is displayed as text rather than executed. Neither example creates a new payment or modifies the saved note.

### 5. Backend behavior, formulas, statuses, receipts and history

Existing calculation, unchanged:

```text
Total Amount Paid = sum(paid_amount for actual records with payment_status = paid)
Remaining Balance = max(Original Amount Due - Total Amount Paid, 0)
Payment Status = Paid only when a valid paid record exists and its total covers the booking
Otherwise Payment Status = Unpaid
```

FacilityPayment supports Paid, Unpaid and Failed record statuses. The booking summary currently supports Paid/Unpaid. Labels are displayed with proper capitalization; Partially Paid, Pending Verification and Refunded are not invented. Failed transaction amounts do not increase the summary's paid total.

The current writer explicitly requires Amount Paid to equal the full outstanding balance and rejects partial entry. There is no new installment or refund architecture. The existing ForeignKey and summary already support multiple stored rows, including historical failed/paid rows; those real rows now have conditional history. A historical outstanding balance can still be settled through the existing full-outstanding validation.

The receipt endpoint remains `/api/bookings/<booking_id>/attachments/<key>/`. Default GET downloads the existing bytes; a supported receipt `?inline=1` lets the browser view those same bytes. JSON adds optional `view_url` beside existing receipt metadata, including existing payment-document metadata. No file bytes enter the detail JSON.

Both responses retain `Cache-Control: private, no-store`, no-sniff and existing authentication/RBAC checks. PNG, JPEG, WebP and PDF are the same types already accepted by validation. Unsupported legacy content, such as HTML, does not get an inline URL and remains a forced download even if an inline query is supplied. Other attachment categories keep their existing default download behavior. Viewing/download/history selection create no duplicate payment or audit events; the existing recording events still appear in Activity.

### 6. Database impact and commands

No schema/model change, migration, new package, live sample data, payment rewrite or route registration. The compact-table refinement changes no backend/API code, permissions, totals, statuses, attachment storage or audit behavior. It consumes the same existing detail endpoint and metadata. No migration or special command is needed; hard-refresh the browser to get `20261017-payment-table`. Normal deployments should include the updated static assets using the project's normal static-file process.

Latest targeted verification command from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.facilities.test_booking_workflow.BookingWorkflowTests.test_payment_requires_or_full_amount_and_approved_state modules.facilities.test_booking_workflow.BookingWorkflowTests.test_paid_state_derived_and_retry_cannot_duplicate_payment modules.facilities.test_booking_workflow.BookingWorkflowTests.test_payment_receipt_view_download_and_history_are_private --keepdb --noinput
```

### 7. Tests and manual verification

Latest compact-table refinement: the three existing Django tests in the command above passed (3 tests, OK; system checks clean). They verify existing full-outstanding/OR/approved-state validation, paid totals and duplicate prevention, and private receipt/history behavior. No new backend behavior or tests were needed for this display-only change.

Latest Chrome batch passed at 1440, 768, 390 and 320 pixels using five isolated Django-generated states: unpaid, paid, paid without a receipt, multiple records and read-only. It verified exactly four summary fields, five correctly headed record rows, desktop table versus stacked tablet/phone rows, clean optional placeholders, conditional history and focus/receipt selection, private links/auth-token preservation, permission-gated actions, Manila dates with a New York browser timezone, unchanged form fields, simulated rejected/successful submit/refresh, and no page overflow. The API responses in this UI harness are isolated fixtures; backend writes and privacy are verified by the separate Django tests. Desktop and phone screenshots were inspected. JavaScript syntax passed. No production record was created by these checks.

Earlier section/private-receipt implementation verification, retained as history (not rerun in full for the compact-table refinement): all 57 booking workflow Django tests passed, followed by the existing Calendar private-attachment test (1 passed). Coverage included actual Record Payment rules, original-charge/recorder authority, OR uniqueness, duplicate payment rejection, Philippine past/current/future dates, paid summaries and permissions, private receipt inline/download headers and bytes, cross-booking denial, anonymous denial, unchanged audit counts, existing historical rows and forced download of legacy active content. Existing document/export/inspection tests in that workflow suite also passed.

Earlier layout verification: JavaScript syntax checking and targeted whitespace checks passed. The Impeccable layout detector returned no findings before/after, but reported degraded regex-only operation because its parser modules are unavailable; this is not a full automated accessibility or computed-style assessment. Source review and Chrome screenshots supplied the layout evidence.

Earlier field-grid browser checks also covered long receipt numbers/names, multiline notes, escaped script-like text and a single failed record. Those checks predate the compact table; do not interpret them as a new table stress-test run. Current fixtures and the compact-table harness stay in `scratch/payment-tab/`, outside production records.

Manual tests:

1. Open an unpaid approved reservation's Payment tab. Check the original amount, zero paid amount, outstanding balance, Unpaid badge, honest empty messages and Record Payment only when permitted.
2. Record a genuine allowed cashier payment with its OR and a supported receipt. Confirm paid amount/balance/status update, the original charge stays the same, the action disappears and Activity keeps the existing events.
3. Choose View Receipt and Download Receipt. Confirm viewing versus download and identical file content. Try an unauthorized session; direct links must not expose a receipt.
4. Open a paid booking without a receipt. Check the exact absent message and no fabricated upload/edit action.
5. Where genuine historical multiple records exist, select each receipt number. Check details/receipt follow selection while the summary remains unchanged. A single record must not produce an empty history table.
6. Check a narrow viewport and keyboard focus: record labels must stack above values without page overflow. On desktop the five records should be a compact bordered table while the summary stays 2 x 2. Inspect Overview, Booking Slip, Job Order, Inspection and Activity for unchanged behavior.

### 8. Debugging, limitations and learning practice

No new correction, partial-payment, refund or after-payment receipt replacement workflow was added. Legacy records without method/recorder metadata show Not recorded rather than guessed values. Unsupported historical file types can be downloaded but are not offered inline viewing. Browser PDF viewing still depends on that browser's file support; a normal download remains available.

The full repository suite, physical Android device, actual printer and screen-reader hardware were not tested. Browser mobile-width checks cover the Django web page, not a Flutter application change. The display cleanup is not an approval to change live financial records.

If totals look wrong, inspect the existing booking total and which actual FacilityPayment rows have status paid; do not patch the sum in JavaScript. If View still downloads, check the `view_url`, `inline=1`, supported MIME type and whether the key belongs to payment metadata. If it returns 401/403, check the admin tab session/role; do not remove access checks. Missing files should return 404. If the screen still shows the old duplicate block, hard-refresh and confirm the new script/CSS version. A blank method/actor on an old record is incomplete recorded history, not permission to invent those fields.

Safe practice: on a local test booking, read the three server amounts with the console snippet above and compare them with the four summary entries. Select another historical record, if present, and verify only details/receipt change. Then temporarily change the table cell vertical padding from 8px to 10px in local CSS, inspect desktop/mobile and restore it. Verify the five labels, receipt links and server amounts remain identical. No payment record or database value needs to be changed to practice layout work. The existing tests are the verification step before keeping a code change.

## Job Order preview loading speed (October 17, 2026)

### 1. Confirmed cause / reason

The converter previously created a brand-new LibreOffice profile for each uncached document. The PDF cache lasted only five minutes. On screen, PDF.js started loading after conversion/download finished, every page was rendered before any paper appeared, and a narrow phone still rendered a 794px-wide canvas.

Local isolated-fixture measurements before the change: first conversion 18.784 seconds, unchanged cached calls 0.071 and 0.042 seconds. A separate controlled profile check measured a new profile at 17.667 seconds versus the same profile's second conversion at 4.269 seconds. This confirms that Office startup/profile preparation is a substantial part of the delay; it does not establish a production network or database delay.

### 2. Exact files, current lines and nearby anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/job_order_docx.py` | 21 `_conversion_lock`; 202 `office_profile`; 207 `job_order_pdf`; 236 `timeout=3600` | Reuse one private temporary Office profile per Django worker, serialize conversion, recheck the existing content cache after waiting, retain PDFs for up to an hour. |
| `backend/static/components/js/job_order_preview.js` | 32 fetch/conversion comment; 46 `Promise.all`; 61 `width`; 71 completed-page comment; 84 error cleanup | Download the renderer and authenticated PDF concurrently, fit canvas resolution to its actual screen width, append each completed page immediately, preserve disabled Print on failure. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 71 `job_order_preview.js` | Refresh the viewer asset version to `20261017-job-preview-speed`. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 15 `job_order_preview.js` | Use the same version on the standalone document page. |
| `backend/core/modules/facilities/test_job_order_preview.py` | 16 `JobOrderPreviewTests`; 40/55/63/80 test methods | Four isolated tests for cache reuse/invalidation, profile reuse, concurrent duplicate requests and recovery after failed conversion. |
| `docs/facility-configuration.md` | This section | Cause, functions/data flow, measurements, tests, troubleshooting and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | Final Job Order preview performance entry | Preserve the current cache/profile/loading boundaries. |

### 3. Changes made

The existing DOCX template, saved fields, plain white paper, PDF/Word Export menu, Print source and Edit Draft workflow remain. Conversion folders are still separate and removed after each job; only this worker's private Office configuration profile is reused. `--nologo`, `--nodefault` and `--norestore` avoid unnecessary startup/recovery behavior. The process-local lock prevents two conversions from interfering with that profile and stops simultaneous identical requests from converting twice.

The client starts PDF.js and its authenticated PDF request together. As soon as a page finishes rendering, that page becomes visible; it no longer waits for later pages or their text extraction. Accessible document text is still extracted for each page. On smaller screens, the canvas uses the actual host width and up to 2x device pixel ratio. Original PDF bytes and export/print resolution are unaffected.

### 4. Functions, inputs/outputs and data flow

- `office_profile()` takes no business data and returns a retained `TemporaryDirectory` object for the current Python worker. Holding the object keeps the private profile alive; normal process exit cleans it up. This is not a public media folder or a stored booking document.
- `job_order_pdf(data)` accepts the existing saved presentation dictionary and returns PDF bytes. It still calls `office_binary()` and `job_order_docx(data)`. SHA-256 of the complete filled DOCX is the existing cache identity. Changed saved text or template bytes produce another key automatically.
- A cache hit returns those same bytes immediately. A miss waits for the worker's conversion lock for at most 60 seconds, checks the cache again, then converts in a fresh job folder using the reused profile. Only validated `%PDF-` output is cached. `finally` releases the lock on both success and failure. A busy timeout or conversion failure keeps the existing error/Retry/Word-download path.
- `load(host)` keeps the existing lazy per-tab lifecycle and abort/cleanup. Its `Promise.all` joins two independent operations: authenticated PDF download and renderer-module loading. It parses the real PDF once and appends completed canvases in page order. The native Print iframe still uses the untouched PDF Blob.

Data flow: authorized existing document view -> saved booking/Job Order values -> unchanged DOCX filler -> content-keyed PDF cache -> locked local conversion only on a miss -> private response -> parallel renderer/download -> completed page canvases. No booking, payment or audit record is written by this performance change.

Annotated example: two simultaneous requests with the same filled DOCX hash both miss the initial cache. Request A converts while Request B waits. A caches the PDF and releases the lock. B's second cache check returns A's bytes without starting Office. A later saved draft change creates a different hash and converts the new document instead of returning stale paper.

### 5. Backend / API behavior

Existing document URLs, RBAC, authentication, `private, no-store` responses, MIME validation, attachment filenames and PDF/DOCX formats are unchanged. The cache is server-side only; it does not make a document publicly cacheable. Every request still passes the existing authorization checks before conversion/cache access. There is no new endpoint, background queue, duplicate document renderer, model, payment rule or permission bypass.

### 6. Database / migration and commands

No database migration, new package or configuration change is required. Let Django's normal development autoreload pick up the Python change, or restart the deployed Django workers normally; hard-refresh the browser for `20261017-job-preview-speed`. Use the project's existing static deployment process for changed assets. No Office service or public listener needs to be started.

Run the new focused tests from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.facilities.test_job_order_preview --keepdb --noinput
```

### 7. Tests performed and measured behavior

Executed eight focused Django tests, all passed; system checks clean. Four new tests cover unchanged cache reuse, one-hour timeout, saved-field/template invalidation, reused profile with separate job folders, duplicate conversion coalescing, and uncached failure followed by a successful retry. Four existing workflow tests exercised real LibreOffice conversion: unchanged original DOCX package/private downloads, one-page A4 output and real saved text, complete long two-page content, and converter failure preserving saved records and Word access.

After the change, a separate local process measured first conversion 10.148 seconds, changed saved content using its warmed profile 3.669 seconds, and an unchanged cached request 0.032 seconds. First-run timing varies with machine/OS/tool state; the 10.148 versus 18.784 measurements are observations rather than a guaranteed cold-start speedup. The controlled new/reused-profile check above demonstrates the repeated conversion benefit.

Chrome checks passed at 1440, 768, 390 and 320px with actual local PDF.js modules/workers and existing isolated PDF/booking fixtures. The harness deliberately delayed the PDF response 300ms: renderer-module requests began before that response completed at all four widths. It also verified that the first page became visible before the second page completed, fitting canvas resolution, saved-draft refresh, error/Retry, pending/read-only handling, private token links, Print routing, Export menu keyboard/outside behavior, standalone paper and no page overflow. Desktop and phone screenshots were inspected. JavaScript syntax and targeted whitespace checks passed. Mocked browser HTTP responses are layout/interaction evidence; Django tests separately verify server behavior. No production records were created.

Manual verification:

1. Open an approved booking > Job Order. Let the first conversion complete; switching away and back should keep the loaded paper without another request.
2. Reload the same booking and reopen Job Order. An unchanged document should use the server PDF cache. Compare its Network request duration with the initial conversion.
3. Save one allowed Edit Draft change. Confirm the new text appears in preview and PDF/Word exports; stale paper must not be returned. Check a long document reveals its first page while later pages finish.
4. Confirm Print still opens the same PDF, and unauthorized sessions cannot access the existing document URLs.

### 8. Remaining limitations, debugging and safe practice

The first conversion after a worker starts can still take several seconds (locally about 10-19 seconds). The current default in-memory cache and profile are per worker; restarting a worker clears them, and another worker has its own warm-up. Cache entries may also be evicted before the one-hour expiry. Different documents queue within one worker to protect its profile; a 60-second queue wait returns an honest Retry error. The converter keeps its existing 60-second execution limit. This change does not install a persistent Office daemon or an asynchronous job system.

If Preparing document remains visible, inspect the existing PDF request in browser Network: a long request points toward server conversion/queue/load; a quick PDF followed by delay points toward PDF.js worker/font/WASM/network/rendering. Check converter availability, temporary-directory permissions and server load for 503 responses. A 401/login response means session renewal, not permission removal. If new saved text is missing, confirm Edit Draft saved successfully and its response contains the new value; the DOCX hash must then differ. After replacing converter binaries/fonts without changing document bytes, restart the workers to clear old rendering caches. Do not delete another user's Office profile or stop their Word/LibreOffice processes.

Safe practice: run `JobOrderPreviewTests` in the isolated test environment, then change only the test's second `items` value and rerun. Verify the changed document triggers a second conversion while the identical request triggers only one. Restore the test text afterwards. This teaches content-based invalidation without touching real bookings or payment data. Actual printer hardware, physical Android, other browser engines, full-repository tests and production-concurrency benchmarks were not run.

## Booking Overview sections and Completion Readiness (October 17, 2026)

### 1. Cause / reason

Confirmed: Overview combined booking, pricing and approval fields in one grid, repeated the header statuses, put Purpose in a separate block, and placed Cancel Booking beside Complete Booking. The backend already rejected early completion inside `transition`, but `allowed_actions` advertised completion for any approved paid booking without checking the schedule or inspections. The UI and writer therefore disagreed about readiness.

Pricing Method was read only from `details.pricing_method`. Current admin/mobile creation already saves that field; older incomplete records can lack it. The fallback now uses the saved quote's `price_type` or the existing facility configuration, preserving any saved method first. Unknown methods are hidden instead of labeled Not recorded. No pricing calculation was changed.

The existing inspection model is saved JSON with findings and a free-text deposit decision. It has no reliable structured unresolved/resolved charge flag. The user explicitly selected a required staff confirmation that damage, deposit and additional charge issues are resolved. The system records that acknowledgement without pretending that free-text findings establish a cleared balance or creating a separate refund/charge ledger.

Latest correction: a missed required pre-use inspection becomes the non-blocking warning `Pre-use inspection was not recorded.` after the reservation ends. The earlier implementation incorrectly kept it as a completion blocker. No independently confirmed BEU exception was found in the inspected workflow/configuration; the existing pre-use-required flag controls before-use work, not a requirement to recreate history after use. Completion Readiness now reports only real remaining blockers, keeps Complete Booking disabled with the actual reason, and requires damage/deposit handling only for a positive saved deposit or recorded post-use issue.

### 2. Exact files, current lines and nearby anchors

| File | Current line / nearby anchor | Change |
| --- | --- | --- |
| `backend/static/components/js/admin_booking_workflow.js` | 99 `completionChecklist`; 102 `renderOverview`; 143 Completion Readiness; 166 inspection kinds; 246 decision form; 275 boolean serialization | Warning versus blocker icons, server count/reason, disabled/ready action, conditional review and existing inspection editor. |
| `backend/static/components/css/admin_booking.css` | 30 `.bk-overview-section`; 48 `.is-warning`; 49 `.bk-completion-state`; 50 disabled primary action | Preserve layout and palette; distinguish advisory warnings and disabled completion. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 13 CSS; 44 `bkPanelOverview`; 72 workflow script | Asset version `20261017-completion-readiness`; existing sections retained. |
| `backend/core/modules/facilities/services/booking_workflow.py` | 123 `allowed_actions`; 214 `reservation_start`; 224 `completion_issues`; 246 `inspection_actions`; 268 `completion_readiness`; 339 completion; 407 inspection | One backend rule set for phase-aware inspections, advisory missed pre-use work, real resolution and final locked completion. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 18 helper import; 148 `completion`; 150 `inspection_actions` | Add allowed inspection kinds to the existing protected detail response; RBAC retained. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 487 required-inspection test; 546 deposit test; 576/594/610/629 new phase/resolution tests | Updated intended behavior plus recorded pre-use, no fake deposit/damage, damage without deposit and deposit review without required post-inspection. |
| `docs/facility-configuration.md` | This section | Implementation, data flow, API contract, debugging, commands, limitations and learning exercise. |
| `CAMPUSHUB_CONTEXT.md` | Final Overview/completion entry | Preserve these workflow/presentation decisions. |

Reused unchanged: Booking, Facility, FacilityPayment and the existing FacilityBookingRequest JSON sidecar; `paid_summary`, `rules`, `metadata`, `actor`, `save_details`, the Facility-then-Booking transaction lock, `audit`, authorization checks, quote calculation and Activity retrieval. No new business models or duplicate payment/pricing/inspection module were added.

The latest correction changes the six application/test files above plus this guide and `CAMPUSHUB_CONTEXT.md`. The existing audit helper in `admin_booking_views.py:56` and its resulting-status metadata remain unchanged in this correction.

### 3. Changes made / Overview structure

The five sections are Booking Information, Pricing Summary, Approval Information, Notes and Completion Readiness. Booking Information shows the saved booking ID, requester, facility, optional real room, source, date/stay, time, participants/guests, optional recorded nights and Purpose. Purpose wraps within that information section. Booking Status and Payment Status stay in the page header.

Pricing uses the saved quote's Base Rental, Discount, Additional Fees, Damage Deposit and Rental Total plus the backend's Amount Paid and Remaining Balance. A positive saved discount is displayed with a minus sign; no totals are recalculated in JavaScript. In this project's existing quote, `rental_total` excludes the damage deposit. When it differs from the real booking charge, an additional Total Amount Due row shows `booking.total_amount` so the breakdown remains honest. Missing historical breakdown fields remain Not recorded rather than fabricated zeroes.

Approval Information shows actual submission/approval data, or Awaiting approval / No approval recorded as appropriate. Real rejected bookings show the existing `details.reject` actor, timestamp and reason. Notes is a small plain text section with the exact empty text No notes provided.; null, NoneType, dash and the legacy Not recorded placeholder do not become notes. User text is escaped and line breaks are retained.

Completion Readiness shows the real backend checklist. Satisfied checks have navy checks, advisory missed pre-use work has a gold warning triangle, and unfinished blocking requirements have an open circle. The exact remaining count comes from Django and excludes advisory warnings. The authorized Complete Booking button remains visible but disabled while real requirements remain, associated with the actual reason; it becomes enabled with Ready for completion. A historical missed pre-use warning remains visible without falsely becoming a completed inspection. Cancel Booking stays inside More Actions. Completed, cancelled and rejected records do not offer invalid terminal actions.

The existing post-use Inspection form now also saves the existing damage/deposit decision with a staff-confirmed resolution boolean. A post-use record may be saved while issues are unresolved; readiness stays blocked. A decision alone is not claimed to be resolved. A real deposit without a configured post-inspection requirement uses the same stored post-use record as Damage / Deposit Review, without inventing a required post-inspection checklist item. No deposit or issue means no resolution requirement or final resolution checkbox.

### 4. Functions, inputs/outputs and data flow

- `completion_readiness(booking, summary=None)` accepts the existing booking and optionally its already-loaded payment summary. It returns `eligible`, `checks`, `remaining_count`, `reason` and `requires_issue_confirmation`. Each check includes `blocking` and a concise `pending_label`. It performs no writes. After the schedule ends, an unrecorded required pre-use inspection has `satisfied=false` and `blocking=false`; only unsatisfied blocking checks contribute to the count or API rejection.
- `reservation_end(booking)` reuses saved slot end time or stay checkout time and returns an aware datetime in the configured Philippine default timezone. A missing checkout clock no longer invents midnight. Readiness catches invalid/missing schedule data and blocks completion safely.
- `reservation_start(booking)` reads the saved slot/check-in time in the same Philippine timezone. `inspection_actions(booking)` returns permitted pre/post kinds: pre-use before the scheduled start, post-use/review after the known end. A late/backdated new pre-use submission cannot fabricate a missed historical inspection. Existing stored inspection evidence is retained.
- `completion_issues(details, post=None)` is a pure read over the saved quote and post-use findings. A positive finite saved deposit, or recorded damage/missing-item/overtime details, requires review. Explicit absence values such as None, No damage found, zero and legacy null placeholders are not damage. An unfamiliar narrative is treated conservatively as needing review; resolution is never inferred from narrative words. A decision plus the real staff boolean establishes recorded resolution.
- `allowed_actions` uses readiness before advertising Complete Booking and allowed inspection kinds before offering inspection actions. `transition` recomputes under the existing locks. Real resolution must already be recorded before completion, and the final true boolean is required only when there is an actual deposit/issue. HTML-only validation cannot bypass the checks.
- `booking_row` resolves the method from saved metadata, then saved quote type, then existing facility type. It uses the existing `PRICING_METHODS` dictionary and returns an empty label when unknown. A saved historical method takes priority over today's configuration.
- `renderOverview()` consumes the authorized response and produces five sections using the existing `dl`, `money`, date/time formatter and action helper. `scheduleLabel`/`reservationTime` format existing values; `completionChecklist` displays server-provided truth rather than calculating eligibility in the browser.
- The small completion modal shows the actual booking/facility/schedule and server checks. It adds an initially unchecked required acknowledgement only for real damage/deposit cases. The same existing action form saves post-use resolution confirmation as a boolean. A rejected response stays visible; success reloads detail, shows Completed/actor/time, removes invalid actions and focuses the Completion Readiness heading.

Data flow: protected detail -> existing booking/quote/payments/inspection JSON -> shared server readiness -> section renderer and confirmation -> existing protected update with locks -> shared readiness recheck + staff acknowledgement -> existing completion metadata/status/audit -> refreshed detail and Activity. Other tab renderers, private document routes and payment logic remain in place.

Annotated existing update example, for an eligible isolated test booking only:

```json
{"action": "complete", "issues_resolved_confirmed": true}
```

For a real deposit/issue, the boolean records an authorized staff attestation; it does not refund a deposit, create a payment or calculate new damage charges. Sending it before the schedule ends or while the required post-use review is unresolved still fails. The string `"true"` is insufficient for a required confirmation. A booking without a deposit or recorded issue can use `{"action":"complete"}` once its real requirements are satisfied; no acknowledgement is fabricated in its completion history.

Annotated warning example: after an ended booking with a required but missed pre-use inspection, Django returns a pre-inspection check with `satisfied:false, blocking:false`. A missing required post-use inspection returns `satisfied:false, blocking:true`. The count is one; the UI shows the warning and disabled action with the post-use reason. Recording the valid post-use inspection makes the count zero unless a real resolution requirement remains. No client-side rule has to reinterpret the warning.

### 5. Backend / API behavior and completion rules

The existing booking detail endpoint adds a `completion` object and existing action lists become more accurate. Completion requires all of the following server facts:

1. Stored status is Approved. With existing full payment this is displayed as Reserved / Confirmed; no new stored status is created.
2. A known reservation/stay end instant is at or before now, using Asia/Manila regardless of an activated viewer timezone.
3. Existing `paid_summary` reports Paid. Pending/failed amounts do not count, and current full-payment rules are unchanged.
4. Required post-use inspection has its existing condition, inspector and timestamp. Before use, required pre-use work is tracked; after the end, a missed pre-use record is advisory and does not prevent completion. No confirmed contrary BEU rule is invented.
5. Only an actual positive saved deposit or recorded post-use issue creates a resolution requirement. The existing post-use decision and staff resolution confirmation must be saved. A deposit alone does not invent a separate post-inspection requirement if the saved workflow does not require one.
6. For applicable damage/deposit cases, final submission also confirms the staff review. Without such a case, there is no mandatory resolution checkbox or fake consent.

The existing update endpoint handles both inspection/review and completion. Inspection accepts the real decision and optional `issues_resolved_confirmed` boolean. Saving an unresolved inspection is allowed; trying to confirm resolution without a decision is rejected. Completion rejects unmet requirements, stale state or missing/false/string final confirmation when applicable with the existing 400 transport. Missing permission remains 403. The protected detail adds `inspection_actions` so the UI cannot offer retrospective pre-use edits. No endpoint, CSRF/RBAC bypass, new status or model was introduced.

On success, existing `details.completion` stores `by`, `at` and the acknowledgement only if applicable. Booking becomes Completed. Existing `booking_completed` Activity retains actor/role/time/result and `booking_status: completed`. Repeated completion/cancellation remains rejected. Older completed records show available history without invented timestamps/staff names. Saving a review uses the existing post-use inspection Activity event; it does not rewrite previous evidence or make a cash refund.

### 6. Database / migration impact and commands

No migration, schema, dependency installation or special data command is needed. Resolution confirmation extends the existing inspection JSON only. No bulk rewrite or production sample data was created. Django development autoreload picks up Python changes; deploy/restart workers and static assets normally. Hard-refresh for `20261017-completion-readiness`. Job Order preview keeps its speed-fix version.

Verification command from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
```

Optional browser fixtures are generated only by isolated tests when `BOOKING_OVERVIEW_REVIEW_DIR` names a local scratch directory. The helper uses the test client/test database, never production sample bookings. Internal completion callers need the true boolean only for actual damage/deposit cases; those cases must first save their resolution through the existing post-use review.

### 7. Tests performed and manual verification

Latest correction: 67 booking-workflow Django tests passed, followed by 22 Calendar/mobile tests plus a repeat of the no-fake-resolution test (89 distinct tests total). Two focused fixture-producing tests were also repeated successfully. System checks clean. Four new regression tests and updated existing tests cover missed versus recorded pre-use history, pre-use actions before start and rejected late backfill, post-use remaining count, false/placeholder/zero issue values, damage without a deposit, deposit review without an invented required inspection, required decision/staff confirmation, real completion, RBAC, terminal actions and preserved audit history. The broader workflow suite includes existing payment, document/Job Order, pricing and inspection regressions.

Earlier Overview implementation evidence, retained as history: 85 Django tests passed. The initial pricing fallback test was corrected to remove its existing saved method before expecting the quote fallback; the application correctly preserves a saved method first.

Latest Chrome checks passed at 1440, 768, 390 and 320px using nineteen real Django-generated isolated states. They verify the exact Completion Readiness title, advisory missed-pre warning versus real blocker icons/count, disabled action with actual reason, ready state despite the missed pre-use record, before-use inspection action and no retrospective action, actual deposit-only review, no final resolution checkbox for a normal no-issue booking, saved post-use resolution followed by completion, conditional final acknowledgement, rejected/successful mocked submit, Completed/Activity/focus, and no page overflow. Desktop blocked and phone ready screenshots were inspected; they show one remaining post-use requirement with the pre-use warning excluded, and then Ready for completion while retaining that historical warning. Browser HTTP uses isolated fixtures; Django tests verify real validation/transitions.

Earlier Overview browser checks covered eleven states at the same widths, including long escaped text, More Actions keyboard/outside behavior, pricing/notes and status hierarchy. Those results predate this correction and do not imply that the former unconditional acknowledgement remains required.

The earlier Overview work also ran the Payment-tab Chrome harness at all four widths. It was not rerun for this latest readiness correction; current backend payment regressions are included in the 67-test workflow suite. Current JavaScript syntax and scoped whitespace checks passed. The earlier layout detector reported degraded regex-only operation; it is not a full accessibility/computed-style assessment.

Manual steps, using an isolated development booking:

1. Before use, check a booking with required pre-use inspection: it is still tracked and can be recorded before the scheduled start. Unpaid/future bookings show disabled completion and their actual reasons.
2. After the end, leave pre-use missing and check its exact warning. Confirm the remaining count excludes that warning. With required post-use work missing, Complete Booking stays disabled with the post-use explanation. A direct API completion must also fail.
3. Record the required post-use inspection. With no deposit/issue, verify Ready for completion without a fake resolution requirement/checkbox. For actual damage/deposit, save its decision and confirm resolution through the existing post-use form; the same requirement must remain unfinished until confirmed.
4. Open the final confirmation and complete. Only an applicable damage/deposit case has the required unchecked review box. Verify Completed/actor/time, no Complete/Cancel action and one Activity event. Repeat attempts and read-only accounts must be rejected.
5. Check real rejected/legacy records and room stays. Verify existing rejection fields and missing data remain honest, and unknown Pricing Method is hidden. Verify Booking Slip, Job Order, Payment, Inspection and Activity still work.

### 8. Remaining limitations, debugging and safe practice

Staff confirmation is a recorded human review, not automatic financial reconciliation. Explicit empty/no-damage/zero placeholders are recognized as absence; an unfamiliar findings narrative conservatively needs review. The system never interprets a free-text decision as proof of settlement without staff confirmation. Old decision text without that confirmation needs staff review through the existing form; historical records are not silently marked resolved. No new charge ledger, partial-payment or refund workflow was introduced. Existing Paid rules still govern zero-charge history. Pricing fallback and saved amounts remain unchanged in this correction.

Readiness changes with time and data. A page already open before the schedule ends needs refresh to update its visible action list; the backend always rechecks on submit. A missing stay checkout time blocks completion until real schedule data is configured/recorded, rather than assuming midnight. Physical Android, actual printer, other browser engines, screen-reader hardware and the full repository suite were not tested.

Debugging: inspect `completion.remaining_count`, `reason`, `checks[].blocking/satisfied` and `inspection_actions` in the protected Network response. After the real end instant a missing pre-use check must have `blocking:false`; a remaining pre-use blocker often means the saved schedule/end clock is still future or missing. Check the actual Asia/Manila schedule instead of changing the browser clock. A disabled action with a resolution reason needs the existing post-use decision and saved true staff confirmation, not a fake deposit. No issue/deposit means no resolution check. An unfamiliar findings phrase may need staff review rather than keyword-based auto-clearance. A 403 or absent action can mean missing manage permission. Confirm asset version `20261017-completion-readiness` if old text persists. Never remove API validation to enable a button.

Safe practice: run the required-inspection test in the isolated test environment. Compare the missed pre-use check before and after the simulated schedule end: its `blocking` flag becomes false while it stays honestly unrecorded. Leave post-use absent and verify the count is still one and the API rejects completion; save the real post-use record and verify readiness. Restore any test edits afterwards. Compare the returned booleans with the UI icons. This teaches how a warning differs from a requirement without changing live bookings or inventing an inspection.

## Final booking inspection workflow (October 17, 2026)

This is the current Inspection implementation report. It incorporates attachment `bd1457ae-699e-47c3-a007-e1095f51c5c2` and the earlier authorized-inspector request. It replaces the earlier inspection guide; the Completion Readiness policy above still applies. There is no separate Inspection sidebar module. Records remain in Booking Details under Overview, Booking Slip, Job Order, Payment, Inspection and Activity.

### 1. Cause / reason

Confirmed before this change: the prior authorized-inspection implementation already had account-based inspectors, private attachments, separate pre/post records and guarded completion. Remaining gaps were a free-text main condition, generic Record Inspection buttons, no inspection shortcut in the row menu, Cancel among ordinary actions, and an update event on every inspection save even when content was unchanged. The existing physical booking schema/writers had no personnel assignment, so there was no real assignment to use as a new inspection default.

The new Personnel In-Charge action adds the missing assignment to the existing booking metadata, using existing accounts and Manage Bookings authority. It creates no duplicate model, staff field, permission, inspection store or sidebar module. The workflow is approved/reserved booking, real personnel assignment, pre-use before use, post-use after use, applicable damage/deposit review, and completion. Existing approval/payment conditions are preserved; assignment itself does not add a new completion requirement.

### 2. Exact files changed, current lines and nearby anchors

Lines are approximate after this update. Search the anchor if subsequent changes move them.

| Folder / file | Line / nearby anchor | Change and purpose |
| --- | --- | --- |
| `backend/core/modules/facilities/services/inspections.py` | 9 `CONDITION_CHOICES`; 46 `default_inspector_id`; 52 `condition_display`; 63 `validate_condition`; 74 `inspection_shortcuts`; 93 `same_inspection` | Reuse staff-grant filters; define the one condition catalog, legacy display, assignment defaults, phase-aware shortcut metadata and unchanged-save comparison. |
| `backend/core/modules/facilities/services/booking_workflow.py` | 17 `ACTION_PERMISSIONS`; 122 `allowed_actions`; 149 `booking_row`; 310 `transition`; around 407 assignment branch | Add the guarded assignment action, row shortcuts, validated condition fields and no-op saves. Existing timing, payment, completion, private JSON and upload helpers retained. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 111 `detail_data`; 196 `update`; 258 `document_values` | Return real staff/defaults/condition data, reject unauthorized recorder, skip audit on unchanged writes, log actual damage/resolution transitions, and use meaningful condition text in existing HTML/PDF reports. |
| `backend/core/modules/facilities/admin_booking_views.py` | 56 `audit` | Extend the same audit helper with personnel account metadata and inspector/type/time for damage/resolution events. No new logging store. |
| `backend/static/components/js/admin_bookings.js` | 241 `openBookingDetails`; 282 `showMoreActions` | Reorder core links, use server-generated inspection shortcuts, deep-link to the correct form, and put Cancel Booking below a divider at the bottom. |
| `backend/static/components/js/admin_booking_workflow.js` | 145 `renderInspections`; around 270 condition editor; `updateOther`; `submit`; final URL action handler | Always render separated pre/post sections with explicit recorded status, assignment control, dropdown/Other field, saved-account defaults, exact timestamp preservation for unchanged edits and `kind` URL routing. |
| `backend/static/components/css/admin_booking.css` | 99 `.bk-inspection-section`; 115 `.bk-inspection-assignment`; around 2154 `.bk-more-menu` | Reuse compact navy/white form and summary styles, touch targets and mobile stacking; add a flat assignment row and restrained menu divider/viewport scrolling. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 13 stylesheet; 69/72 booking scripts | Refresh changed CSS/JS versions to `20261017-inspection-workflow`. Page, six tabs and small action modal remain. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 14 stylesheet; 197 booking script | Refresh the same list/Calendar asset references; keep the existing table/filter/pagination components. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 59 `capture_inspection_flow`; 860 condition test; 883 assignment; 912 no-op; 928 shortcuts; 957 state-change audit | Update valid callers to use configured condition choices and add five focused tests for the newly requested behavior. Test-only fixtures are optional. |
| `docs/facility-configuration.md` | this section | Replace the prior inspection guide with current causes, functions/data flow, behavior, tests, debugging and exercise. |
| `CAMPUSHUB_CONTEXT.md` | latest `Current final booking inspection workflow` entry | Preserve the new assignment/condition/menu policy for later development. |

Browser fixtures/harness/screenshots are under `scratch/inspection-final-workflow/`. Final Django log: `scratch/inspection-final-tests.log`. Browser logs: `scratch/inspection-final-browser.log` and `scratch/inspection-final-browser-confirmed.log`. They use isolated database test records, not live booking data.

### 3. Changes made: Inspection tab and forms

Inspection always has **Pre-Use Inspection** and **Post-Use Inspection** sections. Empty phases explicitly display **Status: Not Recorded**. Authorized users see **Record Pre-Use Inspection** / **Record Post-Use Inspection**, enabled only when the existing backend phase action permits recording. Otherwise the button is disabled with stage context; view-only users do not get recording controls. Saved phases show **Status: Recorded**, actual inspector, Manila inspection time, condition, phase findings and remarks, plus View Details and phase-permitted Edit Inspection.

A small Personnel In-Charge row shows the actual saved assignment or Not assigned. **Assign Personnel / Change Personnel** opens the existing small action modal with an authorized-account dropdown. It is available only for approved bookings and authorized facilities staff. Actual pre/post inspectors remain independent of that assignment.

**Pre-use fields:** Inspector (required), Inspection Date & Time (Philippine time, required), Facility Condition Before Use (required dropdown), Existing Damage / Issues, Remarks and optional Supporting Photo / Report. No overtime, missing-items or setup/cleanliness entry fields.

**Post-use fields:** Inspector, Inspection Date & Time, Facility Condition After Use, and mandatory explicit Damage Found? No / Yes. Yes reveals and requires Damage Description in frontend and backend. No hides/disables that field and clears a forged stale description. Remarks/evidence are optional. The existing damage/deposit decision and confirmation appear for an actual saved deposit/issue or newly selected damage answer, not every booking.

The one backend condition catalog is **Good Condition, Minor Issues, Damaged, Requires Maintenance, Other**. The browser starts with **Select facility condition**. Other reveals **Specify Condition \***; both client and server require its content. Selecting a configured choice disables/hides Other and clears stale detail on save. Historic free-text conditions remain visible unchanged on read; editing presents Other with their original text filled in rather than silently classifying or deleting them. The report/PDF uses the same display helper.

Previously recorded cleanliness/missing-items/overtime values remain historical information in View Details and existing reports. Empty file input preserves prior evidence; a real replacement still uses `validated_attachment`. Existing separate inspector/recorder snapshots and creation/update timestamps remain. Unknown legacy creation times stay Not recorded.

### 4. How it works: functions, inputs / outputs and data flow

- `authorized_inspectors()` returns an ordered, distinct `accounts.User` queryset with active/unsuspended accounts, actual user/group Manage Bookings grants or Super Admin authority, and excludes ordinary User/Student/Guest/External, Marketplace Admin and inactive configured roles before listing. There is no arbitrary first-100 slice or job-title-based auto-grant. `can_record_inspection(user)` reuses existing admin access/permissions; actual actor and selected account are independently checked before saving.
- `default_inspector_id(record, staff, assigned)` returns a still-eligible saved inspector for an edit. For a genuinely new phase, it returns the still-eligible assigned account; otherwise null. It never replaces a saved inspector with a new assignee, and never guesses from the creator/approver.
- `condition_display(record)` returns `{value, other, label}` for the selector and recorded display, including old free text. `validate_condition(data)` accepts the configured main choice and conditional description, returning existing `condition` plus `condition_other`; unsupported choices or blank Other are validation errors.
- `inspection_shortcuts(booking, permitted)` consumes the actual saved phase records and existing `inspection_actions(booking)` guards. It returns action/label metadata for the row menu, not a second booking-state engine. No records yields only the phase currently recordable; pre only yields View Pre-Use plus Record Post-Use only after the end; post only yields View Post-Use; both yields View Inspection. Read-only users get saved-record views only.
- `booking_row()` adds those shortcuts to the existing serialized row. `detail_data()` supplies the same records, staff, assignment/defaults, condition catalog/display, phase actions and Completion Readiness. Main HTML context and JSON API now both emit choices as a list; an initial regression caught a tuple/list mismatch and this was corrected.
- `transition()` keeps the existing Facility-then-Booking locks. Assignment validates real actor/target and saves `details.assigned_personnel={id,name,by,at}` on the existing sidecar. Inspection validates account, phase, local timestamp, condition and applicable damage fields, then merges the existing phase record and evidence. Different inspectors can be selected for pre and post. No standalone Inspection/Assignment model is added.
- `same_inspection(previous, candidate)` compares actual editable content, inspector identity, attachment and equivalent timestamps, excluding automatic save actor/time fields. Equivalent offset spellings are the same instant. If unchanged, `transition()` returns no event before any save; the route returns `changed:false` and **No changes to save.** The browser preserves the original full timestamp when a datetime-local value has not changed, so minute-only input precision does not create a fake edit.
- `renderInspections()` displays the existing tab using escaped real values. The editor controls Other and Damage Description visibility/validity. Submit posts real account IDs and boolean `has_damage`, then refreshes the same tab and restores focus. Row record shortcuts add `tab=Inspection&action=inspection&kind=pre|post` to the existing full-page route; the page verifies the allowed phase again before opening its modal.

Annotated storage example (values are obtained from actual authorized accounts):

```python
# Assignment is a default for NEW inspections, not proof that this person inspected.
details['assigned_personnel'] = {**actor(selected_user), 'by': actor(request.user), 'at': now}
# A saved phase retains its own actual inspector, even after a later reassignment.
default_id = default_inspector_id(saved_phase, eligible_staff, details.get('assigned_personnel'))
```

Data flow: real Booking/Facility rules + saved sidecar ? existing permissions/timing checks ? actual account selector and condition catalog ? existing locked update route ? same inspection/assignment JSON ? existing audit helper ? refreshed summaries, private reports and Completion Readiness. This approach keeps historical data and one state/permission/payment engine.

### 5. Backend / API, menu, audit and completion behavior

Existing routes remain: `GET /api/bookings/<id>/`, `POST /api/bookings/<id>/update/`, `/admin-bookings/<id>/`, private inspection documents and attachment endpoints. Assignment uses the same POST route with `action: assign_personnel` and `personnel_id`; inspection keeps `action: inspection`, `kind`, actual `inspector_id`, `inspected_at`, condition and applicable fields. `condition_other` is required only for Other. Post-use still requires boolean `has_damage`, not strings/null/numbers. Invalid input returns 400; prohibited actors get 403. Selecting an authorized inspector does not give the recorder permission. Student/mobile public details still omit internal inspection/assignment metadata through the existing allowlist.

The list menu prioritizes **View Booking ? Booking Slip ? Job Order ? Payment Details ? inspection shortcut**, preserving current eligibility for each existing link. Unpaid bookings retain Record Payment instead of losing that action. Other permitted Approve/Reject/Edit/Complete/Activity actions remain. **Cancel Booking** is last, below a divider. Cancel and Complete remain unavailable after completion; cancelled/rejected records keep existing read-only behavior and recorded inspection views. No new page or sidebar link.

Pre-use recording/editing remains before scheduled start, only when configured and permitted. After use a saved pre-use remains complete; an absent one displays **Pre-use inspection was not recorded.** and does not count as a remaining blocker. Post-use becomes recordable only after the actual end and when required or a real review is needed. Enabled/disabled controls and direct POSTs use the same backend timing rules; a crafted shortcut cannot bypass them.

Completion uses the existing approved status, actual Manila end instant, paid summary, configured post-use requirement and applicable issue resolution. A real positive saved deposit or recorded damage/legacy issue requires a decision plus explicit staff confirmation. No damage and no deposit/issue creates no invented resolution blocker. Existing charge/payment calculations and status codes are unchanged. Successful completion saves the existing completion actor/time, changes status to Completed, and removes completion/cancellation/inspection-edit actions. Staff confirmation remains a human review, not an automatic refund ledger.

Audit reuses `AccountActivity`: personnel assignment includes the assignee account and actual actor; initial/updated pre/post events include inspector, inspection type and inspection time; real transitions into damage and resolution add **Damage Issue Recorded** / **Damage / Deposit Resolution Completed** once at that state change. An unchanged inspection or same-account assignment adds no event, does not update timestamps and does not rewrite the booking. The main inspection-updated event and a semantic damage/resolution event describe distinct actual changes. Existing booking completion audit remains.

### 6. Database / migration impact and commands

No model/schema changes, migration, seed, new package or production data rewrite is required. Existing Booking, Facility, User/Role, FacilityBookingRequest JSON, FacilityPayment, `metadata`, `save_details`, `actor`, upload/private-document and audit helpers are reused. `condition_other` and real `assigned_personnel` are stored only in existing booking JSON; existing condition, evidence and separate pre/post records remain. No account or permission is created automatically, and historical conditions are not batch-converted.

Restart the Django development server if it has not auto-reloaded, then refresh Bookings/Booking Details. Assets use `20261017-inspection-workflow`. Deployment should use the project's normal static-file process; no extra development command is needed.

Run tests from `backend/core`:

```powershell
.\venv\Scripts\python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
```

Optional isolated browser fixtures: set `BOOKING_OVERVIEW_REVIEW_DIR` to `C:/Users/leste/Desktop/CAMPUSHUB/scratch/inspection-final-workflow` before that test command. The capture helpers only write test responses when this environment variable is supplied. The local Node harness uses the installed Node runtime to run `scratch/inspection-final-workflow/check.cjs`; it mocks transport with those actual test responses and does not contact the live server for writes.

### 7. Tests performed and manual verification

Executed October 17, 2026: **100 distinct Django tests passed** in 43.511 seconds, system checks clean: 78 booking workflow tests plus 22 Calendar/mobile booking tests. Five new focused tests verify condition/Other/legacy handling; real assignment accounts/defaults/separate actual inspectors; unchanged saves with equivalent timezone offsets and unchanged booking timestamps; phase/read-only/completed shortcuts; and damage/resolution audit state changes. Existing authorization, private attachments, pre/post inspection, payment, availability, completion, real DOCX/PDF and route tests also passed. The first 78-test run exposed only the context tuple/API list mismatch; the final combined 100-test run passed after emitting a list consistently.

JavaScript syntax checks passed for both changed booking scripts. Chrome at **1440, 768, 390 and 320px** passed seventeen isolated saved/empty/readonly/missed-pre/assignment/condition states, actual select options/defaults, Other and damage visibility/required rules, unchanged phase protections, save/error/retry/focus, keyboard View Details, real menu order/divider, read-only/completed actions, and pre/post shortcut navigation to the correct modal. No horizontal document/menu overflow. Browser transport is mocked with real Django-test fixtures; actual writes, state changes and permissions are independently covered by Django tests. Desktop/phone screenshots were inspected. Browser-only automation was refined to wait for complete initialization/selected tab and scroll the actual row trigger into view before its final confirmation.

Manual checks on isolated development bookings:

1. Open Inspection on an approved booking. Confirm two phase sections and Not Recorded statuses, no separate sidebar module, and stage-disabled controls when recording is unavailable. Assign a real eligible person; verify assignment actor/time in Activity and that a new pre-use selector defaults to that account.
2. Choose a different actual pre-use inspector, Good Condition or another configured option, a valid Manila inspection timestamp, and optional findings/evidence. Other must reveal/require Specify Condition; selecting a configured option must hide/disable it. Save and verify Recorded summary, View Details/private evidence and the actual inspector, not merely the assignee.
3. Edit without changing anything. Verify No changes to save, no new Activity row and unchanged recorded/update times. Change a real finding and verify one updated event. Edit without selecting another file and verify evidence remains.
4. On the list, verify the core link order and Cancel Booking below its divider. Before use only pre-use can be newly recorded. After saved pre-use, View Pre-Use is available; Record Post-Use appears only after the end. A shortcut must open Booking Details ? Inspection and its correct form. Both saved phases show View Inspection.
5. After the end, leave pre-use missing and verify its warning is not a blocker. Post-use must explicitly select No or Yes; Yes needs damage details. No with no real deposit/issue permits readiness when other requirements pass. Actual damage/deposit keeps readiness blocked until the existing decision/confirmation is recorded.
6. Complete a ready booking. Confirm Completed actor/time/activity, no Complete/Cancel/Edit Inspection, and a direct repeat/cancel/inspection write is rejected. Test a view-only account: records/reports remain readable, assignments/recording/uploads are rejected. Students, guests and marketplace-only accounts cannot become inspectors by typing an ID.

### 8. Remaining limitations, troubleshooting and safe practice

Assignment now has a real booking source and is a default only. It does not schedule staff workloads, send messages or prove that a person performed an inspection. There is no dedicated inspection-only permission: existing Manage Bookings authority and explicit facilities actor/target checks remain. Inactive/suspended/excluded assignees are not offered/defaulted; their saved historical name remains visible. Reassigning personnel never rewrites saved inspectors. This task does not create an unassign action or a new staff-capacity module.

Legacy free-text conditions are honestly displayed and become Other with preserved text when edited. Unknown legacy creation time is not guessed. Names are saved snapshots, and `recorded_by` remains the latest saving actor, with all actual actors retained in Activity. There is no new refund/charge ledger; historical issue fields remain relevant until actually resolved. A page left open across a schedule boundary needs refresh for its visible action list, while every submit rechecks real backend state. Full repository, physical Android/printer, other engines and screen-reader hardware were not tested.

Troubleshooting:

- **Missing/default inspector:** inspect `staff`, saved `assigned_personnel`, `inspection_defaults`, actual active/unsuspended `accounts.User`, current user/group grant and Role status. Mobile `CampusHubUser` rows and job titles alone do not make personnel eligible. On an edit, a saved actual inspector takes priority over assignment; an ineligible saved inspector requires a deliberate valid selection.
- **400 condition error:** send one configured choice. Other needs `condition_other`. Do not replace backend validation with arbitrary free text; use the helper's honest legacy display instead of overwriting history.
- **Repeated audit on apparently unchanged form:** inspect the actual changed fields and full timestamp. The frontend must preserve the saved ISO instant if datetime-local's displayed minute is unchanged. A real timestamp, finding, decision, attachment or inspector change is an update. `changed:false` means no save/event, not failure.
- **Wrong shortcut/disabled action:** inspect `booking.actions`, `inspection_shortcuts` and `inspection_actions`, saved record existence and actual reservation start/end. URL `kind=pre|post` chooses a form but grants no authority. Refresh old assets rather than enabling hidden controls.
- **Wrong completion count:** inspect `completion.checks[].blocking/satisfied`, actual quote deposit and real post-use findings. A missed pre-use after end is a warning. An unfamiliar historical missing-item/overtime finding is not erased merely because that field is no longer in the form.
- **403 or inaccessible evidence:** recorder authorization is separate from selected inspector. Read-only permission does not allow assignment/upload. Use the existing private evidence/report routes; raw evidence is intentionally absent from public/detail JSON.

Safe practice: run `test_personnel_assignment_validates_accounts_defaults_new_inspections_and_keeps_actual_inspectors` in the isolated test database. Predict the pre/post defaults after assignment, after someone else performs pre-use, and after the assignee becomes inactive. Compare those assertions with `default_inspector_id`. Then run `test_unchanged_inspection_does_not_write_or_duplicate_audit`: predict whether the same instant with a different timezone offset counts as a change, and verify it does not; a real remark change should add one updated event. Restore any exploratory test edits. This demonstrates defaults versus facts, typed validation and semantic change detection without modifying live bookings.

## Add Reservation: closed operating-day message (October 17, 2026)

### 1. Cause / reason

The slot selector previously displayed a generic no-configured-slots message for a closed weekday. Manual time entry could instead receive the broad outside-hours/past/minimum-duration message or configured-slot message. Those reasons did not identify the actual facility and closed weekday. The requested example is now **Unavailable — Covered Court is not available on Thursdays. Please select an allowed operating day.** Facility name and weekday come from the selected real record/date, not fixed example data.

### 2. Exact files changed and current anchors

| File | Approximate line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/operating_schedule.py` | 67 `closed_operating_day_messages` | Read the existing validated weekly schedule and build messages only for confirmed closed days. |
| `backend/core/modules/facilities/services/admin_reservations.py` | 13 schedule imports; 124 `closed_message` | Give the same descriptive reason when slot reservation validation rejects that closed day. |
| `backend/core/modules/facilities/admin_booking_views.py` | 87 `result['closed_operating_day_messages']` | Include the shared message map in the existing protected facility-options response. |
| `backend/static/components/js/admin_booking_forms.js` | 9 `closedOperatingDayMessage`; around 171 slot-empty message and 227 preview-error rendering | Display the correct weekday reason with the Unavailable prefix, safely as text. Other conflict/pricing messages remain in their existing paths. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 198 booking form script | Refresh asset version to `20261017-closed-day-message`; shared Calendar template uses the same file. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 70 booking form script | Refresh the shared form asset on Booking Details too. |
| `backend/core/modules/facilities/test_admin_reservations.py` | 68 `test_schedule_preview_without_client_does_not_quote_or_save` | Extend the existing availability contract test for two closed weekdays, a valid open day, unknown hours and no booking creation. |
| `docs/facility-configuration.md` | this section | Current explanation, data flow, debugging and safe exercise. |
| `CAMPUSHUB_CONTEXT.md` | latest closed-day-message entry | Retain the current copy policy for later work. |

### 3. Changes made

Closed-day unavailability explicitly names the facility, weekday and next action. For a different facility or weekday those parts change dynamically. The fixed-slot date selector and the backend preview/creation validation share the same reason. A valid open day still uses the existing availability/slot checks; an unrecognized or missing schedule does not invent a closed weekday.

### 4. How it works: functions, inputs / outputs and data flow

`closed_operating_day_messages(facility)` accepts an existing Facility object, reads `workflow_config.operating_hours` through `weekly_hours()`, and returns a dictionary such as `{'thursday': '<actual facility> is not available on Thursdays. Please select an allowed operating day.'}` only where the validated day value is `None` (Closed). Unknown/missing schedules return an empty dictionary. This does not query the database, alter hours or decide new availability rules.

The existing facility-options endpoint sends that map with the selected facility. `closedOperatingDayMessage()` takes the form's selected date, derives its weekday without a browser-timezone date shift, and reads the corresponding server message. If the slot response has no available choices, the form uses that message or retains its generic fallback. The preview error path uses the same text when the server rejected that closed weekday. It uses `textContent`, so facility names cannot become executable markup.

For manual time entry, `reservation_schedule()` reads the same map before its existing configured-slot/status checks and raises the existing `ReservationUnavailable` with the more precise reason. Data flow: saved facility hours → existing weekly-hours reader → shared closed-day message map → protected options or reservation validation → Add Reservation Availability text. Existing mobile slot availability and conflict logic remain the authority for actual selectable times.

Annotated example: a saved Thursday value of `None` means closed, so a selected Thursday produces the requested message. A saved Thursday opening/closing period does not produce this message merely because every slot is booked; that case keeps its existing slot/conflict explanation.

### 5. Backend / API behavior

The current options route gains only an additive `facility.closed_operating_day_messages` field. Existing preview/create routes still reject unavailable schedules, with `available:false` and the descriptive reason for a closed day. Permissions, booking creation, quote calculations and saved operating hours are unchanged. No new endpoint or duplicate availability engine was added.

### 6. Database / migration impact

No model changes, migration, dependencies, seed or live data edits. Refresh Add Reservation after Django reloads the source. The shared form script asset version is `20261017-closed-day-message`.

### 7. Tests performed

Executed **26 reservation Django tests**, all passed in 5.344 seconds with clean system checks. The updated existing test verifies Thursday/Saturday messages from real isolated test Facility data, a closed day remains unavailable with no booking saved, Friday remains available, an unknown schedule produces no invented weekday message, and the existing academic-conflict explanation remains intact. Node syntax check passed for `admin_booking_forms.js`. Log: `scratch/closed-operating-day-tests.log`.

Run from `backend/core`: `.\venv\Scripts\python.exe manage.py test modules.facilities.test_admin_reservations --keepdb --noinput`. This copy change was not separately exercised in a live browser or physical phone.

### 8. Remaining limitations, debugging and safe practice

The precise weekday message requires an interpretable saved operating schedule. Missing/ambiguous legacy hours keep the existing generic unavailable explanation rather than pretending the facility is closed every week. This change does not make a closed day bookable or change room-accommodation rules.

To debug, check the selected facility/date, its actual Operating Schedule, and the protected options response's `closed_operating_day_messages` entry. If the map is correct but the old generic copy remains, refresh the page and verify the current form-script asset version. Do not open a day in the database merely to suppress the warning.

Safe practice: run the existing availability test above in the isolated test database. Predict the message when Thursday is closed, then inspect the Friday assertion and verify an open period still passes. Compare unknown-hours behavior with a confirmed closed day. Restore exploratory test edits; do not change live operating hours for practice.


## Booking cancellation before scheduled start (October 17, 2026)

### 1. Cause / reason

Confirmed before this update: admin `allowed_actions()` allowed cancellation for every Pending/Approved booking without checking start time, while the mobile endpoint allowed only Pending requests. Those inconsistent rules could allow late admin cancellation and deny future approved/paid owner cancellation. The user now requires one policy: an active Pending Approval or Approved booking can be cancelled only before scheduled use starts, irrespective of recorded payment amount. Started, ended, Completed, Cancelled and Rejected bookings cannot be cancelled. Payment history must remain, with refunds handled separately.

### 2. Exact files changed and current anchors

| Folder / file | Approximate line / nearby anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/booking_workflow.py` | 122 `allowed_actions`; 150 `booking_row`; 220 `reservation_start`; 230 `cancellation_readiness`; 327 `transition` | Add the shared pure cancellation policy, use it for admin action visibility/row reason and revalidate under the existing locks before status changes. |
| `backend/core/modules/facilities/mobile_views.py` | 39 `_serialize`; 213 `cancel` | Use the same policy for `can_cancel` and the owner's locked POST instead of a pending-only check. Existing bearer authentication and ownership remain. |
| `backend/static/components/js/admin_booking_workflow.js` | 240 paid cancellation hint | Explain preserved payments/separate refunds when actual recorded paid amount is positive. The reason form, existing actions and styling remain. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 72 workflow script | Refresh the changed workflow asset version to `20261017-cancellation-policy`. |
| `campushub/lib/module_app/screens/facilities/facility_booking_status_screen.dart` | 69 cancellation confirmation content | Show the same payment-preservation/refund explanation when actual paid amount is positive. Cancellation visibility still follows backend `can_cancel`. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 987 status/payment/start matrix; 1016 terminal/missing start; 1027 room clock/Manila | Verify both active statuses, no/partial/full paid history, exact start boundary, ended schedules, invalid terminal writes, missing clocks, payment immutability and actual audit event count. |
| `backend/core/api/test_mobile_facility_booking.py` | 95 approved/payment regression; 119 mobile start/partial-payment test | Update the old pending-only expectation and prove the owner can cancel a future approved paid booking, cannot cancel started/ended requests and retains original payment rows. Existing ownership tests retained. |
| `docs/facility-configuration.md` | this section | Current eight-part report, functions/data flow, testing, debugging and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | latest cancellation policy entry | Preserve this rule for future development. |

### 3. Changes made and final policy

| Booking situation | Cancellation |
| --- | --- |
| Pending Approval, valid future start | Yes, with existing authority/ownership |
| Approved, valid future start | Yes |
| Reserved / Confirmed, valid future start | Yes |
| Approved with real partial payment history, valid future start | Yes; payments retained |
| Approved and fully paid, valid future start | Yes; payments retained |
| Exactly at scheduled start, or later (including ended use) | No, including Pending requests |
| Completed / Cancelled / Rejected | No |
| Missing/invalid start date or time | No until a valid start is recorded; do not guess a clock |

The database's active booking statuses remain Pending and Approved. Reserved / Confirmed is the existing display of Approved plus full recorded payment; partial/full payment are financial circumstances, not new Booking status codes. This change does not add a partial-payment entry workflow or change existing payment-status labels/calculations. It supports the history that already exists.

### 4. How it works: functions, inputs / outputs and data flow

`cancellation_readiness(booking)` takes an actual Booking and returns `{'eligible': bool, 'reason': str}`. First it excludes non-active lifecycle statuses. Then it calls the existing `reservation_start()` to obtain an aware start instant from slot booking date/start time, or hostel check-in date and the saved/configured check-in clock. It uses CampusHub's default Asia/Manila timezone, not a browser timezone or a guessed midnight. Missing/invalid starts are rejected with an actionable reason. `timezone.now() >= start` rejects equality and every later instant. Only a valid earlier instant yields eligibility.

The helper deliberately does not inspect payments: payment amount cannot turn a future cancellable request into a forbidden one, nor turn a started booking into a cancellable one. Existing user permissions/ownership are separate checks and remain necessary.

Data flow: actual booking status + saved schedule ? `reservation_start` ? shared cancellation policy ? admin `allowed_actions` / row `cancellation` metadata or mobile `can_cancel` ? existing list/detail/mobile controls ? cancellation POST ? same policy rechecked while the Booking is locked ? existing Cancelled status and audit event. Admin also keeps the existing required cancellation reason and actor/time in the sidecar. Mobile retains its existing authenticated owner audit path. No second status or payment engine is introduced.

Annotated boundary example:

```python
# start is an aware Asia/Manila reservation or check-in instant.
# At precisely start, cancellation must already be blocked.
if timezone.now() >= start:
    return {'eligible': False, 'reason': 'This booking cannot be cancelled because the scheduled use has already started.'}
```

Admin and Flutter confirmations inspect their existing actual `paid_amount` only to show the payment reminder. They do not implement the cancellation rule themselves or infer a refund. Both explain that recorded payments remain and refunds must be handled separately.

### 5. Backend / API behavior and payment preservation

Existing admin `POST /api/bookings/<id>/update/` with `action: cancel` rechecks the policy in `transition()` inside the established Facility-then-Booking lock order. Invalid timing/status returns 400 with the reason before any change or success audit. Existing RBAC and required reason stay intact. The corresponding row/details omit Cancel when unavailable and include a read-only `cancellation` eligibility/reason object. The existing action menu keeps Cancel Booking at the bottom when permitted.

Existing owner `POST /api/mobile/bookings/<id>/cancel/` now uses the same rule inside its existing Booking transaction. Authentication and `user=user` ownership filter are unchanged; another account still gets 404 and unauthenticated calls remain rejected. Invalid timing/status returns 409, preserving the mobile conflict-response convention. Mobile list/detail `can_cancel` follows the same result. A direct request cannot bypass a hidden button or reuse an old permitted snapshot.

Neither cancellation path deletes, edits, refunds, zeros or reverses `FacilityPayment` records. Amounts, OR number, paid-at timestamps, payment status and private receipt metadata remain. Cancelling does not record a refund; any actual refund must use the institution's separate authorized process. Existing cancellation releases reserved schedule capacity through the existing cancelled-record exclusion in availability, and existing audit records the actual successful cancellation once. Invalid/repeated terminal attempts do not add a successful cancellation event.

### 6. Database / migration impact and commands

No models, migrations, new Booking/payment statuses, dependency installs, data backfills or live record edits are required. Existing Asia/Manila / USE_TZ settings remain enabled and untouched. Refresh web Booking Details after Django reloads Python and the updated script; mobile needs the normal Flutter hot restart/rebuild to show changed confirmation copy, while server policy already governs both clients.

From `backend/core`, the executed regression command is:

```powershell
.\venv\Scripts\python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_admin_reservations modules.facilities.test_calendar api.test_mobile_facility_booking --keepdb --noinput
```

From `campushub`, targeted static analysis: `flutter analyze lib/module_app/screens/facilities/facility_booking_status_screen.dart`.

### 7. Tests performed and manual verification

Executed October 17, 2026: **130 distinct Django tests passed** in 64.991 seconds, clean system checks. This includes 81 booking workflow tests, 26 admin reservation tests and 23 Calendar/mobile tests. Added boundary tests exercise Pending/Approved against zero, partial and full recorded payments, one microsecond before start, exact start, started/ended use, terminal statuses, missing schedule data, saved hostel check-in clock and a different active timezone. Direct writes and action visibility agree; original payment rows remain byte-for-value identical, and successful cancellation audit occurs once. The mobile paid/partial tests confirm owner-approved cancellation, 409 after start, unchanged receipts and retained ownership enforcement.

JavaScript syntax passed. Targeted Flutter analysis found **no issues** (31.6 seconds). The Dart formatter dry run reported formatting differences; it did not write formatting changes. No live browser/physical Android cancellation was performed in this update. Log: `scratch/booking-cancellation-policy-tests.log`.

Manual checks on isolated development bookings:

1. Before use, check Pending Approval and Approved bookings: an authorized admin sees Cancel Booking and a current owner receives `can_cancel:true`. Repeat with an approved full-paid booking and actual historical partial payment. Positive paid amounts show the preservation/refund reminder.
2. Cancel with a valid admin reason or through the owner's confirmation. Verify Cancelled, existing audit/actor, payment amounts/OR/evidence still present, and the same time can be booked again through normal availability. Do not create a fake refund record.
3. At the exact scheduled start and after the end, refresh: no permitted Cancel action. A direct/stale request is rejected with the started-use explanation. Pending status does not override this timing rule.
4. Check Completed, Cancelled and Rejected: no cancellation; repeat POSTs are rejected. Another mobile account cannot cancel someone else's booking.
5. For hostel, compare the configured/saved check-in clock, not midnight. A missing clock does not produce a guessed cancellation deadline. Record actual schedule data through the existing workflow before retrying.

### 8. Remaining limitations, debugging and safe practice

An open page's old action list can remain visible until refresh as time passes; the locked backend always rechecks the current instant. A cancellation request sent before start but processed at/after start is rejected based on processing time. There is no new automatic cutoff timer, grace period or refund ledger. Missing legacy schedule starts require real correction rather than treating unknown time as permission. This task does not change completed-order revenue reports or add payment adjustment/refund accounting.

Debugging: inspect `booking.status`, actual `booking_date/start_time` or `check_in_date` and saved/configured check-in clock, and the protected `cancellation` or owner `can_cancel` response. Compare aware datetimes in Manila instead of changing the computer clock. A 403 is existing admin permission, 404 on an owner's route can be ownership, and 400/409 with a timing reason is the shared policy. A paid booking denied before use should be checked for status/schedule/permissions, not fixed by deleting payment history. Pending at/after start is intentionally denied.

Safe practice: run `test_cancellation_status_payment_and_exact_start_boundary` in the isolated test database. Predict why start minus one microsecond succeeds while equality fails, regardless of payment amount; inspect the unchanged payment snapshots and audit assertion. Then run the room-clock and mobile partial-payment tests. Restore exploratory test edits. Do not change production clocks, cancel live bookings or delete payment rows as a practice exercise.


## Services table containment and scrolling actions (October 17, 2026)

### 1. Cause / reason

Confirmed in shared CSS: `.facility-table-panel .table-responsive` still supplied `margin-left/right: -24px` and `width: calc(100% + 48px)` from an older padded card. The current Services card has no matching padding, so its table bled outside the toolbar/footer edges. A lower-specificity Services wrap rule lost to the ID-scoped shared `flex-wrap:nowrap`, creating tablet-width page overflow. Services also inherited an unnecessarily wide eight-column table minimum despite having six columns.

The initial and dynamically rendered service dropdowns explicitly skipped the fixed Popper strategy that physical Facilities already used. Once the actions column became sticky, later rows' sticky cells could paint above an earlier open menu unless its focused/open cell was raised. Browser hit-testing confirmed that overlap, not just a visual guess.

### 2. Exact files changed and current anchors

| Folder / file | Approximate line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/static/facilities/css/admin_services.css` | 6 service catalog containment rules; 19 sticky Actions; 24 open/focused cell stack; 26 toolbar wrap | Remove service table bleed, contain horizontal scrolling, size six columns, keep Actions on the visible right edge and raise an open menu above neighboring rows. Override inherited nowrap with matching scope. |
| `backend/templates/partials/facility_row_menu.html` | 11 `data-bs-config` | Give initially rendered service rows the same fixed Popper strategy already used by Facilities. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 16 service stylesheet version; 1400 `getRowMenuHtml` dropdown trigger | Refresh Services CSS as `20261017-service-table-overflow`; apply the same strategy to rows rebuilt after save/edit/archive/restore. Existing row action delegation remains. |
| `docs/facility-configuration.md` | this section | Cause, current source locations, data flow, checks and debugging/practice. |
| `CAMPUSHUB_CONTEXT.md` | latest Services table overflow entry | Preserve the scoped layout policy for future changes. |

Browser-only harness, actual Django-rendered isolated fixtures and screenshots are in `scratch/service-table-overflow/`; relevant logs are `scratch/service-table-overflow-tests.log` and `scratch/service-table-overflow-browser-final.log`. No new application test or duplicate feature guide was created for this CSS fix.

### 3. Changes made

The table, toolbar and footer now share the card's edges. Desktop width fits the six-column table without an unnecessary horizontal scrollbar. Below the readable table width, only the table scrolls horizontally; the document/sidebar do not. Actions stays visible at the right, including while the user scrolls other columns. Status has a stable width, service name keeps its existing truncation, and category/pricing/request text can wrap within its column.

Bootstrap menus use fixed positioning and viewport boundary behavior rather than increasing the table's scroll area. The focused/open Actions cell is stacked above other rows and the header, so its Edit/Archive menu remains clickable. First and last rows work, including a last-row dropdown extending beyond the table edge. The existing menu styling, actions, keyboard Escape/focus behavior and service editor are retained. Filters wrap when needed instead of pushing the page sideways.

### 4. How it works: selectors, existing functions and data flow

The new selectors start with `.service-catalog #facilitiesListSection`, so physical Facilities keeps its existing styling. The scroll wrapper receives `width:100%`, zero side margins, horizontal auto overflow and hidden vertical overflow. Its inner container keeps a readable 880px minimum, while the wrapper remains constrained to the actual card. Only the Actions cells are `position:sticky; right:0`; header/body have separate stacking levels. `:focus-within` and the open Bootstrap menu state raise the active cell so a later sticky row cannot cover it.

Initial rows come from the existing Django Facility/service queryset and shared `facility_row_menu.html` partial. `getRowMenuHtml(isArchived)` produces the equivalent controls when `renderFacilityRow(row, facility)` rebuilds a row after an existing API response. Both now pass `popperConfig.strategy:fixed` to the existing Bootstrap dropdown. Popper handles the actual trigger position, scroll/viewport updates and flipping; no second dropdown implementation, detached portal or custom coordinate engine was added. Existing delegated `[data-facility-row-action]` handling still finds the owning row and opens the same editor/confirmation.

Data flow: real authorized service records ? existing server-rendered/rebuilt rows ? scoped table layout ? existing Bootstrap dropdown and Popper ? existing Edit/Archive/Restore handler. No data values, pricing, filters, permissions or service workflow are calculated by these styles.

Annotated CSS example:

```css
/* The wrapper matches its card; only its wider inner table scrolls. */
width: 100%;
margin: 0;
overflow-x: auto;
/* Actions remain available at the visible right edge of that scroller. */
position: sticky;
right: 0;
```

These declarations belong on different elements (wrapper versus Actions cell); applying sticky or overflow to the entire page would recreate the wrong behavior.

### 5. Backend / API behavior

No backend/API, service records, RBAC grants, pricing, search, filtering, pagination or archive/restore behavior changed. The shared partial's physical Facilities output already used fixed positioning and retains it. Only Services gets the new containment/sticky/wrapping CSS. Read-only users still receive the existing View-only controls; these changes do not grant management access.

### 6. Database / migration impact

No model, migration, package install, seed, live record edit or data command is needed. Refresh Services after Django reloads the template. If stale styling remains, use a hard refresh and confirm the Services stylesheet query version `20261017-service-table-overflow`. Normal deployed static collection rules still apply.

### 7. Tests performed and manual verification

Executed **8 existing Django service navigation/authorization tests**, all passed in 1.371 seconds with clean system checks. They include Services/Service Requests separation, real records, read-only and Marketplace restrictions, empty/paginated states and service-versus-physical reservation boundaries. No new tests were written merely to mirror CSS declarations.

Chrome passed Services at **1920, 1440, 1024, 768, 390 and 320px** using actual isolated Django-rendered fixtures and local copies of the existing assets. Checks covered wrapper/card bounds, zero side bleed, no unnecessary desktop scroll, local small-screen horizontal scrolling, sticky Actions, fixed menu positioning, viewport bounds, unchanged table height/no menu-induced vertical scroll, first/last-row hit-testing, menu usability after horizontal scrolling, Edit Service navigation, Escape/focus restoration and no JavaScript errors or document overflow. Service Requests also passed document overflow/JavaScript checks at the same widths; its request actions were not separately changed or re-tested here. Desktop and phone screenshots were inspected.

Initial browser diagnostics caught sticky-cell menu overlap and the higher-specificity nowrap rule at tablet width; both were corrected before the final all-width run. The first automation selector also matched a header dropdown rather than the row control and was narrowed to `.facility-col-actions`; that selector error was not a product defect. Fixture preparation replaces remote assets locally and performs no live API writes. Physical phones, screen readers and non-Chrome engines were not tested.

Run from `backend/core`: `.\venv\Scripts\python.exe manage.py test modules.facilities.test_service_navigation --keepdb --noinput`.

Manual checks: open Services, compare table edges with filters/footer, open the first and last three-dot menus and click Edit. At a narrow width, scroll the table horizontally and confirm Actions stays at the right and its menu stays usable. Escape should close it and return focus to the trigger. Check filter wrapping at tablet width and verify the page itself never gains horizontal scroll. View the normal Facilities page to confirm its existing layout/actions remain.

### 8. Remaining limitations, debugging and safe practice

Small screens intentionally need horizontal table scrolling to preserve six readable columns. Actions stays visible; the other columns move within the local scroller. This is not a whole-table mobile card redesign. Existing row action size, status styling and service editor remain outside this spacing correction.

Debugging: inspect computed margins/width on `.service-catalog .table-responsive`, not just the authored low-specificity rule. They should be zero side margins and the same width as the card interior. If a menu is behind another row, inspect the open/focused Actions cell's z-index and existing Popper strategy before disabling all overflow. Do not restore global `overflow:visible` or hide body overflow to conceal a wide table; that either reintroduces the bleed or clips content. If an edited/new row behaves differently, check the dynamic `getRowMenuHtml` markup as well as the initial shared partial.

Safe practice: on an isolated browser fixture, temporarily disable only the service wrapper's zero-margin override in DevTools and observe the inherited 24px bleed, then restore it. Next disable the focused/open cell z-index while the first menu is open and see why later sticky cells can cover it. Restore both and verify the last-row menu and horizontal scrolling. This teaches cascade specificity, local overflow and stacking contexts without changing real service records.

## Job Order preparation before opening the tab (October 17, 2026)

### 1. Cause / reason

Confirmed in the code: the original Word template was converted only when the Job Order tab opened. The existing one-hour Django memory cache disappeared on worker restart, so an unchanged document could repeat the slow first conversion. The PDF.js library already loaded in parallel and the converter already reused a worker-private LibreOffice profile; those earlier optimizations are retained.

This change moves the authenticated PDF request earlier and adds a private persistent cache. It does not hide the loading message while leaving the document unavailable. A genuinely new or revised document still needs a real DOCX-to-PDF conversion; exact Word layout cannot be generated instantaneously by removing status text.

### 2. Exact files changed and code anchors

Current lines are approximate and may move with later development.

| File | Line / nearby code anchor | Change and reason |
| --- | --- | --- |
| `backend/core/core/settings.py` | 211, `JOB_ORDER_PDF_CACHE_DIR` | Store prepared PDFs outside public media/static directories. |
| `backend/core/.gitignore` | 6, `.cache/` | Generated private files must not become source-code artifacts. |
| `backend/core/modules/facilities/services/job_order_docx.py` | 208, `prepared_documents`; 215, `prepared_pdf`; 226, `job_order_pdf` | Add bounded disk reuse around the existing conversion and content hash. |
| `backend/static/components/js/job_order_preview.js` | 21, `prepare`; 44, `load`; 133, exported API | Separate early fetch/library preparation from visible canvas rendering. |
| `backend/static/components/js/admin_booking_workflow.js` | 199, `CampusHubJobOrder.prepare` | Start preparation after the saved Booking Details payload creates a valid Job Order host, while Overview remains selected. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 71, `job-preload` | Refresh both changed JavaScript asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 15, `job-preload` | Standalone paper loads the same updated preview module. |
| `backend/core/modules/facilities/test_job_order_preview.py` | 16, `setUp`; 65, `test_prepared_pdf_survives_memory_cache_reset_without_reconverting`; 74, unwritable-cache test | Isolate disk caches and verify restart reuse, changed content and graceful storage failure. |
| `docs/facility-configuration.md` | this section | Explain implementation, verification, troubleshooting and learning exercise. |
| `CAMPUSHUB_CONTEXT.md` | final Job Order preparation entry | Preserve the current policy for future development. |

Local verification helpers are in `scratch/job-order-docx/measure-preload.py`, `test-preload.py`, and `check-preload.cjs`; they are not application routes or runtime dependencies.

### 3. Changes made

The early request starts once per current preview host, not on every tab click. Overview remains usable. Opening Job Order consumes that same in-flight or finished request, then renders pages at the actual visible host width. Hidden canvases are not rendered. Existing document refresh after Edit Draft creates a fresh host/request, so old bytes are not reused as the updated document. Pending bookings have no Job Order host and trigger no preparation.

Prepared PDFs now use Django's file cache at `backend/core/.cache/job-order-pdfs`, with a seven-day logical expiry and a 200-entry bound/culling policy. Existing memory caching remains one hour. Failed conversion output is never saved. If private storage is unavailable, conversion and memory caching still work, but cross-restart reuse is lost. File-cache expiry is checked on access and culling; it is not a scheduled secure-erasure service.

### 4. How it works: functions, inputs, outputs and data flow

`prepare(host)` takes the current preview DOM element with its protected PDF URL. It returns an internal state containing an AbortController and a promise for the PDF blob plus PDF.js library. It does not navigate, show a hidden PDF viewer, or render a hidden canvas. A handled promise rejection is retained for `load(host)` to display through the existing error/Retry state.

`load(host)` takes the same element, reuses its prepared state and renders the PDF onto plain white paper. `dispose()` aborts outstanding work, releases render/print resources and clears host states on page lifecycle/booking refresh. No private PDF is stored in browser localStorage or a service worker.

`prepared_documents()` creates a Django FileBasedCache using the private configured folder. `prepared_pdf(key)` returns valid PDF bytes from memory or that private cache, or `None` if absent/expired/unusable. `job_order_pdf(data)` still fills the original DOCX, hashes the complete filled document, checks caches, serializes conversion within the worker, rechecks caches, converts when necessary and saves successful bytes. A change in saved fields or original template changes the hash, so the old PDF cannot satisfy the new request.

Annotated example: saved items `Projector` produce DOCX hash A and PDF A. A new Django process asks for the same saved fields and reads PDF A from the private disk cache. Editing items to `Projector and microphone` produces hash B, so the backend converts and stores PDF B. No database status or stock/payment field participates in this optimization.

Flow: authorized Booking Details data → create Job Order host on Overview → early protected PDF request + renderer import → saved booking fields → original DOCX → content hash → private prepared PDF or real conversion → tab opening consumes ready bytes → visible paper/Print/Export.

### 5. Backend / API behavior

No new endpoint, background task queue, booking model, action, status or document-generation implementation. All requests still use the existing authenticated Job Order document route and its current booking/RBAC checks. A file being cached does not grant document access: authorization is checked before conversion/cache lookup in the document view. HTTP responses remain `private, no-store`; the server-only disk cache is separate from HTTP/browser caching. Print and PDF/DOCX Export retain the original template and existing workflow. No synthetic data or production test bookings were added.

### 6. Database / migration impact

No migration or package installation is needed. Django creates the private cache directory on use; the server account needs write access there. Restart Django if it has not reloaded the new Python/settings code, then refresh Booking Details to load the versioned JavaScript. Never expose this cache folder through a static/media URL or commit its contents.

### 7. Tests performed and actual results

- Six isolated preview/cache tests passed in 0.239 seconds. They cover identical reuse, changed fields, template invalidation, memory-reset/disk reuse, unwritable storage fallback, same-worker concurrent coalescing and failed conversion retry.
- Final combined preview and existing booking-workflow run: **87 tests passed in 46.542 seconds**, including real LibreOffice A4/long-document exports, private downloads, pending/read-only restrictions and preserved Word access on conversion failure. Generated caches were isolated in a temporary directory; database tests used the existing test database, not live records.
- Both changed JavaScript files passed Node syntax checks.
- Chrome at 1440, 768, 390 and 320 pixels passed early request on Overview, no hidden canvas, reuse on first open and tab switching, no preparation for Pending, edited-draft refresh, read-only/standalone paper, error/Retry, authenticated export dropdown, Escape/focus, Print routing, multipage rendering and no document overflow. Desktop and phone screenshots were inspected. Browser transport used isolated fixtures with a simulated 300 ms PDF response; this is not a live-network timing claim.
- Before this change, an isolated real local conversion measured **13.964 s** and memory reuse **0.020 s**. After the change, a new uncached test PDF still took **14.983 s**, then disk reuse after clearing memory took **0.043 s**. A separate new Python/Django process reused that prepared PDF in **0.024 s** (next memory-reset call **0.018 s**). These are local measurements, not a guarantee for every server.
- Browser prepared-tab-to-paper observations were approximately 209–315 ms after the fixture PDF response had arrived. They include automated polling/render time and must not be presented as real LibreOffice conversion timing.

Repeat backend verification from `backend/core`: `venv/Scripts/python.exe manage.py shell -c "exec(open('../../scratch/job-order-docx/test-preload.py').read())"`. The helper overrides the private cache path with a temporary folder and runs the two relevant test modules.

Manual checks: open an approved test booking and stay on Overview briefly, then open Job Order. Confirm the request began before opening the tab. Switch tabs and confirm no second PDF request. Refresh/restart Django and open the unchanged document again; conversion should be skipped while its prepared entry is available. Edit one saved draft field and confirm the new PDF contains that value. Check Print and both Export formats. Pending must still show no document. Use isolated test records for edits.

### 8. Remaining limitations, debugging and safe practice

There is still first-use latency if the PDF is new, revised, expired, culled, or its private cache is cleared. Opening Job Order immediately after the page loads can still encounter an unfinished conversion. This change moves that work earlier and preserves successful output; it does not promise zero-time first conversion. Multiple server processes have separate Office profiles/locks and can independently convert the same first uncached document; the disk cache is shared on one filesystem, not a distributed conversion lock or queue. Physical phones and other browser engines were not tested.

Debugging: in DevTools Network, the Job Order PDF request should begin on Overview. If it does not, check the new script versions and that an authorized Job Order host exists. If unchanged documents repeatedly convert after restart, check server write permissions for `JOB_ORDER_PDF_CACHE_DIR`, cache culling/expiry and whether saved data/template really changed. Keep the loading/error state honest; removing its text does not improve conversion speed. If the PDF request returns 401/403, inspect existing session/RBAC rather than bypassing the protected route. LibreOffice failures retain the current Retry/Word recovery behavior.

Safe practice: read `test_prepared_pdf_survives_memory_cache_reset_without_reconverting`. In that isolated test only, change the `items` input and predict that the mocked conversion count increases from one to two. Run the preview test module and verify that prediction. Then, in the isolated browser fixture, compare Network request timing before and after opening Job Order. This teaches the difference between reusing results, overlapping work and making the underlying conversion itself faster, without changing live records.

## Explicit Edit actions for Booking Slip and Job Order (October 17, 2026)

### 1. Cause / reason

Confirmed from the current renderer: Job Order still used the existing editor but called its button `Edit Draft`; Booking Slip had only Print and Export PDF in its toolbar. Booking editing was accessible elsewhere in Overview. This made editing within the document tabs unclear. The prior PDF preparation change did not remove the Job Order editor.

### 2. Exact files changed

| File | Approximate current line / code anchor | Change |
| --- | --- | --- |
| `backend/static/components/js/admin_booking_workflow.js` | 17, `titles`; 192, `bk-form-toolbar`; 197, `beu-job-panel-actions` | Explicit `Edit Job Order` label and `Edit Booking Slip` toolbar action. |
| Same JavaScript | 19, `reservationReturnTab`; 233, `action==='edit'`; 395, `campushub:reservation-created` | Remember whether reservation editing started on the slip and restore the updated slip/focus after save. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 72, `document-edit-actions` | Version the changed script so refresh loads the new buttons. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 157, `test_edit_excludes_only_itself_and_preserves_identity` | Verify saved purpose appears in the generated slip, same booking is retained and existing paid-booking restrictions remain. |
| `docs/facility-configuration.md` | this section | Implementation report and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | final document Edit entry | Preserve current behavior for later work. |

Local browser verification helper: `scratch/job-order-docx/check-edit-actions.cjs`, adapted from the existing isolated paper preview harness. It is not an application dependency.

### 3. Changes made

Booking Slip has `Edit Booking Slip` beside Print/Export PDF. Job Order shows `Edit Job Order` rather than `Edit Draft`, including the small editor dialog title. Reuse existing navy/white toolbar button styles and wrapping, with no new CSS or page layout. Both actions still depend on the backend-provided `booking.actions`; the frontend does not grant editing rights.

### 4. How it works

`actionButton(action,label)` accepts an existing backend action identifier and visible label, and returns a button only when that action is allowed. Slip uses `edit`; Job Order uses `job_order`. `editor('edit')` records the selected document tab, then emits the existing `campushub:edit-reservation` event with the current booking payload. `admin_booking_forms.js` already listens for this event and opens/populates Edit Reservation. The document is generated from these saved reservation fields, so there is no second unsynchronized paper editor.

On successful reservation save, the existing `campushub:reservation-created` event carries the saved booking ID. The Details listener reloads that same booking using the existing API, selects Booking Slip when editing began there and focuses `Edit Booking Slip`. Failed saves do not emit this success event or replace the document. Ordinary edits begun on Overview still return to Overview.

`editor('job_order')` continues using the existing saved Job Order draft form and update action; successful saves refresh that tab and its DOCX-derived PDF as before. Early PDF preparation from the previous fix remains in place.

Example: change reservation purpose from `Training event` to `Revised slip purpose`, review the quote and save. The same booking ID remains, and the regenerated Booking Slip includes `Revised slip purpose`. Editing Job Order specifics remains a separate action because those are office draft fields rather than reservation/pricing fields.

### 5. Backend / API behavior

No new endpoint or duplicate save logic. The existing `allowed_actions` helper still determines eligibility and the locked update view rechecks it. Slip editing requires existing booking permissions, an active Pending/Approved booking and no recorded payment, as before. Job Order editing requires approved status and Manage Bookings permission; payment alone does not disable Job Order editing. Completed/read-only bookings retain viewing/printing/exporting without newly granted editing rights. Slip and manually edited Job Order data are not silently overwritten by each other; existing untouched-draft refresh behavior remains.

### 6. Database / migration impact

No migration, new database field, dependency or installation command. Refresh Booking Details; the changed script version is `20261017-document-edit-actions`.

### 7. Tests performed

Node syntax check passed for `admin_booking_workflow.js`. Chrome at 1440, 768, 390 and 320 pixels verified the explicit slip action, opening the real existing Edit Reservation form with saved purpose, returning/focusing the slip after a simulated success event, Job Order edit/save/refresh and new label, no edit action for read-only fixtures, Print/export/Retry/standalone/multipage behavior and no horizontal page overflow. These were isolated browser fixtures; the slip save-success event was simulated rather than a live API write. Backend save behavior is checked separately in Django.

Five focused Django workflow tests passed in **24.615 seconds**: reservation edit preserves identity and updates generated slip text, saved Job Order updates one record, booking edits refresh only untouched generated drafts, Pending denies Job Order access/edit, and Completed historical documents remain read-only. The extended test also verifies paid bookings lose reservation edit while retaining their separately eligible Job Order edit action. Tests use isolated database records. No live booking was edited.

Run from `backend/core`: `venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow.BookingWorkflowTests.test_edit_excludes_only_itself_and_preserves_identity modules.facilities.test_booking_workflow.BookingWorkflowTests.test_job_order_is_structured_and_updates_one_record modules.facilities.test_booking_workflow.BookingWorkflowTests.test_booking_edit_refreshes_only_untouched_generated_draft modules.facilities.test_booking_workflow.BookingWorkflowTests.test_pending_booking_never_exposes_or_edits_job_order modules.facilities.test_booking_workflow.BookingWorkflowTests.test_completed_legacy_job_order_backfills_and_stays_read_only --keepdb --noinput`.

Manual check: open an active unpaid booking as authorized facilities staff. In Booking Slip, click Edit Booking Slip, change a field on a test booking, review its quote and save; confirm the refreshed slip and the same booking ID. In Job Order, click Edit Job Order and save draft fields; confirm the paper refreshes. Check a paid booking: reservation/slip edit stays restricted while Job Order editing follows its separate existing eligibility. Read-only and Completed records must not gain edit buttons.

### 8. Remaining limitations, debugging and safe practice

The paper is not directly editable like a Word document: its values come from saved booking/draft data. Existing paid/terminal status locks remain intentional. If an Edit button is missing, inspect the authorized Details JSON `booking.actions` before changing visibility or permissions. Missing `edit`/`job_order` means the backend currently disallows that operation; do not bypass its guards with a hardcoded button. If the label remains Edit Draft, refresh the versioned JavaScript and check for stale browser assets.

Safe practice: in the isolated browser fixture, compare an authorized booking's action list with the read-only fixture. Predict which Edit button appears, then verify it. Next run the focused Django edit test and inspect how updating the booking purpose changes `booking_form_html` while `Booking.objects.count()` remains one. This teaches authorization-driven UI and generated documents without editing production data.

## Cancelled booking history and separate record archiving (October 17, 2026)

### 1. Cause / reason

Cancelled bookings already lost most editable actions through `allowed_actions`, but direct POST errors were generic, the row menu hid useful historical document links, Overview did not show cancellation information, and empty inspections showed workflow availability instructions. Inspection/history records and payments were already retained. There was no booking archive field or booking archive/restore action: existing archive fields belong to Facilities/Products and must not be reused as a booking's status.

The user confirmed cancelled bookings must stay read-only. This change strengthens that rule, preserves document access and adds a separate, permission-scoped record archive using the existing booking sidecar JSON. It does not reopen cancelled or Completed records.

### 2. Exact files changed

Approximate current lines and nearby anchors:

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/booking_workflow.py` | 22, `CANCELLED_READ_ONLY`; 25, `require_writable_booking`; 130, `allowed_actions`; 180, `is_archived`; 339, `transition` | Shared cancelled write guard, archive/restore eligibility and sidecar-only persistence, record flag in row payload. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 42, `list_data`; 221, `require_writable_booking` | Current/Archived/All query, legacy-safe archive exclusion, guard inside the existing locked update transaction. |
| `backend/core/modules/facilities/mobile_views.py` | 227, cancellation metadata | Save actual requester/time when the owner cancels; preserve other metadata and payment rows. |
| `backend/core/accounts/views.py` | 1143, `booking_record_filter` | Preserve the selected record filter in server-rendered Bookings. |
| `backend/static/components/js/admin_booking_workflow.js` | 141, `Cancellation Information`; 167, `No inspection recorded`; 190, cancelled badge; 246, archive confirmation; 366, focus restoration | Clear historical display, archive/restore confirmations and existing editor/notification transport reuse. |
| `backend/static/components/js/admin_bookings.js` | 25, `bookingRecordFilter`; 84, `record_status`; 293, cancelled menu; 319, menu position | Historical links, Archive/Restore, record filter/error rollback and viewport-safe menu placement. |
| `backend/static/components/css/admin_booking.css` | 18, `.bk-cancelled-status`; 1621, filter grid | Compact navy/light Cancelled badge and four-field responsive filter row. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_bookings.html` | 138, `bkRecordFilter` | Record Status selector and updated CSS/JS asset versions. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 13, 69, 72, `cancelled-history` | Updated assets on Details. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 994, `cancelled_history`; 1012–1085, four cancelled-history tests | Historical private records, denied writes, no invented metadata, permission checks and archive/restore invariants. |
| `backend/core/api/test_mobile_facility_booking.py` | 139, `saved_cancel` | Verify actual mobile cancellation actor/time without inventing a reason. |
| `docs/facility-configuration.md`; `CAMPUSHUB_CONTEXT.md` | this section; final cancelled-history policy | Learning/debugging guide and future context. |

Local verification helpers: `scratch/cancelled-history/check.cjs` and updated `scratch/job-order-docx/test-preload.py`. These are isolated QA tools, not new runtime dependencies.

### 3. Changes made: documents, inspections, overview, payments and archive

- Cancelled records hide booking/slip/Job Order editing, inspection recording/editing, personnel assignment, payment recording, supporting-document creation, completion and repeat cancellation. A direct supported workflow POST returns `Cancelled bookings are read-only and can no longer be edited.` Authorized Archive/Restore is the only visibility-management exception.
- Saved Job Orders remain viewable/printable/exportable from the original DOCX/PDF logic, without Edit. Booking Slips continue rendering from saved reservation data with Print/Export and no source-edit action. The existing PDF/DOCX export dropdown is retained.
- Saved pre/post inspections and protected evidence remain accessible through View Details and existing report links. Missing phases say `No inspection recorded.` No new inspection is fabricated or added after cancellation.
- Overview shows cancellation reason, actual saved actor and date/time, a compact Cancelled badge, and Current/Archived record status. It omits Completion Readiness and its workflow buttons. Missing old cancellation values show `Not recorded`; no actor/reason/date is guessed. New mobile cancellations now save the real requester and time; the mobile form does not collect a reason, so none is invented.
- Payment amounts/status, original amount due, balance, receipt number, method, paid time, history and private receipt attachment remain intact. No refund engine or Refunded status exists in this facility payment workflow. Cancellation/archive/restore does not create a refund, erase payment or reset financial status; refund functionality was not invented.
- Cancelled row menus offer View Booking, Booking Slip, saved Job Order when present, Payment Details, inspection viewing, Activity, then Archive Booking or Restore Booking below a divider. A record with no Job Order does not gain a fake document. Read-only users receive historical links without management actions.
- Record Status filter supports Current Records (default), Archived Records and All Records. Restore changes visibility only: booking status remains Cancelled. Archives preserve all documents/payments/inspection data. Completed workflow restrictions are unchanged.

### 4. How it works: functions, inputs/outputs and data flow

`require_writable_booking(booking, action)` accepts the existing Booking object and action code; it returns normally for eligible workflow categories or raises Django ValidationError for a cancelled workflow write. It is called by the locked admin update view before edit field validation and by the shared `transition` helper, preventing direct requests from bypassing UI rules. Existing permission/CSRF checks still run.

`allowed_actions(booking, user)` returns only `archive` or `restore` for a cancelled booking when the user has the existing Manage Bookings grant; otherwise it returns an empty list. Other statuses retain existing rules. `transition(request, booking, data)` stores `details.archive = {is_archived, by, at}` through `save_details`, then returns `booking_archived`/`booking_restored` for the existing audit helper. It never sets Booking.status, changes payments or rewrites documents for an archive operation. Repeating Archive on an archived record or Restore on a current record is rejected without duplicate audit writes.

`list_data(params, user)` reads `record_status`. It uses a subquery selecting positively archived sidecar booking IDs, then includes/excludes those IDs. This is deliberate: SQL `NOT JSON=True` can exclude rows whose JSON key or sidecar is missing. Current Records must include these historical/normal records. KPI and list results use the selected record scope; normal analytics/payment data sources are not rewritten.

`renderOverview` consumes saved cancellation metadata; `renderInspections` consumes actual phase records; `showMoreActions` consumes backend action/inspection metadata. Archive/restore uses the same small confirmation dialog, JSON update route, success alerts, retry display and audit chain as current booking actions. Escape/focus handling includes the new confirmations. After success, focus moves to the new Restore/Archive control. Fixed menu placement uses the visible client viewport excluding its scrollbar so phone menus remain reachable.

Example: an approved booking with a paid receipt is cancelled. It remains `status=cancelled`, payment remains `paid`, and existing document/inspection history remains. Archive adds a visibility snapshot and audit entry, so the row moves to Archived Records. Restore sets that snapshot false and appends an audit entry; the row returns to Current Records as Cancelled, with no Edit or Complete action.

### 5. Backend / API behavior and helpers reused

Reuse Booking, FacilityBookingRequest.details, FacilityPayment, `metadata`, `save_details`, `allowed_actions`, `transition`, `booking_row`, existing private document/attachment views, `audit`/AccountActivity, user grants and the existing Facility-then-Booking transaction lock order. No duplicate payment, document, inspection, cancellation or logging system was added.

Existing protected endpoints: `GET /api/bookings/?record_status=current|archived|all`, `GET /api/bookings/<id>/`, and `POST /api/bookings/<id>/update/` with `action=archive|restore`. Existing document and attachment URLs remain private. Archived Details remain viewable; archiving is not deletion or an access grant. Mobile ownership and cancellation start-time checks remain in place. Mobile history remains accessible; web record archiving does not delete it.

### 6. Database / migration impact

No migration, model, duplicate status field or package installation. The existing JSON sidecar stores archive metadata, separate from Booking.status. No live records were seeded, cancelled or archived for testing. Refresh web assets after Django reloads the Python code; asset version is `20261017-cancelled-history`.

### 7. Tests performed and how to verify

Final backend run: **114 tests passed in 49.677 seconds**, covering preview, booking workflow, Calendar and mobile booking modules. Four added history tests verify all supported non-archive workflow actions reject cancelled records without data/audit writes; saved private receipt/evidence/Job Order/slip/history remain; archive/restore preserve cancellation and finances; duplicate management actions fail; permissions hold; Completed/active/rejected records do not reopen; and legacy reads do not fabricate metadata. The mobile test verifies actual saved requester/time and no invented reason.

An initial regression run caught two list/KPI failures caused by the nullable JSON exclusion. The positive-ID subquery correction above resolved them in the final full run. This was a confirmed query defect, not missing production bookings. An initial browser harness also used unrelated test-booking IDs for archive/restore responses; the simulation was corrected to represent one record before UI assertions continued.

Both changed JavaScript files passed Node syntax checks. Chrome at 1440, 768, 390 and 320 pixels passed cancelled paid/history/archived/read-only/legacy states, hidden writes, blocked edit deep links, cancellation content, no fake inspection, historical paper/Print availability, archive error/retry/restore, Escape/focus, record filters, row menus, viewport bounds and no page overflow. Desktop and phone screenshots were reviewed. Browser API transport and historical PDF bytes were isolated fixtures, not live writes; real backend record/permission tests ran separately. Actual printer dialogs, physical phones and other browser engines were not tested.

Repeat isolated backend run from `backend/core`: `venv/Scripts/python.exe manage.py shell -c "exec(open('../../scratch/job-order-docx/test-preload.py').read())"`. That helper uses a temporary PDF cache and runs the four relevant test modules. The ordinary targeted module command is `venv/Scripts/python.exe manage.py test modules.facilities.test_booking_workflow modules.facilities.test_calendar api.test_mobile_facility_booking modules.facilities.test_job_order_preview --keepdb --noinput`.

Manual checks on test data: cancel a future approved paid booking with a reason. Inspect every tab: no editing/recording/completion, but saved paper/inspection/evidence/payment/activity still works. Attempt a direct update POST as authorized staff and expect the explicit read-only error. Archive, select Archived Records, verify the same Cancelled/Paid record and receipt, then Restore and verify Cancelled remains. Check a read-only account gets no management action. Check an old missing-cancellation record shows honest missing values, and a normal booking without archive metadata is still visible.

### 8. Remaining limitations, debugging and safe practice

Old cancellation actor/time/reasons cannot be reconstructed reliably when they were never stored; this change does not backfill guesses. The existing Activity payload shows its latest 50 records; all stored audit records remain preserved. Only Cancelled records receive the new booking Archive/Restore flow; Completed retains existing behavior. No refund or financial settlement engine was added. Archive status is a latest snapshot; successive management actions remain in the audit log.

Debugging: inspect `booking.status`, `booking.actions` and `booking.is_archived` in the protected Details payload. A cancelled row should have only Archive or Restore for an authorized manager. If it disappears from Current Records, check its archive snapshot and the selected Record Status filter before changing Booking.status. If normal legacy rows disappear, verify the positive-ID archive subquery rather than using negation of a nullable JSON field. If receipts fail, check current session/RBAC and the saved attachment; never copy private files into public static storage to make a link work. Stale pages with old action buttons still fail safely on the server.

Safe practice: run `test_cancelled_archive_restore_preserves_status_finances_and_history` in the test database. Read the three stages: Cancelled/Current → Cancelled/Archived → Cancelled/Current. Add a local assertion that the receipt number stays the same at each stage, run the test, then remove the practice assertion. Next compare `exclude(pk__in=archived_ids)` with a negated JSON lookup using isolated legacy fixtures and observe why missing keys need care. This teaches separate business/record statuses, server-side guards and SQL NULL behavior without touching real bookings.

## Explicitly authorized deletion of two cancelled booking records (October 17, 2026)

### 1. Cause / reason and scope

The user explicitly chose permanent deletion of both identified cancelled booking requests and their linked financial/document/inspection data after being informed that the scope included two payments and sixteen audit entries. This was a one-time database maintenance operation, not a new delete action in the application. Normal cancelled bookings remain read-only and use Archive/Restore.

Exact confirmed Booking IDs: `BK-2026-2AD68545EC0C4258` and `BK-2026-0F9C4F6D65D84090`. No broader deletion query or status-based bulk wipe was used.

### 2. Files changed

- `scratch/cancelled-history/delete-confirmed-records.py`: line 19, `CONFIRMED_IDS`; line 21, atomic transaction; line 43, PDF keys; line 47, explicit payment deletion; line 64, matching cache purge. This is an executed one-off maintenance helper, never imported by application code.
- `docs/facility-configuration.md`: this maintenance report.
- `CAMPUSHUB_CONTEXT.md`: final maintenance note so later development does not mistake the empty Bookings list for a loading failure.

### 3. Changes made and actual deletion result

Deleted two Booking records, two FacilityBookingRequest sidecars, two FacilityPayment records and sixteen linked Facility Bookings AccountActivity entries. Sidecars contained the two saved Job Orders, two saved inspection records and associated document/receipt/evidence metadata. The generated Booking Slip uses saved booking data and is no longer accessible for those deleted IDs. The two matching current-template Job Order PDF entries were removed from memory/private file caches.

The unrelated remaining Booking record and its sidecar were retained, as were 329 unrelated AccountActivity entries. The physical booking-request list now contains zero records. No facility, account, product, order or application business-rule update was performed by this script.

### 4. How it works: inputs, outputs and data flow

Inputs are the two fixed confirmed IDs and expected linked counts `(2 payments, 2 sidecars, 16 audit entries)`. The script acquires Facility then Booking locks inside `transaction.atomic`, requires exactly those two records still exist and remain Cancelled, and refuses to continue if their related counts changed. It records unrelated counts and computes current PDF cache keys using the existing filled-DOCX content hash.

FacilityPayment uses `on_delete=SET_NULL`, so deleting the parent alone would leave orphaned payment records. The authorized cleanup therefore explicitly deletes only payments linked to the confirmed IDs. It removes only audit entries with both the Facility Bookings module and matching metadata booking IDs, then deletes the two parents. Django cascades the sidecar deletion, including its embedded document data. Assertions verify the selected data is absent and unrelated counts remain unchanged before the transaction commits. After commit, only the computed Job Order cache entries are purged.

Output is deletion counts and verification counts, not a customer-data export or backup. The script intentionally has no fallback to all bookings and refuses to run again once the confirmed records are absent.

### 5. Backend / API behavior

No endpoint, permission, model, refund, cancellation or ordinary archive behavior changed. The deleted IDs no longer resolve as booking records; normal list requests return an empty physical booking-request list. No maintenance action was exposed to normal admin UI users.

### 6. Database / migration impact

This operation permanently removed the selected live database rows as expressly requested. No migration, schema change or package installation was needed. Do not rerun the maintenance helper as an installation step.

### 7. Verification performed

Before deletion, Django's collector and database foreign-key introspection confirmed the sidecar cascade and the separate payment SET_NULL relationship. The transaction completed successfully with the exact deletion counts above. All selected-record absence assertions and unrelated-count assertions passed. A separate fresh Django shell then confirmed zero physical booking requests and zero matching Booking, sidecar, payment or audit rows; the one unrelated Booking remained. This was live database verification of the authorized operation, not a unit-test run. No application test suite was rerun because application code did not change.

### 8. Limitations, troubleshooting and safe learning exercise

This does not erase files users previously downloaded, browser memory, independent backups or every historical converter-version cache; only the selected live records and matching current-template server cache entries were targeted. Refresh an already open browser page to clear its previously loaded record display. Do not interpret an empty list as an API error after this cleanup.

Safe practice: in an isolated test database, create a disposable booking and payment, inspect Django's deletion collector, and observe the difference between SET_NULL and CASCADE. Run a transaction that deletes the disposable parent and deliberately raises an exception; verify the parent/payment still exist after rollback. This teaches relationship-aware deletion and transaction recovery without executing this live maintenance helper or touching real records.

## Service-specific catalog configuration and labelled filters (October 17, 2026)

### 1. Cause / reason

The existing Services catalog already reused Facility storage, a separate service editor and three service modes. Missing pieces were visible filter labels, analysis charging bases, explicit assessment dates, lease-space-specific rate/area/utility settings, direct status actions and persisted service audit events. The shared activity hook previously skipped services entirely. Most validation, image upload, weekly hours, archive/restore and permission handling already existed and were extended rather than replaced.

The UI follows the existing navy/gold/white components. This is a refinement of Services, not a redesign of physical Facilities or a new service transaction engine. New configurations are entered by administrators; no example price, date, requirement or service offering is seeded into live data.

### 2. Exact files changed and approximate current lines

| File | Line / nearby anchor | What changed |
| --- | --- | --- |
| `backend/core/modules/facilities/services/service_configuration.py` | 11, `CATEGORIES`; 20, `CHARGING_BASES`; 37, choices; 51, `service_pricing_label`; 73, `validate_service_payload`; 227, assessment dates; 257, lease details | Category labels, supported pricing/payment choices, validated dates and per-space settings, archived-write guard and real pricing summaries. |
| `backend/core/modules/facilities/services/activity.py` | 21, service event catalog; 44, `facility_snapshot`; 71, `record_facility_activity`; 126, `recent_facility_activities` | Reuse the existing audit hook for Services, detect pricing/status changes, suppress no-op events and scope recent service events separately. |
| `backend/core/accounts/views.py` | 800, `service_events`; 818, `can_view_service_requests` | Display persisted service events and provide the actual request-view permission to menus. |
| `backend/core/modules/facilities/service_views.py` | 29, `service_id`; 45, service filter context | Existing Service Requests route can filter to the selected service. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_facility.html` | 97–146, filter fields; 514, `serviceStatusModal`; 1399, row menu; 1445, pricing label; 2195, status confirmation | Visible filter labels, service-specific menu integration, status confirmation/save/retry, current pricing retained and updated assets. |
| `backend/core/modules/facilities/templates/facilities/partials/service_form.html` | 27, term rates; 34, availability help; 48, assessment dates; 54, lease-space container | Keep eight sections and reveal the new category-specific fields in the existing form. |
| `backend/core/modules/facilities/static/facilities/js/service_form.js` | 46, `sync`; 96, `addAssessmentDate`; 107, `syncLeaseSpaces`; 139, `rowMenu`; 203, `validate`; 224, payload | Dynamic headings/disclosure, repeatable dates, per-space fields, row actions, restored saved data and clean submission payloads. |
| `backend/core/modules/facilities/static/facilities/css/admin_services.css` | 26, filter grid; 43, request filters; 77, repeated configuration rows | Label alignment, responsive controls, compact analysis/date/lease fields and preserved local table scrolling. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_service_requests.html` | 24–31, filters; 54–56, pagination | Search/Request Status labels, visible selected service and persistent service filtering through searches/pages. |
| `backend/core/modules/facilities/test_service_configuration.py` | 384–478, five new configuration/history tests | Test charging bases, dates, mixed lease pricing, status/audit/history, filter labels and request scoping. |
| `backend/core/requirements.txt` | 12, `dj-database-url` | Declare the dependency already imported by the current settings; it was absent from the local environment. |
| `docs/facility-configuration.md`; `CAMPUSHUB_CONTEXT.md` | this section; final Services context entry | Implementation guide, debugging, verification and future context. |

QA helpers/assets are isolated in `scratch/service-final/`, including `editor-check.cjs` and `table-check.cjs`. They are not application routes or dependencies.

### 3. Changes made

**List and menus.** Keep the four existing KPI cards and six columns: Service, Category, Pricing, Request Type, Status, Actions. Labels now appear above Search, Category, Status, Request Type and Record Status. Current/Archived filtering is retained. The compact three-dot menu contains View Service, permitted Edit Service, and View Service Requests only when the account has existing booking/request read permissions. Status actions match the current state: Active offers Temporarily Unavailable/Inactive; Temporarily Unavailable offers Active/Inactive; Inactive offers Active. Existing Archive/Restore remains available to managers. Archived services require restoration before editing/status changes. New AJAX-rendered rows use the same menu builder as initial browser rows.

**Add/Edit and category behavior.** Keep Service Images, Basic Information, Request Configuration, Pricing Configuration, Service Availability, Service-Specific Configuration, Requirements and Terms. Section 6 immediately becomes Food Analysis Configuration, BPP NC II Configuration or Lease Configuration for the selected category. Invalid/blank category alone shows the selection prompt. Request/output suggestions remain editable and do not override a deliberate choice. Existing image upload, six slots, saved image restoration/removal, requirement textarea and per-service terms remain.

**Food Analysis.** Keep configurable sample submission and turnaround information. Analysis rows support name, description, fee, Active and Charging Basis: Per Analysis or Per Sample. New rows have blank names/fees and an explicit selectable basis; old rows without a saved basis retain the prior Per Analysis meaning. No laboratory price or submission requirement is hardcoded. Analysis pricing does not require a fake single general service price.

**BPP NC II.** Keep Assessment/Training Name, optional positive Candidate Capacity, configurable Assessment Fee with the existing Per Candidate basis, and the real scheduling choices. Specific Date reveals repeatable assessment dates with optional start/end times; both times must be entered together and end must be later. Dates are validated and duplicate date/time combinations rejected. Dates may remain unconfigured rather than fabricated. Admin-Assigned Schedule describes submission first/scheduling later. No Scheduled Appointment hides assessment-date inputs and does not require a calendar slot.

**Lease.** Keep the five supported space types and configurable Other text. Selecting a space reveals its location and applicable optional area, water/electricity/internet/utility details. Empty area/water fields are hidden for machine-only spaces unless sqm pricing applies; actual saved values remain visible. Each selected space can inherit service pricing or specify its own basis/rate. Support Fixed Monthly Rental, Per Month, Per Machine/Month, Per sqm/Month, Regular Term/Midyear, Custom/Subject to Agreement, and the existing Fixed Rate compatibility choice. Term pricing requires both real configured rates; custom pricing requires an explanation and allows no known fixed amount. No disputed stall or assessment price is inserted. Different space types can have different bases without copying the service record.

**Availability and internal documents.** Weekly hours remain optional and use the existing Operating Schedule dropdown/row style. Food Analysis help identifies sample/processing hours, BPP help distinguishes office hours from client appointments, and Lease help identifies application receiving hours. Even No Scheduled Appointment may keep optional office hours: these do not create appointments. Lease and assessment date configuration does not create physical calendar reservations. Job Order/SOA/Contract toggles stay absent; existing `service_document_requirements` owns effective document policy, while old compatibility flags/history remain preserved.

### 4. How it works: functions, inputs/outputs and data flow

`service_configuration_choices()` returns the existing category/request/status/pricing catalogs plus charging bases and lease pricing choices. `ServiceFormControls.sync()` reads actual selected values, updates headings, reveals relevant inputs and disables hidden controls. `fill(resource)` restores the saved Facility/workflow data; `payload(images)` returns one validated catalog payload with current fields and the shared image list. `addAssessmentDate` uses the existing 12-hour time dropdown helper and stores canonical `HH:MM`, not invented times. `syncLeaseSpaces` maintains selected space controls, and `leaseDetails` serializes only relevant enabled fields.

`validate_service_payload(data, facility=None)` merges partial updates with saved service settings, validates choices/numbers/dates/hours, strips irrelevant category-owned settings and returns the existing Facility field dictionary. New nested settings are `workflow_config.service.pricing_items[].charging_basis`, `assessment_dates`, `term_rates` and `lease_space_details[space_type]`. Dates are configuration, not new Booking rows. Existing saved request snapshots, payments and documents are not rewritten. Monetary/area inputs must be valid non-negative finite numbers; money retains at most two decimal places. Negative/NaN/invalid rows reject before saving.

`service_pricing_label(resource)` derives the table summary from real saved prices/analysis rows/space overrides. `rowMenu(resource, manage, viewRequests)` derives available UI actions from saved status/archive state and permission flags; it does not grant backend access. Status confirmation sends a partial update through the existing facility update route, retains pricing/images, adjusts current KPIs, displays the real audit response and supports retry. The current pricing label survives the row redraw.

`facility_snapshot` captures existing and service pricing settings. `record_facility_activity` now chooses Facilities or Services scope and records one real add/update/status/pricing/archive/restore event; identical saves still produce no duplicate event. `recent_facility_activities(services=True)` reads the newest five actual Services audit events. Existing legacy derived service summaries remain the fallback until real service events exist; historical requests/payments remain stored regardless of which recent rows are shown.

Example: a Lease service has a shared monthly rate and two space types. The stall can use that default with its configured area/water conditions, while the vendo overrides its basis to Per Machine/Month and supplies its own amount. Saving sends both space configurations in the same existing Facility JSON. Making the service Inactive changes its operational status and creates a status audit entry; it does not modify historical lease applications or payments.

Flow: saved Facility/service choices → shared list/editor → category disclosure and image selection → service payload → existing authenticated write API → shared service validator → Facility fields/workflow JSON → existing audit transaction → real serialized row/pricing/KPIs. Service Requests navigation uses `/admin-service-requests/?service=<real id>` and keeps that scope during searches/pagination.

### 5. Backend / API behavior and reused models/helpers

No duplicate Service model: the project already stores service offerings in Facility with service category/mode filters. Reuse Facility, Booking, FacilityPayment, existing workflow JSON, `validate_facility_payload` dispatch, shared number/weekly-hours/time helpers, image persistence, serializer, current service-request query, role grants and AccountActivity logger. Existing create/update/archive/restore endpoints remain. No new public API or role was added. Status mutations require the existing Manage Facilities permission; request links and destination pages retain their separate read permissions. Permanent service deletion remains disabled, preserving historical transactions.

Supported request values remain Service Request, Assessment Registration and Lease Application, rather than inventing an unimplemented generic Appointment status. Payment Timing labels/validated configuration now also support Upon Approval and According to Agreement. These are catalog policies, not automatic payment collection or invoice issuance.

### 6. Database / migration impact and commands

No model/schema migration. Facility already has `price_type` as a 20-character field, `rate`, capacity, operational status, images, requirements, terms and workflow JSON. The supported new `fixed_monthly`/`term` pricing keys fit that existing field and are validated only in service configuration. All new repeated settings use existing JSON.

Testing initially could not start because current settings already imported `dj_database_url`, but the environment lacked it. Installed `dj-database-url==3.1.2` into the existing Django venv and added that exact dependency to `backend/core/requirements.txt`. No database URL, settings value or credential was changed for this task. This is a startup dependency fix, not a service data source change.

From `backend/core`, use `venv/Scripts/python.exe -m pip install -r requirements.txt` on an environment missing declared dependencies. No migrate command is required for this feature. Restart Django if necessary and refresh Services to load `20261017-service-workflows` assets.

### 7. Tests performed and manual checks

**98 Django tests passed in 4.839 seconds** across service configuration, service navigation, existing facility rental configuration/form controls and facility archiving. New tests cover analysis basis round-trip/invalid input, assessment date uniqueness/time validation/no automatic bookings, per-space lease areas/fees/utilities/term rates, status/pricing audit/no-op behavior, archived-write denial, preserved completed requests/payments and service-scoped request links/filter labels. Existing tests confirm normal physical Facilities behavior remains. Two fixture-export tests were rerun after later template fixes (final fixture export passed in 0.303 seconds); these create isolated test records only.

An intermediate test correctly caught an attempted coupling of No Scheduled Appointment to weekly office hours. The code was corrected to preserve their existing independence; the current behavior is described above. A new test assertion was also corrected to compare Decimal monetary values rather than a formatting-dependent string. Neither required changing real records.

Chrome editor verification at 1440/768/390/320 pixels passed all eight sections, blank Add defaults/no seeded rates, dynamic headings, charging basis, assessment date payloads, lease saved-field restoration, independent space rates/utilities/term rates, status actions and error/retry, saved pricing after status changes, images, repeated edits, read-only controls and no page overflow. Browser save transport was mocked against isolated Django-generated fixtures; real persistence/permission tests ran separately in Django. Initial UI verification caught a wrong audit-response variable in the service save callback; it was corrected to `result.activity` before the final run.

Services table/browser checks at 1920/1440/1024/768/390/320 pixels passed labelled filter layout, containment/local scrolling/sticky Actions, unclipped menus, Edit, Escape/focus and no page overflow. Service Requests checks at those widths verified labelled layout/no JavaScript errors/no page overflow; they did not exercise a new request-processing workflow. Desktop/phone list, request and lease editor screenshots were inspected. Missing brand-image paths in local file fixtures were not treated as production upload failures. Python syntax checks passed for five changed Python files; Node syntax and targeted whitespace checks passed.

Run the backend checks from `backend/core`: `venv/Scripts/python.exe manage.py test modules.facilities.test_service_configuration modules.facilities.test_service_navigation api.test_facility_rental_configuration api.test_facility_form_controls api.test_facilities_archive --keepdb --noinput`.

Manual checks: open Services and confirm labels above all five filters. Add a service without saving and switch all categories; verify the section heading/fields and empty rate defaults. Configure a test analysis with an actual fee and charging basis. Configure a test assessment date and verify No Scheduled Appointment hides dates while optional office hours remain independent. Select stall/vendo lease types and compare inherited versus individual pricing. Save/Edit test records and verify images/settings remain. Change status and confirm its available menu actions, KPI counts, pricing and recent audit row. View service-specific requests, apply filters and paginate without losing service scope. Archive/Restore a test service and verify historical requests/payments still exist. Check a read-only account cannot save or change status.

### 8. Remaining limitations, debugging and safe practice

This updates catalog configuration and its existing request navigation; it does not implement a new laboratory execution, assessment registration, contract-generation, invoice, refund, recurring-billing or lease-renewal transaction engine. Assessment dates are catalog configuration, not capacity reservations or automatic client appointments. Configured utilities/term prices are not automatically charged to existing transactions. Saved request pricing history remains wherever the existing workflow already captured it; there is no invented retroactive price history.

No bulk live service rewrite or fake demo data was performed. Existing services acquire the new settings only when an authorized admin configures/saves them. Real service event auditing applies going forward; old updates cannot be reconstructed as new historical audit events. Physical devices, other browser engines and a complete application test suite were not tested.

Debugging: if Section 6 still prompts after selecting a valid category, verify the asset version, actual category value and `ServiceFormControls.sync`; do not compare visible labels to stored keys. If saved fields disappear, inspect the category, pricing choice and outgoing `workflow_config.service` before adding duplicate database columns. Weekly hours and actual assessment scheduling use different settings. If a status update shows Pricing not configured, inspect the saved `price_label` response/row restoration, not the payment totals. For a status error, inspect existing permission, archive state and validation response; do not hide errors by forcing the DOM state. An inactive/archived service is not a deleted service.

Safe practice: run `test_analysis_charging_basis_round_trips_and_invalid_basis_is_rejected` in the test database. Change its valid basis from sample to analysis and predict the saved value, then run the test and check the result. Next add a second disposable lease type with a different pricing basis and assert both survive an Edit without creating Booking/Room rows. Finally inspect the browser payload after changing to No Scheduled Appointment: assessment dates should be absent, but explicitly configured office hours may remain. This teaches progressive disclosure, shared server validation, JSON configuration and the separation of catalog settings from transactions without modifying production data.
