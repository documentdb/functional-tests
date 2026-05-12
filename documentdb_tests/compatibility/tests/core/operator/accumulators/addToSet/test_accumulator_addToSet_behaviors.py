"""
Behavior coverage for the $addToSet accumulator inside $group.

Oracle: MongoDB 7.0. The accumulator produces an array of distinct values per
group; tests use `ignore_order_in=["vals"]` (or similar) so that the
engine-agnostic contract is "same set of values," not "same array order".
"""

import pytest
from bson import Decimal128

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.aggregate


# ---------------------------------------------------------------------------
# Dedup semantics across types
# ---------------------------------------------------------------------------


def test_accumulator_addToSet_does_not_dedup_string_and_number(collection):
    """A string value and a numerically-equal number are kept as distinct elements."""
    collection.insert_many(
        [
            {"_id": 1, "g": "A", "v": 1},
            {"_id": 2, "g": "A", "v": "1"},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$g", "vals": {"$addToSet": "$v"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "vals": [1, "1"]}],
        ignore_order_in=["vals"],
        msg="String '1' and int 1 are distinct values",
    )


def test_accumulator_addToSet_dedups_int_and_double_numerically_equal(collection):
    """Int 1 and Double 1.0 collapse to a single element."""
    collection.insert_many(
        [
            {"_id": 1, "g": "A", "v": 1},
            {"_id": 2, "g": "A", "v": 1.0},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$g", "vals": {"$addToSet": "$v"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    # Whichever document is consumed first wins the BSON type of the
    # surviving element; the documented contract is set-equality only.
    assertSuccess(
        result,
        [{"_id": "A", "vals": [1]}],
        ignore_order_in=["vals"],
        msg="Int 1 and Double 1.0 are the same set element",
    )


def test_accumulator_addToSet_dedups_decimal128_independent_of_trailing_zeros(
    collection,
):
    """Decimal128('1.0') and Decimal128('1.00') collapse to a single element."""
    collection.insert_many(
        [
            {"_id": 1, "g": "A", "v": Decimal128("1.0")},
            {"_id": 2, "g": "A", "v": Decimal128("1.00")},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$g", "vals": {"$addToSet": "$v"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "vals": [Decimal128("1.0")]}],
        ignore_order_in=["vals"],
        msg="Decimal128 dedup must ignore trailing-zero representation",
    )


def test_accumulator_addToSet_dedups_null_values(collection):
    """Multiple null-valued documents collapse to one null in the output set."""
    collection.insert_many(
        [
            {"_id": 1, "g": "A", "v": None},
            {"_id": 2, "g": "A", "v": None},
            {"_id": 3, "g": "A", "v": 1},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$g", "vals": {"$addToSet": "$v"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "vals": [None, 1]}],
        ignore_order_in=["vals"],
        msg="Null appears at most once in the output set",
    )


def test_accumulator_addToSet_dedups_subdocuments_by_deep_equality(collection):
    """Equal subdocuments collapse to one element."""
    collection.insert_many(
        [
            {"_id": 1, "g": "A", "x": 1, "y": 2},
            {"_id": 2, "g": "A", "x": 1, "y": 2},
            {"_id": 3, "g": "A", "x": 3, "y": 4},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": "$g",
                        "pairs": {"$addToSet": {"x": "$x", "y": "$y"}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "pairs": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}],
        ignore_order_in=["pairs"],
        msg="Equal subdocuments must be deduplicated",
    )


# ---------------------------------------------------------------------------
# Missing-field semantics (known divergence)
# ---------------------------------------------------------------------------


@pytest.mark.engine_xfail(
    engine="documentdb",
    reason=(
        "$addToSet accumulator on a missing field: native MongoDB skips the "
        "document; documentdb includes a null. Tracked divergence."
    ),
    raises=AssertionError,
)
def test_accumulator_addToSet_skips_documents_missing_field(collection):
    """Documents that don't have the source field must be skipped, not included as null."""
    collection.insert_many(
        [
            {"_id": 1, "g": "A"},          # no `v` — must be skipped
            {"_id": 2, "g": "A", "v": 1},
            {"_id": 3, "g": "A", "v": 2},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$g", "vals": {"$addToSet": "$v"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "vals": [1, 2]}],
        ignore_order_in=["vals"],
        msg="Missing-field documents must be skipped by $addToSet",
    )


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


@pytest.mark.engine_xfail(
    engine="documentdb",
    reason=(
        "$addToSet is a unary accumulator and must reject array-shaped "
        "arguments with code 40237; documentdb accepts the array as a "
        "literal value. Tracked divergence."
    ),
    raises=AssertionError,
)
def test_accumulator_addToSet_rejects_multi_arg_array(collection):
    """Passing an array literal as the accumulator argument must fail with 40237."""
    collection.insert_one({"_id": 1, "x": 1, "y": 2})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$group": {
                        "_id": None,
                        "v": {"$addToSet": ["$x", "$y"]},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertFailureCode(
        result,
        40237,
        msg="$addToSet must reject multi-argument array form (40237)",
    )
