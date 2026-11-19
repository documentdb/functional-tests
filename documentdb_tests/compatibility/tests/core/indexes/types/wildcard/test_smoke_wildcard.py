"""
Smoke test for wildcard index type.

Tests basic wildcard index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_wildcard(collection):
    """Test basic wildcard index behavior."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"$**": 1}, "name": "wildcard_index"}],
        },
    )

    assertCommandSupported(result, msg="Should support wildcard index type")
