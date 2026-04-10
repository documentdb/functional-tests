"""
Smoke test for convertToCapped command.

Tests basic convertToCapped command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_convertToCapped(collection):
    """Test basic convertToCapped command behavior."""
    collection.insert_many([{"_id": 1, "value": 10}, {"_id": 2, "value": 20}])

    result = execute_command(collection, {"convertToCapped": collection.name, "size": 100000})

    expected = {"ok": 1.0}
    assertSuccess(result, expected, msg="Should support convertToCapped command", raw_res=True)
