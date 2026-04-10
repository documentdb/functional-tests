"""
Smoke test for $maxN-array-element expression.

Tests basic $maxN-array-element expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_maxN_array_element(collection):
    """Test basic $maxN-array-element expression behavior."""
    collection.insert_many(
        [{"_id": 1, "values": [10, 30, 20, 40]}, {"_id": 2, "values": [5, 25, 15, 35]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"maxTwo": {"$maxN": {"n": 2, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "maxTwo": [40, 30]}, {"_id": 2, "maxTwo": [35, 25]}]
    assertSuccess(result, expected, msg="Should support $maxN-array-element expression")
