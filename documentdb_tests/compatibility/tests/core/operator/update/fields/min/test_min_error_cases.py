"""
Error case tests for $min update field operator.

Tests $min conflict errors, invalid field paths, and dollar-prefixed fields.
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

# Property [Error Cases]: $min rejects conflicting operators on same field and invalid field names.
ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "conflict_with_max_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$min": {"val": 5}, "$max": {"val": 20}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$min and $max on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_set_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$min": {"val": 5}, "$set": {"val": 20}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$min and $set on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_inc_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$min": {"val": 5}, "$inc": {"val": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$min and $inc on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_mul_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$min": {"val": 5}, "$mul": {"val": 2}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$min and $mul on same field should produce conflict error",
    ),
    UpdateTestCase(
        "dollar_prefixed_field_error",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$min": {"$field": 5}},
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="$min with dollar-prefixed field name should produce error",
    ),
    UpdateTestCase(
        "bare_dollar_field_error",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$min": {"$": 5}},
        error_code=BAD_VALUE_ERROR,
        msg="$min with bare '$' as field name should produce BadValue error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_min_errors(collection, test: UpdateTestCase):
    """Test $min error cases produce expected error codes."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]
