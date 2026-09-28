"""
Smoke test for the $$CLUSTER_TIME system variable.

Tests that $$CLUSTER_TIME resolves and yields a BSON timestamp.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.smoke, pytest.mark.requires(cluster_time=True)]


def test_smoke_cluster_time(collection):
    """Test $$CLUSTER_TIME resolves to a BSON timestamp."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": {"$type": "$$CLUSTER_TIME"}}}],
            "cursor": {},
        },
    )

    expected = [{"result": "timestamp"}]
    assertSuccess(result, expected, msg="$$CLUSTER_TIME should resolve to a timestamp")
