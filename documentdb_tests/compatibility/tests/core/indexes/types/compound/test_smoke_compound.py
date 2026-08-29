"""
Smoke test for compound index type.

Tests basic compound index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_compound(collection):
    """Test basic compound index behavior."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"lastName": 1, "firstName": 1}, "name": "name_compound"}],
        },
    )

    assertCommandSupported(result, msg="Should support compound index type")
