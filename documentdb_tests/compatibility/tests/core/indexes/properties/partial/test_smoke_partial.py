"""
Smoke test for partial index property.

Tests basic partial index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_partial(collection):
    """Test basic partial index behavior."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"score": 1},
                    "name": "score_partial",
                    "partialFilterExpression": {"score": {"$gt": 80}},
                }
            ],
        },
    )

    assertCommandSupported(result, msg="Should support partial index property")
