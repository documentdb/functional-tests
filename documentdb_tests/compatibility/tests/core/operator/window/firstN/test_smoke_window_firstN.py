"""Smoke test for the $firstN window operator: the engine accepts it in $setWindowFields."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_firstN(collection):
    """Test the engine accepts $firstN as a window operator."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 3}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$firstN": {"input": "$x", "n": 2},
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $firstN window operator")
