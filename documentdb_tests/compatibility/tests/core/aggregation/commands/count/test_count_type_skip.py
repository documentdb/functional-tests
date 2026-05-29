"""Tests for count command skip type strictness."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Type Strictness: skip (rejected)]: all non-numeric BSON types
# produce a TypeMismatch error, and negative values after coercion produce a
# BAD_VALUE_ERROR.
COUNT_TYPE_STRICTNESS_SKIP_REJECTED_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"type_skip_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {"count": ctx.collection, "skip": v},
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"count should reject {tid} for skip",
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
    CommandTestCase(
        "type_skip_negative_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "skip": -1},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject negative int32 for skip",
    ),
    CommandTestCase(
        "type_skip_negative_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "skip": Int64(-5)},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject negative Int64 for skip",
    ),
    CommandTestCase(
        "type_skip_negative_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "skip": -1.5},
        error_code=BAD_VALUE_ERROR,
        msg="count should reject double -1.5 for skip (truncates to -1)",
    ),
    CommandTestCase(
        "type_skip_negative_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "skip": DECIMAL128_NEGATIVE_ONE_AND_HALF,
        },
        error_code=BAD_VALUE_ERROR,
        msg='count should reject Decimal128("-1.5") for skip (rounds to -2)',
    ),
    CommandTestCase(
        "type_skip_neg_inf_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "skip": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject -Infinity double for skip (converts to int64 min)",
    ),
    CommandTestCase(
        "type_skip_neg_inf_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "skip": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject -Infinity Decimal128 for skip (converts to int64 min)",
    ),
]

# Property [Type Strictness: skip (accepted)]: numeric types are accepted for
# the skip field.
COUNT_TYPE_STRICTNESS_SKIP_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_skip_int32_accepted",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": 3},
        expected={"n": 7, "ok": 1.0},
        msg="count should accept int32 for skip",
    ),
    CommandTestCase(
        "type_skip_int64_accepted",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": Int64(3)},
        expected={"n": 7, "ok": 1.0},
        msg="count should accept Int64 for skip",
    ),
    CommandTestCase(
        "type_skip_decimal128_accepted",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": Decimal128("3")},
        expected={"n": 7, "ok": 1.0},
        msg="count should accept Decimal128 for skip",
    ),
    CommandTestCase(
        "type_skip_neg_half_double_accepted",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": -0.5},
        expected={"n": 10, "ok": 1.0},
        msg="count should accept double -0.5 for skip (truncates to 0)",
    ),
    CommandTestCase(
        "type_skip_neg_half_decimal128_accepted",
        docs=[{"_id": i} for i in range(10)],
        command=lambda ctx: {"count": ctx.collection, "skip": DECIMAL128_NEGATIVE_HALF},
        expected={"n": 10, "ok": 1.0},
        msg='count should accept Decimal128("-0.5") for skip (banker\'s rounds to 0)',
    ),
    CommandTestCase(
        "type_skip_neg_0_6_decimal128_rejected",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "skip": Decimal128("-0.6")},
        error_code=BAD_VALUE_ERROR,
        msg='count should reject Decimal128("-0.6") for skip (rounds to -1)',
    ),
]

COUNT_TYPE_STRICTNESS_SKIP_TESTS = (
    COUNT_TYPE_STRICTNESS_SKIP_REJECTED_TESTS + COUNT_TYPE_STRICTNESS_SKIP_ACCEPTED_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_TYPE_STRICTNESS_SKIP_TESTS))
def test_count_type_skip(database_client, collection, test):
    """Test count command skip type strictness."""
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
