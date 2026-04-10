"""
Smoke test for $bitsAllClear query operator.

Tests basic $bitsAllClear query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_bitsAllClear(collection):
    """Test basic $bitsAllClear query operator behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 20}, {"_id": 2, "value": 10}, {"_id": 3, "value": 5}]
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"value": {"$bitsAllClear": [1, 5]}}}
    )

    expected = [{"_id": 1, "value": 20}, {"_id": 3, "value": 5}]
    assertSuccess(result, expected, msg="Should support $bitsAllClear query operator")
