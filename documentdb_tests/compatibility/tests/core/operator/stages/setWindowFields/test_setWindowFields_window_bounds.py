"""
Validates $setWindowFields frame (window-bounds) semantics using $addToSet as a
representative window operator. Frame semantics are assumed spec-consistent
across all window operators, so they are not re-tested per operator.

Covers bounded/unbounded document windows, self-only windows, range-based
windows, per-partition resets, and the shared window-bounds error cases.

Oracle: MongoDB 8.2.4 (functional-tests CI baseline). $addToSet returns the set
of distinct values seen inside the window; tests assert set equality (not array
order) for engine agnosticism.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.aggregate


def test_setWindowFields_bounded_documents_window(collection):
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
        msg="Bounded window must yield distinct values per window",
    )


def test_setWindowFields_partitionBy_resets_per_partition(collection):
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
        msg="Each partition computes its own window independently",
    )


def test_setWindowFields_unbounded_window_collects_full_partition(collection):
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


def test_setWindowFields_self_only_window_yields_single_element(collection):
    """`documents: [0, 0]` yields a single-element window per row (the row's own value)."""
    collection.insert_many([{"_id": 1, "v": 10}, {"_id": 2, "v": 20}])
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


def test_setWindowFields_range_based_window(collection):
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


def test_setWindowFields_errors_when_documents_and_unit_both_set(collection):
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
        FAILED_TO_PARSE_ERROR,
        msg="`documents` and `unit` set together must fail with FailedToParse (9)",
    )


def test_setWindowFields_errors_when_no_sortBy_for_documents_window(collection):
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
