"""Tests for aggregate command aggregate field type acceptance and rejection."""

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
    BAD_VALUE_ERROR,
    INVALID_NAMESPACE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_ZERO,
)

# Property [Numeric-1 Acceptance]: numeric values equal to 1 activate
# collection-agnostic mode across all numeric types.
AGGREGATE_FIELD_NUMERIC_ONE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "int32_one",
        command={
            "aggregate": 1,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept int32 1 for collection-agnostic mode",
    ),
    CommandTestCase(
        "int64_one",
        command={
            "aggregate": Int64(1),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Int64 1 for collection-agnostic mode",
    ),
    CommandTestCase(
        "double_one",
        command={
            "aggregate": 1.0,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept double 1.0 for collection-agnostic mode",
    ),
    CommandTestCase(
        "decimal128_one",
        command={
            "aggregate": Decimal128("1"),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128('1') for collection-agnostic mode",
    ),
    CommandTestCase(
        "decimal128_precision_loss",
        command={
            "aggregate": Decimal128("0.99999999999999999"),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept Decimal128 that rounds to 1.0 in double precision",
    ),
]

# Property [String Name Acceptance]: string collection names are accepted.
AGGREGATE_FIELD_STRING_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string_name",
        docs=[{"_id": 1}],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept a string collection name",
    ),
]

AGGREGATE_FIELD_ACCEPTANCE_TESTS = (
    AGGREGATE_FIELD_NUMERIC_ONE_TESTS + AGGREGATE_FIELD_STRING_ACCEPTANCE_TESTS
)

# Property [Field Type Rejection]: non-string, non-numeric BSON types for the
# aggregate field are rejected.
AGGREGATE_FIELD_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"reject_{tid}",
        command={"aggregate": val, "pipeline": [], "cursor": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg=f"aggregate should reject {tid} type",
    )
    for tid, val in [
        ("null", None),
        ("bool", True),
        ("array", [1, 2]),
        ("document", {"a": 1}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("regex", Regex(".*")),
        ("binary", Binary(b"hello")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Numeric Value Rejection]: numeric values other than 1 (including
# zero, negative, fractional, NaN, and infinity) are rejected.
AGGREGATE_FIELD_NUMERIC_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "reject_int_0",
        command={
            "aggregate": 0,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject numeric 0",
    ),
    CommandTestCase(
        "reject_int_2",
        command={
            "aggregate": 2,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject numeric value 2",
    ),
    CommandTestCase(
        "reject_int_neg1",
        command={
            "aggregate": -1,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject negative numeric value",
    ),
    CommandTestCase(
        "reject_int64_2",
        command={
            "aggregate": Int64(2),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Int64 value other than 1",
    ),
    CommandTestCase(
        "reject_double_2_5",
        command={
            "aggregate": 2.5,
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject double value other than 1.0",
    ),
    CommandTestCase(
        "reject_decimal128_not_one",
        command={
            "aggregate": Decimal128("0.9999999999999999"),
            "pipeline": [{"$documents": [{"a": 1}]}],
            "cursor": {},
        },
        error_code=BAD_VALUE_ERROR,
        msg="aggregate should reject Decimal128 that does not round to 1.0",
    ),
    *[
        CommandTestCase(
            f"reject_{tid}",
            command=lambda ctx, v=val: {
                "aggregate": v,
                "pipeline": [{"$documents": [{"a": 1}]}],
                "cursor": {},
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"aggregate should reject {tid} numeric value",
        )
        for tid, val in [
            ("double_zero", DOUBLE_ZERO),
            ("double_neg_zero", DOUBLE_NEGATIVE_ZERO),
            ("double_nan", FLOAT_NAN),
            ("double_infinity", FLOAT_INFINITY),
            ("double_neg_infinity", FLOAT_NEGATIVE_INFINITY),
            ("int64_zero", INT64_ZERO),
            ("decimal128_zero", DECIMAL128_ZERO),
            ("decimal128_neg_zero", DECIMAL128_NEGATIVE_ZERO),
            ("decimal128_nan", DECIMAL128_NAN),
            ("decimal128_infinity", DECIMAL128_INFINITY),
            ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
        ]
    ],
]

AGGREGATE_FIELD_REJECTION_TESTS = (
    AGGREGATE_FIELD_TYPE_REJECTION_TESTS + AGGREGATE_FIELD_NUMERIC_REJECTION_TESTS
)

AGGREGATE_FIELD_TESTS = AGGREGATE_FIELD_ACCEPTANCE_TESTS + AGGREGATE_FIELD_REJECTION_TESTS


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_FIELD_TESTS))
def test_aggregate_field(database_client, collection, test):
    """Test aggregate field acceptance and rejection."""
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
