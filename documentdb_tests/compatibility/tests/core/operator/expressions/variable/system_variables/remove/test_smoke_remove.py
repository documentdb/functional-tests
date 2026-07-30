"""
Smoke test for the $$REMOVE system variable.

Tests basic $$REMOVE field-omission behavior.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_remove(collection):
    """Test basic $$REMOVE field omission in $project."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"a": "$$REMOVE", "b": 1}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "b": 2}]
    assertSuccess(result, expected, msg="Should support $$REMOVE to omit a field")
