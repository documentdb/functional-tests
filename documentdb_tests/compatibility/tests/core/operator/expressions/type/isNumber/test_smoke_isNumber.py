"""
Smoke test for $isNumber expression.

Tests basic $isNumber expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_isNumber(collection):
    """Test basic $isNumber expression behavior."""
    collection.insert_many([{"_id": 1, "value": 123}, {"_id": 2, "value": "abc"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isNum": {"$isNumber": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "isNum": True}, {"_id": 2, "isNum": False}]
    assertSuccess(result, expected, msg="Should support $isNumber expression")
