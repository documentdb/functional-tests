"""Tests for killSessions parameter acceptance."""

from __future__ import annotations

import uuid

import pytest
from bson import Binary, Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT32_MAX,
    INT64_ZERO,
)

# Property [maxTimeMS Acceptance]: maxTimeMS accepts values at both
# boundaries of the valid range across all numeric types.
KILLSESSIONS_MAXTIMEMS_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_{tid}",
        command=lambda ctx, v=val: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "maxTimeMS": v,
        },
        expected={"ok": 1.0},
        msg=f"killSessions should accept {tid} maxTimeMS",
    )
    for tid, val in [
        # Lower boundary (0) in all representations.
        ("int32_zero", 0),
        ("int64_zero", INT64_ZERO),
        ("double_zero", DOUBLE_ZERO),
        ("double_negative_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_zero", DECIMAL128_ZERO),
        ("decimal128_negative_zero", DECIMAL128_NEGATIVE_ZERO),
        # Upper boundary (INT32_MAX) in all representations.
        ("int32_max", INT32_MAX),
        ("int64_max", Int64(INT32_MAX)),
        ("double_max", float(INT32_MAX)),
        ("decimal128_max", Decimal128(str(INT32_MAX))),
        # Null treated as omitted.
        ("null", None),
    ]
]

# Property [writeConcern Null Acceptance]: null writeConcern is treated
# as omitted and accepted.
KILLSESSIONS_WRITECONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "writeconcern_null",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "writeConcern": None,
        },
        expected={"ok": 1.0},
        msg="killSessions should accept null writeConcern",
    ),
]

# Property [Unrecognized Fields]: unknown fields in the command document
# are silently ignored.
KILLSESSIONS_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_single",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "unknownField": 1,
        },
        expected={"ok": 1.0},
        msg="killSessions should ignore a single unknown field",
    ),
    CommandTestCase(
        "unrecognized_multiple",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "foo": 1,
            "bar": 2,
        },
        expected={"ok": 1.0},
        msg="killSessions should ignore multiple unknown fields",
    ),
    CommandTestCase(
        "unrecognized_dollar_prefix",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "$unknown": 1,
        },
        expected={"ok": 1.0},
        msg="killSessions should ignore dollar-prefixed unknown field",
    ),
    CommandTestCase(
        "unrecognized_other_command",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "query": {"x": 1},
        },
        expected={"ok": 1.0},
        msg="killSessions should ignore field from another command",
    ),
]

# Property [readConcern Acceptance]: readConcern with level "local", null,
# empty document, or null level is accepted without error.
KILLSESSIONS_READCONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_local",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"level": "local"},
        },
        expected={"ok": 1.0},
        msg="killSessions should accept readConcern with level local",
    ),
    CommandTestCase(
        "readconcern_null",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": None,
        },
        expected={"ok": 1.0},
        msg="killSessions should accept null readConcern",
    ),
    CommandTestCase(
        "readconcern_empty_doc",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {},
        },
        expected={"ok": 1.0},
        msg="killSessions should accept empty readConcern document",
    ),
    CommandTestCase(
        "readconcern_level_null",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "readConcern": {"level": None},
        },
        expected={"ok": 1.0},
        msg="killSessions should accept readConcern with null level",
    ),
]

# Property [Null Array Element Acceptance]: null elements in the array
# are silently accepted without error.
KILLSESSIONS_NULL_ELEMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "element_null_accepted",
        command=lambda ctx: {"killSessions": [None]},
        expected={"ok": 1.0},
        msg="killSessions should accept null array element",
    ),
    CommandTestCase(
        "element_null_after_valid",
        command=lambda ctx: {"killSessions": [{"id": Binary(uuid.uuid4().bytes, 4)}, None]},
        expected={"ok": 1.0},
        msg="killSessions should accept null element after valid element",
    ),
]

# Property [Stable API V1 Acceptance]: killSessions succeeds with
# apiVersion "1" and non-strict API parameters.
KILLSESSIONS_STABLE_API_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "api_version_1",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "apiVersion": "1",
        },
        expected={"ok": 1.0},
        msg="killSessions should succeed with apiVersion 1",
    ),
    CommandTestCase(
        "api_version_1_strict_false",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "apiVersion": "1",
            "apiStrict": False,
        },
        expected={"ok": 1.0},
        msg="killSessions should succeed with apiVersion 1 and apiStrict false",
    ),
    CommandTestCase(
        "api_version_1_deprecation_true",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "apiVersion": "1",
            "apiDeprecationErrors": True,
        },
        expected={"ok": 1.0},
        msg="killSessions should succeed with apiVersion 1 and apiDeprecationErrors true",
    ),
    CommandTestCase(
        "api_version_1_deprecation_false",
        command=lambda ctx: {
            "killSessions": [{"id": Binary(b"\xde\xad" * 8, subtype=4)}],
            "apiVersion": "1",
            "apiDeprecationErrors": False,
        },
        expected={"ok": 1.0},
        msg="killSessions should succeed with apiVersion 1 and apiDeprecationErrors false",
    ),
]

KILLSESSIONS_ACCEPTANCE_TESTS: list[CommandTestCase] = (
    KILLSESSIONS_MAXTIMEMS_ACCEPTANCE_TESTS
    + KILLSESSIONS_WRITECONCERN_ACCEPTANCE_TESTS
    + KILLSESSIONS_UNRECOGNIZED_FIELD_TESTS
    + KILLSESSIONS_READCONCERN_ACCEPTANCE_TESTS
    + KILLSESSIONS_NULL_ELEMENT_TESTS
    + KILLSESSIONS_STABLE_API_ACCEPTANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(KILLSESSIONS_ACCEPTANCE_TESTS))
def test_killSessions_acceptance(collection, test):
    """Test killSessions parameter acceptance."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=True,
    )
