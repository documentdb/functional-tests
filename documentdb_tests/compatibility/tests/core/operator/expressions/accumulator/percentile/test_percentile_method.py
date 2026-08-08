"""Validation of ``method`` and the spec document for $percentile.

Only ``method: "approximate"`` is supported (MongoDB 8.x rejects "discrete"
and "continuous"). The spec must be an object containing the required fields
``input``, ``p``, and ``method``. Captured against MongoDB 8.3.4.
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
    BAD_VALUE_ERROR,
    MISSING_FIELD_ERROR,
    PERCENTILE_SPEC_NOT_OBJECT_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Method Validation]: only "approximate" is accepted; other strings
# are rejected, and a non-string method is a type error.
PERCENTILE_METHOD_TESTS: list[PercentileTest] = [
    PercentileTest(
        "method_discrete_unsupported",
        spec=percentile_spec([10, 20, 30], [0.5], "discrete"),
        error_code=BAD_VALUE_ERROR,
        msg="$percentile method 'discrete' is unsupported and should fail with BadValue",
    ),
    PercentileTest(
        "method_continuous_unsupported",
        spec=percentile_spec([10, 20, 30], [0.5], "continuous"),
        error_code=BAD_VALUE_ERROR,
        msg="$percentile method 'continuous' is unsupported and should fail with BadValue",
    ),
    PercentileTest(
        "method_invalid_string",
        spec=percentile_spec([10, 20, 30], [0.5], "exact"),
        error_code=BAD_VALUE_ERROR,
        msg="$percentile with an unknown method string should fail with BadValue",
    ),
    PercentileTest(
        "method_wrong_type",
        spec=percentile_spec([10, 20, 30], [0.5], 5),
        error_code=TYPE_MISMATCH_ERROR,
        msg="$percentile with a non-string method should fail with TypeMismatch",
    ),
]

# Property [Spec Validation]: the spec must be an object with the required
# fields; missing fields, unknown fields, and non-object specs are rejected.
PERCENTILE_SPEC_TESTS: list[PercentileTest] = [
    PercentileTest(
        "spec_missing_method",
        spec={"input": [10, 20, 30], "p": [0.5]},
        error_code=MISSING_FIELD_ERROR,
        msg="$percentile without method should fail with a missing-field error",
    ),
    PercentileTest(
        "spec_missing_input",
        spec={"p": [0.5], "method": "approximate"},
        error_code=MISSING_FIELD_ERROR,
        msg="$percentile without input should fail with a missing-field error",
    ),
    PercentileTest(
        "spec_missing_p",
        spec={"input": [10, 20, 30], "method": "approximate"},
        error_code=MISSING_FIELD_ERROR,
        msg="$percentile without p should fail with a missing-field error",
    ),
    PercentileTest(
        "spec_unknown_field",
        spec={"input": [10, 20, 30], "p": [0.5], "method": "approximate", "foo": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$percentile with an unknown spec field should fail with an unknown-field error",
    ),
    PercentileTest(
        "spec_not_object",
        spec=[1, 2, 3],
        error_code=PERCENTILE_SPEC_NOT_OBJECT_ERROR,
        msg="$percentile with a non-object spec should fail with a spec-not-object error",
    ),
]

PERCENTILE_METHOD_ALL_TESTS = PERCENTILE_METHOD_TESTS + PERCENTILE_SPEC_TESTS


@pytest.mark.parametrize("test_case", pytest_params(PERCENTILE_METHOD_ALL_TESTS))
def test_percentile_method(collection, test_case: PercentileTest):
    """Test $percentile method and spec-document validation."""
    result = execute_expression(collection, {"$percentile": test_case.spec})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
