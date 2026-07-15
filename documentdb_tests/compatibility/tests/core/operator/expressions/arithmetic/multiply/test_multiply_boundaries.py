"""
Overflow and boundary tests for $multiply expression.

Covers INT32/INT64 max/min (and adjacent) values through the
int32->int64->double promotion chain, double overflow/underflow near the
double range limits (including subnormals), and Decimal128
precision/overflow at its boundary values.
"""

import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_MIN_NEGATIVE_SUBNORMAL,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEAR_MIN,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

MULTIPLY_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_overflow",
        expression={"$multiply": [INT32_MAX, 2]},
        expected=Int64(4294967294),
        msg="Should handle int32 overflow",
    ),
    ExpressionTestCase(
        "int32_max_minus_1_times_2",
        expression={"$multiply": [INT32_MAX_MINUS_1, 2]},
        expected=Int64(4294967292),
        msg="Should handle int32 max minus 1 times 2",
    ),
    ExpressionTestCase(
        "int32_underflow",
        expression={"$multiply": [INT32_MIN, 2]},
        expected=Int64(-4294967296),
        msg="Should handle int32 underflow",
    ),
    ExpressionTestCase(
        "int32_min_plus_1_times_2",
        expression={"$multiply": [INT32_MIN_PLUS_1, 2]},
        expected=Int64(-4294967294),
        msg="Should handle int32 min plus 1 times 2",
    ),
    ExpressionTestCase(
        "int64_overflow",
        expression={"$multiply": [INT64_MAX, 2]},
        expected=pytest.approx(1.8446744073709552e19),
        msg="Should handle int64 overflow",
    ),
    ExpressionTestCase(
        "int64_max_minus_1_times_2",
        expression={"$multiply": [INT64_MAX_MINUS_1, 2]},
        expected=pytest.approx(1.8446744073709552e19),
        msg="Should handle int64 max minus 1 times 2",
    ),
    ExpressionTestCase(
        "int64_underflow",
        expression={"$multiply": [INT64_MIN, 2]},
        expected=pytest.approx(-1.8446744073709552e19),
        msg="Should handle int64 underflow",
    ),
    ExpressionTestCase(
        "int64_min_plus_1_times_2",
        expression={"$multiply": [INT64_MIN_PLUS_1, 2]},
        expected=pytest.approx(-1.8446744073709552e19),
        msg="Should handle int64 min plus 1 times 2",
    ),
    ExpressionTestCase(
        "double_overflow",
        expression={"$multiply": [DOUBLE_NEAR_MAX, 10]},
        expected=float("inf"),
        msg="Should handle double overflow",
    ),
    ExpressionTestCase(
        "double_underflow",
        expression={"$multiply": [-DOUBLE_NEAR_MAX, 10]},
        expected=float("-inf"),
        msg="Should handle double underflow",
    ),
    ExpressionTestCase(
        "decimal_precision",
        expression={"$multiply": [Decimal128("1.5"), Decimal128("2.5")]},
        expected=Decimal128("3.75"),
        msg="Should preserve precision for decimal precision",
    ),
    ExpressionTestCase(
        "decimal_precision_small",
        expression={"$multiply": [Decimal128("0.1"), Decimal128("0.2")]},
        expected=Decimal128("0.02"),
        msg="Should preserve precision for decimal precision small",
    ),
    ExpressionTestCase(
        "decimal_large_precision",
        expression={
            "$multiply": [Decimal128("99999999999999999"), Decimal128("99999999999999999")]
        },
        expected=Decimal128("9999999999999999800000000000000001"),
        msg="Should preserve precision for decimal large precision",
    ),
    ExpressionTestCase(
        "decimal_overflow_to_infinity",
        expression={"$multiply": [DECIMAL128_MAX, 2]},
        expected=DECIMAL128_INFINITY,
        msg="Should handle decimal overflow to infinity",
    ),
    ExpressionTestCase(
        "decimal_max_times_one",
        expression={"$multiply": [DECIMAL128_MAX, 1]},
        expected=DECIMAL128_MAX,
        msg="Should preserve decimal max value when multiplied by one",
    ),
    ExpressionTestCase(
        "decimal_small_exponent_times_one",
        expression={"$multiply": [DECIMAL128_SMALL_EXPONENT, 1]},
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="Should preserve decimal small exponent value when multiplied by one",
    ),
    ExpressionTestCase(
        "decimal_large_exponent_times_one",
        expression={"$multiply": [DECIMAL128_LARGE_EXPONENT, 1]},
        expected=Decimal128("1.000000000000000000000000000000000E+6144"),
        msg="Should preserve decimal large exponent value when multiplied by one",
    ),
    ExpressionTestCase(
        "double_min_subnormal_times_two",
        expression={"$multiply": [DOUBLE_MIN_SUBNORMAL, 2]},
        expected=pytest.approx(1e-323),
        msg="Should handle double min subnormal times two",
    ),
    ExpressionTestCase(
        "double_min_negative_subnormal_times_two",
        expression={"$multiply": [DOUBLE_MIN_NEGATIVE_SUBNORMAL, 2]},
        expected=pytest.approx(-1e-323),
        msg="Should handle double min negative subnormal times two",
    ),
    ExpressionTestCase(
        "double_near_min_underflow_to_zero",
        expression={"$multiply": [DOUBLE_NEAR_MIN, 0.0001]},
        expected=pytest.approx(1e-312),
        msg="Should handle double near-min underflow toward zero",
    ),
]


MULTIPLY_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_overflow",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": INT32_MAX, "val1": 2},
        expected=Int64(4294967294),
        msg="Should handle int32 overflow",
    ),
    ExpressionTestCase(
        "int32_max_minus_1_times_2",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": INT32_MAX_MINUS_1, "val1": 2},
        expected=Int64(4294967292),
        msg="Should handle int32 max minus 1 times 2",
    ),
    ExpressionTestCase(
        "int32_underflow",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": INT32_MIN, "val1": 2},
        expected=Int64(-4294967296),
        msg="Should handle int32 underflow",
    ),
    ExpressionTestCase(
        "int32_min_plus_1_times_2",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": INT32_MIN_PLUS_1, "val1": 2},
        expected=Int64(-4294967294),
        msg="Should handle int32 min plus 1 times 2",
    ),
    ExpressionTestCase(
        "int64_overflow",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": INT64_MAX, "val1": 2},
        expected=pytest.approx(1.8446744073709552e19),
        msg="Should handle int64 overflow",
    ),
    ExpressionTestCase(
        "int64_max_minus_1_times_2",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": INT64_MAX_MINUS_1, "val1": 2},
        expected=pytest.approx(1.8446744073709552e19),
        msg="Should handle int64 max minus 1 times 2",
    ),
    ExpressionTestCase(
        "int64_underflow",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": INT64_MIN, "val1": 2},
        expected=pytest.approx(-1.8446744073709552e19),
        msg="Should handle int64 underflow",
    ),
    ExpressionTestCase(
        "int64_min_plus_1_times_2",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": INT64_MIN_PLUS_1, "val1": 2},
        expected=pytest.approx(-1.8446744073709552e19),
        msg="Should handle int64 min plus 1 times 2",
    ),
    ExpressionTestCase(
        "double_overflow",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DOUBLE_NEAR_MAX, "val1": 10},
        expected=float("inf"),
        msg="Should handle double overflow",
    ),
    ExpressionTestCase(
        "double_underflow",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": -DOUBLE_NEAR_MAX, "val1": 10},
        expected=float("-inf"),
        msg="Should handle double underflow",
    ),
    ExpressionTestCase(
        "decimal_precision",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": Decimal128("1.5"), "val1": Decimal128("2.5")},
        expected=Decimal128("3.75"),
        msg="Should preserve precision for decimal precision",
    ),
    ExpressionTestCase(
        "decimal_precision_small",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": Decimal128("0.1"), "val1": Decimal128("0.2")},
        expected=Decimal128("0.02"),
        msg="Should preserve precision for decimal precision small",
    ),
    ExpressionTestCase(
        "decimal_large_precision",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": Decimal128("99999999999999999"), "val1": Decimal128("99999999999999999")},
        expected=Decimal128("9999999999999999800000000000000001"),
        msg="Should preserve precision for decimal large precision",
    ),
    ExpressionTestCase(
        "int32_overflow_mixed",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": INT32_MAX},
        expected=Int64(4294967294),
        msg="Should handle int32 overflow",
    ),
    ExpressionTestCase(
        "int32_max_minus_1_times_2_mixed",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": INT32_MAX_MINUS_1},
        expected=Int64(4294967292),
        msg="Should handle int32 max minus 1 times 2",
    ),
    ExpressionTestCase(
        "int32_underflow_mixed",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": INT32_MIN},
        expected=Int64(-4294967296),
        msg="Should handle int32 underflow",
    ),
    ExpressionTestCase(
        "int32_min_plus_1_times_2_mixed",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": INT32_MIN_PLUS_1},
        expected=Int64(-4294967294),
        msg="Should handle int32 min plus 1 times 2",
    ),
    ExpressionTestCase(
        "int64_overflow_mixed",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": INT64_MAX},
        expected=pytest.approx(1.8446744073709552e19),
        msg="Should handle int64 overflow",
    ),
    ExpressionTestCase(
        "int64_max_minus_1_times_2_mixed",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": INT64_MAX_MINUS_1},
        expected=pytest.approx(1.8446744073709552e19),
        msg="Should handle int64 max minus 1 times 2",
    ),
    ExpressionTestCase(
        "int64_underflow_mixed",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": INT64_MIN},
        expected=pytest.approx(-1.8446744073709552e19),
        msg="Should handle int64 underflow",
    ),
    ExpressionTestCase(
        "int64_min_plus_1_times_2_mixed",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": INT64_MIN_PLUS_1},
        expected=pytest.approx(-1.8446744073709552e19),
        msg="Should handle int64 min plus 1 times 2",
    ),
    ExpressionTestCase(
        "double_overflow_mixed",
        expression={"$multiply": ["$val0", 10]},
        doc={"val0": DOUBLE_NEAR_MAX},
        expected=float("inf"),
        msg="Should handle double overflow",
    ),
    ExpressionTestCase(
        "double_underflow_mixed",
        expression={"$multiply": ["$val0", 10]},
        doc={"val0": -DOUBLE_NEAR_MAX},
        expected=float("-inf"),
        msg="Should handle double underflow",
    ),
    ExpressionTestCase(
        "decimal_precision_mixed",
        expression={"$multiply": ["$val0", Decimal128("2.5")]},
        doc={"val0": Decimal128("1.5")},
        expected=Decimal128("3.75"),
        msg="Should preserve precision for decimal precision",
    ),
    ExpressionTestCase(
        "decimal_precision_small_mixed",
        expression={"$multiply": ["$val0", Decimal128("0.2")]},
        doc={"val0": Decimal128("0.1")},
        expected=Decimal128("0.02"),
        msg="Should preserve precision for decimal precision small",
    ),
    ExpressionTestCase(
        "decimal_large_precision_mixed",
        expression={"$multiply": ["$val0", Decimal128("99999999999999999")]},
        doc={"val0": Decimal128("99999999999999999")},
        expected=Decimal128("9999999999999999800000000000000001"),
        msg="Should preserve precision for decimal large precision",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_LITERAL_TESTS))
def test_multiply_literal(collection, test):
    """Test $multiply from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_FIELD_REF_TESTS))
def test_multiply_field_ref(collection, test):
    """Test $multiply from documents, using all-field-reference and mixed
    literal/field-reference operand forms."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
