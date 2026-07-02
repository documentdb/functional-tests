"""Tests for collMod validationLevel and validationAction."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import (
    TimeseriesCollection,
    ViewCollection,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

# Property [validationLevel Success]: a validationLevel equal to off, strict,
# or moderate is accepted, and null is accepted as a no-op.
COLLMOD_VALIDATION_LEVEL_SUCCESS_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"level_{lvl}",
            docs=[{"_id": 1, "a": 1}],
            command=lambda ctx, v=lvl: {"collMod": ctx.collection, "validationLevel": v},
            expected={"ok": Eq(1.0)},
            msg=f"collMod should accept the {lvl} validationLevel",
        )
        for lvl in ["off", "strict", "moderate"]
    ],
    CommandTestCase(
        "level_null",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validationLevel": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null validationLevel as an omitted field",
    ),
]

# Property [validationLevel Type Rejection]: a validationLevel value that is
# neither a string nor null produces a TypeMismatch error.
COLLMOD_VALIDATION_LEVEL_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"level_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "validationLevel": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} validationLevel as a non-string",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("array", ["strict"]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [validationLevel Enum Rejection]: the validationLevel enum is
# case-sensitive and applies no whitespace trimming, so any string other than
# the exact lowercase off, strict, or moderate produces a BadValue error, and a
# dollar-prefixed string is rejected as a literal value rather than a field path
# or variable reference.
COLLMOD_VALIDATION_LEVEL_ENUM_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"level_enum_{tid}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "validationLevel": v},
        error_code=BAD_VALUE_ERROR,
        msg=f"collMod should reject {tid} as a validationLevel enum value",
    )
    for tid, val in [
        ("empty", ""),
        ("arbitrary", "nope"),
        ("capitalized_strict", "Strict"),
        ("uppercase_off", "OFF"),
        ("leading_space", " strict"),
        ("trailing_space", "strict "),
        ("embedded_space", "str ict"),
        ("nbsp", "strict\u00a0"),
        ("dollar", "$"),
        ("dollar_dollar", "$$"),
        ("large_invalid", "x" * 16_000_000),
    ]
]

# Property [validationLevel Unsupported Collection Type Rejection]: a
# validationLevel applied to a collection type that does not support validation
# (a view or a time series collection) is rejected.
COLLMOD_VALIDATION_LEVEL_UNSUPPORTED_TARGET_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"level_unsupported_{target_id}",
        docs=[],
        target_collection=target,
        command=lambda ctx: {"collMod": ctx.collection, "validationLevel": "strict"},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"collMod should reject a validationLevel on a {target_id}",
    )
    for target_id, target in [
        ("view", ViewCollection()),
        ("timeseries", TimeseriesCollection()),
    ]
]

# Property [validationAction Success]: a validationAction equal to error, warn,
# or errorAndLog is accepted, and null is accepted as a no-op.
COLLMOD_VALIDATION_ACTION_SUCCESS_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"action_{action}",
            docs=[{"_id": 1, "a": 1}],
            command=lambda ctx, v=action: {"collMod": ctx.collection, "validationAction": v},
            expected={"ok": Eq(1.0)},
            msg=f"collMod should accept the {action} validationAction",
        )
        for action in ["error", "warn", "errorAndLog"]
    ],
    CommandTestCase(
        "action_null",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"collMod": ctx.collection, "validationAction": None},
        expected={"ok": Eq(1.0)},
        msg="collMod should accept a null validationAction as an omitted field",
    ),
]

# Property [validationAction Type Rejection]: a validationAction value that is
# neither a string nor null produces a TypeMismatch error.
COLLMOD_VALIDATION_ACTION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"action_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "validationAction": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"collMod should reject a {tid} validationAction as a non-string",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool_true", True),
        ("bool_false", False),
        ("array", ["error"]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [validationAction Enum Rejection]: the validationAction enum is
# case-sensitive and applies no whitespace trimming, so any string other than
# the exact lowercase error, warn, or errorAndLog produces a BadValue error, and
# a dollar-prefixed string is rejected as a literal value rather than a field
# path or variable reference.
COLLMOD_VALIDATION_ACTION_ENUM_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"action_enum_{tid}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=val: {"collMod": ctx.collection, "validationAction": v},
        error_code=BAD_VALUE_ERROR,
        msg=f"collMod should reject {tid} as a validationAction enum value",
    )
    for tid, val in [
        ("empty", ""),
        ("arbitrary", "nope"),
        ("capitalized_error", "Error"),
        ("uppercase_warn", "WARN"),
        ("leading_space", " error"),
        ("trailing_space", "error "),
        ("embedded_space", "err or"),
        ("nbsp", "error\u00a0"),
        ("dollar", "$"),
        ("dollar_dollar", "$$"),
        ("large_invalid", "x" * 16_000_000),
    ]
]

# Property [validationAction Unsupported Collection Type Rejection]: a
# validationAction applied to a collection type that does not support validation
# (a view or a time series collection) is rejected.
COLLMOD_VALIDATION_ACTION_UNSUPPORTED_TARGET_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"action_unsupported_{target_id}",
        docs=[],
        target_collection=target,
        command=lambda ctx: {"collMod": ctx.collection, "validationAction": "error"},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"collMod should reject a validationAction on a {target_id}",
    )
    for target_id, target in [
        ("view", ViewCollection()),
        ("timeseries", TimeseriesCollection()),
    ]
]

COLLMOD_VALIDATION_LEVEL_ACTION_TESTS: list[CommandTestCase] = (
    COLLMOD_VALIDATION_LEVEL_SUCCESS_TESTS
    + COLLMOD_VALIDATION_LEVEL_TYPE_ERROR_TESTS
    + COLLMOD_VALIDATION_LEVEL_ENUM_ERROR_TESTS
    + COLLMOD_VALIDATION_LEVEL_UNSUPPORTED_TARGET_ERROR_TESTS
    + COLLMOD_VALIDATION_ACTION_SUCCESS_TESTS
    + COLLMOD_VALIDATION_ACTION_TYPE_ERROR_TESTS
    + COLLMOD_VALIDATION_ACTION_ENUM_ERROR_TESTS
    + COLLMOD_VALIDATION_ACTION_UNSUPPORTED_TARGET_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_VALIDATION_LEVEL_ACTION_TESTS))
def test_collMod_validation_level_action(database_client, collection, register_db_cleanup, test):
    """Test collMod validationLevel and validationAction acceptance and rejection."""
    collection = test.prepare(database_client, collection)
    if collection.database.name != database_client.name:
        register_db_cleanup(f"{collection.database.name}.{collection.name}")
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
