"""
Smoke test for $toDecimal expression.

Tests basic $toDecimal expression functionality.
"""

import pytest
from bson import Decimal128

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toDecimal(collection):
    """Test basic $toDecimal expression behavior."""
    collection.insert_many([{"_id": 1, "value": 123}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"decimal": {"$toDecimal": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "decimal": Decimal128("123")}]
    assertSuccess(result, expected, msg="Should support $toDecimal expression")
