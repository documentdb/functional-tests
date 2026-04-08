"""
Smoke test for $sigmoid expression.

Tests basic $sigmoid expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_sigmoid(collection):
    """Test basic $sigmoid expression behavior."""
    collection.insert_many([{"_id": 1, "value": 0}, {"_id": 2, "value": 1}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"sigmoid": {"$sigmoid": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "sigmoid": 0.5}, {"_id": 2, "sigmoid": 0.7310585786300049}]
    assertSuccess(result, expected, msg="Should support $sigmoid expression")
