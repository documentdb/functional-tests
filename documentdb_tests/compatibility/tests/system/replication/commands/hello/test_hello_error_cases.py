"""Tests for hello command error cases.

Validates case-sensitive command name rejection, saslSupportedMechs
invalid format rejection, and saslSupportedMechs type rejection.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.replication.utils.replication_test_case import (  # noqa: E501
    ReplicationTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_FOUND_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Case-Sensitive Command Name]: the hello command is case-sensitive
# and rejects case mismatches.
HELLO_CASE_ERROR_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "case_capital_H",
        command=lambda ctx: {"Hello": 1},
        use_admin=False,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="hello should reject 'Hello' (capital H)",
    ),
    ReplicationTestCase(
        "case_all_caps",
        command=lambda ctx: {"HELLO": 1},
        use_admin=False,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="hello should reject 'HELLO' (all caps)",
    ),
    ReplicationTestCase(
        "case_mixed",
        command=lambda ctx: {"heLLo": 1},
        use_admin=False,
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="hello should reject 'heLLo' (mixed case)",
    ),
]

# Property [saslSupportedMechs Invalid Format]: hello rejects strings
# that do not follow the "db.user" format.
SASL_INVALID_FORMAT_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "sasl_no_dot_separator",
        command=lambda ctx: {
            "hello": 1,
            "saslSupportedMechs": "noDotSeparator",
        },
        use_admin=False,
        error_code=BAD_VALUE_ERROR,
        msg="hello should reject saslSupportedMechs without db.user format",
    ),
    ReplicationTestCase(
        "sasl_empty_string",
        command=lambda ctx: {"hello": 1, "saslSupportedMechs": ""},
        use_admin=False,
        error_code=BAD_VALUE_ERROR,
        msg="hello should reject empty string saslSupportedMechs",
    ),
]

# Property [saslSupportedMechs Type Rejection]: hello rejects non-string
# types for saslSupportedMechs.
SASL_TYPE_REJECTION_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        f"sasl_type_{tid}",
        command=lambda ctx, v=val: {"hello": 1, "saslSupportedMechs": v},
        use_admin=False,
        error_code=err,
        msg=f"hello should reject {tid} as saslSupportedMechs",
    )
    for tid, val, err in [
        ("int", 123, TYPE_MISMATCH_ERROR),
        ("bool", True, TYPE_MISMATCH_ERROR),
        ("array", ["admin.user"], TYPE_MISMATCH_ERROR),
        ("object", {"db": "admin"}, BAD_VALUE_ERROR),
        ("null", None, TYPE_MISMATCH_ERROR),
    ]
]

HELLO_ERROR_ALL_TESTS: list[ReplicationTestCase] = (
    HELLO_CASE_ERROR_TESTS + SASL_INVALID_FORMAT_TESTS + SASL_TYPE_REJECTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(HELLO_ERROR_ALL_TESTS))
def test_hello_error_cases(collection, test):
    """Test hello command error cases."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
