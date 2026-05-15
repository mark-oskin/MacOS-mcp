#!/bin/sh
# macos-native-apps MCP server launcher.
# Delegates to uvx, which fetches and runs the upstream package straight from GitHub.
# Requires `uv` on PATH: brew install uv

if ! command -v uvx >/dev/null 2>&1; then
  echo "macos-native-apps: 'uvx' not found on PATH. Install uv (https://docs.astral.sh/uv/) — e.g. 'brew install uv' — and reopen Claude Desktop." >&2
  exit 127
fi

exec uvx --from git+https://github.com/mark-oskin/MacOS-mcp macos-native-mcp "$@"
