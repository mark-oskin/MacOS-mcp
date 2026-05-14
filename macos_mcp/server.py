"""MCP server: Mail, Calendar, Reminders, Notes, Music (itunes_), and other macOS automation."""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("macos-native-apps")

DEFAULT_MAILBOX = "INBOX"

LIMIT_MIN = 1
LIMIT_MAX = 50

RECIPIENT_PREVIEW_MIN = 20
RECIPIENT_PREVIEW_MAX = 2000

BODY_MAX_MIN = 1000
BODY_MAX_MAX = 2_000_000

MAIL_GET_HEADERS_SCRIPT = Path(__file__).with_name("mail_get_headers.applescript").read_text()
MAIL_GET_MESSAGE_SCRIPT = Path(__file__).with_name("mail_get_message.applescript").read_text()
MAIL_SEND_SCRIPT = Path(__file__).with_name("mail_send.applescript").read_text()
MAIL_LIST_ACCOUNTS_SCRIPT = Path(__file__).with_name("mail_list_accounts.applescript").read_text()
MAIL_LIST_MAILBOXES_SCRIPT = Path(__file__).with_name("mail_list_mailboxes.applescript").read_text()
MAIL_SEARCH_SCRIPT = Path(__file__).with_name("mail_search.applescript").read_text()
MAIL_MOVE_SCRIPT = Path(__file__).with_name("mail_move.applescript").read_text()
MAIL_MARK_SCRIPT = Path(__file__).with_name("mail_mark.applescript").read_text()
MAIL_DELETE_SCRIPT = Path(__file__).with_name("mail_delete.applescript").read_text()
MAIL_REPLY_SCRIPT = Path(__file__).with_name("mail_reply.applescript").read_text()
MAIL_GET_ATTACHMENT_SCRIPT = Path(__file__).with_name("mail_get_attachment.applescript").read_text()
CALENDAR_LIST_CALENDARS_SCRIPT = Path(__file__).with_name("calendar_list_calendars.applescript").read_text()
CALENDAR_LIST_EVENTS_SCRIPT = Path(__file__).with_name("calendar_list_events.applescript").read_text()
CALENDAR_GET_EVENT_SCRIPT = Path(__file__).with_name("calendar_get_event.applescript").read_text()
CALENDAR_SEARCH_EVENTS_SCRIPT = Path(__file__).with_name("calendar_search_events.applescript").read_text()
CALENDAR_ADD_EVENT_SCRIPT = Path(__file__).with_name("calendar_add_event.applescript").read_text()
CALENDAR_ADD_RECURRING_EVENT_SCRIPT = Path(__file__).with_name("calendar_add_recurring_event.applescript").read_text()
CALENDAR_UPDATE_EVENT_SCRIPT = Path(__file__).with_name("calendar_update_event.applescript").read_text()
CALENDAR_DELETE_EVENT_SCRIPT = Path(__file__).with_name("calendar_delete_event.applescript").read_text()

REMINDERS_LIST_LISTS_SCRIPT = Path(__file__).with_name("reminders_list_lists.applescript").read_text()
REMINDERS_LIST_REMINDERS_SCRIPT = Path(__file__).with_name("reminders_list_reminders.applescript").read_text()
REMINDERS_GET_REMINDER_SCRIPT = Path(__file__).with_name("reminders_get_reminder.applescript").read_text()
REMINDERS_ADD_REMINDER_SCRIPT = Path(__file__).with_name("reminders_add_reminder.applescript").read_text()
REMINDERS_SET_COMPLETED_SCRIPT = Path(__file__).with_name("reminders_set_completed.applescript").read_text()
REMINDERS_DELETE_REMINDER_SCRIPT = Path(__file__).with_name("reminders_delete_reminder.applescript").read_text()
REMINDERS_SEARCH_REMINDERS_SCRIPT = Path(__file__).with_name("reminders_search_reminders.applescript").read_text()

NOTES_LIST_ACCOUNTS_SCRIPT = Path(__file__).with_name("notes_list_accounts.applescript").read_text()
NOTES_LIST_FOLDERS_SCRIPT = Path(__file__).with_name("notes_list_folders.applescript").read_text()
NOTES_LIST_NOTES_SCRIPT = Path(__file__).with_name("notes_list_notes.applescript").read_text()
NOTES_GET_NOTE_SCRIPT = Path(__file__).with_name("notes_get_note.applescript").read_text()
NOTES_SEARCH_NOTES_SCRIPT = Path(__file__).with_name("notes_search_notes.applescript").read_text()
NOTES_ADD_NOTE_SCRIPT = Path(__file__).with_name("notes_add_note.applescript").read_text()
NOTES_UPDATE_NOTE_SCRIPT = Path(__file__).with_name("notes_update_note.applescript").read_text()
NOTES_DELETE_NOTE_SCRIPT = Path(__file__).with_name("notes_delete_note.applescript").read_text()

ITUNES_LIST_PLAYLISTS_SCRIPT = Path(__file__).with_name("itunes_list_playlists.applescript").read_text()
ITUNES_SEARCH_LIBRARY_SCRIPT = Path(__file__).with_name("itunes_search_library.applescript").read_text()
ITUNES_GET_TRACK_SCRIPT = Path(__file__).with_name("itunes_get_track.applescript").read_text()
ITUNES_NOW_PLAYING_SCRIPT = Path(__file__).with_name("itunes_now_playing.applescript").read_text()
ITUNES_PLAY_TRACK_SCRIPT = Path(__file__).with_name("itunes_play_track.applescript").read_text()
ITUNES_PLAY_PAUSE_SCRIPT = Path(__file__).with_name("itunes_play_pause.applescript").read_text()

MAX_BODY_BYTES = 10 * 1024 * 1024

SEARCH_LIMIT_MIN = 1
SEARCH_LIMIT_MAX = 50
SEARCH_SCAN_MIN = 1
SEARCH_SCAN_MAX = 2000

CAL_EVENTS_LIMIT_MIN = 1
CAL_EVENTS_LIMIT_MAX = 200
CAL_SEARCH_QUERY_MAX_LEN = 500
CAL_RANGE_MAX_SECONDS = 2 * 366 * 24 * 3600
CAL_PATCH_MAX_BYTES = 256_000
CAL_RRULE_MAX_LEN = 4000

REMINDER_LIMIT_MIN = 1
REMINDER_LIMIT_MAX = 200
REMINDER_QUERY_MAX_LEN = 500

NOTES_LIMIT_MIN = 1
NOTES_LIMIT_MAX = 200
NOTES_QUERY_MAX_LEN = 500
NOTES_SKIP_FIELD = "__SKIP__"

ITUNES_MATCH_LIMIT_MIN = 1
ITUNES_MATCH_LIMIT_MAX = 100
ITUNES_SCAN_MAX_MIN = 100
ITUNES_SCAN_MAX_MAX = 100_000

ATTACHMENT_MAX_FILES = 15
ATTACHMENT_MAX_BYTES_PER_FILE = 5 * 1024 * 1024
ATTACHMENT_MAX_TOTAL_BYTES = 25 * 1024 * 1024

# Short name -> bundle id. Only these apps may be started via macos_launch.
MACOS_LAUNCH_ALLOWLIST: dict[str, str] = {
    "mail": "com.apple.mail",
    "calendar": "com.apple.iCal",
    "reminders": "com.apple.reminders",
    "safari": "com.apple.Safari",
    "preview": "com.apple.Preview",
    "notes": "com.apple.Notes",
    "music": "com.apple.Music",
}

# Extra lookup keys (normalized to lowercase). Use for common alternates (e.g. iCal).
MACOS_LAUNCH_ALIASES: dict[str, str] = {
    "ical": "com.apple.iCal",
    "itunes": "com.apple.Music",
}

LAUNCH_DELAY_MIN = 0.0
LAUNCH_DELAY_MAX = 30.0


def _resolve_mailbox(mailbox: str | None) -> str:
    if mailbox is None:
        return DEFAULT_MAILBOX
    s = mailbox.strip()
    return s if s else DEFAULT_MAILBOX


def _normalize_account(account: str | None) -> str | None:
    if account is None:
        return None
    s = account.strip()
    return s if s else None


def _normalize_recipient_csv(line: str | None) -> str:
    if not line or not line.strip():
        return ""
    parts = re.split(r"[,;]+", line)
    return ",".join(p.strip() for p in parts if p.strip())


def _run_applescript(script: str, args: list[str], timeout: float = 120.0) -> str:
    proc = subprocess.run(
        ["osascript", "-", *args],
        input=script,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or proc.stdout.strip()
        raise RuntimeError(err or f"osascript exited with {proc.returncode}")
    return proc.stdout.strip()


def _b64_utf8(s: str) -> str:
    return base64.standard_b64encode(s.encode("utf-8")).decode("ascii")


def _cal_unix_error(ts: object, label: str) -> str | None:
    try:
        x = float(ts)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return f"{label} must be a number"
    if abs(x) > 1e12:
        return f"{label} is out of range"
    return None


def _cal_range_error(start_unix: object, end_unix: object) -> str | None:
    e = _cal_unix_error(start_unix, "start_unix")
    if e:
        return e
    e = _cal_unix_error(end_unix, "end_unix")
    if e:
        return e
    su, eu = float(start_unix), float(end_unix)  # type: ignore[arg-type]
    if eu <= su:
        return "end_unix must be greater than start_unix"
    if eu - su > CAL_RANGE_MAX_SECONDS:
        return f"time range must be at most {CAL_RANGE_MAX_SECONDS} seconds (~2 years)"
    return None


def _cal_iso_z(ts: float) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _cal_parse_event_tsv_row(ln: str) -> dict[str, str | float | bool] | None:
    parts = ln.split("\t", 6)
    if len(parts) < 7:
        return None
    cal, uid, summary, sux_s, eux_s, ad, loc = parts
    try:
        sux = float(sux_s)
        eux = float(eux_s)
    except ValueError:
        return None
    return {
        "calendar": cal,
        "uid": uid,
        "summary": summary,
        "location": loc,
        "all_day": ad == "1",
        "start_unix": sux,
        "end_unix": eux,
        "start_iso": _cal_iso_z(sux),
        "end_iso": _cal_iso_z(eux),
    }


def _cal_build_patch_blob_b64(updates: dict[str, str | float | bool]) -> str:
    order = ("summary", "description", "location", "url", "start_unix", "end_unix", "all_day")
    lines: list[str] = []
    for k in order:
        if k not in updates:
            continue
        v = updates[k]
        if k == "all_day":
            payload = "1" if v else "0"
        elif k in ("start_unix", "end_unix"):
            payload = str(float(v))  # type: ignore[arg-type]
        else:
            payload = str(v)
        lines.append(f"{k}={_b64_utf8(payload)}")
    text = "\n".join(lines) + ("\n" if lines else "")
    if len(text.encode("utf-8")) > CAL_PATCH_MAX_BYTES:
        raise ValueError(f"patch exceeds {CAL_PATCH_MAX_BYTES} bytes")
    return _b64_utf8(text)


ICAL_PREFS_DOMAIN = "com.apple.iCal"
ICAL_DEFAULT_CAL_ID_KEY = "defaultCalendarID"
ICAL_LAST_SELECTED_CAL_KEY = "last selected calendar list item"


def _ical_defaults_read(key: str) -> str | None:
    proc = subprocess.run(
        ["defaults", "read", ICAL_PREFS_DOMAIN, key],
        capture_output=True,
        text=True,
        timeout=10.0,
        check=False,
    )
    if proc.returncode != 0:
        return None
    s = (proc.stdout or "").strip()
    return s if s else None


def _ical_defaults_write_string(key: str, value: str) -> None:
    proc = subprocess.run(
        ["defaults", "write", ICAL_PREFS_DOMAIN, key, "-string", value],
        capture_output=True,
        text=True,
        timeout=10.0,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or proc.stdout.strip()
        raise RuntimeError(err or "defaults write failed")


def _cal_parse_calendar_list_tsv(raw: str) -> list[dict[str, str | bool]]:
    rows: list[dict[str, str | bool]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t", 3)
        name = parts[0] if len(parts) > 0 else ""
        cid = parts[1] if len(parts) > 1 else ""
        w = parts[2] if len(parts) > 2 else "0"
        col = parts[3] if len(parts) > 3 else ""
        rows.append({"name": name, "id": cid, "writable": w == "1", "color": col})
    return rows


def _cal_fetch_calendar_rows() -> list[dict[str, str | bool]]:
    raw = _run_applescript(CALENDAR_LIST_CALENDARS_SCRIPT, [], timeout=60.0)
    return _cal_parse_calendar_list_tsv(raw)


def _rem_parse_reminder_row(ln: str) -> dict[str, str | float | bool | None] | None:
    parts = ln.split("\t", 5)
    if len(parts) < 6:
        return None
    rid, title, body, du_s, done, lst = parts
    due: float | None = None
    if du_s.strip():
        try:
            due = float(du_s)
        except ValueError:
            due = None
    return {
        "id": rid,
        "title": title,
        "body": body,
        "due_unix": due,
        "due_iso": _cal_iso_z(due) if due is not None else None,
        "completed": done == "1",
        "list": lst,
    }


def _notes_parse_folder_row(ln: str) -> dict[str, str] | None:
    parts = ln.split("\t", 2)
    if len(parts) < 3:
        return None
    return {"account": parts[0], "folder_path": parts[1], "id": parts[2]}


def _notes_parse_note_list_row(ln: str) -> dict[str, str | float] | None:
    parts = ln.split("\t", 4)
    if len(parts) < 5:
        return None
    nid, name, cux, mux, prv = parts
    try:
        cu = float(cux)
        mu = float(mux)
    except ValueError:
        return None
    return {
        "id": nid,
        "name": name,
        "created_unix": cu,
        "modified_unix": mu,
        "preview": prv,
        "created_iso": _cal_iso_z(cu),
        "modified_iso": _cal_iso_z(mu),
    }


def _notes_parse_search_row(ln: str) -> dict[str, str | float] | None:
    parts = ln.split("\t", 3)
    if len(parts) < 4:
        return None
    nid, name, mux, prv = parts
    try:
        mu = float(mux)
    except ValueError:
        return None
    return {
        "id": nid,
        "name": name,
        "modified_unix": mu,
        "preview": prv,
        "modified_iso": _cal_iso_z(mu),
    }


def _itunes_parse_track_row(ln: str) -> dict[str, str | float | int] | None:
    parts = ln.split("\t", 5)
    if len(parts) < 6:
        return None
    pid, name, artist, album, dur_s, tn_s = parts
    try:
        dur = float(dur_s)
        tn = int(tn_s)
    except ValueError:
        dur, tn = 0.0, 0
    return {
        "persistent_id": pid,
        "name": name,
        "artist": artist,
        "album": album,
        "duration_sec": dur,
        "track_number": tn,
    }


def _normalize_mail_ids(mail_ids: str) -> str:
    parts = re.split(r"[,;\s]+", mail_ids.strip())
    return ",".join(p for p in parts if p)


def _parse_header_tsv(raw: str) -> list[dict[str, str]]:
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    out: list[dict[str, str]] = []
    for ln in lines:
        parts = ln.split("\t", 6)
        if len(parts) < 7:
            continue
        mid, rfc_id, subj, sender, date_s, to_addrs, cc_addrs = parts
        out.append(
            {
                "id": mid,
                "message_id": rfc_id,
                "subject": subj,
                "sender": sender,
                "date": date_s,
                "to": to_addrs,
                "cc": cc_addrs,
            }
        )
    return out


def _bundle_id_for_launch_app(app: str) -> str | None:
    """Resolve allowlisted bundle id from short name, alias, Mail.app-style name, or bundle id."""
    raw = app.strip()
    if not raw:
        return None
    # Exact bundle id (case-insensitive) if it is one of our allowlisted apps.
    for bid in MACOS_LAUNCH_ALLOWLIST.values():
        if raw.lower() == bid.lower():
            return bid
    key = _normalize_launch_app_key(raw)
    if key in MACOS_LAUNCH_ALLOWLIST:
        return MACOS_LAUNCH_ALLOWLIST[key]
    if key in MACOS_LAUNCH_ALIASES:
        return MACOS_LAUNCH_ALIASES[key]
    return None


def _normalize_launch_app_key(app: str) -> str:
    """Lowercase single token: strip, collapse spaces, strip one trailing .app."""
    s = " ".join(app.split())
    if len(s) > 4 and s.lower().endswith(".app"):
        s = s[:-4].rstrip()
    return s.lower()


def _launch_allowed_names_for_error() -> str:
    names = sorted(set(MACOS_LAUNCH_ALLOWLIST) | set(MACOS_LAUNCH_ALIASES.keys()))
    return ", ".join(names)


def _osascript_escape_for_bundle_id(bundle_id: str) -> str:
    return bundle_id.replace("\\", "\\\\").replace('"', '\\"')


def _run_macos_launch(bundle_id: str) -> None:
    bid = _osascript_escape_for_bundle_id(bundle_id)
    script = (
        f'tell application id "{bid}" to launch\n'
        f'tell application id "{bid}" to activate\n'
    )
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=60.0,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or proc.stdout.strip()
        raise RuntimeError(err or f"osascript exited with {proc.returncode}")


def _run_mail_send(
    account: str | None,
    from_address: str | None,
    to_csv: str,
    cc_csv: str,
    bcc_csv: str,
    subject: str,
    body_path: str,
) -> str:
    acc = account or ""
    from_a = from_address or ""
    proc = subprocess.run(
        [
            "osascript",
            "-",
            acc,
            from_a,
            to_csv,
            cc_csv,
            bcc_csv,
            subject,
            body_path,
        ],
        input=MAIL_SEND_SCRIPT,
        capture_output=True,
        text=True,
        timeout=120.0,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or proc.stdout.strip()
        raise RuntimeError(err or f"osascript exited with {proc.returncode}")
    return proc.stdout.strip()


def _run_mail_get_headers(
    mailbox: str,
    account: str | None,
    limit: int,
    recipient_preview_chars: int,
) -> str:
    acc = account or ""
    proc = subprocess.run(
        [
            "osascript",
            "-",
            mailbox,
            acc,
            str(limit),
            str(recipient_preview_chars),
        ],
        input=MAIL_GET_HEADERS_SCRIPT,
        capture_output=True,
        text=True,
        timeout=60.0,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or proc.stdout.strip()
        raise RuntimeError(err or f"osascript exited with {proc.returncode}")
    return proc.stdout.strip()


def _run_mail_get_message(
    mailbox: str,
    account: str | None,
    mail_id: str,
    recipient_preview_chars: int,
    body_max_chars: int,
) -> str:
    acc = account or ""
    proc = subprocess.run(
        [
            "osascript",
            "-",
            mailbox,
            acc,
            mail_id,
            str(recipient_preview_chars),
            str(body_max_chars),
        ],
        input=MAIL_GET_MESSAGE_SCRIPT,
        capture_output=True,
        text=True,
        timeout=120.0,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or proc.stdout.strip()
        raise RuntimeError(err or f"osascript exited with {proc.returncode}")
    return proc.stdout.strip()


@mcp.tool()
def mail_get_headers(
    mailbox: str | None = None,
    account: str | None = None,
    limit: int = 10,
    recipient_preview_chars: int = 220,
) -> str:
    """Return header metadata for the newest messages in a Mail mailbox (no bodies).

    Tool prefix mail_* is reserved for Mail.app automation.

    Includes Mail internal id, RFC Message-ID, subject, sender, date received,
    and truncated To / Cc address lists. Does not fetch message content.

    mailbox: Optional mailbox name (sidebar). Defaults to INBOX if omitted or empty.

    account: Optional Mail account name as shown in the sidebar (e.g. iCloud).
        If omitted, the first account that contains a mailbox with the given
        name is used.

    limit: How many of the newest messages to return (default 10). Capped between
        1 and 50.

    recipient_preview_chars: Max characters for each of the To and Cc summary
        strings after joining addresses (default 220). Range 20–2000.
    """
    mb = _resolve_mailbox(mailbox)
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        return json.dumps({"error": "limit must be an integer"}, indent=2)
    n = max(LIMIT_MIN, min(lim, LIMIT_MAX))
    try:
        rpc = int(recipient_preview_chars)
    except (TypeError, ValueError):
        return json.dumps({"error": "recipient_preview_chars must be an integer"}, indent=2)
    preview_n = max(RECIPIENT_PREVIEW_MIN, min(rpc, RECIPIENT_PREVIEW_MAX))
    acc = _normalize_account(account)
    try:
        raw = _run_mail_get_headers(mb, acc, n, preview_n)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    return json.dumps(_parse_header_tsv(raw), indent=2)


@mcp.tool()
def mail_get_message(
    mail_id: str,
    mailbox: str | None = None,
    account: str | None = None,
    recipient_preview_chars: int = 220,
    body_max_chars: int = 500_000,
) -> str:
    """Fetch one Mail message by Mail's internal id (plain-text body + headers metadata).

    Use mail_get_headers to obtain ids. Tool prefix mail_* is reserved for Mail.app.

    mail_id: Mail internal message id string from mail_get_headers.

    mailbox: Optional mailbox name (sidebar). Defaults to INBOX if omitted or empty.

    account: Optional Mail account name. If omitted, the first account that has a
        mailbox matching the given name is used.

    recipient_preview_chars: Max characters for To / Cc summary strings (default 220).
        Range 20–2000.

    body_max_chars: Maximum plain-text body characters to return (default 500000).
        Range 1000–2000000. Truncates longer bodies.
    """
    mid = mail_id.strip()
    if not mid:
        return json.dumps({"error": "mail_id must be a non-empty string"}, indent=2)
    mb = _resolve_mailbox(mailbox)
    try:
        rpc = int(recipient_preview_chars)
    except (TypeError, ValueError):
        return json.dumps({"error": "recipient_preview_chars must be an integer"}, indent=2)
    preview_n = max(RECIPIENT_PREVIEW_MIN, min(rpc, RECIPIENT_PREVIEW_MAX))
    try:
        bmc = int(body_max_chars)
    except (TypeError, ValueError):
        return json.dumps({"error": "body_max_chars must be an integer"}, indent=2)
    body_n = max(BODY_MAX_MIN, min(bmc, BODY_MAX_MAX))
    acc = _normalize_account(account)
    try:
        raw = _run_mail_get_message(mb, acc, mid, preview_n, body_n)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)

    sep = chr(30)
    parts = raw.split(sep, 7)
    if len(parts) < 8:
        return json.dumps(
            {"error": "Unexpected output from Mail (field separator); try again or report bug."},
            indent=2,
        )
    (
        oid,
        rfc_id,
        subj,
        sender,
        date_s,
        to_addrs,
        cc_addrs,
        body,
    ) = parts
    payload = {
        "id": oid,
        "message_id": rfc_id,
        "subject": subj,
        "sender": sender,
        "date": date_s,
        "to": to_addrs,
        "cc": cc_addrs,
        "content": body,
    }
    return json.dumps(payload, indent=2)


@mcp.tool()
def mail_send(
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    account: str | None = None,
    from_address: str | None = None,
) -> str:
    """Send a plain-text email through Mail.app (creates outgoing message and sends).

    Tool prefix mail_* is reserved for Mail.app automation.

    to: Comma or semicolon separated recipient email addresses (required).

    subject: Message subject (may be empty).

    body: Plain-text message body. Written to a temp file for Mail (UTF-8).

    cc / bcc: Optional comma or semicolon separated addresses.

    account: Optional Mail account selector: the account's sidebar **name**, or an
        **email address** listed on that account. Used to set the From line when
        from_address is omitted. Not the same as `tell account "email"` in Mail's
        scripting (the account's internal name is often not the address).

    from_address: Optional From line (e.g. Name <you@domain.com> or you@domain.com)
        matching a configured sender. When set, it overrides account-based From.
    """
    to_csv = _normalize_recipient_csv(to)
    if not to_csv:
        return json.dumps({"error": "to must contain at least one email address"}, indent=2)
    cc_csv = _normalize_recipient_csv(cc)
    bcc_csv = _normalize_recipient_csv(bcc)
    acc = _normalize_account(account)
    from_a = from_address.strip() if from_address else None
    if from_a == "":
        from_a = None

    body_bytes = body.encode("utf-8")
    if len(body_bytes) > MAX_BODY_BYTES:
        return json.dumps(
            {"error": f"body exceeds maximum size ({MAX_BODY_BYTES} bytes)"},
            indent=2,
        )

    fd, path = tempfile.mkstemp(prefix="macos_mcp_mail_", suffix=".txt")
    raw = ""
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(body_bytes)
        os.chmod(path, 0o600)
        try:
            raw = _run_mail_send(acc, from_a, to_csv, cc_csv, bcc_csv, subject, path)
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
        except RuntimeError as e:
            return json.dumps({"error": str(e)}, indent=2)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    if raw.strip().upper() == "OK":
        return json.dumps({"ok": True}, indent=2)
    return json.dumps({"ok": True, "detail": raw}, indent=2)


@mcp.tool()
def mail_list_accounts() -> str:
    """List Mail.app accounts: sidebar name and comma-separated email addresses."""
    try:
        raw = _run_applescript(MAIL_LIST_ACCOUNTS_SCRIPT, [], timeout=60.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t", 1)
        name = parts[0]
        emails = parts[1] if len(parts) > 1 else ""
        rows.append({"name": name, "email_addresses": emails})
    return json.dumps(rows, indent=2)


@mcp.tool()
def mail_list_mailboxes() -> str:
    """List all mailboxes: account name and mailbox path (nested names joined with /)."""
    try:
        raw = _run_applescript(MAIL_LIST_MAILBOXES_SCRIPT, [], timeout=120.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t", 1)
        acct = parts[0]
        path = parts[1] if len(parts) > 1 else ""
        rows.append({"account": acct, "mailbox": path})
    return json.dumps(rows, indent=2)


@mcp.tool()
def mail_search(
    query: str,
    mailbox: str | None = None,
    account: str | None = None,
    limit: int = 20,
    max_scan: int = 500,
    recipient_preview_chars: int = 220,
) -> str:
    """Search recent messages in a mailbox for a substring in subject or sender (metadata only).

    Scans from newest (message 1) up to max_scan messages. Case-insensitive match.

    query: Substring to find in subject or sender (required).

    mailbox: Defaults to INBOX if omitted or empty.

    limit: Max matching messages to return (1–50).

    max_scan: Max messages to scan from the top (1–2000).

    recipient_preview_chars: Same as mail_get_headers (20–2000).
    """
    q = query.strip()
    if not q:
        return json.dumps({"error": "query must be non-empty"}, indent=2)
    mb = _resolve_mailbox(mailbox)
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        return json.dumps({"error": "limit must be an integer"}, indent=2)
    n = max(SEARCH_LIMIT_MIN, min(lim, SEARCH_LIMIT_MAX))
    try:
        scan = int(max_scan)
    except (TypeError, ValueError):
        return json.dumps({"error": "max_scan must be an integer"}, indent=2)
    scan_n = max(SEARCH_SCAN_MIN, min(scan, SEARCH_SCAN_MAX))
    try:
        rpc = int(recipient_preview_chars)
    except (TypeError, ValueError):
        return json.dumps({"error": "recipient_preview_chars must be an integer"}, indent=2)
    preview_n = max(RECIPIENT_PREVIEW_MIN, min(rpc, RECIPIENT_PREVIEW_MAX))
    acc = _normalize_account(account) or ""
    try:
        raw = _run_applescript(
            MAIL_SEARCH_SCRIPT,
            [mb, acc, q, str(n), str(scan_n), str(preview_n)],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    return json.dumps(_parse_header_tsv(raw), indent=2)


@mcp.tool()
def mail_move(
    mail_ids: str,
    to_mailbox: str,
    from_mailbox: str | None = None,
    from_account: str | None = None,
    to_account: str | None = None,
) -> str:
    """Move messages by Mail id from one mailbox to another (same or different account).

    mail_ids: Comma-separated Mail message ids (from mail_get_headers / mail_search).

    from_mailbox: Source mailbox (defaults to INBOX).

    to_mailbox: Destination mailbox name.

    from_account / to_account: Optional; empty to_account uses the source message's account
        when resolving the destination mailbox.
    """
    ids_csv = _normalize_mail_ids(mail_ids)
    if not ids_csv:
        return json.dumps({"error": "mail_ids must list at least one id"}, indent=2)
    fm = _resolve_mailbox(from_mailbox)
    tm = to_mailbox.strip()
    if not tm:
        return json.dumps({"error": "to_mailbox must be non-empty"}, indent=2)
    facc = _normalize_account(from_account) or ""
    tacc = _normalize_account(to_account) or ""
    try:
        raw = _run_applescript(
            MAIL_MOVE_SCRIPT,
            [fm, facc, tm, tacc, ids_csv],
            timeout=180.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    try:
        moved = int(raw.strip())
    except ValueError:
        moved = 0
    return json.dumps({"moved": moved}, indent=2)


@mcp.tool()
def mail_mark(
    mail_ids: str,
    is_read: bool,
    is_flagged: bool,
    mailbox: str | None = None,
    account: str | None = None,
) -> str:
    """Set read/unread and flagged state for messages by Mail id.

    is_read: True for read, False for unread.

    is_flagged: True to set the flag, False to clear it.
    """
    ids_csv = _normalize_mail_ids(mail_ids)
    if not ids_csv:
        return json.dumps({"error": "mail_ids must list at least one id"}, indent=2)
    mb = _resolve_mailbox(mailbox)
    acc = _normalize_account(account) or ""
    rf = "1" if is_read else "0"
    ff = "1" if is_flagged else "0"
    try:
        raw = _run_applescript(
            MAIL_MARK_SCRIPT,
            [mb, acc, ids_csv, rf, ff],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    try:
        n = int(raw.strip())
    except ValueError:
        n = 0
    return json.dumps({"updated": n}, indent=2)


@mcp.tool()
def mail_delete(
    mail_ids: str,
    mailbox: str | None = None,
    account: str | None = None,
) -> str:
    """Move messages to the account Trash mailbox (same as Mail delete)."""
    ids_csv = _normalize_mail_ids(mail_ids)
    if not ids_csv:
        return json.dumps({"error": "mail_ids must list at least one id"}, indent=2)
    mb = _resolve_mailbox(mailbox)
    acc = _normalize_account(account) or ""
    try:
        raw = _run_applescript(
            MAIL_DELETE_SCRIPT,
            [mb, acc, ids_csv],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    try:
        n = int(raw.strip())
    except ValueError:
        n = 0
    return json.dumps({"moved_to_trash": n}, indent=2)


@mcp.tool()
def mail_reply(
    mail_id: str,
    body: str,
    reply_all: bool = False,
    mailbox: str | None = None,
    account: str | None = None,
) -> str:
    """Reply to a message and send immediately (plain-text body appended to Mail's reply).

    Uses Mail's reply command (quoted original may remain). reply_all attempts Reply-All
    when supported; falls back to simple reply on error.
    """
    mid = mail_id.strip()
    if not mid:
        return json.dumps({"error": "mail_id must be non-empty"}, indent=2)
    mb = _resolve_mailbox(mailbox)
    acc = _normalize_account(account) or ""
    body_bytes = body.encode("utf-8")
    if len(body_bytes) > MAX_BODY_BYTES:
        return json.dumps(
            {"error": f"body exceeds maximum size ({MAX_BODY_BYTES} bytes)"},
            indent=2,
        )
    ra = "1" if reply_all else "0"
    fd, path = tempfile.mkstemp(prefix="macos_mcp_reply_", suffix=".txt")
    raw = ""
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(body_bytes)
        os.chmod(path, 0o600)
        try:
            raw = _run_applescript(
                MAIL_REPLY_SCRIPT,
                [mb, acc, mid, path, ra],
                timeout=120.0,
            )
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
        except RuntimeError as e:
            return json.dumps({"error": str(e)}, indent=2)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if raw.strip().upper() == "OK":
        return json.dumps({"ok": True}, indent=2)
    return json.dumps({"ok": True, "detail": raw}, indent=2)


@mcp.tool()
def mail_get_attachment(
    mail_id: str,
    mailbox: str | None = None,
    account: str | None = None,
) -> str:
    """Return attachments for a message as base64 (ephemeral temp files only; nothing kept).

    At most 15 attachments; each file max 5 MiB; combined max 25 MiB (otherwise error).
    """
    mid = mail_id.strip()
    if not mid:
        return json.dumps({"error": "mail_id must be non-empty"}, indent=2)
    mb = _resolve_mailbox(mailbox)
    acc = _normalize_account(account) or ""
    tmp = tempfile.mkdtemp(prefix="macos_mcp_att_")
    try:
        os.chmod(tmp, 0o700)
        try:
            manifest = _run_applescript(
                MAIL_GET_ATTACHMENT_SCRIPT,
                [mb, acc, mid, tmp],
                timeout=180.0,
            )
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Mail AppleScript timed out"}, indent=2)
        except RuntimeError as e:
            return json.dumps({"error": str(e)}, indent=2)

        total = 0
        out: list[dict[str, str | int]] = []
        for ln in manifest.splitlines():
            if not ln.strip():
                continue
            parts = ln.split("\t", 3)
            if len(parts) < 4:
                continue
            fn, name, mime, sz_s = parts[0], parts[1], parts[2], parts[3]
            fp = os.path.join(tmp, fn)
            if not os.path.isfile(fp):
                continue
            try:
                sz = int(sz_s)
            except ValueError:
                sz = os.path.getsize(fp)
            if sz > ATTACHMENT_MAX_BYTES_PER_FILE:
                return json.dumps(
                    {"error": f"attachment {name!r} exceeds {ATTACHMENT_MAX_BYTES_PER_FILE} bytes"},
                    indent=2,
                )
            if total + sz > ATTACHMENT_MAX_TOTAL_BYTES:
                return json.dumps(
                    {"error": f"attachments exceed combined limit {ATTACHMENT_MAX_TOTAL_BYTES} bytes"},
                    indent=2,
                )
            with open(fp, "rb") as bf:
                data = bf.read()
            total += len(data)
            out.append(
                {
                    "filename": name,
                    "mime_type": mime,
                    "size": len(data),
                    "data_base64": base64.standard_b64encode(data).decode("ascii"),
                }
            )
        return json.dumps({"attachments": out}, indent=2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@mcp.tool()
def macos_launch(
    app: str,
    delay_seconds: float = 0.5,
) -> str:
    """Launch an allowlisted macOS application and bring it to the foreground.

    Always runs ``launch`` then ``activate`` so the app is ready for AppleScript
    (e.g. Calendar) even when a background process already existed.

    App names are matched case-insensitively. You may pass a short name (mail,
    calendar, reminders, notes, music, …), the same with ``.app``, common aliases
    (e.g. ical for Calendar, itunes for Music), or the exact Apple bundle identifier
    if it is one of the allowlisted apps.

    delay_seconds: Wait this many seconds after launch/activate (0–30). Useful
    before other tools talk to the app.
    """
    bid = _bundle_id_for_launch_app(app)
    if bid is None:
        return json.dumps(
            {
                "error": f"Unknown app {app!r}. Allowed names and aliases: {_launch_allowed_names_for_error()}",
            },
            indent=2,
        )
    try:
        d = float(delay_seconds)
    except (TypeError, ValueError):
        return json.dumps({"error": "delay_seconds must be a number"}, indent=2)
    d = max(LAUNCH_DELAY_MIN, min(d, LAUNCH_DELAY_MAX))
    try:
        _run_macos_launch(bid)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "macos_launch timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if d > 0:
        time.sleep(d)
    return json.dumps(
        {
            "ok": True,
            "app": app.strip(),
            "bundle_id": bid,
            "activate": True,
            "delay_seconds": d,
        },
        indent=2,
    )


@mcp.tool()
def calendar_list_calendars() -> str:
    """List calendars in Calendar.app (name, id, writable, color).

    Tool prefix calendar_* is reserved for Calendar.app automation.

    Returns JSON array of objects with keys: name, id, writable (boolean),
    color (string representation, may be empty).
    """
    try:
        raw = _run_applescript(CALENDAR_LIST_CALENDARS_SCRIPT, [], timeout=60.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Calendar AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows = _cal_parse_calendar_list_tsv(raw)
    return json.dumps(rows, indent=2)


@mcp.tool()
def calendar_list_events(
    start_unix: float,
    end_unix: float,
    calendar: str | None = None,
    limit: int = 50,
) -> str:
    """List Calendar events whose time range overlaps [start_unix, end_unix).

    Times are POSIX seconds (UTC instant). Overlap uses Calendar's start/end dates
    (half-open window on the server side in AppleScript: start < end_unix and
    end > start_unix).

    calendar: Optional calendar **name** (exact match). If omitted or empty, all
    calendars are scanned in arbitrary order until ``limit`` events are collected.

    limit: Max events to return (1–200). Unsorted when scanning multiple calendars.

    Recurring series may appear as a single master event depending on Calendar's
    scripting model. Use ``macos_launch`` with app ``calendar`` first if AppleScript
    returns not-running errors.
    """
    err = _cal_range_error(start_unix, end_unix)
    if err:
        return json.dumps({"error": err}, indent=2)
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        return json.dumps({"error": "limit must be an integer"}, indent=2)
    n = max(CAL_EVENTS_LIMIT_MIN, min(lim, CAL_EVENTS_LIMIT_MAX))
    cal = (calendar or "").strip()
    try:
        raw = _run_applescript(
            CALENDAR_LIST_EVENTS_SCRIPT,
            [cal, str(float(start_unix)), str(float(end_unix)), str(n)],
            timeout=180.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Calendar AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str | float | bool]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        row = _cal_parse_event_tsv_row(ln)
        if row:
            rows.append(row)
    return json.dumps(rows, indent=2)


@mcp.tool()
def calendar_get_event(
    uid: str,
    calendar: str | None = None,
) -> str:
    """Fetch one Calendar event by **uid** (string from calendar_list_events / calendar_add_event).

    calendar: Optional calendar name hint (exact match). If omitted, every calendar
    is searched until a matching uid is found.

    Returns JSON with calendar, uid, summary, description, location, url,
    start_unix, end_unix, all_day, start_iso, end_iso (UTC Zulu instants).

    For recurring events, uid typically identifies the series; edits/deletes may
    apply to the whole series in Calendar.app.
    """
    u = uid.strip()
    if not u:
        return json.dumps({"error": "uid must be non-empty"}, indent=2)
    hint = (calendar or "").strip()
    try:
        raw = _run_applescript(CALENDAR_GET_EVENT_SCRIPT, [hint, u], timeout=120.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Calendar AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    sep = chr(30)
    parts = raw.split(sep, 8)
    if len(parts) < 9:
        return json.dumps({"error": "Unexpected Calendar output; try macos_launch calendar first."}, indent=2)
    cnm, euid, summ, desc, loc, surl, sux_s, eux_s, ad = parts
    try:
        sux = float(sux_s)
        eux = float(eux_s)
    except ValueError:
        return json.dumps({"error": "Invalid start/end in Calendar output"}, indent=2)
    payload = {
        "calendar": cnm,
        "uid": euid,
        "summary": summ,
        "description": desc,
        "location": loc,
        "url": surl,
        "start_unix": sux,
        "end_unix": eux,
        "all_day": ad == "1",
        "start_iso": _cal_iso_z(sux),
        "end_iso": _cal_iso_z(eux),
    }
    return json.dumps(payload, indent=2)


@mcp.tool()
def calendar_search_events(
    query: str,
    start_unix: float,
    end_unix: float,
    calendar: str | None = None,
    limit: int = 30,
) -> str:
    """Case-insensitive substring search in summary, description, and location for events overlapping the range.

    query: Non-empty substring (max 500 characters).

    start_unix / end_unix: Same overlap semantics as calendar_list_events.

    calendar: Optional calendar name (exact). Empty scans all calendars.

    limit: 1–200 matches (cap). Uses Foundation for lowercasing on the AppleScript side.
    """
    q = query.strip()
    if not q:
        return json.dumps({"error": "query must be non-empty"}, indent=2)
    if len(q) > CAL_SEARCH_QUERY_MAX_LEN:
        return json.dumps(
            {"error": f"query must be at most {CAL_SEARCH_QUERY_MAX_LEN} characters"},
            indent=2,
        )
    err = _cal_range_error(start_unix, end_unix)
    if err:
        return json.dumps({"error": err}, indent=2)
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        return json.dumps({"error": "limit must be an integer"}, indent=2)
    n = max(CAL_EVENTS_LIMIT_MIN, min(lim, CAL_EVENTS_LIMIT_MAX))
    cal = (calendar or "").strip()
    try:
        raw = _run_applescript(
            CALENDAR_SEARCH_EVENTS_SCRIPT,
            [q, cal, str(float(start_unix)), str(float(end_unix)), str(n)],
            timeout=180.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Calendar AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str | float | bool]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        row = _cal_parse_event_tsv_row(ln)
        if row:
            rows.append(row)
    return json.dumps(rows, indent=2)


@mcp.tool()
def calendar_add_event(
    calendar: str,
    summary: str,
    start_unix: float,
    end_unix: float,
    all_day: bool = False,
    description: str | None = None,
    location: str | None = None,
    url: str | None = None,
) -> str:
    """Create a single Calendar event on a named calendar; returns its **uid**.

    calendar: Target calendar name (exact match; use calendar_list_calendars).

    summary: Event title (UTF-8). Must not contain ASCII NUL.

    start_unix / end_unix: POSIX seconds. For all-day events, use midnight-aligned
    instants for the intended local calendar day (Calendar interprets using the
    system timezone).

    all_day: When true, creates an all-day style event.

    description / location / url: Optional UTF-8 strings. Omitted parameters leave
    the property unset. Pass an empty string to set an empty value (still transmitted
    via base64 internally).

    Writable calendars only; read-only calendars raise an AppleScript error.
    """
    cal = calendar.strip()
    if not cal:
        return json.dumps({"error": "calendar must be non-empty"}, indent=2)
    summ = summary if summary is not None else ""
    if "\x00" in summ:
        return json.dumps({"error": "summary must not contain NUL"}, indent=2)
    err = _cal_range_error(start_unix, end_unix)
    if err:
        return json.dumps({"error": err}, indent=2)
    desc_b64 = ""
    if description is not None:
        if "\x00" in description:
            return json.dumps({"error": "description must not contain NUL"}, indent=2)
        desc_b64 = _b64_utf8(description)
    loc_b64 = ""
    if location is not None:
        if "\x00" in location:
            return json.dumps({"error": "location must not contain NUL"}, indent=2)
        loc_b64 = _b64_utf8(location)
    url_b64 = ""
    if url is not None:
        if "\x00" in url:
            return json.dumps({"error": "url must not contain NUL"}, indent=2)
        url_b64 = _b64_utf8(url)
    ad = "1" if all_day else "0"
    summ_b64 = _b64_utf8(summ)
    try:
        raw = _run_applescript(
            CALENDAR_ADD_EVENT_SCRIPT,
            [
                cal,
                summ_b64,
                desc_b64,
                loc_b64,
                url_b64,
                str(float(start_unix)),
                str(float(end_unix)),
                ad,
            ],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Calendar AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    new_uid = raw.strip()
    if not new_uid:
        return json.dumps({"error": "Calendar returned empty uid"}, indent=2)
    return json.dumps({"uid": new_uid}, indent=2)


@mcp.tool()
def calendar_add_recurring_event(
    calendar: str,
    summary: str,
    start_unix: float,
    end_unix: float,
    recurrence: str,
    all_day: bool = False,
    description: str | None = None,
    location: str | None = None,
    url: str | None = None,
) -> str:
    """Create a **recurring** Calendar event (debug path separate from ``calendar_add_event``).

    Same arguments as ``calendar_add_event``, plus **recurrence**: an iCalendar **RRULE**
    body (without the ``RRULE:`` prefix), for example ``FREQ=WEEKLY;BYDAY=MO`` or
    ``FREQ=DAILY;INTERVAL=1``. You can include ``UNTIL=...`` in the rule if Calendar
    accepts it for your pattern.

    The AppleScript creates the event, then sets ``recurrence`` on the new event.
    Writable calendars only. Returns the new series **uid** (same shape as
    ``calendar_add_event``).
    """
    cal = calendar.strip()
    if not cal:
        return json.dumps({"error": "calendar must be non-empty"}, indent=2)
    summ = summary if summary is not None else ""
    if "\x00" in summ:
        return json.dumps({"error": "summary must not contain NUL"}, indent=2)
    rrule = recurrence.strip()
    if not rrule:
        return json.dumps({"error": "recurrence must be a non-empty RRULE string"}, indent=2)
    if len(rrule) > CAL_RRULE_MAX_LEN:
        return json.dumps(
            {"error": f"recurrence must be at most {CAL_RRULE_MAX_LEN} characters"},
            indent=2,
        )
    if "\x00" in rrule:
        return json.dumps({"error": "recurrence must not contain NUL"}, indent=2)
    err = _cal_range_error(start_unix, end_unix)
    if err:
        return json.dumps({"error": err}, indent=2)
    desc_b64 = ""
    if description is not None:
        if "\x00" in description:
            return json.dumps({"error": "description must not contain NUL"}, indent=2)
        desc_b64 = _b64_utf8(description)
    loc_b64 = ""
    if location is not None:
        if "\x00" in location:
            return json.dumps({"error": "location must not contain NUL"}, indent=2)
        loc_b64 = _b64_utf8(location)
    url_b64 = ""
    if url is not None:
        if "\x00" in url:
            return json.dumps({"error": "url must not contain NUL"}, indent=2)
        url_b64 = _b64_utf8(url)
    ad = "1" if all_day else "0"
    summ_b64 = _b64_utf8(summ)
    rrule_b64 = _b64_utf8(rrule)
    try:
        raw = _run_applescript(
            CALENDAR_ADD_RECURRING_EVENT_SCRIPT,
            [
                cal,
                summ_b64,
                desc_b64,
                loc_b64,
                url_b64,
                str(float(start_unix)),
                str(float(end_unix)),
                ad,
                rrule_b64,
            ],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Calendar AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    new_uid = raw.strip()
    if not new_uid:
        return json.dumps({"error": "Calendar returned empty uid"}, indent=2)
    return json.dumps({"uid": new_uid, "recurrence": rrule}, indent=2)


@mcp.tool()
def calendar_update_event(
    uid: str,
    calendar: str | None = None,
    summary: str | None = None,
    description: str | None = None,
    location: str | None = None,
    url: str | None = None,
    start_unix: float | None = None,
    end_unix: float | None = None,
    all_day: bool | None = None,
) -> str:
    """Patch fields on an existing event identified by **uid**.

    Only parameters you pass are applied (``None`` / omitted means leave unchanged).

    start_unix and end_unix must be supplied together when changing times.

    Values are transported in a small base64 patch block; avoid megabyte-sized
    descriptions. NUL bytes are rejected.

    Recurring events: Calendar.app may update the series master; behavior is not
    split into detached instances here.
    """
    u = uid.strip()
    if not u:
        return json.dumps({"error": "uid must be non-empty"}, indent=2)
    updates: dict[str, str | float | bool] = {}
    if summary is not None:
        if "\x00" in summary:
            return json.dumps({"error": "summary must not contain NUL"}, indent=2)
        updates["summary"] = summary
    if description is not None:
        if "\x00" in description:
            return json.dumps({"error": "description must not contain NUL"}, indent=2)
        updates["description"] = description
    if location is not None:
        if "\x00" in location:
            return json.dumps({"error": "location must not contain NUL"}, indent=2)
        updates["location"] = location
    if url is not None:
        if "\x00" in url:
            return json.dumps({"error": "url must not contain NUL"}, indent=2)
        updates["url"] = url
    if start_unix is not None or end_unix is not None:
        if start_unix is None or end_unix is None:
            return json.dumps(
                {"error": "start_unix and end_unix must both be set to change times"},
                indent=2,
            )
        err = _cal_range_error(start_unix, end_unix)
        if err:
            return json.dumps({"error": err}, indent=2)
        updates["start_unix"] = float(start_unix)
        updates["end_unix"] = float(end_unix)
    if all_day is not None:
        updates["all_day"] = bool(all_day)
    if not updates:
        return json.dumps({"error": "provide at least one field to update"}, indent=2)
    try:
        patch_b64 = _cal_build_patch_blob_b64(updates)
    except ValueError as e:
        return json.dumps({"error": str(e)}, indent=2)
    hint = (calendar or "").strip()
    try:
        raw = _run_applescript(
            CALENDAR_UPDATE_EVENT_SCRIPT,
            [hint, u, patch_b64],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Calendar AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    out_uid = raw.strip()
    return json.dumps({"ok": True, "uid": out_uid}, indent=2)


@mcp.tool()
def calendar_delete_event(
    uid: str,
    calendar: str | None = None,
) -> str:
    """Delete an event by **uid** (optional calendar name hint for faster lookup).

    Recurring events may delete the entire series depending on Calendar's rules.
    """
    u = uid.strip()
    if not u:
        return json.dumps({"error": "uid must be non-empty"}, indent=2)
    hint = (calendar or "").strip()
    try:
        raw = _run_applescript(CALENDAR_DELETE_EVENT_SCRIPT, [hint, u], timeout=120.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Calendar AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if raw.strip().upper() == "OK":
        return json.dumps({"ok": True}, indent=2)
    return json.dumps({"ok": True, "detail": raw}, indent=2)


@mcp.tool()
def calendar_default_calendar(set_to: str | None = None) -> str:
    """Get or set the default calendar used for new events (Calendar.app / iCal prefs).

    **Get** (``set_to`` omitted or empty): reads ``com.apple.iCal`` preference
    ``defaultCalendarID`` (falling back to ``last selected calendar list item``)
    and resolves the calendar **name** via ``calendar_list_calendars``. Also returns
    ``preferences_default_mode`` (e.g. ``UseLastSelectedAsDefaultCalendar``) when present.

    **Set** (``set_to`` non-empty): resolves the calendar by **exact name** or by
    **id** string from ``calendar_list_calendars``, then writes the same preference
    keys via ``defaults``. Calendar.app may need a moment to pick up changes; relaunch
    with ``macos_launch`` if the UI looks stale.

    AppleScript does not expose ``default calendar`` reliably across macOS versions,
    so this tool uses the on-disk preference keys Calendar maintains.
    """
    st = set_to.strip() if set_to else ""
    try:
        rows = _cal_fetch_calendar_rows()
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Calendar AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if not st:
        cid = _ical_defaults_read(ICAL_DEFAULT_CAL_ID_KEY) or _ical_defaults_read(ICAL_LAST_SELECTED_CAL_KEY) or ""
        name = ""
        for r in rows:
            if str(r.get("id", "")) == cid:
                name = str(r.get("name", ""))
                break
        mode = _ical_defaults_read("CalDefaultCalendar") or ""
        return json.dumps(
            {
                "id": cid,
                "name": name,
                "preferences_default_mode": mode,
            },
            indent=2,
        )
    target = st
    match: dict[str, str | bool] | None = None
    for r in rows:
        if str(r.get("name", "")) == target:
            match = r
            break
    if match is None:
        for r in rows:
            if str(r.get("id", "")) == target:
                match = r
                break
    if match is None:
        return json.dumps({"error": f"No calendar named or id-matching {target!r}"}, indent=2)
    new_id = str(match.get("id", ""))
    if not new_id:
        return json.dumps({"error": "Matched calendar has empty id"}, indent=2)
    try:
        _ical_defaults_write_string(ICAL_DEFAULT_CAL_ID_KEY, new_id)
        _ical_defaults_write_string(ICAL_LAST_SELECTED_CAL_KEY, new_id)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    return json.dumps(
        {
            "ok": True,
            "default": {"name": str(match.get("name", "")), "id": new_id},
        },
        indent=2,
    )


@mcp.tool()
def reminders_list_lists() -> str:
    """List Reminders.app lists (sidebar) with **name** and **id** strings."""
    try:
        raw = _run_applescript(REMINDERS_LIST_LISTS_SCRIPT, [], timeout=60.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Reminders AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t", 1)
        rows.append({"name": parts[0], "id": parts[1] if len(parts) > 1 else ""})
    return json.dumps(rows, indent=2)


@mcp.tool()
def reminders_list_reminders(
    list_name: str,
    include_completed: bool = False,
    limit: int = 50,
) -> str:
    """List reminders in one list (title, body, due_unix, completed, id).

    list_name: Exact Reminders list name (from reminders_list_lists).

    include_completed: When false, only incomplete reminders are returned.

    limit: 1–200 reminders (arbitrary order as returned by the app).
    """
    ln = list_name.strip()
    if not ln:
        return json.dumps({"error": "list_name must be non-empty"}, indent=2)
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        return json.dumps({"error": "limit must be an integer"}, indent=2)
    n = max(REMINDER_LIMIT_MIN, min(lim, REMINDER_LIMIT_MAX))
    inc = "1" if include_completed else "0"
    try:
        raw = _run_applescript(
            REMINDERS_LIST_REMINDERS_SCRIPT,
            [ln, inc, str(n)],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Reminders AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str | float | bool | None]] = []
    for row_ln in raw.splitlines():
        if not row_ln.strip():
            continue
        r = _rem_parse_reminder_row(row_ln)
        if r:
            rows.append(r)
    return json.dumps(rows, indent=2)


@mcp.tool()
def reminders_get_reminder(
    reminder_id: str,
    list_name: str | None = None,
) -> str:
    """Fetch one reminder by **reminder_id** (x-apple-reminder://… from list/search).

    list_name: Optional list hint for faster lookup; if omitted, all lists are scanned.
    """
    rid = reminder_id.strip()
    if not rid:
        return json.dumps({"error": "reminder_id must be non-empty"}, indent=2)
    hint = (list_name or "").strip()
    try:
        raw = _run_applescript(REMINDERS_GET_REMINDER_SCRIPT, [hint, rid], timeout=60.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Reminders AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    sep = chr(30)
    parts = raw.split(sep, 6)
    if len(parts) < 7:
        return json.dumps({"error": "Unexpected Reminders output"}, indent=2)
    lst, uid, title, body, du_s, done = (
        parts[0],
        parts[1],
        parts[2],
        parts[3],
        parts[4],
        parts[5],
        parts[6],
    )
    due: float | None = None
    if du_s.strip():
        try:
            due = float(du_s)
        except ValueError:
            due = None
    payload = {
        "list": lst,
        "id": uid,
        "title": title,
        "body": body,
        "due_unix": due,
        "due_iso": _cal_iso_z(due) if due is not None else None,
        "completed": done == "1",
    }
    return json.dumps(payload, indent=2)


@mcp.tool()
def reminders_add_reminder(
    list_name: str,
    title: str,
    body: str | None = None,
    due_unix: float | None = None,
) -> str:
    """Create a reminder in a list; returns its **id** string."""
    ln = list_name.strip()
    if not ln:
        return json.dumps({"error": "list_name must be non-empty"}, indent=2)
    tit = title if title is not None else ""
    if "\x00" in tit:
        return json.dumps({"error": "title must not contain NUL"}, indent=2)
    bod = body if body is not None else ""
    if "\x00" in bod:
        return json.dumps({"error": "body must not contain NUL"}, indent=2)
    due_s = ""
    if due_unix is not None:
        err = _cal_unix_error(due_unix, "due_unix")
        if err:
            return json.dumps({"error": err}, indent=2)
        due_s = str(float(due_unix))
    try:
        raw = _run_applescript(
            REMINDERS_ADD_REMINDER_SCRIPT,
            [ln, _b64_utf8(tit), _b64_utf8(bod), due_s],
            timeout=60.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Reminders AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    new_id = raw.strip()
    if not new_id:
        return json.dumps({"error": "Reminders returned empty id"}, indent=2)
    return json.dumps({"id": new_id}, indent=2)


@mcp.tool()
def reminders_set_completed(
    reminder_id: str,
    completed: bool,
    list_name: str | None = None,
) -> str:
    """Mark a reminder completed (true) or incomplete (false)."""
    rid = reminder_id.strip()
    if not rid:
        return json.dumps({"error": "reminder_id must be non-empty"}, indent=2)
    hint = (list_name or "").strip()
    fl = "1" if completed else "0"
    try:
        raw = _run_applescript(
            REMINDERS_SET_COMPLETED_SCRIPT,
            [hint, rid, fl],
            timeout=60.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Reminders AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if raw.strip().upper() == "OK":
        return json.dumps({"ok": True}, indent=2)
    return json.dumps({"ok": True, "detail": raw}, indent=2)


@mcp.tool()
def reminders_delete_reminder(
    reminder_id: str,
    list_name: str | None = None,
) -> str:
    """Delete a reminder by id (optional list hint)."""
    rid = reminder_id.strip()
    if not rid:
        return json.dumps({"error": "reminder_id must be non-empty"}, indent=2)
    hint = (list_name or "").strip()
    try:
        raw = _run_applescript(REMINDERS_DELETE_REMINDER_SCRIPT, [hint, rid], timeout=60.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Reminders AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if raw.strip().upper() == "OK":
        return json.dumps({"ok": True}, indent=2)
    return json.dumps({"ok": True, "detail": raw}, indent=2)


@mcp.tool()
def reminders_search_reminders(
    query: str,
    list_name: str | None = None,
    include_completed: bool = False,
    limit: int = 30,
) -> str:
    """Case-insensitive substring search in reminder title and body."""
    q = query.strip()
    if not q:
        return json.dumps({"error": "query must be non-empty"}, indent=2)
    if len(q) > REMINDER_QUERY_MAX_LEN:
        return json.dumps(
            {"error": f"query must be at most {REMINDER_QUERY_MAX_LEN} characters"},
            indent=2,
        )
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        return json.dumps({"error": "limit must be an integer"}, indent=2)
    n = max(REMINDER_LIMIT_MIN, min(lim, REMINDER_LIMIT_MAX))
    inc = "1" if include_completed else "0"
    lst = (list_name or "").strip()
    try:
        raw = _run_applescript(
            REMINDERS_SEARCH_REMINDERS_SCRIPT,
            [q, lst, inc, str(n)],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Reminders AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str | float | bool | None]] = []
    for row_ln in raw.splitlines():
        if not row_ln.strip():
            continue
        r = _rem_parse_reminder_row(row_ln)
        if r:
            rows.append(r)
    return json.dumps(rows, indent=2)


@mcp.tool()
def notes_list_accounts() -> str:
    """List Notes.app account names (iCloud, On My Mac, …)."""
    try:
        raw = _run_applescript(NOTES_LIST_ACCOUNTS_SCRIPT, [], timeout=60.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Notes AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    names = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    return json.dumps(names, indent=2)


@mcp.tool()
def notes_list_folders(account: str | None = None) -> str:
    """List folders under an account (recursive paths like ``Notes`` or ``A/B``).

    account: Optional account name; if omitted, uses the **default** Notes account.
    Returns JSON rows: account, folder_path, id.
    """
    acc = (account or "").strip()
    try:
        raw = _run_applescript(NOTES_LIST_FOLDERS_SCRIPT, [acc], timeout=120.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Notes AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        r = _notes_parse_folder_row(ln)
        if r:
            rows.append(r)
    return json.dumps(rows, indent=2)


@mcp.tool()
def notes_list_notes(
    folder_path: str,
    account: str | None = None,
    limit: int = 40,
) -> str:
    """List notes in a folder (metadata + plaintext preview).

    folder_path: Slash-separated path from notes_list_folders (e.g. ``Notes`` or ``Work/Clients``).

    account: Optional account name; if omitted, uses the default account.
    """
    fp = folder_path.strip()
    if not fp:
        return json.dumps({"error": "folder_path must be non-empty"}, indent=2)
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        return json.dumps({"error": "limit must be an integer"}, indent=2)
    n = max(NOTES_LIMIT_MIN, min(lim, NOTES_LIMIT_MAX))
    acc = (account or "").strip()
    try:
        raw = _run_applescript(
            NOTES_LIST_NOTES_SCRIPT,
            [acc, fp, str(n)],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Notes AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str | float]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        r = _notes_parse_note_list_row(ln)
        if r:
            rows.append(r)
    return json.dumps(rows, indent=2)


@mcp.tool()
def notes_get_note(note_id: str) -> str:
    """Fetch one note by **id** (from list/search). Returns plaintext, HTML body, and paths."""
    nid = note_id.strip()
    if not nid:
        return json.dumps({"error": "note_id must be non-empty"}, indent=2)
    try:
        raw = _run_applescript(NOTES_GET_NOTE_SCRIPT, [nid], timeout=120.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Notes AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    sep = chr(30)
    parts = raw.split(sep, 7)
    if len(parts) < 8:
        return json.dumps({"error": "Unexpected Notes output"}, indent=2)
    acc, fpath, uid, name, cux, mux, ptx, body = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6], parts[7]
    try:
        cu = float(cux)
        mu = float(mux)
    except ValueError:
        return json.dumps({"error": "Invalid timestamps from Notes"}, indent=2)
    return json.dumps(
        {
            "account": acc,
            "folder_path": fpath,
            "id": uid,
            "name": name,
            "created_unix": cu,
            "modified_unix": mu,
            "created_iso": _cal_iso_z(cu),
            "modified_iso": _cal_iso_z(mu),
            "plaintext": ptx,
            "body": body,
        },
        indent=2,
    )


@mcp.tool()
def notes_search_notes(
    query: str,
    account: str | None = None,
    limit: int = 30,
) -> str:
    """Search note titles and plaintext under an account (recursive folders)."""
    q = query.strip()
    if not q:
        return json.dumps({"error": "query must be non-empty"}, indent=2)
    if len(q) > NOTES_QUERY_MAX_LEN:
        return json.dumps(
            {"error": f"query must be at most {NOTES_QUERY_MAX_LEN} characters"},
            indent=2,
        )
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        return json.dumps({"error": "limit must be an integer"}, indent=2)
    n = max(NOTES_LIMIT_MIN, min(lim, NOTES_LIMIT_MAX))
    acc = (account or "").strip()
    try:
        raw = _run_applescript(
            NOTES_SEARCH_NOTES_SCRIPT,
            [q, acc, str(n)],
            timeout=180.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Notes AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str | float]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        r = _notes_parse_search_row(ln)
        if r:
            rows.append(r)
    return json.dumps(rows, indent=2)


@mcp.tool()
def notes_add_note(
    folder_path: str,
    name: str,
    body: str,
    account: str | None = None,
) -> str:
    """Create a note (body is typically HTML that Notes.app understands)."""
    fp = folder_path.strip()
    if not fp:
        return json.dumps({"error": "folder_path must be non-empty"}, indent=2)
    nm = name if name is not None else ""
    if "\x00" in nm or "\x00" in body:
        return json.dumps({"error": "name/body must not contain NUL"}, indent=2)
    acc = (account or "").strip()
    try:
        raw = _run_applescript(
            NOTES_ADD_NOTE_SCRIPT,
            [acc, fp, _b64_utf8(nm), _b64_utf8(body)],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Notes AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    new_id = raw.strip()
    if not new_id:
        return json.dumps({"error": "Notes returned empty id"}, indent=2)
    return json.dumps({"id": new_id}, indent=2)


@mcp.tool()
def notes_update_note(
    note_id: str,
    name: str | None = None,
    body: str | None = None,
) -> str:
    """Update a note's name and/or body. Omit a field to leave it unchanged."""
    nid = note_id.strip()
    if not nid:
        return json.dumps({"error": "note_id must be non-empty"}, indent=2)
    if name is None and body is None:
        return json.dumps({"error": "provide at least one of name or body"}, indent=2)
    name_tok = NOTES_SKIP_FIELD if name is None else _b64_utf8(name)
    body_tok = NOTES_SKIP_FIELD if body is None else _b64_utf8(body)
    if name is not None and "\x00" in name:
        return json.dumps({"error": "name must not contain NUL"}, indent=2)
    if body is not None and "\x00" in body:
        return json.dumps({"error": "body must not contain NUL"}, indent=2)
    try:
        raw = _run_applescript(
            NOTES_UPDATE_NOTE_SCRIPT,
            [nid, name_tok, body_tok],
            timeout=120.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Notes AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    return json.dumps({"ok": True, "id": raw.strip()}, indent=2)


@mcp.tool()
def notes_delete_note(note_id: str) -> str:
    """Delete a note by id."""
    nid = note_id.strip()
    if not nid:
        return json.dumps({"error": "note_id must be non-empty"}, indent=2)
    try:
        raw = _run_applescript(NOTES_DELETE_NOTE_SCRIPT, [nid], timeout=60.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Notes AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if raw.strip().upper() == "OK":
        return json.dumps({"ok": True}, indent=2)
    return json.dumps({"ok": True, "detail": raw}, indent=2)


@mcp.tool()
def itunes_list_playlists() -> str:
    """List Music.app playlists (Apple Music / library). Tool prefix itunes_* targets Music.app.

    Returns name, persistent_id, and special_kind (may be empty).
    """
    try:
        raw = _run_applescript(ITUNES_LIST_PLAYLISTS_SCRIPT, [], timeout=120.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Music AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        parts = ln.split("\t", 2)
        rows.append(
            {
                "name": parts[0],
                "persistent_id": parts[1] if len(parts) > 1 else "",
                "special_kind": parts[2] if len(parts) > 2 else "",
            }
        )
    return json.dumps(rows, indent=2)


@mcp.tool()
def itunes_search_library(
    query: str,
    limit: int = 25,
    max_scan: int = 8000,
) -> str:
    """Search the main library from the start of the track list (name / artist / album contains).

    max_scan: Cap how many library tracks to examine (100–100000) to avoid huge scans.
    """
    q = query.strip()
    if not q:
        return json.dumps({"error": "query must be non-empty"}, indent=2)
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        return json.dumps({"error": "limit must be an integer"}, indent=2)
    try:
        ms = int(max_scan)
    except (TypeError, ValueError):
        return json.dumps({"error": "max_scan must be an integer"}, indent=2)
    nlim = max(ITUNES_MATCH_LIMIT_MIN, min(lim, ITUNES_MATCH_LIMIT_MAX))
    nscan = max(ITUNES_SCAN_MAX_MIN, min(ms, ITUNES_SCAN_MAX_MAX))
    try:
        raw = _run_applescript(
            ITUNES_SEARCH_LIBRARY_SCRIPT,
            [q, str(nlim), str(nscan)],
            timeout=180.0,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Music AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    rows: list[dict[str, str | float | int]] = []
    for ln in raw.splitlines():
        if not ln.strip():
            continue
        r = _itunes_parse_track_row(ln)
        if r:
            rows.append(r)
    return json.dumps(rows, indent=2)


@mcp.tool()
def itunes_get_track(persistent_id: str) -> str:
    """Look up one library track by **persistent_id** (string of digits from search/list)."""
    pid = persistent_id.strip()
    if not pid:
        return json.dumps({"error": "persistent_id must be non-empty"}, indent=2)
    try:
        raw = _run_applescript(ITUNES_GET_TRACK_SCRIPT, [pid], timeout=60.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Music AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    parts = raw.split("\t", 7)
    if len(parts) < 8:
        return json.dumps({"error": "Unexpected Music output"}, indent=2)
    (
        pid_o,
        name,
        artist,
        album,
        dur_s,
        tn_s,
        genre,
        loc,
    ) = parts
    try:
        dur = float(dur_s)
        tn = int(tn_s)
    except ValueError:
        dur, tn = 0.0, 0
    return json.dumps(
        {
            "persistent_id": pid_o,
            "name": name,
            "artist": artist,
            "album": album,
            "duration_sec": dur,
            "track_number": tn,
            "genre": genre,
            "location": loc,
        },
        indent=2,
    )


@mcp.tool()
def itunes_now_playing() -> str:
    """Return Music.app transport state and current track metadata (if any)."""
    try:
        raw = _run_applescript(ITUNES_NOW_PLAYING_SCRIPT, [], timeout=30.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Music AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    sep = chr(30)
    parts = raw.split(sep, 7)
    if len(parts) < 8:
        return json.dumps({"error": "Unexpected Music output"}, indent=2)
    ps, pid, name, artist, album, pos_s, dur_s = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
    try:
        pos = float(pos_s) if pos_s.strip() else 0.0
        dur = float(dur_s) if dur_s.strip() else 0.0
    except ValueError:
        pos, dur = 0.0, 0.0
    return json.dumps(
        {
            "player_state": ps,
            "persistent_id": pid,
            "name": name,
            "artist": artist,
            "album": album,
            "position_sec": pos,
            "duration_sec": dur,
        },
        indent=2,
    )


@mcp.tool()
def itunes_play_track(persistent_id: str | None = None) -> str:
    """Play a library track by persistent_id, or resume/start playback when id is omitted."""
    pid = persistent_id.strip() if persistent_id else ""
    try:
        raw = _run_applescript(ITUNES_PLAY_TRACK_SCRIPT, [pid], timeout=60.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Music AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if raw.strip().upper() == "OK":
        return json.dumps({"ok": True}, indent=2)
    return json.dumps({"ok": True, "detail": raw}, indent=2)


@mcp.tool()
def itunes_play_pause() -> str:
    """Toggle Music.app play / pause."""
    try:
        raw = _run_applescript(ITUNES_PLAY_PAUSE_SCRIPT, [], timeout=30.0)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Music AppleScript timed out"}, indent=2)
    except RuntimeError as e:
        return json.dumps({"error": str(e)}, indent=2)
    if raw.strip().upper() == "OK":
        return json.dumps({"ok": True}, indent=2)
    return json.dumps({"ok": True, "detail": raw}, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
