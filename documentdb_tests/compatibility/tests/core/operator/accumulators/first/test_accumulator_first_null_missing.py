"""Tests for $first accumulator null, missing, input form, and edge case behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing NOT Excluded]: $first returns whatever the
# first document has, including null and missing values.
FIRST_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_first_then_value",
        docs=[{"v": None}, {"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first doc has null (first wins)",
    ),
    AccumulatorTestCase(
        "null_missing_first_then_value",
        docs=[{"x": 1}, {"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first doc has missing field",
    ),
    AccumulatorTestCase(
        "null_value_first_then_null",
        docs=[{"v": 5}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 5}],
        msg="$first should return 5 when first doc has value, second is null",
    ),
    AccumulatorTestCase(
        "null_value_first_then_missing",
        docs=[{"v": 5}, {"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 5}],
        msg="$first should return 5 when first doc has value, second is missing",
    ),
    AccumulatorTestCase(
        "null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when all docs have null",
    ),
    AccumulatorTestCase(
        "null_missing_all",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when all docs have missing field",
    ),
    AccumulatorTestCase(
        "null_and_missing_mixed",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first is null and second is missing",
    ),
    AccumulatorTestCase(
        "null_remove_first_then_value",
        docs=[{"v": -1}, {"v": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            }
        ],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first doc produces $$REMOVE",
    ),
    AccumulatorTestCase(
        "null_remove_all",
        docs=[{"v": -1}, {"v": -2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            }
        ],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when all docs produce $$REMOVE",
    ),
    AccumulatorTestCase(
        "null_remove_second_value_first",
        docs=[{"v": 5}, {"v": -1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            }
        ],
        expected=[{"_id": None, "result": 5}],
        msg="$first should return value when first doc has value, second $$REMOVE",
    ),
]

# Property [Input Forms]: $first accumulator accepts various expression types as its operand.
FIRST_INPUT_FORM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "input_nested_field",
        docs=[{"a": {"b": 10}}, {"a": {"b": 20}}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$a.b"}}}],
        expected=[{"_id": None, "result": 10}],
        msg="$first should accept a nested document field path",
    ),
    AccumulatorTestCase(
        "input_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": 42}}}],
        expected=[{"_id": None, "result": 42}],
        msg="$first with a literal constant should return that constant",
    ),
    AccumulatorTestCase(
        "input_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": None}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first with null literal should return null",
    ),
]

# Property [Edge Cases]: edge cases unique to the accumulator context.
FIRST_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_single_doc",
        docs=[{"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 42}],
        msg="$first of a single document should return that document's value",
    ),
    AccumulatorTestCase(
        "edge_single_null_doc",
        docs=[{"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first of a single null document should return null",
    ),
    AccumulatorTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first of a single document with missing field should return null",
    ),
    AccumulatorTestCase(
        "edge_many_docs",
        docs=[{"v": i} for i in range(100)],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 0}],
        msg="$first should return first document's value (v=0) across 100 documents",
    ),
    AccumulatorTestCase(
        "edge_empty_collection",
        docs=None,
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[],
        msg="$first on empty collection should return empty result",
    ),
    AccumulatorTestCase(
        "edge_array_not_traversed",
        docs=[{"v": [5, 1, 8]}, {"v": [3, 9, 2]}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": [5, 1, 8]}],
        msg="$first should return array as whole value, not traverse it",
    ),
]

FIRST_SUCCESS_TESTS = FIRST_NULL_MISSING_TESTS + FIRST_INPUT_FORM_TESTS + FIRST_EDGE_CASE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(FIRST_SUCCESS_TESTS))
def test_accumulator_first_null_missing(collection, test_case: AccumulatorTestCase):
    """Test $first accumulator null, missing, input form, and edge case behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
