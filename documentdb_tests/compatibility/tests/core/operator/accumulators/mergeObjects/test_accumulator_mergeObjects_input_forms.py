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
        docs=[{"data": {"inner": {"a": 1}}}, {"data": {"inner": {"b": 2}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$mergeObjects": "$data.inner"}}},
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should accept a nested field path",
    ),
    AccumulatorTestCase(
        "expr_type_literal",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": {"$literal": {"a": 1}}}}}],
        expected=[{"_id": None, "result": {"a": 1}}],
        msg="$mergeObjects should accept a $literal expression",
    ),
    AccumulatorTestCase(
        "expr_type_sysvar_remove",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[
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
        docs=[{"v": {"a": 1}}, {"v": {"b": 2}}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$mergeObjects": {"$ifNull": ["$v", {}]}},
                }
            }
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should accept $ifNull as its operand expression",
    ),
    AccumulatorTestCase(
        "expr_type_cond",
        docs=[{"v": {"a": 1}, "flag": True}, {"v": {"b": 2}, "flag": True}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$mergeObjects": {"$cond": ["$flag", "$v", {"z": 0}]}},
                }
            }
        ],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should accept a $cond expression",
    ),
    AccumulatorTestCase(
        "expr_type_object_with_field_ref",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$mergeObjects": {"a": "$v"}}}},
        ],
        expected=[{"_id": None, "result": {"a": 2}}],
        msg="$mergeObjects should accept object expression with field reference, last wins",
    ),
    AccumulatorTestCase(
        "expr_type_object_with_operator",
        docs=[{"v": -5}, {"v": -10}],
        pipeline=[
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
        docs=[{"v": {"a": 1}}, {"v": {"b": 2}}],
        pipeline=[
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
            {"v": {"0": {"b": {"x": 1}}}},
            {"v": {"0": {"b": {"y": 2}}}},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$mergeObjects": "$v.0.b"}}},
        ],
        expected=[{"_id": None, "result": {"x": 1, "y": 2}}],
        msg="$mergeObjects should traverse numeric string key as object field name",
    ),
    AccumulatorTestCase(
        "field_lookup_nonexistent_returns_empty",
        docs=[{"v": {"a": 1}}, {"v": {"b": 2}}],
        pipeline=[
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
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": {"a": 1, "b": 2}}}}],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$mergeObjects should accept constant object and return it",
    ),
    AccumulatorTestCase(
        "constant_empty_object_returned",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$mergeObjects": {}}}}],
        expected=[{"_id": None, "result": {}}],
        msg="$mergeObjects should accept constant empty object and return empty document",
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
