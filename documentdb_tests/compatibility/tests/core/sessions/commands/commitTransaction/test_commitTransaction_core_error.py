"""Tests for commitTransaction command core behavior.

Validates fundamental command behavior including the no-transaction error,
admin database requirement, and parameter interactions.
"""

from __future__ import annotations

import pytest
from bson import Binary, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    COMMAND_FAILED_ERROR,
    INVALID_OPTIONS_ERROR,
    NOT_A_RETRYABLE_WRITE_COMMAND_ERROR,
    TRANSACTION_TOO_OLD_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.admin, pytest.mark.requires(change_streams=True)]


# Property [No-Transaction Error]: commitTransaction outside a transaction fails.
CORE_NO_TRANSACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "no_transaction_basic",
        command={"commitTransaction": 1},
        error_code=COMMAND_FAILED_ERROR,
        msg="commitTransaction should fail with NoSuchTransaction outside a transaction",
    ),
]

# Property [Parameter Acceptance]: all valid parameters combined are syntactically accepted.
CORE_PARAMETER_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "all_valid_params_no_parse_error",
        command={
            "commitTransaction": 1,
            "autocommit": False,
            "txnNumber": Int64(1),
            "writeConcern": {"w": "majority", "j": True, "wtimeout": 10_000},
            "comment": "full commit",
        },
        error_code=TRANSACTION_TOO_OLD_ERROR,
        msg="commitTransaction with all valid params should not produce a parsing error",
    ),
]

# Property [Parameter Interactions]: combinations of valid parameters behave correctly.
CORE_PARAMETER_INTERACTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "interaction_autocommit_only",
        command={"commitTransaction": 1, "autocommit": False},
        error_code=INVALID_OPTIONS_ERROR,
        msg="commitTransaction with autocommit:false only should fail with InvalidOptions",
    ),
    CommandTestCase(
        "interaction_txn_number_only",
        command={"commitTransaction": 1, "txnNumber": Int64(1)},
        error_code=NOT_A_RETRYABLE_WRITE_COMMAND_ERROR,
        msg="commitTransaction with txnNumber only should fail with NotARetryableWriteCommand",
    ),
    CommandTestCase(
        "interaction_autocommit_txn_number",
        command={"commitTransaction": 1, "autocommit": False, "txnNumber": Int64(1)},
        error_code=TRANSACTION_TOO_OLD_ERROR,
        msg="commitTransaction with autocommit + txnNumber should fail with TransactionTooOld",
    ),
    CommandTestCase(
        "interaction_lsid",
        command={"commitTransaction": 1, "lsid": {"id": Binary(b"\x00" * 16, 4)}},
        error_code=COMMAND_FAILED_ERROR,
        msg="commitTransaction with explicit lsid should accept the field",
    ),
]

CORE_TESTS: list[CommandTestCase] = (
    CORE_NO_TRANSACTION_TESTS + CORE_PARAMETER_ACCEPTANCE_TESTS + CORE_PARAMETER_INTERACTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(CORE_TESTS))
def test_commitTransaction_core_error(collection, test):
    """Test commitTransaction core behavior."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


# Property [Admin Database Requirement]: commitTransaction must run against the admin database.
ADMIN_DB_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "non_admin_database",
        command={"commitTransaction": 1},
        error_code=UNAUTHORIZED_ERROR,
        msg="commitTransaction on a non-admin database should fail with Unauthorized",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ADMIN_DB_TESTS))
def test_commitTransaction_admin_db_required_error(collection, test):
    """Test commitTransaction requires admin database."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)
