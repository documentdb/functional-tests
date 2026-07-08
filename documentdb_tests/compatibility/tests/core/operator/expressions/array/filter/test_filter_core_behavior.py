"""
Core behavior tests for $filter expression.

Tests basic filtering, empty arrays, null propagation, custom 'as' variable,
various condition expressions, nested arrays, limit parameter, objects as
elements, and large arrays.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX

# Success: basic filtering
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "gt_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 3]}}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[4, 5],
        msg="$filter should keep elements greater than 3",
    ),
    ExpressionTestCase(
        "gte_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 3]}}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3, 4, 5],
        msg="$filter should keep elements >= 3",
    ),
    ExpressionTestCase(
        "lt_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$lt": ["$$this", 3]}}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[1, 2],
        msg="$filter should keep elements less than 3",
    ),
    ExpressionTestCase(
        "eq_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", 2]}}},
        doc={"arr": [1, 2, 3, 2, 1]},
        expected=[2, 2],
        msg="$filter should keep elements equal to 2",
    ),
    ExpressionTestCase(
        "ne_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$ne": ["$$this", 2]}}},
        doc={"arr": [1, 2, 3, 2, 1]},
        expected=[1, 3, 1],
        msg="$filter should keep elements not equal to 2",
    ),
    ExpressionTestCase(
        "none_match",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 100]}}},
        doc={"arr": [1, 2, 3]},
        expected=[],
        msg="$filter should return empty when none match",
    ),
    ExpressionTestCase(
        "string_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", "abcd"]}}},
        doc={"arr": ["abcd", "efgh", "abcd", "zyz"]},
        expected=["abcd", "abcd"],
        msg="$filter should filter strings abcd",
    ),
    ExpressionTestCase(
        "bool_cond_true",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="$filter literal true cond should keep all elements",
    ),
    ExpressionTestCase(
        "bool_cond_false",
        expression={"$filter": {"input": "$arr", "cond": False}},
        doc={"arr": [1, 2, 3]},
        expected=[],
        msg="$filter literal false cond should keep no elements",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 0]}}},
        doc={"arr": []},
        expected=[],
        msg="$filter should return empty array for empty input",
    ),
    ExpressionTestCase(
        "null_input",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 0]}}},
        doc={"arr": None},
        expected=None,
        msg="$filter should return null when input is null",
    ),
    ExpressionTestCase(
        "custom_as_var",
        expression={"$filter": {"input": "$arr", "as": "item", "cond": {"$gt": ["$$item", 3]}}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[4, 5],
        msg="$filter should use custom 'as' variable name",
    ),
    ExpressionTestCase(
        "single_element_match",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 0]}}},
        doc={"arr": [42]},
        expected=[42],
        msg="$filter should keep single matching element",
    ),
    ExpressionTestCase(
        "large_array_1000",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 500]}}},
        doc={"arr": list(range(1000))},
        expected=list(range(500, 1000)),
        msg="$filter should filter large array",
    ),
]

# Success: nested arrays (filter does not recurse)
NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_arrays_by_size",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": [{"$size": "$$this"}, 1]}}},
        doc={"arr": [[1, 2], [3, 4, 5], [], [6]]},
        expected=[[1, 2], [3, 4, 5]],
        msg="$filter should filter subarrays by size",
    ),
    ExpressionTestCase(
        "nested_arrays_identity",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [[1], [2], [3]]},
        expected=[[1], [2], [3]],
        msg="$filter should preserve nested arrays when all match",
    ),
]

# Success: elements with null
NULL_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "filter_out_nulls",
        expression={"$filter": {"input": "$arr", "cond": {"$ne": ["$$this", None]}}},
        doc={"arr": [1, None, 2, None, 3]},
        expected=[1, 2, 3],
        msg="$filter should filter out null elements",
    ),
    ExpressionTestCase(
        "keep_only_nulls",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", None]}}},
        doc={"arr": [1, None, 2, None]},
        expected=[None, None],
        msg="$filter should keep only null elements",
    ),
]

# Success: objects as elements
OBJECT_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "filter_objects_by_nested_field",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this.a.b", 2]}}},
        doc={"arr": [{"a": {"b": 1}}, {"a": {"b": 5}}, {"a": {"b": 3}}]},
        expected=[{"a": {"b": 5}}, {"a": {"b": 3}}],
        msg="$filter should filter objects by nested field",
    ),
    ExpressionTestCase(
        "duplicate_objects",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this.a", 1]}}},
        doc={"arr": [{"a": 1}, {"a": 1}, {"a": 2}]},
        expected=[{"a": 1}, {"a": 1}],
        msg="$filter should return all matching duplicate objects",
    ),
    ExpressionTestCase(
        "single_object_no_match",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this.a", 10]}}},
        doc={"arr": [{"a": 1}]},
        expected=[],
        msg="$filter should return empty array when single object does not match",
    ),
]

# Success: limit parameter
LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "limit_1",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": 1}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3],
        msg="$filter should return at most 1 matching element",
    ),
    ExpressionTestCase(
        "limit_2",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": 2}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3, 4],
        msg="$filter should return at most 2 matching elements",
    ),
    ExpressionTestCase(
        "limit_exceeds_matches",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 3]}, "limit": 10}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[4, 5],
        msg="$filter limit > matches should return all matches",
    ),
    ExpressionTestCase(
        "limit_on_empty",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": 5}},
        doc={"arr": []},
        expected=[],
        msg="$filter limit on empty array returns empty",
    ),
    ExpressionTestCase(
        "limit_with_none_matching",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 100]}, "limit": 2}},
        doc={"arr": [1, 2, 3]},
        expected=[],
        msg="$filter limit with no matches returns empty",
    ),
    ExpressionTestCase(
        "limit_long",
        expression={
            "$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": Int64(1)}
        },
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3],
        msg="$filter long limit should work",
    ),
    ExpressionTestCase(
        "limit_double_whole",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": 1.0}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3],
        msg="$filter whole-number double limit should work",
    ),
    ExpressionTestCase(
        "limit_decimal128",
        expression={
            "$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": Decimal128("1")}
        },
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3],
        msg="$filter decimal128 limit should work",
    ),
    ExpressionTestCase(
        "limit_with_duplicates",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", 2]}, "limit": 2}},
        doc={"arr": [2, 2, 2]},
        expected=[2, 2],
        msg="$filter limit 2 with duplicates returns first 2 matches",
    ),
    ExpressionTestCase(
        "limit_int32_max",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": INT32_MAX}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="$filter iNT32_MAX limit should return all matches",
    ),
    ExpressionTestCase(
        "limit_null",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": None}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="$filter null limit should return all matches",
    ),
    ExpressionTestCase(
        "limit_missing_field_ref",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": "$nonexistent"}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="$filter missing field reference for limit should return all matches",
    ),
]

# Success: type-based filtering
TYPE_FILTER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "filter_by_type",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": [{"$type": "$$this"}, "int"]}}},
        doc={"arr": [1, "two", True, None, [5], {"a": 1}]},
        expected=[1],
        msg="$filter should filter by BSON type",
    ),
    ExpressionTestCase(
        "filter_strings_only",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": [{"$type": "$$this"}, "string"]}}},
        doc={"arr": [1, "good", 2, "morning", True]},
        expected=["good", "morning"],
        msg="$filter should keep only string elements",
    ),
]

# Success: cond true or false
COND_FALSY_TRUTHY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "cond_nonzero_truthy",
        expression={"$filter": {"input": "$arr", "cond": "$$this"}},
        doc={"arr": [0, 1, 2, 0, 3]},
        expected=[1, 2, 3],
        msg="$filter non-zero values are truthy",
    ),
    ExpressionTestCase(
        "cond_null_falsy",
        expression={"$filter": {"input": "$arr", "cond": "$$this"}},
        doc={"arr": [1, None, 2, None]},
        expected=[1, 2],
        msg="$filter null is falsy",
    ),
    ExpressionTestCase(
        "cond_zero_falsy",
        expression={"$filter": {"input": "$arr", "cond": 0}},
        doc={"arr": [1, 2]},
        expected=[],
        msg="$filter 0 is falsy",
    ),
    ExpressionTestCase(
        "cond_empty_string_truthy",
        expression={"$filter": {"input": "$arr", "cond": ""}},
        doc={"arr": [1, 2]},
        expected=[1, 2],
        msg="$filter empty string is truthy in MongoDB",
    ),
    ExpressionTestCase(
        "cond_object_truthy",
        expression={"$filter": {"input": "$arr", "cond": {"x": 10}}},
        doc={"arr": [1, 2]},
        expected=[1, 2],
        msg="$filter object is truthy",
    ),
    ExpressionTestCase(
        "cond_empty_object_truthy",
        expression={"$filter": {"input": "$arr", "cond": {}}},
        doc={"arr": [1, 2]},
        expected=[1, 2],
        msg="$filter empty object is truthy",
    ),
    ExpressionTestCase(
        "cond_empty_array_truthy",
        expression={"$filter": {"input": "$arr", "cond": []}},
        doc={"arr": [1, 2]},
        expected=[1, 2],
        msg="$filter empty array is truthy",
    ),
]


# Success: type strict equality
TYPE_STRICT_EQUALITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_vs_zero",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", False]}}},
        doc={"arr": [False, 0, 1, True]},
        expected=[False],
        msg="$eq false should match only false, not 0",
    ),
    ExpressionTestCase(
        "true_vs_one",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", True]}}},
        doc={"arr": [True, 1, 0, False]},
        expected=[True],
        msg="$eq true should match only true, not 1",
    ),
    ExpressionTestCase(
        "empty_string_vs_null",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", ""]}}},
        doc={"arr": ["", None, "a"]},
        expected=[""],
        msg="$eq '' should match only empty string, not null",
    ),
    ExpressionTestCase(
        "null_vs_zero_false_empty_string",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", None]}}},
        doc={"arr": [None, 0, False, ""]},
        expected=[None],
        msg="$eq null should match only null, not 0, false, or empty string",
    ),
]

# Success: numeric equivalence
NUMERIC_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "numeric_equivalence_one",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", 1]}}},
        doc={"arr": [1, Int64(1), 1.0, Decimal128("1")]},
        expected=[1, Int64(1), 1.0, Decimal128("1")],
        msg="$filter all numeric representations of 1 should match",
    ),
    ExpressionTestCase(
        "numeric_equivalence_zero",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", 0]}}},
        doc={"arr": [0, Int64(0), 0.0, Decimal128("0")]},
        expected=[0, Int64(0), 0.0, Decimal128("0")],
        msg="$filter all numeric representations of 0 should match",
    ),
]

# Aggregate and test
ALL_TESTS = (
    BASIC_TESTS
    + NESTED_ARRAY_TESTS
    + NULL_ELEMENT_TESTS
    + OBJECT_ELEMENT_TESTS
    + LIMIT_TESTS
    + TYPE_FILTER_TESTS
    + COND_FALSY_TRUTHY_TESTS
    + TYPE_STRICT_EQUALITY_TESTS
    + NUMERIC_EQUIVALENCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_filter_insert(collection, test):
    """Test $filter with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
