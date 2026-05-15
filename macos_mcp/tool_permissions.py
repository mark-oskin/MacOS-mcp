"""Load, merge, sync, and apply MCP tool enable/disable permissions."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from macos_mcp.dry_run import dry_run_blocked, is_dry_run

CONFIG_DIR = Path.home() / ".config" / "macos-native-mcp"
GLOBAL_CONFIG_PATH = CONFIG_DIR / "tools.json"
PROJECT_CONFIG_NAME = "tools.json"

KNOWN_GROUPS = ("mail", "calendar", "reminders", "notes", "itunes", "macos")


def tool_group(tool_name: str) -> str:
    if tool_name == "macos_launch":
        return "macos"
    for prefix in ("mail_", "calendar_", "reminders_", "notes_", "itunes_"):
        if tool_name.startswith(prefix):
            return prefix[:-1]
    return "other"


def _project_config_path() -> Path:
    return Path.cwd() / PROJECT_CONFIG_NAME


def _empty_config() -> dict[str, Any]:
    return {"groups": {}, "tools": {}}


def _load_json_file(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object")
    groups = data.get("groups", {})
    tools = data.get("tools", {})
    if not isinstance(groups, dict) or not isinstance(tools, dict):
        raise ValueError(f"{path}: groups and tools must be objects")
    return {"groups": dict(groups), "tools": dict(tools)}


def _merge_configs(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = _empty_config()
    for key in ("groups", "tools"):
        merged[key] = {**base.get(key, {}), **overlay.get(key, {})}
    return merged


def load_merged_config() -> tuple[dict[str, Any], list[Path]]:
    """Merge global then project config (project overrides). Returns merged config and paths read."""
    paths_read: list[Path] = []
    merged = _empty_config()
    if GLOBAL_CONFIG_PATH.is_file():
        merged = _merge_configs(merged, _load_json_file(GLOBAL_CONFIG_PATH))
        paths_read.append(GLOBAL_CONFIG_PATH)
    project_path = _project_config_path()
    if project_path.is_file():
        merged = _merge_configs(merged, _load_json_file(project_path))
        paths_read.append(project_path)
    return merged, paths_read


def _groups_for_tools(all_tools: list[str]) -> set[str]:
    groups = {tool_group(n) for n in all_tools}
    groups.discard("other")
    return groups | set(KNOWN_GROUPS)


def sync_config(config: dict[str, Any], all_tools: list[str]) -> tuple[dict[str, Any], list[str]]:
    """Ensure every known group and tool has an explicit entry (default true). Returns changes."""
    config = {
        "groups": dict(config.get("groups", {})),
        "tools": dict(config.get("tools", {})),
    }
    changes: list[str] = []
    for group in sorted(_groups_for_tools(all_tools)):
        if group not in config["groups"]:
            config["groups"][group] = True
            changes.append(f"groups.{group}")
    for name in sorted(all_tools):
        if name not in config["tools"]:
            config["tools"][name] = True
            changes.append(name)
    return config, changes


def _write_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_groups = {k: config["groups"][k] for k in sorted(config["groups"])}
    ordered_tools = {k: config["tools"][k] for k in sorted(config["tools"])}
    payload = {"groups": ordered_groups, "tools": ordered_tools}
    text = json.dumps(payload, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def _notify_config_update(path: Path, changes: list[str]) -> None:
    added = ", ".join(changes)
    sys.stderr.write(
        f"[macos-native-mcp] Updated {path}: added {added}. "
        "Restart the MCP server after changing tool permissions.\n"
    )


def persist_synced_config(config: dict[str, Any], all_tools: list[str]) -> None:
    """Write full catalog to global config; update project file if present."""
    config, global_changes = sync_config(config, all_tools)
    global_existed = GLOBAL_CONFIG_PATH.is_file()
    if not global_existed or global_changes:
        _write_config(GLOBAL_CONFIG_PATH, config)
        if global_changes:
            _notify_config_update(GLOBAL_CONFIG_PATH, global_changes)
        else:
            sys.stderr.write(
                f"[macos-native-mcp] Created default {GLOBAL_CONFIG_PATH} "
                f"({len(all_tools)} tools, all enabled). "
                "Restart the MCP server after changing tool permissions.\n"
            )

    project_path = _project_config_path()
    if project_path.is_file():
        proj_config, proj_changes = sync_config(_load_json_file(project_path), all_tools)
        if proj_changes:
            _write_config(project_path, proj_config)
            _notify_config_update(project_path, proj_changes)


def is_tool_enabled(tool_name: str, config: dict[str, Any]) -> bool:
    groups: dict[str, Any] = config.get("groups", {})
    tools: dict[str, Any] = config.get("tools", {})
    group = tool_group(tool_name)

    if tools.get(tool_name) is False:
        return False
    if tools.get(tool_name) is True:
        return True
    if groups.get(group) is False:
        return False
    return True


def resolve_enabled_tools(all_tools: list[str], config: dict[str, Any]) -> frozenset[str]:
    return frozenset(n for n in all_tools if is_tool_enabled(n, config))


def apply_tool_permissions(mcp: FastMCP, enabled: frozenset[str]) -> None:
    all_tools = [t.name for t in mcp._tool_manager.list_tools()]
    for name in all_tools:
        if name not in enabled:
            mcp.remove_tool(name)


class PermissionedFastMCP(FastMCP):
    """FastMCP server that blocks calls to tools disabled in configuration."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._enabled_tools: frozenset[str] = frozenset()

    def set_enabled_tools(self, enabled: frozenset[str]) -> None:
        self._enabled_tools = enabled

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._enabled_tools:
            msg = json.dumps(
                {
                    "error": (
                        f"Tool {name!r} is disabled in macos-native-mcp configuration. "
                        f"Edit {GLOBAL_CONFIG_PATH} or ./{PROJECT_CONFIG_NAME}, then restart the MCP server."
                    ),
                },
                indent=2,
            )
            return [TextContent(type="text", text=msg)]
        blocked = dry_run_blocked(name)
        if blocked is not None:
            return [TextContent(type="text", text=blocked)]
        return await super().call_tool(name, arguments)


def setup_tool_permissions(mcp: PermissionedFastMCP) -> None:
    all_tools = sorted(t.name for t in mcp._tool_manager.list_tools())
    merged, _paths_read = load_merged_config()
    persist_synced_config(merged, all_tools)
    merged, _ = load_merged_config()
    merged, _ = sync_config(merged, all_tools)
    enabled = resolve_enabled_tools(all_tools, merged)
    apply_tool_permissions(mcp, enabled)
    mcp.set_enabled_tools(enabled)
    disabled = sorted(set(all_tools) - set(enabled))
    sys.stderr.write(
        f"[macos-native-mcp] Tools enabled: {len(enabled)}/{len(all_tools)}"
        + (f" (disabled: {', '.join(disabled)})" if disabled else "")
        + "\n"
    )
    if is_dry_run():
        sys.stderr.write(
            "[macos-native-mcp] DRY RUN enabled (MACOS_MCP_DRY_RUN=1): "
            "mutating tools will not run AppleScript.\n"
        )
