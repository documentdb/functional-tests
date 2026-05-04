"""
Smoke test for sparse index property.

Tests basic sparse index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_sparse(collection):
    """Test basic sparse index behavior."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"email": 1}, "name": "email_sparse", "sparse": True}],
        },
    )

    expected = {
        "numIndexesBefore": 1,
        "numIndexesAfter": 2,
        "createdCollectionAutomatically": True,
        "ok": 1.0,
    }
    assertSuccessPartial(result, expected, msg="Should support sparse index property")
