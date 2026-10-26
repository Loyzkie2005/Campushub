# Separate Codex accounts in VS Code and the ChatGPT app

Configured October 24, 2026 for the native Windows VS Code installation on this PC.

## 1. Cause / reason

The user reports that switching the Codex account in VS Code also changes the app account. Official OpenAI documentation confirms that the CLI and IDE extension share cached credentials. It does not establish this PC's exact desktop-app session behavior, so the specific cross-app cause has not been proven.

Local inspection confirmed that the installed `openai.chatgpt-26.1007.21434-win32-x64` extension resolves its Codex home from `process.env.CODEX_HOME`, falling back to the default `.codex` folder. A separate home and independent VS Code process provide a practical way to isolate this editor's sign-in.

## 2. Exact files changed

| File / line | Purpose |
| --- | --- |
| `C:/Users/leste/OneDrive/Desktop/VS Code - Separate Codex.cmd:1` | New desktop launcher; process-local environment, independent VS Code user-data directory, existing installed extension directory and CampusHub workspace. |
| `C:/Users/leste/.codex-vscode/config.toml:3` | New isolated configuration: `cli_auth_credentials_store = "file"`. |
| `docs/codex-separate-accounts.md:1` | This setup and verification guide. |

An empty directory was also prepared at `C:/Users/leste/AppData/Local/Codex-VSCode-Separate`. Existing app credentials, default Codex configuration and existing VS Code settings were not edited or copied. No account was signed out.

## 3. Changes made

Use the **VS Code - Separate Codex.cmd** desktop launcher for the editor account you want to keep separate. It opens CampusHub in an independent VS Code instance. The ordinary VS Code shortcut continues to use its normal environment; it does not automatically use this isolation setup.

The new instance has its own VS Code settings/state and Codex configuration/history. It reuses the installed extension binaries rather than reinstalling them. Existing global Codex settings, history, plugins and skills are not copied into the new home; project-local files remain in the shared project. Changes to the actual project files are still visible from both windows.

## 4. How it works

The launcher is a batch script, not a change to CampusHub's Python/Dart code:

```bat
setlocal
rem Only child processes launched here inherit this alternative home.
set "CODEX_HOME=%USERPROFILE%\.codex-vscode"
```

It starts the installed `Code.exe` with a dedicated `--user-data-dir` so the command does not attach to the already-running normal VS Code process. `--extensions-dir` points to the existing extension installation folder. File-based auth storage puts this instance's future login in its own Codex home rather than relying on a potentially shared OS credential-store entry. No credentials were copied or entered during setup.

Input is a double-click on the launcher; output is a new isolated editor window. The `--check` argument instead prints the two non-secret isolation paths and exits without launching an app or reading credentials. The `setlocal` environment ends with the launcher; no system-wide or persistent user `CODEX_HOME` was changed.

## First sign-in and verification

1. Save current work. Double-click **VS Code - Separate Codex.cmd** on the desktop. The current windows do not need to be terminated by a script.
2. Open the Codex extension in the new window and sign in with the account intended for VS Code. If the browser offers the wrong account, choose the option to use another account. Complete sign-in yourself; do not paste passwords or tokens into chat.
3. Check the account shown in this new VS Code window and the account shown in the ChatGPT app. Confirm each shows the intended account.
4. Use this launcher for future editor sessions that need separate sign-in. The old, ordinary VS Code window retains its original setup until you close it yourself.

## 5. Backend / API behavior

No CampusHub backend, API, route, permission, source file or environment file changed. This setup only selects local developer-tool configuration and storage paths.

## 6. Database / migration impact

None. No application data, schema, migration, server or deployment was changed.

## 7. Tests performed

- Verified the installed VS Code executable and extension paths exist.
- Executed the launcher's `--check` branch successfully. It printed the separate home/user-data paths and launched no app.
- Confirmed the new isolated Codex home contains no `auth.json` credential file after setup.
- The user still needs to perform the first sign-in and verify both account menus. A working two-account session has **not yet been demonstrated**.

## 8. Limitations and troubleshooting

This configuration targets native Windows VS Code. WSL/SSH/remote extension hosts can use a different environment and require separate inspection. New isolated settings may differ from the old editor profile. Future extension changes could affect home-directory handling.

If both windows still show the same account, first confirm the new window was opened from the dedicated launcher, not the normal taskbar shortcut, then check which account was selected during browser sign-in. Do not delete existing credential stores or sign out of every device to troubleshoot this setup.

Safe practice: open PowerShell and run the launcher with `--check`. Verify that it prints `.codex-vscode` and `Codex-VSCode-Separate` and opens no editor. This tests the launcher environment without touching account credentials.

To stop using the setup, close the isolated editor normally and use the original VS Code shortcut. Files were added without replacing the original configuration.

Sources: [OpenAI authentication and credential storage](https://learn.chatgpt.com/docs/auth#credential-storage), [OpenAI advanced configuration](https://learn.chatgpt.com/docs/config-file/config-advanced). The installed extension source provided the local evidence for `CODEX_HOME` handling.
