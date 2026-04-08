"""
Smoke test for $bitsAllSet query operator.

Tests basic $bitsAllSet query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_bitsAllSet(collection):
    """Test basic $bitsAllSet query operator behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 54}, {"_id": 2, "value": 20}, {"_id": 3, "value": 10}]
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"value": {"$bitsAllSet": [1, 5]}}}
    )

    expected = [{"_id": 1, "value": 54}]
    assertSuccess(result, expected, msg="Should support $bitsAllSet query operator")
