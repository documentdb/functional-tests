"""Validation of the ``p`` field for the $percentile expression operator.

``p`` must be an array of numbers in [0.0, 1.0]. Captured against MongoDB 8.3.4.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.percentile.utils.percentile_common import (  # noqa: E501
    PercentileTest,
    percentile_spec,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    PERCENTILE_INVALID_P_FIELD_ERROR,
    PERCENTILE_INVALID_P_TYPE_ERROR,
    PERCENTILE_INVALID_P_VALUE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [P Range]: probabilities outside [0.0, 1.0] are rejected; the
# boundaries themselves are valid.
PERCENTILE_P_RANGE_TESTS: list[PercentileTest] = [
    PercentileTest(
        "p_above_one",
        spec=percentile_spec([10, 20, 30], [1.5]),
        error_code=PERCENTILE_INVALID_P_VALUE_ERROR,
        msg="$percentile with p > 1 should fail with INVALID_P_VALUE",
    ),
    PercentileTest(
        "p_below_zero",
        spec=percentile_spec([10, 20, 30], [-0.1]),
        error_code=PERCENTILE_INVALID_P_VALUE_ERROR,
        msg="$percentile with p < 0 should fail with INVALID_P_VALUE",
    ),
    PercentileTest(
        "p_boundary_zero",
        spec=percentile_spec([10, 20, 30], [0.0]),
        expected=[10.0],
        msg="$percentile with p=0.0 is valid and returns the minimum",
    ),
    PercentileTest(
        "p_boundary_one",
        spec=percentile_spec([10, 20, 30], [1.0]),
        expected=[30.0],
        msg="$percentile with p=1.0 is valid and returns the maximum",
    ),
]

# Property [P Field Shape]: ``p`` must be a non-empty array; non-array and empty
# values are rejected, and non-numeric elements are rejected.
PERCENTILE_P_SHAPE_TESTS: list[PercentileTest] = [
    PercentileTest(
        "p_scalar_not_array",
        spec={"input": [10, 20, 30], "p": 0.5, "method": "approximate"},
        error_code=PERCENTILE_INVALID_P_FIELD_ERROR,
        msg="$percentile with a scalar (non-array) p should fail with INVALID_P_FIELD",
    ),
    PercentileTest(
        "p_empty_array",
        spec=percentile_spec([10, 20, 30], []),
        error_code=PERCENTILE_INVALID_P_FIELD_ERROR,
        msg="$percentile with an empty p array should fail with INVALID_P_FIELD",
    ),
    PercentileTest(
        "p_non_numeric_element",
        spec=percentile_spec([10, 20, 30], ["x"]),
        error_code=PERCENTILE_INVALID_P_TYPE_ERROR,
        msg="$percentile with a non-numeric p element should fail with INVALID_P_TYPE",
    ),
]

PERCENTILE_P_VALIDATION_ALL_TESTS = PERCENTILE_P_RANGE_TESTS + PERCENTILE_P_SHAPE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(PERCENTILE_P_VALIDATION_ALL_TESTS))
def test_percentile_p_validation(collection, test_case: PercentileTest):
    """Test $percentile p-field validation."""
    result = execute_expression(collection, {"$percentile": test_case.spec})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
