---
name: macos-native-apps-tips
description: Operating guidance for the `macos-native-apps` MCP server. Load before calling any `mail_*`, `calendar_*`, `reminders_*`, `notes_*`, `itunes_*`, or `macos_launch` tool, or when the user asks Claude to read, search, send, or create items in Mac Mail, Calendar, Reminders, Notes, or Music.
---

# Using the macos-native-apps connector

The `macos-native-apps` MCP server drives native macOS apps over AppleScript. Tools return JSON strings. Mutating tools take real action (send mail, create events, delete reminders). Follow these rules every time.

## Launch the app first

Before calling any per-app tool in a session, call `macos_launch` with the app short name:

- `mail` → Mail
- `calendar` (or `ical`) → Calendar
- `reminders` → Reminders
- `notes` → Notes
- `music` (or `itunes`) → Music

This avoids `-600` / "Application isn't running" errors and brings Calendar to the foreground (required for several `calendar_*` tools). Allowlisted apps also include `safari` and `preview`.

If a tool returns a "not running" or "not allowed" error after launch, the host (Cowork / Claude Desktop / Cursor) is missing **Automation** permission for that app under System Settings → Privacy & Security → Automation. Tell the user; do not retry blindly.

## Time fields

Calendar and Reminders tools use POSIX seconds: `start_unix`, `end_unix`. Compute them from the user's request — never paste an ISO string into these. Responses often include `*_iso` UTC fields for display.

## Mail

- `mail_search` uses Spotlight (`mdfind`). Hits may only include `spotlight_path` and lack the internal Mail id needed by `mail_get_message` — fall back to `mail_get_headers` to enumerate by mailbox.
- `mail_send` sends immediately. There is no draft step. Confirm with the user before calling if the message is non-trivial.
- If `mail_search` returns nothing on a query that should match, the host probably lacks **Full Disk Access**.

## Calendar

- Use `calendar_list_calendars` to resolve calendar names before listing/creating events.
- Use `calendar_search_events` (Spotlight) for free-text queries; `calendar_list_events` with `start_unix` / `end_unix` for time-window scans.
- Calendar is the app most likely to error if not foregrounded — re-run `macos_launch` → `calendar` and retry once on `-600`.

## Reminders / Notes

- Reminders: list lists first (`reminders_list_lists`), then `reminders_list_reminders` on a list. Ids look like `x-apple-reminder://…`.
- Notes: resolve `folder_path` via `notes_list_folders` (e.g. `Notes` or `Work/Clients`). `notes_add_note` / `notes_update_note` take HTML bodies.
- Neither app has reliable Spotlight search — use the list tools, not search.

## Music

Library tracks are referenced by `persistent_id` (a string of digits returned by playlist listings). Don't guess ids — fetch via `itunes_list_playlists` or `itunes_get_track`.

## Dry run

The connector ships with `MACOS_MCP_DRY_RUN=0` (real actions). If the user wants to test wiring without sending mail / creating events, tell them to set `MACOS_MCP_DRY_RUN=1` in the connector env. In dry-run mode, mutating tools return a stub `{"dry_run": true, ...}` JSON object; read-only tools still execute.

## Tool permissions

Some tools (e.g. `mail_send`) may be disabled via `~/.config/macos-native-mcp/tools.json` or `./tools.json` in the working directory. If a tool you expect is missing from the available set, the user has likely disabled it — don't try to enable it yourself; ask.

## Confirmation before mutation

Always confirm with the user before:

- `mail_send`
- `calendar_*` create / update / delete
- `reminders_add_reminder`, deletions, completions
- `notes_add_note`, `notes_update_note`, deletions
- `itunes_play_*` (interrupts whatever is playing)

Read-only tools (`*_list_*`, `*_get_*`, `*_search`, `itunes_now_playing`) can be called without confirmation.
