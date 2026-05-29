"""Tests for convertToCapped writeConcern validation."""

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
            "convertToCapped": ctx.collection,
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
            "convertToCapped": ctx.collection,
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

# Property [WriteConcern wtimeout Acceptance]: wtimeout accepts all BSON
# types without error, including non-numeric types and negative values.
WRITECONCERN_WTIMEOUT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wtimeout_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"wtimeout": v},
        },
        expected={"ok": 1.0},
        msg=f"wtimeout={id} should succeed",
    )
    for id, val in [
        ("zero", 0),
        ("positive", 1000),
        ("negative", -1),
        ("string", "hello"),
        ("bool", True),
        ("null", None),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
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

# Property [WriteConcern wtimeout Overflow]: wtimeout values exceeding
# int32 max or infinity produce FAILED_TO_PARSE_ERROR.
WRITECONCERN_WTIMEOUT_OVERFLOW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wtimeout_over_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
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
            "convertToCapped": ctx.collection,
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
            "convertToCapped": ctx.collection,
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
def test_convert_to_capped_wc(database_client, collection, test):
    """Test convertToCapped writeConcern validation."""
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
