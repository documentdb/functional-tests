"""
Smoke test for the $$ROOT system variable.

Tests basic $$ROOT system variable functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_root(collection):
    """Test basic $$ROOT system variable behavior."""
    collection.insert_one({"_id": 1, "a": 10})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "snap": "$$ROOT"}}],
            "cursor": {},
        },
    )

    expected = [{"snap": {"_id": 1, "a": 10}}]
    assertSuccess(result, expected, msg="Should support $$ROOT system variable")
