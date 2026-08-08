"""
Behavior coverage for the $addToSet accumulator inside $group.

Oracle: MongoDB 7.0. The accumulator produces an array of distinct values per
group; tests use `ignore_order_in=["vals"]` (or similar) so that the
engine-agnostic contract is "same set of values," not "same array order".
"""

import pytest
from bson import Decimal128, ObjectId
from datetime import datetime, timezone

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
    engine="pgmongo",
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
    engine="pgmongo",
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


# ---------------------------------------------------------------------------
# Type-specific dedup
# ---------------------------------------------------------------------------


def test_accumulator_addToSet_dedups_objectid(collection):
    """Equal ObjectIds across documents collapse to a single element."""
    oid = ObjectId("64b5e4f0a1b2c3d4e5f60001")
    collection.insert_many(
        [
            {"_id": 1, "g": "A", "v": oid},
            {"_id": 2, "g": "A", "v": oid},
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
        [{"_id": "A", "vals": [oid]}],
        ignore_order_in=["vals"],
        msg="Equal ObjectIds must collapse to a single element",
    )


def test_accumulator_addToSet_dedups_date(collection):
    """Equal Date values across documents collapse to a single element."""
    d = datetime(2024, 1, 1, tzinfo=timezone.utc)
    collection.insert_many(
        [
            {"_id": 1, "g": "A", "v": d},
            {"_id": 2, "g": "A", "v": d},
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
        [{"_id": "A", "vals": [d]}],
        ignore_order_in=["vals"],
        msg="Equal Date values must collapse to a single element",
    )


# ---------------------------------------------------------------------------
# Literal and expression arguments
# ---------------------------------------------------------------------------


def test_accumulator_addToSet_literal_value_collapses_to_single_element(collection):
    """A literal scalar argument produces a single-element set regardless of input row count."""
    collection.insert_many(
        [{"_id": 1, "g": "A"}, {"_id": 2, "g": "A"}, {"_id": 3, "g": "A"}]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$g", "vals": {"$addToSet": "constant"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "vals": ["constant"]}],
        ignore_order_in=["vals"],
        msg="Literal-arg $addToSet must produce a single-element set",
    )


def test_accumulator_addToSet_dedups_after_expression_transform(collection):
    """The accumulator dedups on the expression result, not on the raw field."""
    collection.insert_many(
        [
            {"_id": 1, "g": "A", "v": "abc"},
            {"_id": 2, "g": "A", "v": "ABC"},
            {"_id": 3, "g": "A", "v": "aBc"},
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
                        "vals": {"$addToSet": {"$toUpper": "$v"}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "vals": ["ABC"]}],
        ignore_order_in=["vals"],
        msg="Equality is measured on the expression result, not the raw input",
    )


# ---------------------------------------------------------------------------
# Group key edge cases
# ---------------------------------------------------------------------------


def test_accumulator_addToSet_with_id_null_groups_all_documents(collection):
    """`_id: null` produces a single global group containing the union of values."""
    collection.insert_many(
        [{"_id": 1, "v": 1}, {"_id": 2, "v": 2}, {"_id": 3, "v": 1}]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": None, "vals": {"$addToSet": "$v"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": None, "vals": [1, 2]}],
        ignore_order_in=["vals"],
        msg="`_id: null` must group all documents into a single set",
    )


def test_accumulator_addToSet_treats_reordered_subdocument_keys_as_distinct(
    collection,
):
    """Subdocument elements with reordered keys are kept as distinct set elements."""
    collection.insert_many(
        [
            {"_id": 1, "g": "A", "doc": {"a": 1, "b": 2}},
            {"_id": 2, "g": "A", "doc": {"b": 2, "a": 1}},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$g", "vals": {"$addToSet": "$doc"}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [{"_id": "A", "vals": [{"a": 1, "b": 2}, {"b": 2, "a": 1}]}],
        ignore_order_in=["vals"],
        msg="Field ordering must matter for subdocument set equality",
    )


def test_accumulator_addToSet_empty_input_produces_no_groups(collection):
    """Aggregating an empty collection yields no group rows (not an empty set)."""
    # collection fixture is already empty; do not insert.
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$g", "vals": {"$addToSet": "$v"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [],
        msg="Empty input must yield zero group rows",
    )
