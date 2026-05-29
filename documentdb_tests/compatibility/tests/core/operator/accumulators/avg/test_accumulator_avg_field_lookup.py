"""
Tests for $avg accumulator expression types and field lookup in $group context.

Covers expression types (literal, field path, computed expressions, conditional)
and field path resolution (simple, nested, missing, array traversal).
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Type]: $avg accepts field paths, computed expressions,
# literals, and conditional expressions in $group context.

AVG_EXPRESSION_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "field_path",
        docs=[
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$value"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="$avg with field path should average field values",
    ),
    AccumulatorTestCase(
        "computed_expression",
        docs=[
            {"_id": 1, "a": 2, "b": 3},
            {"_id": 2, "a": 4, "b": 6},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": {"$multiply": ["$a", "$b"]}}}}],
        # (2*3 + 4*6) / 2 = (6 + 24) / 2 = 15
        expected=[{"_id": None, "avg": 15.0}],
        msg="$avg with computed expression should average computed values",
    ),
    AccumulatorTestCase(
        "literal_numeric",
        docs=[
            {"_id": 1},
            {"_id": 2},
            {"_id": 3},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": 5}}}],
        expected=[{"_id": None, "avg": 5.0}],
        msg="$avg with literal numeric should return that constant",
    ),
    AccumulatorTestCase(
        "literal_null",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": None}}}],
        expected=[{"_id": None, "avg": None}],
        msg="$avg with null literal should return null",
    ),
    AccumulatorTestCase(
        "cond_expression",
        docs=[
            {"_id": 1, "value": 10, "include": True},
            {"_id": 2, "value": 20, "include": False},
            {"_id": 3, "value": 30, "include": True},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "avg": {
                        "$avg": {
                            "$cond": [
                                "$include",
                                "$value",
                                None,
                            ]
                        }
                    },
                }
            },
        ],
        # Only values 10 and 30 contribute (null is ignored), avg = 20
        expected=[{"_id": None, "avg": 20.0}],
        msg="$avg with $cond should average only non-null conditional results",
    ),
    AccumulatorTestCase(
        "ifnull_expression",
        docs=[
            {"_id": 1, "value": 10},
            {"_id": 2},
            {"_id": 3, "value": 30},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "avg": {"$avg": {"$ifNull": ["$value", 0]}},
                }
            },
        ],
        # (10 + 0 + 30) / 3 = 13.333...
        expected=[{"_id": None, "avg": 13.333333333333334}],
        msg="$avg with $ifNull should replace missing with 0",
    ),
]

# Property [Field Resolution]: field path resolution behaviors with $avg in $group context.

AVG_FIELD_RESOLUTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nested_field_path",
        docs=[
            {"_id": 1, "nested": {"value": 10}},
            {"_id": 2, "nested": {"value": 20}},
            {"_id": 3, "nested": {"value": 30}},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$nested.value"}}}],
        expected=[{"_id": None, "avg": 20.0}],
        msg="$avg with nested field path should resolve and average",
    ),
    AccumulatorTestCase(
        "missing_field",
        docs=[
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$nonexistent"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="$avg with non-existent field should return null",
    ),
    AccumulatorTestCase(
        "field_resolves_to_array",
        docs=[
            {"_id": 1, "value": [1, 2, 3]},
            {"_id": 2, "value": [4, 5, 6]},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$value"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="$avg in $group should treat array values as non-numeric",
    ),
    AccumulatorTestCase(
        "mixed_array_and_numeric",
        docs=[
            {"_id": 1, "value": [1, 2, 3]},
            {"_id": 2, "value": 10},
            {"_id": 3, "value": 20},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$value"}}}],
        # Array is ignored: (10 + 20) / 2 = 15
        expected=[{"_id": None, "avg": 15.0}],
        msg="$avg in $group should ignore array values and average numerics",
    ),
    AccumulatorTestCase(
        "deeply_nested_path",
        docs=[
            {"_id": 1, "a": {"b": {"c": {"d": 10}}}},
            {"_id": 2, "a": {"b": {"c": {"d": 20}}}},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$a.b.c.d"}}}],
        expected=[{"_id": None, "avg": 15.0}],
        msg="$avg with deeply nested path should resolve correctly",
    ),
    AccumulatorTestCase(
        "intermediate_null",
        docs=[
            {"_id": 1, "a": {"b": 10}},
            {"_id": 2, "a": None},
            {"_id": 3, "a": {"b": 30}},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$a.b"}}}],
        # Doc 2 has null intermediate, treated as missing: (10 + 30) / 2 = 20
        expected=[{"_id": None, "avg": 20.0}],
        msg="$avg should treat null intermediate as missing",
    ),
    AccumulatorTestCase(
        "multiple_accumulators",
        docs=[
            {"_id": 1, "a": 10, "b": 100},
            {"_id": 2, "a": 20, "b": 200},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "avg_a": {"$avg": "$a"},
                    "avg_b": {"$avg": "$b"},
                }
            },
        ],
        expected=[{"_id": None, "avg_a": 15.0, "avg_b": 150.0}],
        msg="Multiple $avg accumulators should work independently",
    ),
]

AVG_FIELD_LOOKUP_TESTS: list[AccumulatorTestCase] = (
    AVG_EXPRESSION_TYPE_TESTS + AVG_FIELD_RESOLUTION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(AVG_FIELD_LOOKUP_TESTS))
def test_accumulator_avg_field_lookup(collection, test_case: AccumulatorTestCase):
    """Test $avg field lookup and expression types in $group context."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
