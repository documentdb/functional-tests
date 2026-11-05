"""Smoke test for the $$USER_ROLES system variable: the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_user_roles(collection):
    """Test the engine accepts $$USER_ROLES in an expression."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": "$$USER_ROLES"}}],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $$USER_ROLES system variable")
