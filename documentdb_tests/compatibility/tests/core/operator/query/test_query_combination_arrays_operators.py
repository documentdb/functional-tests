"""
Tests for $size, $all, and $elemMatch combined with logical, comparison,
element, and evaluation operators, including negation and error cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SIZE_COMBINATION_ARRAY_OPS_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="size_and_all_exact",
        filter={"a": {"$size": 2, "$all": ["a", "b"]}},
        doc=[
            {"_id": 1, "a": ["a", "b"]},
            {"_id": 2, "a": ["a", "b", "c"]},
            {"_id": 3, "a": ["a"]},
        ],
        expected=[{"_id": 1, "a": ["a", "b"]}],
        msg="$size 2 with $all ['a','b'] matches exact",
    ),
    QueryTestCase(
        id="size_larger_than_all",
        filter={"a": {"$size": 3, "$all": ["a", "b"]}},
        doc=[
            {"_id": 1, "a": ["a", "b", "c"]},
            {"_id": 2, "a": ["a", "b"]},
        ],
        expected=[{"_id": 1, "a": ["a", "b", "c"]}],
        msg="$size 3 with $all ['a','b'] matches size 3 containing both",
    ),
    QueryTestCase(
        id="size_and_elemmatch",
        filter={"a": {"$size": 1, "$elemMatch": {"$gt": 5}}},
        doc=[
            {"_id": 1, "a": [10]},
            {"_id": 2, "a": [3]},
            {"_id": 3, "a": [10, 20]},
        ],
        expected=[{"_id": 1, "a": [10]}],
        msg="$size 1 with $elemMatch {$gt: 5}",
    ),
]

SIZE_LOGICAL_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_size_2_matches_other_sizes",
        filter={"a": {"$not": {"$size": 2}}},
        doc=[
            {"_id": 1, "a": [1]},
            {"_id": 2, "a": [1, 2]},
            {"_id": 3, "a": [1, 2, 3]},
        ],
        expected=[{"_id": 1, "a": [1]}, {"_id": 3, "a": [1, 2, 3]}],
        msg="$not $size 2 matches arrays of size != 2",
    ),
    QueryTestCase(
        id="and_size_and_all",
        filter={"$and": [{"a": {"$size": 2}}, {"a": {"$all": ["a"]}}]},
        doc=[
            {"_id": 1, "a": ["a", "b"]},
            {"_id": 2, "a": ["c", "d"]},
            {"_id": 3, "a": ["a"]},
        ],
        expected=[{"_id": 1, "a": ["a", "b"]}],
        msg="$and with $size 2 and $all ['a']",
    ),
    QueryTestCase(
        id="or_size_1_or_2",
        filter={"$or": [{"a": {"$size": 1}}, {"a": {"$size": 2}}]},
        doc=[
            {"_id": 1, "a": [1]},
            {"_id": 2, "a": [1, 2]},
            {"_id": 3, "a": [1, 2, 3]},
        ],
        expected=[{"_id": 1, "a": [1]}, {"_id": 2, "a": [1, 2]}],
        msg="$or with $size 1 or $size 2",
    ),
    QueryTestCase(
        id="nor_size_0",
        filter={"$nor": [{"a": {"$size": 0}}]},
        doc=[
            {"_id": 1, "a": []},
            {"_id": 2, "a": [1]},
            {"_id": 3, "a": "x"},
            {"_id": 4, "b": 1},
        ],
        expected=[
            {"_id": 2, "a": [1]},
            {"_id": 3, "a": "x"},
            {"_id": 4, "b": 1},
        ],
        msg="$nor with $size 0",
    ),
    QueryTestCase(
        id="multi_field_size",
        filter={"a": {"$size": 2}, "b": {"$size": 1}},
        doc=[
            {"_id": 1, "a": [1, 2], "b": [3]},
            {"_id": 2, "a": [1, 2], "b": [3, 4]},
            {"_id": 3, "a": [1], "b": [3]},
        ],
        expected=[{"_id": 1, "a": [1, 2], "b": [3]}],
        msg="$size on multiple fields",
    ),
    QueryTestCase(
        id="and_contradictory_size",
        filter={"$and": [{"a": {"$size": 1}}, {"a": {"$size": 2}}]},
        doc=[
            {"_id": 1, "a": [1]},
            {"_id": 2, "a": [1, 2]},
        ],
        expected=[],
        msg="$and with contradictory $size values returns no matches",
    ),
]

SIZE_COMBINATION_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="size_and_exists",
        filter={"a": {"$size": 2, "$exists": True}},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "b": 1},
        ],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$size 2 with $exists true",
    ),
    QueryTestCase(
        id="size_and_ne_null",
        filter={"a": {"$size": 2, "$ne": None}},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": None},
        ],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$size 2 with $ne null",
    ),
    QueryTestCase(
        id="size_and_type_array",
        filter={"a": {"$size": 2, "$type": "array"}},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": "x"},
        ],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$size 2 with $type array (redundant but valid)",
    ),
    QueryTestCase(
        id="size_with_where",
        filter={"a": {"$size": 1}, "$where": "true"},
        doc=[
            {"_id": 1, "a": []},
            {"_id": 2, "a": [1]},
            {"_id": 3, "a": [1, 2]},
            {"_id": 4, "a": [1, 2, 3]},
        ],
        expected=[{"_id": 2, "a": [1]}],
        msg="$size 1 combined with $where 'true'",
    ),
]

ALL_SIZE_COMBINATION_TESTS = (
    SIZE_COMBINATION_ARRAY_OPS_TESTS
    + SIZE_LOGICAL_OPERATOR_TESTS
    + SIZE_COMBINATION_COMPARISON_TESTS
)


DOLLAR_ALL_CROSS_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="all_with_size",
        filter={"a": {"$all": ["x", "y"], "$size": 2}},
        doc=[
            {"_id": 1, "a": ["x", "y"]},
            {"_id": 2, "a": ["x", "y", "z"]},
            {"_id": 3, "a": ["x"]},
        ],
        expected=[{"_id": 1, "a": ["x", "y"]}],
        msg="$all combined with $size should require both conditions",
    ),
    QueryTestCase(
        id="all_with_nin",
        filter={"a": {"$all": ["x"], "$nin": ["y"]}},
        doc=[
            {"_id": 1, "a": ["x", "y"]},
            {"_id": 2, "a": ["x"]},
        ],
        expected=[{"_id": 2, "a": ["x"]}],
        msg="$all combined with $nin should require both conditions",
    ),
    QueryTestCase(
        id="all_with_type",
        filter={"a": {"$all": ["x"], "$type": "array"}},
        doc=[
            {"_id": 1, "a": ["x"]},
            {"_id": 2, "a": "x"},
        ],
        expected=[{"_id": 1, "a": ["x"]}],
        msg="$all combined with $type should require both conditions",
    ),
    QueryTestCase(
        id="all_with_exists",
        filter={"a": {"$all": ["x"], "$exists": True}},
        doc=[
            {"_id": 1, "a": ["x"]},
            {"_id": 2, "b": 1},
        ],
        expected=[{"_id": 1, "a": ["x"]}],
        msg="$all combined with $exists should require both conditions",
    ),
]

DOLLAR_ALL_LOGICAL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="all_in_and",
        filter={"$and": [{"a": {"$all": ["x", "y"]}}, {"b": 1}]},
        doc=[
            {"_id": 1, "a": ["x", "y"], "b": 1},
            {"_id": 2, "a": ["x", "y"], "b": 2},
        ],
        expected=[{"_id": 1, "a": ["x", "y"], "b": 1}],
        msg="$all in $and with conditions on other fields should work",
    ),
    QueryTestCase(
        id="all_in_or",
        filter={"$or": [{"a": {"$all": ["x", "y"]}}, {"b": 1}]},
        doc=[
            {"_id": 1, "a": ["x", "y"]},
            {"_id": 2, "a": ["z"], "b": 1},
            {"_id": 3, "a": ["z"]},
        ],
        expected=[{"_id": 1, "a": ["x", "y"]}, {"_id": 2, "a": ["z"], "b": 1}],
        msg="$all in $or with other conditions should work",
    ),
    QueryTestCase(
        id="all_nor",
        filter={"$nor": [{"a": {"$all": ["x", "y"]}}]},
        doc=[
            {"_id": 1, "a": ["x", "y"]},
            {"_id": 2, "a": ["x"]},
        ],
        expected=[{"_id": 2, "a": ["x"]}],
        msg="$nor with $all should exclude matching documents",
    ),
]

DOLLAR_ALL_NEGATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_all_excludes_matching",
        filter={"a": {"$not": {"$all": ["x", "y"]}}},
        doc=[
            {"_id": 1, "a": ["x", "y"]},
            {"_id": 2, "a": ["x"]},
            {"_id": 3, "a": ["z"]},
        ],
        expected=[{"_id": 2, "a": ["x"]}, {"_id": 3, "a": ["z"]}],
        msg="$not with $all should exclude docs containing both",
    ),
    QueryTestCase(
        id="not_all_includes_null",
        filter={"a": {"$not": {"$all": ["x"]}}},
        doc=[{"_id": 1, "a": ["x"]}, {"_id": 2, "a": None}],
        expected=[{"_id": 2, "a": None}],
        msg="$not with $all should include documents where field is null",
    ),
    QueryTestCase(
        id="not_all_includes_missing",
        filter={"a": {"$not": {"$all": ["x"]}}},
        doc=[{"_id": 1, "a": ["x"]}, {"_id": 2, "b": 1}],
        expected=[{"_id": 2, "b": 1}],
        msg="$not with $all should include documents where field is missing",
    ),
    QueryTestCase(
        id="not_all_containing_all_elements",
        filter={"a": {"$not": {"$all": ["x", "y"]}}},
        doc=[{"_id": 1, "a": ["x", "y"]}],
        expected=[],
        msg="$not with $all containing all array elements should return no documents",
    ),
    QueryTestCase(
        id="not_all_containing_nonexistent",
        filter={"a": {"$not": {"$all": ["z"]}}},
        doc=[{"_id": 1, "a": ["x", "y"]}],
        expected=[{"_id": 1, "a": ["x", "y"]}],
        msg="$not with $all containing non-existent element should return the document",
    ),
]

DOLLAR_ALL_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="all_with_in",
        filter={"a": {"$all": ["x", "y"], "$in": ["x", "z"]}},
        doc=[
            {"_id": 1, "a": ["x", "y"]},
            {"_id": 2, "a": ["x"]},
        ],
        expected=[{"_id": 1, "a": ["x", "y"]}],
        msg="$all with $in should require both conditions",
    ),
    QueryTestCase(
        id="all_with_gt",
        filter={"a": {"$all": [1, 2], "$gt": 0}},
        doc=[
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [1]},
        ],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$all with $gt should require both conditions",
    ),
    QueryTestCase(
        id="all_with_eq",
        filter={"a": {"$all": ["x"], "$eq": "x"}},
        doc=[{"_id": 1, "a": "x"}, {"_id": 2, "a": ["x", "y"]}],
        expected=[{"_id": 1, "a": "x"}, {"_id": 2, "a": ["x", "y"]}],
        msg="$all with $eq should require both conditions",
    ),
    QueryTestCase(
        id="all_with_ne",
        filter={"a": {"$all": ["x"], "$ne": "y"}},
        doc=[
            {"_id": 1, "a": ["x"]},
            {"_id": 2, "a": ["x", "y"]},
        ],
        expected=[{"_id": 1, "a": ["x"]}],
        msg="$all with $ne should require both conditions",
    ),
    QueryTestCase(
        id="all_with_gte",
        filter={"a": {"$all": [1, 2], "$gte": 1}},
        doc=[
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [1]},
        ],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$all with $gte should require both conditions",
    ),
    QueryTestCase(
        id="all_with_lt",
        filter={"a": {"$all": [1, 2], "$lt": 5}},
        doc=[
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [1]},
        ],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$all with $lt should require both conditions",
    ),
    QueryTestCase(
        id="all_with_lte",
        filter={"a": {"$all": [1, 2], "$lte": 2}},
        doc=[
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [1]},
        ],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$all with $lte should require both conditions",
    ),
]

DOLLAR_ALL_COMBINATION_TESTS = (
    DOLLAR_ALL_CROSS_OPERATOR_TESTS
    + DOLLAR_ALL_LOGICAL_TESTS
    + DOLLAR_ALL_NEGATION_TESTS
    + DOLLAR_ALL_COMPARISON_TESTS
)


ELEMMATCH_LOGICAL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="or_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$or": [{"x": 1}, {"y": 2}]}}},
        doc=[
            {"_id": 1, "a": [{"x": 1, "y": 0}]},
            {"_id": 2, "a": [{"x": 0, "y": 2}]},
            {"_id": 3, "a": [{"x": 0, "y": 0}]},
        ],
        expected=[
            {"_id": 1, "a": [{"x": 1, "y": 0}]},
            {"_id": 2, "a": [{"x": 0, "y": 2}]},
        ],
        msg="$or inside $elemMatch",
    ),
    QueryTestCase(
        id="implicit_and_multiple_conditions",
        filter={"a": {"$elemMatch": {"x": {"$gt": 1}, "y": {"$lt": 5}}}},
        doc=[
            {"_id": 1, "a": [{"x": 3, "y": 2}]},
            {"_id": 2, "a": [{"x": 0, "y": 2}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 3, "y": 2}]}],
        msg="Implicit $and via multiple conditions",
    ),
    QueryTestCase(
        id="explicit_and_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$and": [{"x": {"$gt": 1}}, {"y": {"$lt": 5}}]}}},
        doc=[
            {"_id": 1, "a": [{"x": 3, "y": 2}]},
            {"_id": 2, "a": [{"x": 0, "y": 2}]},
            {"_id": 3, "a": [{"x": 3, "y": 10}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 3, "y": 2}]}],
        msg="Explicit $and inside $elemMatch",
    ),
    QueryTestCase(
        id="not_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$not": {"$gt": 10}}}},
        doc=[
            {"_id": 1, "a": [5, 15]},
            {"_id": 2, "a": [20, 30]},
        ],
        expected=[{"_id": 1, "a": [5, 15]}],
        msg="$not inside $elemMatch — at least one element not > 10",
    ),
    QueryTestCase(
        id="nor_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$nor": [{"x": 1}, {"y": 2}]}}},
        doc=[
            {"_id": 1, "a": [{"x": 1, "y": 0}]},
            {"_id": 2, "a": [{"x": 0, "y": 0}]},
        ],
        expected=[{"_id": 2, "a": [{"x": 0, "y": 0}]}],
        msg="$nor inside $elemMatch",
    ),
    QueryTestCase(
        id="or_with_multiple_elemMatch_in",
        filter={
            "$or": [
                {"a": {"$elemMatch": {"$in": [1, 2]}}},
                {"a": {"$elemMatch": {"$in": [3, 4]}}},
            ]
        },
        doc=[
            {"_id": 1, "a": [1, 5]},
            {"_id": 2, "a": [3, 5]},
            {"_id": 3, "a": [5, 6]},
        ],
        expected=[
            {"_id": 1, "a": [1, 5]},
            {"_id": 2, "a": [3, 5]},
        ],
        msg="$or with multiple $elemMatch using $in",
    ),
]

ELEMMATCH_ELEMENT_EVAL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="exists_true_inside_elemMatch",
        filter={"a": {"$elemMatch": {"x": {"$exists": True}}}},
        doc=[
            {"_id": 1, "a": [{"x": 1}, {"y": 2}]},
            {"_id": 2, "a": [{"y": 2}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1}, {"y": 2}]}],
        msg="$exists:true inside $elemMatch",
    ),
    QueryTestCase(
        id="exists_false_inside_elemMatch",
        filter={"a": {"$elemMatch": {"x": {"$exists": False}}}},
        doc=[
            {"_id": 1, "a": [{"x": 1}, {"y": 2}]},
            {"_id": 2, "a": [{"x": 1}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1}, {"y": 2}]}],
        msg="$exists:false — at least one element without x",
    ),
    QueryTestCase(
        id="type_string_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$type": "string"}}},
        doc=[
            {"_id": 1, "a": ["hello", 1]},
            {"_id": 2, "a": [1, 2]},
        ],
        expected=[{"_id": 1, "a": ["hello", 1]}],
        msg="$type string inside $elemMatch",
    ),
    QueryTestCase(
        id="regex_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$regex": "^abc"}}},
        doc=[
            {"_id": 1, "a": ["abcdef", "xyz"]},
            {"_id": 2, "a": ["xyz", "def"]},
        ],
        expected=[{"_id": 1, "a": ["abcdef", "xyz"]}],
        msg="$regex inside $elemMatch",
    ),
    QueryTestCase(
        id="mod_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$mod": [3, 0]}}},
        doc=[{"_id": 1, "a": [6, 7]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [6, 7]}],
        msg="$mod inside $elemMatch",
    ),
]

ELEMMATCH_NEGATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_elemMatch_no_element_gt_5",
        filter={"a": {"$not": {"$elemMatch": {"$gt": 5}}}},
        doc=[
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [1, 7]},
        ],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$not $elemMatch matches docs where NO element > 5",
    ),
    QueryTestCase(
        id="not_elemMatch_includes_missing_field",
        filter={"a": {"$not": {"$elemMatch": {"$gt": 5}}}},
        doc=[{"_id": 1, "b": 1}, {"_id": 2, "a": [7]}],
        expected=[{"_id": 1, "b": 1}],
        msg="$not $elemMatch includes docs where field is missing",
    ),
    QueryTestCase(
        id="not_elemMatch_includes_null_field",
        filter={"a": {"$not": {"$elemMatch": {"$gt": 5}}}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": [7]}],
        expected=[{"_id": 1, "a": None}],
        msg="$not $elemMatch includes docs where field is null",
    ),
    QueryTestCase(
        id="not_elemMatch_includes_scalar_field",
        filter={"a": {"$not": {"$elemMatch": {"$gt": 5}}}},
        doc=[{"_id": 1, "a": 3}, {"_id": 2, "a": [7]}],
        expected=[{"_id": 1, "a": 3}],
        msg="$not $elemMatch includes docs where field is a scalar",
    ),
    QueryTestCase(
        id="nor_with_elemMatch",
        filter={"$nor": [{"a": {"$elemMatch": {"$gt": 5}}}]},
        doc=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": [1, 7]},
        ],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$nor with $elemMatch",
    ),
]

ALL_COMBINATION_TESTS = (
    ALL_SIZE_COMBINATION_TESTS
    + DOLLAR_ALL_COMBINATION_TESTS
    + ELEMMATCH_LOGICAL_TESTS
    + ELEMMATCH_ELEMENT_EVAL_TESTS
    + ELEMMATCH_NEGATION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_COMBINATION_TESTS))
def test_array_operator_combinations(collection, test):
    """Test $size, $all, and $elemMatch combined with other operators."""
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)


ELEMMATCH_RESTRICTED_OPERATOR_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="where_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$where": "true"}}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="$where inside $elemMatch should fail",
    ),
    QueryTestCase(
        id="text_inside_elemMatch",
        filter={"a": {"$elemMatch": {"$text": {"$search": "test"}}}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="$text inside $elemMatch should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ELEMMATCH_RESTRICTED_OPERATOR_ERROR_TESTS))
def test_query_combination_elemMatch_errors(collection, test):
    """Test error cases for restricted operators inside $elemMatch."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
    )
    assertFailureCode(result, test.error_code)
