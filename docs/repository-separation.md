# Separate CampusHub web and Flutter repositories

## 1. Cause / reason

The user requested separate GitHub projects and exact commit subjects: `Updatw` for the web and `Uploaded Mobile` for Flutter. The existing web repository is [Loyzkie2005/Campushub](https://github.com/Loyzkie2005/Campushub). [Loyzkie2005/CampusHub-Mobile](https://github.com/Loyzkie2005/CampusHub-Mobile) already existed as a public repository with one README-only initial commit, so that repository is reused rather than duplicated.

## 2. Exact files and repository metadata changed

- Root `.gitignore`, anchors `Local assistant/editor state`, `Private environment and database material`, and `Flutter is independently versioned`: ignore the independent mobile checkout, credentials, database files and local tooling.
- `campushub/.gitignore`, anchors `Local editor/assistant state`, `Private credentials`, `Historical backend/database experiments`, and `Recreated by Flutter tooling`: make the Flutter package safe to version independently, without inheriting the parent's ignores.
- Root `README.md`, anchors `Start here`, `Repository structure` and `The Flutter client is independently versioned`: link to the separate mobile source and explain the adjacent local checkout.
- `campushub/README.md`, introductory project links and feature-guide links: use GitHub links to the web documentation so they work from a standalone mobile clone.
- `CAMPUSHUB_CONTEXT.md`, newest repository-split entry: persist the repository boundaries.
- This guide records the commands, checks and limitations. No runtime function was changed specifically for repository separation; existing pending application changes are included in the requested publication.
- Root Git index: stop tracking `campushub/`, assistant/editor state, scratch output, existing database backups and the development SQLite database. These files are retained on disk where they existed. The mobile folder is a normal ignored nested repository, not a submodule.
- `campushub/.git/`: independent repository metadata and origin, based on the mobile repository's existing initial commit. GitHub credentials remain in the system's Git credential manager, never in a URL, source file or committed script.

## 3. Changes made

The root repository's `main` is based on the existing GitHub web tip, preserving its history and current local application files. The mobile repository's `main` is based on its own README-only tip. Neither remote history is replaced or force-pushed. The root removal is from Git tracking only, so the Flutter folder, working database, private environment and local backups remain on this computer. Historical web commits still contain their former tree; separation does not rewrite published history.

The mobile repository contains Flutter Dart source, assets, tests, platform projects, package metadata, development scripts and mobile documentation. Legacy experimental `campushub/backend/` and `campushub/database/` are retained locally and ignored by the Flutter repository; authoritative Django/FastAPI code stays in the web project's `backend/`. Firebase client app configuration is part of the client source; server service-account keys and signing material are excluded.

## 4. How it works / data flow

Git chooses the nearest `.git` directory above the current working directory. Commands issued at `CAMPUSHUB` use the web repository. Commands issued inside `CAMPUSHUB/campushub` use the independent Flutter repository. A commit records that repository's staged files; `git push origin main` sends that commit to its own origin. The shared code workspace stays usable in the current IDE.

```text
CAMPUSHUB/.git/             -> Loyzkie2005/Campushub
CAMPUSHUB/backend/          -> Django + chat source tracked by web Git
CAMPUSHUB/docs/             -> shared project/feature guides tracked by web Git
CAMPUSHUB/campushub/.git/   -> Loyzkie2005/CampusHub-Mobile
CAMPUSHUB/campushub/lib/    -> Dart source tracked only by mobile Git
```

Annotated read-only example:

```powershell
# Run from CAMPUSHUB: these identify the two independent remotes.
git remote get-url origin
git -C campushub remote get-url origin
# Root must list no Flutter files; mobile must list its Dart entry point.
git ls-files campushub
git -C campushub ls-files lib/main.dart
```

New checkout from a parent folder:

```powershell
git clone https://github.com/Loyzkie2005/Campushub.git CAMPUSHUB
git clone https://github.com/Loyzkie2005/CampusHub-Mobile.git CAMPUSHUB/campushub
```

Future publication, using the requested subjects for this upload:

```powershell
# In CAMPUSHUB, inspect/stage intended web files before committing.
git status --short
git commit -m "Updatw"
git push origin main

# Independently inspect/stage intended mobile files.
git -C campushub status --short
git -C campushub commit -m "Uploaded Mobile"
git -C campushub push origin main
```

Those commit commands require staged changes. Do not run a root `git add -f campushub` or turn the folder into a gitlink; that would undo the requested separation. Do not copy `.env`, service accounts, production backups, signing keys or build output into either repository.

## 5. Backend / API behavior

Repository separation changes neither API paths nor client/server logic. Django remains authoritative for accounts, marketplace, facility availability and bookings. FastAPI remains chat-only. Flutter continues using its configured API origin; a new clone must use the existing environment-specific setup guides. Pushing code alone does not perform a production deployment or migrations.

## 6. Database / migration impact

No data records or schemas are changed by this split. Database backups and development database files were removed from the current web tree's tracking, not deleted locally. Existing schema migrations remain source files and are published normally. No migration or production write is run as part of pushing.

## 7. Verification and actual results

- Confirmed authenticated GitHub account `Loyzkie2005`, both existing repository URLs, current default branches and initial mobile README-only tree through GitHub API using the stored Git credential without printing credentials.
- Fetched the latest web `main` and synchronized the Git index/base while preserving the working files; the mobile Git base uses its separate existing history. No force push is used.
- Staged-path/size/content scan checks private-key material, common GitHub/AWS credentials, credential-bearing database URLs, literal password assignments, forbidden local output and oversized files. Password hits in the web tree are isolated test credentials and the existing development-only fallback. Mobile scan reports no candidate credential hits. Vendored PDF.js `build/` files are required runtime source, not local Flutter build output.
- Existing focused application verification from the schedule work remains **67 Django tests passed, 54 Flutter tests passed, clean Flutter analysis, and a successful debug APK build/install**. Repository-ignore/README changes do not require rerunning application behavior tests; this upload is not a claim that every pending module change has passed the entire project suite.
- Verified the staged root contains no mobile files or gitlinks, the mobile tree contains its real `lib/main.dart` and `pubspec.yaml`, and neither staged tree includes the private/local paths checked above or files above GitHub's size limit. The whole staged-tree whitespace check reports existing formatting issues (396 web and3 mobile, chiefly feature-guide whitespace); it is not reported as passing and unrelated source/license formatting was preserved for this publication.
- Before pushing, validate index separation, inspect staged changes and check both remotes. After pushing, compare each local `HEAD` to `git ls-remote origin refs/heads/main` in its own repository; matching hashes confirm publication. Commit subjects must exactly match the requested text.

## 8. Remaining limitations / troubleshooting / safe practice

Both repositories retain their existing public visibility. Prior web history still contains the old mobile tree and previously published files; no unrelated history rewrite was requested. Untracked local editor state, environment files, private server credentials, database records and installed SDKs do not appear in a fresh clone. Recreate local configuration using the deployment guides.

If mobile files appear in root status, confirm the root `/campushub/` ignore rule and check `git ls-files campushub`. If a command targets the wrong repository, use `git -C campushub ...` explicitly. If a push is rejected because someone else updated `main`, fetch and inspect their changes; never solve it with an automatic force push.

Safe practice exercise: run the four read-only commands in the annotated example, then `git status --short` and `git -C campushub status --short`. Confirm the remotes differ and the parent does not track `lib/main.dart`. This teaches the boundary without creating commits, modifying accounts or touching database records.
