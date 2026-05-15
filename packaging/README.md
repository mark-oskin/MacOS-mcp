# Packaging

Source for two distributable bundles of the `macos-native-mcp` server.

| Subdir | Output | Target |
|--------|--------|--------|
| [`cowork-plugin/`](cowork-plugin/) | `dist/macos-native-apps.plugin` | Claude Cowork (drag-drop install) |
| [`mcpb/`](mcpb/) | `dist/macos-native-apps.mcpb` | Claude Desktop Extension (double-click install) |

Both bundles delegate to `uvx --from git+https://github.com/mark-oskin/MacOS-mcp macos-native-mcp` so end users don't need to clone or build a venv. They do need `uv` on PATH (`brew install uv`) and macOS Automation permissions for the host app.

## Build locally

```bash
./scripts/build-bundles.sh
```

Outputs land in `dist/` (gitignored).

## Release

1. Bump versions in both `packaging/cowork-plugin/.claude-plugin/plugin.json` and `packaging/mcpb/manifest.json`.
2. Commit, tag `vX.Y.Z`, push the tag.
3. The [release workflow](../.github/workflows/release.yml) builds both bundles and attaches them to the GitHub Release.

## What lives where

- **Connector definition** (how to launch the MCP server): `cowork-plugin/.mcp.json` for Cowork, `mcpb/manifest.json` → `server.mcp_config` for Desktop.
- **Operating-guidance skill** (Cowork-only): `cowork-plugin/skills/macos-native-apps-tips/SKILL.md`. Keep tool names in sync with `macos_mcp/server.py` — the skill encodes specific tool names and conventions.
- **Launch shim** (Desktop-only): `mcpb/server/run.sh`. Prints a friendly error if `uvx` is missing.

When adding, removing, or renaming a tool in the server, also update the skill's "Mail", "Calendar", "Reminders / Notes", or "Music" sections as needed.
