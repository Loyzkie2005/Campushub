# CampusHub: using design skills in Codex

## Windows "Hook failed" launcher fix (October 27, 2026)

### 1. Cause / reason

The project Impeccable hooks had a Windows override beginning with `if exist ...`, followed by a parenthesized command and `& exit /b`. Those are Command Prompt instructions. PowerShell rejects that text with `MissingOpenParenthesisInIfStatement` and `AmpersandNotAllowed` before the Node helper can start. This syntax mismatch was reproduced with PowerShell's parser. The recent accessible daemon error logs did not identify the user's exact failed hook invocation, so the connection to that particular visible message remains unverified; the project launcher defect itself is confirmed.

The [official OpenAI hook documentation](https://learn.chatgpt.com/docs/hooks) defines `commandWindows` as the Windows override and confirms that hooks run in the session working directory. It also explains that changed non-managed hook definitions may require review and trust again. The OpenAI Docs skill was used to verify these configuration rules.

### 2. Exact files changed / current line anchors

| File | Current line / anchor | Change |
|---|---|---|
| `.codex/hooks.json` | 12 and 25, `commandWindows` | Explicitly launch the Windows conditional with `cmd.exe /d /c` for PostToolUse and Stop. |
| `scratch/hook-fix/verify_hooks.py` | 1, module docstring; `for event` | Local verification helper reads the actual manifest and exercises both events. This ignored scratch helper is not a permanent application test. |
| `docs/codex-design-skills-guide.md` | 3, this section | Cause, configuration/data flow, checks, troubleshooting and learning exercise. |

The existing Impeccable detector source, Unix command, event matchers, timeouts and check behavior are preserved. No hook was disabled and no trust setting was bypassed.

### 3. Changes made

Both Windows overrides now use this command (shown as shell text, not JSON):

```text
cmd.exe /d /c "if exist .agents\skills\impeccable\scripts\hook.mjs node .agents\skills\impeccable\scripts\hook.mjs"
```

`cmd.exe` selects the interpreter that understands `if exist`; `/d` prevents Command Prompt AutoRun commands from changing this invocation; `/c` runs the supplied command and exits. The existing optional-install check remains: if the helper is absent, the command does nothing successfully. The old explicit `exit /b` is unnecessary after the single guarded Node call.

### 4. Functions, inputs/outputs and data flow

`hooks.json` is configuration rather than a Python/Dart function. Codex selects `PostToolUse` after a matching edit or `Stop` when the turn stops, supplies a JSON event through standard input, and uses the Windows override on Windows. The explicit Command Prompt child passes standard input/output through to Node. Node executes the unchanged `hook.mjs`, whose `main()` reads the event, chooses `runHook` or `runStopHook`, and returns the existing detector response and exit status.

```text
Codex event + JSON stdin
  -> commandWindows -> cmd.exe -> optional helper existence check
  -> node hook.mjs -> existing immediate/deep detector
  -> existing JSON stdout + process exit status -> Codex
```

The verifier loads the manifest using Python `json.loads`, then `subprocess.run` invokes each configured Windows command through PowerShell and Command Prompt. Its inputs are safe no-edit events and temporary fixtures; outputs are exit codes, captured stdout/stderr and a JSON result summary. A temporary echo helper confirms the complete event reaches Node unchanged, including when the working-directory path contains spaces. It does not edit a UI file or scan a real changed-file session.

Why this approach: the installed helper already handles its own event parsing and detector behavior. Selecting its intended shell fixes the launcher without rewriting the detector or removing its checks.

### 5. Backend / API behavior

None changed. This is Codex tooling configuration. No Django/Flutter server, endpoint, booking, payment, authentication or notification workflow changed or ran during verification.

### 6. Database / migration impact

None. No database connection, migration, live record operation or application restart was performed. Tests use subprocesses and disposable temporary helper files.

### 7. Tests performed

- Reproduced the original Windows override's two PowerShell parser errors before changing it.
- Parsed the updated manifest and ran **10 launcher checks**: both real hook events through PowerShell and Command Prompt (4); absent-helper guards for both events (2); event/stdin forwarding through both shells for both events using temporary helpers in directories with spaces (4). All exited successfully without stderr.
- The first verifier attempt used Python list escaping for a nested Command Prompt string, producing a test-harness quoting failure. Corrected the verifier to pass a raw Command Prompt command line; the final checks exercise the actual configured command correctly.
- A sandbox run could not access the virtual environment's base Python executable. The approved rerun outside that sandbox completed the checks. No application test suite, browser acceptance or live Codex hook-trust/reload verification is claimed.

To repeat: from the CampusHub root, run `backend\core\venv\Scripts\python.exe scratch\hook-fix\verify_hooks.py`. Expected summary: `"passed": 10`. The helper is an ignored local scratch artifact and may not be present in another checkout.

### 8. Remaining limitations / troubleshooting / safe exercise

The helper path remains relative to the session working directory, as in the original configuration. Start the session at the CampusHub root; supporting sessions started in subdirectories would require a separate path-resolution change. Node must remain available on PATH. These checks prove launcher execution and event forwarding, not the detector's findings on a changed UI.

If Codex still displays the previous error, reopen the project/session so it can load the updated definition. If it requests hook review, review the updated command in the hook controls; official documentation requires trust for the changed definition. Do not bypass that review. A new failure needs its actual event/error text to distinguish command launch, missing Node, timeout or trust state.

Safe exercise: read the two `commandWindows` entries and locate the matching event names and timeouts. Run the scratch verifier from the project root and confirm all ten checks pass. It creates its absent-helper and echo-helper cases in temporary directories, so you do not need to rename or delete the installed helper or change a real booking.

## UX/UI Agent Skills reference kit — October 20, 2026

The complete [plugin87/ux-ui-agent-skills](https://github.com/plugin87/ux-ui-agent-skills) reference kit is installed locally at `.agents/vendor/ux-ui-agent-skills`. Its version is **2.9.10**, commit `d271880757842ea3bee70d958cab80da5621eb81`. The 25 project skill entries already existed under `.agents/skills/` and matched this version. The isolated copy supplies the missing tokens, component specifications, framework adapters, examples and checking scripts without scattering files into CampusHub's root.

### How to use it

Give Codex the canonical skill path inside the complete kit. This matters because the existing flattened `.agents/skills/` copies refer to supporting files three directories above themselves; those files are absent at the project root. Inside the isolated kit, the same relative paths resolve correctly.

Use this prompt for an existing screen:

```text
Use .agents/vendor/ux-ui-agent-skills/.claude/skills/redesign/SKILL.md
to refine CampusHub's existing Facility Details screen in Flutter.
Use that directory as the skill root for all relative references.
Read AGENTS.md and CAMPUSHUB_CONTEXT.md first. Preserve existing GetX
routes, controllers, APIs and booking behavior. Use navy #1A1851,
gold #FCB315, white surfaces and the current mobile font rules.
Improve spacing and hierarchy, inspect the result, and report actual checks.
Do not run, restart or install the phone app.
```

Choose the skill that fits the task:

| Skill folder inside `.claude/skills/` | Purpose |
| --- | --- |
| `redesign` | Improve an existing screen while preserving behavior |
| `image-to-code` | Implement a screenshot/reference design |
| `design-screen` | Build a new screen |
| `design-component` | Specify a component's layout, states and accessibility |
| `design-code` | Implement a component with the existing Flutter or web stack |
| `a11y-audit` | Check accessibility |
| `design-review` | Review an interface before changing it |
| `ux-writing` | Improve labels, errors and empty-state text |

In Codex, selecting a skill with `$` or specifying its full `SKILL.md` path is clearer than treating Claude's slash commands as Codex commands. The repository's `.claude` folder is used here as a reference directory; Claude hooks and plugin registration were not enabled. Existing project skill entries are available on the next turn; use the canonical paths above to load their complete references.

### How files and checks work

The selected `SKILL.md` is the input instruction file. It leads the agent to `frameworks/` for Flutter/web guidance, `components/` for specifications and `tokens/` for reference values. Proposed code still belongs in CampusHub's existing files and must follow CampusHub rules. Generic kit palettes and sample data are not production settings.

For example, `frameworks/adapters/flutter.md` informs Flutter implementation; it does not convert the app to a web framework. Checking scripts receive a file or directory path, inspect that input, and print findings with an exit status. They are not loaded by Django or Flutter. Browser checks need their own dependencies and cannot prove a Flutter screen's native layout; use appropriate Flutter tests and native screenshots too. The kit's `accuracy_report.mjs` checks its own reference kit, not CampusHub's overall quality. See the upstream `docs/INSTALL.md` for command details.

Safe practice: ask Codex to use the canonical `design-review/SKILL.md` to review a screenshot of one screen without editing files. Confirm that its findings refer to visible evidence and CampusHub's actual palette. Then request one small spacing change and its appropriate verification.

### Installation report and troubleshooting

1. **Cause / reason:** Existing skill-only copies lacked the support kit required by their relative links.
2. **Exact files:** Added isolated repository `.agents/vendor/ux-ui-agent-skills/`; updated this guide at the `UX/UI Agent Skills reference kit` anchor. A separate inspection clone is under `scratch/skill-install-review/ux-ui-agent-skills/`.
3. **Changes made:** Downloaded the complete repository using Git; did not execute its installer, hooks or gate scripts. Existing project skill files and root `AGENTS.md` were preserved.
4. **How it works:** Canonical skill paths point inside the complete repository, where `../../../tokens` and other support references resolve to the isolated kit root.
5. **Backend / API behavior:** None changed; no server or app restart, API request or notification sent.
6. **Database / migration impact:** None.
7. **Verification:** Counted 25 canonical skills and 25 matching existing project entries; confirmed all eight required support folders, resolved each canonical skill root, and parsed all 14 token JSON files. Checked version and commit. No accessibility, browser gate or CampusHub UI quality pass is claimed.
8. **Limitations:** This is a project-local reference installation, not a global Codex plugin. Automatic approval review rejected the root installer because its broad file copy could alter project files and future agent behavior. The isolated Git download was approved as a safer alternative. Browser-gate dependencies are not installed. If a flattened skill reports `KIT_MISSING`, use its canonical vendor path instead; do not copy or overwrite root `AGENTS.md`. CampusHub's current rules override the older examples later in this guide, including gold #FCB315 and mobile Poppins with existing identity/wordmark exceptions.

---

Installed October 4, 2026 in the personal Codex skills directory, alongside the existing skills. They will be available on your next turn. If a new skill does not appear, restart Codex and try again. [Official skill usage and discovery documentation](https://learn.chatgpt.com/docs/build-skills).

## Installed skills

| Skill | Use it for | Installed entry point |
| --- | --- | --- |
| `ui-ux-pro-max` | UX decisions, layout, accessibility, chart choices, and searchable web/Flutter guidance | `C:\Users\leste\.codex\skills\ui-ux-pro-max\SKILL.md` |
| `design-system` | Reusable color, typography, spacing and component tokens, including component states | `C:\Users\leste\.codex\skills\design-system\SKILL.md` |
| `frontend-design-codex` | Implementing a coherent interface in the existing frontend and verifying it in a browser | `C:\Users\leste\.codex\skills\frontend-design-codex\SKILL.md` |

Sources: [UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), [Design System](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/main/.claude/skills/design-system), and [Frontend Design Codex](https://github.com/KilimiaoSix/agent-skills/tree/main/skills/frontend-design-codex). These are community skills. The Frontend Design Codex source is the maintained collection, rather than its archived standalone repository.

## A practical workflow

Start with one screen or section. Give Codex the target screen, screenshot or local route, what you want to improve, and what should be preserved. Naming the skill explicitly makes the intended workflow clear. In Codex CLI or the IDE extension, type `$` to select a skill or use `/skills`; plain language such as “Use ui-ux-pro-max” also communicates which skill to load. [Official invocation guidance](https://learn.chatgpt.com/docs/build-skills).

For an existing screen, use UI/UX Pro Max to assess the specific UX issue. Use Design System when reusable tokens or component rules need to be established. Use Frontend Design Codex to implement the selected direction. These roles can be combined in one request; the existing application remains the starting point.

Impeccable is still installed and useful for a focused refinement pass. The existing `design-taste-frontend` skill remains installed; its declared scope favors landing pages, portfolios and redesigns rather than operational dashboards. Choose the workflow that fits the surface instead of loading every design skill for every small change.

### 1. Review before editing

```text
Use $ui-ux-pro-max to review the CampusHub Super Admin Marketplace
Analytics section. Inspect the existing implementation and this screenshot.
Identify problems with hierarchy, spacing, icons, accessibility and mobile
behavior. Recommend specific changes. Do not edit application files yet.
Follow AGENTS.md and the CampusHub project context.
```

### 2. Establish reusable rules

```text
Use $design-system to document CampusHub's existing design system from
AGENTS.md, current CSS and the provided screenshots. Define reusable
tokens for colors, Montserrat typography, spacing, borders and component
states. Cover buttons, inputs, tables, filters and dashboard cards.
Keep navy #1A1851, gold #FCB316, white/light surfaces, and the existing
institutional style. Do not replace the application theme or add Tailwind.
Save the proposed documentation under docs/design-system/.
```

### 3. Implement one section

```text
Use $frontend-design-codex to improve the existing CampusHub Marketplace
Analytics section using the agreed design-system rules. Add consistent
outline icons, improve alignment and make the mobile layout usable.
Keep Sales Overview, Sales Trend, Top 5 Best-Selling Products, and Sales
by Product Categories. Keep real database-driven values and existing filters.
Sales Trend must use sales bars and a completed-orders line, with zero-filled
date buckets still visible. Distinguish a failed API request from zero sales.
Use the existing Django templates, CSS and JavaScript. Verify desktop/mobile
rendering and the core interactions, then report changed files and checks.
```

### A combined request

```text
Use $ui-ux-pro-max for UX guidance, $design-system for reusable tokens,
and $frontend-design-codex for implementation to refine CampusHub's
Super Admin Dashboard. Inspect the current code and screenshot first.
Work only on Marketplace Analytics. Follow AGENTS.md and my latest project
context. Keep navy #1A1851, gold #FCB316, white/light surfaces and Montserrat.
Preserve the existing Django architecture, real analytics data, navigation
and filters. Use compact institutional styling and consistent outline icons.
Keep zero-value charts visible. Verify desktop/mobile and report the results.
```

For Flutter, name the exact screen and state that the implementation must use the existing Flutter architecture and theme. UI/UX Pro Max includes Flutter-specific search guidance; Frontend Design Codex primarily covers web/frontend implementation and browser verification. Do not substitute a web page for a requested Flutter screen.

## CampusHub constraints to preserve

- The supplied palette, Montserrat and institutional style take priority over generic palette/font suggestions from search results.
- Django/PostgreSQL remain the source of truth. FastAPI remains for chat.
- Marketplace analytics use completed paid Cash on Pickup orders; never add fake production metrics.
- A UI refinement preserves routes, permissions, order/booking behavior and factual copy unless the task explicitly changes them.
- Use existing components and icons where suitable. Do not switch frameworks just because a skill offers a starter template.
- Test loading, zero-data, populated and failure states separately, including responsive behavior and keyboard focus.

## Optional local tool commands

You usually only need to send a design prompt. For a direct UX search in PowerShell, the existing project interpreter works without installing another Python:

```powershell
& 'C:\Users\leste\Desktop\CAMPUSHUB\backend\core\venv\Scripts\python.exe' `
  'C:\Users\leste\.codex\skills\ui-ux-pro-max\scripts\search.py' `
  'error summary validation' --domain ux
```

Flutter guidance:

```powershell
& 'C:\Users\leste\Desktop\CAMPUSHUB\backend\core\venv\Scripts\python.exe' `
  'C:\Users\leste\.codex\skills\ui-ux-pro-max\scripts\search.py' `
  'form validation' --stack flutter
```

The design-system token generator accepts a token JSON configuration:

```powershell
node 'C:\Users\leste\.codex\skills\design-system\scripts\generate-tokens.cjs' --help
```

Review generated recommendations against the fixed CampusHub rules before adopting or persisting them. The installation did not generate or apply a production theme.

## Installation report

**Cause / reason:** Install the three requested design workflows and provide a practical CampusHub usage guide.

**Exact folders/files and local adjustments:**

| Folder / file | Approximate line and anchor | What changed / why |
| --- | --- | --- |
| `C:\Users\leste\.codex\skills\ui-ux-pro-max\` | `SKILL.md`, line 37, “Running the search tool” | Installed 77 files. Script examples resolve the containing skill directory in Codex instead of depending on Claude's plugin environment variable. |
| `C:\Users\leste\.codex\skills\design-system\` | `SKILL.md`, frontmatter | Installed 28 files. Removed Claude-specific `argument-hint`, which the Codex validator does not accept. All token resources remain included. |
| `C:\Users\leste\.codex\skills\frontend-design-codex\` | `SKILL.md`, line 1 | Installed 16 files from the maintained source, retaining its existing Codex UI metadata and license notices. |
| `docs/codex-design-skills-guide.md` | “A practical workflow” | Added this guide, examples, sources and installation notes. |

UI/UX Pro Max and Design System were pinned to source revision `477bcb28c9812b385cb51a4605ddf30d7b2266e2`. Frontend Design Codex was pinned to `6095b91576c0295edd8a431d1e8f12abd077c509`. Upstream license notices are included. Existing skills were not overwritten.

**How it works:** Codex loads a named skill's instructions and, when needed, its bundled local scripts and references. Naming each skill's role keeps the combined request focused.

**Backend / API behavior:** No application/backend/API changes.

**Database / migration impact:** None. No live records or migrations were changed.

**Verification:** All three packages passed the Codex skill validator. Local UX and Flutter searches returned matching guidance. A scratch token-generation example resolved primitive, semantic and component references correctly. Installed-file integrity was checked against the reviewed staging copies.

**Limitations / assumptions:** “Design System Skill” was interpreted as the companion `design-system` skill in the UI/UX Pro Max bundle. Installation does not redesign a screen by itself. Skill-selector refresh is handled on the next turn, with restart as a fallback if discovery does not refresh. Optional slide/brand integrations were not installed because the requested scope is these three UI design skills.

Review copies and the token example are under `scratch/skill-install-review/`. PyYAML was installed only into `scratch/skill-validation-deps/` to run the official validator; CampusHub's virtual environment dependencies and requirements files were left unchanged.
