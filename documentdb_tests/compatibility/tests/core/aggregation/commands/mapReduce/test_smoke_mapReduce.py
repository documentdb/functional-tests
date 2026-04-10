"""
Smoke test for mapReduce command.

Tests basic mapReduce command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_mapReduce(collection):
    """Test basic mapReduce command behavior."""
    collection.insert_many(
        [{"_id": 1, "category": "A", "value": 10}, {"_id": 2, "category": "A", "value": 20}]
    )

    result = execute_command(
        collection,
        {
            "mapReduce": collection.name,
            "map": "function() { emit(this.category, this.value); }",
            "reduce": "function(key, values) { return Array.sum(values); }",
            "out": {"inline": 1},
        },
    )

    expected = {"results": [{"_id": "A", "value": 30.0}], "ok": 1.0}
    assertSuccess(result, expected, msg="Should support mapReduce command", raw_res=True)
