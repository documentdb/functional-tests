"""
Smoke test for $covarianceSamp window operator.

Tests basic $covarianceSamp window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_covarianceSamp(collection):
    """Test basic $covarianceSamp window operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "partition": "A", "x": 1, "y": 2},
            {"_id": 2, "partition": "A", "x": 2, "y": 4},
            {"_id": 3, "partition": "A", "x": 3, "y": 6},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {"covariance": {"$covarianceSamp": ["$x", "$y"]}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "covariance": 2.0},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "covariance": 2.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "covariance": 2.0},
    ]
    assertSuccess(result, expected, msg="Should support $covarianceSamp window operator")
