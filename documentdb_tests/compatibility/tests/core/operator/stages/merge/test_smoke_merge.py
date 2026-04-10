"""
Smoke test for $merge stage.

Tests basic $merge functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_merge(collection):
    """Test basic $merge behavior."""
    collection.insert_many([{"_id": 1, "value": 10}, {"_id": 2, "value": 20}])

    target_name = f"{collection.name}_target"
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$merge": {"into": target_name}}],
            "cursor": {},
        },
    )

    target_result = execute_command(collection, {"find": target_name, "filter": {}})

    expected = [{"_id": 1, "value": 10}, {"_id": 2, "value": 20}]
    assertSuccess(
        target_result, expected, msg="Should create target collection with merged documents"
    )
