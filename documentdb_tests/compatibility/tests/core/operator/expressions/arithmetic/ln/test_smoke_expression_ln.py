"""
Smoke test for $ln expression.

Tests basic $ln expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_ln(collection):
    """Test basic $ln expression behavior."""
    collection.insert_many([{"_id": 1, "value": 1}, {"_id": 2, "value": 2.718281828459045}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"naturalLog": {"$ln": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "naturalLog": 0.0}, {"_id": 2, "naturalLog": 1.0}]
    assertSuccess(result, expected, msg="Should support $ln expression")
