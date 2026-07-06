"""
BSON type search and nested array tests for $indexOfArray expression.

Tests searching for various BSON types, numeric equivalence, and
complex nested mixed arrays.
"""

from datetime import datetime
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.indexOfArray.utils.indexOfArray_common import (  # noqa: E501
    IndexOfArrayTest,
    build_args,
    build_insert_args,
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

# ---------------------------------------------------------------------------
# Success: search for various BSON types
# ---------------------------------------------------------------------------
BSON_TYPE_SEARCH_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="search_int64",
        array=[Int64(99), 1],
        search=Int64(99),
        expected=0,
        msg="Should find Int64 value",
    ),
    IndexOfArrayTest(
        id="search_decimal128",
        array=[Decimal128("1.5"), 2],
        search=Decimal128("1.5"),
        expected=0,
        msg="Should find Decimal128 value",
    ),
    IndexOfArrayTest(
        id="search_datetime",
        array=[datetime(2024, 1, 1), 1],
        search=datetime(2024, 1, 1),
        expected=0,
        msg="Should find datetime value",
    ),
    IndexOfArrayTest(
        id="search_objectid",
        array=[ObjectId("000000000000000000000001"), 1],
        search=ObjectId("000000000000000000000001"),
        expected=0,
        msg="Should find ObjectId value",
    ),
    IndexOfArrayTest(
        id="search_binary",
        array=[Binary(b"\x01\x02", 0), 1],
        search=Binary(b"\x01\x02", 0),
        expected=0,
        msg="Should find Binary value",
    ),
    IndexOfArrayTest(
        id="search_regex",
        array=[Regex("^abc", "i"), 1],
        search=Regex("^abc", "i"),
        expected=0,
        msg="Should find Regex value",
    ),
    IndexOfArrayTest(
        id="search_timestamp",
        array=[Timestamp(1, 1), 1],
        search=Timestamp(1, 1),
        expected=0,
        msg="Should find Timestamp value",
    ),
    IndexOfArrayTest(
        id="search_minkey",
        array=[MinKey(), 1],
        search=MinKey(),
        expected=0,
        msg="Should find MinKey value",
    ),
    IndexOfArrayTest(
        id="search_maxkey",
        array=[1, MaxKey()],
        search=MaxKey(),
        expected=1,
        msg="Should find MaxKey value",
    ),
    IndexOfArrayTest(
        id="search_uuid",
        array=[Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")), 1],
        search=Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
        expected=0,
        msg="Should find UUID binary value",
    ),
    # Special float values
    IndexOfArrayTest(
        id="search_infinity",
        array=[FLOAT_INFINITY, 1],
        search=FLOAT_INFINITY,
        expected=0,
        msg="Should find Infinity",
    ),
    IndexOfArrayTest(
        id="search_neg_infinity",
        array=[FLOAT_NEGATIVE_INFINITY, 1],
        search=FLOAT_NEGATIVE_INFINITY,
        expected=0,
        msg="Should find -Infinity",
    ),
    IndexOfArrayTest(
        id="search_infinity_not_found",
        array=[1, 2, 3],
        search=FLOAT_INFINITY,
        expected=-1,
        msg="Should not find Infinity in regular array",
    ),
    # Special Decimal128 values
    IndexOfArrayTest(
        id="search_decimal128_infinity",
        array=[DECIMAL128_INFINITY, 1],
        search=DECIMAL128_INFINITY,
        expected=0,
        msg="Should find Decimal128 Infinity",
    ),
    IndexOfArrayTest(
        id="search_decimal128_neg_infinity",
        array=[DECIMAL128_NEGATIVE_INFINITY, 1],
        search=DECIMAL128_NEGATIVE_INFINITY,
        expected=0,
        msg="Should find Decimal128 -Infinity",
    ),
    # NaN equality: NaN == NaN in BSON comparison (unlike IEEE 754)
    IndexOfArrayTest(
        id="search_nan_found",
        array=[FLOAT_NAN, 1],
        search=FLOAT_NAN,
        expected=0,
        msg="Should find NaN (BSON equality)",
    ),
    IndexOfArrayTest(
        id="search_decimal128_nan_found",
        array=[DECIMAL128_NAN, 1],
        search=DECIMAL128_NAN,
        expected=0,
        msg="Should find Decimal128 NaN (BSON equality)",
    ),
    # Cross-type NaN matching
    IndexOfArrayTest(
        id="search_decimal128_nan_matches_float_nan",
        array=[FLOAT_NAN, 1],
        search=DECIMAL128_NAN,
        expected=0,
        msg="Decimal128 NaN should match float NaN cross-type",
    ),
    IndexOfArrayTest(
        id="search_decimal128_neg_nan_matches_nan",
        array=[DECIMAL128_NAN, 1],
        search=Decimal128("-NaN"),
        expected=0,
        msg="Decimal128 -NaN should match Decimal128 NaN",
    ),
]

# ---------------------------------------------------------------------------
# Success: numeric type equivalence in search
# ---------------------------------------------------------------------------
NUMERIC_EQUIVALENCE_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="int_matches_double",
        array=[1.0, 2.0],
        search=1,
        expected=0,
        msg="Should match int to double",
    ),
    IndexOfArrayTest(
        id="int_matches_long",
        array=[Int64(1), 2],
        search=1,
        expected=0,
        msg="Should match int to long",
    ),
    IndexOfArrayTest(
        id="int_matches_decimal128",
        array=[Decimal128("1"), 2],
        search=1,
        expected=0,
        msg="Should match int to decimal128",
    ),
    IndexOfArrayTest(
        id="double_matches_int",
        array=[1, 2],
        search=1.0,
        expected=0,
        msg="Should match double to int",
    ),
    IndexOfArrayTest(
        id="long_matches_int",
        array=[1, 2],
        search=Int64(1),
        expected=0,
        msg="Should match long to int",
    ),
    IndexOfArrayTest(
        id="decimal128_matches_int",
        array=[1, 2],
        search=Decimal128("1"),
        expected=0,
        msg="Should match decimal128 to int",
    ),
]

# ---------------------------------------------------------------------------
# Success: nested mixed arrays
# ---------------------------------------------------------------------------
NESTED_MIXED_ARRAY_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="nested_find_object_in_mixed",
        array=[1, "two", {"a": 1}, [3, 4], True],
        search={"a": 1},
        expected=2,
        msg="Should find object in mixed array",
    ),
    IndexOfArrayTest(
        id="nested_find_array_in_mixed",
        array=[1, "two", {"a": 1}, [3, 4], True],
        search=[3, 4],
        expected=3,
        msg="Should find array in mixed array",
    ),
    IndexOfArrayTest(
        id="nested_find_bool_in_mixed",
        array=[1, "two", {"a": 1}, [3, 4], True],
        search=True,
        expected=4,
        msg="Should find bool in mixed array",
    ),
    IndexOfArrayTest(
        id="nested_find_null_in_mixed",
        array=[1, None, "three", [4], {"b": 2}],
        search=None,
        expected=1,
        msg="Should find null in mixed array",
    ),
    IndexOfArrayTest(
        id="nested_find_deep_object",
        array=[[1, 2], {"a": {"b": 3}}, "x"],
        search={"a": {"b": 3}},
        expected=1,
        msg="Should find deep object",
    ),
    IndexOfArrayTest(
        id="nested_find_array_with_mixed_types",
        array=[1, [None, "a", 2], "b"],
        search=[None, "a", 2],
        expected=1,
        msg="Should find mixed-type subarray",
    ),
    IndexOfArrayTest(
        id="nested_find_empty_object_in_mixed",
        array=[1, {}, [2], "a"],
        search={},
        expected=1,
        msg="Should find empty object",
    ),
    IndexOfArrayTest(
        id="nested_find_empty_array_in_mixed",
        array=[1, {}, [], "a"],
        search=[],
        expected=2,
        msg="Should find empty array",
    ),
    IndexOfArrayTest(
        id="nested_find_datetime_in_mixed",
        array=["a", datetime(2024, 1, 1), 3, [4]],
        search=datetime(2024, 1, 1),
        expected=1,
        msg="Should find datetime in mixed array",
    ),
    IndexOfArrayTest(
        id="nested_find_objectid_in_mixed",
        array=[1, ObjectId("000000000000000000000001"), "x", [2]],
        search=ObjectId("000000000000000000000001"),
        expected=1,
        msg="Should find objectid in mixed array",
    ),
    IndexOfArrayTest(
        id="nested_find_decimal128_in_mixed",
        array=["a", [1], Decimal128("3.14"), None],
        search=Decimal128("3.14"),
        expected=2,
        msg="Should find decimal128 in mixed array",
    ),
    IndexOfArrayTest(
        id="nested_find_binary_in_mixed",
        array=[1, Binary(b"\x01\x02", 0), "x", [3]],
        search=Binary(b"\x01\x02", 0),
        expected=1,
        msg="Should find binary in mixed array",
    ),
    IndexOfArrayTest(
        id="nested_find_subarray_binary_decimal128",
        array=[1, [Binary(b"\x01\x02", 0), Decimal128("3.14")], "x", [3]],
        search=[Binary(b"\x01\x02", 0), Decimal128("3.14")],
        expected=1,
        msg="Should find subarray with binary and decimal128",
    ),
    IndexOfArrayTest(
        id="nested_find_subarray_object_array",
        array=["a", [{"k": 1}, [2, 3]], None, 4],
        search=[{"k": 1}, [2, 3]],
        expected=1,
        msg="Should find subarray with object and array",
    ),
    IndexOfArrayTest(
        id="nested_find_subarray_null_bool_int",
        array=[[None, True, 42], "x", 1],
        search=[None, True, 42],
        expected=0,
        msg="Should find subarray with null bool int",
    ),
    IndexOfArrayTest(
        id="nested_find_subarray_datetime_objectid",
        array=[0, [datetime(2024, 1, 1), ObjectId("000000000000000000000001")], "end"],
        search=[datetime(2024, 1, 1), ObjectId("000000000000000000000001")],
        expected=1,
        msg="Should find subarray with datetime and objectid",
    ),
    IndexOfArrayTest(
        id="nested_find_subarray_minkey_maxkey",
        array=[[MinKey(), MaxKey()], 1, "a"],
        search=[MinKey(), MaxKey()],
        expected=0,
        msg="Should find subarray with minkey and maxkey",
    ),
    IndexOfArrayTest(
        id="nested_3_levels_deep",
        array=[1, [[2, 3], [4, 5]], "end"],
        search=[[2, 3], [4, 5]],
        expected=1,
        msg="Should find 3-level nested array",
    ),
    IndexOfArrayTest(
        id="nested_4_levels_deep",
        array=["a", [[[1, 2], 3], 4], None],
        search=[[[1, 2], 3], 4],
        expected=1,
        msg="Should find 4-level nested array",
    ),
    IndexOfArrayTest(
        id="nested_deep_mixed_bson",
        array=[0, [[MinKey(), {"a": [Decimal128("1.5")]}], True], "x"],
        search=[[MinKey(), {"a": [Decimal128("1.5")]}], True],
        expected=1,
        msg="Should find deeply nested mixed BSON",
    ),
    IndexOfArrayTest(
        id="nested_inner_not_outer",
        array=[[1, [2, 3]], [2, 3], 4],
        search=[2, 3],
        expected=1,
        msg="Should find inner array match",
    ),
    IndexOfArrayTest(
        id="nested_5_levels_deep",
        array=[[[[[99]]]], "other"],
        search=[[[[99]]]],
        expected=0,
        msg="Should find 5-level nested array",
    ),
    IndexOfArrayTest(
        id="nested_deep_not_found",
        array=[[1, [2, 3]], [4, 5]],
        search=[2, 3],
        expected=-1,
        msg="Should not find array at wrong nesting level",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = BSON_TYPE_SEARCH_TESTS + NUMERIC_EQUIVALENCE_TESTS + NESTED_MIXED_ARRAY_TESTS

TEST_SUBSET_FOR_LITERAL = [
    BSON_TYPE_SEARCH_TESTS[0],  # search_int64
    NUMERIC_EQUIVALENCE_TESTS[0],  # int_matches_double
    NESTED_MIXED_ARRAY_TESTS[0],  # nested_find_object_in_mixed
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_indexOfArray_literal(collection, test):
    """Test $indexOfArray BSON types with literal values."""
    result = execute_expression(collection, {"$indexOfArray": build_args(test)})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_indexOfArray_insert(collection, test):
    """Test $indexOfArray BSON types with values from inserted documents."""
    args, doc = build_insert_args(test)
    result = execute_expression_with_insert(collection, {"$indexOfArray": args}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
