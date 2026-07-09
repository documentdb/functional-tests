"""
Core behavior tests for $indexOfArray expression.

Tests basic search, not found, start/end index ranges, degenerate cases,
mixed types, and large arrays.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_NEGATIVE_ZERO, INT32_MAX

# Success: basic search — value found
BASIC_FOUND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "found_first",
        doc={"arr": [1, 2, 3], "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find first element at index 0",
    ),
    ExpressionTestCase(
        "found_middle",
        doc={"arr": [1, 2, 3], "search": 2},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find middle element at index 1",
    ),
    ExpressionTestCase(
        "found_last",
        doc={"arr": [1, 2, 3], "search": 3},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=2,
        msg="$indexOfArray should find last element at index 2",
    ),
    ExpressionTestCase(
        "found_string",
        doc={"arr": ["a", "b", "c"], "search": "b"},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find string in array",
    ),
    ExpressionTestCase(
        "found_bool_true",
        doc={"arr": [True, False], "search": True},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find true at index 0",
    ),
    ExpressionTestCase(
        "found_bool_false",
        doc={"arr": [True, False], "search": False},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find false at index 1",
    ),
    ExpressionTestCase(
        "found_null",
        doc={"arr": [None, 1, 2], "search": None},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find null at index 0",
    ),
    ExpressionTestCase(
        "found_nested_array",
        doc={"arr": [[1, 2], [3, 4]], "search": [3, 4]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find nested array",
    ),
    ExpressionTestCase(
        "found_object",
        doc={"arr": [{"a": 1}, {"b": 2}], "search": {"a": 1}},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find object in array",
    ),
    ExpressionTestCase(
        "found_single_element",
        doc={"arr": [42], "search": 42},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find value in single-element array",
    ),
    ExpressionTestCase(
        "first_occurrence",
        doc={"arr": [1, 2, 1, 2], "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should return first occurrence index",
    ),
    ExpressionTestCase(
        "duplicate_values",
        doc={"arr": [5, 5, 5], "search": 5},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should return first index for duplicates",
    ),
]

# Success: value not found → -1
NOT_FOUND_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "not_found_int",
        doc={"arr": [1, 2, 3], "search": 4},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for absent int",
    ),
    ExpressionTestCase(
        "not_found_string",
        doc={"arr": ["a", "b"], "search": "z"},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for absent string",
    ),
    ExpressionTestCase(
        "empty_array",
        doc={"arr": [], "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for empty array",
    ),
    ExpressionTestCase(
        "type_mismatch_search",
        doc={"arr": [1, 2, 3], "search": "1"},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for type mismatch",
    ),
    ExpressionTestCase(
        "bool_vs_int",
        doc={"arr": [1, 0], "search": True},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for bool vs int",
    ),
    ExpressionTestCase(
        "not_found_null",
        doc={"arr": [1, 2, 3], "search": None},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for null not in array",
    ),
    ExpressionTestCase(
        "not_found_partial_array",
        doc={"arr": [[1, 2], [3, 4]], "search": [1]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for partial array match",
    ),
    ExpressionTestCase(
        "not_found_partial_object",
        doc={"arr": [{"a": 1, "b": 2}], "search": {"a": 1}},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for partial object match",
    ),
]

# Success: with start index
START_INDEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "start_skips_first",
        doc={"arr": [1, 2, 1, 2], "search": 1, "start": 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=2,
        msg="$indexOfArray should skip first match with start index",
    ),
    ExpressionTestCase(
        "start_at_match",
        doc={"arr": [10, 20, 30], "search": 20, "start": 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=1,
        msg="$indexOfArray should find at start index",
    ),
    ExpressionTestCase(
        "start_past_match",
        doc={"arr": [10, 20, 30], "search": 10, "start": 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=-1,
        msg="$indexOfArray should return -1 when start is past match",
    ),
    ExpressionTestCase(
        "start_at_zero",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=0,
        msg="$indexOfArray should find with start at zero",
    ),
    ExpressionTestCase(
        "start_beyond_array",
        doc={"arr": [1, 2, 3], "search": 1, "start": 20},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=-1,
        msg="$indexOfArray should return -1 when start beyond array",
    ),
    ExpressionTestCase(
        "start_int64",
        doc={"arr": [10, 20, 30], "search": 20, "start": Int64(1)},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=1,
        msg="$indexOfArray should accept Int64 start index",
    ),
    ExpressionTestCase(
        "start_double_integral",
        doc={"arr": [10, 20, 30], "search": 30, "start": 2.0},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=2,
        msg="$indexOfArray should accept integral double start index",
    ),
    ExpressionTestCase(
        "start_decimal128_integral",
        doc={"arr": [10, 20, 30], "search": 20, "start": Decimal128("1")},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=1,
        msg="$indexOfArray should accept Decimal128 start index",
    ),
    ExpressionTestCase(
        "start_decimal128_10E_neg1",
        doc={"arr": [10, 20, 30], "search": 20, "start": Decimal128("10E-1")},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=1,
        msg="$indexOfArray should accept Decimal128 10E-1 as start index 1",
    ),
    ExpressionTestCase(
        "end_decimal128_30E_neg1",
        doc={"arr": [10, 20, 30], "search": 20, "start": 0, "end": Decimal128("30E-1")},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=1,
        msg="$indexOfArray should accept Decimal128 30E-1 as end index 3",
    ),
]

# Success: with start and end index
START_END_INDEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "range_found",
        doc={"arr": ["a", "b", "c", "b"], "search": "b", "start": 1, "end": 3},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=1,
        msg="$indexOfArray should find in range",
    ),
    ExpressionTestCase(
        "range_not_found_exclusive_end",
        doc={"arr": ["a", "b", "c"], "search": "c", "start": 0, "end": 2},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=-1,
        msg="$indexOfArray should not find at exclusive end",
    ),
    ExpressionTestCase(
        "range_end_equals_start",
        doc={"arr": [1, 2, 3], "search": 1, "start": 0, "end": 0},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=-1,
        msg="$indexOfArray should return -1 when end equals start",
    ),
    ExpressionTestCase(
        "range_end_less_than_start",
        doc={"arr": ["a", "b", "c"], "search": "b", "start": 2, "end": 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=-1,
        msg="$indexOfArray should return -1 when end less than start",
    ),
    ExpressionTestCase(
        "range_end_beyond_array",
        doc={"arr": [1, 2, 3], "search": 3, "start": 0, "end": 100},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=2,
        msg="$indexOfArray should find when end beyond array",
    ),
    ExpressionTestCase(
        "range_full_array",
        doc={"arr": [1, 2, 3], "search": 2, "start": 0, "end": 3},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=1,
        msg="$indexOfArray should find in full array range",
    ),
    ExpressionTestCase(
        "range_int64_bounds",
        doc={"arr": [10, 20, 30], "search": 20, "start": Int64(0), "end": Int64(3)},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=1,
        msg="$indexOfArray should accept Int64 bounds",
    ),
    ExpressionTestCase(
        "range_double_integral_bounds",
        doc={"arr": [10, 20, 30], "search": 20, "start": 0.0, "end": 3.0},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=1,
        msg="$indexOfArray should accept integral double bounds",
    ),
    ExpressionTestCase(
        "range_decimal128_bounds",
        doc={
            "arr": [10, 20, 30],
            "search": 20,
            "start": Decimal128("0"),
            "end": Decimal128("3"),
        },
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=1,
        msg="$indexOfArray should accept Decimal128 bounds",
    ),
]

# Success: first occurrence from start with multiple duplicates
FIRST_FROM_START_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dup_skip_to_third_occurrence",
        doc={"arr": [5, 3, 5, 3, 5], "search": 5, "start": 3},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=4,
        msg="$indexOfArray should find third occurrence of 5 when start=3",
    ),
    ExpressionTestCase(
        "dup_skip_different_value",
        doc={"arr": [5, 3, 5, 3, 5], "search": 3, "start": 2},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=3,
        msg="$indexOfArray should find second 3 when start=2",
    ),
]

# Success: detailed range semantics
RANGE_SEMANTICS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "end_exclusive_includes_before_boundary",
        doc={"arr": ["a", "b", "c"], "search": "b", "start": 0, "end": 2},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=1,
        msg="$indexOfArray element before end boundary should be included in [0,2)",
    ),
    ExpressionTestCase(
        "end_exclusive_excludes_at_boundary",
        doc={"arr": ["a", "b", "c"], "search": "b", "start": 0, "end": 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=-1,
        msg="$indexOfArray element at end boundary should be excluded from [0,1)",
    ),
    ExpressionTestCase(
        "empty_range_at_array_length",
        doc={"arr": [1, 2, 3], "search": 3, "start": 3, "end": 3},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=-1,
        msg="$indexOfArray empty range [len,len) at array boundary should return -1",
    ),
    ExpressionTestCase(
        "range_finds_dup_in_subrange",
        doc={"arr": [1, 2, 3, 2, 1, 2, 3], "search": 2, "start": 2, "end": 4},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=3,
        msg="$indexOfArray should find value within range skipping earlier occurrences",
    ),
    ExpressionTestCase(
        "start_at_array_length",
        doc={"arr": ["a", "b", "c"], "search": "a", "start": 3},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=-1,
        msg="$indexOfArray should return -1 when start equals array length",
    ),
    ExpressionTestCase(
        "start_and_end_both_beyond_array",
        doc={"arr": ["a", "b", "c"], "search": "a", "start": 100, "end": 200},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=-1,
        msg="$indexOfArray should return -1 when both start and end are beyond array",
    ),
    ExpressionTestCase(
        "end_before_match_position",
        doc={"arr": ["a", "abc", "b"], "search": "b", "start": 0, "end": 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=-1,
        msg="$indexOfArray should return -1 when end is before the matching element",
    ),
]

# Success: degenerate and single-element edge cases
DEGENERATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_not_found",
        doc={"arr": [1], "search": 2},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 when single element doesn't match",
    ),
    ExpressionTestCase(
        "single_found_in_range",
        doc={"arr": [42], "search": 42, "start": 0, "end": 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=0,
        msg="$indexOfArray single element found in range [0,1)",
    ),
    ExpressionTestCase(
        "single_empty_range",
        doc={"arr": [42], "search": 42, "start": 0, "end": 0},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=-1,
        msg="$indexOfArray single element not found in empty range [0,0)",
    ),
    ExpressionTestCase(
        "single_start_past_element",
        doc={"arr": [42], "search": 42, "start": 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=-1,
        msg="$indexOfArray single element not found when start past it",
    ),
    ExpressionTestCase(
        "all_null_from_start",
        doc={"arr": [None, None, None], "search": None, "start": 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=1,
        msg="$indexOfArray should find null at index 1 from start=1 in all-null array",
    ),
    ExpressionTestCase(
        "all_null_search_different_type",
        doc={"arr": [None, None, None], "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should not find int in all-null array",
    ),
    ExpressionTestCase(
        "all_true_search_false",
        doc={"arr": [True, True, True], "search": False},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should not find false in all-true array",
    ),
]

# Success: mixed types in array
MIXED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_find_string",
        doc={"arr": [1, "2", True, None, [1]], "search": "2"},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find string in mixed array",
    ),
    ExpressionTestCase(
        "mixed_find_null",
        doc={"arr": [1, "2", True, None, [1]], "search": None},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=3,
        msg="$indexOfArray should find null in mixed array",
    ),
    ExpressionTestCase(
        "mixed_find_array",
        doc={"arr": [1, "2", True, None, [1]], "search": [1]},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=4,
        msg="$indexOfArray should find array in mixed array",
    ),
]

# Success: large array
LARGE_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_array_first",
        doc={"arr": list(range(20_000)), "search": 0},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find first in large array",
    ),
    ExpressionTestCase(
        "large_array_last",
        doc={"arr": list(range(20_000)), "search": 19_999},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=19_999,
        msg="$indexOfArray should find last in large array",
    ),
    ExpressionTestCase(
        "large_array_middle",
        doc={"arr": list(range(20_000)), "search": 10_000},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=10_000,
        msg="$indexOfArray should find middle in large array",
    ),
    ExpressionTestCase(
        "large_array_not_found",
        doc={"arr": list(range(20_000)), "search": -1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for absent value in large array",
    ),
    ExpressionTestCase(
        "large_array_with_start",
        doc={"arr": list(range(20_000)), "search": 19_999, "start": 19_998},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=19_999,
        msg="$indexOfArray should find with start in large array",
    ),
]

# Negative zero treated as equivalent to positive zero in search
NEGATIVE_ZERO_SEARCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "search_double_neg_zero_in_zeros",
        doc={"arr": [0, 1, 2], "search": -0.0},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find -0.0 at index of 0",
    ),
    ExpressionTestCase(
        "search_zero_finds_neg_zero",
        doc={"arr": [-0.0, 1, 2], "search": 0},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find 0 matching -0.0 in array",
    ),
    ExpressionTestCase(
        "search_decimal128_neg_zero",
        doc={"arr": [0, 1, 2], "search": Decimal128("-0")},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=0,
        msg="$indexOfArray should find Decimal128 -0 at index of 0",
    ),
]

# Boundary values for start/end indices
BOUNDARY_INDEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "start_int32_max",
        doc={"arr": [1, 2, 3], "search": 1, "start": INT32_MAX},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=-1,
        msg="$indexOfArray should return -1 with INT32_MAX start",
    ),
    ExpressionTestCase(
        "end_int32_max",
        doc={"arr": [1, 2, 3], "search": 2, "start": 0, "end": INT32_MAX},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=1,
        msg="$indexOfArray should find with INT32_MAX end",
    ),
    ExpressionTestCase(
        "start_and_end_int32_max",
        doc={"arr": [1, 2, 3], "search": 1, "start": INT32_MAX, "end": INT32_MAX},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
        expected=-1,
        msg="$indexOfArray should return -1 with both INT32_MAX",
    ),
    ExpressionTestCase(
        "start_int32_max_minus_1",
        doc={"arr": [1, 2, 3], "search": 1, "start": INT32_MAX - 1},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=-1,
        msg="$indexOfArray should return -1 with INT32_MAX-1 start",
    ),
]

# Negative zero as start/end index treated as 0
NEGATIVE_ZERO_INDEX_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_neg_zero_start",
        doc={"arr": [10, 20, 30], "search": 10, "start": -0.0},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=0,
        msg="$indexOfArray should treat -0.0 start as 0",
    ),
    ExpressionTestCase(
        "decimal128_neg_zero_start",
        doc={"arr": [10, 20, 30], "search": 10, "start": DECIMAL128_NEGATIVE_ZERO},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=0,
        msg="$indexOfArray should treat decimal128 -0 start as 0",
    ),
    ExpressionTestCase(
        "double_neg_zero_end",
        doc={"arr": [10, 20, 30], "search": 10, "start": 0, "end": -0.0},
        expression={"$indexOfArray": ["$arr", "$search", "$start", "$end"]},
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

# Property [Literal Evaluation]: $indexOfArray evaluates correctly with inline literal values.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "found_first",
        expression={"$indexOfArray": [[1, 2, 3], 1]},
        expected=0,
        msg="$indexOfArray should find first element at index 0",
    ),
    ExpressionTestCase(
        "not_found_int",
        expression={"$indexOfArray": [[1, 2, 3], 4]},
        expected=-1,
        msg="$indexOfArray should return -1 for absent int",
    ),
    ExpressionTestCase(
        "range_found",
        expression={"$indexOfArray": [["a", "b", "c", "b"], "b", 1, 3]},
        expected=1,
        msg="$indexOfArray should find in range",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_indexOfArray_literal(collection, test):
    """Test $indexOfArray with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_indexOfArray_insert(collection, test):
    """Test $indexOfArray with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
