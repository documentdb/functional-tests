"""
Smoke test for $skip stage.

Tests basic $skip functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_skip(collection):
    """Test basic $skip behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 10}, {"_id": 2, "value": 20}, {"_id": 3, "value": 30}]
    )

    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": [{"$skip": 2}], "cursor": {}}
    )

    expected = [{"_id": 3, "value": 30}]
    assertSuccess(result, expected, msg="Should support $skip stage")
