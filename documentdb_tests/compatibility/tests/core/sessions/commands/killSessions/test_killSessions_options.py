"""Tests for killSessions writeConcern, Stable API, and unrecognized fields."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [writeConcern Null Acceptance]: null writeConcern is treated
# as omitted and accepted.
KILLSESSIONS_WRITECONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_null",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\x00" * 16, subtype=4)}],
            "writeConcern": None,
        },
        expected={"ok": 1.0},
        msg="killSessions should accept null writeConcern",
    ),
]

# Property [writeConcern Type Rejection]: all non-document, non-null BSON
# types for the writeConcern field are rejected.
KILLSESSIONS_WRITECONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"writeconcern_type_{tid}",
        command=lambda ctx, v=val: {
            "killSessions": [{"id": Binary(b"\x00" * 16, subtype=4)}],
            "writeConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"killSessions should reject {tid} writeConcern",
    )
    for tid, val in [
        ("string", "majority"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", []),
        ("array_nonempty", [1, 2]),
        ("binary", Binary(b"data")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [writeConcern Document Rejection]: document values for
# writeConcern are rejected because the command does not support it.
KILLSESSIONS_WRITECONCERN_DOC_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"writeconcern_doc_{tid}",
        command=lambda ctx, v=val: {
            "killSessions": [{"id": Binary(b"\x00" * 16, subtype=4)}],
            "writeConcern": v,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"killSessions should reject writeConcern {tid}",
    )
    for tid, val in [
        ("empty", {}),
        ("w_1", {"w": 1}),
        ("w_majority", {"w": "majority"}),
        ("j_true", {"j": True}),
    ]
]

# Property [Unrecognized Fields]: unknown fields in the command document
# are silently ignored.
KILLSESSIONS_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_single",
        command=lambda ctx: {
            "killSessions": [],
            "unknownField": 1,
        },
        expected={"ok": 1.0},
        msg="killSessions should ignore a single unknown field",
        marks=(pytest.mark.no_parallel,),
    ),
    CommandTestCase(
        "unrecognized_multiple",
        command=lambda ctx: {
            "killSessions": [],
            "foo": 1,
            "bar": 2,
        },
        expected={"ok": 1.0},
        msg="killSessions should ignore multiple unknown fields",
        marks=(pytest.mark.no_parallel,),
    ),
    CommandTestCase(
        "unrecognized_dollar_prefix",
        command=lambda ctx: {
            "killSessions": [],
            "$unknown": 1,
        },
        expected={"ok": 1.0},
        msg="killSessions should ignore dollar-prefixed unknown field",
        marks=(pytest.mark.no_parallel,),
    ),
    CommandTestCase(
        "unrecognized_other_command",
        command=lambda ctx: {
            "killSessions": [],
            "query": {"x": 1},
        },
        expected={"ok": 1.0},
        msg="killSessions should ignore field from another command",
        marks=(pytest.mark.no_parallel,),
    ),
    CommandTestCase(
        "unrecognized_case_variant",
        command=lambda ctx: {
            "killSessions": [],
            "KillSessions": 1,
        },
        expected={"ok": 1.0},
        msg="killSessions should ignore case-variant of command name",
        marks=(pytest.mark.no_parallel,),
    ),
]

KILLSESSIONS_OPTIONS_TESTS: list[CommandTestCase] = (
    KILLSESSIONS_WRITECONCERN_ACCEPTANCE_TESTS
    + KILLSESSIONS_WRITECONCERN_TYPE_ERROR_TESTS
    + KILLSESSIONS_WRITECONCERN_DOC_ERROR_TESTS
    + KILLSESSIONS_UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_OPTIONS_TESTS))
def test_killSessions_options(collection, test):
    """Test killSessions writeConcern and unrecognized fields."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
