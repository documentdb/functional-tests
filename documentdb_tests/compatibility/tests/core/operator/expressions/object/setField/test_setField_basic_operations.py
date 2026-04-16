"""
Tests for $setField basic operations: set/remove, null/missing propagation,
expression types, input correlation, and error conditions.
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
    ExpressionTestCase(
        "update_existing",
        expression={"$setField": {"field": "a", "input": {"a": 1, "b": 2}, "value": 99}},
        expected={"a": 99, "b": 2},
        msg="Should update existing field",
    ),
    ExpressionTestCase(
        "add_new_field",
        expression={"$setField": {"field": "c", "input": {"a": 1}, "value": 99}},
        expected={"a": 1, "c": 99},
        msg="Should add new field",
    ),
    ExpressionTestCase(
        "add_to_empty",
        expression={"$setField": {"field": "x", "input": {}, "value": 1}},
        expected={"x": 1},
        msg="Should add field to empty object",
    ),
    ExpressionTestCase(
        "remove_existing",
        expression={"$setField": {"field": "a", "input": {"a": 1, "b": 2}, "value": "$$REMOVE"}},
        expected={"b": 2},
        msg="Should remove existing field",
    ),
    ExpressionTestCase(
        "remove_nonexistent",
        expression={"$setField": {"field": "z", "input": {"a": 1}, "value": "$$REMOVE"}},
        expected={"a": 1},
        msg="Removing non-existent field should be no-op",
    ),
    ExpressionTestCase(
        "remove_from_empty",
        expression={"$setField": {"field": "x", "input": {}, "value": "$$REMOVE"}},
        expected={},
        msg="Removing from empty should return empty",
    ),
    ExpressionTestCase(
        "remove_only_field",
        expression={"$setField": {"field": "a", "input": {"a": 1}, "value": "$$REMOVE"}},
        expected={},
        msg="Removing only field should return empty",
    ),
    # Null propagation (literal inputs)
    ExpressionTestCase(
        "input_null",
        expression={"$setField": {"field": "x", "input": None, "value": 1}},
        expected=None,
        msg="Null input should return null",
    ),
    ExpressionTestCase(
        "value_null_new",
        expression={"$setField": {"field": "x", "input": {"a": 1}, "value": None}},
        expected={"a": 1, "x": None},
        msg="Null value should set field to null",
    ),
    ExpressionTestCase(
        "value_null_existing",
        expression={"$setField": {"field": "a", "input": {"a": 1}, "value": None}},
        expected={"a": None},
        msg="Null value should update existing to null",
    ),
    ExpressionTestCase(
        "input_null_remove",
        expression={"$setField": {"field": "x", "input": None, "value": "$$REMOVE"}},
        expected=None,
        msg="Null input with $$REMOVE should return null",
    ),
    # Literal expression types
    ExpressionTestCase(
        "input_literal",
        expression={"$setField": {"field": "x", "input": {"a": 1}, "value": 2}},
        expected={"a": 1, "x": 2},
        msg="Setting field on literal object input should succeed",
    ),
    ExpressionTestCase(
        "value_literal",
        expression={"$setField": {"field": "x", "input": {}, "value": 42}},
        expected={"x": 42},
        msg="Setting literal value on empty object should succeed",
    ),
    # Correlation
    ExpressionTestCase(
        "dotted_field",
        expression={"$setField": {"field": "a.b", "input": {}, "value": 1}},
        expected={"a.b": 1},
        msg="Dotted field name should succeed and create literal top-level key",
    ),
    ExpressionTestCase(
        "dollar_field",
        expression={"$setField": {"field": {"$literal": "$x"}, "input": {}, "value": 1}},
        expected={"$x": 1},
        msg="Dollar field via $literal should succeed and create literal key",
    ),
    ExpressionTestCase(
        "literal_dollar_array_value",
        expression={
            "$setField": {"field": {"$literal": "$price"}, "input": {}, "value": [1, 2, 3]}
        },
        expected={"$price": [1, 2, 3]},
        msg="$literal dollar field with array value should succeed",
    ),
    # Document shapes
    ExpressionTestCase(
        "empty_doc",
        expression={"$setField": {"field": "x", "input": {}, "value": 1}},
        expected={"x": 1},
        msg="Setting field on empty document should succeed",
    ),
    ExpressionTestCase(
        "flat_doc",
        expression={
            "$setField": {
                "field": "new",
                "input": {"a": 1, "b": "str", "c": True, "d": None},
                "value": 99,
            }
        },
        expected={"a": 1, "b": "str", "c": True, "d": None, "new": 99},
        msg="Adding field to flat document with scalar types should succeed",
    ),
    ExpressionTestCase(
        "deeply_nested",
        expression={
            "$setField": {"field": "x", "input": {"a": {"b": {"c": {"d": 1}}}}, "value": 2}
        },
        expected={"a": {"b": {"c": {"d": 1}}}, "x": 2},
        msg="Adding field to deeply nested document should succeed",
    ),
    ExpressionTestCase(
        "nested_arrays",
        expression={"$setField": {"field": "x", "input": {"arr": [[1, 2], [3, 4]]}, "value": 5}},
        expected={"arr": [[1, 2], [3, 4]], "x": 5},
        msg="Adding field to document with nested arrays should succeed",
    ),
    ExpressionTestCase(
        "obj_with_array",
        expression={"$setField": {"field": "x", "input": {"obj": {"arr": [1, 2, 3]}}, "value": 6}},
        expected={"obj": {"arr": [1, 2, 3]}, "x": 6},
        msg="Adding field to document containing object with array should succeed",
    ),
    # Overwriting
    ExpressionTestCase(
        "scalar_with_scalar",
        expression={"$setField": {"field": "a", "input": {"a": 1}, "value": 2}},
        expected={"a": 2},
        msg="Overwriting scalar with scalar should succeed",
    ),
    ExpressionTestCase(
        "object_with_scalar",
        expression={"$setField": {"field": "a", "input": {"a": {"b": 1}}, "value": 2}},
        expected={"a": 2},
        msg="Overwriting object with scalar should succeed",
    ),
    ExpressionTestCase(
        "scalar_with_object",
        expression={"$setField": {"field": "a", "input": {"a": 1}, "value": {"b": 2}}},
        expected={"a": {"b": 2}},
        msg="Overwriting scalar with object should succeed",
    ),
    ExpressionTestCase(
        "array_with_scalar",
        expression={"$setField": {"field": "a", "input": {"a": [1, 2, 3]}, "value": "replaced"}},
        expected={"a": "replaced"},
        msg="Overwriting array with scalar should succeed",
    ),
    ExpressionTestCase(
        "change_type",
        expression={"$setField": {"field": "a", "input": {"a": 1}, "value": "string"}},
        expected={"a": "string"},
        msg="Changing field type from int to string should succeed",
    ),
    # Non-traversal
    ExpressionTestCase(
        "dotted_literal",
        expression={"$setField": {"field": "a.b.c", "input": {}, "value": 1}},
        expected={"a.b.c": 1},
        msg="Dotted name should succeed and create literal top-level key, not traverse",
    ),
    ExpressionTestCase(
        "dotted_no_nested_modify",
        expression={"$setField": {"field": "a.b", "input": {"a": {"b": 1}}, "value": 2}},
        expected={"a": {"b": 1}, "a.b": 2},
        msg="Dotted name should succeed and create new top-level key, not modify nested path",
    ),
    ExpressionTestCase(
        "indexed_no_array_modify",
        expression={"$setField": {"field": "a.0", "input": {"a": [10, 20]}, "value": 99}},
        expected={"a": [10, 20], "a.0": 99},
        msg="Indexed name should succeed and create new top-level key, not modify array element",
    ),
    # Field ordering
    ExpressionTestCase(
        "preserves_order_on_add",
        expression={"$setField": {"field": "d", "input": {"c": 3, "a": 1, "b": 2}, "value": 4}},
        expected={"c": 3, "a": 1, "b": 2, "d": 4},
        msg="Should preserve order and append",
    ),
    ExpressionTestCase(
        "update_preserves_position",
        expression={"$setField": {"field": "b", "input": {"a": 1, "b": 2, "c": 3}, "value": 99}},
        expected={"a": 1, "b": 99, "c": 3},
        msg="Should preserve field position on update",
    ),
    # Idempotency
    ExpressionTestCase(
        "same_value_idempotent",
        expression={"$setField": {"field": "a", "input": {"a": 1}, "value": 1}},
        expected={"a": 1},
        msg="Same value should be idempotent",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_setField_literal(collection, test):
    """Test $setField with literal expressions."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


FIELD_REF_TESTS: list[ExpressionTestCase] = [
    # Missing/null propagation with field refs
    ExpressionTestCase(
        "input_missing",
        expression={"$setField": {"field": "x", "input": "$nonexistent", "value": 1}},
        doc={"a": 1},
        expected=None,
        msg="Missing input should return null",
    ),
    ExpressionTestCase(
        "input_missing_remove",
        expression={"$setField": {"field": "x", "input": "$nonexistent", "value": "$$REMOVE"}},
        doc={"a": 1},
        expected=None,
        msg="Missing input with $$REMOVE should return null",
    ),
    ExpressionTestCase(
        "value_missing_ref",
        expression={"$setField": {"field": "x", "input": {}, "value": "$nonexistent"}},
        doc={"a": 1},
        expected={},
        msg="Missing value ref should succeed and not add field",
    ),
    ExpressionTestCase(
        "value_undefined_existing",
        expression={"$setField": {"field": "a", "input": {"a": 1}, "value": "$nonexistent"}},
        doc={"z": 1},
        expected={},
        msg="Undefined value on existing field should succeed and remove it",
    ),
    ExpressionTestCase(
        "value_undefined_new",
        expression={"$setField": {"field": "x", "input": {}, "value": "$nonexistent"}},
        doc={"z": 1},
        expected={},
        msg="Undefined value on new field should succeed and not add field",
    ),
    # Expression types with field refs
    ExpressionTestCase(
        "input_field_ref",
        expression={"$setField": {"field": "x", "input": "$obj", "value": 1}},
        doc={"obj": {"a": 1}},
        expected={"a": 1, "x": 1},
        msg="Field reference as input should succeed and add field",
    ),
    ExpressionTestCase(
        "value_field_ref",
        expression={"$setField": {"field": "x", "input": {}, "value": "$a"}},
        doc={"a": 5},
        expected={"x": 5},
        msg="Field reference as value should succeed and resolve value",
    ),
    ExpressionTestCase(
        "value_obj_expr",
        expression={"$setField": {"field": "x", "input": {}, "value": {"a": "$y"}}},
        doc={"y": 10},
        expected={"x": {"a": 10}},
        msg="Object expression as value should succeed and resolve field refs",
    ),
    ExpressionTestCase(
        "input_array_expr",
        expression={"$setField": {"field": "x", "input": ["$obj"], "value": 1}},
        doc={"obj": {"a": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Array expression as input should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_composite_array",
        expression={"$setField": {"field": "x", "input": "$a.b", "value": 1}},
        doc={"a": [{"b": {"x": 1}}, {"b": {"y": 2}}]},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Composite array path as input should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_array_index_path",
        expression={"$setField": {"field": "x", "input": "$a.0.b", "value": 1}},
        doc={"a": [{"b": {"z": 1}}, {"b": {"z": 2}}]},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Array index path as input should error with invalid input type",
    ),
    ExpressionTestCase(
        "value_array_expr",
        expression={"$setField": {"field": "x", "input": {}, "value": ["$a", "$b"]}},
        doc={"a": 1, "b": 2},
        expected={"x": [1, 2]},
        msg="Array expression as value should succeed and resolve field refs",
    ),
    ExpressionTestCase(
        "input_array_index_on_object_key",
        expression={"$setField": {"field": "new", "input": "$a.0", "value": 1}},
        doc={"a": {"0": {"x": 1}}},
        expected={"x": 1, "new": 1},
        msg="Numeric index on object should succeed and resolve to object key",
    ),
    # $$ROOT and $$CURRENT
    ExpressionTestCase(
        "root_input",
        expression={"$setField": {"field": "x", "input": "$$ROOT", "value": 1}},
        doc={"_id": 1, "a": 1},
        expected={"_id": 1, "a": 1, "x": 1},
        msg="$$ROOT as input should succeed and add new field",
    ),
    ExpressionTestCase(
        "root_remove",
        expression={"$setField": {"field": "a", "input": "$$ROOT", "value": "$$REMOVE"}},
        doc={"_id": 1, "a": 1, "b": 2},
        expected={"_id": 1, "b": 2},
        msg="$$ROOT as input with $$REMOVE should succeed and remove field",
    ),
    ExpressionTestCase(
        "current_input",
        expression={"$setField": {"field": "x", "input": "$$CURRENT", "value": 1}},
        doc={"_id": 1, "a": 1},
        expected={"_id": 1, "a": 1, "x": 1},
        msg="$$CURRENT as input should succeed and add new field",
    ),
    ExpressionTestCase(
        "value_root",
        expression={"$setField": {"field": "x", "input": {}, "value": "$$ROOT"}},
        doc={"_id": 1, "a": 1},
        expected={"x": {"_id": 1, "a": 1}},
        msg="$$ROOT as value should succeed and embed entire document",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_REF_TESTS))
def test_setField_field_ref(collection, test):
    """Test $setField with field references and inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result,
        expected=test.expected if test.error_code is None else None,
        error_code=test.error_code,
        msg=test.msg,
    )
