"""
Tests for $and combined with other query operators.

Tests $and with $not, $regex, $type, $elemMatch, $all, $size, $exists, $expr.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="with_not",
        filter={"$and": [{"a": {"$not": {"$gt": 5}}}, {"b": 1}]},
        doc=[
            {"_id": 1, "a": 3, "b": 1},
            {"_id": 2, "a": 7, "b": 1},
            {"_id": 3, "a": 3, "b": 2},
        ],
        expected=[{"_id": 1, "a": 3, "b": 1}],
        msg="$and with $not matches docs where a <= 5 and b=1",
    ),
    QueryTestCase(
        id="with_regex",
        filter={"$and": [{"name": {"$regex": "^A"}}, {"age": {"$gt": 20}}]},
        doc=[
            {"_id": 1, "name": "Alice", "age": 30},
            {"_id": 2, "name": "Bob", "age": 25},
            {"_id": 3, "name": "Anna", "age": 15},
        ],
        expected=[{"_id": 1, "name": "Alice", "age": 30}],
        msg="$and with $regex matches docs with name starting with A and age > 20",
    ),
    QueryTestCase(
        id="with_type",
        filter={"$and": [{"val": {"$type": "int"}}, {"val": {"$gt": 0}}]},
        doc=[
            {"_id": 1, "val": 5},
            {"_id": 2, "val": -1},
            {"_id": 3, "val": "hello"},
        ],
        expected=[{"_id": 1, "val": 5}],
        msg="$and with $type matches docs where val is int and > 0",
    ),
    QueryTestCase(
        id="with_elemMatch",
        filter={"$and": [{"arr": {"$elemMatch": {"$gt": 1, "$lt": 5}}}, {"status": "A"}]},
        doc=[
            {"_id": 1, "arr": [1, 3, 7], "status": "A"},
            {"_id": 2, "arr": [1, 7, 9], "status": "A"},
            {"_id": 3, "arr": [1, 3, 7], "status": "B"},
        ],
        expected=[{"_id": 1, "arr": [1, 3, 7], "status": "A"}],
        msg="$and with $elemMatch matches docs with array element in range and status A",
    ),
    QueryTestCase(
        id="with_all",
        filter={"$and": [{"tags": {"$all": ["red", "blue"]}}, {"qty": {"$gt": 0}}]},
        doc=[
            {"_id": 1, "tags": ["red", "blue", "green"], "qty": 5},
            {"_id": 2, "tags": ["red", "green"], "qty": 5},
            {"_id": 3, "tags": ["red", "blue"], "qty": 0},
        ],
        expected=[{"_id": 1, "tags": ["red", "blue", "green"], "qty": 5}],
        msg="$and with $all matches docs with all tags and qty > 0",
    ),
    QueryTestCase(
        id="with_size",
        filter={"$and": [{"arr": {"$size": 3}}, {"status": "active"}]},
        doc=[
            {"_id": 1, "arr": [1, 2, 3], "status": "active"},
            {"_id": 2, "arr": [1, 2], "status": "active"},
            {"_id": 3, "arr": [1, 2, 3], "status": "inactive"},
        ],
        expected=[{"_id": 1, "arr": [1, 2, 3], "status": "active"}],
        msg="$and with $size matches docs with array of size 3 and active status",
    ),
    QueryTestCase(
        id="with_exists_both",
        filter={"$and": [{"a": {"$exists": True}}, {"b": {"$exists": True}}]},
        doc=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 1},
            {"_id": 3, "b": 2},
        ],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="$and with $exists on both fields matches only docs with both present",
    ),
    QueryTestCase(
        id="with_expr",
        filter={"$and": [{"$expr": {"$gt": ["$a", "$b"]}}, {"c": 1}]},
        doc=[
            {"_id": 1, "a": 5, "b": 3, "c": 1},
            {"_id": 2, "a": 1, "b": 3, "c": 1},
            {"_id": 3, "a": 5, "b": 3, "c": 2},
        ],
        expected=[{"_id": 1, "a": 5, "b": 3, "c": 1}],
        msg="$and with $expr matches doc where a > b and c=1",
    ),
    QueryTestCase(
        id="with_expr_no_match",
        filter={"$and": [{"$expr": {"$gt": ["$a", "$b"]}}, {"c": 99}]},
        doc=[
            {"_id": 1, "a": 5, "b": 3, "c": 1},
            {"_id": 2, "a": 1, "b": 3, "c": 1},
            {"_id": 3, "a": 5, "b": 3, "c": 2},
        ],
        expected=[],
        msg="$and with $expr and unsatisfied clause returns empty",
    ),
    QueryTestCase(
        id="with_expr_inside",
        filter={"$expr": {"$and": [{"$gt": ["$a", 0]}, {"$lt": ["$a", 10]}]}},
        doc=[
            {"_id": 1, "a": 5, "b": 3, "c": 1},
            {"_id": 2, "a": 1, "b": 3, "c": 1},
            {"_id": 3, "a": 5, "b": 3, "c": 2},
        ],
        expected=[
            {"_id": 1, "a": 5, "b": 3, "c": 1},
            {"_id": 2, "a": 1, "b": 3, "c": 1},
            {"_id": 3, "a": 5, "b": 3, "c": 2},
        ],
        msg="$and inside $expr matches all docs where 0 < a < 10",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_and_operator_combinations(collection, test):
    """Test $and combined with other query operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg)
