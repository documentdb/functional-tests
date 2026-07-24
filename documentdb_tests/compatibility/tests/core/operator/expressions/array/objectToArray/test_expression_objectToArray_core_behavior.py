"""
Core behavior tests for $objectToArray expression.

Tests conversion of objects to k/v arrays, empty and null objects, special
key names, non-recursive behavior, field order preservation (including
stability across a prior $addFields stage), case sensitivity, and null value
handling.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.lazy_payload import materialize
from documentdb_tests.framework.parametrize import pytest_params

# Property [Literal-path parity]: representative cases from each group below
# also run through the literal-value path (not just via inserted documents).
# Defined here directly (not by positional index into the groups below) so the
# mapping is name-stable, and appended to ALL_TESTS below so they also get
# insert coverage.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="single_field",
        doc={"obj": {"a": 1}},
        expected=[{"k": "a", "v": 1}],
        msg="Should convert single-field object",
    ),
    ExpressionTestCase(
        id="mixed_value_types",
        doc={"obj": {"int": 1, "str": "hello", "bool": True, "null": None}},
        expected=[
            {"k": "int", "v": 1},
            {"k": "str", "v": "hello"},
            {"k": "bool", "v": True},
            {"k": "null", "v": None},
        ],
        msg="Should convert object with mixed value types",
    ),
    ExpressionTestCase(
        id="empty_object",
        doc={"obj": {}},
        expected=[],
        msg="Should return empty array for empty object",
    ),
    ExpressionTestCase(
        id="null_object",
        doc={"obj": None},
        expected=None,
        msg="Should return null for null object",
    ),
    ExpressionTestCase(
        id="deeply_nested_not_recursive",
        doc={"obj": {"a": {"b": {"c": {"d": 1}}}}},
        expected=[{"k": "a", "v": {"b": {"c": {"d": 1}}}}],
        msg="Should NOT recursively decompose nested docs",
    ),
    ExpressionTestCase(
        id="case_sensitive_keys",
        doc={"obj": {"a": 1, "A": 2}},
        expected=[{"k": "a", "v": 1}, {"k": "A", "v": 2}],
        msg="Case-different keys should be distinct",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_objectToArray_literal(collection, test):
    """Test $objectToArray with literal values."""
    result = execute_expression(collection, {"$objectToArray": test.doc["obj"]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Basic conversion]: a plain object converts to an array of {k, v}
# pairs, preserving each field's value type (string, nested object, array).
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="multiple_fields",
        doc={"obj": {"a": 1, "b": 2, "c": 3}},
        expected=[{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "c", "v": 3}],
        msg="Should convert multi-field object",
    ),
    ExpressionTestCase(
        id="string_values",
        doc={"obj": {"name": "Alice", "city": "Mycity"}},
        expected=[{"k": "name", "v": "Alice"}, {"k": "city", "v": "Mycity"}],
        msg="Should convert object with string values",
    ),
    ExpressionTestCase(
        id="nested_object_value",
        doc={"obj": {"obj": {"x": 1, "y": 2}}},
        expected=[{"k": "obj", "v": {"x": 1, "y": 2}}],
        msg="Should convert object with nested object value",
    ),
    ExpressionTestCase(
        id="array_value",
        doc={"obj": {"arr": [1, 2, 3]}},
        expected=[{"k": "arr", "v": [1, 2, 3]}],
        msg="Should convert object with array value",
    ),
    ExpressionTestCase(
        id="empty_array_value",
        doc={"obj": {"a": []}},
        expected=[{"k": "a", "v": []}],
        msg="Should convert object with an empty-array value",
    ),
]

# Property [Key preservation]: every key shape (empty, dotted, unicode,
# dollar-prefixed, spaced, numeric-looking) is carried into `k` verbatim as a
# string, with no special-casing or reinterpretation.
SPECIAL_KEY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="empty_string_key",
        doc={"obj": {"": 1}},
        expected=[{"k": "", "v": 1}],
        msg="Should handle empty string key",
    ),
    ExpressionTestCase(
        id="dotted_key",
        doc={"obj": {"a.b.c": 1}},
        expected=[{"k": "a.b.c", "v": 1}],
        msg="Should handle dotted key",
    ),
    ExpressionTestCase(
        id="unicode_key",
        doc={"obj": {"日本語": 1}},
        expected=[{"k": "日本語", "v": 1}],
        msg="Should handle unicode key",
    ),
    ExpressionTestCase(
        id="dollar_sign_key",
        doc={"obj": {"$field": 1}},
        expected=[{"k": "$field", "v": 1}],
        msg="Should handle dollar-sign key",
    ),
    ExpressionTestCase(
        id="key_with_spaces",
        doc={"obj": {"my key": 1}},
        expected=[{"k": "my key", "v": 1}],
        msg="Should handle key with spaces",
    ),
    ExpressionTestCase(
        id="numeric_string_keys",
        doc={"obj": {"0": "a", "1": "b"}},
        expected=[{"k": "0", "v": "a"}, {"k": "1", "v": "b"}],
        msg="Should handle numeric-looking keys as strings",
    ),
]

# Property [Non-recursive]: only the top-level object is decomposed; nested
# objects, arrays, and values that themselves look like a k/v pair are kept
# intact as the `v` payload rather than being expanded or reinterpreted.
NON_RECURSIVE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="value_looks_like_kv_pair",
        doc={"obj": {"a": {"k": "x", "v": 1}}},
        expected=[{"k": "a", "v": {"k": "x", "v": 1}}],
        msg="Should NOT interpret value as pre-existing k/v pair",
    ),
    ExpressionTestCase(
        id="nested_array_with_object",
        doc={"obj": {"k1": [1, {"a": {"b": 1}}]}},
        expected=[{"k": "k1", "v": [1, {"a": {"b": 1}}]}],
        msg="Should preserve nested array containing objects",
    ),
]

# Property [Order, case, and null preservation]: field order (including 10+
# fields) matches document field order, case-different keys stay distinct, and
# null values are preserved rather than omitted.
EDGE_CASE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="preserves_field_order",
        doc={"obj": {"qty": 25, "item": "abc123"}},
        expected=[{"k": "qty", "v": 25}, {"k": "item", "v": "abc123"}],
        msg="Should preserve field order",
    ),
    ExpressionTestCase(
        id="many_fields_order",
        doc={"obj": {f"field_{i}": i for i in range(12)}},
        expected=[{"k": f"field_{i}", "v": i} for i in range(12)],
        msg="Should preserve order for 10+ fields",
    ),
    ExpressionTestCase(
        id="null_value_in_object",
        doc={"obj": {"a": None, "b": 1}},
        expected=[{"k": "a", "v": None}, {"k": "b", "v": 1}],
        msg="Should preserve null values",
    ),
    ExpressionTestCase(
        id="all_null_values",
        doc={"obj": {"a": None, "b": None}},
        expected=[{"k": "a", "v": None}, {"k": "b", "v": None}],
        msg="Should preserve all null values",
    ),
    ExpressionTestCase(
        id="long_key_name",
        doc={"obj": {"k" * 1000: 1}},
        expected=[{"k": "k" * 1000, "v": 1}],
        msg="Should preserve 1000-char key name",
    ),
]

ALL_TESTS = (
    BASIC_TESTS
    + SPECIAL_KEY_TESTS
    + NON_RECURSIVE_TESTS
    + EDGE_CASE_TESTS
    + TEST_SUBSET_FOR_LITERAL
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_objectToArray_insert(collection, test):
    """Test $objectToArray with values from inserted documents."""
    result = execute_expression_with_insert(collection, {"$objectToArray": "$obj"}, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def _run_objectToArray_after_addFields(collection, doc, add_fields):
    """Insert doc, apply $addFields, then $objectToArray over $$ROOT."""
    collection.insert_one(materialize(doc) or {})
    return execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": materialize(add_fields)},
                {"$project": {"_id": 0, "result": {"$objectToArray": "$$ROOT"}}},
            ],
            "cursor": {},
        },
    )


def test_objectToArray_addFields_new_field_placed_last(collection):
    """A field added by a prior $addFields stage appears last in the output (manual B18)."""
    result = _run_objectToArray_after_addFields(
        collection, doc={"_id": 1, "a": 1, "b": 2}, add_fields={"c": 99}
    )
    assert_expression_result(
        result,
        expected=[
            {"k": "_id", "v": 1},
            {"k": "a", "v": 1},
            {"k": "b", "v": 2},
            {"k": "c", "v": 99},
        ],
        msg="Field added by $addFields should appear last in $objectToArray output",
    )


def test_objectToArray_addFields_existing_field_keeps_position(collection):
    """Updating an existing field via $addFields keeps its original position (manual B18)."""
    result = _run_objectToArray_after_addFields(
        collection, doc={"_id": 2, "a": 1, "b": 2, "c": 3}, add_fields={"a": 100}
    )
    assert_expression_result(
        result,
        expected=[
            {"k": "_id", "v": 2},
            {"k": "a", "v": 100},
            {"k": "b", "v": 2},
            {"k": "c", "v": 3},
        ],
        msg="Updating an existing field via $addFields should keep its original position",
    )
