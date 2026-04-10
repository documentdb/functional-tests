"""
Smoke test for listIndexes command.

Tests basic listIndexes command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_listIndexes(collection):
    """Test basic listIndexes command behavior."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_command(collection, {"listIndexes": collection.name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support listIndexes command")
