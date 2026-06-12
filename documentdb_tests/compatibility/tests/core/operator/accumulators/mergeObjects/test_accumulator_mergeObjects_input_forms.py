"""Tests for $mergeObjects accumulator: expression types, field lookup, and constant objects."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Types]: $mergeObjects accepts various expression types
# as its operand and evaluates them per document.
MERGE_OBJECTS_EXPRESSION_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_type_nested_field_path",
        docs=[
            {"s": 1, "data": {"inner": {"a": 1}}},
            {"s": 2, "data": {"inner": {"b": 2}}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$data.inner"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should accept a nested field path",
    ),
    AccumulatorTestCase(
        "expr_type_literal",
        docs=[{"s": 1, "x": 1}, {"s": 2, "x": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": {"$literal": {"a": 1}}}}},
        ],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should accept a $literal expression",
    ),
    AccumulatorTestCase(
        "expr_type_sysvar_remove",
        docs=[{"s": 1, "x": 1}, {"s": 2, "x": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$$REMOVE"}}},
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should accept $$REMOVE and return empty document",
    ),
    AccumulatorTestCase(
        "expr_type_sysvar_root",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$$ROOT"}}},
        ],
        expected=[{"_id": None, "result": {"_id": 2, "x": 2}}],
        msg="$mergeObjects should accept $$ROOT system variable",
    ),
    AccumulatorTestCase(
        "expr_type_sysvar_current",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$$CURRENT"}}},
        ],
        expected=[{"_id": None, "result": {"_id": 2, "x": 2}}],
        msg="$mergeObjects should accept $$CURRENT system variable",
    ),
    AccumulatorTestCase(
        "expr_type_ifnull",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": {"b": 2}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$mergeObjects": {"$ifNull": ["$v", {}]}},
                }
            },
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should accept $ifNull as its operand expression",
    ),
    AccumulatorTestCase(
        "expr_type_cond",
        docs=[
            {"s": 1, "v": {"a": 1}, "flag": True},
            {"s": 2, "v": {"b": 2}, "flag": True},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$mergeObjects": {"$cond": ["$flag", "$v", {"z": 0}]}},
                }
            },
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should accept a $cond expression",
    ),
    AccumulatorTestCase(
        "expr_type_object_with_field_ref",
        docs=[{"s": 1, "v": 1}, {"s": 2, "v": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": {"a": "$v"}}}},
        ],
        expected=[{"_id": None, "result": {"a": 2}}],
        msg="$mergeObjects should accept object expression with field reference, last wins",
    ),
    AccumulatorTestCase(
        "expr_type_object_with_operator",
        docs=[{"s": 1, "v": -5}, {"s": 2, "v": -10}],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$mergeObjects": {"a": {"$abs": "$v"}}},
                }
            },
        ],
        expected=[{"_id": None, "result": {"a": 10}}],
        msg="$mergeObjects should accept object expression with operator, last wins",
    ),
    AccumulatorTestCase(
        "expr_type_let",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": {"b": 2}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$mergeObjects": {"$let": {"vars": {"x": "$v"}, "in": "$$x"}}},
                }
            },
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should accept a $let expression as its operand",
    ),
]

# Property [Field Lookup]: $mergeObjects resolves field paths including nested
# object paths and array index paths.
MERGE_OBJECTS_FIELD_LOOKUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "field_lookup_numeric_key_path",
        docs=[
            {"s": 1, "v": {"0": {"b": {"x": 1}}}},
            {"s": 2, "v": {"0": {"b": {"y": 2}}}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v.0.b"}}},
        ],
        expected=[{"_id": None, "result": {"x": 1, "y": 2}}],
        msg="$mergeObjects should traverse numeric string key as object field name",
    ),
    AccumulatorTestCase(
        "field_lookup_nested_object_path",
        docs=[
            {"s": 1, "data": {"inner": {"obj": {"x": 1}}}},
            {"s": 2, "data": {"inner": {"obj": {"y": 2}}}},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$data.inner.obj"}}},
        ],
        expected=[{"_id": None, "result": {"x": 1, "y": 2}}],
        msg="$mergeObjects should resolve deeply nested object field path",
    ),
    AccumulatorTestCase(
        "field_lookup_nonexistent_returns_empty",
        docs=[{"s": 1, "v": {"a": 1}}, {"s": 2, "v": {"b": 2}}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": "$nonexistent"}}},
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should treat nonexistent field path as missing",
    ),
]

# Property [Constant Object Expression]: a constant object expression (no
# field references or operators) is accepted and returned unchanged.
MERGE_OBJECTS_CONSTANT_OBJECT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "constant_object_returned",
        docs=[{"s": 1, "x": 1}, {"s": 2, "x": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": {"a": 1, "b": 2}}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should accept constant object and return it",
    ),
    AccumulatorTestCase(
        "constant_empty_object_returned",
        docs=[{"s": 1, "x": 1}, {"s": 2, "x": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$mergeObjects": {}}}},
        ],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should accept constant empty object and return empty document",
    ),
    AccumulatorTestCase(
        "constant_object_multi_group",
        docs=[
            {"s": 1, "cat": "A", "x": 1},
            {"s": 2, "cat": "A", "x": 2},
            {"s": 3, "cat": "B", "x": 3},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": "$cat", "result": {"$mergeObjects": {"val": "$x"}}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": {"val": 2}},
            {"_id": "B", "result": {"val": 3}},
        ],
        msg="$mergeObjects with object expression should merge independently per group",
    ),
]

MERGE_OBJECTS_INPUT_FORM_TESTS = (
    MERGE_OBJECTS_EXPRESSION_TYPE_TESTS
    + MERGE_OBJECTS_FIELD_LOOKUP_TESTS
    + MERGE_OBJECTS_CONSTANT_OBJECT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MERGE_OBJECTS_INPUT_FORM_TESTS))
def test_accumulator_mergeObjects_input_forms(collection, test_case: AccumulatorTestCase):
    """Test $mergeObjects expression types, field lookup, and constant objects."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
    actual_docs = result["cursor"]["firstBatch"]
    for actual, exp in zip(actual_docs, test_case.expected):
        if "result" in exp and isinstance(exp["result"], dict):
            actual_keys = list(actual["result"].keys())
            expected_keys = list(exp["result"].keys())
            if actual_keys != expected_keys:
                raise AssertionError(
                    f"[KEY_ORDER_MISMATCH] {test_case.msg}\n"
                    f"Expected key order: {expected_keys}\n"
                    f"Actual key order:   {actual_keys}"
                )
