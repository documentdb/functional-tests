"""
Smoke test for text index type.

Tests basic text index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_text(collection):
    """Test basic text index behavior."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"description": "text"}, "name": "description_text"}],
        },
    )

    assertCommandSupported(result, msg="Should support text index type")
