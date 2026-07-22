"""Numeric data-type and special-value coverage for $percentile.

The ``approximate`` method computes in double precision and always returns
double values, regardless of input numeric type. Captured against MongoDB 8.3.4.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.percentile.utils.percentile_common import (  # noqa: E501
    PercentileTest,
    percentile_spec,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Numeric Types]: $percentile accepts all numeric BSON types and
# returns a double under the approximate method.
PERCENTILE_NUMERIC_TYPE_TESTS: list[PercentileTest] = [
    PercentileTest(
        "type_int32",
        spec=percentile_spec([10, 20, 30], [0.5]),
        expected=[20.0],
        msg="$percentile should compute over int32 input and return a double",
    ),
    PercentileTest(
        "type_int64",
        spec=percentile_spec({"$literal": [Int64(10), Int64(20), Int64(30)]}, [0.5]),
        expected=[20.0],
        msg="$percentile should compute over int64 input and return a double",
    ),
    PercentileTest(
        "type_double",
        spec=percentile_spec({"$literal": [10.0, 20.5, 30.0]}, [0.5]),
        expected=[20.5],
        msg="$percentile should compute over double input",
    ),
    PercentileTest(
        "type_decimal128_returns_double",
        spec=percentile_spec(
            {"$literal": [Decimal128("10"), Decimal128("20"), Decimal128("30")]}, [0.5]
        ),
        expected=[20.0],
        msg="$percentile over Decimal128 input should still return a double (approximate)",
    ),
    PercentileTest(
        "type_mixed_numeric",
        spec=percentile_spec({"$literal": [10, 20.5, Decimal128("30")]}, [0.5]),
        expected=[20.5],
        msg="$percentile should compute across mixed numeric types",
    ),
]

# Property [Special Values]: NaN and infinities participate in ordering;
# the approximate method selects an order statistic accordingly.
PERCENTILE_SPECIAL_VALUE_TESTS: list[PercentileTest] = [
    PercentileTest(
        "special_nan_in_input",
        spec=percentile_spec({"$literal": [10, FLOAT_NAN, 30]}, [0.5]),
        expected=[10.0],
        msg="$percentile should order NaN as the smallest value in the input",
    ),
    PercentileTest(
        "special_positive_infinity",
        spec=percentile_spec({"$literal": [10, FLOAT_INFINITY, 30]}, [0.5]),
        expected=[30.0],
        msg="$percentile should treat +Infinity as the largest value",
    ),
    PercentileTest(
        "special_negative_infinity",
        spec=percentile_spec({"$literal": [FLOAT_NEGATIVE_INFINITY, 10, 30]}, [0.5]),
        expected=[10.0],
        msg="$percentile should treat -Infinity as the smallest value",
    ),
]

PERCENTILE_DATA_TYPE_ALL_TESTS = PERCENTILE_NUMERIC_TYPE_TESTS + PERCENTILE_SPECIAL_VALUE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(PERCENTILE_DATA_TYPE_ALL_TESTS))
def test_percentile_data_types(collection, test_case: PercentileTest):
    """Test $percentile numeric-type and special-value handling."""
    result = execute_expression(collection, {"$percentile": test_case.spec})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
