"""
BSON type search and nested array tests for $indexOfArray expression.

Tests searching for various BSON types, numeric equivalence, and
complex nested mixed arrays.
"""

from datetime import datetime, timezone
from uuid import UUID

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
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Success: search for various BSON types
BSON_TYPE_SEARCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "search_int64",
        doc={"arr": [Int64(99), 1], "search": Int64(99)},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Int64 value",
    ),
    ExpressionTestCase(
        "search_decimal128",
        doc={"arr": [Decimal128("1.5"), 2], "search": Decimal128("1.5")},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Decimal128 value",
    ),
    ExpressionTestCase(
        "search_datetime",
        doc={
            "arr": [datetime(2024, 1, 1, tzinfo=timezone.utc), 1],
            "search": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find datetime value",
    ),
    ExpressionTestCase(
        "search_objectid",
        doc={
            "arr": [ObjectId("000000000000000000000001"), 1],
            "search": ObjectId("000000000000000000000001"),
        },
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find ObjectId value",
    ),
    ExpressionTestCase(
        "search_binary",
        doc={"arr": [Binary(b"\x01\x02", 0), 1], "search": Binary(b"\x01\x02", 0)},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Binary value",
    ),
    ExpressionTestCase(
        "search_regex",
        doc={"arr": [Regex("^abc", "i"), 1], "search": Regex("^abc", "i")},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Regex value",
    ),
    ExpressionTestCase(
        "search_timestamp",
        doc={"arr": [Timestamp(1, 1), 1], "search": Timestamp(1, 1)},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Timestamp value",
    ),
    ExpressionTestCase(
        "search_minkey",
        doc={"arr": [MinKey(), 1], "search": MinKey()},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find MinKey value",
    ),
    ExpressionTestCase(
        "search_maxkey",
        doc={"arr": [1, MaxKey()], "search": MaxKey()},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find MaxKey value",
    ),
    ExpressionTestCase(
        "search_uuid",
        doc={
            "arr": [Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")), 1],
            "search": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
        },
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find UUID binary value",
    ),
    # Special float values
    ExpressionTestCase(
        "search_infinity",
        doc={"arr": [FLOAT_INFINITY, 1], "search": FLOAT_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Infinity",
    ),
    ExpressionTestCase(
        "search_neg_infinity",
        doc={"arr": [FLOAT_NEGATIVE_INFINITY, 1], "search": FLOAT_NEGATIVE_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find -Infinity",
    ),
    ExpressionTestCase(
        "search_infinity_not_found",
        doc={"arr": [1, 2, 3], "search": FLOAT_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should not find Infinity in regular array",
    ),
    # Special Decimal128 values
    ExpressionTestCase(
        "search_decimal128_infinity",
        doc={"arr": [DECIMAL128_INFINITY, 1], "search": DECIMAL128_INFINITY},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Decimal128 Infinity",
    ),
    ExpressionTestCase(
        "search_decimal128_neg_infinity",
        doc={
            "arr": [DECIMAL128_NEGATIVE_INFINITY, 1],
            "search": DECIMAL128_NEGATIVE_INFINITY,
        },
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Decimal128 -Infinity",
    ),
    # NaN equality: NaN == NaN in BSON comparison (unlike IEEE 754)
    ExpressionTestCase(
        "search_nan_found",
        doc={"arr": [FLOAT_NAN, 1], "search": FLOAT_NAN},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find NaN (BSON equality)",
    ),
    ExpressionTestCase(
        "search_decimal128_nan_found",
        doc={"arr": [DECIMAL128_NAN, 1], "search": DECIMAL128_NAN},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Decimal128 NaN (BSON equality)",
    ),
    # Cross-type NaN matching
    ExpressionTestCase(
        "search_decimal128_nan_matches_float_nan",
        doc={"arr": [FLOAT_NAN, 1], "search": DECIMAL128_NAN},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray decimal128 NaN should match float NaN cross-type",
    ),
    ExpressionTestCase(
        "search_decimal128_neg_nan_matches_nan",
        doc={"arr": [DECIMAL128_NAN, 1], "search": Decimal128("-NaN")},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray decimal128 -NaN should match Decimal128 NaN",
    ),
]

# Success: numeric type equivalence in search
NUMERIC_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_matches_double",
        doc={"arr": [1.0, 2.0], "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should match int to double",
    ),
    ExpressionTestCase(
        "int_matches_long",
        doc={"arr": [Int64(1), 2], "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should match int to long",
    ),
    ExpressionTestCase(
        "int_matches_decimal128",
        doc={"arr": [Decimal128("1"), 2], "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should match int to decimal128",
    ),
    ExpressionTestCase(
        "double_matches_int",
        doc={"arr": [1, 2], "search": 1.0},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should match double to int",
    ),
    ExpressionTestCase(
        "long_matches_int",
        doc={"arr": [1, 2], "search": Int64(1)},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should match long to int",
    ),
    ExpressionTestCase(
        "decimal128_matches_int",
        doc={"arr": [1, 2], "search": Decimal128("1")},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should match decimal128 to int",
    ),
]

# Success: nested mixed arrays
NESTED_MIXED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_find_object_in_mixed",
        doc={"arr": [1, "two", {"a": 1}, [3, 4], True], "search": {"a": 1}},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=2,
        msg="$indexOfArray should find object in mixed array",
    ),
    ExpressionTestCase(
        "nested_find_array_in_mixed",
        doc={"arr": [1, "two", {"a": 1}, [3, 4], True], "search": [3, 4]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=3,
        msg="$indexOfArray should find array in mixed array",
    ),
    ExpressionTestCase(
        "nested_find_bool_in_mixed",
        doc={"arr": [1, "two", {"a": 1}, [3, 4], True], "search": True},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=4,
        msg="$indexOfArray should find bool in mixed array",
    ),
    ExpressionTestCase(
        "nested_find_null_in_mixed",
        doc={"arr": [1, None, "three", [4], {"b": 2}], "search": None},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find null in mixed array",
    ),
    ExpressionTestCase(
        "nested_find_deep_object",
        doc={"arr": [[1, 2], {"a": {"b": 3}}, "x"], "search": {"a": {"b": 3}}},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find deep object",
    ),
    ExpressionTestCase(
        "nested_find_array_with_mixed_types",
        doc={"arr": [1, [None, "a", 2], "b"], "search": [None, "a", 2]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find mixed-type subarray",
    ),
    ExpressionTestCase(
        "nested_find_empty_object_in_mixed",
        doc={"arr": [1, {}, [2], "a"], "search": {}},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find empty object",
    ),
    ExpressionTestCase(
        "nested_find_empty_array_in_mixed",
        doc={"arr": [1, {}, [], "a"], "search": []},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=2,
        msg="$indexOfArray should find empty array",
    ),
    ExpressionTestCase(
        "nested_find_datetime_in_mixed",
        doc={
            "arr": ["a", datetime(2024, 1, 1, tzinfo=timezone.utc), 3, [4]],
            "search": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find datetime in mixed array",
    ),
    ExpressionTestCase(
        "nested_find_objectid_in_mixed",
        doc={
            "arr": [1, ObjectId("000000000000000000000001"), "x", [2]],
            "search": ObjectId("000000000000000000000001"),
        },
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find objectid in mixed array",
    ),
    ExpressionTestCase(
        "nested_find_decimal128_in_mixed",
        doc={"arr": ["a", [1], Decimal128("3.14"), None], "search": Decimal128("3.14")},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=2,
        msg="$indexOfArray should find decimal128 in mixed array",
    ),
    ExpressionTestCase(
        "nested_find_binary_in_mixed",
        doc={"arr": [1, Binary(b"\x01\x02", 0), "x", [3]], "search": Binary(b"\x01\x02", 0)},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find binary in mixed array",
    ),
    ExpressionTestCase(
        "nested_find_subarray_binary_decimal128",
        doc={
            "arr": [1, [Binary(b"\x01\x02", 0), Decimal128("3.14")], "x", [3]],
            "search": [Binary(b"\x01\x02", 0), Decimal128("3.14")],
        },
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find subarray with binary and decimal128",
    ),
    ExpressionTestCase(
        "nested_find_subarray_object_array",
        doc={"arr": ["a", [{"k": 1}, [2, 3]], None, 4], "search": [{"k": 1}, [2, 3]]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find subarray with object and array",
    ),
    ExpressionTestCase(
        "nested_find_subarray_null_bool_int",
        doc={"arr": [[None, True, 42], "x", 1], "search": [None, True, 42]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find subarray with null bool int",
    ),
    ExpressionTestCase(
        "nested_find_subarray_datetime_objectid",
        doc={
            "arr": [
                0,
                [
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                    ObjectId("000000000000000000000001"),
                ],
                "end",
            ],
            "search": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                ObjectId("000000000000000000000001"),
            ],
        },
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find subarray with datetime and objectid",
    ),
    ExpressionTestCase(
        "nested_find_subarray_minkey_maxkey",
        doc={"arr": [[MinKey(), MaxKey()], 1, "a"], "search": [MinKey(), MaxKey()]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find subarray with minkey and maxkey",
    ),
    ExpressionTestCase(
        "nested_3_levels_deep",
        doc={"arr": [1, [[2, 3], [4, 5]], "end"], "search": [[2, 3], [4, 5]]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find 3-level nested array",
    ),
    ExpressionTestCase(
        "nested_4_levels_deep",
        doc={"arr": ["a", [[[1, 2], 3], 4], None], "search": [[[1, 2], 3], 4]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find 4-level nested array",
    ),
    ExpressionTestCase(
        "nested_deep_mixed_bson",
        doc={
            "arr": [0, [[MinKey(), {"a": [Decimal128("1.5")]}], True], "x"],
            "search": [[MinKey(), {"a": [Decimal128("1.5")]}], True],
        },
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find deeply nested mixed BSON",
    ),
    ExpressionTestCase(
        "nested_inner_not_outer",
        doc={"arr": [[1, [2, 3]], [2, 3], 4], "search": [2, 3]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find inner array match",
    ),
    ExpressionTestCase(
        "nested_5_levels_deep",
        doc={"arr": [[[[[99]]]], "other"], "search": [[[[99]]]]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find 5-level nested array",
    ),
    ExpressionTestCase(
        "nested_deep_not_found",
        doc={"arr": [[1, [2, 3]], [4, 5]], "search": [2, 3]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should not find array at wrong nesting level",
    ),
]

# Aggregate and test
ALL_TESTS = BSON_TYPE_SEARCH_TESTS + NUMERIC_EQUIVALENCE_TESTS + NESTED_MIXED_ARRAY_TESTS

# Property [Literal Evaluation]: BSON type search with inline literal values.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "search_int64",
        expression={"$indexOfArray": [[Int64(99), 1], Int64(99)]},
        expected=0,
        msg="$indexOfArray should find Int64 value",
    ),
    ExpressionTestCase(
        "int_matches_double",
        expression={"$indexOfArray": [[1.0, 2.0], 1]},
        expected=0,
        msg="$indexOfArray should match int to double",
    ),
    ExpressionTestCase(
        "nested_find_object_in_mixed",
        expression={"$indexOfArray": [[1, "two", {"a": 1}, [3, 4], True], {"a": 1}]},
        expected=2,
        msg="$indexOfArray should find object in mixed array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_indexOfArray_literal(collection, test):
    """Test $indexOfArray BSON types with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_indexOfArray_insert(collection, test):
    """Test $indexOfArray BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
