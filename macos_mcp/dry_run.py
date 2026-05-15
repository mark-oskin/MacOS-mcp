"""Dry-run mode: block mutating tools from running AppleScript (MACOS_MCP_DRY_RUN=1)."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., str])

# Tools that create, update, delete, send, or control apps/media.
MUTATING_TOOLS: frozenset[str] = frozenset(
    {
        "mail_send",
        "mail_move",
        "mail_mark",
        "mail_delete",
        "mail_reply",
        "calendar_add_event",
        "calendar_add_recurring_event",
        "calendar_update_event",
        "calendar_delete_event",
        "calendar_default_calendar",
        "reminders_add_reminder",
        "reminders_set_completed",
        "reminders_delete_reminder",
        "notes_add_note",
        "notes_update_note",
        "notes_delete_note",
        "itunes_play_track",
        "itunes_play_pause",
        "macos_launch",
    }
)


def is_dry_run() -> bool:
    v = os.environ.get("MACOS_MCP_DRY_RUN", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def dry_run_response(tool_name: str) -> str:
    return json.dumps(
        {
            "dry_run": True,
            "tool": tool_name,
            "message": (
                "MACOS_MCP_DRY_RUN is set; this tool did not run AppleScript or change any app. "
                "Unset MACOS_MCP_DRY_RUN to perform the action."
            ),
        },
        indent=2,
    )


def dry_run_blocked(tool_name: str) -> str | None:
    if is_dry_run() and tool_name in MUTATING_TOOLS:
        return dry_run_response(tool_name)
    return None


def requires_live_app(fn: F) -> F:
    """Decorator for MCP tools that must not run when MACOS_MCP_DRY_RUN=1."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        blocked = dry_run_blocked(fn.__name__)
        if blocked is not None:
            return blocked
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
