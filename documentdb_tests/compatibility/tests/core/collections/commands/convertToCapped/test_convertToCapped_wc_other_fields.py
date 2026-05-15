"""Tests for convertToCapped writeConcern other field validation."""

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
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    INT32_OVERFLOW,
)

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

# Property [WriteConcern getLastError Acceptance]: the getLastError
# field accepts any BSON type without validation.
WRITECONCERN_GET_LAST_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"gle_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"getLastError": v},
        },
        expected={"ok": 1.0},
        msg=f"getLastError={id} should succeed",
    )
    for id, val in [
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("null", None),
        ("string", "hello"),
        ("array", [1, 2]),
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

# Property [WriteConcern provenance Type Error]: provenance rejects
# non-string types with TYPE_MISMATCH_ERROR.
WRITECONCERN_PROVENANCE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "provenance_int",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"provenance": 42},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="provenance=int should fail with type mismatch",
    ),
]

# Property [WriteConcern provenance Invalid Enum]: provenance with an
# invalid enum string produces BAD_VALUE_ERROR.
WRITECONCERN_PROVENANCE_ENUM_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "provenance_invalid_enum",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"provenance": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="provenance='invalid' should fail with bad value",
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
    CommandTestCase(
        "uppercase_w",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"W": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Case-sensitive: uppercase W should be unrecognized",
    ),
    CommandTestCase(
        "leading_space_w",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {" w": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Whitespace-sensitive: ' w' should be unrecognized",
    ),
]

WC_OTHER_FIELDS_TESTS: list[CommandTestCase] = (
    WRITECONCERN_WTIMEOUT_ACCEPTANCE_TESTS
    + WRITECONCERN_WTIMEOUT_OVERFLOW_TESTS
    + WRITECONCERN_GET_LAST_ERROR_TESTS
    + WRITECONCERN_PROVENANCE_TYPE_ERROR_TESTS
    + WRITECONCERN_PROVENANCE_ENUM_ERROR_TESTS
    + WRITECONCERN_UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WC_OTHER_FIELDS_TESTS))
def test_convert_to_capped_wc_other_fields(database_client, collection, test):
    """Test convertToCapped writeConcern other field validation."""
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
