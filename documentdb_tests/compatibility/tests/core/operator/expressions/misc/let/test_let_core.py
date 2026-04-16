"""
Core tests for $let expression.

Covers BSON type passthrough, numeric special values, Decimal128 precision,
type distinction, variable binding, scoping basics, field path assignments,
and $$ROOT/$$CURRENT access.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# ---------------------------------------------------------------------------
# All literal-only core tests
# ---------------------------------------------------------------------------
CORE_TESTS: list[ExpressionTestCase] = [
    # BSON types
    ExpressionTestCase(
        "int",
        expression={"$let": {"vars": {"x": 42}, "in": "$$x"}},
        expected=42,
        msg="Should preserve int",
    ),
    ExpressionTestCase(
        "long",
        expression={"$let": {"vars": {"x": Int64(42)}, "in": "$$x"}},
        expected=Int64(42),
        msg="Should preserve long",
    ),
    ExpressionTestCase(
        "double",
        expression={"$let": {"vars": {"x": 1.5}, "in": "$$x"}},
        expected=1.5,
        msg="Should preserve double",
    ),
    ExpressionTestCase(
        "decimal128",
        expression={"$let": {"vars": {"x": DECIMAL128_ONE_AND_HALF}, "in": "$$x"}},
        expected=DECIMAL128_ONE_AND_HALF,
        msg="Should preserve decimal128",
    ),
    ExpressionTestCase(
        "string",
        expression={"$let": {"vars": {"x": "hello"}, "in": "$$x"}},
        expected="hello",
        msg="Should preserve string",
    ),
    ExpressionTestCase(
        "bool_true",
        expression={"$let": {"vars": {"x": True}, "in": "$$x"}},
        expected=True,
        msg="Should preserve bool true",
    ),
    ExpressionTestCase(
        "bool_false",
        expression={"$let": {"vars": {"x": False}, "in": "$$x"}},
        expected=False,
        msg="Should preserve bool false",
    ),
    ExpressionTestCase(
        "date",
        expression={"$let": {"vars": {"x": datetime(2024, 1, 1)}, "in": "$$x"}},
        expected=datetime(2024, 1, 1),
        msg="Should preserve date",
    ),
    ExpressionTestCase(
        "null",
        expression={"$let": {"vars": {"x": None}, "in": "$$x"}},
        expected=None,
        msg="Should preserve null",
    ),
    ExpressionTestCase(
        "object",
        expression={"$let": {"vars": {"x": {"a": 1}}, "in": "$$x"}},
        expected={"a": 1},
        msg="Should preserve object",
    ),
    ExpressionTestCase(
        "array",
        expression={"$let": {"vars": {"x": [1, 2, 3]}, "in": "$$x"}},
        expected=[1, 2, 3],
        msg="Should preserve array",
    ),
    ExpressionTestCase(
        "bindata",
        expression={"$let": {"vars": {"x": Binary(b"\x01\x02")}, "in": "$$x"}},
        expected=b"\x01\x02",
        msg="Should preserve binData",
    ),
    ExpressionTestCase(
        "objectid",
        expression={"$let": {"vars": {"x": ObjectId("000000000000000000000000")}, "in": "$$x"}},
        expected=ObjectId("000000000000000000000000"),
        msg="Should preserve ObjectId",
    ),
    ExpressionTestCase(
        "regex",
        expression={"$let": {"vars": {"x": Regex("abc", "i")}, "in": "$$x"}},
        expected=Regex("abc", "i"),
        msg="Should preserve regex",
    ),
    ExpressionTestCase(
        "javascript",
        expression={"$let": {"vars": {"x": Code("function(){}")}, "in": "$$x"}},
        expected=Code("function(){}"),
        msg="Should preserve javascript",
    ),
    ExpressionTestCase(
        "timestamp",
        expression={"$let": {"vars": {"x": Timestamp(0, 1)}, "in": "$$x"}},
        expected=Timestamp(0, 1),
        msg="Should preserve timestamp",
    ),
    ExpressionTestCase(
        "minkey",
        expression={"$let": {"vars": {"x": MinKey()}, "in": "$$x"}},
        expected=MinKey(),
        msg="Should preserve MinKey",
    ),
    ExpressionTestCase(
        "maxkey",
        expression={"$let": {"vars": {"x": MaxKey()}, "in": "$$x"}},
        expected=MaxKey(),
        msg="Should preserve MaxKey",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$let": {"vars": {"x": []}, "in": "$$x"}},
        expected=[],
        msg="Should preserve empty array",
    ),
    ExpressionTestCase(
        "nested_array",
        expression={"$let": {"vars": {"x": [[1, 2], [3]]}, "in": "$$x"}},
        expected=[[1, 2], [3]],
        msg="Should preserve nested array",
    ),
    ExpressionTestCase(
        "array_of_objects",
        expression={"$let": {"vars": {"x": [{"a": 1}, {"b": 2}]}, "in": "$$x"}},
        expected=[{"a": 1}, {"b": 2}],
        msg="Should preserve array of objects",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$let": {"vars": {"x": {}}, "in": "$$x"}},
        expected={},
        msg="Should preserve empty object",
    ),
    ExpressionTestCase(
        "deeply_nested_object",
        expression={"$let": {"vars": {"x": {"a": {"b": {"c": {"d": 1}}}}}, "in": "$$x"}},
        expected={"a": {"b": {"c": {"d": 1}}}},
        msg="Should preserve deeply nested document",
    ),
    # Numeric special values
    ExpressionTestCase(
        "infinity",
        expression={"$let": {"vars": {"x": FLOAT_INFINITY}, "in": "$$x"}},
        expected=FLOAT_INFINITY,
        msg="Should preserve Infinity",
    ),
    ExpressionTestCase(
        "neg_infinity",
        expression={"$let": {"vars": {"x": FLOAT_NEGATIVE_INFINITY}, "in": "$$x"}},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should preserve -Infinity",
    ),
    ExpressionTestCase(
        "decimal128_inf",
        expression={"$let": {"vars": {"x": DECIMAL128_INFINITY}, "in": "$$x"}},
        expected=DECIMAL128_INFINITY,
        msg="Should preserve Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "double_neg_zero",
        expression={"$let": {"vars": {"x": DOUBLE_NEGATIVE_ZERO}, "in": "$$x"}},
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="Should preserve -0.0",
    ),
    ExpressionTestCase(
        "decimal128_neg_zero",
        expression={"$let": {"vars": {"x": DECIMAL128_NEGATIVE_ZERO}, "in": "$$x"}},
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="Should preserve Decimal128 -0",
    ),
    ExpressionTestCase(
        "int32_max",
        expression={"$let": {"vars": {"x": INT32_MAX}, "in": "$$x"}},
        expected=INT32_MAX,
        msg="Should preserve INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_min",
        expression={"$let": {"vars": {"x": INT32_MIN}, "in": "$$x"}},
        expected=INT32_MIN,
        msg="Should preserve INT32_MIN",
    ),
    ExpressionTestCase(
        "int64_max",
        expression={"$let": {"vars": {"x": INT64_MAX}, "in": "$$x"}},
        expected=INT64_MAX,
        msg="Should preserve INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min",
        expression={"$let": {"vars": {"x": INT64_MIN}, "in": "$$x"}},
        expected=INT64_MIN,
        msg="Should preserve INT64_MIN",
    ),
    ExpressionTestCase(
        "double_near_max",
        expression={"$let": {"vars": {"x": DOUBLE_NEAR_MAX}, "in": "$$x"}},
        expected=DOUBLE_NEAR_MAX,
        msg="Should preserve DOUBLE_NEAR_MAX",
    ),
    ExpressionTestCase(
        "double_min_subnormal",
        expression={"$let": {"vars": {"x": DOUBLE_MIN_SUBNORMAL}, "in": "$$x"}},
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="Should preserve DOUBLE_MIN_SUBNORMAL",
    ),
    ExpressionTestCase(
        "double_min_neg_subnormal",
        expression={"$let": {"vars": {"x": DOUBLE_MIN_NEGATIVE_SUBNORMAL}, "in": "$$x"}},
        expected=DOUBLE_MIN_NEGATIVE_SUBNORMAL,
        msg="Should preserve DOUBLE_MIN_NEGATIVE_SUBNORMAL",
    ),
    ExpressionTestCase(
        "double_near_min",
        expression={"$let": {"vars": {"x": DOUBLE_NEAR_MIN}, "in": "$$x"}},
        expected=DOUBLE_NEAR_MIN,
        msg="Should preserve DOUBLE_NEAR_MIN",
    ),
    # Decimal128 precision
    ExpressionTestCase(
        "d128_max",
        expression={"$let": {"vars": {"x": DECIMAL128_MAX}, "in": "$$x"}},
        expected=DECIMAL128_MAX,
        msg="Should preserve DECIMAL128_MAX",
    ),
    ExpressionTestCase(
        "d128_min",
        expression={"$let": {"vars": {"x": DECIMAL128_MIN}, "in": "$$x"}},
        expected=DECIMAL128_MIN,
        msg="Should preserve DECIMAL128_MIN",
    ),
    ExpressionTestCase(
        "d128_min_positive",
        expression={"$let": {"vars": {"x": DECIMAL128_MIN_POSITIVE}, "in": "$$x"}},
        expected=DECIMAL128_MIN_POSITIVE,
        msg="Should preserve DECIMAL128_MIN_POSITIVE",
    ),
    ExpressionTestCase(
        "d128_small_exp",
        expression={"$let": {"vars": {"x": DECIMAL128_SMALL_EXPONENT}, "in": "$$x"}},
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="Should preserve DECIMAL128_SMALL_EXPONENT",
    ),
    ExpressionTestCase(
        "d128_large_exp",
        expression={"$let": {"vars": {"x": DECIMAL128_LARGE_EXPONENT}, "in": "$$x"}},
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="Should preserve DECIMAL128_LARGE_EXPONENT",
    ),
    ExpressionTestCase(
        "d128_high_precision",
        expression={
            "$let": {"vars": {"x": Decimal128("1.234567890123456789012345678901234")}, "in": "$$x"}
        },
        expected=Decimal128("1.234567890123456789012345678901234"),
        msg="Should preserve 34-digit precision",
    ),
    ExpressionTestCase(
        "d128_neg_zero_exp",
        expression={"$let": {"vars": {"x": Decimal128("-0E+3")}, "in": "$$x"}},
        expected=Decimal128("-0E+3"),
        msg="Should preserve -0E+3 exponent",
    ),
    # BSON type distinction
    ExpressionTestCase(
        "false_not_zero",
        expression={"$let": {"vars": {"x": False}, "in": "$$x"}},
        expected=False,
        msg="Should return false (bool), not 0",
    ),
    ExpressionTestCase(
        "zero_not_false",
        expression={"$let": {"vars": {"x": 0}, "in": "$$x"}},
        expected=0,
        msg="Should return 0 (int), not false",
    ),
    ExpressionTestCase(
        "empty_string_not_null",
        expression={"$let": {"vars": {"x": ""}, "in": "$$x"}},
        expected="",
        msg="Should return empty string, not null",
    ),
    # Scoping basics
    ExpressionTestCase(
        "assignment_order",
        expression={"$let": {"vars": {"a": 1, "b": 2}, "in": {"$add": ["$$a", "$$b"]}}},
        expected=3,
        msg="Vars assignment order should not matter",
    ),
    ExpressionTestCase(
        "variable_reuse",
        expression={"$let": {"vars": {"x": 5}, "in": {"$add": ["$$x", "$$x", "$$x"]}}},
        expected=15,
        msg="All references should resolve to same value",
    ),
    ExpressionTestCase(
        "unused_variables",
        expression={"$let": {"vars": {"x": 1, "y": 2}, "in": 42}},
        expected=42,
        msg="Unused variables should not cause error",
    ),
    ExpressionTestCase(
        "literal_in",
        expression={"$let": {"vars": {"x": 1}, "in": "constant"}},
        expected="constant",
        msg="Literal in expression should return literal",
    ),
    ExpressionTestCase(
        "null_in",
        expression={"$let": {"vars": {"x": 1}, "in": None}},
        expected=None,
        msg="Null in expression should return null",
    ),
    ExpressionTestCase(
        "non_ascii_var_name",
        expression={"$let": {"vars": {"テスト": 42}, "in": "$$テスト"}},
        expected=42,
        msg="Should accept non-ASCII variable name",
    ),
    ExpressionTestCase(
        "vars_expr_operator",
        expression={"$let": {"vars": {"x": {"$add": [1, 2]}}, "in": "$$x"}},
        expected=3,
        msg="Should assign expression result to variable",
    ),
    # NaN
    ExpressionTestCase(
        "nan",
        expression={"$let": {"vars": {"x": FLOAT_NAN}, "in": "$$x"}},
        expected=pytest.approx(FLOAT_NAN, nan_ok=True),
        msg="Should preserve NaN",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$let": {"vars": {"x": DECIMAL128_NAN}, "in": "$$x"}},
        expected=DECIMAL128_NAN,
        msg="Should preserve Decimal128 NaN",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CORE_TESTS))
def test_let_core(collection, test):
    """Test $let core behavior: type passthrough, scoping, and expression types."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Insert-based tests
# ---------------------------------------------------------------------------
INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "vars_field_path",
        expression={"$let": {"vars": {"x": "$a"}, "in": "$$x"}},
        doc={"a": 7},
        expected=7,
        msg="Should assign field path value to variable",
    ),
    ExpressionTestCase(
        "vars_array_expr",
        expression={"$let": {"vars": {"x": ["$a", "$b"]}, "in": "$$x"}},
        doc={"a": 1, "b": 2},
        expected=[1, 2],
        msg="Should assign array of field refs to variable",
    ),
    ExpressionTestCase(
        "vars_object_expr",
        expression={"$let": {"vars": {"x": {"val": "$a"}}, "in": "$$x"}},
        doc={"a": 5},
        expected={"val": 5},
        msg="Should assign object with field ref to variable",
    ),
    ExpressionTestCase(
        "in_sees_current",
        expression={"$let": {"vars": {"x": 1}, "in": "$$CURRENT.a"}},
        doc={"_id": 1, "a": 5},
        expected=5,
        msg="Should access $$CURRENT",
    ),
    ExpressionTestCase(
        "empty_vars_field",
        expression={"$let": {"vars": {}, "in": "$a"}},
        doc={"a": 42},
        expected=42,
        msg="Should return field value with empty vars",
    ),
    ExpressionTestCase(
        "variable_shadows_field",
        expression={"$let": {"vars": {"x": 999}, "in": "$$x"}},
        doc={"x": 100},
        expected=999,
        msg="$$x should return let value, not field",
    ),
    ExpressionTestCase(
        "field_and_variable_same_name",
        expression={"$let": {"vars": {"x": 1}, "in": {"$add": ["$x", "$$x"]}}},
        doc={"x": 100},
        expected=101,
        msg="$x=100 field + $$x=1 variable = 101",
    ),
    ExpressionTestCase(
        "root_full_doc",
        expression={"$let": {"vars": {"doc": "$$ROOT"}, "in": "$$doc"}},
        doc={"_id": 1, "a": 5},
        expected={"_id": 1, "a": 5},
        msg="Should return full document via $$ROOT variable",
    ),
    ExpressionTestCase(
        "root_nested_path",
        expression={"$let": {"vars": {"doc": "$$ROOT"}, "in": "$$doc.a"}},
        doc={"_id": 1, "a": 5},
        expected=5,
        msg="Should access nested path on $$ROOT variable",
    ),
    ExpressionTestCase(
        "vars_current_ref",
        expression={"$let": {"vars": {"doc": "$$CURRENT"}, "in": "$$doc.a"}},
        doc={"_id": 1, "a": 5},
        expected=5,
        msg="Should assign $$CURRENT to variable and access nested path",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INSERT_TESTS))
def test_let_insert(collection, test):
    """Test $let with inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
