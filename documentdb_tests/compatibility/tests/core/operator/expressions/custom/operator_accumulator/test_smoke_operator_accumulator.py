"""
Smoke test for $accumulator custom expression.

Tests basic $accumulator custom expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_operator_accumulator(collection):
    """Test basic $accumulator custom expression behavior."""
    collection.insert_many(
        [{"_id": 1, "category": "A", "value": 5.0}, {"_id": 2, "category": "A", "value": 10.0}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": "$category",
                        "total": {
                            "$accumulator": {
                                "init": "function() { return 0; }",
                                "accumulate": "function(state, value) { return state + value; }",
                                "accumulateArgs": ["$value"],
                                "merge": "function(state1, state2) { return state1 + state2; }",
                                "lang": "js",
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "total": 15.0}]
    assertSuccess(result, expected, msg="Should support $accumulator custom expression")
