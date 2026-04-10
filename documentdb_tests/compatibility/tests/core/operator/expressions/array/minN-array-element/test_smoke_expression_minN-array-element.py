"""
Smoke test for $minN-array-element expression.

Tests basic $minN-array-element expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_minN_array_element(collection):
    """Test basic $minN-array-element expression behavior."""
    collection.insert_many(
        [{"_id": 1, "values": [30, 10, 40, 20]}, {"_id": 2, "values": [25, 5, 35, 15]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"minTwo": {"$minN": {"n": 2, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "minTwo": [10, 20]}, {"_id": 2, "minTwo": [5, 15]}]
    assertSuccess(result, expected, msg="Should support $minN-array-element expression")
