#!/bin/sh
# Build distributable bundles for the Cowork plugin and Claude Desktop Extension.
#
# Outputs:
#   dist/macos-native-apps.plugin   (Cowork plugin)
#   dist/macos-native-apps.mcpb     (Claude Desktop Extension)
#
# Versions are read from packaging/cowork-plugin/.claude-plugin/plugin.json
# and packaging/mcpb/manifest.json — bump those before tagging a release.

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$REPO_ROOT/dist"
PLUGIN_SRC="$REPO_ROOT/packaging/cowork-plugin"
MCPB_SRC="$REPO_ROOT/packaging/mcpb"

mkdir -p "$DIST"
rm -f "$DIST/macos-native-apps.plugin" "$DIST/macos-native-apps.mcpb"

# Validate JSON before zipping.
python3 -c "import json,sys; [json.load(open(p)) for p in sys.argv[1:]]" \
  "$PLUGIN_SRC/.claude-plugin/plugin.json" \
  "$PLUGIN_SRC/.mcp.json" \
  "$MCPB_SRC/manifest.json"

# Ensure the mcpb shim is executable inside the zip.
chmod +x "$MCPB_SRC/server/run.sh"

(cd "$PLUGIN_SRC" && zip -qr "$DIST/macos-native-apps.plugin" . -x "*.DS_Store")
(cd "$MCPB_SRC"   && zip -qr "$DIST/macos-native-apps.mcpb"   . -x "*.DS_Store")

ls -la "$DIST"
