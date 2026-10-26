# CampusHub turnover readiness checklist

## Source publication procedure ? October 26, 2026

1. **Cause / reason:** The repository has many approved pending Django/Flutter changes, but no root ignore policy. Review output, private uploads, local tool state and temporary files must not accompany application source. An old zero-byte index lock and another active staging process make direct staging in the main working tree inappropriate.
2. **Exact files changed:** `.gitignore:1` adds repository-wide source-publication exclusions; this section of `docs/system-turnover-checklist.md` documents the procedure; the latest entry in `CAMPUSHUB_CONTEXT.md` records the user's approved publication scope. Application files are published as they already exist, without changing business logic for this Git task.
3. **Changes made:** Ignore local review output, installers, assistant/editor state, private environment/key files, database dumps, uploads, caches and device-generated build registrations. Required application assets, vendored runtime libraries, dependency lockfiles, client Firebase configuration and feature documentation remain source inputs. Ignore rules do not erase already tracked history or remove local files.
4. **How it works:** A local manifest takes Git's changed/untracked source paths, applies the approved exclusions, checks file sizes and scans for credential patterns without printing values. An isolated checkout of the current main commit receives only selected files/deletions. Their hashes are compared with the working source before a commit is created. Existing Git author identity is reused for this commit only. A normal non-forced push must reject remote divergence. No deployment or migration command belongs in this flow.
5. **Backend / API behavior:** None. Git copies and version-controls source; it does not run application writers, change permissions or activate database schema.
6. **Database / migration impact:** None. Source migration files may be versioned, but are not applied. Backups, private media and working records remain local.
7. **Verification:** Current source selection and secret-location reports are saved under ignored `scratch/github-push-review-20261026/`. Push success must be verified by comparing the remote branch commit with the new local commit. Existing feature test reports remain in their guides; this publication procedure does not certify that every pending feature has been retested together. A push is not institutional acceptance or a deployment.
8. **Remaining limitations:** The original working index/lock and any other running Git process must remain untouched. If publication uses an isolated checkout, the original local main branch can remain behind the published main commit until the existing Git operation is resolved. Do not force-push, delete another process's lock or run a hard reset to hide that state.

No runtime function is added. Inputs are approved source paths and their current bytes; outputs are a review manifest, commit/tree objects and the verified remote revision. Source flows from working files to the isolated staging index, then to a commit and GitHub. For example, `backend/core/modules/marketplace/templates/marketplace/pages/bundle_monitoring.html` is source, while `scratch/dataset-kpis-20261026/dataset-1440.png` is local review output. This separates deployable implementation from verification artifacts without deleting either.

Safe practice: use `git check-ignore scratch/example.txt` to confirm review output is ignored, then inspect `git status --short --untracked-files=normal` and confirm private environment/upload files are absent from the proposed manifest. Inspect the commit's file list before pushing and verify the resulting GitHub hash afterward. Never paste credentials into logs or seed application records for a Git check.

Reviewed October25,2026. This records confirmed materials and remaining acceptance work. No BEU/ICT maintainer, training completion, source release or deployment approval is invented or assigned here.

| Area | Existing evidence | Remaining acceptance work |
| --- | --- | --- |
| Source release | Current Django/Flutter/chat source and feature guides exist. | Review the pre-existing dirty working tree, approve the exact release, tag/package it and verify an independently obtained copy. No release was created by this task. |
| Installation/deployment | [Deployment guide](kamatera-web-deployment.md) and repository dependency/configuration files. | Perform a clean installation rehearsal and document the exact deployed revision, service accounts, environment/profile and rollback procedure. FIFO is not deployed/activated by this task. |
| Database configuration | [Database/backup guide](database-backup-neon.md) documents local versus server separation. | Have the receiving team verify its intended target, permissions and private configuration; never copy secrets into a public guide or repository. |
| Backup/recovery | FIFO pre-cutover dump was restored successfully into a disposable database; manifest and proposed balances are recorded in [FIFO guide](fifo-inventory.md). | Agree backup schedule, private storage/retention, off-machine recovery and recurring restore drills. A local successful restore is not proof of off-site disaster recovery. |
| Administrator access | Existing roles, scoped permissions, tab sessions and protected-final-Super-Admin rules. | Approve named receiving accounts, transfer secrets through an agreed private channel, test access and document credential rotation/revocation. No personnel or passwords are assigned here. |
| BEU/ICT training | Inventory/FIFO/order/report guides include safe isolated exercises. | Schedule and record staff training, demonstrate receipt/allocation/cancellation/report exports and obtain acceptance. Training has not been certified complete. |
| Troubleshooting | Feature guides explain errors, data flow, checks and current limitations. | Agree escalation contacts, incident records, monitoring checks and access to required logs. |
| Maintenance ownership | Django remains the source of truth; FastAPI remains messaging-only. | Institution must name the accountable maintainer, backup operator, access administrator and escalation route, with cover arrangements and approval authority. |

## Operating data flow and training example

Authorized administrator → existing scoped Inventory workspace → `receive_stock` → `fifo.receive` → Product.save/audit hook → actual batch and available quantity. Buyer order → existing reservation service → exact FIFO allocations → existing completion or cancellation. Report builder → existing preview/CSV/PDF/native print. The [FIFO implementation guide](fifo-inventory.md) names inputs, outputs, exact files and lines, tests and remaining limits.

Example to explain during training: an isolated receipt of20followed by30and an order of25reserves20from the first batch and5from the second. Cancellation restores those same batches once; completion does not deduct again. This example must not be seeded into working inventory.

## Safe practice and verification

Use an isolated installation/test database, run the targeted FIFO tests, and have the trainee explain the0/25remaining balances and the restored20/30balances. Verify CSV/PDF records against the selected actual test orders and distinguish physical units from derived bundles. Rehearse a restore into a newly named disposable database, checking quantities and active reservations before removing that disposable database. Do not restore over a working database for a training exercise.

This checklist adds documentation only. It does not transfer ownership, authorize a production cutover, change APIs/models, or claim training/deployment completion. Actual code/schema tests and the recoverable local backup are documented in the linked FIFO guide; organizational acceptance items above remain open.
