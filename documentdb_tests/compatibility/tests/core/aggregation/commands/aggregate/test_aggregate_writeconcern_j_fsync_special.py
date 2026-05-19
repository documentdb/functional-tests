"""Tests for aggregate command writeConcern j and fsync special value truthiness."""

from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
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
    FLOAT_NEGATIVE_NAN,
)

# Property [writeConcern Sub-field j Special Values]: j accepts special
# numeric values (NaN, Infinity, -Infinity, -0) without type error.
AGGREGATE_WRITECONCERN_J_SPECIAL_VALUES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_j_special_{sid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"j": v},
        },
        expected={"ok": Eq(1.0)},
        msg=f"aggregate should accept j={sid}",
    )
    for sid, val in [
        ("float_nan", FLOAT_NAN),
        ("float_neg_nan", FLOAT_NEGATIVE_NAN),
        ("float_infinity", FLOAT_INFINITY),
        ("float_neg_infinity", FLOAT_NEGATIVE_INFINITY),
        ("double_neg_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_nan", DECIMAL128_NAN),
        ("decimal128_infinity", DECIMAL128_INFINITY),
        ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
        ("decimal128_neg_zero", DECIMAL128_NEGATIVE_ZERO),
    ]
]

# Property [writeConcern Sub-field fsync Special Values]: fsync accepts
# special numeric values (NaN, Infinity, -Infinity, -0) without type error.
AGGREGATE_WRITECONCERN_FSYNC_SPECIAL_VALUES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_fsync_special_{sid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "writeConcern": {"fsync": v},
        },
        expected={"ok": Eq(1.0)},
        msg=f"aggregate should accept fsync={sid}",
    )
    for sid, val in [
        ("float_nan", FLOAT_NAN),
        ("float_neg_nan", FLOAT_NEGATIVE_NAN),
        ("float_infinity", FLOAT_INFINITY),
        ("float_neg_infinity", FLOAT_NEGATIVE_INFINITY),
        ("double_neg_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_nan", DECIMAL128_NAN),
        ("decimal128_infinity", DECIMAL128_INFINITY),
        ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
        ("decimal128_neg_zero", DECIMAL128_NEGATIVE_ZERO),
    ]
]

# Property [writeConcern Sub-field j and fsync Numeric Truthiness]: NaN and
# Infinity are truthy for the j+fsync conflict check; -0.0 is falsy.
AGGREGATE_WRITECONCERN_J_FSYNC_TRUTHINESS_TESTS: list[CommandTestCase] = [
    # Numeric truthy combinations that trigger the conflict
    *[
        CommandTestCase(
            f"wc_j_fsync_conflict_{sid}",
            docs=[{"_id": 1}],
            command=lambda ctx, j=j_val, f=f_val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "writeConcern": {"j": j, "fsync": f},
            },
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"aggregate should reject j+fsync both truthy: {sid}",
        )
        for sid, j_val, f_val in [
            ("j_nan_fsync_true", FLOAT_NAN, True),
            ("j_true_fsync_nan", True, FLOAT_NAN),
            ("j_inf_fsync_true", FLOAT_INFINITY, True),
            ("j_true_fsync_inf", True, FLOAT_INFINITY),
            ("j_nan_fsync_nan", FLOAT_NAN, FLOAT_NAN),
            ("j_int1_fsync_int1", 1, 1),
            ("j_double1_fsync_double1", 1.0, 1.0),
            ("j_dec1_fsync_dec1", Decimal128("1"), Decimal128("1")),
        ]
    ],
    # Numeric falsy values that avoid the conflict
    *[
        CommandTestCase(
            f"wc_j_fsync_no_conflict_{sid}",
            docs=[{"_id": 1}],
            command=lambda ctx, j=j_val, f=f_val: {
                "aggregate": ctx.collection,
                "pipeline": [],
                "cursor": {},
                "writeConcern": {"j": j, "fsync": f},
            },
            expected={"ok": Eq(1.0)},
            msg=f"aggregate should accept j+fsync when one is falsy: {sid}",
        )
        for sid, j_val, f_val in [
            ("j_neg_zero_fsync_true", DOUBLE_NEGATIVE_ZERO, True),
            ("j_true_fsync_neg_zero", True, DOUBLE_NEGATIVE_ZERO),
            ("j_int0_fsync_int1", 0, 1),
            ("j_int1_fsync_int0", 1, 0),
            ("j_double0_fsync_double1", DOUBLE_ZERO, 1.0),
            ("j_double1_fsync_double0", 1.0, DOUBLE_ZERO),
            ("j_dec0_fsync_dec1", DECIMAL128_ZERO, Decimal128("1")),
            ("j_dec1_fsync_dec0", Decimal128("1"), DECIMAL128_ZERO),
        ]
    ],
]

AGGREGATE_WRITECONCERN_J_FSYNC_SPECIAL_TESTS = (
    AGGREGATE_WRITECONCERN_J_SPECIAL_VALUES_TESTS
    + AGGREGATE_WRITECONCERN_FSYNC_SPECIAL_VALUES_TESTS
    + AGGREGATE_WRITECONCERN_J_FSYNC_TRUTHINESS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_WRITECONCERN_J_FSYNC_SPECIAL_TESTS))
def test_aggregate_writeconcern_j_fsync_special(database_client, collection, test):
    """Test aggregate command writeConcern j/fsync special values and truthiness."""
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
