"""
Smoke test for $type expression.

Tests basic $type expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_type(collection):
    """Test basic $type expression behavior."""
    collection.insert_many([{"_id": 1, "value": 123}, {"_id": 2, "value": "abc"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"valueType": {"$type": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "valueType": "int"}, {"_id": 2, "valueType": "string"}]
    assertSuccess(result, expected, msg="Should support $type expression")
