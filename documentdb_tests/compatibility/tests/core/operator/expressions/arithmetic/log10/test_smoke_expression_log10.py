"""
Smoke test for $log10 expression.

Tests basic $log10 expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_log10(collection):
    """Test basic $log10 expression behavior."""
    collection.insert_many([{"_id": 1, "value": 100}, {"_id": 2, "value": 1000}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"log10": {"$log10": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "log10": 2.0}, {"_id": 2, "log10": 3.0}]
    assertSuccess(result, expected, msg="Should support $log10 expression")
