"""
Tests for $unsetField basic operations: core behavior, null/missing handling,
expression types, field lookup, system variables, and multiple documents.
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
from documentdb_tests.framework.error_codes import SET_FIELD_INVALID_INPUT_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_TESTS: list[ExpressionTestCase] = [
    # Core behavior — field removal
    ExpressionTestCase(
        "remove_existing",
        expression={"$unsetField": {"field": "a", "input": {"a": 1, "b": 2}}},
        expected={"b": 2},
        msg="Should remove existing field",
    ),
    ExpressionTestCase(
        "remove_from_three",
        expression={"$unsetField": {"field": "b", "input": {"a": 1, "b": 2, "c": 3}}},
        expected={"a": 1, "c": 3},
        msg="Should remove middle field from three-field doc",
    ),
    ExpressionTestCase(
        "remove_only_field",
        expression={"$unsetField": {"field": "a", "input": {"a": 1}}},
        expected={},
        msg="Should return empty doc when removing only field",
    ),
    ExpressionTestCase(
        "remove_null_value",
        expression={"$unsetField": {"field": "a", "input": {"a": None, "b": 2}}},
        expected={"b": 2},
        msg="Should remove field with null value",
    ),
    ExpressionTestCase(
        "remove_array_value",
        expression={"$unsetField": {"field": "a", "input": {"a": [1, 2, 3], "b": 2}}},
        expected={"b": 2},
        msg="Should remove field with array value",
    ),
    ExpressionTestCase(
        "remove_object_value",
        expression={"$unsetField": {"field": "a", "input": {"a": {"x": 1}, "b": 2}}},
        expected={"b": 2},
        msg="Should remove field with object value",
    ),
    ExpressionTestCase(
        "remove_bool_value",
        expression={"$unsetField": {"field": "a", "input": {"a": True, "b": 2}}},
        expected={"b": 2},
        msg="Should remove field with boolean value",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$unsetField": {"field": "z", "input": {"a": 1, "b": 2}}},
        expected={"a": 1, "b": 2},
        msg="Non-existent field should return doc unchanged",
    ),
    ExpressionTestCase(
        "empty_doc",
        expression={"$unsetField": {"field": "a", "input": {}}},
        expected={},
        msg="Empty doc should return empty doc",
    ),
    # Null/Missing handling
    ExpressionTestCase(
        "null_input",
        expression={"$unsetField": {"field": "a", "input": None}},
        expected=None,
        msg="Null input should return null",
    ),
    ExpressionTestCase(
        "remove_input",
        expression={"$unsetField": {"field": "a", "input": "$$REMOVE"}},
        expected=None,
        msg="$$REMOVE input should return null",
    ),
    # Document shapes
    ExpressionTestCase(
        "flat_scalars",
        expression={
            "$unsetField": {"field": "a", "input": {"a": 1, "b": "str", "c": True, "d": None}}
        },
        expected={"b": "str", "c": True, "d": None},
        msg="Unsetting field from flat doc with scalar types should succeed",
    ),
    ExpressionTestCase(
        "deeply_nested",
        expression={"$unsetField": {"field": "a", "input": {"a": {"b": {"c": {"d": 1}}}, "x": 1}}},
        expected={"x": 1},
        msg="Removing field with deeply nested value should succeed",
    ),
    ExpressionTestCase(
        "nested_arrays",
        expression={"$unsetField": {"field": "arr", "input": {"arr": [[1, 2], [3, 4]], "x": 1}}},
        expected={"x": 1},
        msg="Removing field with nested arrays should succeed",
    ),
    ExpressionTestCase(
        "obj_with_array",
        expression={"$unsetField": {"field": "obj", "input": {"obj": {"arr": [1, 2, 3]}, "x": 1}}},
        expected={"x": 1},
        msg="Removing object field containing array should succeed",
    ),
    # Field order preservation
    ExpressionTestCase(
        "remove_first",
        expression={"$unsetField": {"field": "a", "input": {"a": 1, "b": 2, "c": 3}}},
        expected={"b": 2, "c": 3},
        msg="Removing first field should succeed and preserve remaining order",
    ),
    ExpressionTestCase(
        "remove_middle",
        expression={"$unsetField": {"field": "b", "input": {"a": 1, "b": 2, "c": 3}}},
        expected={"a": 1, "c": 3},
        msg="Removing middle field should succeed and preserve remaining order",
    ),
    ExpressionTestCase(
        "remove_last",
        expression={"$unsetField": {"field": "c", "input": {"a": 1, "b": 2, "c": 3}}},
        expected={"a": 1, "b": 2},
        msg="Removing last field should succeed and preserve remaining order",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_unsetField_literal(collection, test):
    """Test $unsetField core behavior and null/missing handling."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_field_ref",
        expression={"$unsetField": {"field": "x", "input": "$nonexistent"}},
        doc={"a": 1},
        expected=None,
        msg="Missing field reference as input should succeed and return null",
    ),
    ExpressionTestCase(
        "input_field_ref",
        expression={"$unsetField": {"field": "a", "input": "$obj"}},
        doc={"obj": {"a": 1, "b": 2}},
        expected={"b": 2},
        msg="Field reference as input should succeed and remove field",
    ),
    ExpressionTestCase(
        "input_nested_field_ref",
        expression={"$unsetField": {"field": "a", "input": "$x.y"}},
        doc={"x": {"y": {"a": 1, "b": 2}}},
        expected={"b": 2},
        msg="Nested field reference as input should succeed and remove field",
    ),
    ExpressionTestCase(
        "input_object_expr",
        expression={"$unsetField": {"field": "a", "input": {"a": "$x"}}},
        doc={"x": 1},
        expected={},
        msg="Object expression as input should succeed, evaluate, then unset",
    ),
    ExpressionTestCase(
        "input_array_ref_errors",
        expression={"$unsetField": {"field": "a", "input": "$arr"}},
        doc={"arr": [{"a": 1}, {"a": 2}]},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Array input via field ref should error with invalid input type",
    ),
    # $$ROOT and $$CURRENT
    ExpressionTestCase(
        "input_root",
        expression={"$unsetField": {"field": "x", "input": "$$ROOT"}},
        doc={"_id": 1, "x": 1, "y": 2},
        expected={"_id": 1, "y": 2},
        msg="$$ROOT as input should succeed and remove field",
    ),
    ExpressionTestCase(
        "input_current",
        expression={"$unsetField": {"field": "x", "input": "$$CURRENT"}},
        doc={"_id": 1, "x": 1, "y": 2},
        expected={"_id": 1, "y": 2},
        msg="$$CURRENT as input should succeed and remove field",
    ),
    # Non-traversal and special inputs
    ExpressionTestCase(
        "array_input_errors",
        expression={"$unsetField": {"field": "a", "input": "$items"}},
        doc={"items": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Array input via field ref should error with invalid input type, not traverse",
    ),
    ExpressionTestCase(
        "numeric_string_field",
        expression={"$unsetField": {"field": "0", "input": "$$ROOT"}},
        doc={"_id": 1, "0": "zero", "1": "one", "a": 1},
        expected={"_id": 1, "1": "one", "a": 1},
        msg="Numeric string field should be successfully removed from $$ROOT",
    ),
    ExpressionTestCase(
        "remove_id_from_root",
        expression={"$unsetField": {"field": "_id", "input": "$$ROOT"}},
        doc={"_id": 1, "a": 2},
        expected={"a": 2},
        msg="Removing _id from $$ROOT should succeed",
    ),
    ExpressionTestCase(
        "regular_field_preserves_id",
        expression={"$unsetField": {"field": "a", "input": "$$ROOT"}},
        doc={"_id": 1, "a": 2, "b": 3},
        expected={"_id": 1, "b": 3},
        msg="Removing regular field from $$ROOT should succeed and preserve _id",
    ),
    ExpressionTestCase(
        "composite_array_path_errors",
        expression={"$unsetField": {"field": "x", "input": "$a.b"}},
        doc={"a": [{"b": {"x": 1}}, {"b": {"y": 2}}]},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Composite array path as input should error with invalid input type",
    ),
    ExpressionTestCase(
        "array_index_on_object_key",
        expression={"$unsetField": {"field": "x", "input": "$a.0"}},
        doc={"a": {"0": {"x": 1, "y": 2}}},
        expected={"y": 2},
        msg="Numeric index on object should succeed and resolve to object key",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_REF_TESTS))
def test_unsetField_field_ref(collection, test):
    """Test $unsetField with field references and inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result,
        expected=test.expected if test.error_code is None else None,
        error_code=test.error_code,
        msg=test.msg,
    )


def test_unsetField_many_fields(collection):
    """Test removing a field from a document with 50+ fields."""
    doc = {chr(i): i for i in range(97, 123)}  # a-z
    doc.update({f"f{i}": i for i in range(26)})  # f0-f25, total 52 fields
    result = execute_expression(collection, {"$unsetField": {"field": "m", "input": doc}})
    expected = dict(doc)
    del expected["m"]
    assert_expression_result(result, expected=expected, msg="Should remove field from large doc")


def test_unsetField_deeply_nested_value(collection):
    """Test removing field with deeply nested value (10+ levels)."""
    nested = {"val": 1}
    for _ in range(10):
        nested = {"inner": nested}
    doc = {"deep": nested, "keep": 1}
    result = execute_expression(collection, {"$unsetField": {"field": "deep", "input": doc}})
    assert_expression_result(result, expected={"keep": 1}, msg="Should remove deeply nested value")
