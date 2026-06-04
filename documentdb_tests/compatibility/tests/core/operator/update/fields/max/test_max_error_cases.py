"""
Error case tests for $max update field operator.

Tests $max conflict errors, invalid field paths, and dollar-prefixed fields.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONFLICTING_UPDATE_OPERATORS_ERROR,
    DOLLAR_PREFIXED_FIELD_NAME_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "conflict_with_min_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": 20}, "$min": {"val": 5}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$max and $min on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_set_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": 20}, "$set": {"val": 5}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$max and $set on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_inc_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": 20}, "$inc": {"val": 5}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$max and $inc on same field should produce conflict error",
    ),
    UpdateTestCase(
        "dollar_prefixed_field_error",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"$field": 20}},
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="$max with dollar-prefixed field name should produce error",
    ),
    UpdateTestCase(
        "bare_dollar_field_error",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"$": 20}},
        error_code=BAD_VALUE_ERROR,
        msg="$max with bare '$' as field name should produce BadValue error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_max_errors(collection, test: UpdateTestCase):
    """Test $max error cases produce expected error codes."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]
