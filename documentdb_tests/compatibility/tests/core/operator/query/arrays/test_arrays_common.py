"""
Tests for cross-operator interactions between array query operators.

Validates $all with $elemMatch sub-expressions including nested $elemMatch,
array operator combinations involving $elemMatch with $all and $size,
and error cases when mixing $elemMatch with plain values or regex in $all.
"""

import pytest
from bson import Regex

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ARRAY_OPERATOR_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="single_elemmatch",
        filter={"a": {"$all": [{"$elemMatch": {"x": 1, "y": 2}}]}},
        doc=[
            {"_id": 1, "a": [{"x": 1, "y": 2}]},
            {"_id": 2, "a": [{"x": 1, "y": 3}]},
            {"_id": 3, "a": [{"x": 1}, {"y": 2}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1, "y": 2}]}],
        msg="$all with single $elemMatch should match",
    ),
    QueryTestCase(
        id="multiple_elemmatch",
        filter={
            "a": {
                "$all": [
                    {"$elemMatch": {"x": 1, "y": 2}},
                    {"$elemMatch": {"x": 2, "y": 3}},
                ]
            }
        },
        doc=[
            {"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 2, "y": 3}]},
            {"_id": 2, "a": [{"x": 1, "y": 2}]},
            {"_id": 3, "a": [{"x": 1, "y": 2}, {"x": 2, "y": 1}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 2, "y": 3}]}],
        msg="$all with multiple $elemMatch should require all conditions met",
    ),
    QueryTestCase(
        id="nested_elemmatch_in_all",
        filter={"a": {"$all": [{"$elemMatch": {"b": {"$elemMatch": {"$gt": 5}}}}]}},
        doc=[
            {"_id": 1, "a": [{"b": [3, 7]}, {"b": [1]}]},
            {"_id": 2, "a": [{"b": [1, 2]}]},
        ],
        expected=[{"_id": 1, "a": [{"b": [3, 7]}, {"b": [1]}]}],
        msg="$all with $elemMatch containing nested $elemMatch",
    ),
    QueryTestCase(
        id="elemMatch_with_size",
        filter={"a": {"$elemMatch": {"$gt": 1}, "$size": 3}},
        doc=[
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [1, 2]},
            {"_id": 3, "a": [0, 0, 0]},
        ],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$elemMatch combined with $size",
    ),
    QueryTestCase(
        id="elemMatch_with_all",
        filter={"a": {"$elemMatch": {"$gt": 1}, "$all": [2, 3]}},
        doc=[
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [2, 3]},
            {"_id": 3, "a": [1, 2]},
        ],
        expected=[
            {"_id": 1, "a": [1, 2, 3]},
            {"_id": 2, "a": [2, 3]},
        ],
        msg="$elemMatch combined with $all",
    ),
    QueryTestCase(
        id="all_inside_elemMatch_embedded",
        filter={"a": {"$elemMatch": {"tags": {"$all": ["x", "y"]}}}},
        doc=[
            {"_id": 1, "a": [{"tags": ["x", "y", "z"]}]},
            {"_id": 2, "a": [{"tags": ["x"]}]},
        ],
        expected=[{"_id": 1, "a": [{"tags": ["x", "y", "z"]}]}],
        msg="$all inside $elemMatch on embedded doc tags field",
    ),
    QueryTestCase(
        id="size_inside_elemMatch_embedded",
        filter={"a": {"$elemMatch": {"arr": {"$size": 2}}}},
        doc=[
            {"_id": 1, "a": [{"arr": [1, 2]}, {"arr": [3]}]},
            {"_id": 2, "a": [{"arr": [1]}]},
        ],
        expected=[{"_id": 1, "a": [{"arr": [1, 2]}, {"arr": [3]}]}],
        msg="$size inside $elemMatch on embedded doc array field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_OPERATOR_COMBINATION_TESTS))
def test_array_operator_combinations(collection, test):
    """Test valid array operator combinations with $elemMatch."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)


ALL_MIXED_OPERAND_ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="mixed_elemmatch_and_value",
        filter={"a": {"$all": [{"$elemMatch": {"x": 1}}, "y"]}},
        doc=[{"_id": 1, "a": [{"x": 1}, "y"]}],
        error_code=BAD_VALUE_ERROR,
        msg="Mixed $elemMatch and plain values should produce error",
    ),
    QueryTestCase(
        id="all_mixed_plain_and_elemMatch",
        filter={"a": {"$all": [1, {"$elemMatch": {"x": 1}}]}},
        doc=[{"_id": 1, "a": [1]}],
        error_code=BAD_VALUE_ERROR,
        msg="$all with mixed plain value and $elemMatch should error",
    ),
    QueryTestCase(
        id="all_mixed_regex_and_elemMatch",
        filter={"a": {"$all": [Regex("^abc"), {"$elemMatch": {"x": 1}}]}},
        doc=[{"_id": 1, "a": ["abc"]}],
        error_code=BAD_VALUE_ERROR,
        msg="$all with mixed regex and $elemMatch should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_MIXED_OPERAND_ERROR_TESTS))
def test_array_operator_errors(collection, test):
    """Test error cases when mixing array operators."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
    )
    assertFailureCode(result, test.error_code)
