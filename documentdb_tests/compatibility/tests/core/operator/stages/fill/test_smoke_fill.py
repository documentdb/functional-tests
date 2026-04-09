"""
Smoke test for $fill stage.

Tests basic $fill functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_fill(collection):
    """Test basic $fill behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 1}, {"_id": 2, "value": None}, {"_id": 3, "value": 3}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$fill": {"output": {"value": {"method": "locf"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "value": 1}, {"_id": 2, "value": 1}, {"_id": 3, "value": 3}]
    assertSuccess(result, expected, msg="Should support $fill stage")
