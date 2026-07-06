"""
Smoke test for $isArray expression.

Tests basic $isArray expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_isArray(collection):
    """Test basic $isArray expression behavior."""
    collection.insert_many([{"_id": 1, "value": [1, 2, 3]}, {"_id": 2, "value": "not an array"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isArray": {"$isArray": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "isArray": True}, {"_id": 2, "isArray": False}]
    assertSuccess(result, expected, msg="Should support $isArray expression")
