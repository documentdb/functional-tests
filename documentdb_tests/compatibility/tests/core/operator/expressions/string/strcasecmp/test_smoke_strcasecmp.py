"""
Smoke test for $strcasecmp expression.

Tests basic $strcasecmp expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_strcasecmp(collection):
    """Test basic $strcasecmp expression behavior."""
    collection.insert_many(
        [{"_id": 1, "str1": "hello", "str2": "HELLO"}, {"_id": 2, "str1": "abc", "str2": "xyz"}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$strcasecmp": ["$str1", "$str2"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 0}, {"_id": 2, "result": -1}]
    assertSuccess(result, expected, msg="Should support $strcasecmp expression")
