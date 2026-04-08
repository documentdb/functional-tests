"""
Smoke test for $toBool expression.

Tests basic $toBool expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toBool(collection):
    """Test basic $toBool expression behavior."""
    collection.insert_many([{"_id": 1, "value": 1}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"bool": {"$toBool": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "bool": True}]
    assertSuccess(result, expected, msg="Should support $toBool expression")
