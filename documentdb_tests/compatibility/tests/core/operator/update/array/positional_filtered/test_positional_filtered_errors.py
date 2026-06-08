"""Tests for $[<identifier>] error cases and restrictions.

Covers: identifier naming rules, upsert behavior, missing arrayFilters,
identifier mismatch, restricted operators in arrayFilters, and non-array fields.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.array.positional_filtered.utils.filtered_update_test_case import (  # noqa: E501
    FilteredUpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

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
]


RESTRICTED_OPERATOR_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "text_in_arrayFilters",
        setup_docs=[{"_id": 1, "arr": ["hello", "world"]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"$text": {"$search": "hello"}}],
        error_code=BAD_VALUE_ERROR,
        msg="arrayFilters with $text should fail",
    ),
]


NON_ARRAY_FIELD_TESTS: list[FilteredUpdateTestCase] = [
    FilteredUpdateTestCase(
        "field_exists_but_not_array",
        setup_docs=[{"_id": 1, "arr": 5}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gte": 1}}],
        error_code=BAD_VALUE_ERROR,
        msg="$[<id>] on a scalar field (not an array) should fail",
    ),
]


ALL_ERROR_TESTS = (
    MISSING_FILTERS_TESTS
    + UPSERT_ERROR_TESTS
    + IDENTIFIER_NAMING_ERROR_TESTS
    + RESTRICTED_OPERATOR_TESTS
    + NON_ARRAY_FIELD_TESTS
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
