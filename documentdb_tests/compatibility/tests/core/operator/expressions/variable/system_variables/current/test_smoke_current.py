"""
Smoke test for the $$CURRENT system variable.

Tests basic $$CURRENT field access behavior.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_current(collection):
    """Test basic $$CURRENT field path access."""
    collection.insert_one({"_id": 1, "a": 5})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": "$$CURRENT.a"}}],
            "cursor": {},
        },
    )

    expected = [{"result": 5}]
    assertSuccess(result, expected, msg="Should support $$CURRENT field path access")
