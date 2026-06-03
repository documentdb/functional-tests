"""Tests for $[<identifier>] arrayFilters conditions.

Covers: comparison operators, logical operators, element operators,
restricted operators, multiple arrayFilters, and edge cases.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ArrayFilterTest(BaseTestCase):
    """Test case for arrayFilters conditions."""

    setup_docs: Any = None
    query: Any = None
    update: Any = None
    array_filters: Any = None


# --- Comparison Operators in arrayFilters ---

COMPARISON_TESTS: list[ArrayFilterTest] = [
    ArrayFilterTest(
        "eq",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 2]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$eq": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $eq should match equal elements",
    ),
    ArrayFilterTest(
        "gt",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gt": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $gt should match elements > value",
    ),
    ArrayFilterTest(
        "gte",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gte": 3}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $gte should match elements >= value",
    ),
    ArrayFilterTest(
        "lt",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$lt": 3}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $lt should match elements < value",
    ),
    ArrayFilterTest(
        "lte",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$lte": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $lte should match elements <= value",
    ),
    ArrayFilterTest(
        "ne",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$ne": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $ne should match elements != value",
    ),
    ArrayFilterTest(
        "in",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$in": [2, 4]}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $in should match elements in list",
    ),
    ArrayFilterTest(
        "nin",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$nin": [2, 4]}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $nin should match elements not in list",
    ),
]


# --- Logical Operators in arrayFilters ---

LOGICAL_TESTS: list[ArrayFilterTest] = [
    ArrayFilterTest(
        "and_multiple_conditions",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gt": 2, "$lt": 5}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with implicit $and should match elements meeting all conditions",
    ),
    ArrayFilterTest(
        "or",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"$or": [{"elem": {"$eq": 1}}, {"elem": {"$eq": 5}}]}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $or should match elements meeting any condition",
    ),
    ArrayFilterTest(
        "not",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4, 5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$not": {"$gt": 3}}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $not should match elements not meeting condition",
    ),
]


# --- Element Operators in arrayFilters ---

ELEMENT_TESTS: list[ArrayFilterTest] = [
    ArrayFilterTest(
        "exists",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}, {"y": 2}, {"x": 3}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem].x": 99}},
        array_filters=[{"elem.x": {"$exists": True}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $exists should match elements with field",
    ),
    ArrayFilterTest(
        "type",
        setup_docs=[{"_id": 1, "arr": [1, "two", 3, "four"]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$type": "string"}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="arrayFilters with $type should match elements of specified type",
    ),
]


# --- Multiple arrayFilters ---

MULTIPLE_FILTERS_TESTS: list[ArrayFilterTest] = [
    ArrayFilterTest(
        "multiple_identifiers",
        setup_docs=[{"_id": 1, "arr": [{"a": 1, "b": 10}, {"a": 2, "b": 20}, {"a": 3, "b": 30}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[x].a": 99, "arr.$[y].b": 99}},
        array_filters=[{"x.a": {"$gte": 2}}, {"y.b": {"$lte": 20}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="Multiple arrayFilters with different identifiers should work",
    ),
]


ALL_SUCCESS_TESTS = COMPARISON_TESTS + LOGICAL_TESTS + ELEMENT_TESTS + MULTIPLE_FILTERS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_SUCCESS_TESTS))
def test_positional_filtered_array_filters_success(collection, test: ArrayFilterTest):
    """Test $[<identifier>] arrayFilters conditions - success cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update, "arrayFilters": test.array_filters}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)


# --- Restricted Operators (should fail) ---

RESTRICTED_OPERATOR_TESTS: list[ArrayFilterTest] = [
    ArrayFilterTest(
        "text_in_arrayFilters",
        setup_docs=[{"_id": 1, "arr": ["hello", "world"]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"$text": {"$search": "hello"}}],
        error_code=BAD_VALUE_ERROR,
        msg="arrayFilters with $text should fail",
    ),
    ArrayFilterTest(
        "where_in_arrayFilters",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"$where": "true"}],
        error_code=BAD_VALUE_ERROR,
        msg="arrayFilters with $where should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESTRICTED_OPERATOR_TESTS))
def test_positional_filtered_array_filters_error(collection, test):
    """Test $[<identifier>] arrayFilters restricted operators - error cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update, "arrayFilters": test.array_filters}],
    }
    result = execute_command(collection, command)
    assertFailureCode(result, test.error_code, msg=test.msg)
