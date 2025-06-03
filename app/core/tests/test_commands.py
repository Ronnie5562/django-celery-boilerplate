"""
Test custom Django management commands
"""

from unittest.mock import patch
from django.test import SimpleTestCase
from django.db.utils import OperationalError
from django.core.management import call_command
from psycopg2 import OperationalError as Psycopg2OperationalError


@patch("core.management.commands.wait_for_db.Command.check")
class CommandTestCases(SimpleTestCase):
    """
    Test for our django custom commands
    """

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for db until it's ready"""
        patched_check.return_value = True
        call_command("wait_for_db")

        patched_check.assert_called_once_with(databases=["default"])

    @patch("time.sleep")
    def test_wait_for_db_delay(self, patched_time, patched_check):
        """Test waiting for db when db is not available"""
        patched_check.side_effect = [
            Psycopg2OperationalError,
            Psycopg2OperationalError,
            OperationalError,
            OperationalError,
            True,
        ]

        call_command("wait_for_db")

        self.assertEqual(patched_check.call_count, 5)
        patched_check.assert_called_with(databases=["default"])
