"""Tests for $max accumulator null/missing handling, input forms, and edge cases."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ===========================================================================
# 1. Null and Missing Handling
# ===========================================================================

# Property [Null and Missing Ignored]: null values, missing fields, and
# $$REMOVE are excluded from the max computation. When no non-null/non-missing
# values remain, the result is null.
MAX_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_all_null",
        docs=[{"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max should return null when all values are null",
    ),
    AccumulatorTestCase(
        "null_all_missing",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max should return null when all values reference missing fields",
    ),
    AccumulatorTestCase(
        "null_and_missing_all",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max should return null when values are mix of null and missing",
    ),
    AccumulatorTestCase(
        "null_single_among_values",
        docs=[{"v": None}, {"v": 5}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should exclude null and return max of remaining numerics",
    ),
    AccumulatorTestCase(
        "null_missing_single_among_values",
        docs=[{"x": 1}, {"v": 5}, {"v": 3}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should exclude missing and return max of remaining numerics",
    ),
    AccumulatorTestCase(
        "null_and_missing_among_values",
        docs=[{"v": None}, {"x": 1}, {"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 10}],
        msg="$max should exclude both null and missing, return max of numerics",
    ),
    AccumulatorTestCase(
        "null_one_value",
        docs=[{"v": None}, {"x": 1}, {"v": 7}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 7}],
        msg="$max should return the only numeric value when others are null/missing",
    ),
    AccumulatorTestCase(
        "null_two_docs",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max should return null when one doc is null and one is missing",
    ),
    AccumulatorTestCase(
        "null_remove_via_cond",
        docs=[{"v": -1}, {"v": 5}, {"v": 3}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$max": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should treat $$REMOVE as missing and exclude it",
    ),
    AccumulatorTestCase(
        "null_remove_all",
        docs=[{"v": -1}, {"v": -2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$max": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max should return null when all docs produce $$REMOVE",
    ),
    AccumulatorTestCase(
        "null_remove_with_values",
        docs=[{"v": -1}, {"v": 10}, {"v": -3}, {"v": 7}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$max": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 10}],
        msg="$max should return max of remaining values after $$REMOVE exclusion",
    ),
]


# ===========================================================================
# 2. Expression Argument Tests
# ===========================================================================

# Property [Input Forms]: $max accumulator accepts various expression types
# as its operand.
MAX_INPUT_FORM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "input_field_path",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 20}],
        msg="$max should accept a basic field path reference",
    ),
    AccumulatorTestCase(
        "input_nested_field",
        docs=[{"a": {"b": 10}}, {"a": {"b": 20}}, {"a": {"b": 5}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$a.b"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 20}],
        msg="$max should accept a nested document field path",
    ),
    AccumulatorTestCase(
        "input_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": 42}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 42}],
        msg="$max with a literal constant should return that constant",
    ),
    AccumulatorTestCase(
        "input_expression",
        docs=[{"price": 10, "qty": 2}, {"price": 5, "qty": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"$multiply": ["$price", "$qty"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 50}],
        msg="$max should accept a computed expression as operand",
    ),
    AccumulatorTestCase(
        "input_cond_remove",
        docs=[{"v": -1}, {"v": 5}, {"v": 3}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$max": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$max should accept conditional with $$REMOVE as operand",
    ),
    AccumulatorTestCase(
        "input_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": None}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max with null literal should return null (all docs produce null)",
    ),
]


# ===========================================================================
# 3. Accumulator-Specific Edge Cases
# ===========================================================================

# Property [Edge Cases]: edge cases unique to accumulator context.
MAX_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_single_doc",
        docs=[{"v": 42}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 42}],
        msg="$max of a single document should return that document's value",
    ),
    AccumulatorTestCase(
        "edge_single_null_doc",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max of a single null document should return null",
    ),
    AccumulatorTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$max of a single document with missing field should return null",
    ),
    AccumulatorTestCase(
        "edge_multi_group",
        docs=[
            {"g": "A", "v": 10},
            {"g": "A", "v": 20},
            {"g": "B", "v": 5},
            {"g": "B", "v": 15},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 20}],
        msg="$max should compute correctly across documents (single group via $literal)",
    ),
    AccumulatorTestCase(
        "edge_many_docs",
        docs=[{"v": i} for i in range(100)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 99}],
        msg="$max should return correct value across 100 documents",
    ),
    AccumulatorTestCase(
        "edge_array_field_not_traversed",
        docs=[{"v": [5, 1, 8]}, {"v": [3, 9, 2]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [5, 1, 8]}],
        msg="$max should compare arrays as whole values, not traverse them",
    ),
    AccumulatorTestCase(
        "edge_mixed_array_scalar",
        docs=[{"v": [1, 2, 3]}, {"v": 5}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$max should pick array over scalar (array > number in BSON order)",
    ),
]


# ===========================================================================
# Combined success tests and test function
# ===========================================================================

MAX_NULL_MISSING_SUCCESS_TESTS = MAX_NULL_MISSING_TESTS + MAX_INPUT_FORM_TESTS + MAX_EDGE_CASE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MAX_NULL_MISSING_SUCCESS_TESTS))
def test_accumulator_max_null_missing(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator null/missing, input forms, and edge cases via $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
