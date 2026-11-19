"""
Smoke test for hidden index property.

Tests basic hidden index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_hidden(collection):
    """Test basic hidden index behavior."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"status": 1}, "name": "status_1", "hidden": True}],
        },
    )

    assertCommandSupported(result, msg="Should support hidden index property")
