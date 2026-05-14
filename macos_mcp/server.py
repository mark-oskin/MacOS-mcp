"""MCP server: Mail and other macOS automation via AppleScript."""

from __future__ import annotations

import json
import os
import re
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

MAX_BODY_BYTES = 10 * 1024 * 1024


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
    return json.dumps(out, indent=2)


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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
