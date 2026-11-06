from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.median.utils.median_common import (  # noqa: E501
    MedianTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Syntax Validation / Errors]: $median expects an object containing
# 'input' and 'method' fields. Invalid formats, missing fields, or invalid
# option values result in appropriate parsing or validation errors.
MEDIAN_ERROR_TESTS: list[MedianTest] = [
    MedianTest(
        "missing_method",
        args={"input": "$values"},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$median should reject configuration with missing method field",
    ),
    MedianTest(
        "invalid_method",
        args={"input": "$values", "method": "exact"},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$median should reject method other than approximate",
    ),
    MedianTest(
        "missing_input",
        args={"method": "approximate"},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$median should reject configuration with missing input field",
    ),
    MedianTest(
        "extra_field",
        args={"input": "$values", "method": "approximate", "extraField": 123},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$median should reject configuration with unrecognized extra fields",
    ),
    MedianTest(
        "non_object_arg_array",
        args=[10, 20],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$median should reject a non-object array argument",
    ),
    MedianTest(
        "non_object_arg_scalar",
        args=123,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$median should reject a non-object scalar argument",
    ),
    MedianTest(
        "fieldpath_bare_dollar",
        args={"input": "$", "method": "approximate"},
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$median should reject bare '$' as an invalid field path in input",
    ),
    MedianTest(
        "fieldpath_double_dollar",
        args={"input": "$$", "method": "approximate"},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$median should reject '$$' as an empty variable name in input",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MEDIAN_ERROR_TESTS))
def test_median_errors(collection, test_case: MedianTest):
    """Test $median error cases."""
    # When test_case.args is a dict, we wrap it in $median directly.
    # When it's not a dict (like list or scalar), we also wrap it directly in $median.
    expression = {"$median": test_case.args}
    result = execute_expression(collection, expression)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
