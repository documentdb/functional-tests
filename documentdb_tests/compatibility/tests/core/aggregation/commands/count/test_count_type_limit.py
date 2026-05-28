"""Tests for count command limit type strictness."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_MIN,
)

# Property [Type Strictness: limit (accepted)]: int32, int64, whole-number
# doubles, and whole-number Decimal128 (including trailing zeros and scientific
# notation) are accepted for the limit field.
COUNT_TYPE_STRICTNESS_LIMIT_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_limit_int32",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": 3},
        expected={"n": 3, "ok": 1.0},
        msg="count should accept int32 for limit",
    ),
    CommandTestCase(
        "type_limit_int64",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": Int64(3)},
        expected={"n": 3, "ok": 1.0},
        msg="count should accept Int64 for limit",
    ),
    CommandTestCase(
        "type_limit_whole_double",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": 3.0},
        expected={"n": 3, "ok": 1.0},
        msg="count should accept whole-number double for limit",
    ),
    CommandTestCase(
        "type_limit_whole_decimal128",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": Decimal128("3")},
        expected={"n": 3, "ok": 1.0},
        msg="count should accept whole-number Decimal128 for limit",
    ),
    CommandTestCase(
        "type_limit_decimal128_trailing_zeros",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": Decimal128("3.00")},
        expected={"n": 3, "ok": 1.0},
        msg="count should accept Decimal128 with trailing zeros for limit",
    ),
    CommandTestCase(
        "type_limit_decimal128_sci_notation",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {"count": ctx.collection, "limit": Decimal128("30E-1")},
        expected={"n": 3, "ok": 1.0},
        msg="count should accept Decimal128 in scientific notation for limit",
    ),
]

# Property [Type Strictness: limit (rejected)]: invalid types and
# non-representable numeric values are rejected for the limit field.
COUNT_TYPE_STRICTNESS_LIMIT_REJECTED_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"type_limit_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {"count": ctx.collection, "limit": v},
            error_code=BAD_VALUE_ERROR,
            msg=f"count should reject {tid} for limit",
        )
        for tid, val in [
            ("string", "hello"),
            ("bool", True),
            ("array", [1, 2]),
            ("object", {"a": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("^abc")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    *[
        CommandTestCase(
            f"type_limit_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {"count": ctx.collection, "limit": v},
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"count should reject {tid} for limit",
        )
        for tid, val in [
            ("fractional_double", 1.5),
            ("fractional_decimal128", DECIMAL128_ONE_AND_HALF),
            ("nan_double", FLOAT_NAN),
            ("neg_nan_double", FLOAT_NEGATIVE_NAN),
            ("nan_decimal128", Decimal128("NaN")),
            ("neg_nan_decimal128", DECIMAL128_NEGATIVE_NAN),
            ("infinity_double", FLOAT_INFINITY),
            ("neg_infinity_double", FLOAT_NEGATIVE_INFINITY),
            ("infinity_decimal128", DECIMAL128_INFINITY),
            ("neg_infinity_decimal128", DECIMAL128_NEGATIVE_INFINITY),
            ("exceeds_int64_decimal128", Decimal128("9999999999999999999999")),
        ]
    ],
    CommandTestCase(
        "type_limit_int64_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "limit": INT64_MIN},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject Int64 minimum value for limit",
    ),
    CommandTestCase(
        "type_limit_decimal128_int64_min",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "limit": Decimal128("-9223372036854775808"),
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject Decimal128 representing int64 minimum for limit",
    ),
]

COUNT_TYPE_STRICTNESS_LIMIT_TESTS = (
    COUNT_TYPE_STRICTNESS_LIMIT_ACCEPTED_TESTS + COUNT_TYPE_STRICTNESS_LIMIT_REJECTED_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_TYPE_STRICTNESS_LIMIT_TESTS))
def test_count_type_limit(database_client, collection, test):
    """Test count command limit type strictness."""
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
