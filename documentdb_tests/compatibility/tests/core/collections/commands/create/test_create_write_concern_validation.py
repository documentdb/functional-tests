"""Tests for the create command write concern validation behavior."""

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
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_OVERFLOW,
)

# Property [WriteConcern Type Validation]: non-document types for
# writeConcern produce TYPE_MISMATCH_ERROR.
CREATE_WC_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"wc_type_{label}",
        command=lambda ctx, val=val: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": val,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{label} writeConcern should fail with type mismatch",
    )
    for label, val in [
        ("string", "invalid"),
        ("int", 1),
        ("bool", True),
        ("array", [1]),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("binary", Binary(b"x")),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [WriteConcern w Type Validation]: non-int/non-string/non-object
# types for w produce FAILED_TO_PARSE_ERROR.
CREATE_WC_W_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"wc_w_type_{tid}",
        command=lambda ctx, v=val: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": v},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"{tid} w should fail",
    )
    for tid, val in [
        ("bool", True),
        ("array", [1]),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [WriteConcern w Validation]: invalid w values produce
# BAD_VALUE_ERROR or FAILED_TO_PARSE_ERROR.
CREATE_WC_W_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="wc_w_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": None},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w:null coerced to empty string should fail",
    ),
    CommandTestCase(
        id="wc_w_negative",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": -1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:-1 (negative) should fail",
    ),
    CommandTestCase(
        id="wc_w_exceeds_50",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 51},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:51 (> 50) should fail",
    ),
    CommandTestCase(
        id="wc_w_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": FLOAT_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:NaN should fail",
    ),
    CommandTestCase(
        id="wc_w_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": FLOAT_NEGATIVE_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:-NaN should fail",
    ),
    CommandTestCase(
        id="wc_w_decimal128_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": DECIMAL128_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Decimal128 NaN should fail",
    ),
    CommandTestCase(
        id="wc_w_decimal128_negative_nan",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": DECIMAL128_NEGATIVE_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Decimal128 -NaN should fail",
    ),
    CommandTestCase(
        id="wc_w_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": FLOAT_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Infinity clamped to INT64_MAX should fail (> 50)",
    ),
    CommandTestCase(
        id="wc_w_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:-Infinity should fail (negative)",
    ),
    CommandTestCase(
        id="wc_w_decimal128_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": DECIMAL128_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Decimal128 Infinity should fail (> 50)",
    ),
    CommandTestCase(
        id="wc_w_decimal128_negative_infinity",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": DECIMAL128_NEGATIVE_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w:Decimal128 -Infinity should fail (negative)",
    ),
    CommandTestCase(
        id="wc_w_tagged_non_numeric_value",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": {"dc1": "hello"}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Tagged object with non-numeric value should fail",
    ),
]

# Property [WriteConcern j Type Strictness]: non-numeric and non-bool types
# for j produce TYPE_MISMATCH_ERROR.
CREATE_WC_J_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id=f"wc_j_type_{tid}",
        command=lambda ctx, v=val: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "j": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{tid} j should fail with type mismatch",
    )
    for tid, val in [
        ("string", "yes"),
        ("array", [1]),
        ("object", {"a": 1}),
        ("binary", Binary(b"x")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex("x")),
        ("code", Code("f()")),
        ("code_with_scope", Code("f()", {"x": 1})),
        ("timestamp", Timestamp(0, 0)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [WriteConcern Unknown Fields]: unknown sub-fields in
# writeConcern produce UNRECOGNIZED_COMMAND_FIELD_ERROR.
CREATE_WC_UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="wc_unknown_field",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown sub-field in writeConcern should fail",
    ),
]

# Property [WriteConcern wtimeout Overflow]: wtimeout numeric values
# exceeding INT32_MAX produce FAILED_TO_PARSE_ERROR.
CREATE_WC_WTIMEOUT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="wc_wtimeout_exceeds_int32_max",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": Int64(INT32_OVERFLOW)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout exceeding the upper int32 bound should fail",
    ),
]

CREATE_WRITE_CONCERN_ERROR_TESTS: list[CommandTestCase] = (
    CREATE_WC_TYPE_ERROR_TESTS
    + CREATE_WC_W_TYPE_ERROR_TESTS
    + CREATE_WC_W_ERROR_TESTS
    + CREATE_WC_J_TYPE_ERROR_TESTS
    + CREATE_WC_UNKNOWN_FIELD_ERROR_TESTS
    + CREATE_WC_WTIMEOUT_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_WRITE_CONCERN_ERROR_TESTS))
def test_create_write_concern_validation(database_client, collection, test):
    """Test create command write concern validation behavior."""
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
