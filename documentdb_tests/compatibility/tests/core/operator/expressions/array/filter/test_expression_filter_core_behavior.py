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

# ---------------------------------------------------------------------------
# Success: basic filtering
# ---------------------------------------------------------------------------
BASIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="gt_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 3]}}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[4, 5],
        msg="Should keep elements greater than 3",
    ),
    ExpressionTestCase(
        id="gte_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 3]}}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3, 4, 5],
        msg="Should keep elements >= 3",
    ),
    ExpressionTestCase(
        id="lt_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$lt": ["$$this", 3]}}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[1, 2],
        msg="Should keep elements less than 3",
    ),
    ExpressionTestCase(
        id="eq_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", 2]}}},
        doc={"arr": [1, 2, 3, 2, 1]},
        expected=[2, 2],
        msg="Should keep elements equal to 2",
    ),
    ExpressionTestCase(
        id="ne_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$ne": ["$$this", 2]}}},
        doc={"arr": [1, 2, 3, 2, 1]},
        expected=[1, 3, 1],
        msg="Should keep elements not equal to 2",
    ),
    ExpressionTestCase(
        id="none_match",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 100]}}},
        doc={"arr": [1, 2, 3]},
        expected=[],
        msg="Should return empty when none match",
    ),
    ExpressionTestCase(
        id="string_filter",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", "abcd"]}}},
        doc={"arr": ["abcd", "efgh", "abcd", "zyz"]},
        expected=["abcd", "abcd"],
        msg="Should filter strings abcd",
    ),
    ExpressionTestCase(
        id="bool_cond_true",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="Literal true cond should keep all elements",
    ),
    ExpressionTestCase(
        id="bool_cond_false",
        expression={"$filter": {"input": "$arr", "cond": False}},
        doc={"arr": [1, 2, 3]},
        expected=[],
        msg="Literal false cond should keep no elements",
    ),
    ExpressionTestCase(
        id="empty_array",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 0]}}},
        doc={"arr": []},
        expected=[],
        msg="Should return empty array for empty input",
    ),
    ExpressionTestCase(
        id="null_input",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 0]}}},
        doc={"arr": None},
        expected=None,
        msg="Should return null when input is null",
    ),
    ExpressionTestCase(
        id="custom_as_var",
        expression={"$filter": {"input": "$arr", "as": "item", "cond": {"$gt": ["$$item", 3]}}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[4, 5],
        msg="Should use custom 'as' variable name",
    ),
    ExpressionTestCase(
        id="single_element_match",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 0]}}},
        doc={"arr": [42]},
        expected=[42],
        msg="Should keep single matching element",
    ),
    ExpressionTestCase(
        id="large_array_1000",
        expression={"$filter": {"input": "$arr", "cond": {"$gte": ["$$this", 500]}}},
        doc={"arr": list(range(1000))},
        expected=list(range(500, 1000)),
        msg="Should filter large array",
    ),
]

# ---------------------------------------------------------------------------
# Success: nested arrays (filter does not recurse)
# ---------------------------------------------------------------------------
NESTED_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_arrays_by_size",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": [{"$size": "$$this"}, 1]}}},
        doc={"arr": [[1, 2], [3, 4, 5], [], [6]]},
        expected=[[1, 2], [3, 4, 5]],
        msg="Should filter subarrays by size",
    ),
    ExpressionTestCase(
        id="nested_arrays_identity",
        expression={"$filter": {"input": "$arr", "cond": True}},
        doc={"arr": [[1], [2], [3]]},
        expected=[[1], [2], [3]],
        msg="Should preserve nested arrays when all match",
    ),
]

# ---------------------------------------------------------------------------
# Success: elements with null
# ---------------------------------------------------------------------------
NULL_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="filter_out_nulls",
        expression={"$filter": {"input": "$arr", "cond": {"$ne": ["$$this", None]}}},
        doc={"arr": [1, None, 2, None, 3]},
        expected=[1, 2, 3],
        msg="Should filter out null elements",
    ),
    ExpressionTestCase(
        id="keep_only_nulls",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", None]}}},
        doc={"arr": [1, None, 2, None]},
        expected=[None, None],
        msg="Should keep only null elements",
    ),
]

# ---------------------------------------------------------------------------
# Success: objects as elements
# ---------------------------------------------------------------------------
OBJECT_ELEMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="filter_objects_by_nested_field",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this.a.b", 2]}}},
        doc={"arr": [{"a": {"b": 1}}, {"a": {"b": 5}}, {"a": {"b": 3}}]},
        expected=[{"a": {"b": 5}}, {"a": {"b": 3}}],
        msg="Should filter objects by nested field",
    ),
    ExpressionTestCase(
        id="duplicate_objects",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this.a", 1]}}},
        doc={"arr": [{"a": 1}, {"a": 1}, {"a": 2}]},
        expected=[{"a": 1}, {"a": 1}],
        msg="Should return all matching duplicate objects",
    ),
    ExpressionTestCase(
        id="single_object_no_match",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this.a", 10]}}},
        doc={"arr": [{"a": 1}]},
        expected=[],
        msg="Should return empty array when single object does not match",
    ),
]

# ---------------------------------------------------------------------------
# Success: limit parameter
# ---------------------------------------------------------------------------
LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="limit_1",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": 1}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3],
        msg="Should return at most 1 matching element",
    ),
    ExpressionTestCase(
        id="limit_2",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": 2}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3, 4],
        msg="Should return at most 2 matching elements",
    ),
    ExpressionTestCase(
        id="limit_exceeds_matches",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 3]}, "limit": 10}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[4, 5],
        msg="Limit > matches should return all matches",
    ),
    ExpressionTestCase(
        id="limit_on_empty",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": 5}},
        doc={"arr": []},
        expected=[],
        msg="Limit on empty array returns empty",
    ),
    ExpressionTestCase(
        id="limit_with_none_matching",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 100]}, "limit": 2}},
        doc={"arr": [1, 2, 3]},
        expected=[],
        msg="Limit with no matches returns empty",
    ),
    ExpressionTestCase(
        id="limit_long",
        expression={
            "$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": Int64(1)}
        },
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3],
        msg="Long limit should work",
    ),
    ExpressionTestCase(
        id="limit_double_whole",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": 1.0}},
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3],
        msg="Whole-number double limit should work",
    ),
    ExpressionTestCase(
        id="limit_decimal128",
        expression={
            "$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 2]}, "limit": Decimal128("1")}
        },
        doc={"arr": [1, 2, 3, 4, 5]},
        expected=[3],
        msg="Decimal128 limit should work",
    ),
    ExpressionTestCase(
        id="limit_with_duplicates",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", 2]}, "limit": 2}},
        doc={"arr": [2, 2, 2]},
        expected=[2, 2],
        msg="Limit 2 with duplicates returns first 2 matches",
    ),
    ExpressionTestCase(
        id="limit_int32_max",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": INT32_MAX}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="INT32_MAX limit should return all matches",
    ),
    ExpressionTestCase(
        id="limit_null",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": None}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="Null limit should return all matches",
    ),
    ExpressionTestCase(
        id="limit_missing_field_ref",
        expression={"$filter": {"input": "$arr", "cond": True, "limit": "$nonexistent"}},
        doc={"arr": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="Missing field reference for limit should return all matches",
    ),
]

# ---------------------------------------------------------------------------
# Success: type-based filtering
# ---------------------------------------------------------------------------
TYPE_FILTER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="filter_by_type",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": [{"$type": "$$this"}, "int"]}}},
        doc={"arr": [1, "two", True, None, [5], {"a": 1}]},
        expected=[1],
        msg="Should filter by BSON type",
    ),
    ExpressionTestCase(
        id="filter_strings_only",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": [{"$type": "$$this"}, "string"]}}},
        doc={"arr": [1, "good", 2, "morning", True]},
        expected=["good", "morning"],
        msg="Should keep only string elements",
    ),
]

# ---------------------------------------------------------------------------
# Success: cond true or false
# ---------------------------------------------------------------------------
COND_FALSY_TRUTHY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="cond_nonzero_truthy",
        expression={"$filter": {"input": "$arr", "cond": "$$this"}},
        doc={"arr": [0, 1, 2, 0, 3]},
        expected=[1, 2, 3],
        msg="Non-zero values are truthy",
    ),
    ExpressionTestCase(
        id="cond_null_falsy",
        expression={"$filter": {"input": "$arr", "cond": "$$this"}},
        doc={"arr": [1, None, 2, None]},
        expected=[1, 2],
        msg="Null is falsy",
    ),
    ExpressionTestCase(
        id="cond_zero_falsy",
        expression={"$filter": {"input": "$arr", "cond": 0}},
        doc={"arr": [1, 2]},
        expected=[],
        msg="0 is falsy",
    ),
    ExpressionTestCase(
        id="cond_empty_string_truthy",
        expression={"$filter": {"input": "$arr", "cond": ""}},
        doc={"arr": [1, 2]},
        expected=[1, 2],
        msg="Empty string is truthy in MongoDB",
    ),
    ExpressionTestCase(
        id="cond_object_truthy",
        expression={"$filter": {"input": "$arr", "cond": {"x": 10}}},
        doc={"arr": [1, 2]},
        expected=[1, 2],
        msg="Object is truthy",
    ),
    ExpressionTestCase(
        id="cond_empty_object_truthy",
        expression={"$filter": {"input": "$arr", "cond": {}}},
        doc={"arr": [1, 2]},
        expected=[1, 2],
        msg="Empty object is truthy",
    ),
    ExpressionTestCase(
        id="cond_empty_array_truthy",
        expression={"$filter": {"input": "$arr", "cond": []}},
        doc={"arr": [1, 2]},
        expected=[1, 2],
        msg="Empty array is truthy",
    ),
]


# ---------------------------------------------------------------------------
# Success: type strict equality
# ---------------------------------------------------------------------------
TYPE_STRICT_EQUALITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="false_vs_zero",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", False]}}},
        doc={"arr": [False, 0, 1, True]},
        expected=[False],
        msg="$eq false should match only false, not 0",
    ),
    ExpressionTestCase(
        id="true_vs_one",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", True]}}},
        doc={"arr": [True, 1, 0, False]},
        expected=[True],
        msg="$eq true should match only true, not 1",
    ),
    ExpressionTestCase(
        id="empty_string_vs_null",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", ""]}}},
        doc={"arr": ["", None, "a"]},
        expected=[""],
        msg="$eq '' should match only empty string, not null",
    ),
    ExpressionTestCase(
        id="null_vs_zero_false_empty_string",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", None]}}},
        doc={"arr": [None, 0, False, ""]},
        expected=[None],
        msg="$eq null should match only null, not 0, false, or empty string",
    ),
]

# ---------------------------------------------------------------------------
# Success: numeric equivalence
# ---------------------------------------------------------------------------
NUMERIC_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="numeric_equivalence_one",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", 1]}}},
        doc={"arr": [1, Int64(1), 1.0, Decimal128("1")]},
        expected=[1, Int64(1), 1.0, Decimal128("1")],
        msg="All numeric representations of 1 should match",
    ),
    ExpressionTestCase(
        id="numeric_equivalence_zero",
        expression={"$filter": {"input": "$arr", "cond": {"$eq": ["$$this", 0]}}},
        doc={"arr": [0, Int64(0), 0.0, Decimal128("0")]},
        expected=[0, Int64(0), 0.0, Decimal128("0")],
        msg="All numeric representations of 0 should match",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
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
