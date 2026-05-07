"""
Tests for logical operators combined with other query operators.

Tests $and, $or, $nor, $not with $type, $elemMatch, $all, $size, $exists, $expr,
and combinations of logical operators with each other.
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
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


OR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="or_with_type",
        filter={"$or": [{"val": {"$type": "int"}}, {"val": {"$type": "string"}}]},
        doc=[
            {"_id": 1, "val": 5},
            {"_id": 2, "val": "hello"},
            {"_id": 3, "val": 3.14},
        ],
        expected=[{"_id": 1, "val": 5}, {"_id": 2, "val": "hello"}],
        msg="$or with $type matches docs of either type",
    ),
    QueryTestCase(
        id="or_with_elemMatch",
        filter={"$or": [{"arr": {"$elemMatch": {"$gt": 5}}}, {"status": "B"}]},
        doc=[
            {"_id": 1, "arr": [1, 2, 3], "status": "A"},
            {"_id": 2, "arr": [1, 7, 9], "status": "A"},
            {"_id": 3, "arr": [1, 2, 3], "status": "B"},
        ],
        expected=[
            {"_id": 2, "arr": [1, 7, 9], "status": "A"},
            {"_id": 3, "arr": [1, 2, 3], "status": "B"},
        ],
        msg="$or with $elemMatch matches docs with element > 5 or status B",
    ),
    QueryTestCase(
        id="or_with_all",
        filter={"$or": [{"tags": {"$all": ["red", "blue"]}}, {"qty": 0}]},
        doc=[
            {"_id": 1, "tags": ["red", "blue"], "qty": 5},
            {"_id": 2, "tags": ["red"], "qty": 0},
            {"_id": 3, "tags": ["green"], "qty": 3},
        ],
        expected=[
            {"_id": 1, "tags": ["red", "blue"], "qty": 5},
            {"_id": 2, "tags": ["red"], "qty": 0},
        ],
        msg="$or with $all matches docs with all tags or qty=0",
    ),
    QueryTestCase(
        id="or_with_size",
        filter={"$or": [{"arr": {"$size": 2}}, {"arr": {"$size": 3}}]},
        doc=[
            {"_id": 1, "arr": [1]},
            {"_id": 2, "arr": [1, 2]},
            {"_id": 3, "arr": [1, 2, 3]},
        ],
        expected=[{"_id": 2, "arr": [1, 2]}, {"_id": 3, "arr": [1, 2, 3]}],
        msg="$or with $size matches docs with array of size 2 or 3",
    ),
    QueryTestCase(
        id="or_with_exists",
        filter={"$or": [{"a": {"$exists": True}}, {"b": {"$exists": True}}]},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "b": 2},
            {"_id": 3, "c": 3},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "b": 2}],
        msg="$or with $exists matches docs with either field present",
    ),
    QueryTestCase(
        id="or_with_expr",
        filter={"$or": [{"$expr": {"$gt": ["$a", "$b"]}}, {"c": 2}]},
        doc=[
            {"_id": 1, "a": 5, "b": 3, "c": 1},
            {"_id": 2, "a": 1, "b": 3, "c": 2},
            {"_id": 3, "a": 1, "b": 3, "c": 1},
        ],
        expected=[{"_id": 1, "a": 5, "b": 3, "c": 1}, {"_id": 2, "a": 1, "b": 3, "c": 2}],
        msg="$or with $expr matches docs where a > b or c=2",
    ),
    QueryTestCase(
        id="or_with_not",
        filter={"$or": [{"a": {"$not": {"$gt": 2}}}, {"b": 3}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 3, "b": 3},
            {"_id": 3, "a": 5, "b": 1},
        ],
        expected=[{"_id": 1, "a": 1, "b": 1}, {"_id": 2, "a": 3, "b": 3}],
        msg="$or with $not matches docs where a <= 2 or b=3",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OR_TESTS))
def test_or_operator_combinations(collection, test):
    """Test $or combined with other query operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


NOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nor_with_type",
        filter={"$nor": [{"val": {"$type": "int"}}, {"val": {"$type": "string"}}]},
        doc=[
            {"_id": 1, "val": 5},
            {"_id": 2, "val": "hello"},
            {"_id": 3, "val": 3.14},
        ],
        expected=[{"_id": 3, "val": 3.14}],
        msg="$nor with $type excludes docs of either type",
    ),
    QueryTestCase(
        id="nor_with_elemMatch",
        filter={"$nor": [{"arr": {"$elemMatch": {"$gt": 5}}}]},
        doc=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [1, 7, 9]},
            {"_id": 3, "arr": [4, 5]},
        ],
        expected=[{"_id": 1, "arr": [1, 2, 3]}, {"_id": 3, "arr": [4, 5]}],
        msg="$nor with $elemMatch excludes docs with element > 5",
    ),
    QueryTestCase(
        id="nor_with_size",
        filter={"$nor": [{"arr": {"$size": 3}}]},
        doc=[
            {"_id": 1, "arr": [1, 2]},
            {"_id": 2, "arr": [1, 2, 3]},
            {"_id": 3, "arr": [1]},
        ],
        expected=[{"_id": 1, "arr": [1, 2]}, {"_id": 3, "arr": [1]}],
        msg="$nor with $size excludes docs with array of size 3",
    ),
    QueryTestCase(
        id="nor_with_exists",
        filter={"$nor": [{"a": {"$exists": True}}, {"b": {"$exists": True}}]},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "b": 2},
            {"_id": 3, "c": 3},
        ],
        expected=[{"_id": 3, "c": 3}],
        msg="$nor with $exists excludes docs with either field present",
    ),
    QueryTestCase(
        id="nor_with_expr",
        filter={"$nor": [{"$expr": {"$gt": ["$a", "$b"]}}]},
        doc=[
            {"_id": 1, "a": 5, "b": 3},
            {"_id": 2, "a": 1, "b": 3},
            {"_id": 3, "a": 3, "b": 3},
        ],
        expected=[{"_id": 2, "a": 1, "b": 3}, {"_id": 3, "a": 3, "b": 3}],
        msg="$nor with $expr excludes docs where a > b",
    ),
    QueryTestCase(
        id="nor_with_all",
        filter={"$nor": [{"tags": {"$all": ["red", "blue"]}}]},
        doc=[
            {"_id": 1, "tags": ["red", "blue", "green"]},
            {"_id": 2, "tags": ["red", "green"]},
            {"_id": 3, "tags": ["blue"]},
        ],
        expected=[{"_id": 2, "tags": ["red", "green"]}, {"_id": 3, "tags": ["blue"]}],
        msg="$nor with $all excludes docs containing all specified tags",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NOR_TESTS))
def test_nor_operator_combinations(collection, test):
    """Test $nor combined with other query operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


NOT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_with_type",
        filter={"val": {"$not": {"$type": "int"}}},
        doc=[
            {"_id": 1, "val": 5},
            {"_id": 2, "val": "hello"},
            {"_id": 3, "val": 3.14},
        ],
        expected=[{"_id": 2, "val": "hello"}, {"_id": 3, "val": 3.14}],
        msg="$not with $type matches docs where val is not int",
    ),
    QueryTestCase(
        id="not_with_elemMatch",
        filter={"arr": {"$not": {"$elemMatch": {"$gt": 5}}}},
        doc=[
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [1, 7, 9]},
            {"_id": 3, "arr": [4, 5]},
        ],
        expected=[{"_id": 1, "arr": [1, 2, 3]}, {"_id": 3, "arr": [4, 5]}],
        msg="$not with $elemMatch matches docs without element > 5",
    ),
    QueryTestCase(
        id="not_with_size",
        filter={"arr": {"$not": {"$size": 3}}},
        doc=[
            {"_id": 1, "arr": [1, 2]},
            {"_id": 2, "arr": [1, 2, 3]},
            {"_id": 3, "arr": [1]},
        ],
        expected=[{"_id": 1, "arr": [1, 2]}, {"_id": 3, "arr": [1]}],
        msg="$not with $size matches docs where array is not size 3",
    ),
    QueryTestCase(
        id="not_with_all",
        filter={"tags": {"$not": {"$all": ["red", "blue"]}}},
        doc=[
            {"_id": 1, "tags": ["red", "blue", "green"]},
            {"_id": 2, "tags": ["red", "green"]},
            {"_id": 3, "tags": ["blue"]},
        ],
        expected=[{"_id": 2, "tags": ["red", "green"]}, {"_id": 3, "tags": ["blue"]}],
        msg="$not with $all matches docs not containing all specified tags",
    ),
    QueryTestCase(
        id="not_with_exists",
        filter={"a": {"$not": {"$exists": True}}},
        doc=[
            {"_id": 1, "a": 1},
            {"_id": 2, "b": 2},
            {"_id": 3, "a": None},
        ],
        expected=[{"_id": 2, "b": 2}],
        msg="$not with $exists:true matches docs without the field",
    ),
    QueryTestCase(
        id="not_with_regex",
        filter={"name": {"$not": {"$regex": "^A"}}},
        doc=[
            {"_id": 1, "name": "Alice"},
            {"_id": 2, "name": "Bob"},
            {"_id": 3, "name": "Anna"},
        ],
        expected=[{"_id": 2, "name": "Bob"}],
        msg="$not with $regex matches docs where name does not start with A",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NOT_TESTS))
def test_not_operator_combinations(collection, test):
    """Test $not combined with other query operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


LOGICAL_COMBINATION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="and_with_or",
        filter={"$and": [{"$or": [{"a": 1}, {"a": 2}]}, {"b": {"$gt": 1}}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 2, "b": 2},
            {"_id": 3, "a": 3, "b": 3},
        ],
        expected=[{"_id": 2, "a": 2, "b": 2}],
        msg="$and with $or matches docs satisfying OR and additional clause",
    ),
    QueryTestCase(
        id="and_with_nor",
        filter={"$and": [{"$nor": [{"a": 1}]}, {"b": {"$gt": 1}}]},
        doc=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 2, "b": 2},
            {"_id": 3, "a": 3, "b": 1},
        ],
        expected=[{"_id": 2, "a": 2, "b": 2}],
        msg="$and with $nor matches docs excluded by $nor and satisfying other clause",
    ),
    QueryTestCase(
        id="or_with_and",
        filter={"$or": [{"$and": [{"a": 1}, {"b": 1}]}, {"$and": [{"a": 2}, {"b": 2}]}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 2, "b": 2},
            {"_id": 3, "a": 1, "b": 2},
        ],
        expected=[{"_id": 1, "a": 1, "b": 1}, {"_id": 2, "a": 2, "b": 2}],
        msg="$or with nested $and matches docs satisfying either AND branch",
    ),
    QueryTestCase(
        id="or_with_nor",
        filter={"$or": [{"$nor": [{"a": 1}]}, {"b": 1}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 2, "b": 2},
            {"_id": 3, "a": 1, "b": 2},
        ],
        expected=[{"_id": 1, "a": 1, "b": 1}, {"_id": 2, "a": 2, "b": 2}],
        msg="$or with $nor matches docs excluded by $nor or satisfying other clause",
    ),
    QueryTestCase(
        id="nor_with_and",
        filter={"$nor": [{"$and": [{"a": 1}, {"b": 1}]}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 1, "b": 2},
            {"_id": 3, "a": 2, "b": 1},
        ],
        expected=[{"_id": 2, "a": 1, "b": 2}, {"_id": 3, "a": 2, "b": 1}],
        msg="$nor with nested $and excludes docs satisfying the AND",
    ),
    QueryTestCase(
        id="nor_with_or",
        filter={"$nor": [{"$or": [{"a": 1}, {"b": 1}]}]},
        doc=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 2, "b": 1},
            {"_id": 3, "a": 2, "b": 2},
        ],
        expected=[{"_id": 3, "a": 2, "b": 2}],
        msg="$nor with nested $or excludes docs satisfying the OR",
    ),
    QueryTestCase(
        id="and_or_nor_combined",
        filter={"$and": [{"$or": [{"a": 1}, {"a": 2}]}, {"$nor": [{"b": 3}]}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 2, "b": 3},
            {"_id": 3, "a": 3, "b": 1},
        ],
        expected=[{"_id": 1, "a": 1, "b": 1}],
        msg="$and combining $or and $nor matches docs satisfying OR and not excluded by NOR",
    ),
    QueryTestCase(
        id="not_inside_and_with_or",
        filter={"$and": [{"a": {"$not": {"$gt": 2}}}, {"$or": [{"b": 1}, {"b": 2}]}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 3, "b": 1},
            {"_id": 3, "a": 2, "b": 3},
        ],
        expected=[{"_id": 1, "a": 1, "b": 1}],
        msg="$and with $not and $or matches docs where a <= 2 and b is 1 or 2",
    ),
    QueryTestCase(
        id="not_inside_or_with_nor",
        filter={"$or": [{"a": {"$not": {"$lt": 3}}}, {"$nor": [{"b": 1}]}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 3, "b": 1},
            {"_id": 3, "a": 1, "b": 2},
        ],
        expected=[{"_id": 2, "a": 3, "b": 1}, {"_id": 3, "a": 1, "b": 2}],
        msg="$or with $not and $nor matches docs where a >= 3 or b != 1",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LOGICAL_COMBINATION_TESTS))
def test_logical_operator_combinations(collection, test):
    """Test logical operators combined with each other."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)
