"""
Smoke test for setIndexCommitQuorum command.

Tests basic setIndexCommitQuorum functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailure
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_setIndexCommitQuorum(collection):
    """Test basic setIndexCommitQuorum behavior."""
    collection.insert_one({"_id": 1, "x": 1})
    collection.create_index([("x", 1)])

    result = execute_command(
        collection,
        {
            "setIndexCommitQuorum": collection.name,
            "indexNames": ["x_1"],
            "commitQuorum": "majority",
        },
    )

    expected = {
        "code": 27,
        "msg": (
            f"Cannot find an index build on collection "
            f"'{collection.database.name}.{collection.name}' "
            f"with the provided index names"
        ),
    }
    assertFailure(result, expected, msg="Should support setIndexCommitQuorum command")
