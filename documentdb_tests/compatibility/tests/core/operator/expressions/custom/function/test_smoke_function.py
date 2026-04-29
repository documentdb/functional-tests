"""
Smoke test for $function custom expression.

Tests basic $function custom expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_function(collection):
    """Test basic $function custom expression behavior."""
    collection.insert_many([{"_id": 1, "value": 5.0}, {"_id": 2, "value": 10.0}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "doubled": {
                            "$function": {
                                "body": "function(x) { return x * 2; }",
                                "args": ["$value"],
                                "lang": "js",
                            }
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "doubled": 10.0}, {"_id": 2, "doubled": 20.0}]
    assertSuccess(result, expected, msg="Should support $function custom expression")
