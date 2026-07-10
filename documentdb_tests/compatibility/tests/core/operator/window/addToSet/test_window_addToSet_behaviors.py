"""
Behavior coverage for the $addToSet window operator inside $setWindowFields.

Oracle: MongoDB 7.0. The accumulator returns the set of distinct values seen
inside the window; tests assert set equality (not array order) for engine
agnosticism.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.aggregate


def test_window_addToSet_bounded_documents_window(collection):
    """Sliding [-1, 0] window yields the distinct values from current + prior doc."""
    collection.insert_many(
        [
            {"_id": 1, "t": 1, "v": 10},
            {"_id": 2, "t": 2, "v": 20},
            {"_id": 3, "t": 3, "v": 10},
            {"_id": 4, "t": 4, "v": 30},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"t": 1},
                        "output": {
                            "unique": {
                                "$addToSet": "$v",
                                "window": {"documents": [-1, 0]},
                            }
                        },
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "t": 1, "v": 10, "unique": [10]},
            {"_id": 2, "t": 2, "v": 20, "unique": [10, 20]},
            {"_id": 3, "t": 3, "v": 10, "unique": [10, 20]},
            {"_id": 4, "t": 4, "v": 30, "unique": [10, 30]},
        ],
        ignore_order_in=["unique"],
        msg="Bounded window $addToSet must yield distinct values per window",
    )


def test_window_addToSet_partitionBy_resets_per_partition(collection):
    """partitionBy restricts the window to documents within the same partition."""
    collection.insert_many(
        [
            {"_id": 1, "p": "x", "v": 1},
            {"_id": 2, "p": "x", "v": 1},
            {"_id": 3, "p": "y", "v": 1},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$p",
                        "sortBy": {"_id": 1},
                        "output": {"unique": {"$addToSet": "$v"}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "p": "x", "v": 1, "unique": [1]},
            {"_id": 2, "p": "x", "v": 1, "unique": [1]},
            {"_id": 3, "p": "y", "v": 1, "unique": [1]},
        ],
        ignore_order_in=["unique"],
        msg="Each partition computes its own set independently",
    )
