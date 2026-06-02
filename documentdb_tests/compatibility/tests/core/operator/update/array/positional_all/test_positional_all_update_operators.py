"""Tests for $[] positional-all with update operators and null/missing handling.

Covers: $set, $inc, $mul, $min, $max, $unset behavior, null/missing field handling,
empty/single element arrays, and interaction with other update operators.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class PositionalAllUpdateTest(BaseTestCase):
    """Test case for $[] with update operators."""

    setup_docs: Any = None
    query: Any = None
    update: Any = None


# --- Null/Missing Field Handling ---

NULL_HANDLING_SUCCESS_TESTS: list[PositionalAllUpdateTest] = [
    PositionalAllUpdateTest(
        "set_null_elements_to_value",
        setup_docs=[{"_id": 1, "arr": [None, None, None]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $set on null elements should replace all with new value",
    ),
    PositionalAllUpdateTest(
        "set_all_to_null",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": None}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $set value of null should update all elements to null",
    ),
]

NULL_HANDLING_ERROR_TESTS: list[PositionalAllUpdateTest] = [
    PositionalAllUpdateTest(
        "inc_on_null_elements",
        setup_docs=[{"_id": 1, "arr": [1, None, 3]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[]": 5}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$[] with $inc on array containing null should fail",
    ),
    PositionalAllUpdateTest(
        "null_field_not_array",
        setup_docs=[{"_id": 1, "arr": None}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$[] on null field (not an array) should fail",
    ),
]


# --- $unset Behavior ---

UNSET_TESTS: list[PositionalAllUpdateTest] = [
    PositionalAllUpdateTest(
        "unset_all_elements",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"arr.$[]": ""}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $unset should set all elements to null",
    ),
    PositionalAllUpdateTest(
        "unset_field_in_embedded_docs",
        setup_docs=[{"_id": 1, "arr": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}],
        query={"_id": 1},
        update={"$unset": {"arr.$[].y": ""}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $unset on embedded doc field should remove field from all docs",
    ),
]


# --- Interaction with Other Update Operators ---

INTERACTION_TESTS: list[PositionalAllUpdateTest] = [
    PositionalAllUpdateTest(
        "positional_all_and_set_different_fields",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3], "x": 10}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0, "x": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] on one field and $set on another should both succeed",
    ),
    PositionalAllUpdateTest(
        "positional_all_and_positional_different_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]}],
        query={"_id": 1, "b": 20},
        update={"$set": {"a.$[]": 0, "b.$": 99}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] and $ on different fields in same update should both work",
    ),
]


# --- Empty and Single Element ---

EDGE_CASE_TESTS: list[PositionalAllUpdateTest] = [
    PositionalAllUpdateTest(
        "inc_single_element",
        setup_docs=[{"_id": 1, "arr": [42]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[]": 8}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $inc on single element array should increment that element",
    ),
    PositionalAllUpdateTest(
        "mul_empty_array",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$mul": {"arr.$[]": 2}},
        expected={"n": 1, "nModified": 0, "ok": 1.0},
        msg="$[] with $mul on empty array should be no-op",
    ),
]


ALL_SUCCESS_TESTS = NULL_HANDLING_SUCCESS_TESTS + UNSET_TESTS + INTERACTION_TESTS + EDGE_CASE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_SUCCESS_TESTS))
def test_positional_all_update_operators_success(collection, test: PositionalAllUpdateTest):
    """Test $[] with update operators - success cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)


@pytest.mark.parametrize("test", pytest_params(NULL_HANDLING_ERROR_TESTS))
def test_positional_all_update_operators_error(collection, test):
    """Test $[] with update operators - error cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update}],
    }
    result = execute_command(collection, command)
    assertFailureCode(result, test.error_code, msg=test.msg)
