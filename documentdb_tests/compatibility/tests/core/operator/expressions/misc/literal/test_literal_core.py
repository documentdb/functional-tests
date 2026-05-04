"""
Core tests for $literal expression.

Covers BSON type passthrough, numeric special values, Decimal128 precision,
type distinction, argument formats, object/array passthrough, expression
suppression, field path suppression, and dollar-sign handling.
"""

import math
from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_TRAILING_ZERO,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
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
# Data type passthrough
# ---------------------------------------------------------------------------
DATA_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double", expression={"$literal": 2.5}, expected=2.5, msg="Should return double as-is"
    ),
    ExpressionTestCase(
        "int", expression={"$literal": 42}, expected=42, msg="Should return int as-is"
    ),
    ExpressionTestCase(
        "long",
        expression={"$literal": Int64(123456789)},
        expected=Int64(123456789),
        msg="Should return long as-is",
    ),
    ExpressionTestCase(
        "decimal128",
        expression={"$literal": Decimal128("1.23")},
        expected=Decimal128("1.23"),
        msg="Should return decimal128 as-is",
    ),
    ExpressionTestCase(
        "string",
        expression={"$literal": "hello"},
        expected="hello",
        msg="Should return string as-is",
    ),
    ExpressionTestCase(
        "bool_true", expression={"$literal": True}, expected=True, msg="Should return true as-is"
    ),
    ExpressionTestCase(
        "bool_false",
        expression={"$literal": False},
        expected=False,
        msg="Should return false as-is",
    ),
    ExpressionTestCase(
        "date",
        expression={"$literal": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expected=datetime(2024, 1, 1, tzinfo=timezone.utc),
        msg="Should return date as-is",
    ),
    ExpressionTestCase(
        "null", expression={"$literal": None}, expected=None, msg="Should return null as-is"
    ),
    ExpressionTestCase(
        "object",
        expression={"$literal": {"a": 1, "b": 2}},
        expected={"a": 1, "b": 2},
        msg="Should return object as-is",
    ),
    ExpressionTestCase(
        "array",
        expression={"$literal": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="Should return array as-is",
    ),
    ExpressionTestCase(
        "bindata",
        expression={"$literal": Binary(b"\x01\x02")},
        expected=b"\x01\x02",
        msg="Should return binData as-is",
    ),
    ExpressionTestCase(
        "objectid",
        expression={"$literal": ObjectId("000000000000000000000000")},
        expected=ObjectId("000000000000000000000000"),
        msg="Should return ObjectId as-is",
    ),
    ExpressionTestCase(
        "regex",
        expression={"$literal": Regex("^abc", "i")},
        expected=Regex("^abc", "i"),
        msg="Should return regex as-is",
    ),
    ExpressionTestCase(
        "javascript",
        expression={"$literal": Code("function(){}")},
        expected=Code("function(){}"),
        msg="Should return javascript as-is",
    ),
    ExpressionTestCase(
        "timestamp",
        expression={"$literal": Timestamp(1, 1)},
        expected=Timestamp(1, 1),
        msg="Should return timestamp as-is",
    ),
    ExpressionTestCase(
        "minkey",
        expression={"$literal": MinKey()},
        expected=MinKey(),
        msg="Should return MinKey as-is",
    ),
    ExpressionTestCase(
        "maxkey",
        expression={"$literal": MaxKey()},
        expected=MaxKey(),
        msg="Should return MaxKey as-is",
    ),
    ExpressionTestCase(
        "nan",
        expression={"$literal": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN",
    ),
    ExpressionTestCase(
        "inf",
        expression={"$literal": FLOAT_INFINITY},
        expected=FLOAT_INFINITY,
        msg="Should return Infinity",
    ),
    ExpressionTestCase(
        "neg_inf",
        expression={"$literal": FLOAT_NEGATIVE_INFINITY},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="Should return -Infinity",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        expression={"$literal": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="Should return Decimal128 NaN",
    ),
    ExpressionTestCase(
        "decimal128_inf",
        expression={"$literal": DECIMAL128_INFINITY},
        expected=DECIMAL128_INFINITY,
        msg="Should return Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "decimal128_neg_inf",
        expression={"$literal": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="Should return Decimal128 -Infinity",
    ),
    ExpressionTestCase(
        "neg_zero_double",
        expression={"$literal": DOUBLE_NEGATIVE_ZERO},
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="Should return -0.0",
    ),
    ExpressionTestCase(
        "decimal128_neg_zero",
        expression={"$literal": DECIMAL128_NEGATIVE_ZERO},
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="Should return Decimal128 -0",
    ),
    ExpressionTestCase(
        "int32_max",
        expression={"$literal": INT32_MAX},
        expected=INT32_MAX,
        msg="Should return INT32_MAX",
    ),
    ExpressionTestCase(
        "int32_min",
        expression={"$literal": INT32_MIN},
        expected=INT32_MIN,
        msg="Should return INT32_MIN",
    ),
    ExpressionTestCase(
        "int64_max",
        expression={"$literal": INT64_MAX},
        expected=INT64_MAX,
        msg="Should return INT64_MAX",
    ),
    ExpressionTestCase(
        "int64_min",
        expression={"$literal": INT64_MIN},
        expected=INT64_MIN,
        msg="Should return INT64_MIN",
    ),
    ExpressionTestCase(
        "double_near_max",
        expression={"$literal": DOUBLE_NEAR_MAX},
        expected=DOUBLE_NEAR_MAX,
        msg="Should return DOUBLE_NEAR_MAX",
    ),
    ExpressionTestCase(
        "double_min_subnormal",
        expression={"$literal": DOUBLE_MIN_SUBNORMAL},
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="Should return DOUBLE_MIN_SUBNORMAL",
    ),
    ExpressionTestCase(
        "d128_high_precision",
        expression={"$literal": Decimal128("1.234567890123456789012345678901234")},
        expected=Decimal128("1.234567890123456789012345678901234"),
        msg="Should preserve full precision",
    ),
    ExpressionTestCase(
        "d128_max",
        expression={"$literal": DECIMAL128_MAX},
        expected=DECIMAL128_MAX,
        msg="Should preserve DECIMAL128_MAX",
    ),
    ExpressionTestCase(
        "d128_min",
        expression={"$literal": DECIMAL128_MIN},
        expected=DECIMAL128_MIN,
        msg="Should preserve DECIMAL128_MIN",
    ),
    ExpressionTestCase(
        "d128_trailing_zero",
        expression={"$literal": DECIMAL128_TRAILING_ZERO},
        expected=DECIMAL128_TRAILING_ZERO,
        msg="Should preserve trailing zero",
    ),
    ExpressionTestCase(
        "d128_many_trailing_zeros",
        expression={"$literal": DECIMAL128_MANY_TRAILING_ZEROS},
        expected=DECIMAL128_MANY_TRAILING_ZEROS,
        msg="Should preserve many trailing zeros",
    ),
    ExpressionTestCase(
        "d128_min_positive",
        expression={"$literal": DECIMAL128_MIN_POSITIVE},
        expected=DECIMAL128_MIN_POSITIVE,
        msg="Should preserve DECIMAL128_MIN_POSITIVE",
    ),
    ExpressionTestCase(
        "d128_neg_zero_e_plus_3",
        expression={"$literal": Decimal128("-0E+3")},
        expected=Decimal128("-0E+3"),
        msg="Should preserve -0E+3 exponent",
    ),
    ExpressionTestCase(
        "false_not_zero",
        expression={"$literal": False},
        expected=False,
        msg="Should return false (bool), not 0",
    ),
    ExpressionTestCase(
        "zero_not_false",
        expression={"$literal": 0},
        expected=0,
        msg="Should return 0 (int), not false",
    ),
    ExpressionTestCase(
        "empty_string_not_null",
        expression={"$literal": ""},
        expected="",
        msg="Should return empty string, not null",
    ),
    ExpressionTestCase(
        "epoch",
        expression={"$literal": datetime(1970, 1, 1, tzinfo=timezone.utc)},
        expected=datetime(1970, 1, 1, tzinfo=timezone.utc),
        msg="Should return epoch date",
    ),
    ExpressionTestCase(
        "bindata_generic",
        expression={"$literal": Binary(b"\x01\x02\x03", 0)},
        expected=b"\x01\x02\x03",
        msg="Should return BinData subtype 0",
    ),
    ExpressionTestCase(
        "bindata_uuid",
        expression={
            "$literal": Binary(
                b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10", 4
            )
        },
        expected=Binary(b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10", 4),
        msg="Should return UUID BinData",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATA_TYPE_TESTS))
def test_literal_data_types(collection, test):
    """Test $literal returns all data types unchanged."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Argument formats and passthrough
# ---------------------------------------------------------------------------
ARGUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "flat_object",
        expression={"$literal": {"a": 1, "b": "hello", "c": True}},
        expected={"a": 1, "b": "hello", "c": True},
        msg="Should return flat object",
    ),
    ExpressionTestCase(
        "deeply_nested",
        expression={"$literal": {"a": {"b": {"c": {"d": 1}}}}},
        expected={"a": {"b": {"c": {"d": 1}}}},
        msg="Should return deeply nested object",
    ),
    ExpressionTestCase(
        "nested_arrays",
        expression={"$literal": {"arr": [[1, 2], [3, 4]]}},
        expected={"arr": [[1, 2], [3, 4]]},
        msg="Should return nested arrays in object",
    ),
    ExpressionTestCase(
        "nested_empty",
        expression={"$literal": {"a": {}, "b": [], "c": ""}},
        expected={"a": {}, "b": [], "c": ""},
        msg="Should return nested empty values",
    ),
    ExpressionTestCase(
        "dollar_and_int_array",
        expression={"$literal": ["$a", 1, "$b", 2]},
        expected=["$a", 1, "$b", 2],
        msg="Should return mixed dollar/int array",
    ),
    ExpressionTestCase(
        "array_of_objects",
        expression={"$literal": [{"val": "$x"}, {"val": "$y"}]},
        expected=[{"val": "$x"}, {"val": "$y"}],
        msg="Should return array of objects with dollar strings",
    ),
    ExpressionTestCase(
        "mixed_special_object",
        expression={"$literal": {"a": None, "b": MinKey(), "c": MaxKey(), "d": Timestamp(0, 0)}},
        expected={"a": None, "b": MinKey(), "c": MaxKey(), "d": Timestamp(0, 0)},
        msg="Should return object with special BSON values",
    ),
    ExpressionTestCase(
        "mixed_special_array",
        expression={"$literal": [None, MinKey(), MaxKey(), True, False, 0, "", []]},
        expected=[None, MinKey(), MaxKey(), True, False, 0, "", []],
        msg="Should return array with special BSON values",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARGUMENT_TESTS))
def test_literal_arguments(collection, test):
    """Test $literal accepts various argument formats and returns them unchanged."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Expression suppression
# ---------------------------------------------------------------------------
SUPPRESSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "add_not_evaluated",
        expression={"$literal": {"$add": [2, 3]}},
        expected={"$add": [2, 3]},
        msg="Should return {$add: [2, 3]} as document, not 5",
    ),
    ExpressionTestCase(
        "nested_literal",
        expression={"$literal": {"$literal": 1}},
        expected={"$literal": 1},
        msg="Should return {$literal: 1} as document",
    ),
    ExpressionTestCase(
        "double_nested_literal",
        expression={"$literal": {"$literal": {"$literal": 1}}},
        expected={"$literal": {"$literal": 1}},
        msg="Should return nested $literal as document",
    ),
    ExpressionTestCase(
        "dollar_price",
        expression={"$literal": "$price"},
        expected="$price",
        msg="Should return string '$price'",
    ),
    ExpressionTestCase(
        "dollar_nested_path",
        expression={"$literal": "$a.b"},
        expected="$a.b",
        msg="Should return string '$a.b'",
    ),
    ExpressionTestCase(
        "dollar_root",
        expression={"$literal": "$$ROOT"},
        expected="$$ROOT",
        msg="Should return string '$$ROOT'",
    ),
    ExpressionTestCase(
        "dollar_current",
        expression={"$literal": "$$CURRENT"},
        expected="$$CURRENT",
        msg="Should return string '$$CURRENT'",
    ),
    ExpressionTestCase(
        "dollar_remove",
        expression={"$literal": "$$REMOVE"},
        expected="$$REMOVE",
        msg="Should return string '$$REMOVE'",
    ),
    ExpressionTestCase(
        "dollar_nonexistent",
        expression={"$literal": "$nonexistent"},
        expected="$nonexistent",
        msg="Should return string '$nonexistent', not null",
    ),
    ExpressionTestCase(
        "match_obj",
        expression={"$literal": {"$match": {"x": 1}}},
        expected={"$match": {"x": 1}},
        msg="Should return $match object as-is",
    ),
    ExpressionTestCase(
        "group_obj",
        expression={"$literal": {"$group": {"_id": None}}},
        expected={"$group": {"_id": None}},
        msg="Should return $group object as-is",
    ),
    ExpressionTestCase(
        "unwind_obj",
        expression={"$literal": {"$unwind": "$arr"}},
        expected={"$unwind": "$arr"},
        msg="Should return $unwind object as-is",
    ),
    ExpressionTestCase(
        "type_obj",
        expression={"$literal": {"$type": "string"}},
        expected={"$type": "string"},
        msg="Should return $type object as-is",
    ),
    ExpressionTestCase(
        "dollar_string_array",
        expression={"$literal": ["$a", "$b", "$c"]},
        expected=["$a", "$b", "$c"],
        msg="Should return array of dollar strings",
    ),
    ExpressionTestCase(
        "expr_array",
        expression={"$literal": [{"$add": [1, 2]}, {"$subtract": [5, 3]}]},
        expected=[{"$add": [1, 2]}, {"$subtract": [5, 3]}],
        msg="Should return array of expression objects",
    ),
    ExpressionTestCase(
        "nested_dollar_obj",
        expression={"$literal": {"a": {"b": {"c": {"$add": [1, 2]}}}}},
        expected={"a": {"b": {"c": {"$add": [1, 2]}}}},
        msg="Should return nested $add unevaluated",
    ),
    ExpressionTestCase(
        "obj_dollar_string",
        expression={"$literal": {"val": "$field"}},
        expected={"val": "$field"},
        msg="Should return object with dollar string value",
    ),
    ExpressionTestCase(
        "embedded_dollar_field",
        expression={"$literal": {"a$b": 1}},
        expected={"a$b": 1},
        msg="Should return object with embedded dollar in field name",
    ),
    ExpressionTestCase(
        "consecutive_dollar_field",
        expression={"$literal": {"a$$b": 1}},
        expected={"a$$b": 1},
        msg="Should return object with consecutive dollars in field name",
    ),
    # System variable suppression
    ExpressionTestCase(
        "system_var_now",
        expression={"$literal": "$$NOW"},
        expected="$$NOW",
        msg="Should return string '$$NOW', not current date",
    ),
    ExpressionTestCase(
        "system_var_cluster_time",
        expression={"$literal": "$$CLUSTER_TIME"},
        expected="$$CLUSTER_TIME",
        msg="Should return string '$$CLUSTER_TIME', not timestamp",
    ),
    # Bare dollar-sign edge cases
    ExpressionTestCase(
        "bare_dollar",
        expression={"$literal": "$"},
        expected="$",
        msg="Should return bare '$' as-is",
    ),
    ExpressionTestCase(
        "bare_double_dollar",
        expression={"$literal": "$$"},
        expected="$$",
        msg="Should return '$$' as-is",
    ),
    ExpressionTestCase(
        "dollar_dot",
        expression={"$literal": "$."},
        expected="$.",
        msg="Should return '$.' as-is",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SUPPRESSION_TESTS))
def test_literal_suppression(collection, test):
    """Test $literal prevents evaluation of expressions and returns values as-is."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Large/complex values
# ---------------------------------------------------------------------------
def test_literal_large_array(collection):
    """Test $literal with a large array returns same array."""
    large_array = list(range(1000))
    result = execute_expression(collection, {"$literal": large_array})
    assert_expression_result(result, expected=large_array, msg="Should return 1000-element array")


def test_literal_deeply_nested_object(collection):
    """Test $literal with deeply nested object returns same object."""
    obj = {"val": 1}
    for _ in range(10):
        obj = {"nested": obj}
    result = execute_expression(collection, {"$literal": obj})
    assert_expression_result(result, expected=obj, msg="Should return 10-level nested object")


def test_literal_many_keys_object(collection):
    """Test $literal with object containing many keys returns same object."""
    obj = {f"key_{i}": i for i in range(100)}
    result = execute_expression(collection, {"$literal": obj})
    assert_expression_result(result, expected=obj, msg="Should return 100-key object")
