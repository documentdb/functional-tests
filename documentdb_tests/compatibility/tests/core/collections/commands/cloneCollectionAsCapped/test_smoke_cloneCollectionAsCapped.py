"""
Smoke test for cloneCollectionAsCapped command.

Tests basic cloneCollectionAsCapped command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_cloneCollectionAsCapped(collection):
    """Test basic cloneCollectionAsCapped command behavior."""
    collection.insert_many([{"_id": 1, "value": 10}, {"_id": 2, "value": 20}])

    result = execute_command(
        collection,
        {
            "cloneCollectionAsCapped": collection.name,
            "toCollection": f"{collection.name}_capped",
            "size": 100000,
        },
    )

    expected = {"ok": 1.0}
    assertSuccess(
        result, expected, msg="Should support cloneCollectionAsCapped command", raw_res=True
    )
