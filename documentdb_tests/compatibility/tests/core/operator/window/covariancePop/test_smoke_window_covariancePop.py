"""
Smoke test for $covariancePop window operator.

Tests basic $covariancePop window operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_window_covariancePop(collection):
    """Test basic $covariancePop window operator behavior."""
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
                        "output": {"covariance": {"$covariancePop": ["$x", "$y"]}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "covariance": 1.3333333333333333},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "covariance": 1.3333333333333333},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "covariance": 1.3333333333333333},
    ]
    assertSuccess(result, expected, msg="Should support $covariancePop window operator")
