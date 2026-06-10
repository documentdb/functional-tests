"""Tests for killAllSessions user array entry validation errors."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.no_parallel

# Property [User Entry Not Object]: non-object entries in the user array are rejected.
KILLALLSESSIONS_ENTRY_NOT_OBJECT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"entry_{tid}",
        command=lambda ctx, v=val: {"killAllSessions": [v]},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killAllSessions should reject {tid} array entry",
    )
    for tid, val in [
        ("string", "notAnObject"),
        ("int", 123),
        ("bool", True),
        ("array", [1, 2]),
    ]
]

# Property [User Entry Missing Fields]: user array entries with missing
# required fields are rejected.
KILLALLSESSIONS_MISSING_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_object",
        command=lambda ctx: {"killAllSessions": [{}]},
        error_code=MISSING_FIELD_ERROR,
        msg="killAllSessions should reject empty object entry",
    ),
    CommandTestCase(
        "missing_db",
        command=lambda ctx: {"killAllSessions": [{"user": "test"}]},
        error_code=MISSING_FIELD_ERROR,
        msg="killAllSessions should reject entry missing db field",
    ),
    CommandTestCase(
        "missing_user",
        command=lambda ctx: {"killAllSessions": [{"db": "admin"}]},
        error_code=MISSING_FIELD_ERROR,
        msg="killAllSessions should reject entry missing user field",
    ),
]

# Property [User Entry Invalid User Type]: non-string user field in array
# entry is rejected.
KILLALLSESSIONS_INVALID_USER_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"user_{tid}",
        command=lambda ctx, v=val: {
            "killAllSessions": [{"user": v, "db": "admin"}],
        },
        error_code=error,
        msg=f"killAllSessions should reject {tid} user field",
    )
    for tid, val, error in [
        ("int", 123, TYPE_MISMATCH_ERROR),
        ("bool", True, TYPE_MISMATCH_ERROR),
        ("array", [], TYPE_MISMATCH_ERROR),
        ("null", None, MISSING_FIELD_ERROR),
    ]
]

# Property [User Entry Invalid DB Type]: non-string db field in array
# entry is rejected.
KILLALLSESSIONS_INVALID_DB_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"db_{tid}",
        command=lambda ctx, v=val: {
            "killAllSessions": [{"user": "test", "db": v}],
        },
        error_code=error,
        msg=f"killAllSessions should reject {tid} db field",
    )
    for tid, val, error in [
        ("int", 123, TYPE_MISMATCH_ERROR),
        ("bool", True, TYPE_MISMATCH_ERROR),
        ("array", [], TYPE_MISMATCH_ERROR),
        ("null", None, MISSING_FIELD_ERROR),
    ]
]

# Property [User Entry Extra Fields]: extra fields in user array entries are rejected.
KILLALLSESSIONS_EXTRA_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "extra_field",
        command=lambda ctx: {
            "killAllSessions": [{"user": "test", "db": "admin", "extra": 1}],
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="killAllSessions should reject extra fields in user entry",
    ),
]

KILLALLSESSIONS_USER_ARRAY_ERROR_TESTS: list[CommandTestCase] = (
    KILLALLSESSIONS_ENTRY_NOT_OBJECT_TESTS
    + KILLALLSESSIONS_MISSING_FIELD_TESTS
    + KILLALLSESSIONS_INVALID_USER_TYPE_TESTS
    + KILLALLSESSIONS_INVALID_DB_TYPE_TESTS
    + KILLALLSESSIONS_EXTRA_FIELDS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLALLSESSIONS_USER_ARRAY_ERROR_TESTS))
def test_killAllSessions_user_array_errors(collection, test):
    """Test killAllSessions user array entry validation errors."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
