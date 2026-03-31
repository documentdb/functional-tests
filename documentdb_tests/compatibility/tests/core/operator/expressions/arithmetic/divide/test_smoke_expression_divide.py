"""
Smoke test for $divide expression.

Tests basic $divide expression functionality.
"""

import pytest

from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.assertions import assertSuccess

pytestmark = pytest.mark.smoke


def test_smoke_expression_divide(collection):
    """Test basic $divide expression behavior."""
    collection.insert_many([
        {"_id": 1, "a": 20, "b": 4},
        {"_id": 2, "a": 30, "b": 5}
    ])
    
    result = execute_command(collection, {
        "aggregate": collection.name,
        "pipeline": [
            {"$project": {"quotient": {"$divide": ["$a", "$b"]}}}
        ],
        "cursor": {}
    })
    
    expected = [{"_id": 1, "quotient": 5}, {"_id": 2, "quotient": 6}]
    assertSuccess(result, expected, "Should support $divide expression")
