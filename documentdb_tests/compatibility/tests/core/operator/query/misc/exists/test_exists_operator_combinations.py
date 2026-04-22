"""
Tests for $exists combined with other query operators.

Covers $exists with comparison, $type, $in, $nin, $regex, $size, $all,
$not, and logical operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS: list[dict] = [
    {"_id": 1, "a": 1},
    {"_id": 2, "a": None},
    {"_id": 3, "b": 1},
]

COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="exists_and_gt",
        filter={"a": {"$exists": True, "$gt": 0}},
        doc=[{"_id": 1, "a": 10}, {"_id": 2, "a": -1}, {"_id": 3, "b": 1}],
        expected=[{"_id": 1, "a": 10}],
        msg="$exists: true AND $gt: 0",
    ),
    QueryTestCase(
        id="exists_and_eq_null",
        filter={"a": {"$exists": True, "$eq": None}},
        doc=DOCS,
        expected=[{"_id": 2, "a": None}],
        msg="$exists: true AND $eq: null — field exists and is null",
    ),
    QueryTestCase(
        id="exists_and_ne_null",
        filter={"a": {"$exists": True, "$ne": None}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1}],
        msg="$exists: true AND $ne: null — field exists and is not null",
    ),
    QueryTestCase(
        id="exists_and_type_string",
        filter={"a": {"$exists": True, "$type": "string"}},
        doc=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": 123}, {"_id": 3, "b": 1}],
        expected=[{"_id": 1, "a": "hello"}],
        msg="$exists: true AND $type: string",
    ),
    QueryTestCase(
        id="exists_and_in",
        filter={"a": {"$exists": True, "$in": [1, 2, 3]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "b": 1}],
        expected=[{"_id": 1, "a": 1}],
        msg="$exists: true AND $in: [1, 2, 3]",
    ),
    QueryTestCase(
        id="exists_and_nin",
        filter={"a": {"$exists": True, "$nin": [1, 2]}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": None}, {"_id": 3, "b": 1}],
        expected=[{"_id": 2, "a": None}],
        msg="$exists: true AND $nin: [1, 2] — null field matches",
    ),
]

REGEX_SIZE_ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="exists_and_regex",
        filter={"a": {"$exists": True, "$regex": "^h"}},
        doc=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": 123}, {"_id": 3, "b": 1}],
        expected=[{"_id": 1, "a": "hello"}],
        msg="$exists: true AND $regex matches",
    ),
    QueryTestCase(
        id="exists_and_size",
        filter={"a": {"$exists": True, "$size": 2}},
        doc=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [1]}, {"_id": 3, "b": 1}],
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="$exists: true AND $size: 2",
    ),
    QueryTestCase(
        id="exists_and_all",
        filter={"a": {"$exists": True, "$all": [1, 2]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [1, 2]}, {"_id": 3, "b": 1}],
        expected=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [1, 2]}],
        msg="$exists: true AND $all: [1, 2]",
    ),
]

NOT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="not_exists_true",
        filter={"a": {"$not": {"$exists": True}}},
        doc=DOCS,
        expected=[{"_id": 3, "b": 1}],
        msg="$not {$exists: true} equivalent to $exists: false",
    ),
    QueryTestCase(
        id="not_exists_false",
        filter={"a": {"$not": {"$exists": False}}},
        doc=DOCS,
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": None}],
        msg="$not {$exists: false} equivalent to $exists: true",
    ),
]

LOGICAL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="or_exists_false_or_gt",
        filter={"$or": [{"a": {"$exists": False}}, {"a": {"$gt": 10}}]},
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": 15}, {"_id": 3, "b": 1}],
        expected=[{"_id": 2, "a": 15}, {"_id": 3, "b": 1}],
        msg="$or with $exists: false or $gt: 10",
    ),
    QueryTestCase(
        id="nor_exists_true",
        filter={"$nor": [{"a": {"$exists": True}}]},
        doc=DOCS,
        expected=[{"_id": 3, "b": 1}],
        msg="$nor with $exists: true — equivalent to $exists: false",
    ),
    QueryTestCase(
        id="or_overlapping",
        filter={"$or": [{"a": {"$exists": True}}, {"b": {"$exists": True}}]},
        doc=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 1},
            {"_id": 3, "b": 2},
            {"_id": 4, "c": 3},
        ],
        expected=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 1},
            {"_id": 3, "b": 2},
        ],
        msg="$or with overlapping $exists conditions",
    ),
    QueryTestCase(
        id="and_both_fields_exist",
        filter={"$and": [{"a": {"$exists": True}}, {"b": {"$exists": True}}]},
        doc=[
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 1},
            {"_id": 3, "b": 2},
            {"_id": 4, "c": 3},
        ],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="$and with both fields must exist",
    ),
]

ALL_TESTS = COMPARISON_TESTS + REGEX_SIZE_ALL_TESTS + NOT_TESTS + LOGICAL_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_exists_operator_combinations(collection, test):
    """Parametrized test for $exists combined with other operators."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
