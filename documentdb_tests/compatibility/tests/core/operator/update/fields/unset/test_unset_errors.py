"""
Tests for $unset update operator - error code validation.

Covers empty field name, dot-path edge cases, conflicting paths, and _id immutability.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CONFLICTING_UPDATE_OPERATORS_ERROR,
    EMPTY_FIELD_NAME_ERROR,
    IMMUTABLE_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

UNSET_ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="empty_field_name",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$unset": {"": ""}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Empty field name should fail",
    ),
    UpdateTestCase(
        id="empty_field_name_trailing_dot",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$unset": {"a.": ""}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Trailing dot in path should fail (empty field name)",
    ),
    UpdateTestCase(
        id="empty_field_name_leading_dot",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$unset": {".a": ""}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Leading dot in path should fail (empty field name)",
    ),
    UpdateTestCase(
        id="empty_field_name_double_dot",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$unset": {"a..b": ""}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Double dot in path should fail (empty field name)",
    ),
    UpdateTestCase(
        id="conflicting_paths",
        setup_docs=[{"_id": 1, "a": {"b": 1}}],
        query={"_id": 1},
        update={"$unset": {"a": "", "a.b": ""}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Conflicting paths should fail",
    ),
    UpdateTestCase(
        id="unset_id",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$unset": {"_id": ""}},
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="Cannot unset _id",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_ERROR_TESTS))
def test_unset_errors(collection, test):
    """Test $unset error cases."""
    collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    assertFailureCode(result, test.error_code, msg=test.msg)
