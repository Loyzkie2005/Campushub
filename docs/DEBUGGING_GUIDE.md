    # CampusHub debugging guide and issue template

Created: 2026-10-06. This is a guide and a reusable issue template, not a claim that every example below is a current bug.

## User.Meta type warning fix - 2026-10-08

### 1. Cause / reason

Confirmed from `accounts/models.py`: `User` subclasses Django's `AbstractUser`, but its nested `Meta` was an unrelated class. Pylance treats `Meta` as a class attribute and requires the overriding class to be compatible with `AbstractUser.Meta`. This was a static typing diagnostic, not a database failure.

### 2. Exact files changed

- `backend/core/accounts/models.py:2`, `TYPE_CHECKING`: import the standard typing flag.
- Same file, line 7, `if TYPE_CHECKING`: define `_UserMetaBase` for the appropriate reader.
- Same file, line 56, `class Meta(_UserMetaBase)`: use the compatible base while retaining the existing `db_table`.
- `docs/DEBUGGING_GUIDE.md:5`, `User.Meta type warning fix`: this explanation and verification report.

### 3. Changes made

Added a private base alias and changed only the nested `User.Meta` inheritance. No fields, methods, permissions, checker configuration or diagnostic suppressions were added/removed. A direct `class Meta(AbstractUser.Meta)` was tried during investigation but not retained: inheriting Django's verbose-name options made `makemigrations --check --dry-run` propose an options migration even though the visible values were the same.

### 4. How it works: inputs, outputs and data flow

`TYPE_CHECKING` is recognized as true by static analyzers and is false when Python runs the application. Its input is the analysis/runtime context; its output selects the base class:

```python
if TYPE_CHECKING:
    _UserMetaBase = AbstractUser.Meta  # Compatible type for Pylance/Pyright.
else:
    _UserMetaBase = object             # Same runtime base as the original Meta.
```

The nested `Meta` supplies configuration to Django's model metaclass. At runtime, Django still reads only the existing `db_table = "campushub_accounts_user"` declaration into `User._meta`. No request inputs or user records flow through this helper. Static analysis sees `User.Meta` as a subclass of the inherited type, resolving the override mismatch. This approach keeps typing accurate without changing runtime options just to satisfy an editor.

### 5. Backend / API behavior

Unchanged. The real `User` remains concrete and continues using the existing authentication table, fields and access rules. No endpoint or serializer changed.

### 6. Database / migration impact

None in the final implementation. The final migration check reports `No changes detected`. The investigation used dry-run checks only; no migration file was created or applied for this fix.

### 7. Verification results

- `npx --yes pyright --outputjson backend/core/accounts/models.py`: one file analyzed, zero errors, zero warnings.
- From `backend/core`, `venv/Scripts/python.exe manage.py check`: no issues.
- `venv/Scripts/python.exe manage.py makemigrations --check --dry-run`: no changes detected.
- Read-only Django shell assertions confirmed `abstract=False`, table `campushub_accounts_user`, names `user`/`users`, empty custom permissions and exactly the original `User._meta.original_attrs` dictionary. No database records were read or written for those assertions.

Safe practice: in a separate scratch Python file, define a parent class with a nested `Meta` and a child class with an unrelated nested `Meta`. Run Pyright on that file. Then change the child's declaration to `class Meta(Parent.Meta)` and rerun; explain why inheritance makes the override compatible. Do not change the production `TYPE_CHECKING` flag or disable diagnostics to try this exercise.

### 8. Remaining limitations / troubleshooting

The CLI check uses Pyright, the type-checking engine used by Pylance; the running VS Code editor was not controlled. If an old warning remains, save the file and restart the Python language server or reload the editor window. Confirm that its interpreter is `backend/core/venv/Scripts/python.exe`. Avoid silencing the entire override diagnostic: that would hide other genuine type errors. Line numbers in older reports below are historical; use their code anchors.

## 1. Cause / Reason

You requested debugging information in the project documentation. The aim is to help you locate a problem, collect evidence and test a small fix yourself. A guess becomes a confirmed bug only after you can reproduce the difference between expected and actual behavior.

## 2. Exact Files Changed

This guide is added at `docs/DEBUGGING_GUIDE.md:1`. Its use is recorded in `CAMPUSHUB_CONTEXT.md:9`, and the current column-color report links it. The accompanying dashboard change is documented separately in [dashboard-column-heading-colors.md](dashboard-column-heading-colors.md), including exact application files and line numbers.

The follow-up clarification on 2026-10-06 changed `AGENTS.md:8` (the every-change documentation rule), `CAMPUSHUB_CONTEXT.md:11` (standing rule), and this guide's standing documentation workflow below. This follow-up changed documentation only.

## 3. Changes Made

Added an investigation workflow, a map of relevant dashboard functions, common troubleshooting cases, a safe practice exercise and a reusable issue record. This guide does not install a debugger, enable production debug settings or change application behavior.

The follow-up makes this documentation a requirement for every code fix or change, rather than only when a separate explanation is requested.

## 4. How It Works

### Standing documentation workflow for every code change

1. Read the project rules/context and inspect the relevant implementation.
2. Create or update the existing feature guide in `docs/`; a small edit does not need a duplicate document.
3. Record what was added, changed, removed or moved, with current file/line locations and nearby function or selector names.
4. Explain the cause, the function inputs/outputs and how data flows through the changed code. Include a small annotated example and safe practice exercise when useful.
5. Add debugging steps: how to reproduce the symptom, what evidence to inspect, and why the fix addresses the confirmed cause. Label unconfirmed causes as hypotheses.
6. Report all eight project-required items: reason, files, changes, how it works, backend/API behavior, database/migrations, tests and limitations.
7. List tests actually run and their results; state when a check was not run. Record remaining issues using the issue template rather than inventing or hiding them.
8. Link the relevant guide in the completion reply so the user can learn from the change.

This is a documentation workflow, not a runtime function: its input is the inspected change and verification evidence; its output is a reviewable explanation in the appropriate feature guide. The rules file and context preserve the requirement for future work.

### Follow one problem from symptom to evidence

1. **Describe one observable symptom.** For example, “Sales share text is gray after refresh,” rather than “the dashboard is broken.” Record the page, account role, filter selection and whether sample mode is enabled.
2. **Reproduce it.** Write the clicks and inputs in order. Try the same steps again. Capture expected and actual behavior separately.
3. **Identify the layer.** Incorrect spacing/color is usually CSS. A button doing nothing can be JavaScript or a failed API call. A wrong value might come from filters, aggregation or records. These are starting hypotheses, not conclusions.
4. **Inspect before editing.** Use Elements/Computed for CSS, Console for JavaScript, Network for API requests, and the Django terminal traceback for server errors. Record the exact error and relevant file/line; do not copy authentication tokens, cookies or database passwords into notes.
5. **Find the source.** Search the visible label or class with `rg`, then read the surrounding code and the function callers. Example from the project root:

   ```powershell
   rg -n --glob '*.html' 'Sales share' backend/templates
   rg -n 'marketplace-category-table' backend/static/components/css
   ```

6. **Make the smallest relevant change.** Predict what it will do before saving. Change one cause at a time so you know which change affected the result.
7. **Verify the original steps and one nearby case.** For a hover fix, check mouse movement and keyboard focus. For a filter fix, check another period and an empty state. For CSS, inspect the computed value rather than relying only on appearance.
8. **Record the outcome.** Mark the issue verified only after those checks pass. If it still fails, record the remaining symptom and your evidence rather than declaring it fixed.

### Understand the dashboard's functions and data flow

Current line numbers are reference points; search by the function name when later edits shift them.

| Location / function | Input | Output / responsibility | Useful debugging evidence |
| --- | --- | --- | --- |
| `backend/core/modules/reports/views.py:914`, `admin_dashboard_page(request)` | Authenticated request, user role and filters | Dashboard context and rendered page | Django traceback, rendered template, role-specific route behavior. |
| `backend/core/modules/reports/views.py`, `admin_dashboard_api(request)` | Authenticated API request with date/grouping parameters | Dashboard JSON response | Network status, request parameters, returned values. |
| `backend/static/components/js/admin_dashboard_filter.js:479`, `load(period, salesOnly)` | Requested date range and update scope | Fetches the existing API; renders chart-only or global updates | Network request, console error, busy/error state, selected scope. |
| Same JavaScript, `render(payload, sampleOnly)` at line 298 | Dashboard payload | Updates relevant DOM content | Compare response values with the displayed text. |
| Same JavaScript, `renderSalesTrend(payload)` at line 282 | Sales trend payload | Updates only the chart presentation | Grouping, labels and series; verify right-hand cards remain unchanged. |
| Same JavaScript, `categoryAtPointer(event)` at line 51 | Pointer coordinates and category segment ranges | Matching SVG circle or no match | Coordinate/angle calculation, chosen category, center/outside behavior. |
| Same JavaScript, `showCategoryTooltip()` at line 37 | Segment and display coordinates | Tooltip text/position and selected segment class | Segment metadata, `is-active`, actual tooltip text. |
| Same JavaScript, `hideCategoryTooltip()` at line 32 | Dismissal or refresh event | Clears tooltip and selected class | Escape, outside tap, moving away and data replacement. |
| `backend/static/components/css/admin_dashboard_palette.css:14` | Dashboard-scoped heading elements | Navy, white, semibold headers | Matched rules, Computed styles and loaded stylesheet version. |

The main flow is actual database records → Django aggregation → HTML context/API JSON → JavaScript-rendered elements → CSS presentation. Compare the result at each boundary. If JSON is correct but displayed text is wrong, investigate rendering; if the text is correct but its color is wrong, investigate CSS. Do not alter database records to solve a styling problem.

### Read a small diagnostic example

Run this read-only snippet in the browser Console while the dashboard is open:

```javascript
const heading = document.querySelector('.marketplace-category-table thead th:nth-child(2)');
if (heading) {
    const style = getComputedStyle(heading); // The final styles after CSS rules compete.
    console.table({
        label: heading.textContent.trim(), // Expect Sales share.
        color: style.color,                // Expect rgb(26, 24, 81).
        weight: style.fontWeight,          // Expect 600.
        background: style.backgroundColor // Expect rgb(255, 255, 255).
    });
}
```

`querySelector()` takes a CSS selector and returns the first matching element, or `null`. `getComputedStyle()` takes that element and returns its final resolved CSS values. `console.table()` displays the diagnostic values; it does not save or modify database records. A correct value in this output helps distinguish a CSS problem from a font-rendering or screen-display difference.

### Common symptoms to investigate

| Symptom | First check | Relevant code / action |
| --- | --- | --- |
| New CSS does not appear | Network stylesheet URL/version and Computed rules | Ctrl+F5; inspect the winning rule and template stylesheet link. Do not keep adding duplicate overrides. |
| Sales Overview remains zero | Applied date range and completed **paid** Cash on Pickup records | Compare the API response and database-backed aggregation; an honest empty state is expected when no qualifying records exist. |
| Category does not enlarge on hover | Console errors, populated chart and active class | Inspect `categoryAtPointer()`, segment metadata and CSS transform. An empty category card has no segment to hover. |
| Hover feels unstable at the edge | Geometry and hit-detection bounds | The `1.055` scale and outer bound `113` work together; see [donut hover zoom](category-donut-hover-zoom.md). |
| Daily/Weekly/Monthly seems to change other cards | Whether the **global date filter** or chart grouping was used | Chart grouping is local to Sales Trend; global dates and Refresh update all cards. See [filter scope](sales-chart-independent-grouping.md). |
| API request fails | Status code, response message, selected parameters and Django traceback | Inspect `load()` and the API view. Keep server-side permissions; do not remove checks to bypass the error. |
| Chart animation measurement is inconsistent in a headless test | Virtual time versus real compositor animation | Inspect its final state or use an actual mouse event with a real-time wait. The preview-only animation finish is not production behavior. |

### Safe practice exercise

1. Select the Sales share heading in Developer Tools → Elements.
2. Temporarily change its color to gold in the Styles panel. This affects only your browser session.
3. Run the diagnostic snippet. It should now report the temporary color if your rule wins. If it does not, inspect the competing rule's specificity or `!important` flag.
4. Reload the page to discard your temporary edit. Run the snippet again and confirm navy returns.
5. Explain the result in one sentence: “The database value stayed the same; only the browser's presentation changed.”

This exercise teaches observation, CSS precedence and verification without changing source files or live records.

### Reusable issue record

Copy this section into the relevant feature guide when a real symptom is reported. Fill in evidence; leave unknown causes marked unknown.

```markdown
### Issue: [short observable symptom]
- Status: Needs reproduction / Confirmed / Fixed, awaiting verification / Verified
- Reported on: [date]
- Page and account role: [path, role; omit tokens]
- Filters / data mode: [date range, grouping, real or sample]
- Expected behavior: [what should happen]
- Actual behavior: [what happens]
- Reproduction steps: [numbered steps]
- Evidence: [exact error, API status, computed style, screenshot or test output]
- Suspected cause: [hypothesis, or unknown]
- Confirmed cause: [evidence-backed cause, or not yet confirmed]
- Relevant file / function / current line: [location and nearby anchor]
- Fix attempted: [small specific change, or none]
- Verification: [checks run and results; distinguish passed from not run]
- Remaining work / limitations: [next concrete step or untested case]
```

No new unresolved application bug was confirmed while creating this guide. The table above is troubleshooting guidance. Known limitations of recent work remain recorded in each feature report; they should not be relabeled as confirmed bugs without reproduction evidence.

## 5. Backend / API Behavior

The documentation request does not change backend/API behavior. Investigations must preserve Django as the source of truth, existing RBAC and the independent FastAPI chat boundary.

## 6. Database / Migration Impact

None. The diagnostic snippet and practice exercise do not write database records. No migrations are introduced.

## 7. Tests Performed

Referenced paths, function names and current code anchors were checked against the workspace. The accompanying column-color changes were checked in two Chrome preview cases and both stylesheets parsed successfully; details are in [the column-color report](dashboard-column-heading-colors.md). The troubleshooting steps for unrelated symptoms are instructions, not claims that those scenarios were reproduced or tested during this change.

For the follow-up standing-rule clarification, only the documentation references, required eight report sections and Markdown diff were checked. Application tests were not rerun because no application code changed.

Useful local checks, run from the project root when relevant:

```powershell
# Check JavaScript syntax; this does not prove all runtime behavior works.
node --check backend/static/components/js/admin_dashboard_filter.js

# Existing fixture-based integration check; does not seed live orders.
node scratch/sales-overview-system-test/check-in-dashboard-sample.cjs
```

Choose tests that exercise the changed behavior. A passing syntax check alone cannot establish that permissions, calculations or user interactions are correct.

## 8. Remaining Limitations

This document is not an automatic error scanner or a complete bug inventory. It does not guarantee that all existing features are error-free. Function line numbers will shift as code changes; use the anchors to locate them. Confirm problems with actual evidence, and record untested cases honestly.
