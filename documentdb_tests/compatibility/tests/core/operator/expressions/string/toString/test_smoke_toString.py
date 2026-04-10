"""
Smoke test for $toString expression.

Tests basic $toString expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toString(collection):
    """Test basic $toString expression behavior."""
    collection.insert_many([{"_id": 1, "value": 123}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"str": {"$toString": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "str": "123"}]
    assertSuccess(result, expected, msg="Should support $toString expression")
