"""
Smoke test for $literal expression.

Tests basic $literal expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_literal(collection):
    """Test basic $literal expression behavior."""
    collection.insert_many([{"_id": 1, "name": "test"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"literalValue": {"$literal": "$field"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "literalValue": "$field"}]
    assertSuccess(result, expected, msg="Should support $literal expression")
