"""Smoke test for the $minMaxScaler window operator (new in 8.2): the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_minMaxScaler(collection):
    """Test the engine accepts $minMaxScaler as a window operator."""
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 2, "x": 3}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {"result": {"$minMaxScaler": {"input": "$x"}}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $minMaxScaler window operator")
