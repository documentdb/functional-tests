"""
Behavior coverage for the $addToSet window operator inside $setWindowFields.

Oracle: MongoDB 7.0. The accumulator returns the set of distinct values seen
inside the window; tests assert set equality (not array order) for engine
agnosticism.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
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


# ---------------------------------------------------------------------------
# Window-bounds variants
# ---------------------------------------------------------------------------


def test_window_addToSet_unbounded_window_collects_full_partition(collection):
    """An unbounded window yields the union of all values in the partition for every row."""
    collection.insert_many(
        [
            {"_id": 1, "t": 1, "v": 10},
            {"_id": 2, "t": 2, "v": 20},
            {"_id": 3, "t": 3, "v": 10},
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
                            "all_unique": {
                                "$addToSet": "$v",
                                "window": {"documents": ["unbounded", "unbounded"]},
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
            {"_id": 1, "t": 1, "v": 10, "all_unique": [10, 20]},
            {"_id": 2, "t": 2, "v": 20, "all_unique": [10, 20]},
            {"_id": 3, "t": 3, "v": 10, "all_unique": [10, 20]},
        ],
        ignore_order_in=["all_unique"],
        msg="Unbounded window must include the full partition for every row",
    )


def test_window_addToSet_self_only_window_yields_single_element(collection):
    """`documents: [0, 0]` yields a single-element set per row (the row's own value)."""
    collection.insert_many(
        [{"_id": 1, "v": 10}, {"_id": 2, "v": 20}]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "self": {
                                "$addToSet": "$v",
                                "window": {"documents": [0, 0]},
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
            {"_id": 1, "v": 10, "self": [10]},
            {"_id": 2, "v": 20, "self": [20]},
        ],
        ignore_order_in=["self"],
        msg="`documents: [0, 0]` must contain only the current row's value",
    )


def test_window_addToSet_range_based_window(collection):
    """A range-based window includes documents whose sort-key value is within [-1, 1]."""
    collection.insert_many(
        [
            {"_id": 1, "t": 0, "v": 10},
            {"_id": 2, "t": 1, "v": 20},
            {"_id": 3, "t": 5, "v": 30},
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
                            "in_range": {
                                "$addToSet": "$v",
                                "window": {"range": [-1, 1]},
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
            {"_id": 1, "t": 0, "v": 10, "in_range": [10, 20]},
            {"_id": 2, "t": 1, "v": 20, "in_range": [10, 20]},
            {"_id": 3, "t": 5, "v": 30, "in_range": [30]},
        ],
        ignore_order_in=["in_range"],
        msg="Range-based window must include rows whose sort-key value is within bounds",
    )


# ---------------------------------------------------------------------------
# Shared-error cases (must fail with the same code on native and on documentdb)
# ---------------------------------------------------------------------------


def test_window_addToSet_errors_when_documents_and_unit_both_set(collection):
    """Window bounds combining `documents` and `unit` must fail with FailedToParse (9)."""
    collection.insert_one({"_id": 1, "t": 0, "v": 10})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"t": 1},
                        "output": {
                            "bad": {
                                "$addToSet": "$v",
                                "window": {
                                    "documents": [-1, 0],
                                    "unit": "second",
                                },
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        9,
        msg="`documents` and `unit` set together must fail with FailedToParse (9)",
    )


def test_window_addToSet_errors_when_no_sortBy_for_documents_window(collection):
    """A document-based window without sortBy must fail with code 5339901."""
    collection.insert_one({"_id": 1, "v": 10})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "output": {
                            "bad": {
                                "$addToSet": "$v",
                                "window": {"documents": [-1, 0]},
                            }
                        }
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        5339901,
        msg="Document-based window without sortBy must fail with code 5339901",
    )
