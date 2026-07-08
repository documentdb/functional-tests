"""
Core behavior tests for $indexOfArray expression.

Tests basic search, not found, start/end index ranges, degenerate cases,
mixed types, and large arrays.
"""

import pytest
from bson import Decimal128, Int64

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
from documentdb_tests.framework.test_constants import DECIMAL128_NEGATIVE_ZERO, INT32_MAX

# Success: basic search — value found
BASIC_FOUND_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "found_first",
        array=[1, 2, 3],
        search=1,
        expected=0,
        msg="$indexOfArray should find first element at index 0",
    ),
    IndexOfArrayTest(
        "found_middle",
        array=[1, 2, 3],
        search=2,
        expected=1,
        msg="$indexOfArray should find middle element at index 1",
    ),
    IndexOfArrayTest(
        "found_last",
        array=[1, 2, 3],
        search=3,
        expected=2,
        msg="$indexOfArray should find last element at index 2",
    ),
    IndexOfArrayTest(
        "found_string",
        array=["a", "b", "c"],
        search="b",
        expected=1,
        msg="$indexOfArray should find string in array",
    ),
    IndexOfArrayTest(
        "found_bool_true",
        array=[True, False],
        search=True,
        expected=0,
        msg="$indexOfArray should find true at index 0",
    ),
    IndexOfArrayTest(
        "found_bool_false",
        array=[True, False],
        search=False,
        expected=1,
        msg="$indexOfArray should find false at index 1",
    ),
    IndexOfArrayTest(
        "found_null",
        array=[None, 1, 2],
        search=None,
        expected=0,
        msg="$indexOfArray should find null at index 0",
    ),
    IndexOfArrayTest(
        "found_nested_array",
        array=[[1, 2], [3, 4]],
        search=[3, 4],
        expected=1,
        msg="$indexOfArray should find nested array",
    ),
    IndexOfArrayTest(
        "found_object",
        array=[{"a": 1}, {"b": 2}],
        search={"a": 1},
        expected=0,
        msg="$indexOfArray should find object in array",
    ),
    IndexOfArrayTest(
        "found_single_element",
        array=[42],
        search=42,
        expected=0,
        msg="$indexOfArray should find value in single-element array",
    ),
    IndexOfArrayTest(
        "first_occurrence",
        array=[1, 2, 1, 2],
        search=1,
        expected=0,
        msg="$indexOfArray should return first occurrence index",
    ),
    IndexOfArrayTest(
        "duplicate_values",
        array=[5, 5, 5],
        search=5,
        expected=0,
        msg="$indexOfArray should return first index for duplicates",
    ),
]

# Success: value not found → -1
NOT_FOUND_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "not_found_int",
        array=[1, 2, 3],
        search=4,
        expected=-1,
        msg="$indexOfArray should return -1 for absent int",
    ),
    IndexOfArrayTest(
        "not_found_string",
        array=["a", "b"],
        search="z",
        expected=-1,
        msg="$indexOfArray should return -1 for absent string",
    ),
    IndexOfArrayTest(
        "empty_array",
        array=[],
        search=1,
        expected=-1,
        msg="$indexOfArray should return -1 for empty array",
    ),
    IndexOfArrayTest(
        "type_mismatch_search",
        array=[1, 2, 3],
        search="1",
        expected=-1,
        msg="$indexOfArray should return -1 for type mismatch",
    ),
    IndexOfArrayTest(
        "bool_vs_int",
        array=[1, 0],
        search=True,
        expected=-1,
        msg="$indexOfArray should return -1 for bool vs int",
    ),
    IndexOfArrayTest(
        "not_found_null",
        array=[1, 2, 3],
        search=None,
        expected=-1,
        msg="$indexOfArray should return -1 for null not in array",
    ),
    IndexOfArrayTest(
        "not_found_partial_array",
        array=[[1, 2], [3, 4]],
        search=[1],
        expected=-1,
        msg="$indexOfArray should return -1 for partial array match",
    ),
    IndexOfArrayTest(
        "not_found_partial_object",
        array=[{"a": 1, "b": 2}],
        search={"a": 1},
        expected=-1,
        msg="$indexOfArray should return -1 for partial object match",
    ),
]

# Success: with start index
START_INDEX_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "start_skips_first",
        array=[1, 2, 1, 2],
        search=1,
        start=1,
        expected=2,
        msg="$indexOfArray should skip first match with start index",
    ),
    IndexOfArrayTest(
        "start_at_match",
        array=[10, 20, 30],
        search=20,
        start=1,
        expected=1,
        msg="$indexOfArray should find at start index",
    ),
    IndexOfArrayTest(
        "start_past_match",
        array=[10, 20, 30],
        search=10,
        start=1,
        expected=-1,
        msg="$indexOfArray should return -1 when start is past match",
    ),
    IndexOfArrayTest(
        "start_at_zero",
        array=[1, 2, 3],
        search=1,
        start=0,
        expected=0,
        msg="$indexOfArray should find with start at zero",
    ),
    IndexOfArrayTest(
        "start_beyond_array",
        array=[1, 2, 3],
        search=1,
        start=20,
        expected=-1,
        msg="$indexOfArray should return -1 when start beyond array",
    ),
    IndexOfArrayTest(
        "start_int64",
        array=[10, 20, 30],
        search=20,
        start=Int64(1),
        expected=1,
        msg="$indexOfArray should accept Int64 start index",
    ),
    IndexOfArrayTest(
        "start_double_integral",
        array=[10, 20, 30],
        search=30,
        start=2.0,
        expected=2,
        msg="$indexOfArray should accept integral double start index",
    ),
    IndexOfArrayTest(
        "start_decimal128_integral",
        array=[10, 20, 30],
        search=20,
        start=Decimal128("1"),
        expected=1,
        msg="$indexOfArray should accept Decimal128 start index",
    ),
    IndexOfArrayTest(
        "start_decimal128_10E_neg1",
        array=[10, 20, 30],
        search=20,
        start=Decimal128("10E-1"),
        expected=1,
        msg="$indexOfArray should accept Decimal128 10E-1 as start index 1",
    ),
    IndexOfArrayTest(
        "end_decimal128_30E_neg1",
        array=[10, 20, 30],
        search=20,
        start=0,
        end=Decimal128("30E-1"),
        expected=1,
        msg="$indexOfArray should accept Decimal128 30E-1 as end index 3",
    ),
]

# Success: with start and end index
START_END_INDEX_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "range_found",
        array=["a", "b", "c", "b"],
        search="b",
        start=1,
        end=3,
        expected=1,
        msg="$indexOfArray should find in range",
    ),
    IndexOfArrayTest(
        "range_not_found_exclusive_end",
        array=["a", "b", "c"],
        search="c",
        start=0,
        end=2,
        expected=-1,
        msg="$indexOfArray should not find at exclusive end",
    ),
    IndexOfArrayTest(
        "range_end_equals_start",
        array=[1, 2, 3],
        search=1,
        start=0,
        end=0,
        expected=-1,
        msg="$indexOfArray should return -1 when end equals start",
    ),
    IndexOfArrayTest(
        "range_end_less_than_start",
        array=["a", "b", "c"],
        search="b",
        start=2,
        end=1,
        expected=-1,
        msg="$indexOfArray should return -1 when end less than start",
    ),
    IndexOfArrayTest(
        "range_end_beyond_array",
        array=[1, 2, 3],
        search=3,
        start=0,
        end=100,
        expected=2,
        msg="$indexOfArray should find when end beyond array",
    ),
    IndexOfArrayTest(
        "range_full_array",
        array=[1, 2, 3],
        search=2,
        start=0,
        end=3,
        expected=1,
        msg="$indexOfArray should find in full array range",
    ),
    IndexOfArrayTest(
        "range_int64_bounds",
        array=[10, 20, 30],
        search=20,
        start=Int64(0),
        end=Int64(3),
        expected=1,
        msg="$indexOfArray should accept Int64 bounds",
    ),
    IndexOfArrayTest(
        "range_double_integral_bounds",
        array=[10, 20, 30],
        search=20,
        start=0.0,
        end=3.0,
        expected=1,
        msg="$indexOfArray should accept integral double bounds",
    ),
    IndexOfArrayTest(
        "range_decimal128_bounds",
        array=[10, 20, 30],
        search=20,
        start=Decimal128("0"),
        end=Decimal128("3"),
        expected=1,
        msg="$indexOfArray should accept Decimal128 bounds",
    ),
]

# Success: first occurrence from start with multiple duplicates
FIRST_FROM_START_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "dup_skip_to_third_occurrence",
        array=[5, 3, 5, 3, 5],
        search=5,
        start=3,
        expected=4,
        msg="$indexOfArray should find third occurrence of 5 when start=3",
    ),
    IndexOfArrayTest(
        "dup_skip_different_value",
        array=[5, 3, 5, 3, 5],
        search=3,
        start=2,
        expected=3,
        msg="$indexOfArray should find second 3 when start=2",
    ),
]

# Success: detailed range semantics
RANGE_SEMANTICS_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "end_exclusive_includes_before_boundary",
        array=["a", "b", "c"],
        search="b",
        start=0,
        end=2,
        expected=1,
        msg="$indexOfArray element before end boundary should be included in [0,2)",
    ),
    IndexOfArrayTest(
        "end_exclusive_excludes_at_boundary",
        array=["a", "b", "c"],
        search="b",
        start=0,
        end=1,
        expected=-1,
        msg="$indexOfArray element at end boundary should be excluded from [0,1)",
    ),
    IndexOfArrayTest(
        "empty_range_at_array_length",
        array=[1, 2, 3],
        search=3,
        start=3,
        end=3,
        expected=-1,
        msg="$indexOfArray empty range [len,len) at array boundary should return -1",
    ),
    IndexOfArrayTest(
        "range_finds_dup_in_subrange",
        array=[1, 2, 3, 2, 1, 2, 3],
        search=2,
        start=2,
        end=4,
        expected=3,
        msg="$indexOfArray should find value within range skipping earlier occurrences",
    ),
    IndexOfArrayTest(
        "start_at_array_length",
        array=["a", "b", "c"],
        search="a",
        start=3,
        expected=-1,
        msg="$indexOfArray should return -1 when start equals array length",
    ),
    IndexOfArrayTest(
        "start_and_end_both_beyond_array",
        array=["a", "b", "c"],
        search="a",
        start=100,
        end=200,
        expected=-1,
        msg="$indexOfArray should return -1 when both start and end are beyond array",
    ),
    IndexOfArrayTest(
        "end_before_match_position",
        array=["a", "abc", "b"],
        search="b",
        start=0,
        end=1,
        expected=-1,
        msg="$indexOfArray should return -1 when end is before the matching element",
    ),
]

# Success: degenerate and single-element edge cases
DEGENERATE_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "single_not_found",
        array=[1],
        search=2,
        expected=-1,
        msg="$indexOfArray should return -1 when single element doesn't match",
    ),
    IndexOfArrayTest(
        "single_found_in_range",
        array=[42],
        search=42,
        start=0,
        end=1,
        expected=0,
        msg="$indexOfArray single element found in range [0,1)",
    ),
    IndexOfArrayTest(
        "single_empty_range",
        array=[42],
        search=42,
        start=0,
        end=0,
        expected=-1,
        msg="$indexOfArray single element not found in empty range [0,0)",
    ),
    IndexOfArrayTest(
        "single_start_past_element",
        array=[42],
        search=42,
        start=1,
        expected=-1,
        msg="$indexOfArray single element not found when start past it",
    ),
    IndexOfArrayTest(
        "all_null_from_start",
        array=[None, None, None],
        search=None,
        start=1,
        expected=1,
        msg="$indexOfArray should find null at index 1 from start=1 in all-null array",
    ),
    IndexOfArrayTest(
        "all_null_search_different_type",
        array=[None, None, None],
        search=1,
        expected=-1,
        msg="$indexOfArray should not find int in all-null array",
    ),
    IndexOfArrayTest(
        "all_true_search_false",
        array=[True, True, True],
        search=False,
        expected=-1,
        msg="$indexOfArray should not find false in all-true array",
    ),
]

# Success: mixed types in array
MIXED_TYPE_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "mixed_find_string",
        array=[1, "2", True, None, [1]],
        search="2",
        expected=1,
        msg="$indexOfArray should find string in mixed array",
    ),
    IndexOfArrayTest(
        "mixed_find_null",
        array=[1, "2", True, None, [1]],
        search=None,
        expected=3,
        msg="$indexOfArray should find null in mixed array",
    ),
    IndexOfArrayTest(
        "mixed_find_array",
        array=[1, "2", True, None, [1]],
        search=[1],
        expected=4,
        msg="$indexOfArray should find array in mixed array",
    ),
]

# Success: large array

LARGE_ARRAY_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "large_array_first",
        array=list(range(20_000)),
        search=0,
        expected=0,
        msg="$indexOfArray should find first in large array",
    ),
    IndexOfArrayTest(
        "large_array_last",
        array=list(range(20_000)),
        search=19_999,
        expected=19_999,
        msg="$indexOfArray should find last in large array",
    ),
    IndexOfArrayTest(
        "large_array_middle",
        array=list(range(20_000)),
        search=10_000,
        expected=10_000,
        msg="$indexOfArray should find middle in large array",
    ),
    IndexOfArrayTest(
        "large_array_not_found",
        array=list(range(20_000)),
        search=-1,
        expected=-1,
        msg="$indexOfArray should return -1 for absent value in large array",
    ),
    IndexOfArrayTest(
        "large_array_with_start",
        array=list(range(20_000)),
        search=19_999,
        start=19_998,
        expected=19_999,
        msg="$indexOfArray should find with start in large array",
    ),
]

# Negative zero treated as equivalent to positive zero in search
NEGATIVE_ZERO_SEARCH_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "search_double_neg_zero_in_zeros",
        array=[0, 1, 2],
        search=-0.0,
        expected=0,
        msg="$indexOfArray should find -0.0 at index of 0",
    ),
    IndexOfArrayTest(
        "search_zero_finds_neg_zero",
        array=[-0.0, 1, 2],
        search=0,
        expected=0,
        msg="$indexOfArray should find 0 matching -0.0 in array",
    ),
    IndexOfArrayTest(
        "search_decimal128_neg_zero",
        array=[0, 1, 2],
        search=Decimal128("-0"),
        expected=0,
        msg="$indexOfArray should find Decimal128 -0 at index of 0",
    ),
]

# Boundary values for start/end indices
BOUNDARY_INDEX_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "start_int32_max",
        array=[1, 2, 3],
        search=1,
        start=INT32_MAX,
        expected=-1,
        msg="$indexOfArray should return -1 with INT32_MAX start",
    ),
    IndexOfArrayTest(
        "end_int32_max",
        array=[1, 2, 3],
        search=2,
        start=0,
        end=INT32_MAX,
        expected=1,
        msg="$indexOfArray should find with INT32_MAX end",
    ),
    IndexOfArrayTest(
        "start_and_end_int32_max",
        array=[1, 2, 3],
        search=1,
        start=INT32_MAX,
        end=INT32_MAX,
        expected=-1,
        msg="$indexOfArray should return -1 with both INT32_MAX",
    ),
    IndexOfArrayTest(
        "start_int32_max_minus_1",
        array=[1, 2, 3],
        search=1,
        start=INT32_MAX - 1,
        expected=-1,
        msg="$indexOfArray should return -1 with INT32_MAX-1 start",
    ),
]

# Negative zero as start/end index treated as 0
NEGATIVE_ZERO_INDEX_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        "double_neg_zero_start",
        array=[10, 20, 30],
        search=10,
        start=-0.0,
        expected=0,
        msg="$indexOfArray should treat -0.0 start as 0",
    ),
    IndexOfArrayTest(
        "decimal128_neg_zero_start",
        array=[10, 20, 30],
        search=10,
        start=DECIMAL128_NEGATIVE_ZERO,
        expected=0,
        msg="$indexOfArray should treat decimal128 -0 start as 0",
    ),
    IndexOfArrayTest(
        "double_neg_zero_end",
        array=[10, 20, 30],
        search=10,
        start=0,
        end=-0.0,
        expected=-1,
        msg="$indexOfArray should treat -0.0 end as 0",
    ),
]

# Aggregate and test
ALL_TESTS = (
    BASIC_FOUND_TESTS
    + NOT_FOUND_TESTS
    + START_INDEX_TESTS
    + START_END_INDEX_TESTS
    + FIRST_FROM_START_TESTS
    + RANGE_SEMANTICS_TESTS
    + DEGENERATE_TESTS
    + MIXED_TYPE_TESTS
    + LARGE_ARRAY_TESTS
    + NEGATIVE_ZERO_SEARCH_TESTS
    + BOUNDARY_INDEX_TESTS
    + NEGATIVE_ZERO_INDEX_TESTS
)

TEST_SUBSET_FOR_LITERAL = [
    BASIC_FOUND_TESTS[0],  # found_first
    NOT_FOUND_TESTS[0],  # not_found_int
    START_END_INDEX_TESTS[0],  # range_found
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_indexOfArray_literal(collection, test):
    """Test $indexOfArray with literal values."""
    result = execute_expression(collection, {"$indexOfArray": build_args(test)})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_indexOfArray_insert(collection, test):
    """Test $indexOfArray with values from inserted documents."""
    args, doc = build_insert_args(test)
    result = execute_expression_with_insert(collection, {"$indexOfArray": args}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
