"""
Smoke test for sparse index property.

Tests basic sparse index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
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

    assertCommandSupported(result, msg="Should support sparse index property")
