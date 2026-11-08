# CampusHub Bookings: reusable project context

## Discount eligibility safeguard, relevant notes and smaller cost typography - November 6, 2026

### 1. Cause / reason

The pasted task identified two confirmed defects in `complete_mobile_quote`: it granted discounts based solely on authenticated `user_type`, and attached a family-verification note whenever any special rule existed at the facility. The latter did not mean the customer had requested that discount. The user also requested smaller Estimated Total and cost-card text.

**Verification dependency remains unresolved:** inspection found no authoritative account-wide institutional-affiliation verification state in `CampusHubUser`, admin `User`, the account-management handlers, or Flutter's AuthUser/session models. Email verification confirms mailbox access; profile completion, typed IDs and declared account type do not confirm USTP affiliation. Existing protected staff reservation controls record verification evidence for an individual booking, not an account-wide verified status. Inferring global eligibility from those records or adding a new verification registry without its lifecycle, review permissions and revocation rules would exceed a minimal pricing fix. The task explicitly permits reporting this dependency instead of inventing eligibility.

### 2. Exact files changed / current anchors

| File | Line / code anchor | Change |
|---|---|---|
| `backend/core/modules/facilities/services/mobile_booking.py` | 230 `complete_mobile_quote`; 254 affiliation comment; 259 authenticated account type; 265 `discount_note`; 273 signed eligibility context | Remove account-type-only automatic discounts; reject mobile discount claims; return empty irrelevant note; bind signed quotes to current authenticated account type and unavailable verification source. |
| `backend/core/api/test_mobile_facility_booking.py` | 227 complete quote; 266 deposits; 297 account evidence matrix; 320 forged claims; 333 re-quote/history; 357 staff-verified scope | Update unverified quote expectations and add security, history, staff verification and scope coverage. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 152 Sound System fixture; 1585 slip fixture selections | Explicitly configure equipment requested by two older document fixtures, consistent with the earlier admin-selected requirements change. No runtime document code changed. |
| `campushub/lib/module_app/widgets/facilities/booking_review_summary.dart` | 25 `_heading`; 42 `_card`; 221 `_costRow`; 292 note visibility; 313 compact cost card | Smaller cost-only typography/spacing, right-aligned amounts and text-scale-aware stacked rows. Hide whitespace-only notes. |
| `campushub/test/booking_review_summary_test.dart` | 133 undiscounted quote; 162 server label/recorded note | Check no zero-discount row, blank-note hiding, smaller total and long server label/note at enlarged text. |
| This guide; `CAMPUSHUB_CONTEXT.md` | Leading entries | Explain behavior, missing verification dependency, tests and safe practice. |

### 3. Changes made

New mobile estimates are **undiscounted until an authoritative affiliation-verification mechanism exists**. This applies to declared Student/Faculty/Employee accounts as well as Guest/External/Admin; administrative privileges alone are not evidence. Nonempty mobile `discount_index` claims are rejected rather than accepted as verification. Request-supplied user type, client ID, approval flags, verification methods and reasons never become staff evidence. Configured Student/Internal/Immediate Family/Other rules remain saved and usable in the existing authorized staff verification path; no percentages, scopes or prices were changed. No special-discount application workflow was added.

`discount_note` remains API-compatible as an empty string on ordinary new mobile quotes. Active family/other rules no longer manufacture a pending request or a generic notice. The renderer hides empty/missing/whitespace notes, displays a discount row only for a positive server amount, and keeps a supplied label/relevant note unchanged. The selected fixture's discount row remains only a presentation test input; it is not evidence that automatic verified mobile discounts exist.

The cost card heading is 15px; row labels and server notes are 12px; ordinary amounts are 13px with medium weight; Estimated Total uses a 12px semibold label and 15px semibold amount (previously an 18px bold amount). Rows have tighter spacing. Normal layouts align values right with more space for labels; enlarged text stacks label and amount so long content can wrap. Other Review cards retain their existing typography. The cost breakdown remains visible, with no collapse control or new disclaimer.

### 4. How it works / functions, inputs, outputs and data flow

The existing bearer decoder in `api.views._mobile_user_from_bearer` resolves the actual account from the database on every request. `complete_mobile_quote(facility, day, start, end, data, user)` builds safe staff-engine inputs using that owner's ID, validated schedule, attendee count and fee quantities. It invokes the original `reservation_quote` without an asserted discount. No mobile evidence is copied into `discount_reason`, `verification_method` or eligibility. It then rejects an explicit discount selection and returns the existing quote amounts plus `discount_note: ''`.

The existing signature now includes the authenticated account type and a fixed `affiliation_verification: 'unavailable'` context alongside facility, owner, request, workflow and quote. The booking POST recomputes the quote/signature in the existing locked-facility transaction. Changed account type, pricing or an older discounted signature requires a new Review. Existing request fingerprint and exact saved-request retries remain; historical quote JSON is not recalculated. Staff verification remains per reservation, through its original permission-checked preview/create/edit architecture.

Flutter `_costRow(label, formattedAmount, total: ...)` is presentation only. `_cost` passes actual quote values and the server label into it; no rate, discount or total is computed in Dart. New optional `_card(..., compact: true)` changes only the cost card. The wizard controllers, navigation, quote request, submission key and payload remain intact.

Annotated isolated example: configured rental 3000 plus 500 additional hours and 20 chairs at saved test rate 10 produce an unverified mobile total of 3700, with `discount_amount: '0.00'` and no discount line/note. Through the existing authorized staff path, inspected Student/Faculty evidence can apply the configured 50% entire-rental discount: 1750 discount, 200 chair fee unchanged, total 1950. These are fixtures, not production pricing changes. A configured base-rate-only rule reduces 1500 instead; additional-hour-only reduces 250. No discount is stacked. Percentage deposits still follow the same engine and undiscounted/discounted rental basis as appropriate.

### 5. Backend / API behavior

No routes or payload schema changed. Ordinary new quotes retain all existing pricing fields and an empty `discount_note`; no irrelevant special-rule message appears. New mobile discount-index claims receive HTTP 400. The quote token changes because it now signs current eligibility context; old unsaved estimates must be reviewed again. Existing saved bookings, exact retry behavior and public/private quote filtering remain. Original configuration, chair amounts, deposits, scope calculations, RBAC, approval, Job Order, SOA and payment implementations are preserved.

### 6. Database / migration impact

None. No model, migration, new verification table, dependency, account permission, configured rate, live record or historical quote edits. Tests write only to disposable local PostgreSQL databases. No server/phone restart, build, install, deployment or Git push.

### 7. Tests performed

- Final Flutter command: `flutter test --no-pub test/booking_review_summary_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart --reporter expanded`: **23 tests passed in 45 seconds**. Covers blank/missing notes, zero-discount hiding, supplied discount labels, smaller total, long labels at 280px/200% text, Review/Back, quote amounts/token/quantities and retries.
- `flutter analyze --no-pub`: **No issues found**, 112.3 seconds. Formatting and scoped whitespace checks passed. Inspected the actual compact cost-card capture at `scratch/discount-review-20261106/quote-390.png`; its discounted amounts are an isolated supplied UI fixture.
- Final `backend/core/venv/Scripts/python.exe -B scratch/schedule-policy-20261105/run_tests.py api.test_mobile_facility_booking api.test_facility_rental_configuration modules.facilities.test_admin_reservations modules.facilities.test_booking_workflow`: **220 tests passed in 36.344 seconds**, system checks clean and disposable PostgreSQL database destroyed. Coverage includes unverified account types plus email/profile/ID/admin-role non-evidence, forged family/internal claims on quote and submission, account changes after Review, history and exact retry preservation, staff-verified Student/Faculty scope calculations, chair fees/deposits, rental configuration and existing document/payment/approval workflow cases.
- The first broad run exposed a new test comparing private saved data to the intentionally filtered public response, plus two older document fixtures requesting unconfigured equipment. The assertion and isolated fixtures were corrected; no public-data filtering or document behavior was weakened. The corrected history/staff-scope focused rerun passed **2 tests in 0.245s**.

### 8. Remaining limitations / troubleshooting / safe practice

**Verified automatic mobile discounts are not implemented:** no trusted institutional-affiliation verification source exists. Tests confirm the safe fallback and existing per-booking staff discounts; they do not claim verified Student/Faculty accounts automatically receive mobile discounts. A future integration needs staff-controlled verified affiliation, evidence/provenance, expiry/revocation and a protected way to maintain it. It must map verified Student to configured Student/Internal rules and verified Faculty/Employee to Internal, choose one applicable rule using the existing engine, and recheck evidence at submission. Family eligibility needs separately verified relationship evidence; a profile or dropdown cannot grant it.

No physical-device, live-API or full-app-suite verification. Existing eligible-client booking-access rules are unchanged; this fix targets discount eligibility only. Do not reuse a past booking's evidence as permanent account affiliation. Staff can continue using the original verified reservation workflow; the task did not authorize a new self-service discount application.

Safe practice: run `test_account_type_email_profile_or_admin_role_do_not_verify_discount_affiliation` and verify every declared type receives zero automatic discount even with email/profile flags set. Run `test_staff_verified_student_and_faculty_discounts_preserve_configured_scope` and compare its expected 1750/1500/250 reductions with the configured scope, leaving chair fees unchanged. In the widget fixture, supply zero `discount_amount` and an empty note, then a real supplied label/amount, and verify the corresponding row appears only in the latter case. Do not alter real rates or grant real account verification for a screenshot.

## Review Booking uses separate reference-style information cards - November 6, 2026

### 1. Cause / reason

The user supplied a Review layout with separate schedule, requestor, event, requirements/notes and estimated-cost cards, explicitly excluding the `1 pc` requirement wording, Subject to final verification disclaimer and expand/collapse interaction. The existing Review put facility imagery and all sections into one large Booking Summary card separated by dividers. This update changes that presentation, using the actual current form and Django quote values rather than copying example records or amounts from the images.

### 2. Exact files changed / current anchors

| File | Lines / anchors | Purpose |
|---|---|---|
| `campushub/lib/module_app/widgets/facilities/booking_review_summary.dart` | New: 8 `BookingReviewSummary`, 25 `_heading`, 42 `_card`, 62 `_stackedValue`, 82 `_schedule`, 135 `_requestor`, 148 `_event`, 159 `_requirementsAndNotes`, 220 `_cost`, 274 `build` | Dedicated read-only Review presentation, reusing BookingCard, BookingValue, shared icons, typography and money/date/time helpers. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | New widget import; 1748 `BookingReviewSummary(...)` | Replace the old monolithic Review markup with the presentation widget, passing existing date, time, draft, quote and facility terms. |
| `campushub/test/booking_review_summary_test.dart` | New: 74 responsive long-content cases; 119 empty optional-details case | Verify 390px/normal and 280px/200% text, long names/email/event data, supplied quote amounts, no unsupported quantity suffix/disclaimer/collapse and no empty optional card. |
| `campushub/test/facility_booking_flow_test.dart` | 226 card keys; 237 cost capture | Extend the existing form flow to verify the separate cards and omitted reference elements while retaining Review/Back/submission coverage. |
| `campushub/test/covered_court_booking_test.dart` | 230 updated fee labels; 241 Estimated Total capture; 419 fee lookup | Preserve the authoritative pricing/token/quantity checks with the new display labels. |
| This guide; `CAMPUSHUB_CONTEXT.md` | Leading entries | Record changes, data flow, evidence and safe practice. |

### 3. Changes made

Review now starts with Booking Schedule: date and weekday alongside duration and time range. The columns stack on narrow screens or enlarged text. Requestor Information stacks Full Name, optional Organization, Contact Number and Email Address, allowing long values to wrap. Event Information retains label/value rows for event, purpose and attendee count.

Additional Requirements and Additional Notes share a card when present, separated by a divider. Requirement rows show shared icons and saved item names, without `pc` quantities. The cost card remains fully visible and non-collapsible. It displays Base Rental Fee, applicable Additional Hours, server discount label/value, actual item fee quantities/amounts, applicable refundable deposit, existing server-provided notes and Estimated Total. Quantity-based cost rows use `Chairs × 20` rather than adding `20 pc` to the requirement list. Do not add a static Subject to final verification disclaimer or collapse arrow.

Remove the old overall Booking Summary heading, facility thumbnail/identity block and monolithic interior layout from this stage, following the supplied card sequence. Selected facility state and payload remain unchanged. Preserve optional Organization and Rules & Guidelines when saved, as well as actual Django discount/requirement notes; these are existing data, not the excluded generic disclaimer. Shared components remain available to other screens.

### 4. How it works / functions, inputs, outputs and data flow

`BookingReviewSummary` receives `date`, `start`, `end`, `details`, `quote` and optional `termsConditions`. It returns a Column of read-only cards; it has no controller, network client, expansion state or submission callback. The booking screen still owns `_fields`, `_requirements`, `_feeFields`, `_quote`, request key, quote refresh and submission lifecycle. `_bookingInputs` supplies the same draft mapping to both Review presentation and the existing booking request.

`_schedule` formats the selected date/time and uses the server's quoted hours. `_requestor` reads the entered contact fields; `_event` reads event/purpose/attendees. `_requirementsAndNotes` renders only selected saved requirement labels and actual notes, omitting the card when both are empty. `_cost` formats amounts already present in the quote; it does not recalculate rent, discounts, fees, deposit or total. `_card`, `_heading` and `_stackedValue` provide consistent layout using the existing shared styles.

Annotated isolated example: `details.additional_requirements = ['Chairs']`, quote fee `{name: 'Chairs', quantity: '20', amount: '200.00'}` -> requirement card shows **Chairs**, cost row shows **Chairs × 20 / PHP 200.00**. `quote.total_amount = '2450.00'` -> Estimated Total is PHP 2450.00 exactly. The fixture total includes its separately configured deposit; no production rate or total is seeded. Review Back still returns to the retained draft, and Submit still sends the original quoted amount/token and fee quantities.

### 5. Backend / API behavior

Unchanged. No endpoints, authorization, configuration, schedule/conflict checks, quote signatures, pricing calculations, booking submission, retry handling, approval, Job Order, SOA or payment behavior changed. The customer-visible total remains the actual Django quote. No example screenshot value is used as application data.

### 6. Database / migration impact

None. No schema, migrations, dependencies, configured rates, working records or deployment changes. New sample values exist only in isolated widget tests.

### 7. Tests performed

- `flutter test --no-pub test/booking_review_summary_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart --reporter expanded`: **21 tests passed in 13 seconds**. New display tests cover long content at 390px/normal and 280px/200% text, horizontal bounds and optional empty details. Existing integration tests retain quote/token/quantity totals, Review/Back input retention, final submission, uncertain retries, configured-only requirements and Chair editing/removal.
- `flutter analyze --no-pub`: **No issues found**, 11.8 seconds. Dart formatting and scoped tracked-file whitespace checks passed.
- Inspected actual captures at `scratch/review-cards-20261106/review-booking.png` and `quote-390.png`: separate top cards, requirement names without piece suffixes and a fully visible cost breakdown. Additional captures include `review-cost.png` and `quote-320.png`. These renders use test fixtures, not production records.
- No backend regression suite rerun for this presentation extraction; no backend code changed.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-phone, real screen-reader or full-app-suite verification. On narrow/enlarged-text screens, cards grow and Schedule stacks to keep text readable; the page intentionally scrolls. Quantity is still visible where it explains an actual priced cost line. Server-provided special-discount/requirements notes are retained. Optional Organization/Rules remain when entered/configured, even though omitted from the sample images.

Safely run the listed fixture suites. In a fixture draft, enter a long email and note, select Chairs, visit Review, check the card sequence and compare the displayed amounts with its supplied quote. Scroll to Estimated Total without expanding anything, return to Details and confirm the inputs remain. Set optional requirements/notes empty in the display fixture and verify no empty combined card appears. Restore fixture edits afterward. Do not change real facility fees or create live bookings for layout practice. For broken text-based tests, use the new card keys and labels (`review-cost`, `Estimated Total`, `Chairs × 20`) instead of removed Booking Summary / Total Amount wording.

## Remove the gray back-arrow container from Review Booking - November 6, 2026

1. **Cause / reason:** Review Booking still used the shared non-flat header, whose back chevron sat inside a light-gray rounded Material with a gray outline. The user requested removal of that gray line/container.
2. **Exact files changed / anchors:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:1253` (`flatAppBar`); `campushub/test/facility_booking_flow_test.dart:219` (Review header assertion and capture); this guide; `CAMPUSHUB_CONTEXT.md:3` (summary).
3. **Changes made:** Enable the existing plain header for the Review stage as well as Details. Review now uses the same plain navy chevron as the earlier wizard stages, removing its gray back-button fill/outline and the non-flat app-bar divider. Shared history/status headers, page content, booking cards and bottom actions remain as before.
4. **How it works / functions, inputs, outputs and data flow:** The booking screen passes `flatAppBar: _step == 1 || _step == 2` into `BookingScaffold`. Its existing `build` method selects the plain localized IconButton when that flag is true. The button still invokes `Navigator.maybePop`; the wizard's PopScope moves Review back to Details and preserves the existing controllers. Example: enter a note, advance to Review and tap the plain chevron; Details returns with the same note. No new navigation function, input, output or booking-data path was introduced; this reuses an existing presentation option.
5. **Backend / API behavior:** Unchanged. Quotes, pricing, submission, permissions, approvals and payments retain their existing behavior.
6. **Database / migration impact:** None. No schema, migration, dependency or working-record changes.
7. **Tests performed:** `flutter test --no-pub test/facility_booking_flow_test.dart test/covered_court_booking_test.dart --reporter expanded`: **18 tests passed in 13 seconds**. Existing form test asserts Review's leading control is an IconButton, taps it to verify retained values, then submits through the existing fixture service. `flutter analyze --no-pub`: **No issues found**, 14.0 seconds. Formatting/scoped whitespace checks passed. Inspected the actual Review header at `scratch/review-plain-back-20261106/review-booking.png`: plain chevron with no gray container/outline.
8. **Remaining limitations / safe practice:** No physical-phone or full-suite verification. Reload the updated Flutter code, use the isolated booking fixture to enter Details and reach Review, inspect the plain back chevron, tap it and verify input retention. Do not create live bookings to practice this styling change.

## Chevron back icons from Select Schedule through Review Booking - November 6, 2026

1. **Cause / reason:** The user requested removal of the straight horizontal line from the booking arrow. Select Schedule and Booking Details used Flutter's default BackButton, which displayed an arrow with a stem. Review Booking already used a chevron.
2. **Exact files changed / anchors:** `campushub/lib/module_app/widgets/facilities/booking_widgets.dart:272` (`BookingScaffold` flat-header leading IconButton); `campushub/test/facility_booking_flow_test.dart:118`, `:120`, `:219`, `:227` (icons across all three stages and actual Review back tap); `campushub/test/select_schedule_test.dart:1216` (existing responsive-header lookup), `:377` (braces around the formatted screenshot condition); this guide; `CAMPUSHUB_CONTEXT.md:3` (summary).
3. **Changes made:** Replace the flat-header default BackButton with an IconButton displaying `Icons.arrow_back_ios_new_rounded`, a simple chevron with no horizontal stem. Keep the existing leading width, navy color, title, header layouts and Review's existing chevron container. Other non-flat BookingScaffold headers are unchanged.
4. **How it works / functions, inputs, outputs and data flow:** `BookingScaffold.build(context)` already chooses its flat header when `schedulePresentation` or `flatAppBar` is true. Those flags are used by the current wizard's Schedule and Details stages. Its new IconButton uses the localized Back tooltip and the same `Navigator.of(context).maybePop()` route action. The existing wizard PopScope still returns from Review to Details and Details to Schedule, retaining controllers; Schedule still permits leaving the route. Example: enter notes, visit Review and tap the chevron; Details reappears with the same notes. No booking data or navigation state is stored by the icon itself. This changes the visible glyph while keeping the established navigation path.
5. **Backend / API behavior:** None changed. Quote/submission endpoints, permissions, availability, pricing and booking workflows remain intact.
6. **Database / migration impact:** None. No schema, migration, dependency or working-record changes.
7. **Tests performed:** `flutter test --no-pub test/facility_booking_flow_test.dart test/select_schedule_test.dart test/covered_court_booking_test.dart --reporter expanded`: **54 tests passed in 18 seconds**. The existing form test checks the chevron at Schedule, Details and Review and taps Review's header button, verifying retained inputs and later submission. Existing responsive calendar, schedule, quote and quantity cases passed. Final `flutter analyze --no-pub`: **No issues found**, 6.8 seconds. Formatting/scoped whitespace checks passed. Inspected the actual Details header capture at `scratch/booking-chevron-20261106/additional-notes.png`. Formatting exposed an existing unbraced screenshot condition; enclosed it in braces before the final clean analysis, without changing its behavior.
8. **Remaining limitations / safe practice:** No physical-phone or full-suite verification. Review retains its existing rounded back-button container; only the arrow's horizontal stem was targeted. Reload the updated Flutter code, open the fixture booking, advance Schedule -> Details -> Review, then tap the chevron to return. Verify entered values remain and use the initial Schedule chevron to leave the draft. Do not submit live bookings merely to practice an icon change.

## Chairs checkbox removes directly; card body edits quantity - November 6, 2026

1. **Cause / reason:** The user reported that tapping the checked box still opened the quantity modal. The box was a decorative Container inside the card's InkWell, so it had no separate action; the whole card routed to `_editChairs`.
2. **Exact files changed / anchors:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:3` (CustomSemanticsAction import), `:1096` (`toggleSelection`), `:1110` (remove/edit semantic actions), `:1186` (`booking-requirement-toggle-Chairs` tap target); `campushub/test/covered_court_booking_test.dart:307` (direct removal, re-selection and semantic action checks); this guide; `CAMPUSHUB_CONTEXT.md:3` (summary).
3. **Changes made:** Keep the existing checkbox appearance, colors and card dimensions. Add an independent 48x48 tap target over the supported Chairs checkbox. Tapping a checked box immediately removes Chairs; tapping an unchecked box opens the quantity popup. Tapping the rest of the card still edits quantity. The popup's Remove Chairs and Cancel actions remain. Other requirement cards and included-chair selection retain their existing behavior. The selected card's primary semantic action removes it, with a separate Edit chairs quantity custom action.
4. **How it works / functions, inputs, outputs and data flow:** `_requirementCard(label, icon)` still reads `_requirements` and its configured fee/controller. Its local `toggleSelection()` calls `_toggleRequirement(label)` when a priced Chair selection is checked; that existing function removes the requirement and resets its fee controller to `0`. Otherwise it calls `_tapRequirement(label)` to open the existing quantity editor or toggle an ordinary requirement. A Positioned InkWell sits above the card body in a Stack, so its taps do not also trigger the sibling card InkWell. The card body still calls `_tapRequirement` directly. The same original controllers flow through `_bookingInputs` -> Django quote -> Review -> submission.

   Annotated example: select 15 Chairs, then tap the top-right check. No modal opens; the selection clears and the next quote sends `fee_quantities: {'0': '0'}` with no Chairs requirement. Tap the empty box to open the quantity sheet at `1`; Cancel leaves it unselected. Tap the body of an already selected card to edit its confirmed quantity.
5. **Backend / API behavior:** Unchanged. No route, rate, quantity-validation, configured-option, payment, approval or permission changes. Existing Django pricing remains authoritative.
6. **Database / migration impact:** None. No models, migrations, dependencies or working-record changes.
7. **Tests performed:** Final `flutter test --no-pub test/covered_court_booking_test.dart test/facility_booking_flow_test.dart test/chairs_quantity_sheet_test.dart --reporter expanded`: **24 tests passed in 17 seconds**. Updated the existing removal regression to tap the actual 48x48 checkbox target, assert the sheet stays closed and the quote quantity becomes zero, reselect through the unchecked box, cancel, and exercise the selected semantic callback. Existing body-edit, quantity, popup Remove, configured choices and booking submission tests passed. Final `flutter analyze --no-pub`: **No issues found**, 17.1 seconds. Formatting/scoped whitespace checks passed. Actual selected-card render inspected at `scratch/chairs-checkbox-20261106/confirmed-chairs-card.png`. Initial compile check caught the missing semantics import; corrected before the successful final run.
8. **Remaining limitations / safe practice:** No physical-device, real screen-reader or full-suite verification. Separate priced-chair controls apply to the supported single valid Chair fee case; ordinary/included requirements retain their single toggle. Safely run the fixture suite, select a quantity, tap only the checkbox and verify no sheet appears; then tap the empty box, cancel and verify it stays empty. Reconfirm a quantity, tap the card label/summary and verify it opens for editing. Inspect the test quote for zero after removal. Do not create a live booking for practice. Reload the updated Flutter code before checking the behavior in an already-running app.

## Additional Notes label and placeholder cleanup - November 6, 2026

1. **Cause / reason:** The user requested removal of the duplicate Notes label below the Additional Notes heading and a clearer placeholder. The shared field helper always rendered a permanent field label and generated `Enter notes` from it.
2. **Exact files changed / anchors:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:897` (`showLabel` / `hintText` arguments), `:910` (placeholder override), `:996` (optional permanent label), `:1698` (Additional Notes section); `campushub/test/facility_booking_flow_test.dart:146` (existing form-flow assertions and capture), `:231` / `:242` (retained/submitted notes); this guide; `CAMPUSHUB_CONTEXT.md:3` (summary).
3. **Changes made:** Keep the Additional Notes heading, remove the repeated Notes label and its 8px gap, and replace the placeholder with **Add any details or instructions for your booking.** Keep the three-line white input, existing borders, typography, optional status and semantic name. Other field labels/placeholders retain their defaults.
4. **How it works / functions, inputs, outputs and data flow:** `_field(key, label, ...)` accepts optional `showLabel` (default `true`) and `hintText` (default generated from the label). The Notes call uses key `notes`, semantic label Additional Notes, `showLabel: false` and the new placeholder. The shared helper still returns the same controller-backed form field; its Semantics wrapper retains an accessible name even though the duplicate visual label is hidden. Input -> `_fields['notes']` -> `_bookingInputs['notes']` -> quote/review -> existing booking submission is unchanged. Example: entering `Please arrange the chairs before the event.` still sends that exact text under `notes`. Using optional helper arguments avoids copying the shared input styling for one field.
5. **Backend / API behavior:** None changed. Existing notes validation, payload, booking workflow and permissions remain.
6. **Database / migration impact:** None. No schema, migration, dependency or working-record changes.
7. **Tests performed:** `flutter test --no-pub test/facility_booking_flow_test.dart --reporter expanded`: **9 tests passed in 9 seconds**. Updated the existing form-flow case to check the absent duplicate label/new placeholder and verify entered notes survive Review/Back and reach submission. `flutter analyze --no-pub`: **No issues found**, 11.7 seconds. Dart formatting and scoped whitespace checks passed. Inspected the actual rendered empty field at `scratch/additional-notes-20261106/additional-notes.png`. No backend test rerun was needed for this label/placeholder change.
8. **Remaining limitations / safe practice:** No physical-phone, screen-reader or full-suite verification. Safely run the fixture suite, inspect the single heading/new placeholder, enter a short note, visit Review, return and verify the note remains. Inspect the fixture's submitted `notes` value. Other fields should keep their labels. Do not create live bookings to practice a presentation edit.

## Remove the duplicate inline Chairs quantity field - November 6, 2026

1. **Cause / reason:** The user's screenshot showed an extra inline Chairs quantity field and helper paragraphs below the requirement cards. The existing Chairs card already opens the quantity popup, so the supported single-fee case exposed the same value twice.
2. **Exact files changed / anchors:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:858` (`_feeQuantity` fallback), `:1684` (configured fee rendering); `campushub/test/covered_court_booking_test.dart:307` (Remove and zero payload), `:335` (card-only editing and submission); this guide; `CAMPUSHUB_CONTEXT.md:3` (summary).
3. **Changes made:** Skip the inline fee field when it is the same configured fee handled by `_chairRentalFee` and the popup. Remove its now-unused read-only/onTap/helper wording branches from `_feeQuantity`. Remove the pictured general configured-charge explanation and its spacing below the controls. Keep the requirement heading/cards and their confirmed quantity/charge summary. Other fee inputs and ambiguous/unpriced Chair configurations retain their existing fallback controls.
4. **How it works / functions, inputs, outputs and data flow:** The rendering loop compares each configured fee to `_chairRentalFee`; the supported Chair fee is omitted from the widget tree. Its `_feeFields` controller is retained as booking state. Tapping the Chairs card still invokes `_editChairs`, which opens `showChairsQuantitySheet` with the current quantity and Django rate. Confirm writes the result into that same controller; Cancel leaves it untouched; Remove writes `0` and clears the selected requirement. `_bookingInputs` still reads the controller into `fee_quantities` for quote/review/submission. This removes duplicate presentation without deleting the stored quantity path.

   Annotated fixture example: confirm 20 chairs at the isolated rate 12.35; the card shows `20 chairs` and PHP 247.00, and the request still sends `fee_quantities: {'0': '20'}`. Removing Chairs changes that payload to `{'0': '0'}`. No inline field is needed to submit either value.
5. **Backend / API behavior:** Unchanged. Existing Django configured-choice, quantity, rate and quote validation remain authoritative. No approval, Job Order, SOA, payment, permission or endpoint changes.
6. **Database / migration impact:** None. No schema, migration, dependency, configured-rate or working-record changes.
7. **Tests performed:** `flutter test --no-pub test/covered_court_booking_test.dart test/facility_booking_flow_test.dart test/chairs_quantity_sheet_test.dart --reporter expanded`: **24 tests passed in 16 seconds**. Existing tests now assert the duplicate field/helper text are absent, verify card/popup state, Cancel/Back, Remove, and quote/final submission quantities. `flutter analyze --no-pub`: **No issues found**, 17.9 seconds. Dart formatting and scoped whitespace checks passed. Inspected the actual card-only render at `scratch/chairs-card-only-20261106/confirmed-chairs-card.png`. Backend tests were not rerun for this presentation-only removal.
8. **Remaining limitations / safe practice:** No physical-phone or full-suite verification. Unsupported/ambiguous fee configurations retain the previous quantity field so a required input is not hidden without a working popup. To practice safely, run the fixture suites, tap the Chairs card, confirm 20, reopen and Cancel a different draft, then remove it. Verify the card summary and outgoing quantity; confirm the extra field and explanation are absent. Do not submit live bookings or change actual rates for this exercise.

## Additional Requirements follow the admin's saved selections - November 6, 2026

### 1. Cause / reason

Confirmed two independent fixed lists: Flutter `_requirementChoices` always offered Chairs, Tables, Sound System, Projector and Others, while Django `_details` accepted only those names. The actual physical-facility admin heading is Additional Requirements, stored in the existing `Facility.amenities` list. The admin's Other entry is resolved into its actual custom label by `validate_features`; it is not an instruction to add a universal Others card. As a result, unchecked choices appeared on mobile and configured items such as Microphone, Stage and Extension Cords could not be submitted. New regression cases reproduced the missing fresh-options response and acceptance of unconfigured quote choices before the fix.

### 2. Exact files changed / current anchors

| File | Line / nearby anchor | Change |
|---|---|---|
| `backend/core/modules/facilities/services/feature_configuration.py` | 16 `booking_requirement_options`; 22 `validate_booking_requirements` | Read valid saved labels and validate this facility's selected request values. |
| `backend/core/modules/facilities/services/mobile_booking.py` | 222 `mobile_pricing_options`; 242 `requirements = validate_booking_requirements` | Return fresh choices through the existing quote response; enforce them for full quotes and new submissions. |
| `backend/core/modules/facilities/mobile_views.py` | 175 `Basic shape is checked` | Replace the universal allowlist with input-shape validation; configured-choice checks remain in the quote engine after existing-request retry lookup. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 49 `_requirementOptions`; 73 initialization; 750 `_cleanRequirementOptions`; 757 `_loadPricingOptions`; 802 `_chairRentalFee`; 1167 `_requirementChoices`; 1687 fee rendering | Build cards from saved/fresh labels, clear removed draft choices, suppress an unconfigured Chair editor, reuse shared amenity icons and show an honest empty state. Remove unused Lucide import. |
| `backend/core/api/test_mobile_facility_booking.py` | 61 admin-to-mobile custom-label round trip; 90 unconfigured-choice rejection; 103 removal/retry test | Test actual authorized admin update, catalog, fresh options, quote, submission, removal and exact retry preservation. Update fixtures and the old exact response assertion for the additive API field. |
| `campushub/test/fixtures/facility_booking_fixture.dart` | 11 `testFacilityWithRequirements` | Reuse explicit isolated configuration without changing the shared fixture's original default labels. |
| `campushub/test/facility_booking_flow_test.dart` | 17 configured fixture; 248 selected/custom choices; 290 empty state | Test explicit fixture choices, no unselected defaults, custom requirement submission, selection retention and existing responsive cards. |
| `campushub/test/covered_court_booking_test.dart` | 25 `requirementOptions`; 433 fresh-choice regression | Exercise fresh server options overriding a stale facility object and clearing a removed Chair quantity. |
| This guide; `CAMPUSHUB_CONTEXT.md` | New leading entries | Record cause, data flow, verification and recovery steps. |

### 3. Changes made

Mobile now displays exactly the configured label list, keeping its order and custom names while trimming/deduplicating labels. It no longer invents the five default choices or adds Others automatically. An empty list displays **No additional requirements are configured for this facility.** The existing card layout, white/navy colors, check states and shared icon mapping remain. The configured Chairs choice still opens the existing quantity popup when a single valid Chair fee exists; included chairs still use ordinary selection. If refreshed choices remove Chairs, its old fee draft becomes `0` and its quantity editor is hidden. Other fee calculations were not rewritten.

### 4. How it works / functions, inputs, outputs and data flow

`booking_requirement_options(facility)` reads `facility.amenities`, retains valid plain labels up to the existing 200-character limit, and returns an ordered unique list. `validate_booking_requirements(facility, requirements)` takes a submitted list, checks exact membership in those options and returns unique selected values; otherwise it raises a Django validation error. It does not create charges or modify facility configuration.

The original admin save path remains `amenities` plus `workflow_config.other_feature` -> `validate_features` -> saved `Facility.amenities`. The existing Schedule availability-only quote now returns `pricing_options.requirement_options`, next to the unchanged `item_fees`. Flutter initially reads `widget.facility.amenities`, then `_loadPricingOptions` replaces that draft option list with the fresh response before showing Details. `_requirementChoices` maps each saved label to a card and shared `iconForAmenity` result; `_requirements` still holds the customer's selections. `_bookingInputs` at line 741 sends those selections and existing `fee_quantities` -> full Django quote -> Review -> existing booking POST.

Annotated example: admin checks **Stage** and **Microphone**, selects **Other**, and enters **Extension Cords**. Saved `amenities` and mobile options become `['Stage', 'Microphone', 'Extension Cords']`. Selecting Extension Cords sends `additional_requirements: ['Extension Cords']`. It does not send an Others marker or assume a rental fee. If Projector is not configured, no Projector card appears and a forged Projector selection receives HTTP 400.

`_details` validates text/list shape before computing the submission fingerprint. New submissions then validate current configured choices inside the locked facility quote path. Already-saved exact retries return the existing booking first, even when the admin has since removed an option; this preserves idempotency and historical requests. Saved requests are not rewritten by current configuration changes. This shared server source was chosen over maintaining another category-based or hardcoded mobile item registry.

### 5. Backend / API behavior

Additive response field: `pricing_options.requirement_options` on the existing availability-only and complete quote responses. Full quotes and new booking submissions now reject unconfigured/removed labels. The routes, bearer authentication, permissions, schedule/conflict checks, rate/discount/quantity calculation, pricing signature, request keys, approval, Job Order, SOA and payment flows remain. The existing `requirements` prose field is not parsed into selectable equipment; it remains separate from the admin checkbox list. Older clients that send unsupported hardcoded choices now receive a validation error and should use the updated app.

### 6. Database / migration impact

None. Reuse `Facility.amenities`, existing workflow JSON and existing booking request details; no schema, migrations, dependency, seeding, working-record, price or permission changes. Tests create and destroy a disposable local PostgreSQL database. No live server or phone was restarted or installed.

### 7. Tests performed

- Before the fix, two new backend regression tests failed: missing requirement options and unconfigured choices accepted by full quotes.
- Final `backend/core/venv/Scripts/python.exe -B scratch/schedule-policy-20261105/run_tests.py api.test_mobile_facility_booking api.test_facility_rental_configuration`: **103 tests passed in 11.581 seconds**, system checks clean, disposable PostgreSQL database destroyed. Includes actual Facilities Admin update through its authorized endpoint, custom-label quote/submission persistence, unchecked/empty-list rejection, post-review removal, exact retry preservation, current pricing and existing rental configuration tests.
- Final `flutter test --no-pub test/facility_booking_flow_test.dart test/covered_court_booking_test.dart test/chairs_quantity_sheet_test.dart test/select_schedule_test.dart --reporter expanded`: **60 tests passed in 33 seconds**. Includes configured-only/empty/custom cards, removed Chair quantity clearing, current popup behavior, quote/submission mapping, and existing schedule/large-text cases.
- `flutter analyze --no-pub`: **No issues found**, 23.2 seconds. Dart formatting and scoped root/nested Git whitespace checks passed. Inspected the actual render at `scratch/requirements-admin-selection-20261106/requirements-selected.png` with selected custom Extension Cords.
- Initial reruns exposed an obsolete exact JSON assertion, two new tests tapping before scroll animations settled, an unused import and one incorrect optional test-module label. Corrected those before the final successful runs; no failed run is counted as a passing suite.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-phone, screen-reader, full-app suite or deployment verification. Fresh choices load on the existing Schedule-to-Details validation, not as live pushed checkbox changes while a form is open. If an admin changes choices after Review, a new submission rejects unsupported selections; go Back to Select Schedule, then Next to Booking Details to reload the current choices. Existing requestor fields remain. A missing options field from an older server falls back to the facility object's actual saved amenities, never to the former five-item list. All configured labels remain displayable, including fixed features that the admin chose under the current Additional Requirements heading; no hidden category-based filtering is invented.

For a safe exercise, run the isolated admin round-trip test at line 61. Change only its custom fixture label from Extension Cords to another plain label and update its corresponding expectation; rerun, then restore the fixture. In the Flutter fixtures, configure only Microphone and Stage, confirm that Chairs/Projector/Others are absent, select an item and verify its exact label persists into the submitted request. Configure an empty list and verify the empty state. Do not alter production facility settings or create live bookings for practice. If choices disagree, inspect the facility's saved `amenities` and fresh `pricing_options.requirement_options`; do not copy the entire global admin choices registry into the customer form.

## Compact Chairs Quantity layout and Request Booking button size - November 6, 2026

This refinement supersedes the larger popup presentation described in the preceding implementation history below.

1. **Cause / reason:** The user supplied a compact popup reference and requested its layout with existing CampusHub colors and the Request Booking button size. The earlier sheet had a description, steppers, separate pricing paragraphs and 48px actions.
2. **Exact files changed / anchors:** `campushub/lib/module_app/widgets/facilities/chairs_quantity_sheet.dart:100` (`_actions`), `:148` (`build`), `:173` (quantity input), `:227` (Estimated chair charge); `campushub/test/chairs_quantity_sheet_test.dart:128` (compact layout and button checks), `:169` (invalid-input checks); `campushub/test/covered_court_booking_test.dart:353` (charge text lookup); this guide; `CAMPUSHUB_CONTEXT.md:3` (summary). Existing unrelated work was preserved.
3. **Changes made:** Use a compact title, one left-aligned rounded numeric input, an estimated-charge row and equal-width Cancel/Confirm actions. Remove steppers, drag-handle decoration and extra explanatory paragraphs. Both buttons copy the existing Request Booking dimensions/style at `facility_details_screen.dart:1227`: 52px minimum height, 12px horizontal/vertical padding, StadiumBorder and 14px semibold text. Keep white surfaces, navy text/Cancel outline and existing gold Confirm (`#FCB316`). Remove Chairs remains for a previously confirmed selection. Narrow enlarged-text layouts stack actions and wrap the charge.
4. **How it works / functions, inputs, outputs and data flow:** `showChairsQuantitySheet(context, currentQuantity, unitCentavos, maxQuantity)` still returns a confirmed integer, `0` for Remove, or `null` for cancellation. The controller holds a draft. `_valid` at line 86 validates a whole number within the supplied maximum; `_close` at line 89 dismisses focus and returns the result. `_actions` uses those same callbacks; `build` renders the compact field and `chairMoney(quantity * unitCentavos)` estimate. The existing booking screen `_editChairs` copies only a confirmed result into the original fee controller/requirements; `_bookingInputs` sends `fee_quantities` through Django quote and submission. Controller disposal remains at line 95. Reusing this path avoids a second quantity state or price authority.

   Annotated fixture example: rate `1235` centavos and quantity `2` display PHP 24.70. Cancel returns `null`, retaining the old quantity. Confirm returns `2`, and existing fee index `0` sends `fee_quantities: {'0': '2'}`. No estimated amount becomes an authoritative submitted price.
5. **Backend / API behavior:** Unchanged. Django supplies the saved rate and validates/calculates the actual quote. Other requirements, Function Hall included-chair selection, permissions, approval, Job Order, SOA and payments are unchanged.
6. **Database / migration impact:** None. No schema, migration, dependency, saved-rate or working-record changes. Capture prices come from isolated fixtures.
7. **Tests performed:** `flutter test --no-pub test/chairs_quantity_sheet_test.dart test/covered_court_booking_test.dart test/facility_booking_flow_test.dart --reporter expanded`: **21 tests passed in 17 seconds**. Tests cover default/edit/invalid/overflow values, cancellation/Back/barrier/Remove, booking payloads, Function Hall without a separate fee, and keyboard/narrow enlarged-text layouts. The updated layout check measures both actions at 52px and checks the retained gold color. `flutter analyze --no-pub`: **No issues found**, 18.6 seconds. Formatting and scoped whitespace checks passed. Actual renders inspected: `scratch/chairs-compact-20261106/chairs-compact-default.png` and `chairs-280.0-2.0.png`.
8. **Remaining limitations / troubleshooting / safe practice:** No physical-phone, live-booking, full-suite or screen-reader verification. Quantity still uses the existing maximum 100000, not an inventory guarantee. The narrow capture is scrolled to Confirm, so part of the heading is above the viewport; its keyboard uses simulated insets. Safely rerun the listed fixture tests, enter `2`, inspect the estimate, Cancel/reopen and verify the prior value remains; then Confirm and inspect the existing quote quantity. Enter `0` or `100001` and verify Confirm disables. Do not modify live fees or create a real booking for practice. For test lookup failures after this copy change, use `chairs-quantity-subtotal` for the amount and the new Estimated chair charge label.

## Chair quantity bottom sheet adapted to the current local source - November 6, 2026

1. **Cause / reason:** The user supplied a ChatGPT task/example and warned that it might not match their unpushed code. Inspected the actual local Flutter form and Django pricing contract instead of replacing the form with the snippet or pulling GitHub. The current form already owns `_feeFields`, `_itemFees`, `_requirements` and the correct `fee_quantities` mapping. Previously tapping Chairs merely toggled the requirement and required a separate quantity edit.
2. **Exact files changed:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:777` (`_chairRentalFee`), `:785` (`_editChairs`), `:824` (`_tapRequirement`), `:837` (existing quantity-field entry), `:1058` / `:1119` (card estimate); new `campushub/lib/module_app/widgets/facilities/chairs_quantity_sheet.dart:7` (existing limit), `:24` / `:37` (rate parsing/centavo display), `:40` (modal launcher), `:63` / `:99` (state/controller lifecycle), `:104` (responsive actions), `:155` (sheet layout); `campushub/test/covered_court_booking_test.dart:135`, `:304`, `:335`, `:403`; new `campushub/test/chairs_quantity_sheet_test.dart:105`, `:131`, `:163`, `:210`, `:252`; this guide. Other local changes and all migration files were preserved.
3. **Changes made:** For one valid separately configured Chair item fee, the card displays the saved rate and opens a white bottom sheet with Montserrat, navy `#1A1851`, gold `#FCB316`, minus/plus, editable quantity, saved rate, estimated subtotal, Cancel and Confirm. A new choice defaults to `1`; existing choices reopen at the confirmed value. Confirm updates the original controller/selection; Remove Chairs writes `0` and unchecks Chairs. Cancel, barrier dismissal and Android Back do not commit the draft. The white selected card displays confirmed quantity and estimated charge. Preserve the existing Chairs quantity field/controller/key; it is read-only for this supported case and tapping it opens the same editor. Its validator and payload mapping remain in place. Other requirement and fee controls retain their behavior. No document notice was reintroduced.
4. **How it works / functions, inputs, outputs and data flow:** Existing Django availability-only quote response -> `_loadPricingOptions` -> `_itemFees` / indexed `_feeFields` -> `_chairRentalFee`. That getter accepts exactly one recognized Chair fee with a valid saved rate. `_tapRequirement` routes only that Chair interaction to `_editChairs`; all other cases use the existing toggle. `_editChairs` passes current quantity and unit centavos to `showChairsQuantitySheet`, which returns an integer on Confirm/Remove or `null` on cancellation. A stateful `ChairsQuantitySheet` owns its temporary controller through the modal closing animation and disposes it in `State.dispose`; the unsafe example pattern of disposing an external controller immediately after awaiting the route is not used. `_editChairs` rejects a commit if the field/rate changed or the form left Details while the sheet was open.

   `chairUnitCentavos` validates finite, non-negative saved prices with the existing two-decimal/max-amount contract; missing or malformed prices do not become a fabricated zero. `chairMoney` displays integer centavos, keeping quantity multiplication exact within the existing limits. The subtotal is labeled an estimate. The original controllers -> `_bookingInputs['fee_quantities']` -> Django quote -> Review -> original booking submission remain the only processing path; the mobile app never sends an arbitrary Chair rate or subtotal.

   Annotated isolated example: saved test rate `12.35` -> `1235` centavos; confirmed `20` chairs -> estimated `247.00`; original fee index `0` still sends `{'0': '20'}`. This is test data, not a configured production rate. The attendees field remains independent and can contain a different number.
5. **Backend / API behavior:** No backend code or API contract changed. Read `mobile_booking.mobile_pricing_options` for active item/unit fee indices, names and saved rates; `complete_mobile_quote` and `admin_reservations.whole_number` remain authoritative for request validation. Final fees still come from Django's saved configuration and quote token. The implementation does not hardcode the policy's Chair rate, add charges to included Function Hall chairs, change approval, Job Order, SOA or payment handling, or move business logic into FastAPI.
6. **Database / migration impact:** None. No migrations, inventory, prices, permissions, dependency or working-record changes. No Git pull, commit or push was performed.
7. **Tests performed:** Final `flutter test test/chairs_quantity_sheet_test.dart test/covered_court_booking_test.dart test/facility_booking_flow_test.dart test/select_schedule_test.dart --reporter expanded`: **57 tests passed in 19 seconds**. Final `flutter analyze --no-pub`: **No issues found**, 17.9 seconds. Refreshed the confirmed-card capture with the existing Lucide test font, rerunning its single integration case: **1 passed in 3 seconds** (a repeat, not an additional distinct case). Formatting/scoped whitespace checks passed. Verified default quantity, steppers/bounds, invalid/zero/negative/fractional/overflowing input, Confirm, edits, Cancel, Back/barrier dismissal, Remove, route/controller closing lifecycle, keyboard Done, 280px/200% text with keyboard insets, navigation safe area, original quote/submission quantities and request keys, and Function Hall without a separate Chair fee. Initial standalone test failures were incorrect Tooltip/Scrollable finders; corrected before the successful final run. Actual sheet and confirmed-card captures in `scratch/chairs-quantity-20261106/` were inspected. Visual review led to stacked buttons for narrow enlarged text and explicit Montserrat variable weights.
8. **Remaining limitations / troubleshooting and safe practice:** The current pricing API does not expose per-facility Chair stock or a lower configured quantity cap; the popup uses the existing mobile/Django maximum of **100000**, not a claim that this many chairs are available. Final availability/acceptance remains with Django/office processing. No physical-phone, live-server or full-suite verification. Missing, malformed or multiple Chair fee mappings retain the previous controls instead of guessing a rate/index; included chairs keep ordinary selection. If the popup does not open, inspect the actual `pricing_options.item_fees` response and the existing aliases `chair`, `chairs`, `chair rental`, without editing working prices. In isolated fixtures, confirm 20 chairs, reopen and edit to 99 then Cancel/Back, verify 20 remains, remove and verify quantity `0`, then inspect quote/submission `fee_quantities`. Exercise another rate to prove no fixed price was introduced. Use `CHAIRS_REVIEW_DIR` with the widget suites for actual rendered captures; do not change production inventory or submit live bookings for this exercise.

## Remove the remaining Job Order description from the booking form - November 6, 2026

1. **Cause / reason:** After removing the notice heading and service label, the user also requested removal of its description paragraph.
2. **Exact files changed:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:1099` (build now follows the requirements helpers directly), `:1585` (Details ends with Additional Notes), `:1803` (Review ends with applicable Rules & Guidelines); `campushub/test/facility_booking_flow_test.dart:111`, `:140`, `:189`, `:296` (assert the notice and text are absent); this guide.
3. **Changes made:** Delete the unused `_jobOrderRequest()` presentation helper and both its Details/Review calls. This removes the paragraph, its white card and its bottom padding without leaving an empty section. Keep the white requirement selection cards and all other form sections.
4. **How it works / data flow:** The existing build method simply renders the remaining form/review children. No replacement helper, input or output is introduced. Controllers and `_requirements` still feed `_details()` -> Django quote -> Review -> existing booking submission. Example: a selected Tables card still sends the same requirement while no document explanation appears below Notes.
5. **Backend / API behavior:** None changed. Actual post-approval Job Order generation, document access, booking validation, prices, category mapping and submission request keys remain unchanged.
6. **Database / migration impact:** None. No schema, migration, dependency or working-record changes.
7. **Tests performed:** `flutter test test/facility_booking_flow_test.dart test/covered_court_booking_test.dart --reporter expanded`: **13 tests passed in 14 seconds**. `flutter analyze --no-pub`: **No issues found**, 19.3 seconds. Formatting and scoped whitespace checks passed. No new visual capture or physical-phone verification was run for this removal.
8. **Remaining limitations / safe practice:** Targeted tests only, not a full-suite claim. Use the isolated booking fixtures to open Details, scroll past Notes and proceed to Review; verify the paragraph/card are absent and the existing action bar still advances/submits. Check selected requirements survive Back/Review. Do not create a live booking or modify actual document records to test a UI removal.

## White selected requirement cards and simplified document notice - November 6, 2026

1. **Cause / reason:** The user requested white requirement cards even when selected, and removal of the visible Job Order Request / Facility Rental labels. The previous selected Material used `bookingGoldBg`; the bottom notice contained both a section title and configured service-label row.
2. **Exact files changed:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:1004` (`_requirementCard` surface), `:1098` (`_jobOrderRequest` notice); `campushub/test/facility_booking_flow_test.dart:111` (notice position/hidden labels), `:262` (selected white surface), `:295` (missing-mapping case); this guide. Other pending work was preserved.
3. **Changes made:** Always use a white Material for the five requirement cards. Retain the navy selected border, filled checkbox/checkmark, icons and whole-card tap target. Remove the Job Order Request heading and service-label/icon row from the notice on Booking Details and Review, including the unknown-service display fallback. Keep the existing explanatory paragraph and bottom spacing in its white BookingCard. No blank heading space remains.
4. **How it works / data flow:** `_requirementCard(label, icon)` still derives its checked state from `_requirements`; `_toggleRequirement` still updates that set and clears configured Chair quantities when appropriate. Only the surface color changed. `_jobOrderRequest()` now returns a constant padded BookingCard with the same explanation and a stable `booking-job-order-notice` key. It no longer reads `facility.jobOrderService` for display; that model field and server mapping remain intact. Existing request controllers/requirements -> `_details()` -> Django quote/review/submission are unchanged. Example: choosing Tables shows a navy check on white while submitting the same `Tables` requirement value as before.
5. **Backend / API behavior:** None changed. Existing booking validation, pricing, request keys, category workflows and actual post-approval Job Order generation remain unchanged. Hiding these labels does not delete a document or change its service category.
6. **Database / migration impact:** None. No model, migration, permission, dependency, rate or working-record edits.
7. **Tests performed:** `flutter test test/facility_booking_flow_test.dart test/covered_court_booking_test.dart --reporter expanded`: **13 tests passed in 17 seconds**. `flutter analyze --no-pub`: **No issues found**, 21.4 seconds. Formatting and scoped whitespace checks passed. Tests verify selected surfaces stay white, checked states still toggle at normal/enlarged text, the two labels are absent in Details/Review, the notice remains below Notes, selections survive review/back/submission and configured Chair quantities clear on deselection. Inspected the actual selected-state capture at `scratch/white-requirements-20261106/requirements-selected.png`.
8. **Remaining limitations / safe practice:** No physical-phone or full-suite verification. The explanatory paragraph still mentions Job Order processing; only the requested heading and service-label row were removed. To practice safely, select Tables/Others in the fixture, check the white background and navy checks, scroll below Notes to confirm the paragraph remains without the labels, and review/back to confirm selections persist. If a notice-position test needs a finder, use `booking-job-order-notice` rather than the removed title. Do not create live bookings or modify real document metadata to test this presentation change.

## Event Information and selectable requirement cards - November 6, 2026

1. **Cause / reason:** The user requested the same Add Product-style fields for Event Information and supplied a reference showing five outlined requirement cards. The existing form used floating event labels and a vertical CheckboxListTile list.
2. **Exact files changed:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:3` (existing Lucide package import), `:825` (preserve the attendee unit in styled fields), `:918` (`_informationCard`), `:969` (`_eventInformation`), `:982` (`_toggleRequirement`), `:995` (`_requirementCard`), `:1057` (`_requirementChoices`), `:1598` / `:1609` (form placement), `:1615` / `:1633` (Other details / Notes styling); `campushub/test/facility_booking_flow_test.dart:107`, `:236`; `campushub/test/covered_court_booking_test.dart:277`; `campushub/test/select_schedule_test.dart:613`; this guide. Unrelated pending work was preserved.
3. **Changes made:** Reuse one `_informationCard` helper for Requestor and Event Information, with a white surface, icon, wrapping title and permanent labels above rounded fields. Event name, purpose and attendee count use the same existing product-field typography/border/focus/error style as Requestor; attendee count retains the `persons` suffix. Other details and Additional Notes use that field style too. Replace the five checkbox rows with white rounded cards: navy icon at upper left, checkbox indicator at upper right, label below. Selected cards show a navy check/border and pale gold surface. Keep the existing choices, configured fee controls, quote guidance and bottom Job Order notice.
4. **How it works / functions and data flow:** `_informationCard(title, icon, fields)` returns presentation only. `_eventInformation()` supplies the same three controller-backed fields and their existing required/capacity validation. `_requirementChoices()` reads available width and text scale, then lays out two columns when each card has sufficient width; narrow or enlarged text falls back to one column. Rows grow with their labels. `_requirementCard(label, icon)` reads `_requirements`, paints the current state and exposes a checked semantic action; tapping the entire card calls `_toggleRequirement(label)`. That extracted callback retains the former checkbox behavior, including resetting configured Chair fee quantities to `0` on deselection. Entering a positive Chair quantity still selects Chairs through the unchanged `_feeQuantity` callback. Existing controllers and `_requirements` -> `_details()` -> Django quote -> Review -> existing submission remain the data path.

   Example: selecting **Others** reveals the existing `other_requirements` controller; its conditional validation still requires a description. Selecting **Tables** alone adds `Tables` to the existing request list and does not invent a price. Returning from Review retains both selections and entered text. The visual helper was chosen to share the current field design without changing backend contracts.
5. **Backend / API behavior:** None changed. Django still validates eligibility, capacity, schedules and prices. No API route, payment, Job Order approval, messaging or category-workflow changes. The displayed requirements retain their existing request meanings; a card is not proof that equipment is in stock or a new charge is due.
6. **Database / migration impact:** None. No model, migration, dependency, rate or working-record changes. Lucide was already installed.
7. **Tests performed:** `flutter test test/facility_booking_flow_test.dart test/covered_court_booking_test.dart test/select_schedule_test.dart --reporter expanded`: **49 tests passed in 25 seconds**. Final `flutter analyze --no-pub`: **No issues found**, 8.8 seconds. Checked formatting on the changed form/flow/Court files and scoped whitespace across all changed files. The schedule test received only its stable-key field lookup, preserving its existing formatting. An initial run exposed an old floating-label lookup in that test; it was corrected. Tests cover all five card toggles at 390px/normal and 320px/200% text, selected state, retained selections/write-in through review/back/submission, actual quote quantities and resetting Chair quantity on deselection. Actual Event, selected/unselected requirements and large-text captures were inspected in `scratch/event-requirements-20261106/`. Visual review led to a one-column fallback at enlarged text to avoid splitting Projector across awkward lines.
8. **Remaining limitations / debugging and safe practice:** No physical-device, full-suite or screen-reader verification; no measured accessibility-score claim. Single-column layout intentionally takes more scrolling at large text sizes. To practice safely, run the fixture suites, tap Tables and Others, enter a test description, review and return; confirm checked states and text remain. In the isolated Court fixture, enter a Chair quantity, deselect Chairs and verify the next quote sends quantity `0`. If a field test cannot find a permanent label as `labelText`, use its `booking-field-<key>` finder (for example, `booking-field-full_name`) and its descendant TextField. If a card seems clipped, first inspect text scale and available width rather than adding a fixed card height. Do not submit live reservations or modify actual fees for this exercise.

## Requestor fields match Add Product; Job Order notice moved to the bottom - November 6, 2026

1. **Cause / reason:** The booking form used floating field labels while Add Product uses permanent labels above white outlined fields. The Job Order explanation preceded the actual booking information. The user requested the Add Product field design for Requestor Information and the Job Order section at the bottom.
2. **Exact files changed:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:10` (shared field-label/style import), `:804` (`_field`), `:915` (`_requestorInformation`), `:1459` (requestor section placement), `:1539` and `:1757` (Job Order placement); `campushub/test/facility_booking_flow_test.dart:18`, `:104` (capture, validation, ordering and submission checks); `campushub/test/covered_court_booking_test.dart:174` (field lookup); this guide. Dashboard/Profile and three header tests also changed for the associated all-tab background request; see [the navigation guide](mobile-services-navigation.md).
3. **Changes made:** Place the four requestor fields in a white BookingCard with a person icon and wrapping section title. Reuse `ProductFieldLabel`, `ProductFormStyle` border/radius/error values and `AppTypography` from the existing Add Product UI. Show permanent labels, real required markers, white outlined inputs, 14/15px inner padding and a navy focus outline. Organization remains optional. Event, fee, notes and requirement controls keep their existing appearance. Move the unchanged `_jobOrderRequest()` notice below Additional Notes on Booking Details and below summary/rules on Review, above the existing fixed action bar.
4. **How it works / functions and data flow:** `_requestorInformation()` returns the card and calls `_field(..., productStyle: true)` for name, organization, phone and email. `_field` receives the same field key, label, required flag, keyboard type and controller; its new optional flag selects decoration/label layout only. Its existing validator returns the same required/email/capacity messages. Controllers still feed `_details()` -> existing Django quote -> Review -> existing idempotent submission. `_jobOrderRequest()` still reads the configured service label and explains post-approval draft preparation; moving it creates no Job Order or signature.

   ```dart
   // Same stored organization value; optional input with the Add Product appearance.
   _field('organization', 'Organization / Office',
       required: false, productStyle: true);
   ```

   This approach reuses the actual label/style primitives while preserving the booking navy, existing form controllers and business rules. Test lookups now recognize permanent-label fields by their hints; stable `booking-field-<key>` keys also identify the inputs.
5. **Backend / API behavior:** None changed. Request payloads, quote authority, booking eligibility, conflict checks, request keys, pricing, approval and existing post-approval Job Order handling remain unchanged. No new endpoint or online form workflow.
6. **Database / migration impact:** None. No model, migration, permission, rate, account or working-record edits. Add Product implementation and its persisted data were not changed.
7. **Tests performed:** Shared final six-file run listed in the navigation guide: **57 tests passed in 30 seconds**; `flutter analyze --no-pub`: **No issues found**, 14.6 seconds. Relevant cases cover requestor validation, retained input, review/back navigation, single submission, actual quote quantities and retry keys, 320/390px booking review, enlarged text, header navigation and standalone Profile. The form test verifies the Job Order notice follows Additional Notes and scrolls down to find the notice on the lazy Review list. Actual normal and enlarged-text form captures were inspected under `scratch/shared-tabs-requestor-20261106/`. Formatting and scoped whitespace checks passed. Initial test lookup failures were resolved before this final run.
8. **Remaining limitations / safe practice:** No physical-device, keyboard/screen-reader, live booking or full-suite verification. The Job Order notice is intentionally below the fold; scroll to reach it. Safely rerun the fixture suites, leave name/email blank to inspect validation, enter isolated fixture values, review, go Back and confirm the values remain. Scroll below Notes and then to the end of Review to locate Job Order. Confirm one fixture submission and the same request key; do not create a live booking or sign as another user for this exercise.

## Non-selected adjacent wheel numbers visibility restored - November 5, 2026

### 1. Cause / reason

The adjacent non-selected numbers in the time picker wheels appeared invisible because of two compounding factors:
1. **Double opacity reduction**: Flutter's `CupertinoPicker` / `ListWheelScrollView` automatically applies `overAndUnderCenterOpacity: 0.447` to all off-center items above and below the center selection. In our previous widget tree, the children were wrapped in an additional `Opacity(0.38)` widget. This compounded to `0.447 * 0.38 = 0.17` (17% effective opacity), which washed out the text against the white background into near-white `(215, 215, 225)` ghost pixels.
2. **Tight viewport clipping**: `wheelHeight` was constrained to `extent * 3 = 120px` with `diameterRatio: 2.2`. This pushed the adjacent items right to the cylinder clipping boundary of `RenderListWheelViewport`.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/booking_time_dialog.dart` | Lines 45–130 (`wheelHeight`, `diameterRatio: 1.15`, child `Text` styling) | Increased `wheelHeight` to `(extent * 3.6).clamp(150.0, 196.0)` and set `diameterRatio: 1.15`. Removed the redundant `Opacity(0.38)` wrapper, letting `CupertinoPicker`'s built-in `overAndUnderCenterOpacity: 0.447` provide clear, high-contrast muted text (`(152, 151, 176)`) for adjacent items. Used `FontWeight.w600` on selected item and `FontWeight.w500` on adjacent items. |
| `campushub/test/select_schedule_test.dart` | Lines 775–783 | Updated assertions to verify both selected and adjacent items (`booking-time-am`, `booking-time-pm`) are present and rendered with `w600` (selected) vs. `w500` (adjacent) weights. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | Top section | Document root cause, exact file/line anchors, functions/data flow, verification results, and safe practice exercise. |

### 3. How it works / functions and data flow

```text
[Stack (height: 150..196px)]
  ├── Positioned Container (height: extent, color: #F2F4F7, borderRadius: 10)  ◄── Centered gray selection pill
  └── CupertinoPicker (diameterRatio: 1.15, selectionOverlay: null)
        └── Children: 01..12, 00..59, AM/PM
              ├── Item above center: rendered at (152, 151, 176) via native 0.447 dimming, w500 (clearly visible!)
              ├── Center selected item: rendered at (26, 24, 81) full navy, w600 (crystal clear over gray pill!)
              └── Item below center: rendered at (152, 151, 176) via native 0.447 dimming, w500 (clearly visible!)
```

### 4. Tests performed & safe practice exercise

- `flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart`: **46/46 passed in 17s**.
- `flutter analyze --no-pub lib/module_app/widgets/facilities/booking_time_dialog.dart lib/module_app/screens/facilities/facility_booking_screen.dart test/select_schedule_test.dart`: **No issues found (2.1s)**.
- Pixel verification of exported frame (`dialog_830.png`):
  - Above center (`Y=325..355`): `darkest = (152, 151, 176)` (crisp, readable muted slate-navy).
  - Center (`Y=385..400`): `darkest = (26, 24, 81)` (deep primary navy).
  - Below center (`Y=430..460`): `darkest = (152, 151, 176)` (crisp, readable muted slate-navy).
- Safe practice: open `booking_time_dialog.dart` and trace `CupertinoPicker`'s `overAndUnderCenterOpacity: 0.447` behavior. Verify that adjacent numbers above and below render with clear contrast against white surfaces without compounding external `Opacity` widgets.

## Time picker wheel visibility fix: selection background behind numbers - November 5, 2026

### 1. Cause / reason

In `BookingTimeDialog` (`campushub/lib/module_app/widgets/facilities/booking_time_dialog.dart`), the subtle light-gray selection background (`#F2F4F7`) was initially supplied to `CupertinoPicker.selectionOverlay`. In Flutter's `CupertinoPicker`, `selectionOverlay` is stacked **on top** of the wheel items (`ListWheelScrollView`). Because `Color(0xFFF2F4F7)` was solid opaque, it covered and completely hid the selected numbers, making only the gray selection container visible to the user.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/booking_time_dialog.dart` | Lines 64–130 (`wheel` widget in `_BookingTimeDialogState`) | Placed the `Positioned` selection background container (`#F2F4F7`, `key: selectionKey`) in a `Stack` **behind** `CupertinoPicker`, and set `CupertinoPicker.selectionOverlay: null` so numbers render directly in front of the background. Increased number font size to `22px` for crisp legibility. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | Top section | Record root cause, exact file/line anchors, functions/data flow, verification results, and safe practice exercise. |

### 3. How it works / functions and data flow

```text
[Stack]
  ├── Positioned Container (height: extent, color: #F2F4F7, borderRadius: 10)  ◄── BACKGROUND (behind)
  └── CupertinoPicker (selectionOverlay: null)                                 ◄── FOREGROUND (on top)
        └── Children: 01..12, 00..59, AM/PM
              ├── Selected item (center): Opacity 1.0, 22px, #1A1851 (crystal clear in front of gray pill)
              └── Adjacent items (top/bottom): Opacity 0.38, 22px, #1A1851
```

- Each wheel column wraps the selection background in a `Stack` behind the `CupertinoPicker`.
- Because `selectionOverlay` is `null`, no overlay covers or obscures the text.
- The numbers (`01`–`12`, `00`–`59`, `AM`/`PM`) render directly in the foreground, perfectly centered over the subtle `#F2F4F7` pill with adjacent values visible above and below.

### 4. Tests performed & safe practice exercise

- `flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart`: **46/46 passed in 16s**.
- `flutter analyze --no-pub lib/module_app/widgets/facilities/booking_time_dialog.dart lib/module_app/screens/facilities/facility_booking_screen.dart test/select_schedule_test.dart`: **No issues found (1.6s)**.
- Pixel verification of exported frame (`time-wheel-390.0-1.0.png`): confirmed `1,966` dark navy pixels present in the wheel center area (`Y=1380` to `1420`), proving numbers are now fully rendered and visible.
- Safe exercise: open `BookingTimeDialog`, inspect the `Stack` structure in `wheel()`, and verify that the selection background is drawn as child 1 (behind) and `CupertinoPicker` with `selectionOverlay: null` as child 2 (in front).

## Bottom-sheet 3-column time picker layout (Hour / Minute / AM-PM) - November 5, 2026

### 1. Cause / reason

The user requested updating the Flutter **Select Schedule** `Start Time` / `End Time` picker layout (`BookingTimeDialog`) to a bottom-sheet layout with rounded top corners, a top drag handle, centered `Start Time` / `End Time` title, three vertically scrollable columns (`Hour`, `Minute`, `AM/PM`) with centered light-gray selection backgrounds (`#F2F4F7`) and reduced opacity (`0.38`) on adjacent values, and horizontal `Cancel` / `OK` buttons at the bottom while preserving CampusHub branding (`#1A1851` navy, `#FCB316` gold, white, `Montserrat` typography) and all existing time-selection and validation behavior.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 378 `_pickTime` (`showModalBottomSheet<TimeOfDay>`) | Open `BookingTimeDialog` via `showModalBottomSheet<TimeOfDay>` (`isScrollControlled: true`, `useSafeArea: true`, `backgroundColor: Colors.transparent`) instead of `showDialog<TimeOfDay>`. |
| `campushub/lib/module_app/widgets/facilities/booking_time_dialog.dart` | 24 `_hourIndex`/`_minuteIndex`/`_periodIndex`; 28 `_hours`/`_minutes`/`_periods`; 52 `wheel(...)`; 130 `Align(alignment: Alignment.bottomCenter, ...)`; 150 `booking-time-drag-handle`; 162 `booking-time-title`; 175 three-column `Row`; 232 horizontal `Cancel` / `OK` `Row` | Render a bottom-sheet surface with 24px rounded top corners, drag handle, centered title, three `CupertinoPicker` columns (`Hour`, `Minute`, `AM/PM`) with `#F2F4F7` selection pills and `0.38` adjacent opacity, and horizontal `Cancel` / `OK` buttons. |
| `campushub/test/select_schedule_test.dart` | 453 `AM/PM wheel preserves and converts hour`; 706 responsive bounds & 3-column wheel/selection/opacity assertions; 1538 Covered Court sheet check | Verify `BottomSheet` presence, drag handle, centered title, 3 side-by-side wheels, centered selection backgrounds, `{1.0, 0.38}` selected vs. adjacent opacity, horizontal `Cancel`/`OK` buttons, and absence of `Confirm`/`Remove` buttons across `390x844`, `280x844` (`200%` text scale), and `320x568`. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | Top section | Record root cause, exact file/line anchors, functions/data flow, verification results, and safe practice exercise. |

### 3. How it works / functions and data flow

1. When the user taps **Start Time** or **End Time**, `FacilityBookingScreen._pickTime(bool start)` (`facility_booking_screen.dart:371`) calls `showModalBottomSheet<TimeOfDay>` with `BookingTimeDialog(title: start ? 'Start Time' : 'End Time', initialTime: _clock(initialValue))`.
2. `_BookingTimeDialogState` initializes three `FixedExtentScrollController` instances: `_hours` (`(initialTime.hour + 11) % 12`, values `01`–`12`), `_minutes` (`initialTime.minute`, values `00`–`59`), and `_periods` (`initialTime.period == DayPeriod.am ? 0 : 1`, values `AM` / `PM`).
3. Each column uses `CupertinoPicker` with a centered rounded light-gray `selectionOverlay` (`#F2F4F7`, `borderRadius: BorderRadius.circular(10)`). The selected item renders at `Opacity(opacity: 1.0)` with `FontWeight.w600` (`Montserrat`), while adjacent items above and below render at `Opacity(opacity: 0.38)` with `FontWeight.w500`. Each wheel item is also wrapped in a synchronous `GestureDetector(onTap: ...)` so tapping an adjacent item jumps immediately without triggering `CupertinoPicker._handleChildTap`'s async haptic delay.
4. Tapping **Cancel** (`booking-time-cancel`) pops `null` without mutating booking state; tapping **OK** (`booking-time-ok`) converts the 3 wheel indices back into a 24-hour `TimeOfDay` (`hour: (hourIndex + 1) % 12 + (periodIndex == 1 ? 12 : 0), minute: minuteIndex`) and returns it to `_pickTime()`, which validates the interval via `_applyTime()`.

### 4. Backend / API & database impact

None. No Django, PostgreSQL, API, model, migration, or booking validation changes.

### 5. Tests performed & safe practice exercise

- `flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart`: **46/46 passed in 17s**.
- `flutter analyze --no-pub lib/module_app/widgets/facilities/booking_time_dialog.dart lib/module_app/screens/facilities/facility_booking_screen.dart test/select_schedule_test.dart`: **No issues found (2.9s)**.
- Safe exercise: run `flutter test --no-pub test/select_schedule_test.dart --plain-name "AM/PM wheel preserves and converts hour"` from `campushub/` to verify all 4 midnight/noon/morning/afternoon 12-hour wheel conversions in isolation.

## Available Hours requires a manual window choice after changing dates - November 5, 2026

1. **Cause / reason:** Confirmed with a failing widget regression: `_syncCustomWindow` automatically assigned `_window`, `_customStart` and `_customEnd` whenever a loaded date had exactly one available custom window. Available Hours therefore displayed a selected check icon without a tap on its hours. This is Flutter selection state, not an API availability error. The latest request supersedes that automatic single-window selection described in older entries below.

2. **Exact files changed:** `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:362` (`_resetTimeSelection`), with callers at 183/274/319; `campushub/test/select_schedule_test.dart:250` (new date-change regression), 333 (changed-hours refresh), 368 (unchanged draft), plus the four-category refresh cases; this guide and the latest summary in `CAMPUSHUB_CONTEXT.md`.

3. **Changes made:** Loading a date lists its actual hours with an empty selection circle. Start/End controls appear after the user taps a custom booking window. Choosing another date clears the old window and completed interval even if the new date has identical hours; Next stays disabled until the existing time-selection flow is completed again.

4. **How it works / functions and data flow:** `_resetTimeSelection()` takes no arguments and returns no value. It clears the local window, start/end draft, explicit-time flag and selected interval while preserving the fetched availability. `_loadMonth` and `_loadSlots` call it after receiving Django data. The row renderer at line 1181 derives its icon/border from `_window`/`_slot`, and time controls at line 1300 require an explicitly chosen custom window. On same-date refresh, `_refreshAvailability` rebinds an unchanged manually chosen window and preserves unfinished input. Changed/removed bounds clear the choice instead of selecting a replacement. Example: select December 1, tap 08:00-17:00 and confirm a valid interval; choosing December 2 with identical hours lists 08:00-17:00 unselected and disables Next. Availability is data; choosing it is a separate user action.

5. **Backend / API behavior:** Unchanged. Existing month/day reads, race guards, dialog cancellation, actual availability, minimum duration, permissions, quote and final submission validation remain. Selecting a date or window creates no booking.

6. **Database / migration impact:** None. No models, migrations, dependencies or working records changed; tests use isolated Flutter service fixtures.

7. **Tests performed:** The focused regression failed before the fix because a selected icon was already present, then passed afterward. Final four-file run: **74/74 Flutter tests passed in20s**, covering `select_schedule_test.dart`, `facility_booking_flow_test.dart`, `covered_court_booking_test.dart` and `facility_details_test.dart`. `flutter analyze --no-pub` reported no issues in54.4s. Nested-repository whitespace checks passed. A separate focused rerun passed while capturing the actual screen; inspected `scratch/available-hours-choice-20261105/hours-after-date-change.png`, showing an empty hours selection circle, no Start/End controls and disabled Next.

8. **Remaining limitations / troubleshooting and safe practice:** No phone install or APK rebuild was performed. Run/restart the updated Flutter app; refreshing Django cannot update an installed old app. Existing initial date selection and picker defaults after a manual window tap remain. Safe exercise: choose a date, tap hours, confirm a valid interval, then choose another date with the same hours. Verify the empty selection circle and disabled Next; tap hours to reveal time controls. Refresh unchanged hours and confirm a manually chosen draft remains. Use the isolated widget test to practice without creating working bookings. After an admin edit invalidates the window, select the new hours manually.

## Operating days now control client booking dates - November 5, 2026

The user explicitly chose **Allow bookings on any enabled operating day**, for all facilities and Add/Edit. This supersedes the older weekend-only/separate allowed-booking-day policy in historical entries below. Confirmed cause: Covered Court had open weekdays, closed weekends and an old weekend-only flag, yielding no bookable dates. The shared Django `booking_day_restriction` now reads operating hours; Add/Edit cleans retired policy keys and `workflow_for_display` omits them from copied presentation data. Flutter removes obsolete policy instructions/badges and still selects only dates/time periods returned by Django. Existing class/maintenance/reservation conflicts, configured minimums, status, client eligibility, quote/payment and final submission protections remain.

Inputs/data flow: admin's seven-day hours -> existing locked Django validation/save -> actual month/day availability -> Flutter calendar refresh -> exact selected interval -> existing quote/submission revalidation. Example: open Monday 08:00-17:00 is eligible even on an old record with `weekend_only:true`; a closed Saturday remains closed. No working records are rewritten to demonstrate this. Current-source read-only December check: 23 available weekdays and 8 closed weekend dates. Full current file/line anchors, functions, tests, setup corrections, troubleshooting, limitations and safe practice exercise are in [the configuration guide](facility-configuration.md#operating-days-control-booking-availability-for-all-facilities---november-5-2026). Four new category-based Flutter refresh cases verify old flags cannot hide server-enabled dates and that changed operating hours replace old selections. Physical-phone/APK/deployed-server verification remains outside this local check.

## Scheduling integration verification and stale draft-hour refresh fix - November 5, 2026

### 1. Cause / reason

Inspected the latest local source, including unpushed schedule/policy and time-dialog work. Confirmed one Flutter defect with a failing widget regression: when a custom free period changed while no complete interval was selected, `_refreshAvailability()` replaced the calendar rows but retained the old `_window`, `_customStart` and `_customEnd`. Example: the list changed from08:00-17:00 to13:00-17:00 after a10:00-13:00 class, but Start Time still displayed08:00. The backend's availability was correct; no backend runtime defect was reproduced.

### 2. Exact files changed / current anchors

| File | Current line / code anchor | Change in this task |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 99 `_refreshAvailability`; 166 unselected-window branch; 362 existing `_syncCustomWindow` | Rebind an unchanged draft window to its fresh server row, or resynchronize draft hours when boundaries/selection type/minimum change. Reuse the existing helper; no new scheduling UI/service. |
| `campushub/test/select_schedule_test.dart` | 127 `ChangingClassCalendarService`; 235 class add/cancel refresh; 259 unchanged draft test | Reproduce stale hours, verify add/cancel updates, and ensure unchanged windows preserve an unfinished invalid entry and its minimum-duration feedback. |
| `backend/core/api/test_mobile_facility_booking.py` | 437 `test_partial_recurring_class_lifecycle_preserves_minimum_and_approved_reservations` | Add isolated four-category API coverage for the user's exact partial-day example, recurrence, minimum duration, conflicting edits, cancellation and reservation preservation. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | this entry / current summary | Record confirmed cause, inputs/outputs, verification and safe practice. |

Earlier unpushed changes remain intact. No new edits in this task to `mobile_booking.py`, `schedules.py`, `operating_schedule.py`, `admin_booking_views.py`, the admin modal, service endpoints, pricing, payments, permissions or time-dialog layout.

### 3. Changes made

When there is no completed interval, refresh now compares the old draft window's start/end, selection type and minimum duration with fresh available rows. If the same window remains, it uses the fresh row and keeps the user's current draft values. If it changed/disappeared, it calls existing `_syncCustomWindow`: one remaining custom period seeds its new bounds; multiple periods require the existing period selection. It still requires explicit time selection before Next. Existing invalidation of a completed interval that becomes blocked remains unchanged.

Operating Schedule still defines regular weekday hours, independently of Manage Facility Schedule. The latter retains Class / Academic Schedule, Official Campus Use, Maintenance, Administrative Hold / Unavailable and Other, plus existing all-day, effective-date and weekly controls. No duplicate calendar, model or scheduling module was added.

### 4. Functions, inputs / outputs and data flow

Admin `scheduleControls()` / submit logic in `backend/static/components/js/admin_booking_forms.js:278/328` reads the existing modal type, date range, all-day flag, times and weekday numbers. Existing create/update endpoints use `validate_schedule()` and `schedule_days()` in `services/schedules.py:49/35`. `save_schedule()` in `admin_booking_views.py:219` expands occurrences only for conflict checking, then stores one Booking plus its existing JSON sidecar. Facility-first locking protects create/update/cancel, sharing the lock with reservation creation. It rejects an overlap rather than cancelling a reservation.

`configured_slots()` in `services/mobile_booking.py:15` reads saved operating hours/presets. `conflicting_bookings():33` finds active reservations, actual occupied room nights and applicable recurring blocks. `schedule_payload():120` splits flexible operating periods at real conflict boundaries; `slot_status():88` assigns actual block types and enforces minimum duration on free intervals. `day_availability():172` returns status, existing reason, rows and available rows; saved booking policy is checked through `booking_day_restriction`. The existing mobile availability endpoint returns `Cache-Control: private, no-store` for day/month reads.

Flutter's existing `FacilityBookingService.monthSlots`/`slots` consumes that response. The screen refreshes through its existing timer, pull-to-refresh, app resume and return-to-route paths; the small new branch synchronizes draft window state with those fresh rows. The existing time selector, validation, schedule-only check, quotation and final submit still use Django. No price or scheduling decision was moved into Flutter.

Annotated example: operating08:00-17:00, class10:00-13:00, minimum4h -> rows08:00-10:00 **unavailable** (only2h),10:00-13:00 **class**,13:00-17:00 **available**. Django does not advertise the2h fragment as a valid rental. With a1h minimum both free fragments can be offered, retaining the user's original operating period and class record. Recurrence applies only on selected weekdays from the effective start through end, inclusively. Existing Covered Court `weekend_only` can still make an otherwise free weekday not bookable.

### 5. Backend / API behavior

No backend runtime/endpoint change. Existing code and tests confirm all five block types, full-day closures, partial windows, minimum duration, recurring effective bounds, exact conflict detection, cancelled-block release, policy restrictions and failed-submit protection. Existing reasons such as `Class / Academic Schedule` are returned without client names/private titles; no new status, label or UI element was introduced. The added test edits a recurring block into a later approved reservation: HTTP409, original block time preserved and reservation still Approved. Editing to a valid time updates availability; cancelling the block retains its history and releases only its time. An approved reservation remains reserved afterward.

### 6. Database / migration impact

No working PostgreSQL business-record writes in this task. Fixtures, normal browser test logins and API saves ran only in a uniquely named local database created/destroyed by the guarded runner. No new tables, models, migrations, dependencies, booking cancellation or automatic policy/schedule update. The preceding separately requested booking deletion is not repeated by these tests.

### 7. Tests performed

- The new stale-draft regression **failed before the change**, expecting Start Time1:00PM but finding the old8:00AM. It **passed after the change**. The initial targeted combined run passed40 tests; adding the unchanged-draft test exposed a test-only lazy-scroll assertion, corrected by scrolling to the existing error before asserting its text.
- **237/237 Django tests passed in88.070s**, system checks clean, disposable database destroyed. Suites: `api.test_facility_form_controls`, `api.test_facility_rental_configuration`, `api.test_mobile_facility_booking`, `modules.facilities.test_admin_reservations`, `modules.facilities.test_calendar`, `modules.facilities.test_booking_workflow`, `api.test_facility_schedule_live_browser`. The new lifecycle test runs Court, Hall, Hostel and Other in their existing **slot** mode; separate existing room tests cover actual room/night behavior.
- Included **111 real HTTP Chrome checks**, no page errors, verify Add/View/Edit, role restrictions, operating hours, policy retention and save/reload/mobile synchronization. This is the retained facility-configuration browser test; it does not claim a fresh manual click-through of every Manage Schedule modal action. Modal wiring was inspected; its create/edit/cancel endpoints were exercised by Django tests.
- Final **41/41 Flutter tests passed in16s**: `select_schedule_test.dart`, `facility_booking_flow_test.dart`, `covered_court_booking_test.dart`. Covers changed unselected windows, unchanged unfinished entries, selected interval invalidation, foreground/resume/route refresh, exact times, minimums, conflicts and final submission. Whole-app `flutter analyze --no-pub`: **No issues found in14.4s**. Test commands from `campushub/`: `flutter test test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart --reporter expanded`, then `flutter analyze --no-pub`. Scoped whitespace checks passed in both repositories.
- Backend uses the established external guarded runner and the seven labels above; optional browser variables use existing Playwright and `SCHEDULE_LIVE_OUT=C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261105/scheduling-integration/`. No extra packages installed. Browser results/captures remain in that external folder.

### 8. Remaining limitations / troubleshooting / safe practice

No physical phone, APK rebuild/install, deployment or working-database schedule edit. Availability synchronization uses the existing30-second foreground poll, pull refresh, app resume, route return and final server checks; this task adds no push/WebSocket scheduling transport. Preset-slot facilities retain whole configured slots rather than becoming custom-time rentals. Specialized service/lease workflows remain separate.

Safe practice: run the isolated lifecycle test and compare its three rows before edit, after edit and after cancellation. Change only its fixture minimum from4h to1h in a practice branch and verify that08:00-10:00 becomes available while10:00-13:00 stays class; revert the practice change. Do not create fake bookings or change real campus schedules for testing. To debug a stale mobile field, compare the latest API row with the selected window, then reproduce with `ChangingClassCalendarService` rather than clearing real records.

## Time dialog: AM/PM selector moved to top-right header - November 5, 2026

### 1. Cause / reason

The user requested moving the `AM` / `PM` selector in the mobile **Select Schedule** `Start Time` / `End Time` time picker dialog (`BookingTimeDialog`) from below the `Hour` and `Minute` swipe wheels to the **top-right corner** of the dialog header.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/booking_time_dialog.dart` | 108 `titlePadding` & `title: Row(...)`; 131 `SegmentedButton<DayPeriod>`; 182 `content` | Move `SegmentedButton<DayPeriod>` (`ValueKey('booking-time-period')`) into the top-right corner of the dialog `title` row opposite `widget.title` (`Start Time` / `End Time`), wrapped in `Flexible` + `FittedBox(fit: BoxFit.scaleDown)` for narrow screens and `200%` text scaling; simplify `content` to the `Hour` / `:` / `Minute` wheel row. |
| `campushub/test/select_schedule_test.dart` | 567 `periodRect` & `hourWheelRect` in `chooseHour` | Verify that `booking-time-period` sits above the `Hour` wheel (`periodRect.bottom <= hourWheelRect.top`) and in the right half of the dialog (`periodRect.right > dialog.center.dx`) across `390x844`, `280x844` (`200%` scale), and `320x568`. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | Top section | Document root cause, exact file/line anchors, functions, data flow, verification results, and safe practice exercise. |

### 3. Changes made

- Moved the `AM` / `PM` `SegmentedButton<DayPeriod>` (`key: const ValueKey('booking-time-period')`) from below the swipe wheels in `content` to the top-right corner of the `AlertDialog` `title` row alongside `widget.title` (`Start Time` or `End Time` on the left).
- Set `titlePadding: const EdgeInsets.fromLTRB(16, 14, 16, 4)` so the left title and top-right `AM` / `PM` toggle align horizontally with the wheel columns below (`contentPadding: const EdgeInsets.fromLTRB(16, 8, 16, 16)`).
- Wrapped the top-right `SegmentedButton<DayPeriod>` in `Flexible` → `Align(alignment: Alignment.centerRight)` → `FittedBox(fit: BoxFit.scaleDown)` so narrow `280dp` viewports at `200%` text scaling never overflow horizontally.
- Preserved all widget keys (`booking-time-dialog`, `booking-time-period`, `booking-time-am`, `booking-time-pm`, `booking-time-hour-wheel`, `booking-time-minute-wheel`, `booking-time-cancel`, `booking-time-ok`), 12-hour `01`–`12` + `00`–`59` wheel behavior, `DayPeriod` conversion to `TimeOfDay`, and Cancel/OK actions.

### 4. How it works / functions and data flow

1. When the user taps **Start Time** or **End Time** in `FacilityBookingScreen._pickTime(bool start)` (`facility_booking_screen.dart:365`), `showDialog<TimeOfDay>` opens `BookingTimeDialog(title: start ? 'Start Time' : 'End Time', initialTime: _clock(initialValue))`.
2. `_BookingTimeDialogState` initializes `_hours` (`(initialTime.hour + 11) % 12`), `_minutes` (`initialTime.minute`), and `_period` (`initialTime.period`).
3. In `build()` (`booking_time_dialog.dart:38`), the dialog header (`title`) renders a `Row` with `Expanded(child: Text(widget.title))` on the top left and `SegmentedButton<DayPeriod>` (`AM` / `PM`) in the top-right corner. Tapping `AM` or `PM` updates `_period` via `setState`.
4. Tapping `OK` (`booking_time_dialog.dart:214`) converts the 12-hour wheel index and `_period` back into a 24-hour `TimeOfDay` (`hour: (_hours.selectedItem + 1) % 12 + (_period == DayPeriod.pm ? 12 : 0), minute: _minutes.selectedItem`) and returns it to `_pickTime()`, which validates the interval via `_applyTime()`.

### 5. Backend / API behavior

No backend or API changes. Django continues to receive 24-hour `HH:MM` strings and enforces operating hours, booking day eligibility, minimum duration, and conflict checks.

### 6. Database / migration impact

No database writes, schema changes, or migrations.

### 7. Tests performed

- `flutter analyze --no-pub lib/module_app/widgets/facilities/booking_time_dialog.dart test/select_schedule_test.dart`: **No issues found** (3.8s).
- `flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart`: **39/39 passed** (20s), including top-right header geometry checks (`periodRect.bottom <= hourWheelRect.top` and `periodRect.right > dialog.center.dx`) at `390x844`, `280x844` (`200%` text scale), and `320x568`.

### 8. Remaining limitations / safe exercise

No physical-phone run or APK rebuild/install was performed in this step; hot restart the active Flutter session to load the updated dialog layout. Safe exercise: run `flutter test --no-pub test/select_schedule_test.dart --plain-name "centered swipe time dialog"` in `campushub/` and observe that `booking-time-period` renders in the top-right header above the `Hour` wheel across all tested screen sizes and text scales.

## Remove redundant booking-day form controls; preserve eligibility - November 5, 2026

1. **Cause / reason:** Latest user request removes only the Add/Edit Allowed Booking Days UI; inspected unpushed code depended on its elements and serializer.
2. **Exact files / anchors:** `admin_facility.html:482/614/1601` removes the section/unused load option and versions the script; `facility_form_controls.js:56/179/225/233` removes checkbox construction, synchronization, serialization and load state. `facility_configuration.py:290/368/381` distinguishes an explicitly submitted list from an omitted saved value. All backend paths are under `backend/core/modules/facilities/`. Complete test/doc file table: [configuration guide](facility-configuration.md#remove-the-allowed-booking-days-form-section-safely---november-5-2026).
3. **Changes made:** Keep Operating Schedule and Manage Facility Schedule; no replacement UI. No Flutter source change in this task; the existing mobile availability integration remains.
4. **How it works:** Form sends operating hours without `allowed_booking_days`. `booking_days_provided` is captured before the backend merges saved JSON. Omitted saved lists stay exact while explicit inputs retain validation. Example: saved Sunday-only list plus `weekend_only: true` still permits only Sunday clients after a campus weekday-hours edit. Closing Sunday blocks its runtime period without deleting that list; reopening cannot permit Saturday. This preserves data without migrations or duplicated Flutter policy.
5. **Backend / API behavior:** Shared eligibility, operating-period, minimum-duration, pricing, interval and conflict checks remain; active Pending/Approved reservations block excluding schedule edits. Specific-date blocks still use existing calendar logic. Permissions and API routes unchanged.
6. **Database / migration impact:** No working-record writes, migrations, new fields or dependencies. No policy backfill/clearing; tests use disposable PostgreSQL.
7. **Tests performed:** 236 Django tests passed (including111 real Chrome checks), and62 relevant Flutter tests passed. Browser verifies absent section, actual hours save/reload, preserved narrower policy, mobile availability and Marketplace restriction. Syntax/reference/whitespace checks passed. See the configuration guide for commands/evidence.
8. **Remaining limitations / safe practice:** No physical phone, APK or deployment verified. Hard-refresh for `20261105-operating-schedule-only`. Inspect unsaved Add/Edit operating controls, then cancel; use disposable tests for persistence/reservation experiments. Saved JSON eligibility remains enforced and has no replacement editor in this task. The previous entry's checklist UI is superseded; server restrictions are preserved.

## Separate campus operation and client booking eligibility - November 5, 2026

1. **Cause / reason:** Operating hours previously doubled as rental eligibility. Latest requirements allow campus weekday operation while retaining Covered Court weekend-only client rentals.
2. **Exact files / anchors:** Shared backend functions are `operating_schedule.py:114` (`booking_day_restriction`), `:136` (`validate_booking_days`) and `:148` (`validate_schedule_change`); callers are `mobile_booking.py:78/92` and `admin_reservations.py:125/141`. Flutter uses `facility_detail_information.dart:68/134` for separate display and `facility_details_screen.dart:882` for the clarified policy chip. All paths are under the existing facilities service/mobile modules; the complete exact file/test table is in the [configuration guide](facility-configuration.md#separate-operating-hours-and-allowed-client-booking-days---november-5-2026).
3. **Changes made:** Existing operating presets configure actual hours; a nearby booking-day checklist configures client eligibility. No unrelated layout/navigation/pricing change.
4. **How it works:** Form inputs produce existing weekly `operating_hours` plus optional JSON `allowed_booking_days`. Django validates distinct day names, open-day subset and saved `weekend_only`, then returns availability. Example: Monday08:00-17:00 with allowed days Saturday/Sunday means campus operation Monday, no Monday client slot. Flutter displays the actual Monday hours while its calendar follows the unavailable server status. This reuses existing scheduling rather than duplicating policy in Dart. Missing list preserves legacy eligibility; explicit empty list closes client dates; existing unrelated saves do not seed it. Room explicit eligibility applies per occupied night, excluding checkout.
5. **Backend / API behavior:** Shared date eligibility applies before existing interval/minimum/conflict/quote/submission checks. A forged weekday selection cannot bypass saved weekend policy. Active Pending/Approved reservations cannot be newly excluded by a schedule/eligibility change; no new endpoint or independent pricing formula.
6. **Database / migration impact:** Optional field lives inside existing workflow JSON when deliberately saved. No schema, migrations, dependencies, automatic backfill or working-record changes. Test saves used disposable PostgreSQL only.
7. **Tests performed:** 234 Django and 70 Flutter tests passed; whole-app Flutter analysis clean. Final separate real HTTP Chrome run passed103 checks with both authorized roles plus Marketplace denial; exported-page matrix passed233 checks. Actual detail widget and browser schedule renders inspected. Complete commands/evidence/setup corrections are in the configuration guide.
8. **Remaining limitations / safe practice:** No physical-phone run, APK rebuild/install or deployment. Hard-refresh admin for script `20261105-operating-booking-days-v2`. Practice safely in an unsaved Add/Edit draft: enable weekday operation, verify Covered Court weekday booking boxes stay disabled, then cancel. Use disposable tests for persistence/reservation experiments. Earlier entries that require closed weekday campus hours are superseded only in that respect; client weekend policy remains enforced.

## Time dialog: AM/PM format and plain titles - November 5, 2026

### 1. Cause / reason

The user requested a 12-hour picker and removal of the visible format suffix. The preceding swipe dialog still used 00-23 and appended (24-hour) to its title. This entry supersedes only that display/conversion behavior; the centered dialog and booking rules remain.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/booking_time_dialog.dart` | 23 hour initialization; 28 `_period`; 145 `SegmentedButton<DayPeriod>`; OK callback near the end of `build` | Display hours 01-12, seed AM/PM from the actual time, add an accessible AM/PM selector and convert the selection back into an exact TimeOfDay. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 375 title in `_pickTime` | Use only Start Time / End Time, without either format suffix. |
| `campushub/test/select_schedule_test.dart` | 205 AM/PM boundary cases; 458 responsive dialog cases; `chooseHour` helper | Add four midnight/noon/morning/afternoon seed, round-trip and period-switch cases; update wheel indices in existing validation/payload scenarios. |
| `docs/booking-module-chatgpt-context.md` | 3 this report | Record functions/data flow, verification and safe exercise. |
| `CAMPUSHUB_CONTEXT.md` | 3 AM/PM summary | Preserve latest requested format and titles. |

### 3. Changes made

The Hour wheel shows 01-12, Minute remains 00-59, and the AM/PM selector sits below the wheels so narrow/large-text phones retain room for the digits. Titles are simply Start Time or End Time. Cancel/OK, centered layout, existing colors/font and absence of a bottom sheet remain.

### 4. How it works / functions and data flow

The initial hour's wheel index is `(hour + 11) % 12`, while `initialTime.period` selects AM/PM. These values are pending dialog state. OK converts the display hour through `(index + 1) % 12`, adding 12 for PM, and preserves the minute. Cancel returns no value. `_pickTime` still guards stale results and `_applyTime` still validates the actual interval. The server keeps receiving its existing HH:mm values; only the user-facing selection format changes.

Examples: 12:07 AM converts to 00:07, 12:07 PM to 12:07, and 2:07 PM to 14:07. This conversion avoids confusing noon with midnight while preserving exact-minute bookings.

### 5. Backend / API behavior

No backend or API source changes. Existing availability, minimum duration, ordering, conflict, pricing and final submission validation remain. A visible PM selection does not bypass the server's permitted hours.

### 6. Database / migration impact

No database writes, model/schema/migration changes, plugins or dependencies. No working bookings/configuration were created or modified.

### 7. Tests performed

- `flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart`: **38/38 passed in 24 seconds**. Four new cases verify initial 00:07, 12:07, 01:07 and 13:07, unchanged confirmation, period switching and titles without format wording. Existing exact 14:07 payload, cancellation, minimum rejection and responsive dialog scenarios pass.
- Whole-app `flutter analyze --no-pub`: **No issues found in 13.9 seconds**. Dart formatting and scoped whitespace checks passed.
- Inspected actual 320px Court, 280px/200% text and 320x568 captures under external `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261105/schedule-ampm-dialog/`. Digits, AM/PM selector, plain title and actions fit. No optional design-kit or full accessibility-certification claim.

### 8. Remaining limitations / safe exercise

No physical-phone run or APK build/install. Hot restart Flutter to apply the update. Safe exercise: run the four AM/PM boundary tests, change only a fixture's minute and confirm it survives both period conversions. On an unsent selection, toggle AM/PM then Cancel to check that the booking value remains unchanged. Do not create working demonstration records.

## Time selection: centered hour/minute swipe dialog - November 5, 2026

### 1. Cause / reason

The user explicitly replaced the preceding bottom-sheet preference with a centered dialog like the attached reference, using swipe selection and no container sliding up from the bottom. This supersedes the sheet and anchored-menu presentation below. Existing booking requirements remain unchanged.

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/booking_time_dialog.dart` | 7 `BookingTimeDialog`; 22/25 wheel controllers; 37 `build`; 60 `CupertinoPicker`; 98 `AlertDialog`; 139 `actions` | New reusable centered 24-hour wheel dialog with Hour/Minute labels, Cancel/OK and locally owned/disposed controllers. Uses built-in Flutter widgets and existing schedule font/colors. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 365 `_pickTime`; 389 `_applyTime`; 422 `_timeChoices` | Remove bottom-sheet/list/exact-entry paths and call the wheel dialog directly. Preserve date/window guards, refresh suspension and shared interval checks. |
| `campushub/test/select_schedule_test.dart` | 402 responsive dialog scenarios; 419 `chooseHour`; 1175 swipe cancellation | Replace sheet/menu assertions with dialog bounds, wheel selection, exact-minute payload, actual swipe/cancellation, minimum errors and valid progression. |
| `docs/booking-module-chatgpt-context.md` | 3 this report | Record updated interaction, functions/data flow, tests and practice. |
| `CAMPUSHUB_CONTEXT.md` | 3 swipe-dialog entry | Preserve the latest explicit preference for future changes. |

### 3. Changes made

Tapping Start or End opens a centered white dialog titled Start time (24-hour) or End time (24-hour). Hours 00-23 and minutes 00-59 scroll independently on wheels. Cancel closes without changing the booking; OK returns the centered values. There is no bottom sheet, long option list, quarter-hour restriction or extra exact-entry action. The page's separate booking-time confirmation checkbox remains absent. Dialog content supports scrolling when vertical space is limited, and wheel sizes follow text scale.

### 4. How it works / functions, inputs, outputs and data flow

`_pickTime(start)` passes the current field's exact `TimeOfDay` and title to `BookingTimeDialog` through `showDialog<TimeOfDay>`. Each `FixedExtentScrollController` starts on that hour/minute and owns only the pending dialog value. Swiping does not change `_customStart`, `_customEnd`, `_slot` or the quote. Cancel/Back/scrim returns null; OK reads the centered wheel indices and returns a `TimeOfDay`. Controllers are disposed with the dialog.

The screen rejects stale date/window results and passes confirmed values to the unchanged `_applyTime()`. That function updates displayed times/duration, clears the old quote and accepts `_slot` only inside the server period with correct ordering and minimum duration. Unlike the former suggestion list, wheels allow every exact minute; invalid choices receive the existing clear validation message and keep Next disabled. The next step and final submission still ask Django to validate the exact interval.

Example: in an isolated 13:00-17:00 period with no extra minimum, selecting Start 14:07 and End 15:00 sends precisely `14:07` and `15:00`, not rounded quarter hours. With a four-hour minimum, 13:00-15:00 is rejected; 13:00-17:00 enables Next. Swiping a minute wheel and then Cancel leaves the previous value intact.

### 5. Backend / API behavior

No backend or API changes. Availability, weekend restrictions, overlap checks, pricing, eligibility and final locked booking submission remain authoritative in Django. The orange selected-date marker stays removed.

### 6. Database / migration impact

No database writes, migrations, model/schema changes, native plugins or dependencies. `CupertinoPicker` is part of the installed Flutter SDK; Django remains the source of booking rules. No production booking was created.

### 7. Tests performed

- `flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart`: **34/34 passed in 30 seconds**. Includes a real minute-wheel drag followed by Cancel, precise `14:07` API input, invalid interval/minimum rejection, valid Next, and dialog bounds at 390x844, 280x844/200% text and 320x568.
- Whole-app `flutter analyze --no-pub`: **No issues found in 17.9 seconds**. Formatting and scoped whitespace checks passed.
- Inspected actual captures of the 320px Court dialog, short 320x568 dialog and 280px/200% text dialog. Colon and action text use explicit existing font styling. External evidence: `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261105/schedule-wheel-dialog/`, including `court-time-wheel-320.png`, `time-wheel-320.0-1.0.png` and `time-wheel-280.0-2.0.png`.
- The first run's three bounds assertions measured AlertDialog's full route wrapper instead of its visible Material surface; tests now measure the actual dialog surface. This was a test-target correction, not removal of responsive checks. Only the final run is counted as passing. No optional design-kit gate or full accessibility-certification claim.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-phone run, APK build/install or deployed change. Hot restart Flutter to apply the Dart changes. Wheel choices are pending until OK; invalid hours/minutes relative to the selected free period still produce the existing schedule error. Safe exercise: run the responsive dialog scenarios, select 14:07/15:00 in isolated fixtures and verify the exact quote body; swipe and Cancel to verify no change. Use fixture tests or unsent selections, without creating demonstration bookings in the working database.

## Time selection: bounded mobile bottom sheet - November 5, 2026

### 1. Cause / reason

The user's phone screenshot shows the anchored time menu covering most of the form. The preceding implementation constrained `showMenu` to 45% height, but that route still chose its position around the field and selected item; it did not provide a stable titled selection area. For this long, dependent list on small screens, this update uses a bounded modal bottom sheet. This is a contextual UI choice, not a claim that dropdowns are universally wrong. Flutter documents modal sheets as an alternative to menus/dialogs with scrolling, safe-area and dismissal support: [official API](https://api.flutter.dev/flutter/material/showModalBottomSheet.html).

### 2. Exact files changed / current anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 364 `_pickTime`; 420 `booking-time-sheet`; 452 `booking-time-close`; 549 `_enterExactTime`; 632 `_applyTime`; 665 `_timeChoices` | Replace anchored menu with a full-width bounded sheet, fixed title/window/Close header, independently scrolling choices and fixed exact-time footer. Remove unused field-position/Builder plumbing; retain existing choice generation and validation. |
| `campushub/test/select_schedule_test.dart` | 114 optional `height`; 395 responsive time scenarios; 423 sheet bounds; 1204 Close action | Add 320x568 coverage alongside 390x844 and 280x844 at 200% text; verify sheet bounds/visible Close, scroll offscreen choices, and preserve cancellation/validation/payload checks. |
| `docs/booking-module-chatgpt-context.md` | 3 this report | Record cause, functions/data flow, verification and practice. |
| `CAMPUSHUB_CONTEXT.md` | 3 bounded-sheet entry | Record current mobile behavior; supersedes anchored-menu layout below. |

### 3. Changes made

Start/End fields retain their current appearance. Tapping either opens a white sheet no taller than 55% of the screen, with a maximum width of 620px on wider screens. The header names the field and shows its available period. Close and Enter exact time remain visible while only the options scroll. The current value is marked with a check. A selection closes the sheet immediately; no new confirmation step. Safe areas protect system controls, and Close, Back, drag or tapping the scrim dismisses the modal without changing values.

### 4. How it works / functions and data flow

`_pickTime(start)` still derives the same time suggestions from the current Django period, selected Start and configured minimum. `showModalBottomSheet<String>` now returns an `HH:mm` choice, `exact`, or null. A bounded Column keeps the header/footer fixed and gives the central ListView the remaining space. `_enterExactTime()` handles arbitrary minutes; `_applyTime()` remains the shared boundary/order/minimum validator. Date/window guards and the existing refresh flag protect open selections. `_next()` continues sending the exact valid interval to Django. No pricing or availability calculation moved into the UI.

Example: a four-hour minimum within 13:00-17:00 offers 17:00 for End. Selecting it closes the sheet and enables Next. Closing the sheet instead retains the previous selection. The exact-time path still rejects 15:00 under the same four-hour minimum.

### 5. Backend / API behavior

No backend/API changes or new routes. Django remains authoritative for availability, conflicts, eligibility, pricing and final submission. The previous selected-date orange-dot removal and absence of a booking-time confirmation checkbox remain.

### 6. Database / migration impact

No database writes, schema/model/migration changes, dependencies or production test records.

### 7. Tests performed

- Final `flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart`: **34/34 passed in 19 seconds**. Includes short-screen bounds, 200% text, scrolling to later times, Close without selection, invalid exact input/minimum duration, exact API values and existing quote/submission behavior.
- Whole-app `flutter analyze --no-pub`: **No issues found in 10.6 seconds**. Formatting and scoped whitespace checks passed.
- Actual rendered sheets inspected at 390x844, 280x844/200% text and 320x568. Header, Close, time list and exact-entry footer fit; the short-screen list scrolls in its assigned area. Evidence: external `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261105/schedule-time-sheet/`, including `time-dropdown-390.0-1.0.png`, `time-dropdown-280.0-2.0.png`, and `time-dropdown-320.0-1.0.png` (historical capture names now depict sheets).
- Initial migration run had two widget failures because tests tried to find offscreen lazy list items before scrolling. Tests now scroll the actual options list; this was not fixed by disabling validation or eagerly rendering every option. Only the final passing run is counted. Optional design-kit gates remain unavailable; no full accessibility certification or physical-phone claim.

### 8. Remaining limitations / safe practice

No APK build/install or physical-phone run. Hot restart Flutter to load the change. The sheet intentionally makes the underlying form inactive until a choice or dismissal, avoiding accidental form taps. For practice, run the responsive time scenarios with the isolated fixtures: open End, scroll to a later value, choose it, and verify the same `start`/`end` reaches the fixture quote; reopen and Close to confirm no change. Do not create fake working bookings for UI practice.

## Select Schedule: plain selected date and working time dropdowns - November 5, 2026

### 1. Cause / reason

Confirmed: the calendar added a separate gold/orange `_StatusDot(scheduleGold)` inside the selected date's navy circle. Also, the Start/End buttons displayed dropdown chevrons but opened only a manual time-entry dialog. The user requested removal of that selected-date dot and functional dropdowns.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/booking_schedule_calendar.dart` | 247 `child: number` in `_date` | Remove the selected-date Stack/gold dot; keep the navy circle, white date and real status indicators elsewhere. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 364 `_pickTime`; 481 `_enterExactTime`; 564 `_applyTime`; 597 `_timeChoices` | Anchor scrollable popup menus to the time fields, derive suggestions from the selected server period/minimum, retain exact-minute entry, and share the original interval validator. |
| `campushub/test/select_schedule_test.dart` | 412 `chooseHour`; 905 gold-dot assertion; 923 selected-date capture; 1099 Covered Court scenario; 1198 dropdown capture | Exercise Start and End menu choices, exact-entry rejection, minimum filtering, dismissal, exact submitted times, no gold selected-date marker, and responsive renders. |
| `docs/booking-module-chatgpt-context.md` | 3 this report | Explain implementation, verification and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | 3 dropdown summary | Record the latest behavior for subsequent work. |

### 3. Changes made

Selected dates now show only the existing navy circle with white text. Unselected dates retain database-backed status dots/prohibition marks. The time controls open actual Flutter popup menus aligned to the pressed field. Menus use the existing font, navy text, white surface and light outline, with no heavy shadow. Lists scroll and retain large text sizing. The earlier removal of the booking-time confirmation checkbox remains.

### 4. How it works / functions, inputs, outputs and data flow

`_pickTime(start, fieldContext)` reads the selected available window and its minimum duration. Start suggestions stop early enough to leave room for that minimum. End suggestions begin at selected Start plus the minimum, or strictly after Start when no positive minimum exists. Quarter-hour suggestions include exact server boundaries and positive minimum-derived boundaries, rather than rounding away authorized times. It does not invent availability or alter operating hours.

The built-in `showMenu<String>` returns an `HH:mm` value, `exact`, or null on dismissal. `exact` opens `_enterExactTime()`, preserving arbitrary valid minute values. Both routes call `_applyTime()`, which contains the original boundary/order/minimum checks, updates displayed values/duration, clears the old quote and assigns `_slot` only when valid. Dismissal makes no selection. Date/window identity guards discard stale results; the existing `_pickingTime` flag prevents background refresh from replacing the window during selection. `_next()` still sends the exact chosen interval to Django before Details.

Example using an isolated available period 13:00-17:00 with a 240-minute minimum: Start offers 13:00 and End offers 17:00, followed by Enter exact time. Selecting 17:00 enables Next directly. Entering 15:00 through exact entry still shows the four-hour minimum error. Quarter-hour suggestions are a convenience, not a new booking-increment policy.

### 5. Backend / API behavior

No Django/API changes. Server availability, weekend policy, eligibility, charges, conflicts and final locked submission checks remain authoritative. The menus use the existing response rather than a new endpoint or local schedule copy.

### 6. Database / migration impact

No saved-data writes, model/migration/schema changes or dependencies. No production booking or configuration was created or changed. Earlier approved deposit corrections were not replayed.

### 7. Tests performed

- Final targeted run: `flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart` — **33/33 passed**. Covers both dropdowns at 390px and 280px/200% text, out-of-period exact entry, minimum duration, cancellation, direct progression at 320px, quote/submission behavior and live availability. Selected-date assertions cover 280/320/390/768px.
- Final whole-app `flutter analyze --no-pub` reported **No issues found**. Dart formatting and scoped whitespace checks passed.
- Actual rendered captures were inspected: plain selected date at 390px, End dropdown at 320px, and dropdown at 280px/200% text. Initial visual inspection prompted explicit variable-font weights and a light menu border with zero elevation; refreshed captures verify those changes. Evidence: `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261105/schedule-dropdowns/`, including `selected-date-390.0-1.0.png`, `court-end-dropdown-320.png` and `time-dropdown-280.0-2.0.png`.
- Tests use disposable UI responses, not a live server/database. The optional design-kit scripts remain unavailable; no kit-wide gate or accessibility-certification claim.

### 8. Remaining limitations / troubleshooting / safe practice

No physical-phone verification, APK rebuild/install or production booking was performed. Hot restart the existing Flutter session to load the Dart changes. Only permitted times for the selected free period appear; choose a different available period if needed. Enter exact time supports non-quarter-hour requests, with the same local/server validation. A shorter window than the required minimum offers exact entry but cannot produce a valid booking.

Safe practice: run the existing Covered Court scenario in `test/select_schedule_test.dart`. Open Start, dismiss it and verify Next stays disabled; choose End 17:00 for the isolated 13:00-17:00/four-hour fixture and verify Next enables without confirmation. Run the shorter-duration scenario to see exact 15:00 rejected. Use fixtures or unsent selections rather than saving fake bookings to the working database.

## Mobile Select Schedule: compact time fields without confirmation - November 5, 2026

### 1. Cause / reason

The user supplied an Available Hours reference and requested the mobile Select Schedule design without its "Confirm my selected booking time" checkbox. Inspection confirmed that the current Flutter source already had no such checkbox: a valid time-picker result enabled Next directly. The existing fields placed labels inside tall buttons and stacked at 320px. This update makes the fields follow the supplied compact layout while retaining the existing selection and validation behavior.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 476 `_timeChoices`; 514 `stackFields`; 540 `Semantics` | Put labels above compact bordered time controls, add chevrons, fit two columns on regular phones, stack for narrow/large-text layouts, and name each time button for assistive technology. Remove the long instruction sentence; retain configured minimum duration, selected duration and validation colors. |
| `campushub/test/select_schedule_test.dart` | 1057 Covered Court test; 1112 `startRect`; 1152 capture | Extend the existing scenario to check no checkbox, two columns and minimum 48px targets at 320px, enabled Next after a valid selection, and the exact interval passed to server validation without creating a booking. Enable an optional actual-screen capture. |
| `docs/booking-module-chatgpt-context.md` | 3 this report | Record cause, behavior, data flow, tests and safe practice. |
| `CAMPUSHUB_CONTEXT.md` | 3 compact time-field entry | Preserve the latest requested UI behavior for future work. |

### 3. Changes made

Start Time and End Time now appear above their respective bordered buttons. Each control shows its value and a downward chevron, with at least a 48px target. They sit beside each other when the content width is at least 260px and the scaled 14px text is no larger than 21px; otherwise they stack. Existing navy, font, borders, picker, available periods, summary and Next button remain. There is no separate confirmation control or confirmation flag.

### 4. How it works / functions and data flow

`_timeChoices()` reads `_window`, `_customStart`, `_customEnd`, `_hasExplicitTimeSelection` and `_error`, then returns the responsive fields and computed duration. Each button calls the existing `_pickTime(start)` with true for Start or false for End. That function validates the chosen interval against the selected server window and configured minimum, updates the displayed values, and assigns `_slot` only when valid. Next uses that valid `_slot`; `_next()` sends its exact date/start/end through the existing Django schedule validation before opening Details. A displayed opening time is only a starting value until the user chooses a time; no full-day reservation is silently selected.

Example: for an isolated available period 13:00-17:00 with a 240-minute minimum, choosing 17:00 as End displays four hours and enables Next immediately. Choosing 15:00 instead shows the existing minimum-duration error and leaves Next disabled. No checkbox is involved.

### 5. Backend / API behavior

No backend or API source changed for this update. Django still supplies actual availability and revalidates the exact interval. Weekend restrictions, booking conflicts, prices, eligibility, deposits and final submission remain in the existing server workflows.

### 6. Database / migration impact

No working-data write, model, migration, dependency or schema change. UI tests use disposable in-memory responses; no production bookings were created. The previously approved removal of the mistaken Court deposit was not replayed.

### 7. Tests performed

- `flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart`: **33/33 passed in 19 seconds**. Includes 320px side-by-side controls/no confirmation/direct Next, invalid intervals and minimum duration, existing live availability behavior, 280px at 200% text scale, and complete Review/submission scenarios.
- `flutter analyze --no-pub`: **No issues found**, 11.8 seconds. Scoped `git diff --check` passed (only a line-ending conversion notice).
- Actual Flutter captures were generated with `SELECT_SCHEDULE_REVIEW_DIR=C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261105/schedule-no-confirm`. Inspected `court-times-no-confirm-320.png` and `custom-time-280.0-2.0.png`: compact fields fit regular phones, large-text fields stack, and no confirmation checkbox appears. The 320px capture shows Next enabled after valid selection. These are isolated widget renders, not a connected-phone session.
- The optional design-skill token/gate scripts are not installed in this project, so no design-kit gate or full accessibility certification is claimed. The actual project checks above were run.

### 8. Remaining limitations / troubleshooting / safe practice

No APK was rebuilt or installed for this small Dart layout update, and no physical-phone run was performed. Hot restart the existing Flutter session to load it. If Next stays disabled, choose a valid time inside the selected available period and satisfy the displayed minimum; no confirmation checkbox is needed. Django may reject a period if availability changes before validation.

Safe exercise: run the existing Covered Court test in `test/select_schedule_test.dart`; observe that a valid 13:00-17:00 choice enables Next and sends those exact values. Use the existing shorter-duration test to verify 13:00-15:00 stays disabled with a four-hour minimum. Practice only with these isolated fixtures or an unsent mobile selection, without creating demonstration bookings in the working database.

## Select Schedule UI/UX, Wrapping Legend, Explicit Custom Time Selection & Summary - November 4, 2026

### 1. Cause / reason

Confirmed UI/UX and time-selection issues on the Flutter **Select Schedule** screen (`FacilityBookingScreen` step `0`):
1. **Stepper & Scroll Layout**: `BookingScaffold` disabled top `SafeArea` (`top: false`), `BookingSteps` had `top: 6` without `FittedBox(fit: BoxFit.scaleDown)` around step labels (`Schedule`, `Details`, `Review`, `Submit`), and the `ListView` used `EdgeInsets.fromLTRB(16, 0, 16, 32)` bottom padding, which allowed the fixed bottom `Next: Booking Details` bar to overlap bottom time controls on short viewports.
2. **Horizontal Legend Clipping**: `BookingScheduleCalendar` used `SingleChildScrollView(scrollDirection: Axis.horizontal)` with 6 short internal labels (`Available`, `Not Bookable`, `Campus Use / Hold`, `Reserved`, `Maintenance`, `Class Schedule`), clipping legend items horizontally on phone viewports instead of wrapping with clear institutional explanations.
3. **Flexible Operating Hours vs. Selected Booking Interval**: When the backend returned a flexible custom window (`time_selection == 'custom'`, e.g., Covered Court `8:00 AM - 5:00 PM` with `minimum_duration_minutes: 240`), the section heading still read `Available Time Slots`, tapping the available window silently assumed the user wanted the entire 9-hour operating period (`08:00`–`17:00`) and enabled `Next: Booking Details` immediately, and picking an invalid duration in `_pickTime()` returned early without updating the displayed `Start Time` / `End Time` or `Selected Duration`.

### 2. Exact files changed / current lines and anchors

| File | Current line / code anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/booking_widgets.dart` | 318 `BookingScaffold.build` (`SafeArea`); 510 `BookingSteps.build` (`FittedBox`) | Enable full `SafeArea` in `BookingScaffold`; increase `BookingSteps` top padding to `10` and wrap step labels (`Schedule`, `Details`, `Review`, `Submit`) in `FittedBox(fit: BoxFit.scaleDown)` with `maxLines: 1` so steps never clip on `280dp`–`320dp` or `200%` text scale. |
| `campushub/lib/module_app/widgets/facilities/booking_schedule_calendar.dart` | 142 `FittedBox` + `Row(key: ValueKey('schedule-legend'))`; 267 `_legend` | Render the 4 status labels (`Available`, `Closed`, `Unavailable`, `Reserved`) in a single straight row without long descriptions, scaled inside `FittedBox(fit: BoxFit.scaleDown)` so it never clips horizontally while preserving all calendar day dot colors and `ScheduleProhibitionPainter`. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 54 `_customStart`, `_customEnd`, `_hasExplicitTimeSelection`; 330 `_hasCustomHours`; 343 `_syncCustomWindow`; 364 `_pickTime`; 476 `_timeChoices`; 628 `_selectionSummary`; 761 `_next` catch scroll; 985 `ListView` padding; 1150 `Available Hours` heading; 1175 partial-day indicator; 1211 slot/window selector | Separate the available operating window (`_window`) from the confirmed booking interval (`_slot`), auto-attach single custom windows, require explicit valid start/end selection, display `Available Hours`, `Select Booking Time`, `Start Time`, `End Time`, `Selected Duration`, `Minimum booking duration`, and the compact `_selectionSummary()`, and increase bottom scroll padding to `96dp`. |
| `campushub/test/select_schedule_test.dart` | 759 wrapping legend assertions; 1057 `Covered Court flexible window requires explicit selection, validates 4h minimum and shows summary without overlap` | Update legend assertions for `Wrap` and add end-to-end widget coverage for non-clipping stepper, partial-day availability text, explicit custom time selection, 4-hour minimum duration validation, compact selection summary, and non-overlapping bottom `Next` button. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | Top section | Document root cause, exact file/line anchors, functions, data flow, verification results, and safe practice exercise. |

### 3. Changes made

- **Responsive Stepper & Scroll Clearance**: `BookingSteps` keeps `Schedule` → `Details` → `Review` → `Submit` visible below the AppBar and status bar with `SafeArea`, scaling labels cleanly on narrow `280dp`–`320dp` screens and `200%` text scaling. `ListView` padding is `EdgeInsets.fromLTRB(16, 8, 16, 96)` so the bottom `Next: Booking Details` button never overlaps `Start Time`, `End Time`, or the compact summary.
- **Single-Row Centered Calendar Availability Legend**: `BookingScheduleCalendar` renders the 4 availability status labels (`Available`, `Closed`, `Unavailable`, `Reserved`) centered in one straight horizontal row (`Row` inside `FittedBox(fit: BoxFit.scaleDown, alignment: Alignment.center)`) without description text or horizontal clipping.
- **Available Hours, Select Booking Time & Explicit Selection**:
  - Displays **Available Hours** when the backend provides flexible windows (`time_selection == 'custom'`) and preserves **Available Time Slots** for fixed preset slots.
  - For partially occupied dates (`_slots` containing both available and blocked/occupied periods), displays `Remaining available hours for this date.` and lists only the open periods.
  - Shows each flexible window with a clock icon and `Available booking window` subtitle, separate from the user's chosen interval.
  - Under **Select Booking Time**, displays `Minimum booking duration: X hours.` (from Django's `minimum_duration_minutes`), `Start Time`, `End Time`, and `Selected Duration`.
  - Does not silently assume the entire operating window (`8:00 AM - 5:00 PM`) is the user's intended booking duration: `_slot` stays `null` and `Next: Booking Details` stays disabled until the user explicitly selects a valid time interval.
  - When an invalid interval is chosen (e.g., `8:00 AM`–`11:00 AM` = `3 hours` when minimum is `4 hours`, or `3:00 PM`–`6:00 PM` outside `8:00 AM - 5:00 PM`), `Start Time`, `End Time`, and `Selected Duration` update to reflect the user's input in red while `_slot` is cleared, `_error` shows a concise message, and `Next: Booking Details` remains disabled.
  - Once a valid interval is selected, `_selectionSummary()` renders a compact summary showing `Selected Date`, `Start Time`, `End Time`, and `Total Duration`.

### 4. How it works / functions, inputs, outputs and data flow

1. `_loadMonth()` and `_loadSlots()` receive the slot list from Django (`GET /api/mobile/facilities/<id>/availability/`) and call `_syncCustomWindow(slots)`. If a date has a single open custom window (`time_selection == 'custom'`), `_window` is initialized to that window with `_customStart = window['start']`, `_customEnd = window['end']`, `_hasExplicitTimeSelection = false`, and `_slot = null`.
2. `_pickTime(bool start)` opens Flutter's 24-hour `showTimePicker` (with narrow-screen textScaler clamping so dialog buttons never clip), formats the picked `TimeOfDay` as `HH:MM` (`first` / `last`), sets `_hasExplicitTimeSelection = true`, and computes `minutes = _minutesBetween(first, last)`.
3. If `first < window['start']`, `last > window['end']`, or `first >= last`, `_slot` is set to `null` and `_error` is set to `'Choose a start before the end, within ${window['label']}.'`. If `minutes < window['minimum_duration_minutes']`, `_slot` is set to `null` and `_error` is set to `'Minimum booking duration is ${_durationLabel(minimum.toInt())}.'`. Otherwise `_slot` is populated with the validated 24-hour `start` and `end` while the UI displays readable 12-hour AM/PM labels via `bookingTime()`.
4. Tapping `Next: Booking Details` calls `_next()`, which sets `_busy = true` (showing a loading spinner and preventing duplicate taps) and posts `{date, start, end, availability_only: true}` to `POST /api/mobile/facilities/<id>/quote/`. Only after Django confirms the interval is still available does the screen advance to Step 1 (`Booking Details`).

Annotated example (Covered Court weekend flexible window):

```text
Django availability slot: start="08:00", end="17:00", time_selection="custom", minimum_duration_minutes=240
1. Initial state on Saturday:
   - Available Hours: 8:00 AM - 5:00 PM (Available booking window)
   - Start Time: 8:00 AM | End Time: Select time | Selected Duration: Select start and end time
   - Next: Booking Details -> disabled (_slot == null)
2. User selects End Time = 11:00 AM (08:00 to 11:00):
   - Selected Duration: 3 hours (highlighted in red)
   - Error: "Minimum booking duration is 4 hours."
   - Next: Booking Details -> disabled (_slot == null)
3. User selects End Time = 12:00 PM (08:00 to 12:00):
   - Selected Duration: 4 hours
   - Compact Summary: Selected Date, Start Time (8:00 AM), End Time (12:00 PM), Total Duration (4 hours)
   - Next: Booking Details -> enabled -> validates with Django quote/ before advancing
```

### 5. Backend / API behavior

No Django routes or payload contracts were changed. Flutter continues to read `GET /api/mobile/facilities/<id>/availability/?month=YYYY-MM` and `?date=YYYY-MM-DD`, revalidate schedule intervals via `POST /api/mobile/facilities/<id>/quote/` (`availability_only: true` on Step 0, full quote on Step 1), and submit via `POST /api/mobile/bookings/` in `Asia/Manila` time.

### 6. Database / migration impact

None. No models, migrations, or working PostgreSQL records were modified.

### 7. Tests performed

- **Flutter static analysis**: `flutter analyze --no-pub` — **No issues found** (`13.2s`).
- **Flutter widget & integration tests**: **63/63 tests passed** across `test/select_schedule_test.dart` (`23/23`), `test/covered_court_booking_test.dart`, `test/facility_booking_flow_test.dart`, `test/facility_details_test.dart`, and `test/job_order_screen_test.dart`.
- **Django backend facility tests**: **74/74 tests passed in 12.179s** (`System check identified no issues`) across `api.test_mobile_facility_booking`, `modules.facilities.test_admin_reservations`, and `modules.facilities.test_calendar` using the guarded disposable local PostgreSQL test runner.

### 8. Remaining limitations / troubleshooting / safe practice

- Verification was performed in the automated Flutter widget test harness (`280dp` at `200%` text scale, `320dp`, `390dp`, and `768dp`) and the guarded local PostgreSQL test runner; physical Android handset interaction was not claimed for this step.
- **Safe practice exercise**: In `campushub/test/select_schedule_test.dart`, locate the test `'Covered Court flexible window requires explicit selection, validates 4h minimum and shows summary without overlap'`. Temporarily change the entered end hour from `'17'` (`5:00 PM`, 4 hours from `1:00 PM`) to `'16'` (`4:00 PM`, 3 hours from `1:00 PM`), run `flutter test --no-pub test/select_schedule_test.dart`, and observe that `Next: Booking Details` stays disabled (`onPressed == null`) and `Minimum booking duration is 4 hours.` is shown. Restore `'17'` and re-run the test to confirm all 23 tests pass.

## Covered Court: complete Django quotes and Flutter submission - November 4, 2026

### 1. Cause / reason

Confirmed blocker: the old mobile quote called `slot_base_amount()` with its simple-quote safeguards. A facility with active additional fees, discounts or a damage deposit was intentionally rejected for staff quotation. Covered Court actually has all three settings. Meanwhile the existing staff `reservation_quote()` already supports these charges. Flutter sent only date/start/end when requesting its full quote, had no quantity input, and displayed only a base amount and total. Booking History also had a real refresh defect: its expression-bodied `setState` callback returned a Future, which Flutter rejects in debug mode.

Read-only inspection of actual Covered Court `CAMFACIL20261013F13A` confirmed weekend-only policy, Monday-Friday closed, Saturday/Sunday08:00-17:00, minimum4hours, package3000/first4hours plus500/additional hour, optional700/hour, Chairs10/item, internal50% and immediate-family20% discount rules, and a separate fixed10 damage deposit marked applicable. The source reference documents10/chair, not an established Court damage deposit. The saved deposit is a data correction requiring the user's explicit confirmation, not permission to silently reinterpret it as a different charge. The proposed correction is recorded in the [configuration guide](facility-configuration.md#covered-court-weekend-controls-and-deposit-correction---november-4-2026).

The existing weekend controls were tested in an isolated browser: allowed Saturday/Sunday times and Custom remain editable, including after View -> Edit; Weekdays/Daily and Monday-Friday remain disabled/closed. No calendar/editor redesign or operating-policy rewrite was needed. Existing hours and conflict records were not replaced.

### 2. Exact files changed / current lines and anchors

| File | Current line / code anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/rental_configuration.py` | 341 `slot_price_components`; 371 `slot_base_amount` | Share package/hour arithmetic and expose initial/extra-hour components while retaining the legacy simple-quote guard. |
| `backend/core/modules/facilities/services/admin_reservations.py` | 164 `configured_discount_amount`; 181 `reservation_quote` | Share discount arithmetic; return detailed rental components and fee units; clearly reject incomplete/invalid deposit configuration. |
| `backend/core/modules/facilities/services/mobile_booking.py` | 200 `rental_quote`; 220 `mobile_pricing_options`; 228 `complete_mobile_quote` | Delegate complete mobile quotes to the staff engine, validate optional quantities, bind discount eligibility to the authenticated account, and sign the reviewed configuration/quote. |
| `backend/core/modules/facilities/mobile_views.py` | 83 `availability`; 139 `quote`; 160 `_details`; 185 `bookings` | Preserve real availability; expose saved quantity options; require complete quotes for configured adjustments; revalidate under the facility lock and protect immutable idempotent retries. Explicitly type the existing mixed JSON details dictionary. |
| `backend/core/modules/facilities/services/booking_workflow.py` | 527 `public_client_details` | Return client-facing initial/extra-hour and discount labels/notes in saved history/status without exposing staff evidence or submission fingerprints. |
| `backend/core/api/test_mobile_facility_booking.py` | 61 `covered_court_pricing`; 87 complete quote parity; 114 weekend intervals; 125 deposits; 135 quantities; 144 forged eligibility; 156 changed quote/conflict; 645 concurrency class | Add isolated PostgreSQL pricing, persistence, validation, history, idempotency and true two-connection overlap coverage; update the additive schedule-only response assertion. |
| `backend/core/modules/facilities/test_booking_workflow.py` | 1484 private/no-store assertions; 1546 invalid tab-auth redirect | Align two old assertions with the already-existing stronger no-cache header and HTML login redirect. No authentication implementation changed. |
| `campushub/lib/module_app/services/facility_booking_service.dart` | 9 `BookingException`; 34 `request` | Retain status and distinguish uncertain submission failures from definite validation errors. POST booking failures are never automatically replayed. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 43 quantity controllers; 628 `_selectionSummary`; 687 `_go`; 696 `_next`; 764 `_bookingInputs`; 773 `_loadPricingOptions`; 800 `_feeQuantity`; 1037 recovery action; 1589 cost breakdown | Send actual attendees/requirements/quantities, display only Django-computed components, submit the reviewed token and freeze uncertain retries. Preserve concurrent Schedule refinements; repair their undefined surface reference using the existing `bookingSurfaceLight`. Keep existing steps/navigation; let the success status wrap at narrow widths. |
| `campushub/lib/module_app/screens/facilities/facility_booking_history_screen.dart` | 35 lifecycle handler; 42 `_refresh` | Refresh actual approval/history on resume and fix the Future-returning `setState` callback. |
| `campushub/test/covered_court_booking_test.dart` | 18 fixture service; 189/235/255/273 new UI scenarios | Verify matching breakdown/payload at320/390px, one-booking lost-response retry, definite rejection recovery and resumed approval. Fixture prices/deposits are isolated, not new working settings. |
| `docs/booking-module-chatgpt-context.md` | 83 this report | Full implementation/data-flow/testing guide. |
| `docs/facility-configuration.md` | 3 companion report | Actual saved settings, editable controls and explicit deposit-correction proposal. |
| `CAMPUSHUB_CONTEXT.md` | 10 complete-quote summary | Preserve the new complete-quote behavior and limitations for subsequent work. |

### 3. Changes made

Backend remains the sole price authority. The existing package/hourly calculation now supplies separate initial and additional-hour amounts to both quote callers. The staff calculation still handles fees, discounts and deposits; mobile delegates to it instead of duplicating financial arithmetic. Fee output includes saved unit amount/index/basis for clear display. Discount calculation is capped to the applicable basis and gross rental so it cannot create negative rental charges.

Mobile eligibility comes from the bearer owner's saved Django `user_type`, never caller-supplied `client_id`, affiliation or staff-verification text. Saved student accounts may use configured Student/Internal rules; faculty/employee accounts may use Internal rules. If several eligible configured rules apply, the largest single reduction is selected without stacking. Guest/unclassified accounts receive none. Immediate-family/Other and custom-scope discounts still require Facilities Admin verification; mobile cannot claim them by posting an index or a reason. This uses existing account classification, not a newly implemented institutional-ID verification system.

Optional per-item fees come from the actual configuration returned during Schedule validation. Selecting Chairs requires a positive chair quantity when an active saved chair fee exists. Quantity0 omits an optional item from the amount; negative, fractional, boolean, oversized or unknown-index quantities are rejected. No rate is seeded from a name and no missing chair price is fabricated. Other unpriced requests remain explicitly subject to availability/staff quotation.

Flutter keeps the existing Schedule -> Details -> Review -> Submitted flow and components. Details gains only the quantity fields needed for configured item fees. Review shows initial rental, extra-hour charges, eligible discount, selected item charges, configured refundable deposit and final server total. A positive quantity selects the existing Chairs requirement; clearing that checkbox resets its quantity. A definite rejection returns to retained Details for re-quotation. An uncertain network/server response retains the exact submitted payload/key, offers an explicit Check My Bookings action, and retries that same payload; background availability refresh does not discard a pending submission.

### 4. How it works / functions, inputs, outputs and data flow

1. `availability()` returns actual database-backed periods for the displayed month/date, including policy and schedule conflicts. The already-existing Schedule request with `availability_only: true` calls `reservation_schedule(..., check_capacity=False)` and returns only availability plus current saved per-item options; it supplies no payable quote.
2. The Details request sends date/start/end, attendee count, selected requirements and `fee_quantities` keyed by the configuration's existing fee index. `complete_mobile_quote()` validates quantities, constructs trusted client fields from the bearer owner, and calls `reservation_quote()`. That engine validates the exact interval/capacity and calculates rental, one eligible discount, configured fees and deposit. `slot_price_components()` and `configured_discount_amount()` contain the shared arithmetic.
3. The returned `quote_token` is an HMAC signature from Django's existing signer over the user/facility, normalized pricing inputs, saved workflow and resulting quote. It is not a login token. A different amount, quantity, facility configuration or authenticated account cannot reuse the reviewed signature. No new signing dependency or database quote table is needed.
4. On POST `/api/mobile/bookings/`, the existing `transaction.atomic()` and `select_for_update()` facility lock serialize competing bookings. Before creating records, Django reruns eligibility, exact schedule/capacity/conflict checks and the complete quote. It checks the supplied reviewed token for adjusted configurations and any token-bearing request, and checks `quoted_amount` when supplied. A schedule-only flag does not bypass this path.
5. Successful submission creates the existing `Booking` and `FacilityBookingRequest` rows with pending status, correct total and a charge snapshot. A submission fingerprint prevents an already-used key from silently accepting changed details. A true repeat for the same owner/facility returns the original booking; no second reservation is created. Failed validation creates neither booking nor sidecar.
6. Existing owner-scoped detail/history serializers expose current status and the saved client-facing quote. Internal evidence and fingerprints stay private. Booking History refreshes on resume/pull/return; the existing Status screen refreshes on resume/pull. Approvals remain staff-controlled and are not fabricated locally.

Annotated isolated example, with **no deposit configured**:

```text
08:00-13:00 = 5 hours, saved four-hour package:
3000 initial rental + 500 extra hour = 3500 gross rental
50% eligible Internal reduction = 1750; net rental = 1750
20 chairs x saved10 = 200; refundable deposit = 0
Estimated total = 1950
```

The authorized-deposit fixture separately verifies fixed500 and40% of net rental; Flutter's captured fixture uses fixed500 and displays2450. These are test cases, not a policy decision or automatic deposit configuration for the real Covered Court.

### 5. Backend / API behavior

Existing routes are reused. Full quote POST now receives attendees and optional quantities and returns the full authoritative breakdown plus `quote_token`. Schedule-only responses add `pricing_options.item_fees`; they remain amount-free. Adjusted bookings require a reviewed matching token. Basic legacy callers retain the existing server-calculated simple booking path. Status/history add client-facing component fields while retaining existing keys, owner checks and statuses. The old direct `rental_quote()` call without authenticated full-quote inputs retains its simple-quote safety guard. Other booking modes and legacy equipment/custom quotes still use their existing staff processes. FastAPI remains chat-only.

### 6. Database / migration impact

No model, migration, new dependency or new database table. New bookings store additional snapshot/idempotency metadata in the existing JSON sidecar. Existing booking, payment, schedule and quote records are not rewritten. All test mutations ran only in a uniquely named disposable **local** PostgreSQL database, guarded to localhost:5432 and the generated test name, which was destroyed afterwards. After the user explicitly answered **Yes—remove only the mistaken ₱10 deposit**, the exact two-key correction was applied to the one working Covered Court row and verified in a fresh read-only transaction. The deposit flag is now false and the mistaken deposit object is absent; every other reviewed field matches the original snapshot.

The approved correction changed only `workflow_config.damage_deposit_applicable` to false and removed `workflow_config.damage_deposit`. It preserved Chairs10/item, schedules, pricing, discount rules and all existing reservations. The external helper checked the complete pre-reviewed workflow SHA256 under a row lock, validated the proposed configuration, kept a local before/after backup and would abort if saved settings changed after review. It creates no new booking and is not installed in startup or migrations. `deposit-correction-result.json` records `applied: true`; `facility-after.json` independently verifies the exact resulting row.

### 7. Tests performed

- **226/226 Django tests passed in50.556s**, with no system-check issues, across `api.test_mobile_facility_booking`, `modules.facilities.test_admin_reservations`, `modules.facilities.test_calendar`, `modules.facilities.test_booking_workflow`, `api.test_facility_form_controls` and `api.test_facility_rental_configuration`. Includes genuine PostgreSQL persistence, weekday/weekend hours, exact interval/capacity validation, fee quantity errors, discount forgery rejection, configured-only deposits, matching admin/mobile totals, price/configuration changes, late overlaps, idempotency, public history and a two-connection race where exactly one request succeeds.
- The initial broader run's two failures were stale expectations in the existing full-page tests: exact shorter Cache-Control and HTML401 instead of the already-documented redirect. Their assertions were corrected without changing authentication source. The concurrency test initially exposed the existing unmanaged-FK test cleanup requirement; it now uses the project's established cascading **test-database-only** cleanup pattern. Neither failed run is reported as a pass.
- The original affected Flutter run passed62/62; after additional Schedule edits in the shared workspace, the latest five-file run passed **63/63 in29s** across `covered_court_booking_test.dart`, `facility_booking_flow_test.dart`, `select_schedule_test.dart`, `facility_details_test.dart`, and `job_order_screen_test.dart`. The additional source/tests were preserved, not reverted. New pricing tests exercise actual Review labels and posted values at320/390px, retained inputs on rejection, immutable uncertain retries and approval refresh. Initial new-test compile/fixture issues and the temporarily undefined shared surface token were resolved before this successful run. Final whole-app `flutter analyze --no-pub` reported **No issues found in9.8s**. The two Review capture tests then passed again in3s, and the refreshed captures were visually inspected.
- Isolated Chrome checks using the actual controls/configuration and the saved read-only Court snapshot: **16/16 checks passed**, no page errors. Verified closed/disabled weekdays, disabled Weekdays/Daily, editable weekend times, Custom preservation, View -> Edit re-enablement and no orange preview. Unsaved fixture hours were changed to09:15/16:45 to prove editing; working hours remain08:00-17:00. An additional fixture check confirmed Add Fee is enabled after Edit.
- Actual Flutter Review captures at320/390px with bundled Inter/Material Icons and the actual existing screen were generated and inspected. Both preserve the layout and show each charge/total; no overflow in those scenarios. An initial320px success-status overflow was fixed by letting the existing status row wrap. Browser evidence is an isolated control harness, not a live admin session.
- Scoped Pyright for `mobile_views.py` and `services/mobile_booking.py`: **0 errors, 0 warnings**. A broader five-file Pyright check still reports **12 diagnostics on10 unchanged source lines** in older room/admin workflow/Decimal typing sections. All10 lines were compared with HEAD and match. No global backend typing pass or diagnostic suppression is claimed.
- Final `flutter build apk --debug --no-pub` succeeded in37.9s: `campushub/build/app/outputs/flutter-apk/app-debug.apk` (189870952bytes). This rebuild includes the final shared Schedule edits and pricing integration. The APK was not installed/launched; the user's current phone/debugging session is preserved. No real booking was created merely for demonstration.
- Live read-only HTTP checks returned200: November7 has the actual08:00-17:00 available window/minimum240minutes; November9 is not bookable because the weekend-only policy applies. No live booking was submitted for these checks. All344 application Python files compiled in memory successfully.
- Evidence: external `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261104/covered-court-integration/`, including guarded `run_backend_tests.py`, `facility-before.json`, `check-schedule.cjs`, `schedule-controls.json`, `weekend-controls.png`, `quote-320.png`, `quote-390.png`, `latest-flutter.log`, `live-availability.json`, `deposit-correction-proposal.json`, `correct_deposit.py`, dry-run, backup, applied-result and `facility-after.json`. The one approved write is complete; do not treat the old proposal as authorization to modify other settings or rerun changes arbitrarily.

Reproduce backend tests through that reviewed local guarded runner; do not run integration fixtures against the working server/database. From `campushub/`, run the five Flutter files listed above and `flutter analyze --no-pub`. No external design-kit gate is claimed; the app's root kit tokens/scripts remain unavailable.

### 8. Remaining limitations / troubleshooting / safe practice

The physical phone has not submitted a real booking against the working server; PostgreSQL creation/approval/history and races were verified in the isolated integration database. Apply the Dart changes through the user's normal hot restart/stop-start; no new native plugin is required. Deployed hosting/static collection is not performed here. The approved saved-data correction is complete, so future Court quotes have no damage deposit unless an authorized administrator later configures an approved requirement. Historical booking/payment/deposit snapshots were preserved.

Immediate-family/Other/custom discount eligibility still needs staff evidence; the mobile app does not grant those discounts from a checkbox. Unknown or legacy equipment/custom fee bases still require a staff quote. Optional quantities are not a newly implemented chair-stock/inventory system; staff approval and availability remain separate. The optional700/hour choice remains supported by Django's existing rate flag; this task does not add a new mobile rate-selection redesign.

Safe exercise: run `test_complete_mobile_quote_matches_staff_and_persists_charge_breakdown` in the isolated test database. Change only its fixture chair quantity20 to21 and update expected chair fee200 to210/total1950 to1960, then rerun and restore the fixture. Compare staff/mobile response fields and confirm only one pending booking exists after a retry. For manual UI practice, use an **unsaved** admin Edit draft to change Saturday hours and cancel it; do not save policy changes or submit fake working bookings for a screenshot.

## Admin-to-mobile availability synchronization - November 4, 2026

This is the current status/refresh contract. It supersedes earlier entries that put a prohibition symbol on every unavailable date or read the displayed month through separate daily HTTP calls. The existing calendar layout, request form, pricing safeguards and saved facility policies remain.

### 1. Cause / reason

The admin and mobile sides were already connected to the same PostgreSQL records. `admin_booking_views.save_schedule()` stores a legacy `Booking` plus the existing `FacilityBookingRequest.details` JSON sidecar. The confirmed gaps were in projection and refresh: only class/maintenance prefixes received specific categories; official use/holds/Other looked like reservations; empty/ordinary restricted dates shared the red symbol; the mobile screen did not reload while open or after returning to it. Classification could depend on database row order when old overlapping blocks existed.

Existing **Add Facility Schedule** accepts structured facility, effective dates, times, all-day and weekly recurrence fields. An uploaded PDF/image is private supporting evidence on that same record; it does not become a second calendar or an automatic timetable parser. No new model, duplicate availability endpoint, attachment parser or fabricated calendar was added.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Added, changed or removed |
| --- | --- | --- |
| `backend/core/modules/facilities/services/mobile_booking.py` | 33 `conflicting_bookings`; 53 `blocking_kind`; 74 `date_restriction`; 87 `slot_status`; 119 `schedule_payload`; 171 `day_availability`; 187 `conflict_description` | Read active pending/approved records; honor all-day metadata and authoritative admin type; deterministic conflict categories; reasons and day summaries; retain actual custom/preset periods. |
| `backend/core/modules/facilities/mobile_views.py` | 81 `availability` | Add a month query to the same GET route, day summary fields, optional authenticated client-eligibility projection and no-store response headers. Existing admin editing exclusion remains permission checked. |
| `backend/core/modules/facilities/services/admin_reservations.py` | 144 conflict-state branch | Treat the new `blocked` category as a real backend conflict and describe its saved schedule type. Web and mobile still share this validator. |
| `campushub/lib/module_app/services/facility_booking_service.dart` | 76 `manilaNow`; 81 `monthSlots`; 143 `dayStatus` | Replace many daily month requests with one existing-route month request; reject missing/malformed/inconsistent responses; use Manila civil dates; distinguish restrictions from schedule blocks. |
| `campushub/lib/module_app/widgets/facilities/booking_schedule_calendar.dart` | 33 Manila today; 148 legend; 216 prohibition branch | Keep borderless calendar/title/arrows/slot styling; gray restricted/past numbers; reserve circle/slash for real `blocked` days; retain green/blue/purple/amber status dots and semantics. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 62 timer; 75 `didChangeDependencies`; 87 lifecycle; 92 `_refreshAvailability`; 193 `dispose`; 706 `RefreshIndicator`; 911 available-row filter | Refresh on route return, app foreground, pull gesture and every 30 seconds while active/idle; revalidate selected exact interval; clear invalid date/time/quote; preserve requestor controllers; show only valid available rows. |
| `backend/core/api/test_mobile_facility_booking.py` | 192 `admin_schedule`; 210-307 synchronization cases | Exercise actual admin create/edit/cancel routes and authenticated mobile reads in isolated PostgreSQL records; update legacy hold/assessment expectations to the explicit blocked category. |
| `campushub/test/select_schedule_test.dart` | 201 Manila check; 225 response validation; 250 polling; 284 requestor retention; 332 route return; month and geometry cases below | Exercise refresh, recovery, civil dates, actual time controls, one month request, gray restrictions and circle placement with isolated responses. |
| `campushub/test/fixtures/facility_booking_fixture.dart` | 28 fake `monthSlots` | Keep overridden test-only rows separate from the production HTTP month integration. |
| `campushub/test/facility_booking_flow_test.dart` | 55 conflict test / `open` cleanup | Verify blocked rows are omitted and final conflict still prevents progress; dispose polling screens after tests. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | This section / newest context entry | Explain inputs, outputs, data flow, evidence, remaining limits and safe practice. |

Inspected and reused without model/route/UI duplication: `api/models.py:618` (`Booking`), `:675` (`FacilityBookingRequest`), `api/views.py:1797` (`_serialize_booking_event`), `admin_booking_views.py:219` (`save_schedule`) and `:290` (`schedule_update`), `services/schedules.py:49` (`validate_schedule`), existing `services/calendar.py`, schedule form/JavaScript, and `core/settings.py:203` (`TIME_ZONE='Asia/Manila'`, `USE_TZ=True`). Line anchors are the reliable lookup when earlier sections become historical.

### 3. Changes made / status rules

| Condition | API day status | Calendar behavior |
| --- | --- | --- |
| At least one eligible remaining period | `available` | Green dot; selectable; show only its valid available time rows. |
| Past, weekend-only weekday, closed/unconfigured operating day, inactive facility, ineligible signed-in client or no period meeting the saved minimum | `not_bookable` | Gray number, disabled, no prohibition circle. |
| No available period and an active reservation occupies applicable periods | `reserved` | Blue dot, disabled. Existing pending reservations also retain their conflict hold. |
| No available period and maintenance applies | `maintenance` | Purple dot, disabled. |
| No available period and class/academic schedule applies | `class` | Amber dot, disabled. |
| No available period and official use, administrative hold or another actual blocking schedule applies | `blocked` | Red prohibition circle/slash around the number, disabled. |
| Missing/failed API response | Not converted into a closed date | Unknown/disabled calendar, explicit error and Retry Schedule action. |

Partial schedules take their exact stored interval. **Other** currently has no nonblocking-event toggle in the admin form: it is a block for its saved selected times, or the whole day only when saved as all-day. It is never automatically expanded to an entire day merely because its type is Other. Effective dates are inclusive; weekly occurrences use the stored Python weekday indices (Monday=0). No duplicate occurrence records are created.

When several categories cover a fully unbookable day, priority is maintenance, class, block, then reservation; the response also lists all relevant `blocking_statuses`. Any eligible available period takes priority over those categories. Ordinary policy restrictions take priority over schedule symbols, so a restricted weekday remains gray even if an admin record exists on it.

### 4. How it works / functions and data flow

1. Facilities Admin saves the existing structured form through `/api/bookings/create/`, or edits/cancels through `/api/facility-schedules/<id>/update/`. The current transaction locks the facility and writes `Booking` plus its JSON sidecar. Cancel preserves history with `status='cancelled'`.
2. `conflicting_bookings(facility, day, start, end)` queries the same facility's active pending/approved records, inclusive effective dates, matching recurrence weekdays, interval overlaps, all-day metadata and stays. Cancelled/rejected/completed rows do not occupy a future booking period. The existing final submission lock and revalidation remain mandatory.
3. `blocking_kind(booking)` reads the saved JSON schedule type first and falls back to legacy purpose prefixes. `slot_status()` applies current Manila time, facility policies, configured hours, deterministic overlap categories and minimum duration. `schedule_payload()` retains presets; custom hours split only at actual conflict/current-time boundaries and keep unoccupied portions.
4. `day_availability()` returns date, status, safe reason, complete public slot rows, valid `available_slots` and blocking statuses. Public rows expose categories/times, not client identities, private titles, attachment contents or booking IDs. A signed-in ineligible client receives no available rows; quote/create enforce eligibility independently.
5. Flutter `monthSlots()` requests the displayed month, checks every eligible date exists and its server status agrees with its slots, and rejects broken responses as API errors. `dayStatus()` uses only loaded server rows; `manilaNow()` converts the instant to Manila's fixed UTC+8 civil date, regardless of phone timezone. The prior UI booking-range boundary remains unchanged.
6. `_refreshAvailability()` updates the displayed month without replacing the form controllers. Presets require the same exact start/end; custom choices must remain inside a current free window and meet its current minimum. An invalid selection loses its quote and returns to Schedule. Valid selections remain. Request versions prevent older month/day reads from overwriting newer choices. Polling stops at disposal and avoids background/covered routes, busy submissions and open time dialogs. A response cannot replace the submitted-success screen.

### 5. Backend / API behavior and annotated example

Same existing public availability URL; daily requests remain supported for selection/revalidation and admin editing:

```text
GET /api/mobile/facilities/<facility-id>/availability/?date=2026-11-07
GET /api/mobile/facilities/<facility-id>/availability/?month=2026-11
```

The month response contains `month`, `timezone: "Asia/Manila"` and `days`. Each day includes `date`, `status`, `reason`, `slots`, `available_slots`, and `blocking_statuses`. Each blocked row adds safe `blocking_types` and a reason. `Cache-Control: private, no-store` prevents stale HTTP reuse. Requests supplying a bearer token validate it and project that client's eligibility; the existing public/admin GET usage remains supported. No admin-only event details become public. Invalid month parameters return400, not500.

Illustrative data flow, **not a production record inserted by this task**: operating hours08:00-17:00, minimum4h, class08:00-12:00 → `slots` contains the class and a remaining available12:00-17:00 period; `available_slots` contains only12:00-17:00; day status is `available`. Mobile displays one selectable remaining period. A request10:00-14:00 still fails backend overlap validation. If an official hold then occupies12:00-17:00, no eligible slot remains. Removing/cancelling either block changes the next API response, which mobile fetches on refresh.

The actual live Covered Court response was checked read-only: **November6,2026** is `not_bookable` with the saved weekend-only reason; **November7** is `available`,08:00-17:00 with saved minimum240minutes. All30 date summaries agreed with their available-slot lists. No working schedule was added just to demonstrate a colored dot.

### 6. Database / migration impact

No schema or migrations; no working facility, schedule, reservation, pricing rule, user, or attachment record changed. Existing admin create/update/cancel APIs and PostgreSQL storage remain authoritative. Integration mutations run only in the disposable local PostgreSQL test database created/destroyed by the guarded runner documented below. Live verification performs GETs only. Existing full mobile deposit/fee quote safeguards remain in place.

### 7. Tests performed / verification

- Final backend run: **67 tests passed in10.181s** across `api.test_mobile_facility_booking`, `modules.facilities.test_admin_reservations`, and `modules.facilities.test_calendar`; Django system check clean; disposable database destroyed. Six added tests cover every schedule type, all-day maintenance, partial classes/official/Other, exact preset overlap, actual admin edit/cancel, deletion visibility, recurrence boundaries, facility isolation, real reservation double-booking prevention, status precedence, authenticated eligibility, invalid months and Manila midnight. Admin cancellation is the production removal workflow; physical deletion is checked only with isolated test records.
- Final Flutter run: **54 tests passed in21s** across Schedule, booking flow and Facility Details. Verification includes real time-dialog input, 280/320/390/768dp layouts and large text, gray restricted date numbers versus block circles, one month request with bearer, malformed responses, polling/route return/foreground refresh, error/retry, invalidated selection and requestor-field retention.
- Whole-app `flutter analyze --no-pub`: no issues in18.8s. Initial lint findings were fixed. Initial new-test failures were harness issues (a deliberately blocked fake initial day and an invalid direct paused→resumed lifecycle transition); the test now selects a known isolated open day and uses the real inactive→resumed transition. No production behavior was weakened to satisfy them.
- Thirteen actual Flutter widget renders were generated; the390dp status calendar and initial saved-weekend calendar were visually inspected. Ordinary weekday numbers are gray, actual blocked day circles and colored status dots remain, and the existing centered title/arrows/borderless layout are preserved. These captures use isolated responses, not newly inserted production events. Native Flutter tests/renders apply here; HTML-only design-kit browser gates do not validate a Dart widget screen. No contrast/compliance score or full-release acceptance claim is made.
- Read-only running-Django month request: HTTP200,30 real dates, Asia/Manila and no-store headers verified, all day/available-slot summaries consistent. Evidence: `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261104/schedule-admin-sync-20261104/live-month.json`; renders in the sibling `renders/` folder.
- Final debug APK built in28.1s and installed in place after the user said continue. Installation checks confirmed no focused text editor and verified that the existing saved account/session values were retained, comparing hashes without printing their contents. The first retention guard stopped before installation because it looked for an outdated preference key; the existing key was located and the corrected guard passed. No login or booking record changed, app launch was not forced, and no physical-device calendar acceptance check is claimed. `phone-install.json` in the same evidence folder records successful installation and saved-user/token retention.

```powershell
# From campushub:
flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/facility_details_test.dart
flutter analyze --no-pub
flutter build apk --debug --no-pub
# From root: uniquely named disposable LOCAL PostgreSQL test DB only.
backend/core/venv/Scripts/python.exe -B C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261104/schedule-web-parity-20261104/run_backend_tests.py api.test_mobile_facility_booking modules.facilities.test_admin_reservations modules.facilities.test_calendar
```

### 8. Remaining limitations / troubleshooting / safe practice

Admin changes appear on route return, foreground, pull refresh, or within the next30-second active/idle poll; this is bounded polling, not a new websocket service. Busy requests and open time dialogs defer background refresh, and backend quote/submission still catches a new conflict immediately. The new app and backend must be deployed together for the month response; an older server produces a visible retryable API error. An uploaded attachment alone does not parse timetable dates/times. No physical-phone end-to-end admin editing/booking submission or full project suite is claimed.

Covered Court retains weekend closures, the four-hour minimum and its existing Facilities Admin requirement for full deposit/additional-fee pricing. An empty list can correctly mean closed/unconfigured hours; a network failure instead shows an error. For unexpected colors, inspect the day's `status`, `reason`, `blocking_statuses`, `slots` and saved facility policy before changing data. Never make a weekday available simply to turn a dot green.

Safe learning exercise: in an isolated test database, find `test_admin_partial_blocks_preserve_valid_custom_and_preset_periods` and change the class end from12:00 to11:00; update its expected free start to11:00 and rerun only that test using the guarded runner. Then restore the test fixture. Verify a longer remaining window becomes available while an overlapping quote remains rejected. For read-only production practice, compare one existing weekday/weekend API response with the Flutter calendar and pull down to refresh; do not add dummy working schedules.

## Schedule: circle over numbers and shared web time validation - November 4, 2026

This is the current schedule behavior. It restores the unavailable circle/slash **over the number**, superseding the below-number marker entry that follows. It also replaces the whole-operating-window-only restriction for facilities that use custom times on the web. Existing saved facility policies remain authoritative.

### 1. Cause / reason

Comparison with the actual web implementation found three confirmed differences. Web reservations use `admin_reservations.reservation_schedule()` to accept a start/end interval inside saved operating hours when no preset slots exist. Mobile instead required exact equality with the complete configured operating window. Mobile availability also assigned one status to that whole window, so a partial class/reservation could hide the remainder of an otherwise open day. Finally, the mobile Schedule step attempted a full price quote before advancing; the real Covered Court has deposits/additional charges that the existing mobile quote intentionally sends to Facilities Admin.

The date numbers and saved operating hours were already real. No production mock data or fabricated booking record was found. Covered Court remains weekend-only, 08:00-17:00, with a saved minimum duration of **4 hours**. The fix changes the projection, time controls and schedule validation; it does not make closed weekdays available or bypass pricing guards.

### 2. Exact files changed / current lines and code anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `backend/core/modules/facilities/services/mobile_booking.py` | 53 `slot_status`; 87 `schedule_payload`; 138 `rental_quote` | Preserve actual blocking categories, split custom operating periods at real conflict/current-time boundaries, publish custom/minimum metadata, and call the web schedule validator for mobile quotes. |
| `backend/core/modules/facilities/mobile_views.py` | 114 `quote`; 123 `availability_only` | Add an authenticated schedule-only mode to the existing quote endpoint, matching the web preview's availability stage. |
| `backend/core/api/test_mobile_facility_booking.py` | 196 partial-window regression; 211 exact-choice persistence; 227 minimum/new conflict; 254 schedule-only/full-pricing guard | Seven added regressions for web/mobile scheduling parity, recurrence/all-day blocks, elapsed opening time, presets and authentication/pricing safety. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 48 `_window`; 189 `_pickTime`; 297 `_timeChoices`; 403 `_next` schedule-only flag | Keep the selected free window separate from the user's chosen interval, add editable times with real bounds/minimum checks, and separate Schedule availability from the subsequent full quote. |
| `campushub/lib/module_app/widgets/facilities/booking_schedule_calendar.dart` | 216 `foregroundPainter`; 311 `ScheduleProhibitionPainter` | Restore the unavailable circle/slash around the actual date number; remove the separate below-number mark. |
| `campushub/test/select_schedule_test.dart` | 64 `CustomCalendarService`; 201 custom interval checks; 280 minimum-duration case; 572 circle geometry | Test custom time editing and exact schedule requests at390dp/100% and280dp/200%, preset behavior and restored circle geometry. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | This section / newest context entry | Persist confirmed causes, source/data flow, actual verification and limits. |

The web's `admin_reservations.py`, calendar UI, permissions, pricing configuration and operating-hours editor were inspected and reused, not rewritten.

### 3. Changes made

Unavailable day numbers are again enclosed/crossed by the red prohibition stroke. For a facility with real preset slots, the existing slot choices remain exact and no custom editor appears. For a facility without presets, the backend returns actual remaining periods. After selecting an available period, mobile displays **Start time** and **End time** controls and the saved minimum duration. Editing a time retains the chosen period's selection but changes the exact interval sent to Django. No hourly grid, default duration or alternative booking record is invented.

The time dialog uses explicit 24-hour input while the surrounding mobile page retains its normal time labels. Narrow dialogs reduce their horizontal padding and cap only their own text scale at1.3; the underlying page retains the full requested text scale. Geometry tests verify that both the minute field and OK action fit before interaction, so horizontal scrolling cannot hide a clipped action.

### 4. How it works / functions, inputs, outputs and data flow

`configured_slots(facility, day)` continues to read the saved weekly/preset schedule. For custom-time facilities, `schedule_payload()` starts with those real opening/closing boundaries and adds only overlapping booking/schedule start/end boundaries plus the next valid minute on the current day. It reuses `conflicting_bookings()` and `slot_status()`, the same core helpers used by web reservations. The resulting public rows contain start/end/label/status without private event titles or client identities. Cancelled/rejected blocks are excluded by the existing query; recurring and all-day blocks retain their actual coverage. Blocking categories are resolved before checking the minimum rental duration so a one-hour class is still displayed as a class even when the facility requires a four-hour rental. It never becomes selectable.

Each custom row adds `time_selection: "custom"` and the saved `minimum_duration_minutes`. Presets keep the original row contract. The existing Flutter service passes these server fields through without importing test fixtures. The existing initial-date logic still chooses a real available day and month navigation still clears selections.

`_window` holds the original selected free period; `_slot` holds the user's chosen interval. `_pickTime(start)` opens the appropriate input, then rejects old completions after date/window changes, start>=end, outside-window choices and intervals shorter than the server's minimum. A valid edit clears the stale quote. `_next()` at Schedule sends the exact date/start/end with `availability_only: true`; after Details it requests the existing full quote without that flag. Final submission retains full pricing and locking/revalidation.

```jsonc
// Actual Covered Court availability on 2026-11-07, from the saved policy.
{
  "start": "08:00", "end": "17:00",
  "label": "08:00 AM - 05:00 PM", "status": "available",
  "time_selection": "custom", "minimum_duration_minutes": 240
}
```

Annotated actual example: choose that period, set **10:00-14:00**, and continue. The existing authenticated quote route checks this four-hour interval through the web's `reservation_schedule(..., check_capacity=False)` and returns `available: true` with the exact date/times, without fabricating a price. The actual running server returned HTTP200 for this request and agreed with the web validator. Choosing fewer than four hours fails. A new conflict still blocks the final quote/submission. Selecting a preset facility instead preserves its exact slot-only rule.

`rental_quote()` imports the web validator locally to avoid an import cycle, then retains the existing mobile price calculation and its complete-quote safeguards. The schedule-only endpoint performs the same bearer and client-eligibility checks before validation. Its response contains no amount, and a client cannot use its flag to bypass final pricing.

### 5. Backend / API behavior

The existing daily availability endpoint adds custom/minimum metadata only for non-preset facilities and can return several real free/blocked intervals instead of marking the whole day occupied. The existing mobile quote POST accepts optional boolean `availability_only: true`; normal quote responses retain their pricing behavior. Both Schedule checks and full quotes now use the same schedule validator as the web. Final booking creation still recalculates the full quote under the existing facility lock and enforces authentication, eligibility, capacity, conflicts and idempotency. No admin-only calendar endpoint, private schedule description, new route, seller permission or FastAPI logic was exposed.

### 6. Database / migration impact

No models, migrations, working facilities, operating policies, schedules or booking records were changed. Django regressions ran against a uniquely named disposable **local PostgreSQL test database**, using the existing unmanaged-table bootstrap, and that database was destroyed afterwards. Live checks performed GETs, pure validator calls and one schedule-only POST; no actual reservation was submitted. Android installation was performed in place with saved user/token values verified unchanged without printing them.

### 7. Tests performed

- **61 Django regressions passed in5.621s** across `api.test_mobile_facility_booking`, `modules.facilities.test_admin_reservations` and `modules.facilities.test_calendar`; system checks reported no issues. Coverage includes partial/free windows, real class status under a minimum duration, exact custom persistence in isolated records, changed conflicts, minimums, recurring/all-day blocks, current-day remaining time, preset restrictions and a schedule-only request that cannot bypass full pricing/submission/authentication.
- **49 Flutter tests passed in15s** across Schedule, booking flow and Facility Details. They exercise real time-dialog interactions, invalid bounds, exact 24-hour requests, the minimum-duration guard, preset behavior, stale responses and circle geometry at four viewports/scales. Whole-app analysis reported **no issues in15.9s**. Dart formatting and changed-file whitespace checks completed.
- Thirteen actual Flutter captures were generated in `renders/`, using isolated responses. Custom controls at390dp, the280dp/200% time dialog and the restored circle calendar were inspected. Initial QA found lazy-list test lookup issues and a real narrow-dialog horizontal-clipping problem; the harness now scrolls to rows, and the dialog uses24-hour input/padding plus explicit action/field bounds checks. These are verified fixes, not ignored test warnings.
- Read-only live API checks matched saved Django data for Covered Court. `actual-custom-quote.json` records **2026-11-07,10:00-14:00**, web duration4h, saved minimum240min, HTTP200 `available: true` and no booking submission. The same actual facility's full mobile pricing still requires Facilities Admin for its configured deposits/charges; that safeguard was not bypassed.
- Debug APK built in39.0s and installed over the existing app. `phone-install.json` confirms saved user/token retention and no forced app launch. No physical-phone calendar interaction or live completed booking is claimed.

Evidence stays outside the workspace in `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261104/schedule-web-parity-20261104/` (`renders/`, `live-availability.json`, `actual-custom-quote.json`, `phone-install.json`, local guarded `run_backend_tests.py`). The runner pins the project root, asserts a local PostgreSQL host/port and the unique test database before its legacy-schema bootstrap; do not substitute a production database or execute the bootstrap against working tables.

```powershell
# From campushub:
flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/facility_details_test.dart
flutter analyze --no-pub
flutter build apk --debug --no-pub
# From the project root, this session's guarded disposable test runner:
backend/core/venv/Scripts/python.exe -B C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261104/schedule-web-parity-20261104/run_backend_tests.py api.test_mobile_facility_booking modules.facilities.test_admin_reservations modules.facilities.test_calendar
```

### 8. Remaining limitations / troubleshooting / safe practice

The time editor appears **after selecting a real available period** whose API row declares custom selection. If the saved policy has only one operating window, that real window can still be one row; use its Start/End controls rather than expecting invented hourly slots. Presets remain fixed. For Covered Court, the four-hour minimum, weekend closures and configured deposits/charges remain; a full quote with those charges still requires Facilities Admin under the existing mobile pricing workflow. This task implements schedule/time parity, not new fee/discount selection or payment logic.

Older mobile builds ignore the additive row fields and cannot show the new controls; reopen the updated installed app. Unknown/failed availability stays disabled, and availability can change after loading. Very narrow/large-text shared step labels can still wrap; only the new time dialog/control layout was adapted here. No full-project, release or physical-device booking acceptance suite is claimed.

Safe exercise: open Covered Court, select a genuinely available weekend period, tap Start time and End time, and enter10:00/14:00. Confirm the displayed four-hour minimum and that changing the end to12:00 is rejected. Return using Back without submitting a reservation. Inspect the read-only availability response and compare its custom/minimum fields with `_window` and `_slot`; never change saved facility rules or create dummy bookings to make dates green.

## Select Schedule: actual initial period and unavailable marker below dates - November 4, 2026

This supersedes only the earlier date-number prohibition overlay and the closed-today initial selection behavior. Existing month changes still clear date/time selections; other booking steps, permissions, quotes and submission remain.

### 1. Cause / reason

The calendar was already reading actual Django availability, not placeholder dates. Read-only inspection confirmed that **Covered Court** (`CAMFACIL20261013F13A`) has saved `weekend_only=true`, Monday-Friday closed, and Saturday/Sunday operating hours **08:00-17:00**. The actual running daily API returned no slots for November4/9 and one available **08:00 AM - 05:00 PM** period for November7. Those weekend/weekday indicators were therefore correct and were not replaced with invented availability.

The confirmed presentation issue was that `_loadMonth(initialDate: today)` selected only today when today was available. On a closed weekday it left `_date=null` even after loading real future open dates, so the Available Time Slots area showed only `Choose an available date.` The user also requested moving the prohibition mark below the unavailable day number rather than crossing it.

### 2. Exact files changed / current lines and anchors

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/services/facility_booking_service.dart` | 135 `firstAvailableDate` | Select the earliest loaded date on/after the initial date with an actually valid available period. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 108 `initialSelection`; 443 weekend instruction | On first load/retry, show the next actual open date and its loaded periods if today is closed. Explain the saved weekend-only rule when present. |
| `campushub/lib/module_app/widgets/facilities/booking_schedule_calendar.dart` | 247 marker height; 251 `schedule-prohibited`; 311 `ScheduleProhibitionPainter` | Render an 11px prohibition marker below the number, aligned with other status markers; remove the number overlay. |
| `campushub/test/select_schedule_test.dart` | 155 initial selection test; 183 HTTP-backed widget regression; 412 marker geometry checks | Verify sorted real-response selection, closed/past/reserved/malformed exclusion, the initial period with no automatic submission, and marker placement at four viewport/text combinations. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | This section / latest schedule entry | Record confirmed cause, actual backend evidence, implementation and safe verification. |

### 3. Changes made

First opening now selects the earliest bookable date from the loaded current-month responses and displays its real time periods. Today still wins when it has a valid open period. The time period itself is **not** automatically selected: the user must choose one before Next becomes enabled. Month navigation keeps its existing cleared selection behavior. An empty/failed month never receives a fake fallback date or time.

The Select Date instruction becomes **Weekend bookings only. Choose an available date.** only when the selected facility's saved `workflowConfig['weekend_only']` is true. Other facilities retain their existing instruction. Unavailable numbers remain readable with a separate red prohibition marker beneath them; available/reserved/maintenance/class indicators and selected navy/gold styling remain.

### 4. How it works / functions, inputs, outputs and data flow

The unchanged Django flow reads `Facility.workflow_config` and stored schedule/booking records. `configured_slots(facility, day)` applies saved operating hours; `schedule_payload(facility, day)` supplies real start/end/label/status values through `GET /api/mobile/facilities/<id>/availability/?date=YYYY-MM-DD`. The mobile `monthSlots()` still makes at most four daily requests concurrently and never imports test fixtures.

`firstAvailableDate(days, onOrAfter: initialDate)` takes that date-keyed response map, excludes dates before the supplied calendar date and any day without a valid `available` period, sorts the remaining keys and returns the earliest date or null. It uses the existing `isAvailableSlot()` validation for real HH:MM intervals. `_loadMonth()` invokes it only when an initial date is supplied, copies the chosen response into `_slots`, and leaves `_slot` null. Its original request-version guard still discards stale results.

```dart
// The dates and periods have already come from the existing daily API.
final initialSelection = initialDate == null
    ? null
    : FacilityBookingService.firstAvailableDate(days, onOrAfter: initialDate);
// No time is selected and no quote/booking is submitted by this default.
```

Annotated actual example: November4 returns `slots: []`; November7 returns the saved available `08:00`-`17:00` period. First opening shows **Nov7,2026 (Saturday)** and that period. Choosing the period enables the existing Next action, whose server quote still rechecks current availability. Moving to another month clears this selection. This approach exposes existing data immediately without changing the facility policy or adding another endpoint.

### 5. Backend / API behavior

No backend, endpoint, payload, permission or conflict/quote logic changed. The live API was checked using three read-only HTTP GETs, and each response matched the existing Django `schedule_payload()` result from the configured database. Weekday closures are real saved policy, not a reason to enable those dates. Tests use isolated HTTP/service fixtures only; they are not production records.

### 6. Database / migration impact

None. No facility configuration, schedule, booking, quote record, model or migration was changed. Verification created no real booking and submitted no live quote. The Android update replaced the installed package in place; the saved user and login token were verified unchanged without printing or saving their values.

### 7. Tests performed

- **46 Flutter tests passed in10s** across `select_schedule_test.dart`, `facility_booking_flow_test.dart` and `facility_details_test.dart`.
- Whole-app `flutter analyze --no-pub` reported **no issues in14.5s**. Dart formatting and scoped whitespace checks completed.
- Nine actual widget PNGs were rendered at280dp/200%,320dp,390dp and768dp/dark context, including the initial weekend-response state. The initial390dp and280dp/200% calendar captures were visually inspected. These are real Flutter widget renders with isolated responses, not physical-phone or live-DB screenshots.
- The actual running Django API returned HTTP200 and matched saved schedule data for **2026-11-04**, **2026-11-07** and **2026-11-09**. `live-availability.json` stores only public facility/policy/period data.
- Debug APK build completed in22.6s and installed successfully with `adb install -r`. The saved user and token matched before/after the update. CampusHub was not launched by this check, leaving the user's current phone app in use; no physical-phone calendar screenshot or live booking acceptance test is claimed.

Evidence: `C:/Users/leste/Desktop/CAMPUSHUB-artifacts-20261104/select-schedule-real-20261104/`, including `renders/`, `live-availability.json` and `phone-install.json`.

```powershell
# Run from campushub; captures are optional and stay outside the repository.
$env:SELECT_SCHEDULE_REVIEW_DIR = 'C:\Users\leste\Desktop\CAMPUSHUB-artifacts-20261104\select-schedule-real-20261104\renders'
flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/facility_details_test.dart
flutter analyze --no-pub
flutter build apk --debug --no-pub
```

### 8. Remaining limitations / troubleshooting / safe practice

Only dates in the loaded month can be defaulted. If that month has no real open periods, the existing honest empty state remains; the user can move to another month. Month navigation intentionally clears both selections. Availability may change after loading, so date taps and the existing backend quote/submission still revalidate. At280dp with200% text, the existing shared step labels and long month title can wrap awkwardly; this focused change does not redesign shared booking typography. No new Django suite, full-project suite, real booking submission or physical-phone calendar render is claimed.

Safe exercise: reopen Covered Court's Schedule page on a weekday. Confirm the weekend restriction text, the next actual available date and its saved period. Confirm Next remains disabled until you choose that period, then leave with Back without submitting. Check that unavailable marks sit beneath numbers. To understand a closed day, inspect its read-only availability GET and the saved operating hours; do not change a booking policy merely to make a calendar date green.

## Mobile Select Schedule: live calendar and clean presentation - November 4, 2026

This update changes only the Schedule step of the existing slot-booking screen. Booking Details, Review, Submit, the automatic Job Order process and facility/service-specific workflows retain their existing behavior.

### 1. Cause / reason

The existing stock `CalendarDatePicker` allowed choosing dates without displaying the backend's day availability. It loaded slots only for the chosen day. The legend wrapped beneath the Available Time Slots heading, followed by a separate Selected Date section. The shared booking shell supplied a boxed chevron, header/footer separators and connecting step lines. Those confirmed implementation details did not match the requested plain white calendar, inline day indicators, single-row legend and Add Product-style back arrow. Facility identity/status/location were already absent from this Schedule body and remain absent.

### 2. Exact files changed / current lines and anchors

Paths are relative to the project root; named anchors remain searchable if later edits move lines.

| File | Current line / anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart` | 87 `_loadMonth`; 128 `_changeMonth`; 134 `_loadSlots`; 327 `schedulePresentation`; 472 calendar; 530 Available Time Slots | Replace only the Schedule body, manage monthly/day loading and reset/stale-response state, keep chosen date as the slot-heading subtitle, and retain the existing quote/submission flow. |
| `campushub/lib/module_app/widgets/facilities/booking_schedule_calendar.dart` | 7 schedule font/color constants; 12 `BookingScheduleCalendar`; 143 `schedule-legend`; 192 `FittedBox`; 310 `ScheduleProhibitionPainter` | New supporting widget within the existing facilities module: borderless month grid, centered month/year, disabled/semantic date controls, actual status markers, selected navy circle/gold dot and horizontal legend. The foreground painter crosses the actual unavailable date number. |
| `campushub/lib/module_app/widgets/facilities/booking_widgets.dart` | 211 `schedulePresentation` default; 268 leading; 313 header shape; 331 footer decoration; 357 `BookingButton`; 500 `BookingSteps` | Add opt-in Schedule appearance and font parameters, preserving all defaults. Only step 0 uses the standard `BackButton`, no separators/shadow or step connectors, and Montserrat. Variable-font weights are explicit so the bundled face renders correctly. |
| `campushub/lib/module_app/services/facility_booking_service.dart` | 77 `monthSlots`; 110 `isAvailableSlot`; 125 `dayStatus` | Read existing daily availability with at most four requests in flight per month load; derive a read-only day presentation and reject malformed/open-with-invalid-time slots. No endpoint is added. |
| `campushub/test/select_schedule_test.dart` | 150 daily-route/bearer/concurrency test; 236 responsive integration; 389 past/malformed; 416 empty; 439 partial-day; error/stale tests below | Twelve focused tests for actual request construction, loading failure/cancellation, colors, date-number overlays, month reset, valid selection, stale revalidation and responsive geometry. Optional actual-widget captures use an external output directory. |
| `campushub/test/facility_details_test.dart` | 645 slot-read regression; 661 current-month/first-batch calculation | Update the former one-day read expectation for bounded monthly reads. Keep zero schedule calls before entering booking, retry/error behavior and zero submissions. |
| `docs/booking-module-chatgpt-context.md`; `CAMPUSHUB_CONTEXT.md` | This report / newest Select Schedule entry | Record current behavior, data flow, actual checks and safe practice. |

### 3. Changes made

Select Schedule keeps its centered header and four Schedule / Details / Review / Submit steps on white. The back arrow is the same native Flutter `BackButton` used by Add Product, with no enclosing box. The header/footer gray separators and connecting step lines are removed only here. The calendar has no outer card, border or tinted surface. Navy is `#1A1851`; this explicitly requested screen uses gold `#FCB316` and bundled Montserrat, without changing other screens' fonts.

Available date numbers are navy with green dots. Unavailable date numbers sit inside thin red circles with diagonal strokes across the number. Reserved, Maintenance and Class Schedule use blue, purple and amber dots. The selected available date is white on navy with a small gold dot. Past dates and unknown/loading dates are disabled and are not represented as confirmed availability. The selected double-digit number scales down only if needed to fit its circle at extreme narrow/large-text settings.

One horizontally scrollable legend follows the dates. There is no Facility Status heading, legend box/background or separate Selected Date section. Available Time Slots follows with the actual chosen date, including year, as a small subtitle. Existing backend slot labels render in full-width white rows. The selected row has a navy border and check; blocked rows stay disabled and retain their actual status explanation. Next: Booking Details stays fixed at the bottom and is unavailable until a valid date and open slot are selected.

### 4. How it works / functions, inputs, outputs and data flow

`FacilityBookingScreen` receives the existing facility and booking service. `_loadMonth()` passes the visible month and a generation/lifecycle predicate to `monthSlots(facilityId, month)`. The service calls the unchanged `slots(facilityId, date)` method for each non-past date within the existing picker range. Four workers bound concurrency; one failed read produces a retryable month error rather than green dates. Month changes invalidate older loads, clear the selected date/slot/quote and stop scheduling obsolete requests. Responses already in flight may finish, but version checks prevent them restoring old state.

The result is `Map<DateTime, List<Map<String, dynamic>>>`, containing actual daily slot responses. `dayStatus(rows)` uses those responses only. A date with at least one valid open slot is Available; if all slots are blocked, the displayed status prioritizes Maintenance, Class Schedule, Reserved, then Unavailable. Thus a partially occupied day can still offer its remaining legitimate open periods, while its conflicting slot rows remain disabled. A missing response is Unknown, not Available. An empty configured slot list is unavailable.

`BookingScheduleCalendar` receives this map, visible month, selected date and callbacks. It does not call an API or create bookings. Tapping an available date invokes `_loadSlots()` to obtain a fresh daily response, clears the previous time selection and updates the day's status. A newly reserved date is disabled and its selection removed. Today is initially selected only if its successfully loaded response contains an open slot; Next still requires an explicit time-slot selection. Month navigation never retains the previous selection, including when returning to that month.

`isAvailableSlot` requires the backend's `available` status plus valid increasing `HH:mm` start/end values. The existing Next action requests the original quote endpoint and the existing final Submit uses the same booking endpoint and idempotency key. A Schedule quote failure clears the slot and rereads the selected date without inventing success. The server remains authoritative for timing, conflicts, permissions, pricing and submission.

```dart
// Existing authenticated daily API, not a synthetic/demo calendar.
final days = await service.monthSlots(facility.id, visibleMonth);
final status = FacilityBookingService.dayStatus(days[chosenDate]);
// Only an actually open period can enable the existing Next action.
final selectable = FacilityBookingService.isAvailableSlot(actualSlot);
```

This approach avoids a new endpoint or duplicate booking system. Shared shell/button/step options default to their previous values, and are enabled only while `_step == 0`.

### 5. Backend / API behavior

No Django, DRF, route, permission, conflict rule, approval, Job Order, billing or audit implementation changed. The real requests still use `/api/mobile/facilities/<id>/availability/?date=YYYY-MM-DD`, the existing bearer transport, original quote route and original booking POST. The backend's current operating hours, minimum duration, past-time checks and reserved/class/maintenance calculations remain authoritative. No calendar GET creates a booking or runs analysis. A comparison against the preceding cleanup snapshot confirms all 77 relevant Facilities/backend-contract/other-booking-screen files match. Two unrelated Marketplace template/CSS changes were observed in the wider old snapshot comparison and left untouched.

### 6. Database / migration impact

None. No models, migrations, settings, working bookings, schedules, orders or approval records were edited or created. Flutter checks use isolated service/HTTP responses and local test preferences. No working booking submission or Django maintenance command was used for verification.

### 7. Tests performed

- **44 Flutter tests passed in 8 seconds** across `select_schedule_test.dart`, `facility_booking_flow_test.dart` and `facility_details_test.dart`. Coverage includes the existing full Details/Review/Submit workflow, conflict rejection, field retention and exactly one submission; monthly actual-route/bearer construction, four-request bound, no past reads, failures/cancellation, malformed-slot rejection, all day statuses, unavailable-number foreground painting, partial-day open/blocked rows, month resets, stale daily responses and date revalidation.
- Responsive actual-widget checks cover **280dp at 200% text, 320dp, 390dp and 768dp**, with a dark parent theme in the tablet scenario while retaining this approved white screen. Checks verify centered month title, no separator border, unboxed back arrow, one horizontal legend, correct marker colors, selected navy row/check, double-digit containment and no Flutter layout exceptions. **Eight actual widget renders** were produced; phone and extreme narrow/large-text calendar/selected-slot captures were visually inspected.
- Final whole-app `flutter analyze --no-pub`: **no issues in 6.8 seconds**. Dart formatting and scoped `git diff --check` passed; Git emitted only its normal existing line-ending conversion notice for the service file. The 77 relevant protected-file hashes matched.
- Initial runs exposed obsolete one-day request-count expectations and lazy-list test finders for offscreen large-text elements. They were updated for the actual new contract. Visual inspection caught the variable font's thin default weight and selected double-digit crowding; explicit weight axes and measured fit corrected them before the final passing run. No unrelated screen was restyled to satisfy a test.

Evidence remains outside the cleaned project: `C:\Users\leste\Desktop\CAMPUSHUB-artifacts-20261104\select-schedule-20261104\` contains `tests.log`, `analyze.log`, `backend-preservation.json` and `renders/`.

Reproduce from `campushub`:

```powershell
flutter test --no-pub test/select_schedule_test.dart test/facility_booking_flow_test.dart test/facility_details_test.dart
flutter analyze --no-pub
# Optional: set SELECT_SCHEDULE_REVIEW_DIR to an external folder before the tests.
```

### 8. Remaining limitations / troubleshooting / safe practice

The current API exposes availability one day at a time, so a full future month requires up to 31 GETs, bounded to four concurrent reads per month load. This is intentionally explicit; there is no invented monthly snapshot or extra backend route. Slow networks can delay the month, and requests already sent cannot be revoked by leaving the page. Unknown/error states remain disabled, and Retry loads current data. A future bulk API would be separate work.

Verification uses actual Flutter rendering with isolated service/HTTP fixtures, not an installed physical device or a signed-in deployed acceptance session. No new Django regression or full-project suite is claimed. At narrow widths and large text the page scrolls vertically and the legend horizontally. The existing device-date picker boundary is retained; the backend independently rejects elapsed times and new conflicts.

Safe exercise: open an existing slot-bookable facility and select Schedule. Confirm the plain back arrow and no gray separator lines, then inspect the live statuses and swipe the legend. Choose an actually open date/time, change months and verify Next becomes disabled and both selections clear. Return and select again; stop before final Submit when reviewing working data. Run the isolated conflict/revalidation tests for blocked or changed availability instead of creating real conflicting reservations. If every date is disabled, inspect the actual API error/operating configuration and retry; do not add fake dates or bypass server checks.

## Remove external signature progress and setup text — October 27, 2026

1. **Cause / reason:** the shared signature toolbar rendered a signed-count/revision paragraph and copied the server's setup notice below the official preview. The user requested removal of both visible lines. This supersedes earlier guidance to display those lines outside the document.
2. **Exact files changed:** `backend/static/components/js/job_order_signatures.js`, `mount()` (line 21), removes the summary and initial notice text; Booking Details template `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` (line 14) and standalone/mobile template `backend/core/modules/facilities/templates/facilities/pages/job_order.html` (line 5) version their assets as `20261027-sign-action-only`; this guide and `CAMPUSHUB_CONTEXT.md` record the behavior. No CSS or backend code changed.
3. **Changes made:** remove the external `0 of 4 signed` / revision display and staff-roster/Flutter setup message. Hide the entire controls host when no unsigned section is currently eligible, avoiding an empty footer. Keep the actual authorized Sign action and capture error messages.
4. **How it works:** `mount(host, config, refresh)` still receives the same server payload. It renders the existing role/action for `!section.signed && section.can_sign`, sets `host.hidden` when there is no eligible action, and starts the live error/status paragraph empty. The existing `open()` function can still show a missing-pad error and open the unchanged capture modal. For example, an unassigned account gets no footer, while an eligible assigned aide gets the existing Sign action. Server metadata is retained; only its external display is removed.
5. **Backend / API behavior:** unchanged. Actual signature counts/revisions/notices remain in the existing API payload; roster, authentication, signing sequence, audit events, client Flutter handoff and server-side prepare/confirm enforcement are preserved. Saved signatures, names and dates remain inside the original document preview/PDF/DOCX.
6. **Database / migration impact:** none. No working records, office assignments, permissions, settings, models or migrations changed. The separately proposed roster editor remains unimplemented.
7. **Verification:** Node syntax check passed. Chromium ran the actual shared component with isolated UI fixtures: **37 assertions passed** across 1440, 1024, 768, 390 and 320px. Checks cover hidden unassigned/waiting/signed controls, absent summary/setup text, visible eligible Sign, no controls overflow and preserved missing-pad error feedback. Protected backend/document/workflow/mobile source fingerprints still match the preceding task. This was component verification, not a new full Django or native-device acceptance run; earlier regression results below are historical.
8. **Limitations / safe practice:** reload Booking Details to load the versioned script. The controls renderer is shared with the standalone/mobile Job Order page, so the same text is removed there. Signing remains unavailable without an actual authorized assignment. Safe exercise: compare two isolated component states with `can_sign=false` and `can_sign=true`; verify the first host is hidden and the second retains Sign, with no progress/setup paragraphs in either state. Do not change a real roster or create real signatures for this check. Evidence: ignored `scratch/job-order-action-only-20261027/browser-results.json`.

## Facilities Admin roster enforcement and eligible-only Sign action — October 27, 2026

This section supersedes the earlier disabled-waiting-button presentation. The latest request is to show Sign only when currently authorized, while preserving the signing roster and client-first workflow.

### 1. Cause / reason

Inspection confirmed that the backend already permits Facilities Admin accounts to sign explicitly assigned staff sections. `assigned_admin()` resolves the existing roster and checks account activity and booking permissions; `can_sign()` compares that account with the authenticated actor and checks the unsigned section, approved booking and sequence. Facilities Admin is an account role, not automatic BEU Manager appointment. The remaining UI mismatch was that `mount()` also rendered a disabled Sign button for assigned actors who were not yet eligible.

### 2. Exact files changed

| File | Current line / anchor | Change |
|---|---|---|
| `backend/static/components/js/job_order_signatures.js` | 35 `if (!section.signed && section.can_sign)` | Render Sign only for currently eligible sections; remove the disabled-waiting-action branch. Keep status and explanatory notices. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 14 `20261027-roster-only-sign` | Refresh asset versions for Booking Details. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 5 `20261027-roster-only-sign` | Refresh the same assets for the existing standalone/mobile Job Order view. |
| `backend/core/modules/facilities/test_job_order_signatures.py` | 132 assigned-section matrix; 153 unassigned manager rejection; 172 mid-capture revocation | Three security regressions using disposable PostgreSQL fixtures. |
| `docs/booking-module-chatgpt-context.md` | 3 this section | Record cause, code/data flow, verification and limits. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest entry | Persist the current visibility rule and pending roster-editor boundary. |

### 3. Changes made

The compact signed-count/revision summary remains visible. A waiting actor sees the existing explanation without a Sign button. An eligible assigned Facilities Admin sees Sign Job Order for their own office and opens the unchanged Signature Pad modal. The role does not authorize another office, and an unassigned Facilities Admin cannot sign as BEU Manager. No new permission grant, role, editor, account assignment or document generator was introduced.

### 4. How it works / functions, inputs, outputs and data flow

`status_data(booking, user, source)` still receives the real booking and authenticated actor and returns the existing section eligibility and notices. `mount(host, config, refresh)` consumes that payload and renders an action only for `can_sign=true`. Its condition is a UI reflection of the server decision:

```javascript
if (!section.signed && section.can_sign) {
    // Render this actor's existing Sign action and open the existing pad.
}
```

The unchanged data flow is roster + authenticated account + booking/sequence -> `can_sign()` -> status payload -> toolbar -> protected prepare/sign POST -> locked service recheck -> private booking signature JSON + real audit event -> original DOCX/PDF renderer and refreshed preview. Browser changes cannot confer signing authority because `sign_or_prepare()` checks the roster again inside the existing booking lock for both prepare and confirmation.

### 5. Backend / API behavior

No backend runtime code changed. Existing booking-read permissions remain necessary. Assigned Facilities Admins can act as Administrative Aide, Personnel In-Charge or BEU Manager only when that particular section names their own account and all existing signing conditions hold. Forged actor fields are ignored as authority. Removing an assignment after preparation causes confirmation to return 403 without recording a signature or success audit. Super Admin also receives no automatic office sign-off. Client signing remains the linked client's authenticated Flutter handoff/WebView; an administrator cannot sign the Client field.

### 6. Database / migration impact

None. No migration, working role grant, roster entry, booking, payment or signature was changed for this task. The earlier database-backed Staff Signing Roster editor remains proposed and gated by the user's required schema approval. Current runtime still uses the existing configured roster; it has not been replaced by an unapproved database model. Tests override it only inside disposable databases. No real administrator has been appointed to an office by this implementation.

### 7. Tests actually performed

- **40 targeted signing/preview tests passed in 6.345 seconds.** Added coverage proves each of the three explicitly assigned Facilities Admins signs only their own section, checks all other sections are denied, rejects unassigned manager prepare/confirm requests even after the first three sign-offs, and rejects assignment revocation during capture.
- **215 broader Facilities/mobile-booking regression tests passed in 34.699 seconds.**
- Actual authenticated browser acceptance: **74 signing/export assertions plus 8 empty-roster Facilities Admin assertions passed**. The final live-server test passed in **34.520 seconds** against disposable PostgreSQL. It covers hidden waiting/unassigned actions, eligible modal opening and mouse/touch capture, valid-CSRF direct-request denial for an unassigned Facilities Admin, client handoff, all four official sign-offs, audit count, unchanged approved booking/no payments, actual PDF/DOCX export and seven widths (1920, 1440, 1280, 1024, 768, 390 and 320). No browser JavaScript errors were recorded.
- The actual exported PDF was verified as one A4 page with all four recorded names/signatures/dates and visually inspected; the narrow-screen unassigned-viewer screenshot was also inspected.
- An initial browser run failed its compact-height assertion at 390px. An unchanged application rerun passed; the final harness waits for finite layout animations/fonts before measuring. The initial failure is retained, and no unrelated production CSS was changed based on that result.
- Evidence: ignored `scratch/job-order-facilities-roster-20261027/`, including logs, screenshots, actual exports, protected-source fingerprints and source manifest. Node syntax and Django system checks are recorded in its verification summary.

### 8. Remaining limitations / safe practice

The working staff roster is still unassigned, so a real Facilities Admin should not see Sign until an actual office appointment is configured and the existing sequence is ready. No usernames are guessed. The proposed Super Admin roster editor is not implemented by this narrower task. Physical-device Flutter acceptance was not rerun because no mobile code changed; authenticated client handoff and ownership are covered by the Django/browser checks. Arbitrary very long document content is not guaranteed to fit one page.

Safe exercise: run the targeted tests against a disposable test database. Follow the assigned aide -> personnel -> manager test and compare the unassigned-manager case after the first three signatures. Verify only the assigned account gets the eligible action, both forged request intents return 403 for the outsider, the audit count is unchanged after denial, and booking/payment state does not change. Never appoint a real administrator or sign a real booking merely to test this UI.

## Sign-action visibility and Staff Signing Roster inspection — October 27, 2026

### 1. Cause / reason

Read-only inspection of the approved booking `BK-2026-2786ED550F1C4A57` confirmed a linked mobile client, an empty staff roster and client-first signing enabled. All current administrator roles therefore received `can_sign=False`; the UI silently hid every action. Super Admin access alone is not appointment as Administrative Aide, Personnel In-Charge or BEU Manager. Client sign-off uses the linked mobile account, not a staff signature on the client's behalf.

### 2. Exact files changed for the visibility fix

| File | Current line / anchor | Change |
|---|---|---|
| `backend/core/modules/facilities/services/job_order_signatures.py` | 109 `status_data`; 140 `client_hint` | Add assignment-versus-readiness presentation flags, per-section blocking reasons and an honest overall notice. Signing policy functions remain unchanged. |
| `backend/static/components/js/job_order_signatures.js` | 22 `mount`, 30 `beuSigningNotice`, 38 `button.disabled` | Show active Sign for eligible actors; show assigned waiting actors a disabled action with an accessible reason. Unassigned viewers receive an explanation without signing authority. |
| `backend/static/components/css/job_order.css` | 19 `.beu-signature-controls button:disabled` | Clear disabled styling; hover remains restricted to enabled controls. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 14 `20261027-sign-action` | Version the affected assets. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 5 `20261027-sign-action` | Same controls for the owner-only mobile Job Order page. |
| `backend/core/modules/facilities/test_job_order_signatures.py` | 132 missing-roster test; 141/149 assigned waiting/ready tests; 157 mobile-owner test; 169/175 missing-client/terminal tests | Six additional API/state regressions without changing existing coverage. |
| `docs/booking-module-chatgpt-context.md`, `CAMPUSHUB_CONTEXT.md` | this section / latest entry | Record current behavior, tests and the separately gated roster proposal. |

### 3. Changes made

`0 of 4 signed` stays visible. No four-card signature gallery is reintroduced. Only the current assigned actor sees the Sign action; it is disabled while an earlier required signature is pending or the booking is read-only. An eligible actor retains the existing Signature Pad modal. An unassigned account gets a clear explanation rather than a misleading active button. Existing role/ownership checks are not bypassed.

### 4. How it works / functions and data flow

`status_data(booking, user, source)` reads existing assignments and calls unchanged `can_sign()` for eligibility. It now returns `is_current_signer`, `blocked_reason` and `notice` in addition to the existing fields. These are display hints, not write permissions. `mount()` uses them to render the appropriate control and connects disabled controls to the notice with `aria-describedby`. The existing challenge/sign POST still independently enforces assignment, actor source, booking state and sequence.

```text
Confirmed identity/assignment + existing can_sign() decision
 -> status_data() readiness and reason
 -> active Sign / disabled waiting action / unassigned-viewer explanation
 -> unchanged Signature Pad and protected signing service
```

Example: an assigned Administrative Aide sees a disabled Sign button and Waiting for the Client signature. After the client signs and the Job Order is refreshed, the same aide receives the active button. A Super Admin who is not a signatory remains unable to sign that section.

### 5. Backend / API and Flutter behavior

Only the existing signing-status payload is extended. `can_sign`, `assigned_admin`, capture validation, challenge enforcement, audit persistence and revision behavior are unchanged. The client signs through Flutter > Bookings > Booking Details > View Job Order Request. The existing bearer-authenticated handoff opens the booking-only WebView and requires no Django Admin login. Missing linked accounts or inactive clients receive an honest setup explanation. Approved-state/sequence rules and all actual signatures in the official PDF/DOCX remain intact.

### 6. Database / migration impact

The completed visibility fix adds no model, migration, account, role, roster assignment or working signature/payment change. No environment usernames are guessed or populated. The separate database-backed roster editor below is a proposal only and has not been implemented or migrated.

### 7. Actual verification

- **37 targeted signing/preview tests passed in 6.906 seconds.**
- **212 Facilities/mobile-booking regression tests passed in 39.441 seconds.**
- Actual HTTP/browser checks: **8 unconfigured-Super-Admin visibility checks** and **69 full signing/export checks** passed. These verify missing-roster guidance, visible disabled waiting actions, accessible explanations, active eligible actions/modal opening, owner-only client signing, mouse/touch capture, seven widths, all four saved sign-offs and preserved one-page real PDF/DOCX export.
- **3 Flutter Job Order screen/navigation tests passed.** Physical-device installation was not claimed.
- Evidence: ignored `scratch/job-order-sign-action-20261027/`. Its database and fixture users are isolated from working records. Policy-function and protected-source fingerprints are checked separately.

### 8. Staff Signing Roster proposal / approval gate

The user clarified that office appointments are not finalized and requested a Super Admin roster editor, not manual/hardcoded usernames. Inspection found existing Roles & Permissions handlers in `backend/core/accounts/role_management.py`, its `admin_roles.html`/`admin_roles.js` UI and existing activity logging. `admin_roles_page` at line 164 and `role_post` already enforce both Super Admin identity and `can_manage_roles_permissions`; reuse those guards for the roster. `can_manage_settings` is shared with other administrator roles and is not sufficient authority for roster edits.

There is no existing general settings model: the accounts models are Department, ProgramMajor, User, Role, AdminTabToken and AccountActivity. Recommend one small, additive `JobOrderSigningRoster` configuration model in `accounts/models.py`, with nullable references to the three real administrator accounts, confirmation actor/time and a version counter. No initial account assignments or data-seeding migration. Only explicit confirmation should activate chosen positions; empty positions remain unavailable. Existing account roles/grants stay unchanged. The current database has two active administrators with booking access; no additional accounts should be invented to fill the third position.

Place three account selectors and explicit confirmation inside the existing Roles & Permissions page, with no new sidebar module. Load eligible real accounts by stable database ID; recheck active/suspended state, existing booking access, distinct assignments and current Super Admin authority during save. Audit before/after assignments and confirmation identity/time atomically. Recheck the confirmed roster on signing, reject stale pending staff challenges after roster changes, and preserve previously completed signature/audit evidence. Client ownership and Flutter signing stay separate.

Expected implementation files after approval: `accounts/models.py`, one generated additive accounts migration, `accounts/role_management.py`, existing role template/JS/CSS, `core/urls.py`, the existing signature service and relevant tests/docs. Assignment cleanup must retain an audit trail when an assigned account is removed. No roster/schema source or working-database migration has been created in this inspection. **Approval is required before adding/applying the configuration schema, as explicitly requested by the user.**

Safe exercise: use isolated tests to compare an unassigned viewer, an assigned aide waiting for the client, and that same aide after the client signs. Verify the active button only in the last state, direct unauthorized POST rejection in the others, and unchanged official exports. Do not modify a real roster or sign a real booking to test visibility.

## Signatures inside the official document, compact signing controls — October 27, 2026

### 1. Confirmed cause

The existing pipeline already passed `job_order_data().signatures` into `job_order_docx()` and embedded saved PNGs in the original four sign-off cells. The confirmed UI problem was a second set of four signature cards below the DOCX-derived PDF, repeating names/dates/images and making the controls look like a separate document. A read-only database check found one saved working Job Order, zero saved signatures and zero signing audit events. Its blank signature fields are correct; pending actors and legacy editor metadata must never be printed as completed signatures.

A separate confirmed rendering issue was independent width/height clamping: a tall/narrow capture could be stretched rather than fitted proportionally. The original Word template itself was not missing signature fields.

### 2. Exact changed files and current anchors

| File | Line / anchor | Change |
|---|---|---|
| `backend/core/modules/facilities/services/job_order_docx.py` | 27 `PDF_CACHE_VERSION`; 38 `embed_signatures`; 56 proportional `scale`; 295 `job_order_pdf` | Fit the real image within 1120000 x 400000 EMU without distortion; isolate the updated renderer's PDF cache namespace. |
| `backend/static/components/js/job_order_signatures.js` | 21 `mount`; 25 `.beu-signature-toolbar`; 39 `open` | Replace all four duplicate cards/thumbnails with progress, revision, current authorized designation and Sign action. Preserve capture modal and server requests. |
| `backend/static/components/js/job_order_preview.js` | 27 `fetch` | Explicit `cache: no-store` when loading protected PDF bytes. Existing dispose/reload after signing remains. |
| `backend/static/components/css/job_order.css` | 2 `.beu-signatures`; 3 `.beu-signature-toolbar` | Compact wrapping controls; remove unused four-card, thumbnail and responsive-card-grid rules. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 14 CSS; 71 preview script; 73 signature script | Version assets `20261027-sign-in-document` so older card scripts/styles are not reused. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 5 CSS; 18/20 scripts | Same versioned viewer/capture assets for the existing standalone/mobile document view. |
| `backend/core/modules/facilities/test_job_order_signatures.py` | 227 official-cell test; 253 narrow-image test | Assert four correct image/name/Manila-date mappings and bounded, proportional image geometry. |
| `backend/core/modules/facilities/test_job_order_preview.py` | 66 obsolete-renderer-cache test | Confirm a legacy cache entry cannot replace output from the updated renderer. |
| `docs/booking-module-chatgpt-context.md` | 3 this section | Cause, source map, functions/data flow, checks and safe exercise. |
| `CAMPUSHUB_CONTEXT.md` | 3 latest entry | Persist the document-first UI behavior. |

### 3. Changes made

The official paper is the only place displaying completed signature images, signer names and signing dates. Beneath it, a compact line shows the actual number signed and revision. An eligible actor retains the existing Sign Job Order action and Signature Pad modal. Read-only users see no signing action. There is no duplicate signature heading, four-card grid or external signature-image gallery.

The original `.docx` template, header, document code, four role labels and unsigned blanks are preserved. Images fit a smaller shared bounding box with their aspect ratio intact. Full names/dates are not replaced with placeholders. Very long saved document content still follows the existing pagination behavior; the one-page claim below applies to the verified fixture, not arbitrary unlimited content.

### 4. Functions, inputs/outputs and data flow

`mount(host, config, refresh)` still receives the server's authoritative signature count, revision and `can_sign` sections. It now outputs only compact controls. `open(section, trigger)` still opens the existing mouse/touch pad, prepares its document-bound challenge, validates empty input and posts the actual drawing. On success the existing callback disposes the old preview and loads updated booking/document data.

```text
Authenticated capture -> existing locked signature service/private JSON/audit
 -> job_order_data() -> embed_signatures() in the original Word cells
 -> same DOCX export or LibreOffice PDF -> PDF.js preview / Print
```

`embed_signatures()` receives only recorded sign-offs. It computes `scale = min(max_width / image.width, max_height / image.height)` and applies that same scale to both dimensions. For example, a 120 x 180 capture stays in a 2:3 ratio rather than being stretched wide. No signature record means the existing blank cell remains blank.

`job_order_pdf()` continues hashing the complete filled DOCX. Its new `job-order-docx-v2-signatures-` namespace logically invalidates older renderer output without deleting unrelated cache files or booking history. Subsequent signatures change the DOCX hash; identical exports still reuse cached bytes. Browser PDF requests explicitly avoid stale HTTP caching.

### 5. Backend/API behavior

Signing and image endpoints, actor/section authorization, office assignments, client ownership, CSRF, one-time challenges, audit events and revision handling are unchanged. Existing Print/PDF/DOCX routes remain the sole document pipeline. No new template or generator was created. No inventory or unrelated module was modified.

### 6. Database/migration impact

No model or migration changes, no working database migrations, and no real booking/payment/signature edits. The original Word template and four protected authorization/workflow source files are fingerprinted against the inspection baseline. Browser/renderer verification creates signatures only in a separately named disposable PostgreSQL database.

### 7. Actual verification

- Final targeted signing/preview regressions: **31 tests passed in 5.173 seconds**, including each recorded Manila timestamp in the correct official cell.
- Facilities plus mobile-booking regressions: **206 tests passed in 58.046 seconds**.
- Real authenticated HTTP/browser acceptance: **59 checks passed** at 1920/1440/1280/1024/768/390/320px, including all four actual captures, mouse/touch/resize, compact status updates, no duplicate cards/images, authorized actions and preserved exports. Normal application responses were not replaced by fixture HTML.
- Real LibreOffice export: **one A4 page** containing all four signatures/names/dates. PDF page count/text assertions passed, and `signed-paper.png` was visually inspected. Original labels/header/code remain visible.
- Existing ownership, permission, audit, concurrency, snapshot and cache regression coverage remains intact. No physical-device/printer acceptance is implied.
- Evidence: ignored `scratch/job-order-signatures-in-document-20261027/`, including before copies, protected hashes, regression log, HTTP runner, browser results and actual test PDF/DOCX/PNG. These are isolated test documents, not real institutional sign-offs.

### 8. Troubleshooting and safe practice

An unsigned working document must remain blank. A progress count or assigned person's name is not evidence of a saved signature. Staff assignments remain a separate required setup; this layout fix does not grant signing authority or manufacture signatures. If a signed preview looks outdated, reload once to pick up the new asset versions, use the existing Retry action, and inspect the protected PDF response before assuming stored data is missing.

Safe exercise: run the isolated signature/preview tests using the standard Django test runner. In a disposable database only, sign the four sections with their assigned actors and inspect the original Word table's second row: each cell must contain its own PNG/name/Manila date. Export the PDF and verify one page with all four sign-offs. Repeat with one section unsigned and confirm its field remains blank. Compare the original template hash and verify that no separate HTML signature cards appear. Do not sign a real booking merely to demonstrate the layout.

## Authenticated Job Order signatures — October 27, 2026

### 1. Cause and scope

The original Job Order had four blank sign-off cells and private exports but no signature capture. Legacy `filled_out_by`, `assisted_by`, `verified_by` and `approved_by` values are workflow actors, **not signatures**. The booking approver is not automatically the BEU Manager signatory. This addition implements authenticated section signatures inside the existing Job Order; earlier draft-only descriptions below predate it. Overall document status remains Draft. Signing does not approve, pay or complete a booking.

### 2. Exact files and current anchors

Paths are repository-relative. Search the anchor if later edits move a line.

| File | Line / anchor | Purpose |
|---|---|---|
| `backend/core/modules/facilities/services/job_order_signatures.py` | 36 `locked_booking`; 57 `revision_hash`; 75 `assigned_admin`; 125 `validated_png`; 155 `sign_or_prepare`; 215 `reconcile_edit` | Identity/section policy, atomic signatures, private images, replay checks and signed revisions. |
| `backend/core/modules/facilities/services/job_order.py` | 154 `current_job_order_data`; 181 `job_order_data` | Preserve the field formatter and render signed snapshots. |
| `backend/core/modules/facilities/services/job_order_docx.py` | 37 `embed_signatures`; 152 `job_order_docx`; 293 `job_order_pdf` | Original-cell image embedding and deterministic DOCX/PDF caching. |
| `backend/core/modules/facilities/job_order_signature_views.py` | 45 `admin_sign`; 76 `owner`; 97 `mobile_handoff`; 143 `mobile_view`; 172 `mobile_sign`; 192 `mobile_document` | Protected signing, images and the restricted mobile owner view. |
| `backend/core/modules/facilities/booking_workflow_views.py` | 77 `without_attachments`; 118 `detail_data`; 226 `previous_job`; 255 `reconcile_edit` | Redact private state, return section status and archive signed revisions on edits. |
| `backend/core/modules/facilities/mobile_views.py` | 73 `can_view_job_order` | Existing mobile booking response exposes Job Order availability. |
| `backend/core/core/urls.py` | 107 mobile routes; 229 administrator routes | Register narrowly scoped signing/viewing endpoints; existing export routes remain. |
| `backend/core/core/settings.py` | 282 `JOB_ORDER_SIGNERS` | Explicit office roster, empty by default; ordered signing enabled. |
| `backend/core/modules/facilities/templates/facilities/pages/admin_booking_details.html` | 72 signature scripts | Load the local capture dependency and component. |
| `backend/core/modules/facilities/templates/facilities/pages/job_order.html` | 14 `beuStandaloneSignatures` | Reuse the document page for the authenticated mobile owner. |
| `backend/static/components/js/admin_booking_workflow.js` | 206 `CampusHubJobOrderSignatures.mount` | Place status/capture beneath the existing preview; reload its current tab after signing. |
| `backend/static/components/js/job_order_signatures.js` | 13 `post`; 24 `mount`; 57 `open` | Mouse/touch pad, Clear/Cancel/preview, errors, focus and authenticated thumbnails. |
| `backend/static/components/css/job_order.css` | 2 `.beu-signatures`; 12 `.beu-signature-dialog` | Compact responsive navy/gold/white controls. |
| `backend/static/vendor/signature_pad/5.1.4/signature_pad.umd.min.js` and `LICENSE` | 1 Signature Pad 5.1.4 / MIT | Pinned local asset; capture does not depend on an external runtime CDN. |
| `campushub/lib/module_app/screens/facilities/job_order_screen.dart` | 8 `jobOrderNavigationAllowed`; 22 `JobOrderScreen` | Restricted native WebView, header handoff and navigation/error handling. |
| `campushub/lib/module_app/screens/facilities/facility_booking_status_screen.dart` | 138 `View Job Order Request` | Launch from existing mobile Booking Details. |
| `campushub/pubspec.yaml` and `campushub/pubspec.lock` | 38 / 768 `webview_flutter` | Native WebView dependency and resolved versions. |
| `backend/core/modules/facilities/test_job_order_signatures.py` | 32 `JobOrderSignatureTests`; 334 `JobOrderSignatureConcurrencyTests` | Authorization, private storage, revisions, cache and PostgreSQL race regressions. |
| `campushub/test/job_order_screen_test.dart` | 6 `main` | Restricted destinations, unsupported-platform and missing-authentication behavior. |
| `docs/booking-module-chatgpt-context.md`, `CAMPUSHUB_CONTEXT.md` | 3 this section / latest entry | Implementation and verification record. |

### 3. Changes and office assignments

Four sections display recorded name/designation, Pending/Signed, signature and Philippine-local time. Sign actions appear only for an eligible assigned actor. Client signing requires the actual linked `CampusHubUser`; an administrator cannot sign the client section, including through a forged API call or roster entry. Numeric client/admin IDs are namespaced, not treated as the same person.

Staff accounts must be explicitly designated in the server's `CAMPUSHUB_JOB_ORDER_SIGNERS` JSON object: `assisted_by` is the actual Administrative Aide username, `verified_by` the actual Personnel In-Charge username, and `approved_by` the actual BEU Manager username. They must be distinct, active, unsuspended administrator accounts with existing booking-read access. Set real values only after BEU confirms them, then restart Django. No accounts or permissions are created automatically. Missing, duplicate, inactive or unauthorized assignments remain unavailable. **The working roster has intentionally not been populated; actual BEU usernames are still required.**

`JOB_ORDER_SIGNATURE_SEQUENCE=True` applies Client -> Aide -> Personnel -> Manager. Only Approved bookings permit new signatures. Completed/Cancelled documents remain historical evidence under existing access rules; signing does not become a booking-completion prerequisite.

### 4. Functions, inputs/outputs and data flow

`status_data(booking, account, source)` returns the four section summaries, actual values and `can_sign` hints. `can_sign()` repeats authorization during writes; hiding a button is not the security boundary.

`sign_or_prepare()` accepts the authenticated actor, section and intent. Prepare creates a five-minute single-use challenge bound to booking, account source/ID, section and the printable document/template revision. Sign rechecks everything under the existing Facility -> Booking lock and atomically saves the signature and existing `AccountActivity` event. Names, roles and timestamps submitted by a caller cannot override server identity/time. Audit failure rolls the signature back.

`validated_png()` bounds encoded/decoded size and dimensions, checks PNG content and non-empty ink, and re-encodes it. The browser's `isEmpty()` check alone is insufficient. PostgreSQL advisory locking and a normalized image digest reject exact stored-image reuse, including concurrent requests. There is no saved-signature picker. Pixel-altered imitations cannot be conclusively attributed from an image alone; this is not biometric identity verification.

```text
Existing administrator access + explicit office assignment
 -> prepare challenge -> draw/preview -> confirm
 -> locked identity/revision/image checks -> private JSON + audit -> refreshed preview

Authenticated Flutter booking owner
 -> bearer-authenticated handoff POST -> single-use header exchange
 -> short-lived booking-only HttpOnly cookie -> same pad/service, client section only
```

The mobile handoff expires after 60 seconds. Its owner session/challenges last at most five minutes; the owner session cannot outlive the original token. The mobile bearer token never enters JavaScript, a URL or the WebView. The restricted cookie is HttpOnly, SameSite=Strict and scoped to this booking's Job Order. Production requires HTTPS. It cannot authenticate Admin Web or another booking. Unrelated WebView origins, bookings and schemes are denied; local PDF blobs are allowed.

The first signature freezes all printable fields and the original Word template. Images remain bounded private JSON attachments; ordinary details omit binary data and private challenges. Example shape (not a real record): `job_order.signatures.filled_out_by` contains `actor_ref=mobile:<actual ID>`, server `at`, `document_hash`, `image_hash` and a private PNG attachment. Actual account names/designations are snapshotted without inventing historical identities.

`reconcile_edit()` compares changed paper fields with the signed snapshot. A real change archives the signed record in `job_order.revisions`, increments the revision and clears current signatures/challenges. Unchanged paper fields retain signatures. A later profile edit cannot silently rewrite a signed paper. Previous image digests remain retained. No new revision-browser UI is added.

`embed_signatures()` fills the original four Word cells with the PNG, recorded name and Asia/Manila time. Stable ZIP metadata preserves identical DOCX bytes. The existing `job_order_pdf()` hash therefore changes for new signatures and reuses identical exports. Successful saves reload the existing preview. Protected thumbnail requests use authenticated fetch because ordinary image requests cannot send administrator per-tab headers.

### 5. Backend/API behavior

Administrator POST `/api/bookings/<id>/job-order/sign/` accepts `intent: prepare` or `intent: sign`. It requires existing booking access, exact section assignment and normal CSRF protection. Private PNGs use `/api/bookings/<id>/job-order/signatures/<section>/` with existing booking-read checks.

Mobile routes under `/api/mobile/bookings/<id>/job-order/` are `handoff/`, `view/`, `sign/`, `document/` and `signatures/<section>/`. Only the bearer-authenticated handoff POST is CSRF-exempt, matching existing mobile authentication. Cookie-authenticated signing retains CSRF. Expired/consumed/mismatched grants and inactive/suspended clients are rejected. Existing approved physical-booking draft generation, Print/PDF/DOCX generation and document permissions are preserved.

### 6. Database and workflow impact

No new model, table or migration. Existing `FacilityBookingRequest.details['job_order']` holds bounded signatures, snapshots, hashed temporary authentication state and revision history. Existing `AccountActivity` holds real success events without raw images/challenges. No working-database migration was applied and no working booking/payment records were created or signed for testing. Approval, cashier, reservation, inventory, laboratory and completion rules are unchanged.

The historical `ensure_job_order_draft()` GET backfill still exists. Do not assume an arbitrary working Job Order GET is database-write-free. Verification used disposable PostgreSQL records.

### 7. Actual verification

- Final Facilities/mobile-booking regression: **203 Django tests passed in 57.839 seconds**, including authorization, CSRF, ownership, expiry/replay, private storage, snapshots, revision retention, cache invalidation, single-read template/hash consistency and an actual PostgreSQL concurrent double-confirmation test. Two simultaneous confirmations produce one signature and one audit event.
- Actual authenticated browser/HTTP acceptance: **52 checks passed** at 1920/1440/1280/1024/768/390/320px, all four pad captures (actual mouse and Chromium touch input), responsive canvas resize without lost ink, Clear/Cancel/empty validation, focus return, private thumbnails, status refresh and real signed PDF/DOCX exports. No browser JavaScript errors. The deliberately anonymous document request was denied.
- The actual LibreOffice signed PDF was visually inspected: **one page**, original USTP header/document code and all four recorded sign-offs. Arbitrarily long saved content is not guaranteed to fit one page.
- Initial isolated fixtures lacked a client contact number; the fixtures were corrected without weakening booking validation. Browser inspection found per-tab thumbnail authentication missing; authenticated fetch fixed it and the complete run passed again.
- Flutter: **eight tests passed**, covering existing facility booking screens plus new owner-view/navigation checks. Targeted analysis of the two affected screens and new test reports **No issues found**. Android debug APK built successfully (final incremental build 40.0 seconds) at `campushub/build/app/outputs/flutter-apk/app-debug.apk`. No physical-device/iOS installation or institutional acceptance is implied.
- Django system and Node syntax checks passed. `makemigrations --check --dry-run`: **No changes detected**.
- Evidence: ignored `scratch/job-order-signatures-20261027/` contains runners, screenshots and real signed test PDF/DOCX. Its test identities/strokes are disposable fixtures, not working institutional sign-offs.

Reproduce backend regressions using the standard Django runner (it creates a disposable test database). The ignored evidence runner additionally selects a separate test-database name for concurrent QA runs:

```powershell
& backend/core/venv/Scripts/python.exe -B backend/core/manage.py test modules.facilities api.test_mobile_facility_booking --noinput
# From campushub/:
flutter test test/job_order_screen_test.dart test/facility_booking_flow_test.dart
flutter analyze lib/module_app/screens/facilities/job_order_screen.dart lib/module_app/screens/facilities/facility_booking_status_screen.dart test/job_order_screen_test.dart
flutter build apk --debug --no-pub
```

The working database was checked separately inside `SET TRANSACTION READ ONLY`: zero signed Job Orders, zero `job_order_signed` events and zero configured staff-roster entries. This is evidence that test signatures were not created in the working database; it is not a claim to have reconstructed every unrelated payment change.

### 8. Limitations, troubleshooting and safe exercise

Staff activation still requires the three actual BEU usernames; do not weaken guards or map every office to the only Facilities Admin. Pending can mean an earlier sign-off is incomplete. Not assigned can indicate missing, duplicate, inactive or unauthorized configuration. This is not a migration problem.

If the mobile session expires, return to Booking Details and reopen Job Order. A client without a linked account needs an authorized identity-resolution process; staff cannot sign for them. Physical WebView behavior, native print/download UX, assistive technologies and institutional acceptance need separate verification. Unsupported native platforms show an honest message.

JSON history grows with real signed revisions; retention must preserve evidence. Database administrators can still alter database records. This is authenticated electronic-signature capture with application audit history, not certificate-based digital signing or external notarization.

Safe exercise: run isolated signature tests, then use a disposable database with distinct authorized staff and a linked test client. Sign in order; inspect four namespaced actor references and four audit events, unchanged booking/payment state, protected images and populated PDF cells. Edit one paper field: revision 2 should be pending while revision 1 retains the real test signatures. Never use a real booking or a copied signature for this exercise.

## Job Order explained in plain language (October 27, 2026)

A **Job Order (JO)** records the work or service a client requests. It tells the responsible office who the client is, what work is needed and the relevant details. Issuing the request does not, by itself, mean the work has been accepted, completed or paid.

In CampusHub, distinguish the required **Food Analysis procedure** from the **automatic draft already implemented for physical facility bookings**. They use the Job Order concept, but have different processing steps.

### What each document means

| Document | Main question it answers | Meaning |
|---|---|---|
| Booking Slip | What reservation was recorded? | Saved client, facility and reservation details; not proof of payment. |
| Job Order Request | What work or service is requested? | Instructions and details for staff to review and process; not proof of payment. |
| Statement of Account (SOA) | What charges are due? | Billing information; not proof that the client paid. |
| Official Receipt (OR) | What payment was received? | Receipt issued by the authorized cashier for an actual payment. CampusHub records the receipt information; it does not issue the cashier's legal OR. |
| Certificate of Analysis | What were the laboratory results? | Laboratory output released according to the Food Analysis procedure. |

### Food Analysis: the required office procedure

The following sequence comes from the project-provided procedure **DPM-USTP-Oro-BEU-004** in [AGENTS.md](../AGENTS.md), Section 7. The original ISO document was not independently inspected for this explanation.

1. **Inquiry:** the client asks about the needed analysis.
2. **Sample receiving:** staff inspect sealing, required quantity, temperature and signs of foul smell or leakage.
3. **Job Order Request:** if the sample passes the checklist, staff issue **FM-USTP-Oro-BEU-001** for the requested work.
4. **Resource check:** staff coordinate with the laboratory technician about reagents, chemicals, equipment and calibration.
5. **Acceptance or disapproval:** accepted work is logged with its turnaround deadline. Disapproval requires a written notice with a specific reason.
6. **Analysis:** laboratory staff perform the tests.
7. **Billing and payment:** after completion, staff issue the SOA (**FM-USTP-Oro-BEU-002**). The client pays at the Collecting Officer / Cashiering Office and receives an OR.
8. **Results release:** the client presents the OR at the laboratory to receive the Certificate of Analysis.
9. **Feedback:** the client completes the Customer Feedback Form (**FM-USTP-Oro-BEU-Survey**).

**Illustrative example only:** a client submits bread for protein and moisture testing. After the receiving checklist passes, the Job Order identifies the sample and requested tests. The laboratory still checks its resources before accepting the work. Fees and turnaround must come from actual approved rates and staff decisions; this example supplies neither.

These are required workflow steps, not a claim that every step has a working CampusHub screen. The current service guide records that the full laboratory transaction workflow is still incomplete: see [service configuration and limitations](service-configuration.md).

### Physical bookings: what CampusHub currently prepares

An eligible approved physical booking receives a **draft** Job Order using its saved information. Covered Court and Function Hall map to **Facility Rental**; Hostel maps to **Hotel Accommodation**. Unknown physical types leave the service choice for staff. Service resources and academic/maintenance schedule blocks are excluded from this automatic physical-booking draft.

The draft can include client details, facility, purpose, schedule or stay dates, participants/guests and additional requirements when recorded. Staff review and complete official fields. The generated request number is blank; the system does not invent a number, signature, payment or final approval. Pending bookings do not expose the Job Order. Authorized staff can use the existing preview and PDF/DOCX exports; the draft is not a separate signed/final approval lifecycle.

### Where the current code lives and how information moves

The following source locations were inspected on October 27, 2026. They are reference locations, not application files changed for this explanation.

| File and current line | Function or anchor | Input, output and purpose |
|---|---|---|
| `backend/core/modules/facilities/services/job_order.py:20` | `default_job_order_service(facility)` | Reads facility type/mode; returns the physical-booking service label or an empty string. |
| `backend/core/modules/facilities/services/job_order.py:29` | `draft_eligible(booking, details)` | Reads booking status/resource/source; returns whether a missing physical-booking draft may be prepared. Approved and Completed are eligible statuses. |
| `backend/core/modules/facilities/services/job_order.py:38` | `add_job_order_draft(booking, details)` | Adds a missing draft to the supplied details dictionary; returns whether it added one. The caller handles persistence. |
| `backend/core/modules/facilities/services/job_order.py:87` | `ensure_job_order_draft(booking)` | Locks an eligible historical booking and its sidecar before saving a missing draft; existing drafts are preserved. |
| `backend/core/modules/facilities/services/job_order.py:154` | `job_order_data(booking, *, row=None)` | Converts saved client/draft data into plain document fields. Missing official fields stay blank. |
| `backend/core/api/models.py:660` | `FacilityBookingRequest`; `details` at line 668 | Existing related record stores the JSON dictionary, including `details['job_order']`; there is no separate Job Order model. |
| `backend/core/modules/facilities/booking_workflow_views.py:355` | `document(request, booking_id, kind)` | Checks access and physical-booking document eligibility, formats fields and returns the private document response. |
| `backend/core/modules/facilities/services/job_order_docx.py:91` | `job_order_docx(data)` | Fills the existing Word template from formatted fields and returns DOCX bytes. |
| `backend/core/modules/facilities/services/job_order_docx.py:227` | `job_order_pdf(data)` | Converts the filled document, reusing the private cache where possible, and returns PDF bytes. |
| `backend/core/modules/facilities/services/service_configuration.py:44` | `service_document_requirements(category, request_type)` | Returns document-policy booleans. Food Analysis requires JO and SOA; this helper creates no document or laboratory transaction. |

```text
Saved physical booking + authorized approval
  -> eligibility check + shared service mapping
  -> draft in FacilityBookingRequest.details['job_order']
  -> staff review of recorded details
  -> job_order_data() -> Word template -> DOCX or PDF
```

For an already eligible historical booking, opening its details/document can initialize a missing draft through `ensure_job_order_draft()`. Therefore, do not assume every document GET is database-write-free. A booking with an existing saved draft keeps that draft.

This design reuses the existing booking and JSON sidecar so the document draws from the saved reservation instead of creating a second reservation record. The separate service-policy helper describes required documents without pretending that the full laboratory workflow has been implemented.

Annotated reading example: `default_job_order_service(facility)` returns `Facility Rental` for a physical Covered Court. A Food Analysis service returns an empty string from this physical-booking helper; its JO requirement belongs to the separate service policy above.

### Troubleshooting and a safe learning exercise

- **No Job Order on Pending:** expected; approval is required before exposure. Do not approve a real request merely to test the document.
- **Food Analysis has no automatic physical-booking draft:** expected separation of workflows, not evidence that the laboratory does not require a JO.
- **Blank official number or signature:** do not fabricate values. Staff must follow the actual office process.
- **Preview fails:** use the existing Retry action and inspect the HTTP response/server error. PDF conversion requires the local converter; see the cache-setting troubleshooting report immediately below. A preview failure does not establish that the booking or payment is wrong.

Safe exercise: without editing code or records, open `job_order.py`, find `default_job_order_service` and predict the labels for Covered Court, Hostel and Food Analysis. Then compare your answers with the mapping and its service exclusion: **Facility Rental**, **Hotel Accommodation**, **empty string**. Finally, open `service_document_requirements` and verify that Food Analysis still requires both JO and SOA. This teaches the difference between physical draft generation and service-document policy without changing a real booking.

### Documentation update record (Section 10 protocol)

1. **Cause / reason:** the user requested a Markdown explanation of Job Orders; existing sections mainly describe implementation history.
2. **Exact files changed:** `docs/booking-module-chatgpt-context.md`, this plain-language section near the top.
3. **Changes made:** added definition, document comparison, Food Analysis procedure, current physical-booking behavior, source anchors, data flow and practice exercise.
4. **How it works:** documentation explains the existing functions and distinguishes project procedure from implemented behavior; no function was added or changed.
5. **Backend / API behavior:** unchanged. Source inspection confirmed access/eligibility handling and the existing possibility of lazy draft creation during a document read.
6. **Database / migration impact:** none; this documentation task did not connect to the database or run document endpoints.
7. **Tests performed:** inspected the cited source functions and existing service guide; checked the added section and source line anchors. No application tests, browser checks or PDF conversion were run for this documentation-only update. Earlier test reports below remain historical results.
8. **Remaining limitations:** no independent inspection of the original ISO form/procedure, live office acceptance or new laboratory processing feature. Current lines can move after later code edits; use the function anchors to find them.

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

## Booking Details app bar matches the schedule arrow - November 5, 2026

### 1. Cause / reason

After selecting a schedule, the Booking Details header showed a gray bottom line and a boxed chevron. Confirmed source: `BookingScaffold` selected its border-free app bar and standard Flutter `BackButton` only when `schedulePresentation` was true. That flag was enabled for Select Schedule (`_step == 0`), so Booking Details (`_step == 1`) used the other header branch.

### 2. Exact files changed

| File and current line | Nearby code anchor | Change |
| --- | --- | --- |
| `campushub/lib/module_app/widgets/facilities/booking_widgets.dart:203` | `BookingScaffold` | Added optional `flatAppBar`, default false, and combined it with the existing schedule flag only for the app bar's back control, elevation and border. |
| `campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:898` | `flatAppBar: _step == 1` | Enabled that header presentation for Booking Details. |
| `docs/booking-module-chatgpt-context.md` | This section | Recorded cause, implementation, checks and a safe practice exercise. |

### 3. Changes made

Booking Details now uses the same unboxed standard back arrow as Select Schedule, zero app-bar elevation and no bottom border. Its existing Poppins typography, requester fields, progress indicator and footer remain governed by their existing configuration. Review, Submitted, booking history and booking status screens retain their previous header selection.

### 4. How it works: functions, inputs, outputs and data flow

`FacilityBookingScreen.build` reads the existing `_step` and passes `flatAppBar: _step == 1` into `BookingScaffold`. The scaffold's `build` computes `useFlatAppBar = schedulePresentation || flatAppBar`. A true result chooses `BackButton`, zero elevation and an empty `Border`; false retains the existing boxed-chevron/bottom-border branch. The separate flag avoids enabling schedule typography or footer styling merely to reuse its header.

```dart
// Existing schedule styling stays specific to step 0.
schedulePresentation: _step == 0,
// Only step 1 additionally reuses the flat header and standard arrow.
flatAppBar: _step == 1,
```

The standard arrow calls Flutter navigation's existing pop handling. The enclosing `PopScope` still handles returning from Booking Details to the previous schedule step. Request data, availability loading, validation, submission and payment do not flow through the new styling flag.

### 5. Backend / API behavior

None changed. This is a Flutter presentation change. Django continues validating actual schedule availability, quotes and submissions through the existing endpoints.

### 6. Database / migration impact

None. No schema, migration, dependency, working booking, payment or account record changed.

### 7. Tests performed

- Existing Flutter suites: `flutter test --no-pub test/facility_booking_flow_test.dart test/select_schedule_test.dart test/capture_facility_screens_test.dart` — **42 tests passed**, including the requester form/back-navigation flow and captured booking screens.
- Targeted `dart analyze` on the two changed Dart files — **No issues found**.
- Inspected generated fixture screenshots `scratch/screenshots/2_select_schedule.png` and `scratch/screenshots/3_booking_details.png`: matching standard arrow, white header and no app-bar divider on Booking Details.
- Nested Flutter repository `git diff --check` for the two changed files — clean. The initial sandboxed Flutter/analysis commands stalled without results, were stopped, and were rerun successfully with SDK-cache access; those initial attempts are not counted as passing tests.

### 8. Remaining limitations and troubleshooting

No phone build/install or deployed-device verification was performed. The screenshot harness renders text with its test font blocks, so those images confirm the arrow/border layout rather than final device typography. The optional web design-kit token/gate files are not installed here; verification used this project's Flutter suites and analyzer rather than claiming a web gate result.

If the line remains on a running device, hot restart after saving the Dart files and confirm that this is the Booking Details step immediately after Select Schedule. The later transaction details/status screen is a different screen. Keep form field outlines and the footer border separate from the app-bar border when inspecting the result.

Safe practice: on a test facility, manually choose a date/window and continue to Booking Details without submitting. Compare both app bars, tap the standard back arrow and verify you return to Select Schedule. Continue again, enter a draft requester field, return and revisit to confirm the existing draft behavior; inspect `PopScope` rather than adding a second navigation callback. Use fixtures for automated checks and do not create or alter working bookings to test this styling change.


---

## 34. Available Hours Selection Indicator: Circle-Dot Redesign

### 1. Cause / Reason
The mobile facility schedule picker previously rendered Icons.check_circle_outline_rounded (a circle with a checkmark) when an available time slot was selected, and Icons.circle_outlined when unselected. For single-choice slot selection, a circle-dot (radio-dot: an outer circular ring containing a solid centered dot when selected, and an empty circular ring when unselected) provides clearer visual affordance without implying a multi-selection checkbox.

### 2. Exact Files & Current Line Numbers
- campushub/lib/module_app/screens/facilities/facility_booking_screen.dart:
  - **Anchor**: inside the _slots.map((slot) { ... }) builder for the Available Hours list (around lines 1285–1325).
  - Replaced the Icon(selected ? Icons.check_circle_outline_rounded : available ? Icons.circle_outlined : Icons.block) widget with a dedicated circle-dot container:
    - Blocked/unavailable slots render const Icon(Icons.block, size: 19, color: bookingGreyDot).
    - Available slots render a 20x20 Container with BoxShape.circle, bordered in ookingNavy (width 2.0) when selected or ookingGreyDot (width 1.5) when unselected.
    - When selected, the container hosts a centered 10x10 solid circular dot in ookingNavy (ValueKey('available-hours-inner-dot')).
- campushub/test/select_schedule_test.dart:
  - **Anchor**: helper declarations (around line 203) and test assertions (lines 254, 264, 268, 282, 320, 351, 363, 1292).
  - Added Finder selectedSlotDot() => find.byKey(const ValueKey('available-hours-inner-dot'));.
  - Updated selection assertions from ind.byIcon(Icons.check_circle_outline_rounded) to selectedSlotDot().

### 3. Functions & Data Flow
`
User taps slot
     │
     ▼
_pickSlot(slot)  ──>  setState(() { _slot = slot['time']; })
                             │
                             ▼
                    Build Available Hours row
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
      available == false                available == true
            │                                 │
     Icon(Icons.block)              20x20 Circular Container
                                    (bookingNavy vs bookingGreyDot border)
                                              │
                                     selected == true ?
                                     ┌────────┴────────┐
                                    Yes                No
                                     │                 │
                             10x10 inner dot         null
                              (bookingNavy)      (empty circle)
`
- **Inputs**: slot['time'], slot['available'], _slot state.
- **Outputs**: Institutional circle-dot selection indicator.
- **Integrity**: Operating schedule rules, date pickers, validation logic, minimum booking durations, and Django quote requests are completely untouched.

### 4. Verification Results
- lutter test --no-pub test/select_schedule_test.dart: 36/36 tests passed.
- lutter test --no-pub test/facility_booking_flow_test.dart test/covered_court_booking_test.dart: 10/10 tests passed.
- lutter analyze --no-pub lib/module_app/screens/facilities/facility_booking_screen.dart test/select_schedule_test.dart: 0 issues found.
- Screenshot generation at 390.0/1.0 scale confirmed pixel layout without overflow.

### 5. Beginner Practice Exercise
1. In acility_booking_screen.dart, locate ValueKey('available-hours-inner-dot').
2. Inspect the diameter: outer container is 20 px, inner dot is 10 px, outer border is 2.0 px when selected.
3. Calculate spacing: (20 - 4 - 10) / 2 = 3.0 px padding between inner dot and outer ring.
4. Verify by running lutter test --no-pub test/select_schedule_test.dart.


---

## 35. Facilities Screen: Top "My Bookings" Button Removed - November 6, 2026

### 1. Cause / Reason
The mobile Facilities catalog tab (`FacilitiesPage`) previously rendered an `Align` container with a `TextButton.icon` (`Icons.receipt_long_outlined`, label `'My Bookings'`) at the top of the facility listing. The user requested removing "My Bookings" from the facilities section in mobile. Users already have primary access to their booking history through the side navigation drawer (`SellerDrawer` / `MainDrawer` -> `My Bookings`) as well as the confirmation screen after submitting a reservation (`Check My Bookings`). Removing this button cleans up the facility catalog view, aligning the top edge of the list directly with facility cards or status feedback.

### 2. Exact Files & Current Line Numbers
- `campushub/lib/module_app/screens/facility_screen.dart`:
  - **Anchor**: top imports (around line 7-8).
    - Removed `import 'facilities/facility_booking_history_screen.dart';`.
  - **Anchor**: inside `_FacilitiesPageState.build()` `ListView(children: [...])` (around line 79-92).
    - Removed the `Align` block containing `TextButton.icon(icon: const Icon(Icons.receipt_long_outlined, size: 18), label: const Text('My Bookings'), ...)` that pushed `FacilityBookingHistoryScreen`.
- `campushub/test/resource_catalog_cards_test.dart`:
  - **Anchor**: widget test at line 454.
    - Updated test name from `'facility listing retains selected details and My Bookings'` to `'facility listing retains selected details without top My Bookings button'`.
    - Updated assertion from `expect(find.text('My Bookings'), findsOneWidget);` to `expect(find.text('My Bookings'), findsNothing);`.

### 3. Changes Made
- In `facility_screen.dart`:
  - Removed the unused import `facilities/facility_booking_history_screen.dart`.
  - Removed the `Align(alignment: Alignment.centerRight, child: TextButton.icon(...))` widget from the top of the `children` list in `ListView`.
- In `resource_catalog_cards_test.dart`:
  - Updated widget test assertions to verify that `'My Bookings'` is no longer present on the `FacilitiesPage`.

### 4. Functions & Data Flow
```
User navigates to Facilities tab (Tab index 3)
                     │
                     ▼
             FacilitiesPage
                     │
                     ▼
         _FacilitiesPageState.initState()
                     │
                     ▼
             _fetchFacilities()
                     │
      ┌──────────────┴──────────────┐
      │                             │
Loading state                  Success state
      │                             │
      ▼                             ▼
CircularProgressIndicator     ResourceCardGrid
                              (FacilityPreviewCard widgets)
```
- **Inputs**: `loadFacilities` callback returning `FacilityServiceResult`.
- **Outputs**: Clean listing of `FacilityPreviewCard` items inside `ResourceCardGrid` without a superfluous top action button.
- **Navigation Preservation**: Navigating to `FacilityBookingHistoryScreen` remains fully intact via the navigation drawer item `bookings('My Bookings', 'MAIN', Iconsax.calendar_tick_copy)` in `lib/module_app/widgets/navigation/seller_drawer.dart` and the post-booking submission step in `lib/module_app/screens/facilities/facility_booking_screen.dart`.

### 5. Backend / API Behavior
No backend or API changes. The facilities endpoint (`GET /api/facilities/`) and booking endpoints continue functioning as designed.

### 6. Database / Migration Impact
None. No database models, migrations, or database records were modified.

### 7. Tests Performed
- `flutter test test/resource_catalog_cards_test.dart`: 18/18 tests passed.
- `flutter test test/facility_status_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart test/select_schedule_test.dart`: 74/74 tests passed.
- `flutter analyze --no-pub`: 0 issues found (`No issues found!`).

### 8. Remaining Limitations
No physical Android/iOS device deployment or APK rebuild was performed in this session.

### 9. Beginner Safe Practice Exercise
1. Open `campushub/lib/module_app/screens/facility_screen.dart`.
2. Inspect `build(BuildContext context)`: observe that `ListView(children: [...])` begins directly with `if (_isLoading)` without any preceding buttons.
3. Open `campushub/lib/module_app/widgets/navigation/seller_drawer.dart`: observe where `bookings('My Bookings', ...)` provides the persistent drawer entry point.
4. Run `flutter test test/resource_catalog_cards_test.dart` from the `campushub` directory to verify the test suite verifies that `My Bookings` does not appear on the facilities catalog.


---

## 36. Facility Details: Bottom Action Button Matches Product Details Style & Size - November 6, 2026

### 1. Cause / Reason
The user requested copying the style and size of the button from Product Details to Facility Details. In `ProductDetailsScreen` (`_ProductBottomBar`), the main action button (`Buy Now`) uses a 52 px height (`minimumSize: const Size(0, 52)`), a pill-shaped outline (`shape: const StadiumBorder()`), `FontWeight.w600` typography, zero elevation, and standard horizontal/vertical padding (`EdgeInsets.symmetric(horizontal: 12, vertical: 12)`). In contrast, `FacilityDetailsScreen` (`_FacilityBookingBar`) previously used 56 px tall buttons with rectangular 14 px corner radiuses (`RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))`) and heavier `FontWeight.w700` text. Updating the Facility Details bottom action bar buttons (`Request Booking` / `Message Admin` and `Chat`) to match this exact style and 52 px height delivers design consistency across the mobile application.

### 2. Exact Files & Current Line Numbers
- `campushub/lib/module_app/screens/facility_details_screen.dart`:
  - **Anchor**: inside `_FacilityBookingBar.build()` (around lines 1162–1240).
  - Updated outer footer padding to `EdgeInsets.fromLTRB(16, 10, 16, 10)` matching the Product Details bottom bar safe area inset.
  - In `OutlinedButton` (`facility-chat-button`):
    - Added `elevation: 0`.
    - Changed `minimumSize` from `Size(0, 56)` to `Size(0, 52)`.
    - Changed `padding` to `EdgeInsets.symmetric(horizontal: 12, vertical: 12)`.
    - Changed `shape` from `RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))` to `const StadiumBorder()`.
  - In `FilledButton` (`facility-request-booking-button`):
    - Added `elevation: 0`.
    - Changed `minimumSize` from `Size(double.infinity, 56)` to `Size(double.infinity, 52)`.
    - Changed `padding` to `EdgeInsets.symmetric(horizontal: 12, vertical: 12)`.
    - Changed `shape` from `RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))` to `const StadiumBorder()`.
    - Updated `textStyle` weight from `FontWeight.w700` to `FontWeight.w600` matching `AppTypography.text(fontSize: 14, fontWeight: FontWeight.w600)`.

### 3. Changes Made
```dart
// OutlinedButton (facility-chat-button):
style: OutlinedButton.styleFrom(
  backgroundColor: _facilityControlSurface,
  foregroundColor: bookingNavy,
  elevation: 0,
  minimumSize: const Size(0, 52),
  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
  side: const BorderSide(color: _facilityOutline),
  shape: const StadiumBorder(),
  textStyle: _detailText(14, weight: FontWeight.w600),
),

// FilledButton (facility-request-booking-button):
style: FilledButton.styleFrom(
  backgroundColor: _facilityDetailGold,
  foregroundColor: bookingNavy,
  disabledBackgroundColor: _facilityControlSurface,
  disabledForegroundColor: _facilityMuted,
  elevation: 0,
  minimumSize: const Size(double.infinity, 52),
  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
  shape: const StadiumBorder(),
  textStyle: _detailText(
    14,
    weight: FontWeight.w600,
    color: bookingNavy,
  ),
),
```

### 4. Functions & Data Flow
```
User navigates to Facility Details screen
                   │
                   ▼
         FacilityDetailsScreen
                   │
                   ▼
         Scaffold bottomNavigationBar
                   │
                   ▼
         _FacilityBookingBar
         ┌─────────┴─────────┐
         │                   │
showBookingAction == true   showBookingAction == false
         │                   │
         ▼                   ▼
Row:                        Full-width:
- OutlinedButton (Chat)     - FilledButton (Message Admin)
  [StadiumBorder, 52h]        [StadiumBorder, 52h]
- FilledButton (Request)
  [StadiumBorder, 52h]
```
- **Inputs**: `showBookingAction`, `onChat`, `onPressed` callbacks.
- **Outputs**: Institutional, unified pill-shaped bottom action bar buttons across products and facilities.

### 5. Backend / API Behavior
None. This is purely a Flutter presentation and styling update. All facility quote, booking, and chat endpoints behave identically.

### 6. Database / Migration Impact
None. No database models, migrations, or database records were changed.

### 7. Tests Performed
- `flutter test test/facility_details_test.dart`: **41/41 tests passed** in 9s.
- `flutter test test/facility_details_test.dart test/facility_status_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart test/select_schedule_test.dart test/resource_catalog_cards_test.dart`: **115/115 tests passed** in 26s.
- `flutter analyze --no-pub`: 0 issues found (`No issues found! (ran in 10.4s)`).

### 8. Remaining Limitations
No physical phone APK install was performed; layout verified through automated widget testing and headless Flutter test runtime.

### 9. Beginner Safe Practice Exercise
1. Open `campushub/lib/module_app/screens/facility_details_screen.dart` and locate `_FacilityBookingBar`.
2. Inspect `FilledButton.styleFrom` and `OutlinedButton.styleFrom`: verify both have `shape: const StadiumBorder()` and `minimumSize: const Size(..., 52)`.
3. Open `campushub/lib/module_app/screens/product_details_screen.dart` and locate `_ProductBottomBar`: verify the identical button shape (`StadiumBorder`) and height (`52`).
4. Run `flutter test test/facility_details_test.dart` to verify all button height and interaction tests pass.


---

## 37. Facility Details: Chat Button Styled with Pure White Container & Navy Blue Outline - November 6, 2026

### 1. Cause / Reason
The user provided a visual reference and requested designing the Chat button in the Facility Details bottom action bar with a pure white container (`Colors.white`) and a navy blue outline (`bookingNavy`, `#1A1851`). Previously, the Chat `OutlinedButton` used a subtle grey background (`_facilityControlSurface`, `#F5F6FA`) with a subtle grey border (`_facilityOutline`, `#E3E5ED`). Updating it to a pure white container with a 1.2 px solid navy blue border gives the button clear contrast, institutional branding, and a crisp pill appearance alongside the gold `Request Booking` button.

### 2. Exact Files & Current Line Numbers
- `campushub/lib/module_app/screens/facility_details_screen.dart`:
  - **Anchor**: inside `_FacilityBookingBar.build()` `OutlinedButton` (`ValueKey('facility-chat-button')`) (around lines 1170–1188).
  - Changed `backgroundColor` from `_facilityControlSurface` to `Colors.white`.
  - Changed `side` from `const BorderSide(color: _facilityOutline)` to `const BorderSide(color: bookingNavy, width: 1.2)`.
  - Preserved `foregroundColor: bookingNavy`, `shape: const StadiumBorder()`, `minimumSize: const Size(0, 52)`, and `elevation: 0`.
- `campushub/test/facility_details_test.dart`:
  - **Anchor**: widget test at lines 205–240.
  - Added explicit test expectations asserting `chatButton.style!.backgroundColor!.resolve({}) == Colors.white` and `chatButton.style!.side!.resolve({})!.color == const Color(0xFF1A1851)`.

### 3. Changes Made
```dart
// OutlinedButton (facility-chat-button):
OutlinedButton(
  key: const ValueKey('facility-chat-button'),
  onPressed: onChat,
  style: OutlinedButton.styleFrom(
    backgroundColor: Colors.white, // Pure white container
    foregroundColor: bookingNavy, // Navy blue text & icon
    elevation: 0,
    minimumSize: const Size(0, 52),
    padding: const EdgeInsets.symmetric(
      horizontal: 12,
      vertical: 12,
    ),
    side: const BorderSide(color: bookingNavy, width: 1.2), // Navy blue outline
    shape: const StadiumBorder(),
    textStyle: _detailText(14, weight: FontWeight.w600),
  ),
  child: ...
)
```

### 4. Functions & Data Flow
```
Facility details rendered with showBookingAction == true
                     │
                     ▼
         _FacilityBookingBar
         ┌───────────┴───────────┐
         │                       │
OutlinedButton (Chat)    FilledButton (Request Booking)
- Background: Colors.white- Background: #FCB316 (Gold)
- Border: #1A1851 (Navy) - Border: none
- Text/Icon: #1A1851     - Text: #1A1851
- Shape: StadiumBorder   - Shape: StadiumBorder
- Height: 52px           - Height: 52px
```
- **Inputs**: `onChat` callback.
- **Outputs**: High-contrast, institutional pure white Chat button with crisp navy blue outline.

### 5. Backend / API Behavior
None. Purely a Flutter visual presentation styling update.

### 6. Database / Migration Impact
None. No database models or migrations involved.

### 7. Tests Performed
- `flutter test test/facility_details_test.dart`: **41/41 tests passed** in 14s.
- `flutter test test/facility_details_test.dart test/facility_status_test.dart test/facility_booking_flow_test.dart test/covered_court_booking_test.dart test/select_schedule_test.dart test/resource_catalog_cards_test.dart`: **115/115 tests passed** in 31s.
- `flutter analyze --no-pub`: 0 issues found (`No issues found! (ran in 9.3s)`).

### 8. Remaining Limitations
No physical phone APK install was performed; automated tests verify styling, background color resolution, and outline color resolution.

### 9. Beginner Safe Practice Exercise
1. Open `campushub/lib/module_app/screens/facility_details_screen.dart` and locate `_FacilityBookingBar`.
2. Inspect `OutlinedButton.styleFrom`: verify `backgroundColor: Colors.white` and `side: const BorderSide(color: bookingNavy, width: 1.2)`.
3. In `test/facility_details_test.dart`, locate `final chatButton = tester.widget<OutlinedButton>(chat);` and see how Flutter widget tests inspect resolved button background and border side colors.
4. Run `flutter test test/facility_details_test.dart` to verify the tests pass.


---

## 38. Facility Details: Chat Button Icon Replaced with Circular Speech Bubble (Lucide messageCircle) - November 6, 2026

### 1. Cause / Reason
The user provided a picture and requested: *"change icon also same as pic"*. The reference image showed a clean, circular outline speech bubble with a small downward-left pointer tail and an empty interior. Previously, `_FacilityBookingBar` used Material's `Icons.chat_outlined` (which renders a rectangular chat shape with horizontal message lines inside). Replacing it with `LucideIcons.messageCircle` (19 px) reproduces the exact circular outline speech bubble shown in the user's reference image.

### 2. Exact Files & Current Line Numbers
- `campushub/lib/module_app/screens/facility_details_screen.dart`:
  - **Anchor**: top imports (around line 12).
    - Added `import 'package:lucide_icons/lucide_icons.dart';`.
  - **Anchor**: inside `_FacilityBookingBar.build()` (around lines 1195, 1203, 1246).
    - Replaced `Icon(Icons.chat_outlined, size: 20)` with `Icon(LucideIcons.messageCircle, size: 19)` in both the compact column and standard row layouts for the Chat button, as well as the full-width `Message Admin` fallback button.
- `campushub/test/facility_details_test.dart`:
  - **Anchor**: top imports and widget test at line 424.
    - Added `import 'package:lucide_icons/lucide_icons.dart';`.
    - Updated expectation from `find.byIcon(Icons.chat_outlined)` to `find.byIcon(LucideIcons.messageCircle)`.

### 3. Changes Made
```dart
// facility_details_screen.dart:
Icon(LucideIcons.messageCircle, size: 19)

// facility_details_test.dart:
expect(find.byIcon(LucideIcons.messageCircle), findsOneWidget);
expect(
  tester.getRect(find.text('Chat')).left,
  greaterThan(tester.getRect(find.byIcon(LucideIcons.messageCircle)).right),
);
```

### 4. Functions & Data Flow
```
Facility Details bottom navigation bar
                   │
                   ▼
         _FacilityBookingBar
         ┌─────────┴─────────┐
         │                   │
showBookingAction == true   showBookingAction == false
         │                   │
         ▼                   ▼
OutlinedButton (Chat)       FilledButton (Message Admin)
- Icon: LucideIcons.messageCircle
- Container: Colors.white
- Border: #1A1851 (Navy)
```
- **Inputs**: Lucide icon asset definition (`0xf3cd`).
- **Outputs**: Exact circular speech bubble icon matching user reference screenshot.

### 5. Backend / API Behavior
None. Visual frontend presentation update only.

### 6. Database / Migration Impact
None.

### 7. Tests Performed
- `flutter test test/facility_details_test.dart`: **41/41 tests passed** in 10s.
- `flutter analyze --no-pub`: 0 issues found (`No issues found! (ran in 10.9s)`).

### 8. Remaining Limitations
None. Verified via automated widget tests and analyzer.

### 9. Beginner Safe Practice Exercise
1. Open `campushub/lib/module_app/screens/facility_details_screen.dart` and locate line 1195.
2. Note the use of `LucideIcons.messageCircle`: a circular speech bubble from the `lucide_icons` package.
3. Compare with `product_details_screen.dart` line 1689 which uses `LucideIcons.messageSquare`.
4. Run `flutter test test/facility_details_test.dart` to verify the widget finder matches `LucideIcons.messageCircle`.
