# macos-native-mcp

MCP server that automates native macOS apps through AppleScript: **Mail**, **Calendar**, **Reminders**, **Notes**, and **Music** (tools use the `itunes_*` prefix). Tools return JSON strings. Mutating actions can send email, create calendar events, and similar—use permissions and dry-run when experimenting.

**Requirements:** macOS, Python 3.10+, and Automation permission for the app that runs the server (Terminal, Cursor, Claude Desktop, etc.) to control Mail, Calendar, Reminders, Notes, and Music.

---

## Install

From a clone of this repository:

```bash
cd /path/to/MacOS-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

The console entry point is **`macos-native-mcp`** (runs `macos_mcp.server:main` over stdio).

Verify:

```bash
which macos-native-mcp
# e.g. /path/to/MacOS-mcp/.venv/bin/macos-native-mcp
```

Use the **full path** to that binary in MCP client config (or `uv run` / `python -m` equivalents below).

---

## Connect in Cursor

1. Open **Cursor Settings → MCP** (or edit the MCP config file directly).
2. Add a server entry. Example using the venv binary:

```json
{
  "mcpServers": {
    "macos-native-apps": {
      "command": "/absolute/path/to/MacOS-mcp/.venv/bin/macos-native-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

**Alternative** (run via module without installing the script):

```json
{
  "mcpServers": {
    "macos-native-apps": {
      "command": "/absolute/path/to/MacOS-mcp/.venv/bin/python",
      "args": ["-m", "macos_mcp.server"],
      "env": {}
    }
  }
}
```

3. Save and **restart MCP** (or reload the window). The server name in the UI is **`macos-native-apps`**; tools appear in the agent tool list (grouped alphabetically by prefix: `mail_*`, `calendar_*`, …).

**Recommended `env` for safer development:**

```json
"env": {
  "MACOS_MCP_DRY_RUN": "1"
}
```

See [Dry run](#dry-run) below.

**Project-specific tool permissions:** if you add `./tools.json` in the project root (Cursor’s cwd when the server starts), it is merged on top of the global config. See [Tool permissions](#tool-permissions).

---

## Connect in Claude Desktop

### One-click install (Desktop Extension)

Download `macos-native-apps.mcpb` from the [latest release](https://github.com/mark-oskin/MacOS-mcp/releases/latest) and double-click it. Claude Desktop opens an install dialog with a **Dry run** toggle; accept and the connector is live.

Requires [`uv`](https://docs.astral.sh/uv/) on PATH — install with `brew install uv`. The bundle invokes `uvx` to fetch and run the server straight from GitHub; no manual venv setup.

### Manual config

Alternatively, edit Claude Desktop's MCP config directly:

| macOS location |
|----------------|
| `~/Library/Application Support/Claude/claude_desktop_config.json` |

Add the same structure under `mcpServers`:

```json
{
  "mcpServers": {
    "macos-native-apps": {
      "command": "/absolute/path/to/MacOS-mcp/.venv/bin/macos-native-mcp",
      "args": [],
      "env": {
        "MACOS_MCP_DRY_RUN": "0"
      }
    }
  }
}
```

Quit and reopen **Claude Desktop** after saving. On first use, macOS may prompt to allow **Claude** (or the host app) to control Mail, Calendar, etc.—approve for the apps you intend to automate.

Claude's MCP UI may differ slightly by version; if tools do not appear, confirm the config path and check Claude's logs (see [Troubleshooting](#troubleshooting)).

---

## Connect in Claude Cowork

Download `macos-native-apps.plugin` from the [latest release](https://github.com/mark-oskin/MacOS-mcp/releases/latest) and drag it into any Cowork conversation. Cowork shows a rich preview with an **Install** button.

The plugin ships with:

- the `macos-native-apps` connector (same `uvx` launch as the `.mcpb` above, requires `brew install uv`)
- a `macos-native-apps-tips` skill that loads automatically when Claude is about to call any `mail_*` / `calendar_*` / `reminders_*` / `notes_*` / `itunes_*` / `macos_launch` tool — encodes launch-first ordering, Spotlight caveats, time-field rules, and confirm-before-mutate behavior

To change the `MACOS_MCP_DRY_RUN` default or other env vars, open the connector in Cowork's settings.

---

## macOS Automation permissions

AppleScript needs **Automation** access. If tools fail with errors like “not allowed” or “Application isn’t running”:

1. Open **System Settings → Privacy & Security → Automation**.
2. Enable control for the **host** (e.g. **Cursor**, **Claude**, or **Terminal**) over **Mail**, **Calendar**, **Reminders**, **Notes**, and **Music** as needed.
3. For Calendar especially, call **`macos_launch`** with `app: "calendar"` (or `ical`) before other `calendar_*` tools so the app is frontmost.

Allowlisted apps for `macos_launch`: `mail`, `calendar` (`ical`), `reminders`, `notes`, `music` (`itunes`), `safari`, `preview`.

---

## Tool overview

Tools are named by prefix. Typical flow: **launch app** (if needed) → **list/search** → **get** → **mutate**.

| Prefix | App | Examples |
|--------|-----|----------|
| `mail_*` | Mail | `mail_list_accounts`, `mail_get_headers`, `mail_get_message`, `mail_search` (Spotlight), `mail_send`, … |
| `calendar_*` | Calendar | `calendar_list_calendars`, `calendar_list_events`, `calendar_search_events` (Spotlight), `calendar_get_event`, … |
| `reminders_*` | Reminders | `reminders_list_lists`, `reminders_list_reminders`, `reminders_get_reminder`, `reminders_add_reminder`, … |
| `notes_*` | Notes | `notes_list_accounts`, `notes_list_folders`, `notes_list_notes`, `notes_get_note`, `notes_add_note`, … |
| `itunes_*` | Music | `itunes_list_playlists`, `itunes_get_track`, `itunes_now_playing`, `itunes_play_track`, `itunes_play_pause` |
| `macos_*` | Various | `macos_launch` — start and activate an allowlisted app |

**Time fields:** Calendar and Reminders tools use **POSIX `start_unix` / `end_unix`** (seconds since 1970-01-01 UTC). Responses often include `*_iso` UTC timestamps for convenience.

**Notes bodies:** `notes_add_note` / `notes_update_note` typically use HTML bodies Notes understands.

**Music IDs:** Library tracks are referenced by **`persistent_id`** (string of digits from playlists).

**Search:** `mail_search` and `calendar_search_events` use **Spotlight** (`mdfind`). Notes, Reminders, and Music have no reliable Spotlight search API—use list tools instead. Grant the MCP host **Full Disk Access** if mail search returns nothing.

Each tool’s docstring in `macos_mcp/server.py` describes parameters and limits.

---

## Tool permissions

Control which tools the MCP client sees at startup.

### Config files (merged)

| File | Role |
|------|------|
| `~/.config/macos-native-mcp/tools.json` | Global config (created/updated automatically on first run) |
| `./tools.json` | Optional project overrides (merged **on top** of global; same cwd as when the server starts) |

Copy [`tools.example.json`](tools.example.json) as a starting point.

### Format

```json
{
  "groups": {
    "mail": true,
    "calendar": true,
    "reminders": true,
    "notes": true,
    "itunes": true,
    "macos": true
  },
  "tools": {
    "mail_send": false,
    "mail_get_headers": true
  }
}
```

- **`groups`:** `false` disables every tool in that family (`mail_*`, `calendar_*`, …; `macos` = `macos_launch`).
- **`tools`:** Per-tool override. `true` on a tool can re-enable it when its group is `false`.
- Missing keys default to **enabled**. On startup, new tools are **added as `true`** and the config file is updated; a message is printed to **stderr** (visible in MCP host logs).

**After editing permissions, restart the MCP server** (and reconnect the client). Disabled tools are not listed and cannot be called.

---

## Dry run

Set environment variable **`MACOS_MCP_DRY_RUN=1`** (also `true`, `yes`, `on`) in the MCP server `env` block.

Mutating tools (send mail, add events, delete reminders, play music, `macos_launch`, etc.) return JSON immediately:

```json
{
  "dry_run": true,
  "tool": "mail_send",
  "message": "MACOS_MCP_DRY_RUN is set; this tool did not run AppleScript..."
}
```

Read-only tools (`mail_list_accounts`, searches, getters, …) still run. Use dry run when testing MCP wiring or agent prompts without touching real data.

Run unit tests (no live Mail):

```bash
.venv/bin/python -m unittest tests.test_dry_run -v
```

---

## Usage tips for agents

1. **Launch first:** `macos_launch` with `app: "mail"` / `"calendar"` / `"reminders"` / `"notes"` / `"music"` before other tools if you see timeouts or “not running”.
2. **Mail:** Use `mail_search` (Spotlight) or `mail_get_headers` for messages; `mail_get_message` needs Mail’s internal id (Spotlight hits may only include `spotlight_path`). `mail_send` sends immediately (not a draft).
3. **Calendar:** Use `calendar_list_calendars` for names; `calendar_search_events` or `calendar_list_events` with `start_unix` / `end_unix`.
4. **Reminders:** Use `reminders_list_lists`, then `reminders_list_reminders` on a list; ids look like `x-apple-reminder://…`.
5. **Notes:** Use `notes_list_folders` for `folder_path` (e.g. `Notes` or `Work/Clients`).
6. **Least privilege:** Turn off `mail_send` and other mutators in `tools.json` if the agent only needs read access.

---

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| No tools in Cursor/Claude | Check `command` path, restart MCP, open host logs |
| `Unknown app` from `macos_launch` | Use allowlisted short names (`mail`, `calendar`, `music`, …) |
| Calendar `-600` / not running | `macos_launch` → `calendar`, short delay, retry |
| Mail send did nothing | Automation permission for host → Mail; check Mail accounts |
| Permission changes ignored | Restart MCP server after editing `tools.json` |
| Accidental send during dev | `MACOS_MCP_DRY_RUN=1` in `env` |

**Logs:** The server prints permission sync and dry-run notices to **stderr**. In Cursor, check the MCP server output panel; for Claude Desktop, consult Anthropic’s docs for log locations.

---

## Development

```bash
source .venv/bin/activate
pip install -e .
python -m unittest discover -s tests -v
```

AppleScript sources live in `macos_mcp/*.applescript` and are loaded at import time; restart the server after editing scripts.

---

## License

See repository defaults; adjust if you add a `LICENSE` file.
