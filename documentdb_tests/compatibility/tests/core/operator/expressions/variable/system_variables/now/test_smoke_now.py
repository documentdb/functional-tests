"""Smoke test for the $$NOW system variable: resolves to a BSON date."""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_now(collection):
    """Test $$NOW resolves to a BSON date."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": {"$type": "$$NOW"}}}],
            "cursor": {},
        },
    )

    expected = [{"result": "date"}]
    assertSuccess(result, expected, msg="$$NOW should resolve to a date")
