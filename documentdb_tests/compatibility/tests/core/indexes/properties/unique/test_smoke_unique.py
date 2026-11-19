"""
Smoke test for unique index property.

Tests basic unique index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_unique(collection):
    """Test basic unique index behavior."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"email": 1}, "name": "email_unique", "unique": True}],
        },
    )

    assertCommandSupported(result, msg="Should support unique index property")
