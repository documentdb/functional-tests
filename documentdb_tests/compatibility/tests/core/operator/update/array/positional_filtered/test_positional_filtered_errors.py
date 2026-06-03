"""Tests for $[<identifier>] error cases and restrictions.

Covers: identifier naming rules, upsert behavior, missing arrayFilters,
identifier mismatch, and interaction with other positional operators.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.array.positional_filtered.utils.filtered_update_test_case import (  # noqa: E501
    FilteredUpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# --- Missing arrayFilters ---

MISSING_FILTERS_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "no_arrayFilters_option",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=None,
        error_code=BAD_VALUE_ERROR,
        msg="$[<id>] without arrayFilters option should fail",
    ),
    FilteredUpdateTestCase(
        "identifier_not_in_arrayFilters",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[x]": 99}},
        array_filters=[{"y": {"$gte": 2}}],
        error_code=BAD_VALUE_ERROR,
        msg="$[<id>] with identifier not matching any arrayFilters entry should fail",
    ),
]


# --- Upsert Behavior ---

UPSERT_ERROR_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "upsert_without_equality",
        setup_docs=None,
        query={"x": {"$gt": 5}},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gte": 1}}],
        upsert=True,
        error_code=BAD_VALUE_ERROR,
        msg="$[<id>] in upsert without exact equality match should fail",
    ),
]


# --- $rename restriction ---

RENAME_ERROR_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "rename_with_filtered_positional",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}, {"a": 2}]}],
        query={"_id": 1},
        update={"$rename": {"arr.$[elem].a": "arr.$[elem].b"}},
        array_filters=[{"elem.a": {"$gte": 1}}],
        error_code=BAD_VALUE_ERROR,
        msg="$rename with $[<id>] should fail (source field may not be dynamic)",
    ),
]


ALL_ERROR_TESTS = MISSING_FILTERS_TESTS + UPSERT_ERROR_TESTS + RENAME_ERROR_TESTS


# --- Identifier Naming Rules ---

IDENTIFIER_NAMING_ERROR_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "identifier_starts_with_digit",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[1elem]": 99}},
        array_filters=[{"1elem": {"$gte": 2}}],
        error_code=BAD_VALUE_ERROR,
        msg="$[<id>] with identifier starting with digit should fail",
    ),
    FilteredUpdateTestCase(
        "identifier_empty",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        array_filters=[{"": {"$gte": 2}}],
        error_code=BAD_VALUE_ERROR,
        msg="$[<id>] with empty identifier should fail",
    ),
]


ALL_ERROR_TESTS = (
    MISSING_FILTERS_TESTS + UPSERT_ERROR_TESTS + RENAME_ERROR_TESTS + IDENTIFIER_NAMING_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_positional_filtered_errors(collection, test):
    """Test $[<identifier>] error cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.array_filters is not None:
        update_doc["arrayFilters"] = test.array_filters
    if test.upsert:
        update_doc["upsert"] = True
    command = {"update": collection.name, "updates": [update_doc]}
    result = execute_command(collection, command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# --- Interaction with other positional operators (should succeed) ---

INTERACTION_SUCCESS_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "filtered_and_positional_different_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]}],
        query={"_id": 1, "a": 2},
        update={"$set": {"a.$": 99, "b.$[elem]": 0}},
        array_filters=[{"elem": {"$gte": 20}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$ and $[<id>] on different fields in same update should both work",
    ),
    FilteredUpdateTestCase(
        "filtered_and_all_different_fields",
        setup_docs=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30]}],
        query={"_id": 1},
        update={"$set": {"a.$[]": 0, "b.$[elem]": 99}},
        array_filters=[{"elem": {"$gte": 20}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] and $[<id>] on different fields in same update should both work",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INTERACTION_SUCCESS_TESTS))
def test_positional_filtered_interaction_success(collection, test: FilteredUpdateTestCase):
    """Test $[<identifier>] interaction with other positional operators."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.array_filters is not None:
        update_doc["arrayFilters"] = test.array_filters
    command = {"update": collection.name, "updates": [update_doc]}
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
