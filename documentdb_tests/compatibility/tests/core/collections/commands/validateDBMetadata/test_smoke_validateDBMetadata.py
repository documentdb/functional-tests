"""
Smoke test for validateDBMetadata command.

Tests basic database metadata validation functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_validateDBMetadata(collection):
    """Test basic validateDBMetadata command."""
    result = execute_admin_command(
        collection,
        {
            "validateDBMetadata": 1,
            "db": collection.database.name,
            "apiParameters": {"version": "1", "strict": True},
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support validateDBMetadata command")
