# CampusHub Bookings: reusable project context

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
