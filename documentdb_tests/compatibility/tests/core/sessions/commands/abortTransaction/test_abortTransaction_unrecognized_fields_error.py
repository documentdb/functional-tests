"""Tests for abortTransaction unrecognized field handling.

Validates that the abortTransaction command rejects unknown fields. Covers
single unknown fields, multiple unknown fields, case-sensitive field names,
known fields from other commands, and dollar-prefixed fields.
"""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import UNRECOGNIZED_COMMAND_FIELD_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


# Property [Unrecognized Field Rejection]: unknown fields are rejected.
UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_single_field",
        command={"abortTransaction": 1, "unknownField": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="abortTransaction should reject single unknown field",
    ),
    CommandTestCase(
        "unknown_multiple_fields",
        command={"abortTransaction": 1, "foo": 1, "bar": 2},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="abortTransaction should reject multiple unknown fields",
    ),
]

# Property [Case Sensitivity]: field names are case-sensitive and wrong-case variants are rejected.
CASE_SENSITIVITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "case_WriteConcern",
        command={"abortTransaction": 1, "WriteConcern": {"w": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="abortTransaction should reject 'WriteConcern' (capital W) as unrecognized",
    ),
    CommandTestCase(
        "case_Autocommit",
        command={"abortTransaction": 1, "Autocommit": False},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="abortTransaction should reject 'Autocommit' (capital A) as unrecognized",
    ),
    CommandTestCase(
        "case_TxnNumber",
        command={"abortTransaction": 1, "TxnNumber": Int64(1)},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="abortTransaction should reject 'TxnNumber' (capital T) as unrecognized",
    ),
    CommandTestCase(
        "case_Comment",
        command={"abortTransaction": 1, "Comment": "test"},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="abortTransaction should reject 'Comment' (capital C) as unrecognized",
    ),
]

# Property [Foreign Field Rejection]: fields from other commands are rejected.
FOREIGN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "foreign_query",
        command={"abortTransaction": 1, "query": {"x": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="abortTransaction should reject 'query' field from other commands",
    ),
    CommandTestCase(
        "dollar_prefixed",
        command={"abortTransaction": 1, "$unknown": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="abortTransaction should reject dollar-prefixed unknown field",
    ),
]

# Property [writeConcern Unknown Sub-Field]: unknown writeConcern sub-fields are rejected.
WRITECONCERN_UNKNOWN_SUBFIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_unknown_subfield",
        command={"abortTransaction": 1, "writeConcern": {"w": 1, "unknownOption": True}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="abortTransaction should reject unknown writeConcern sub-field",
    ),
]

UNRECOGNIZED_TESTS: list[CommandTestCase] = (
    UNRECOGNIZED_FIELD_TESTS
    + CASE_SENSITIVITY_TESTS
    + FOREIGN_FIELD_TESTS
    + WRITECONCERN_UNKNOWN_SUBFIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(UNRECOGNIZED_TESTS))
def test_abortTransaction_unrecognized_fields_error(collection, test):
    """Test abortTransaction unrecognized field error cases."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
