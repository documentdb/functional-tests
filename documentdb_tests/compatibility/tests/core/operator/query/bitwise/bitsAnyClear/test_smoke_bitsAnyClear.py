"""
Smoke test for $bitsAnyClear query operator.

Tests basic $bitsAnyClear query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_bitsAnyClear(collection):
    """Test basic $bitsAnyClear query operator behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 20}, {"_id": 2, "value": 15}, {"_id": 3, "value": 54}]
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"value": {"$bitsAnyClear": [1, 5]}}}
    )

    expected = [{"_id": 1, "value": 20}, {"_id": 2, "value": 15}]
    assertSuccess(result, expected, msg="Should support $bitsAnyClear query operator")
