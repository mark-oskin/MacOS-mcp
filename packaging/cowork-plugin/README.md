# macos-native-apps (Cowork plugin)

Wraps [mark-oskin/MacOS-mcp](https://github.com/mark-oskin/MacOS-mcp) as a Cowork connector. Lets Claude read and act on **Mail, Calendar, Reminders, Notes, and Music** through AppleScript on macOS.

## What's inside

- **Connector `macos-native-apps`** — launches the MCP server via `uvx --from git+https://github.com/mark-oskin/MacOS-mcp macos-native-mcp`. No manual venv setup needed.
- **Skill `macos-native-apps-tips`** — loads automatically when Claude is about to use any `mail_*` / `calendar_*` / `reminders_*` / `notes_*` / `itunes_*` / `macos_launch` tool. Encodes launch-first ordering, Spotlight caveats, time-field rules, and confirm-before-mutate behavior from the upstream README.

## Requirements

- macOS
- [`uv`](https://docs.astral.sh/uv/) installed and on PATH (`brew install uv`). The connector invokes `uvx`, which fetches the server straight from GitHub on first run.
- **Automation permissions**: macOS will prompt to allow the host app (Claude / Cowork) to control Mail, Calendar, Reminders, Notes, and Music. Approve on first use, or set them up ahead of time in System Settings → Privacy & Security → Automation.
- For Mail Spotlight search: grant the host **Full Disk Access**.

## Environment variables

Set on the connector entry to change defaults:

| Var | Default | Effect |
|-----|---------|--------|
| `MACOS_MCP_DRY_RUN` | `0` | Set to `1` to make mutating tools return stubs instead of sending mail / creating events. Read-only tools still run. |

## Tool gating

Edit `~/.config/macos-native-mcp/tools.json` (or `./tools.json` in the working directory) to disable tool families or individual tools — for example, turn off `mail_send` if Claude should only read mail. Restart Cowork after edits. See the upstream [README](https://github.com/mark-oskin/MacOS-mcp#tool-permissions).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `uvx: command not found` | Install `uv`: `brew install uv` (or `curl -LsSf https://astral.sh/uv/install.sh \| sh`). |
| Calendar errors with `-600` | Skill prompts a re-launch and retry; check Automation permission. |
| Mail search returns nothing | Grant the host Full Disk Access. |
| No tools listed in Cowork | Restart Cowork after installing the plugin; check stderr from the MCP server in the host logs. |
