"""Tests for cloneCollectionAsCapped writeConcern validation."""

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
    FLOAT_INFINITY,
    INT32_OVERFLOW,
)

# Property [WriteConcern j Acceptance]: j accepts bool, numeric, and
# null values.
WRITECONCERN_J_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"j_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"j": v},
        },
        expected={"ok": 1.0},
        msg=f"j={id} should succeed",
    )
    for id, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("int32", 0),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", DECIMAL128_ZERO),
        ("null", None),
    ]
]

# Property [WriteConcern j Type Rejection]: j rejects non-coercible
# types with TYPE_MISMATCH_ERROR.
WRITECONCERN_J_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"j_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"j": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"j={id} should fail with type mismatch",
    )
    for id, val in [
        ("string", "true"),
        ("array", [1]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01")),
        ("regex", Regex("abc", "i")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [WriteConcern wtimeout Acceptance]: valid wtimeout values
# are accepted.
WRITECONCERN_WTIMEOUT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wtimeout_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"wtimeout": 0},
        },
        expected={"ok": 1.0},
        msg="wtimeout=0 should succeed",
    ),
    CommandTestCase(
        "wtimeout_positive",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"wtimeout": 1000},
        },
        expected={"ok": 1.0},
        msg="wtimeout=1000 should succeed",
    ),
]

# Property [WriteConcern wtimeout Overflow]: wtimeout values exceeding
# int32 max or infinity produce FAILED_TO_PARSE_ERROR.
WRITECONCERN_WTIMEOUT_OVERFLOW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wtimeout_over_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"wtimeout": INT32_OVERFLOW},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout > INT32_MAX should fail with failed to parse",
    ),
    CommandTestCase(
        "wtimeout_positive_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"wtimeout": FLOAT_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout=+Infinity should fail with failed to parse",
    ),
]

# Property [WriteConcern Unrecognized Fields]: unrecognized fields
# within writeConcern produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
WRITECONCERN_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 100_000,
            "writeConcern": {"unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field in writeConcern should fail",
    ),
]

WC_TESTS: list[CommandTestCase] = (
    WRITECONCERN_J_ACCEPTANCE_TESTS
    + WRITECONCERN_J_TYPE_REJECTION_TESTS
    + WRITECONCERN_WTIMEOUT_ACCEPTANCE_TESTS
    + WRITECONCERN_WTIMEOUT_OVERFLOW_TESTS
    + WRITECONCERN_UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WC_TESTS))
def test_clone_collection_as_capped_wc(database_client, collection, test):
    """Test cloneCollectionAsCapped writeConcern validation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
