"""
Core tests for $getField expression.

Covers basic syntax (shorthand and full), return type preservation for all
BSON types, expression types for field and input parameters, system variables,
null/missing propagation, and non-object input behavior.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Return type preservation — all BSON types
# ---------------------------------------------------------------------------
RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int",
        expression={"$getField": {"field": "val", "input": {"val": 1}}},
        expected=1,
        msg="Should return int",
    ),
    ExpressionTestCase(
        "long",
        expression={"$getField": {"field": "val", "input": {"val": Int64(1)}}},
        expected=Int64(1),
        msg="Should return long",
    ),
    ExpressionTestCase(
        "double",
        expression={"$getField": {"field": "val", "input": {"val": 1.5}}},
        expected=1.5,
        msg="Should return double",
    ),
    ExpressionTestCase(
        "decimal128",
        expression={"$getField": {"field": "val", "input": {"val": Decimal128("1.5")}}},
        expected=Decimal128("1.5"),
        msg="Should return decimal128",
    ),
    ExpressionTestCase(
        "string",
        expression={"$getField": {"field": "val", "input": {"val": "hello"}}},
        expected="hello",
        msg="Should return string",
    ),
    ExpressionTestCase(
        "bool",
        expression={"$getField": {"field": "val", "input": {"val": True}}},
        expected=True,
        msg="Should return bool",
    ),
    ExpressionTestCase(
        "null",
        expression={"$getField": {"field": "val", "input": {"val": None}}},
        expected=None,
        msg="Should return null",
    ),
    ExpressionTestCase(
        "date",
        expression={
            "$getField": {
                "field": "val",
                "input": {"val": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            }
        },
        expected=datetime(2024, 1, 1, tzinfo=timezone.utc),
        msg="Should return date",
    ),
    ExpressionTestCase(
        "objectid",
        expression={
            "$getField": {"field": "val", "input": {"val": ObjectId("000000000000000000000000")}}
        },
        expected=ObjectId("000000000000000000000000"),
        msg="Should return objectId",
    ),
    ExpressionTestCase(
        "array",
        expression={"$getField": {"field": "val", "input": {"val": [1, 2, 3]}}},
        expected=[1, 2, 3],
        msg="Should return array",
    ),
    ExpressionTestCase(
        "object",
        expression={"$getField": {"field": "val", "input": {"val": {"x": 1}}}},
        expected={"x": 1},
        msg="Should return object",
    ),
    ExpressionTestCase(
        "bindata",
        expression={"$getField": {"field": "val", "input": {"val": Binary(b"\x01\x02")}}},
        expected=b"\x01\x02",
        msg="Should return binData",
    ),
    ExpressionTestCase(
        "regex",
        expression={"$getField": {"field": "val", "input": {"val": Regex("abc", "i")}}},
        expected=Regex("abc", "i"),
        msg="Should return regex",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$getField": {"field": "val", "input": {"val": []}}},
        expected=[],
        msg="Should return empty array",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$getField": {"field": "val", "input": {"val": {}}}},
        expected={},
        msg="Should return empty object",
    ),
    ExpressionTestCase(
        "nested_object",
        expression={"$getField": {"field": "val", "input": {"val": {"a": {"b": {"c": 1}}}}}},
        expected={"a": {"b": {"c": 1}}},
        msg="Should return nested object",
    ),
    ExpressionTestCase(
        "mixed_array",
        expression={"$getField": {"field": "val", "input": {"val": [1, "two", None, True]}}},
        expected=[1, "two", None, True],
        msg="Should return mixed array",
    ),
    ExpressionTestCase(
        "minkey",
        expression={"$getField": {"field": "val", "input": {"val": MinKey()}}},
        expected=MinKey(),
        msg="Should return MinKey",
    ),
    ExpressionTestCase(
        "maxkey",
        expression={"$getField": {"field": "val", "input": {"val": MaxKey()}}},
        expected=MaxKey(),
        msg="Should return MaxKey",
    ),
    ExpressionTestCase(
        "timestamp",
        expression={"$getField": {"field": "val", "input": {"val": Timestamp(0, 1)}}},
        expected=Timestamp(0, 1),
        msg="Should return Timestamp",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RETURN_TYPE_TESTS))
def test_getField_return_types(collection, test):
    """Test $getField preserves BSON type of returned value."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Literal success — syntax, expression types, input types
# ---------------------------------------------------------------------------
LITERAL_SUCCESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "full_syntax",
        expression={"$getField": {"field": "a", "input": {"a": 1}}},
        expected=1,
        msg="Should return value with full syntax",
    ),
    ExpressionTestCase(
        "field_concat_expr",
        expression={"$getField": {"field": {"$concat": ["a", "b"]}, "input": {"ab": 1}}},
        expected=1,
        msg="Should resolve $concat expression to field name",
    ),
    ExpressionTestCase(
        "field_literal_dollar",
        expression={
            "$getField": {
                "field": {"$literal": "$x"},
                "input": {"$setField": {"field": {"$literal": "$x"}, "input": {}, "value": 5}},
            }
        },
        expected=5,
        msg="Should access $-prefixed field via $literal",
    ),
    ExpressionTestCase(
        "field_toString_expr",
        expression={"$getField": {"field": {"$toString": "a"}, "input": {"a": 1}}},
        expected=1,
        msg="Should resolve $toString expression to field name",
    ),
    ExpressionTestCase(
        "input_mergeObjects_expr",
        expression={"$getField": {"field": "a", "input": {"$mergeObjects": [{"a": 1}, {"b": 2}]}}},
        expected=1,
        msg="Should return value from $mergeObjects input",
    ),
    ExpressionTestCase(
        "deeply_nested_object_input",
        expression={"$getField": {"field": "a", "input": {"a": {"b": {"c": {"d": 1}}}}}},
        expected={"b": {"c": {"d": 1}}},
        msg="Should return nested object value",
    ),
    ExpressionTestCase(
        "object_with_nested_arrays",
        expression={"$getField": {"field": "arr", "input": {"arr": [[1, 2], [3, 4]]}}},
        expected=[[1, 2], [3, 4]],
        msg="Should return nested array value",
    ),
    ExpressionTestCase(
        "concat_literals_dotted_field",
        expression={
            "$getField": {
                "field": {"$concat": ["price", ".", "usd"]},
                "input": {"$setField": {"field": "price.usd", "input": {}, "value": 45}},
            }
        },
        expected=45,
        msg="Should resolve $concat of literals to dotted field name",
    ),
    ExpressionTestCase(
        "null_input",
        expression={"$getField": {"field": "a", "input": None}},
        expected=None,
        msg="Should return null when input is null",
    ),
    ExpressionTestCase(
        "field_value_null",
        expression={"$getField": {"field": "a", "input": {"a": None}}},
        expected=None,
        msg="Should return null for null field value",
    ),
    ExpressionTestCase(
        "dollar_field_value_null",
        expression={
            "$getField": {
                "field": {"$literal": "$x"},
                "input": {"$setField": {"field": {"$literal": "$x"}, "input": {}, "value": None}},
            }
        },
        expected=None,
        msg="Should return null when $-prefixed field value is null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_SUCCESS_TESTS))
def test_getField_literal_success(collection, test):
    """Test $getField success cases with literal inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Insert-based success — shorthand, field refs, system variables
# ---------------------------------------------------------------------------
INSERT_SUCCESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "shorthand",
        expression={"$getField": "a"},
        doc={"a": 1},
        expected=1,
        msg="Should return field value with shorthand syntax",
    ),
    ExpressionTestCase(
        "field_ref",
        expression={"$getField": {"field": "$fieldName", "input": {"a": 1}}},
        doc={"fieldName": "a"},
        expected=1,
        msg="Should resolve field reference to string",
    ),
    ExpressionTestCase(
        "input_field_ref",
        expression={"$getField": {"field": "a", "input": "$subdoc"}},
        doc={"subdoc": {"a": 5}},
        expected=5,
        msg="Should return value from field reference input",
    ),
    ExpressionTestCase(
        "dynamic_field_from_doc",
        expression={"$getField": {"field": "$fieldName", "input": "$$CURRENT"}},
        doc={"fieldName": "target", "target": 42},
        expected=42,
        msg="Should resolve field name dynamically from document",
    ),
    ExpressionTestCase(
        "dynamic_field_concat_with_ref",
        expression={"$getField": {"field": {"$concat": ["$prefix", "b"]}, "input": {"ab": 99}}},
        doc={"prefix": "a"},
        expected=99,
        msg="Should resolve $concat with field ref to field name",
    ),
    ExpressionTestCase(
        "nested_getfield_as_field",
        expression={"$getField": {"field": {"$getField": "fieldName"}, "input": {"x": 1}}},
        doc={"fieldName": "x"},
        expected=1,
        msg="Should resolve nested $getField as field name",
    ),
    ExpressionTestCase(
        "explicit_current",
        expression={"$getField": {"field": "a", "input": "$$CURRENT"}},
        doc={"a": 1},
        expected=1,
        msg="Should return value from explicit $$CURRENT",
    ),
    ExpressionTestCase(
        "root",
        expression={"$getField": {"field": "a", "input": "$$ROOT"}},
        doc={"a": 1},
        expected=1,
        msg="Should return value from $$ROOT",
    ),
    ExpressionTestCase(
        "current_dotted_path_as_field_ref",
        expression={"$getField": {"field": "$$CURRENT.fieldName", "input": {"a": 1}}},
        doc={"fieldName": "a"},
        expected=1,
        msg="Should resolve $$CURRENT.fieldName to string field name",
    ),
    ExpressionTestCase(
        "root_dotted_path_as_field_ref",
        expression={"$getField": {"field": "$$ROOT.fieldName", "input": {"a": 1}}},
        doc={"fieldName": "a"},
        expected=1,
        msg="Should resolve $$ROOT.fieldName to string field name",
    ),
    ExpressionTestCase(
        "input_ref_resolves_to_null",
        expression={"$getField": {"field": "a", "input": "$sub"}},
        doc={"sub": None},
        expected=None,
        msg="Should return null when input ref resolves to null",
    ),
    ExpressionTestCase(
        "field_value_is_null",
        expression={"$getField": "a"},
        doc={"a": None},
        expected=None,
        msg="Should return null when field value is null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INSERT_SUCCESS_TESTS))
def test_getField_insert_success(collection, test):
    """Test $getField success cases with inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Missing result cases (literal) — includes non-object input types
# ---------------------------------------------------------------------------
LITERAL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_field_in_input",
        expression={"$getField": {"field": "missing_field", "input": {"a": 1}}},
        msg="Should return missing when field not in input",
    ),
    ExpressionTestCase(
        "empty_object_input",
        expression={"$getField": {"field": "a", "input": {}}},
        msg="Should return missing when field not in empty object",
    ),
    ExpressionTestCase(
        "nested_outer_input_missing",
        expression={
            "$getField": {"field": "a", "input": {"$getField": {"field": "x", "input": {"y": 1}}}}
        },
        msg="Should return missing when nested getField outer input is missing",
    ),
    ExpressionTestCase(
        "nested_inner_missing",
        expression={
            "$getField": {
                "field": "b",
                "input": {"$getField": {"field": "missing", "input": {"a": {"b": 1}}}},
            }
        },
        msg="Should return missing when inner getField result is missing",
    ),
    ExpressionTestCase(
        "dollar_field_not_present",
        expression={"$getField": {"field": {"$literal": "$x"}, "input": {"a": 1}}},
        msg="Should return missing when $-prefixed field not present",
    ),
    ExpressionTestCase(
        "int_input",
        expression={"$getField": {"field": "a", "input": 1}},
        msg="Should return missing for int input",
    ),
    ExpressionTestCase(
        "long_input",
        expression={"$getField": {"field": "a", "input": Int64(1)}},
        msg="Should return missing for long input",
    ),
    ExpressionTestCase(
        "double_input",
        expression={"$getField": {"field": "a", "input": 1.5}},
        msg="Should return missing for double input",
    ),
    ExpressionTestCase(
        "decimal128_input",
        expression={"$getField": {"field": "a", "input": Decimal128("1")}},
        msg="Should return missing for decimal128 input",
    ),
    ExpressionTestCase(
        "bool_input",
        expression={"$getField": {"field": "a", "input": True}},
        msg="Should return missing for bool input",
    ),
    ExpressionTestCase(
        "string_input",
        expression={"$getField": {"field": "a", "input": "hello"}},
        msg="Should return missing for string input",
    ),
    ExpressionTestCase(
        "array_input",
        expression={"$getField": {"field": "a", "input": [1, 2]}},
        msg="Should return missing for array input",
    ),
    ExpressionTestCase(
        "date_input",
        expression={
            "$getField": {"field": "a", "input": datetime(2024, 1, 1, tzinfo=timezone.utc)}
        },
        msg="Should return missing for date input",
    ),
    ExpressionTestCase(
        "objectid_input",
        expression={"$getField": {"field": "a", "input": ObjectId("000000000000000000000000")}},
        msg="Should return missing for objectId input",
    ),
    ExpressionTestCase(
        "bindata_input",
        expression={"$getField": {"field": "a", "input": Binary(b"\x00")}},
        msg="Should return missing for binData input",
    ),
    ExpressionTestCase(
        "regex_input",
        expression={"$getField": {"field": "a", "input": Regex("abc")}},
        msg="Should return missing for regex input",
    ),
    ExpressionTestCase(
        "timestamp_input",
        expression={"$getField": {"field": "a", "input": Timestamp(0, 1)}},
        msg="Should return missing for timestamp input",
    ),
    ExpressionTestCase(
        "minkey_input",
        expression={"$getField": {"field": "a", "input": MinKey()}},
        msg="Should return missing for minKey input",
    ),
    ExpressionTestCase(
        "maxkey_input",
        expression={"$getField": {"field": "a", "input": MaxKey()}},
        msg="Should return missing for maxKey input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_MISSING_TESTS))
def test_getField_literal_missing(collection, test):
    """Test $getField returns missing for literal input cases."""
    result = execute_expression(collection, test.expression)
    assertSuccess(result, [{}], msg=test.msg)


# ---------------------------------------------------------------------------
# Missing result cases
# ---------------------------------------------------------------------------
INSERT_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "shorthand_missing_field",
        expression={"$getField": "b"},
        doc={"a": 1},
        msg="Should return missing when shorthand field not in document",
    ),
    ExpressionTestCase(
        "missing_input_ref",
        expression={"$getField": {"field": "x", "input": "$nonexistent"}},
        doc={"a": 1},
        msg="Should return missing when input ref is missing",
    ),
    ExpressionTestCase(
        "array_of_objects_input",
        expression={"$getField": {"field": "a", "input": "$items"}},
        doc={"items": [{"a": 1}, {"a": 2}]},
        msg="Should return missing when input is array of objects",
    ),
    ExpressionTestCase(
        "remove_input",
        expression={"$getField": {"field": "a", "input": "$$REMOVE"}},
        doc={"a": 1},
        msg="Should return missing when input is $$REMOVE",
    ),
    ExpressionTestCase(
        "no_nested_traversal",
        expression={"$getField": {"field": "a.b", "input": "$doc"}},
        doc={"doc": {"a": {"b": 1}}},
        msg="Should return missing — no implicit nested traversal",
    ),
    ExpressionTestCase(
        "no_array_index_traversal",
        expression={"$getField": {"field": "a.0", "input": "$doc"}},
        doc={"doc": {"a": [10, 20]}},
        msg="Should return missing — no implicit array index traversal",
    ),
    ExpressionTestCase(
        "no_deep_nested_traversal",
        expression={"$getField": {"field": "a.b.c", "input": "$doc"}},
        doc={"doc": {"a": {"b": {"c": 1}}}},
        msg="Should return missing — no deep nested traversal",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INSERT_MISSING_TESTS))
def test_getField_insert_missing(collection, test):
    """Test $getField returns missing for insert-based cases."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assertSuccess(result, [{}], msg=test.msg)
