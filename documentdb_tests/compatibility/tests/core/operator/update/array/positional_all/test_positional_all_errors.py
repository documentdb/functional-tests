"""Tests for $[] positional-all error cases and restrictions.

Covers: non-array field, null field, missing field, intermediate field type
validation, and upsert restrictions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "non_array_field",
        setup_docs=[{"_id": 1, "x": "not_an_array"}],
        query={"_id": 1},
        update={"$set": {"x.$[]": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$[] on non-array field should fail",
    ),
    UpdateTestCase(
        "null_field",
        setup_docs=[{"_id": 1, "arr": None}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$[] on null field should fail",
    ),
    UpdateTestCase(
        "upsert_without_equality_match",
        setup_docs=None,
        query={"x": {"$gt": 5}},
        update={"$set": {"arr.$[]": 99}},
        upsert=True,
        error_code=BAD_VALUE_ERROR,
        msg="$[] in upsert without exact equality match should fail",
    ),
    UpdateTestCase(
        "missing_field",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$[] on missing field should fail (path must exist)",
    ),
    UpdateTestCase(
        "missing_nested_field",
        setup_docs=[{"_id": 1, "outer": {}}],
        query={"_id": 1},
        update={"$set": {"outer.arr.$[]": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$[] on missing nested field should fail (path must exist)",
    ),
    UpdateTestCase(
        "null_query_on_missing_field",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"arr": None},
        update={"$set": {"arr.$[]": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$[] with null query on missing field should fail (no array)",
    ),
    UpdateTestCase(
        "field_exists_but_not_array",
        setup_docs=[{"_id": 1, "arr": 5}],
        query={"_id": 1, "arr": 5},
        update={"$set": {"arr.$[]": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$[] on scalar field should fail even when query matches",
    ),
    UpdateTestCase(
        "intermediate_field_is_scalar",
        setup_docs=[{"_id": 1, "a": {"b": "string_value"}}],
        query={"_id": 1},
        update={"$set": {"a.b.$[]": 99}},
        error_code=BAD_VALUE_ERROR,
        msg="$[] should fail when intermediate field (a.b) is a scalar, not an array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_positional_all_errors(collection, test):
    """Test $[] positional-all error cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.upsert:
        update_doc["upsert"] = True
    command = {"update": collection.name, "updates": [update_doc]}
    result = execute_command(collection, command)
    assertFailureCode(result, test.error_code, msg=test.msg)


UPSERT_SUCCESS_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "upsert_with_equality_match",
        setup_docs=None,
        query={"_id": 1, "arr": [1, 2, 3]},
        update={"$set": {"arr.$[]": 0}},
        upsert=True,
        expected={"n": 1, "nModified": 0, "ok": 1.0, "upserted": [{"_id": 1, "index": 0}]},
        msg="$[] in upsert with exact equality match on array should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UPSERT_SUCCESS_TESTS))
def test_positional_all_upsert_success(collection, test: UpdateTestCase):
    """Test $[] positional-all upsert success cases."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update, "upsert": True}
    command = {"update": collection.name, "updates": [update_doc]}
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
