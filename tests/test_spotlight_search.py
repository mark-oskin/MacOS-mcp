"""Unit tests for Spotlight search helpers (mocked mdfind/mdls)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from macos_mcp.spotlight_search import (
    search_calendar_events_spotlight,
    search_mail_spotlight,
)


class TestSpotlightSearch(unittest.TestCase):
    @patch("macos_mcp.spotlight_search.mdls_values")
    @patch("macos_mcp.spotlight_search.mdfind_paths")
    def test_mail_search_maps_metadata(self, mock_find: object, mock_mdls: object) -> None:
        mock_find.return_value = ["/Users/me/Library/Mail/V10/msg.emlx"]  # type: ignore[attr-defined]
        mock_mdls.return_value = {  # type: ignore[attr-defined]
            "kMDItemSubject": "Hello",
            "kMDItemAuthors": "alice@example.com",
            "kMDItemContentCreationDate": "2026-05-15 12:00:00 +0000",
            "kMDItemRecipientAddresses": "bob@example.com",
        }
        rows = search_mail_spotlight("hello", limit=5)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["subject"], "Hello")
        self.assertEqual(rows[0]["sender"], "alice@example.com")
        self.assertIn("msg.emlx", rows[0]["spotlight_path"])

    @patch("macos_mcp.spotlight_search.mdls_values")
    @patch("macos_mcp.spotlight_search.mdfind_paths")
    def test_calendar_search_parses_dates(self, mock_find: object, mock_mdls: object) -> None:
        mock_find.return_value = ["/tmp/event.ics"]  # type: ignore[attr-defined]
        mock_mdls.return_value = {  # type: ignore[attr-defined]
            "kMDItemTitle": "Standup",
            "kMDItemStartDate": "2026-05-15 15:00:00 +0000",
            "kMDItemEndDate": "2026-05-15 15:30:00 +0000",
            "kMDItemDescription": "Room A",
        }
        rows = search_calendar_events_spotlight(
            "standup",
            start_unix=1_700_000_000.0,
            end_unix=1_900_000_000.0,
            limit=5,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["summary"], "Standup")
        self.assertIsNotNone(rows[0]["start_unix"])
        self.assertIsNotNone(rows[0]["end_unix"])


if __name__ == "__main__":
    unittest.main()
