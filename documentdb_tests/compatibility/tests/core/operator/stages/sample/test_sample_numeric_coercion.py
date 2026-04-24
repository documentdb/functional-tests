"""Tests for $sample stage numeric coercion."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_INT64_OVERFLOW,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MAX_COEFFICIENT,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_MAX,
    DOUBLE_PRECISION_LOSS,
    FLOAT_INFINITY,
    INT32_MAX,
    INT32_OVERFLOW,
    INT64_MAX,
)

# Property [Accepted Numeric Types]: whole-number values of all numeric BSON
# types are accepted as size.
SAMPLE_ACCEPTED_NUMERIC_TYPES_TESTS: list[StageTestCase] = [
    StageTestCase(
        "type_int32",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": 2}}, {"$count": "n"}],
        expected=[{"n": 2}],
        msg="$sample should accept int32 as size",
    ),
    StageTestCase(
        "type_int64",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": Int64(2)}}, {"$count": "n"}],
        expected=[{"n": 2}],
        msg="$sample should accept Int64 as size",
    ),
    StageTestCase(
        "type_double_whole",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": 2.0}}, {"$count": "n"}],
        expected=[{"n": 2}],
        msg="$sample should accept whole-number double as size",
    ),
    StageTestCase(
        "type_decimal128_whole",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": Decimal128("2")}}, {"$count": "n"}],
        expected=[{"n": 2}],
        msg="$sample should accept whole-number Decimal128 as size",
    ),
    StageTestCase(
        "type_decimal128_trailing_zeros",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DECIMAL128_TRAILING_ZERO}}, {"$count": "n"}],
        expected=[{"n": 1}],
        msg="$sample should accept Decimal128 with trailing zeros as size",
    ),
    StageTestCase(
        "type_decimal128_many_trailing_zeros",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DECIMAL128_MANY_TRAILING_ZEROS}}, {"$count": "n"}],
        expected=[{"n": 1}],
        msg="$sample should accept Decimal128 with 32 trailing zeros as size",
    ),
]

# Property [Double Coercion]: fractional positive doubles are truncated toward
# zero to determine the effective size.
SAMPLE_DOUBLE_COERCION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "double_truncate_1_9",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": 1.9}}, {"$count": "n"}],
        expected=[{"n": 1}],
        msg="$sample should truncate double 1.9 toward zero to size 1",
    ),
    StageTestCase(
        "double_truncate_2_1",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": 2.1}}, {"$count": "n"}],
        expected=[{"n": 2}],
        msg="$sample should truncate double 2.1 toward zero to size 2",
    ),
]

# Property [Decimal128 Coercion]: fractional Decimal128 values use banker's
# rounding (round half to even), and high-precision coefficients round
# correctly.
SAMPLE_DECIMAL128_COERCION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "decimal128_bankers_1_5",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DECIMAL128_ONE_AND_HALF}}, {"$count": "n"}],
        expected=[{"n": 2}],
        msg="$sample should round Decimal128('1.5') to 2 via banker's rounding",
    ),
    StageTestCase(
        "decimal128_bankers_2_5",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DECIMAL128_TWO_AND_HALF}}, {"$count": "n"}],
        expected=[{"n": 2}],
        msg="$sample should round Decimal128('2.5') to 2 via banker's rounding",
    ),
    StageTestCase(
        "decimal128_bankers_3_5",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": Decimal128("3.5")}}, {"$count": "n"}],
        expected=[{"n": 4}],
        msg="$sample should round Decimal128('3.5') to 4 via banker's rounding",
    ),
    StageTestCase(
        "decimal128_just_above_half",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": Decimal128("0.51")}}, {"$count": "n"}],
        expected=[{"n": 1}],
        msg="$sample should round Decimal128('0.51') up to 1",
    ),
    StageTestCase(
        "decimal128_just_below_1_5",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[
            {"$sample": {"size": Decimal128("1.499999999999999999999999999999999")}},
            {"$count": "n"},
        ],
        expected=[{"n": 1}],
        msg="$sample should round Decimal128 just below 1.5 down to 1",
    ),
    StageTestCase(
        "decimal128_just_below_2_5",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[
            {"$sample": {"size": Decimal128("2.499999999999999999999999999999999")}},
            {"$count": "n"},
        ],
        expected=[{"n": 2}],
        msg="$sample should round Decimal128 just below 2.5 down to 2",
    ),
    StageTestCase(
        "decimal128_34_digit_below_one",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[
            {"$sample": {"size": Decimal128("0." + "9" * 33)}},
            {"$count": "n"},
        ],
        expected=[{"n": 1}],
        msg="$sample should round 34-digit Decimal128 coefficient below 1 up to 1",
    ),
]

# Property [Special Float Values]: positive infinity (double and Decimal128)
# is accepted as a valid size and returns all documents in the collection.
SAMPLE_SPECIAL_FLOAT_SUCCESS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "special_float_inf",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": FLOAT_INFINITY}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept float('inf') and return all documents",
    ),
    StageTestCase(
        "special_decimal128_inf",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DECIMAL128_INFINITY}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept Decimal128('Infinity') and return all documents",
    ),
]

# Property [Large Positive Values]: extreme positive numeric values of all
# types are accepted and return all available documents.
SAMPLE_LARGE_POSITIVE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "large_int32_max",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": INT32_MAX}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept int32 max as size and return all documents",
    ),
    StageTestCase(
        "large_int32_overflow",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": INT32_OVERFLOW}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept int64 value exceeding int32 range as size",
    ),
    StageTestCase(
        "large_int64_max",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": INT64_MAX}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept int64 max as size and return all documents",
    ),
    StageTestCase(
        "large_double_max",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DOUBLE_MAX}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept the maximum double value as size and return all documents",
    ),
    StageTestCase(
        "large_double_max_safe_integer",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": 9_007_199_254_740_991.0}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept max safe integer double (2^53 - 1) as size",
    ),
    StageTestCase(
        "large_double_precision_loss",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": float(DOUBLE_PRECISION_LOSS)}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept precision-loss double beyond 2^53 as size",
    ),
    StageTestCase(
        "large_decimal128_max",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DECIMAL128_MAX}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept Decimal128 max as size and return all documents",
    ),
    StageTestCase(
        "large_decimal128_large_exponent",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DECIMAL128_LARGE_EXPONENT}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept Decimal128 with the largest exponent as size",
    ),
    StageTestCase(
        "large_decimal128_int64_overflow",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DECIMAL128_INT64_OVERFLOW}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept Decimal128 exceeding int64 max as size",
    ),
    StageTestCase(
        "large_decimal128_max_coefficient",
        docs=[{"_id": i} for i in range(5)],
        pipeline=[{"$sample": {"size": DECIMAL128_MAX_COEFFICIENT}}, {"$count": "n"}],
        expected=[{"n": 5}],
        msg="$sample should accept 34-digit all-nines Decimal128 coefficient as size",
    ),
]

SAMPLE_NUMERIC_COERCION_TESTS = (
    SAMPLE_ACCEPTED_NUMERIC_TYPES_TESTS
    + SAMPLE_DOUBLE_COERCION_TESTS
    + SAMPLE_DECIMAL128_COERCION_TESTS
    + SAMPLE_SPECIAL_FLOAT_SUCCESS_TESTS
    + SAMPLE_LARGE_POSITIVE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SAMPLE_NUMERIC_COERCION_TESTS))
def test_sample_numeric_coercion(collection, test_case: StageTestCase):
    """Test $sample stage numeric coercion."""
    if test_case.setup:
        test_case.setup(collection)
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
