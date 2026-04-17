"""
Smoke test for $setUnion expression accumulator.

Tests basic $setUnion expression accumulator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_setUnion(collection):
    """Test basic $setUnion expression accumulator behavior."""
    collection.insert_many(
        [{"_id": 1, "a": [1, 2], "b": [2, 3]}, {"_id": 2, "a": [4, 5], "b": [5, 6]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"union": {"$setUnion": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "union": [1, 2, 3]}, {"_id": 2, "union": [4, 5, 6]}]

    def sort_union(docs):
        return [{**d, "union": sorted(d["union"], key=str)} for d in docs]

    assertSuccess(
        result,
        expected,
        msg="Should support $setUnion expression accumulator",
        transform=sort_union,
    )
