"""Regression tests for table-state changes. Run with python -m unittest backend.test_status_logic."""
import unittest

from .status_logic import TableState


class TableStateTests(unittest.TestCase):
    def test_missing_observations_cannot_confirm_change(self):
        table = TableState()
        table.observe(4, 0, 0, 0)
        table.observe(4, 0, 0, 2)
        table.observe(4, 1, 0, 3)
        table.observe(4, 1, 0, 8)
        self.assertEqual(table.status, "free")
        table.observe(4, 1, 0, 10)
        self.assertEqual(table.status, "partly_taken")

    def test_stale_reading_and_new_items_interval(self):
        table = TableState()
        table.observe(4, 0, 1, 0)
        table.observe(4, 0, 1, 2)
        self.assertEqual(table.snapshot(1, 5)["items_seconds"], 5)
        stale = table.snapshot(1, 14)
        self.assertEqual(stale["status"], "unknown")
        self.assertIsNone(stale["items"])
        table.observe(4, 0, 1, 14)
        self.assertEqual(table.status, "unknown")
        table.observe(4, 0, 1, 16)
        self.assertEqual(table.snapshot(1, 16)["items_seconds"], 2)

    def test_capacity_change_requires_confirmation(self):
        table = TableState()
        table.observe(4, 3, 0, 0)
        table.observe(4, 3, 0, 2)
        table.observe(3, 3, 0, 3)
        self.assertEqual(table.status, "unknown")
        table.observe(3, 3, 0, 5)
        self.assertEqual(table.status, "full")
