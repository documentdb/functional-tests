"""
writeConcern field validation tests.

Tests type validation for the writeConcern field itself and its sub-fields
(w, j, wtimeout) across write commands (update, delete, findAndModify).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.query_and_write.write_concern.utils import (
    WRITE_COMMANDS,
    build_cmd,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
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
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_MIN,
)

_NON_DOCUMENT_TYPES = [
    ("string", "majority"),
    ("int32", 1),
    ("int64", Int64(1)),
    ("double", 3.14),
    ("decimal128", Decimal128("1")),
    ("bool", True),
    ("array", [1]),
    ("objectId", ObjectId()),
    ("date", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ("binary", Binary(b"x")),
    ("regex", Regex("x")),
    ("code", Code("f()")),
    ("timestamp", Timestamp(0, 0)),
    ("minKey", MinKey()),
    ("maxKey", MaxKey()),
]

# Property [Non-Document Rejection]: writeConcern field rejects non-document types.
NON_DOCUMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_rejects_non_document_wc_{type_name}",
        command=lambda ctx, _wc=value, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{cmd} should reject writeConcern of type {type_name}.",
    )
    for cmd in WRITE_COMMANDS
    for type_name, value in _NON_DOCUMENT_TYPES
]


@pytest.mark.parametrize("test", pytest_params(NON_DOCUMENT_TESTS))
def test_write_concern_rejects_non_document(collection, test: CommandTestCase):
    """Test writeConcern rejects non-document types."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


_W_INVALID_TYPES = [
    ("bool", True),
    ("array", [1]),
    ("binary", Binary(b"x")),
    ("objectId", ObjectId()),
    ("date", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ("regex", Regex("x")),
    ("code", Code("f()")),
    ("timestamp", Timestamp(0, 0)),
    ("minKey", MinKey()),
    ("maxKey", MaxKey()),
]

# Property [w Type Rejection]: w rejects non-numeric non-string types.
W_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_w_rejects_{type_name}",
        command=lambda ctx, _wc={"w": value}, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"{cmd} should reject w of type {type_name}.",
    )
    for cmd in WRITE_COMMANDS
    for type_name, value in _W_INVALID_TYPES
]


@pytest.mark.parametrize("test", pytest_params(W_TYPE_REJECTION_TESTS))
def test_write_concern_w_rejects_invalid_type(collection, test: CommandTestCase):
    """Test w sub-field rejects non-numeric non-string types."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


_W_INVALID_VALUES = [
    ("null", None, BAD_VALUE_ERROR),
    ("negative", -1, FAILED_TO_PARSE_ERROR),
    ("exceeds_50", 51, FAILED_TO_PARSE_ERROR),
    ("float_nan", FLOAT_NAN, FAILED_TO_PARSE_ERROR),
    ("float_neg_nan", FLOAT_NEGATIVE_NAN, FAILED_TO_PARSE_ERROR),
    ("decimal128_nan", DECIMAL128_NAN, FAILED_TO_PARSE_ERROR),
    ("decimal128_neg_nan", DECIMAL128_NEGATIVE_NAN, FAILED_TO_PARSE_ERROR),
    ("float_inf", FLOAT_INFINITY, FAILED_TO_PARSE_ERROR),
    ("float_neg_inf", FLOAT_NEGATIVE_INFINITY, FAILED_TO_PARSE_ERROR),
    ("decimal128_inf", DECIMAL128_INFINITY, FAILED_TO_PARSE_ERROR),
    ("decimal128_neg_inf", DECIMAL128_NEGATIVE_INFINITY, FAILED_TO_PARSE_ERROR),
    ("tagged_non_numeric", {"dc1": "hello"}, FAILED_TO_PARSE_ERROR),
    ("int64_max", INT64_MAX, FAILED_TO_PARSE_ERROR),
    ("int64_min", INT64_MIN, FAILED_TO_PARSE_ERROR),
]

# Property [w Value Rejection]: w rejects null, negatives, >50, NaN, and Infinity.
W_VALUE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_w_rejects_{val_name}",
        command=lambda ctx, _wc={"w": value}, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        error_code=err,
        msg=f"{cmd} should reject w value {val_name}.",
    )
    for cmd in WRITE_COMMANDS
    for val_name, value, err in _W_INVALID_VALUES
]


@pytest.mark.parametrize("test", pytest_params(W_VALUE_REJECTION_TESTS))
def test_write_concern_w_rejects_invalid_value(collection, test: CommandTestCase):
    """Test w sub-field rejects invalid values."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


_J_INVALID_TYPES = [
    ("string", "yes"),
    ("array", [1]),
    ("object", {"a": 1}),
    ("binary", Binary(b"x")),
    ("objectId", ObjectId()),
    ("date", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ("regex", Regex("x")),
    ("code", Code("f()")),
    ("timestamp", Timestamp(0, 0)),
    ("minKey", MinKey()),
    ("maxKey", MaxKey()),
]

# Property [j Type Rejection]: j rejects non-boolean non-numeric types.
J_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_j_rejects_{type_name}",
        command=lambda ctx, _wc={"w": 1, "j": value}, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{cmd} should reject j of type {type_name}.",
    )
    for cmd in WRITE_COMMANDS
    for type_name, value in _J_INVALID_TYPES
]


@pytest.mark.parametrize("test", pytest_params(J_TYPE_REJECTION_TESTS))
def test_write_concern_j_rejects_invalid_type(collection, test: CommandTestCase):
    """Test j sub-field rejects non-boolean non-numeric types."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [wtimeout Overflow Rejection]: wtimeout rejects Int64 exceeding INT32_MAX.
WTIMEOUT_OVERFLOW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_wtimeout_rejects_int64_overflow",
        command=lambda ctx, _wc={"w": 1, "wtimeout": Int64(INT32_MAX + 1)}, _cmd=cmd: build_cmd(
            _cmd, ctx, _wc
        ),
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"{cmd} should reject wtimeout exceeding INT32_MAX.",
    )
    for cmd in WRITE_COMMANDS
]


@pytest.mark.parametrize("test", pytest_params(WTIMEOUT_OVERFLOW_TESTS))
def test_write_concern_wtimeout_overflow(collection, test: CommandTestCase):
    """Test wtimeout rejects values exceeding INT32_MAX."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [Unknown Field Rejection]: unrecognized fields in writeConcern are rejected.
UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_rejects_unknown_wc_field",
        command=lambda ctx, _wc={"w": 1, "unknownField": 1}, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg=f"{cmd} should reject unrecognized fields in writeConcern.",
    )
    for cmd in WRITE_COMMANDS
]


@pytest.mark.parametrize("test", pytest_params(UNKNOWN_FIELD_TESTS))
def test_write_concern_rejects_unknown_field(collection, test: CommandTestCase):
    """Test writeConcern rejects unrecognized fields."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [w Case Sensitivity]: non-"majority" string w values are rejected on standalone.
W_CASE_SENSITIVITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_w_rejects_{case_name}",
        command=lambda ctx, _wc={"w": value}, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        error_code=BAD_VALUE_ERROR,
        msg=f"{cmd} should reject w:'{value}' (case-sensitive).",
    )
    for cmd in WRITE_COMMANDS
    for case_name, value in [("wrong_case_Majority", "Majority"), ("all_caps_MAJORITY", "MAJORITY")]
]


@pytest.mark.parametrize("test", pytest_params(W_CASE_SENSITIVITY_TESTS))
def test_write_concern_w_case_sensitivity(collection, test: CommandTestCase):
    """Test w field is case-sensitive for 'majority'."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [w Empty String]: empty string w is treated as custom tag, rejected on standalone.
W_EMPTY_STRING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_w_rejects_empty_string",
        command=lambda ctx, _wc={"w": ""}, _cmd=cmd: build_cmd(_cmd, ctx, _wc),
        error_code=BAD_VALUE_ERROR,
        msg=f"{cmd} should reject w:'' (empty string custom tag) on standalone.",
    )
    for cmd in WRITE_COMMANDS
]


@pytest.mark.parametrize("test", pytest_params(W_EMPTY_STRING_TESTS))
def test_write_concern_w_empty_string(collection, test: CommandTestCase):
    """Test w empty string is rejected as custom tag on standalone."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [w Tagged Object Validation]: w as an object must be non-empty with numeric values only.
W_TAGGED_OBJECT_TESTS: list[CommandTestCase] = (
    [
        CommandTestCase(
            f"{cmd}_w_tagged_rejects_empty_object",
            command=lambda ctx, _cmd=cmd: build_cmd(_cmd, ctx, {"w": {}}),
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"{cmd} should reject empty object w (tagged write concern requires tags).",
        )
        for cmd in WRITE_COMMANDS
    ]
    + [
        CommandTestCase(
            f"{cmd}_w_tagged_rejects_string_value",
            command=lambda ctx, _cmd=cmd: build_cmd(_cmd, ctx, {"w": {"dc1": "hello"}}),
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"{cmd} should reject tagged w with non-numeric tag value.",
        )
        for cmd in WRITE_COMMANDS
    ]
    + [
        CommandTestCase(
            f"{cmd}_w_tagged_rejects_nested_object",
            command=lambda ctx, _cmd=cmd: build_cmd(_cmd, ctx, {"w": {"dc1": {"nested": 1}}}),
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"{cmd} should reject tagged w with nested object tag value.",
        )
        for cmd in WRITE_COMMANDS
    ]
)


@pytest.mark.parametrize("test", pytest_params(W_TAGGED_OBJECT_TESTS))
def test_write_concern_w_tagged_object_validation(collection, test: CommandTestCase):
    """Test w sub-field validates tagged write concern object structure."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [wtimeout Extended Overflow Rejection]: wtimeout rejects double, Decimal128,
# and +Infinity values exceeding INT32_MAX, in addition to Int64 overflow.
WTIMEOUT_EXTENDED_OVERFLOW_TESTS: list[CommandTestCase] = (
    [
        CommandTestCase(
            f"{cmd}_wtimeout_rejects_double_overflow",
            command=lambda ctx, _cmd=cmd: build_cmd(
                _cmd, ctx, {"w": 1, "wtimeout": float(INT32_OVERFLOW)}
            ),
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"{cmd} should reject double wtimeout exceeding INT32_MAX.",
        )
        for cmd in WRITE_COMMANDS
    ]
    + [
        CommandTestCase(
            f"{cmd}_wtimeout_rejects_decimal128_overflow",
            command=lambda ctx, _cmd=cmd: build_cmd(
                _cmd, ctx, {"w": 1, "wtimeout": Decimal128(str(INT32_OVERFLOW))}
            ),
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"{cmd} should reject Decimal128 wtimeout exceeding INT32_MAX.",
        )
        for cmd in WRITE_COMMANDS
    ]
    + [
        CommandTestCase(
            f"{cmd}_wtimeout_rejects_float_infinity",
            command=lambda ctx, _cmd=cmd: build_cmd(
                _cmd, ctx, {"w": 1, "wtimeout": FLOAT_INFINITY}
            ),
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"{cmd} should reject +Infinity wtimeout (exceeds INT32_MAX).",
        )
        for cmd in WRITE_COMMANDS
    ]
)


@pytest.mark.parametrize("test", pytest_params(WTIMEOUT_EXTENDED_OVERFLOW_TESTS))
def test_write_concern_wtimeout_extended_overflow(collection, test: CommandTestCase):
    """Test wtimeout rejects double, Decimal128, and +Infinity values exceeding INT32_MAX."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)
