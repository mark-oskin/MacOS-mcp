"""MCP server: Mail and other macOS automation via AppleScript."""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
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

MAX_BODY_BYTES = 10 * 1024 * 1024

SEARCH_LIMIT_MIN = 1
SEARCH_LIMIT_MAX = 50
SEARCH_SCAN_MIN = 1
SEARCH_SCAN_MAX = 2000

ATTACHMENT_MAX_FILES = 15
ATTACHMENT_MAX_BYTES_PER_FILE = 5 * 1024 * 1024
ATTACHMENT_MAX_TOTAL_BYTES = 25 * 1024 * 1024


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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
