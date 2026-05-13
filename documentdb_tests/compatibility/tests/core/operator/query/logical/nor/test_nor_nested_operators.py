"""
Tests for $nor query operator with nested operators.

Covers comparison operators, array operators, $regex, $type, $mod, $expr,
and nested logical operators ($and, $or, $not) within $nor expressions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

COMPARISON_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="with_gt",
        filter={"$nor": [{"val": {"$gt": 10}}]},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}],
        expected=[{"_id": 1, "val": 5}],
        msg="$nor with $gt should exclude docs where val > 10",
    ),
    QueryTestCase(
        id="with_gte",
        filter={"$nor": [{"val": {"$gte": 10}}]},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "val": 15}],
        expected=[{"_id": 1, "val": 5}],
        msg="$nor with $gte should exclude docs where val >= 10",
    ),
    QueryTestCase(
        id="with_lt",
        filter={"$nor": [{"val": {"$lt": 10}}]},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}],
        expected=[{"_id": 2, "val": 15}],
        msg="$nor with $lt should exclude docs where val < 10",
    ),
    QueryTestCase(
        id="with_lte",
        filter={"$nor": [{"val": {"$lte": 10}}]},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 10}, {"_id": 3, "val": 15}],
        expected=[{"_id": 3, "val": 15}],
        msg="$nor with $lte should exclude docs where val <= 10",
    ),
    QueryTestCase(
        id="with_in",
        filter={"$nor": [{"val": {"$in": [1, 2, 3]}}]},
        doc=[{"_id": 1, "val": 1}, {"_id": 2, "val": 4}],
        expected=[{"_id": 2, "val": 4}],
        msg="$nor with $in should exclude docs where val is in list",
    ),
    QueryTestCase(
        id="with_nin",
        filter={"$nor": [{"val": {"$nin": [1, 2, 3]}}]},
        doc=[{"_id": 1, "val": 1}, {"_id": 2, "val": 4}],
        expected=[{"_id": 1, "val": 1}],
        msg="$nor with $nin should exclude docs where val is NOT in list",
    ),
]

ARRAY_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="with_size",
        filter={"$nor": [{"arr": {"$size": 3}}]},
        doc=[{"_id": 1, "arr": [1, 2, 3]}, {"_id": 2, "arr": [1, 2]}],
        expected=[{"_id": 2, "arr": [1, 2]}],
        msg="$nor with $size should exclude docs where array has specified size",
    ),
    QueryTestCase(
        id="with_elemMatch",
        filter={"$nor": [{"arr": {"$elemMatch": {"$gt": 5}}}]},
        doc=[{"_id": 1, "arr": [1, 2, 3]}, {"_id": 2, "arr": [1, 10]}],
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="$nor with $elemMatch should exclude docs where any element matches",
    ),
    QueryTestCase(
        id="with_all",
        filter={"$nor": [{"arr": {"$all": [1, 2]}}]},
        doc=[{"_id": 1, "arr": [1, 2, 3]}, {"_id": 2, "arr": [1, 3]}],
        expected=[{"_id": 2, "arr": [1, 3]}],
        msg="$nor with $all should exclude docs where array contains all elements",
    ),
]

OTHER_OPERATOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="with_regex",
        filter={"$nor": [{"name": {"$regex": "^A"}}]},
        doc=[{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}],
        expected=[{"_id": 2, "name": "Bob"}],
        msg="$nor with $regex should exclude docs matching pattern",
    ),
    QueryTestCase(
        id="with_type",
        filter={"$nor": [{"val": {"$type": "string"}}]},
        doc=[{"_id": 1, "val": "hello"}, {"_id": 2, "val": 42}],
        expected=[{"_id": 2, "val": 42}],
        msg="$nor with $type should exclude docs where field is specified type",
    ),
    QueryTestCase(
        id="with_mod",
        filter={"$nor": [{"val": {"$mod": [2, 0]}}]},
        doc=[{"_id": 1, "val": 4}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$nor with $mod should exclude docs where val satisfies modulo",
    ),
    QueryTestCase(
        id="with_expr",
        filter={"$nor": [{"$expr": {"$gt": ["$a", "$b"]}}]},
        doc=[{"_id": 1, "a": 10, "b": 5}, {"_id": 2, "a": 3, "b": 7}],
        expected=[{"_id": 2, "a": 3, "b": 7}],
        msg="$nor with $expr should exclude docs where expression is true",
    ),
]

NESTED_LOGICAL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="containing_and",
        filter={"$nor": [{"$and": [{"a": 1}, {"b": 2}]}]},
        doc=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 1, "b": 1},
            {"_id": 3, "a": 2, "b": 2},
        ],
        expected=[{"_id": 2, "a": 1, "b": 1}, {"_id": 3, "a": 2, "b": 2}],
        msg="$nor containing $and should exclude docs matching the AND condition",
    ),
    QueryTestCase(
        id="containing_or",
        filter={"$nor": [{"$or": [{"a": 1}, {"b": 2}]}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 2, "b": 2},
            {"_id": 3, "a": 2, "b": 1},
        ],
        expected=[{"_id": 3, "a": 2, "b": 1}],
        msg="$nor containing $or should exclude docs matching any OR condition",
    ),
    QueryTestCase(
        id="containing_not",
        filter={"$nor": [{"val": {"$not": {"$gt": 10}}}]},
        doc=[{"_id": 1, "val": 5}, {"_id": 2, "val": 15}],
        expected=[{"_id": 2, "val": 15}],
        msg="$nor containing $not — double negation: excludes docs where val <= 10",
    ),
    QueryTestCase(
        id="nested_inside_and",
        filter={"$and": [{"$nor": [{"a": 1}]}, {"b": 2}]},
        doc=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 2, "b": 2},
            {"_id": 3, "a": 2, "b": 1},
        ],
        expected=[{"_id": 2, "a": 2, "b": 2}],
        msg="$nor nested inside $and should combine with other conditions",
    ),
    QueryTestCase(
        id="nested_inside_or",
        filter={"$or": [{"$nor": [{"a": 1}]}, {"b": 2}]},
        doc=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 2, "b": 1},
            {"_id": 3, "a": 1, "b": 1},
        ],
        expected=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 1}],
        msg="$nor nested inside $or should be one branch of the OR",
    ),
]

COMBINED_WITH_TOP_LEVEL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="combined_with_top_level_field",
        filter={"status": "active", "$nor": [{"priority": "low"}, {"age": {"$gt": 30}}]},
        doc=[
            {"_id": 1, "status": "active", "priority": "low", "age": 25},
            {"_id": 2, "status": "active", "priority": "high", "age": 35},
            {"_id": 3, "status": "active", "priority": "high", "age": 25},
            {"_id": 4, "status": "inactive", "priority": "high", "age": 25},
        ],
        expected=[{"_id": 3, "status": "active", "priority": "high", "age": 25}],
        msg="$nor combined with top-level field conditions should apply both",
    ),
]

ALL_TESTS = (
    COMPARISON_OPERATOR_TESTS
    + ARRAY_OPERATOR_TESTS
    + OTHER_OPERATOR_TESTS
    + NESTED_LOGICAL_TESTS
    + COMBINED_WITH_TOP_LEVEL_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_nested_operators(collection, test):
    """Test $nor query operator with nested operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
