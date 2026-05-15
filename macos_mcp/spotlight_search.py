"""Spotlight (mdfind/mdls) helpers for Mail and Calendar search."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from typing import Any


def _escape_spotlight_word(query: str) -> str:
    """Sanitize a user term for embedding in a Spotlight query string."""
    s = query.strip()
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return s


def _spotlight_time_z(unix_ts: float) -> str:
    return datetime.fromtimestamp(float(unix_ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mdfind_paths(query: str, *, limit: int, timeout: float = 60.0) -> list[str]:
    proc = subprocess.run(
        ["mdfind", "-0", query],
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        raise RuntimeError(err or f"mdfind exited with {proc.returncode}")
    raw = proc.stdout.decode("utf-8", errors="replace")
    paths = [p for p in raw.split("\0") if p]
    return paths[: max(limit, 0)]


def mdls_values(path: str, keys: list[str], *, timeout: float = 15.0) -> dict[str, str]:
    if not path:
        return {}
    proc = subprocess.run(
        ["mdls", "-plist", path],
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout:
        try:
            import plistlib

            data = plistlib.loads(proc.stdout)
            if isinstance(data, dict):
                return {k: _stringify_mdls(data.get(k)) for k in keys}
        except Exception:
            pass
    return _mdls_values_raw(path, keys, timeout=timeout)


def _mdls_values_raw(path: str, keys: list[str], *, timeout: float) -> dict[str, str]:
    out: dict[str, str] = {}
    for key in keys:
        proc = subprocess.run(
            ["mdls", "-raw", "-name", key, path],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if proc.returncode != 0:
            continue
        val = proc.stdout.decode("utf-8", errors="replace").strip()
        if val and val != "(null)":
            out[key] = val
    return out


def _stringify_mdls(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, list):
        return ", ".join(str(x) for x in val)
    return str(val)


def search_mail_spotlight(
    query: str,
    *,
    limit: int,
    mailbox: str | None = None,
    account: str | None = None,
) -> list[dict[str, str]]:
    q = _escape_spotlight_word(query)
    if not q:
        return []
    spotlight_q = f'kind:mail "{q}"'
    paths = mdfind_paths(spotlight_q, limit=limit * 4, timeout=90.0)
    mb = (mailbox or "").strip().lower()
    acc = (account or "").strip().lower()
    rows: list[dict[str, str]] = []
    keys = [
        "kMDItemSubject",
        "kMDItemAuthors",
        "kMDItemAuthorEmailAddresses",
        "kMDItemRecipientAddresses",
        "kMDItemContentCreationDate",
        "kMDItemContentModificationDate",
        "kMDItemDisplayName",
    ]
    for path in paths:
        if len(rows) >= limit:
            break
        if mb and mb not in path.lower():
            continue
        if acc and acc not in path.lower():
            continue
        meta = mdls_values(path, keys)
        subj = meta.get("kMDItemSubject") or meta.get("kMDItemDisplayName") or ""
        sender = meta.get("kMDItemAuthors") or meta.get("kMDItemAuthorEmailAddresses") or ""
        date_s = meta.get("kMDItemContentCreationDate") or meta.get("kMDItemContentModificationDate") or ""
        to_addrs = meta.get("kMDItemRecipientAddresses") or ""
        rows.append(
            {
                "id": "",
                "message_id": "",
                "subject": subj,
                "sender": sender,
                "date": date_s,
                "to": to_addrs,
                "cc": "",
                "spotlight_path": path,
            }
        )
    return rows


def search_calendar_events_spotlight(
    query: str,
    *,
    start_unix: float,
    end_unix: float,
    limit: int,
    calendar_name: str | None = None,
) -> list[dict[str, Any]]:
    q = _escape_spotlight_word(query)
    if not q:
        return []
    start_z = _spotlight_time_z(start_unix)
    end_z = _spotlight_time_z(end_unix)
    text_clause = (
        f'(kMDItemTitle == "*{q}*"cd || kMDItemTextContent == "*{q}*"cd '
        f'|| kMDItemDescription == "*{q}*"cd || kMDItemWhereFroms == "*{q}*"cd)'
    )
    spotlight_q = (
        f"kind:event kMDItemStartDate < $time.{end_z} "
        f"kMDItemEndDate > $time.{start_z} {text_clause}"
    )
    paths = mdfind_paths(spotlight_q, limit=limit * 3, timeout=90.0)
    cal_hint = (calendar_name or "").strip().lower()
    rows: list[dict[str, Any]] = []
    keys = [
        "kMDItemTitle",
        "kMDItemStartDate",
        "kMDItemEndDate",
        "kMDItemContentCreationDate",
        "kMDItemDescription",
        "kMDItemWhereFroms",
    ]
    for path in paths:
        if len(rows) >= limit:
            break
        meta = mdls_values(path, keys)
        title = meta.get("kMDItemTitle") or ""
        if cal_hint and cal_hint not in path.lower() and cal_hint not in title.lower():
            loc = meta.get("kMDItemWhereFroms") or meta.get("kMDItemDescription") or ""
            if cal_hint not in loc.lower():
                continue
        sux = _parse_mdls_date_to_unix(meta.get("kMDItemStartDate"))
        eux = _parse_mdls_date_to_unix(meta.get("kMDItemEndDate"))
        if sux is None:
            sux = _parse_mdls_date_to_unix(meta.get("kMDItemContentCreationDate"))
        if eux is None and sux is not None:
            eux = sux + 3600
        if sux is None or eux is None:
            continue
        loc = meta.get("kMDItemWhereFroms") or meta.get("kMDItemDescription") or ""
        rows.append(
            {
                "calendar": calendar_name or "",
                "uid": "",
                "summary": title,
                "location": loc,
                "all_day": False,
                "start_unix": sux,
                "end_unix": eux,
                "start_iso": _iso_z(sux),
                "end_iso": _iso_z(eux),
                "spotlight_path": path,
            }
        )
    return rows


def _iso_z(ts: float) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_mdls_date_to_unix(raw: str | None) -> float | None:
    if not raw:
        return None
    s = raw.strip()
    if s.startswith("$time."):
        s = s[6:]
    for fmt in (
        "%Y-%m-%d %H:%M:%S %z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            dt = datetime.strptime(s.replace(" +0000", " +0000"), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", s)
    if m:
        try:
            dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            pass
    return None
