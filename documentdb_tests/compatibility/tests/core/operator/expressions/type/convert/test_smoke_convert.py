"""
Smoke test for $convert expression.

Tests basic $convert expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_convert(collection):
    """Test basic $convert expression behavior."""
    collection.insert_many([{"_id": 1, "value": "123"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"converted": {"$convert": {"input": "$value", "to": "int"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "converted": 123}]
    assertSuccess(result, expected, msg="Should support $convert expression")
