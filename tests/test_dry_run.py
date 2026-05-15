"""Tests for MACOS_MCP_DRY_RUN — no live Mail/Calendar/etc. automation."""

from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest.mock import patch

import macos_mcp.server as server
from macos_mcp.dry_run import MUTATING_TOOLS, dry_run_blocked, is_dry_run


class TestDryRunEnv(unittest.TestCase):
    def test_is_dry_run_truthy_values(self) -> None:
        for v in ("1", "true", "YES", "on"):
            with patch.dict(os.environ, {"MACOS_MCP_DRY_RUN": v}):
                self.assertTrue(is_dry_run())

    def test_is_dry_run_off(self) -> None:
        with patch.dict(os.environ, {"MACOS_MCP_DRY_RUN": "0"}, clear=False):
            self.assertFalse(is_dry_run())
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MACOS_MCP_DRY_RUN", None)
            self.assertFalse(is_dry_run())


class TestDryRunTools(unittest.TestCase):
    def setUp(self) -> None:
        self._env = patch.dict(os.environ, {"MACOS_MCP_DRY_RUN": "1"})
        self._env.start()

    def tearDown(self) -> None:
        self._env.stop()

    def test_mail_send_blocked_without_applescript(self) -> None:
        with patch.object(server, "_run_mail_send") as mock_send:
            out = server.mail_send(to="test@example.com", subject="hi", body="there")
            mock_send.assert_not_called()
        data = json.loads(out)
        self.assertTrue(data.get("dry_run"))
        self.assertEqual(data.get("tool"), "mail_send")

    def test_mail_list_accounts_not_in_mutating_set(self) -> None:
        self.assertNotIn("mail_list_accounts", MUTATING_TOOLS)

    @patch.object(server, "_run_applescript", return_value="")
    def test_mail_list_accounts_can_run_under_dry_run(self, mock_as: object) -> None:
        server.mail_list_accounts()
        mock_as.assert_called_once()  # type: ignore[attr-defined]

    def test_call_tool_blocks_mutating_via_mcp(self) -> None:
        server.mcp.set_enabled_tools(frozenset(["mail_send"]))

        async def run() -> str:
            blocks = await server.mcp.call_tool(
                "mail_send",
                {"to": "x@y.com", "subject": "s", "body": "b"},
            )
            return blocks[0].text

        with patch.object(server, "_run_mail_send") as mock_send:
            text = asyncio.run(run())
            mock_send.assert_not_called()
        data = json.loads(text)
        self.assertTrue(data.get("dry_run"))

    def test_call_tool_disabled_still_checked_first(self) -> None:
        server.mcp.set_enabled_tools(frozenset())

        async def run() -> str:
            blocks = await server.mcp.call_tool("mail_send", {})
            return blocks[0].text

        with patch.object(server, "_run_mail_send") as mock_send:
            text = asyncio.run(run())
            mock_send.assert_not_called()
        self.assertIn("disabled", text.lower())

    def test_dry_run_blocked_helper(self) -> None:
        self.assertIsNotNone(dry_run_blocked("mail_delete"))
        self.assertIsNone(dry_run_blocked("mail_get_headers"))


if __name__ == "__main__":
    unittest.main()
