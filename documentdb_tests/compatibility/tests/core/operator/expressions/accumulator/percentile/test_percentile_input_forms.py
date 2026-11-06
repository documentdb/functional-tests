"""Input-form coverage for the $percentile expression operator.

Verifies that ``input`` accepts each expression form (literal array, raw array
expression, scalar, expression operator, field reference, dotted path) and that
an empty input yields [null]. Captured against MongoDB 8.3.4.
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
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Input Forms]: ``input`` accepts any expression that resolves to a
# number or an array of numbers.
PERCENTILE_INPUT_FORMS_TESTS: list[PercentileTest] = [
    PercentileTest(
        "form_literal_array",
        spec=percentile_spec({"$literal": [10, 20, 30]}, [0.5]),
        expected=[20.0],
        msg="$percentile should accept a $literal array as input",
    ),
    PercentileTest(
        "form_raw_array",
        spec=percentile_spec([10, 20, 30], [0.5]),
        expected=[20.0],
        msg="$percentile should accept a raw array expression as input",
    ),
    PercentileTest(
        "form_scalar_number",
        spec=percentile_spec(42, [0.5]),
        expected=[42.0],
        msg="$percentile should accept a single scalar number as input",
    ),
    PercentileTest(
        "form_expression_operator",
        spec=percentile_spec({"$concatArrays": [[10, 20], [30]]}, [0.5]),
        expected=[20.0],
        msg="$percentile should accept an expression operator that resolves to an array",
    ),
    PercentileTest(
        "form_empty_array",
        spec=percentile_spec([], [0.5]),
        expected=[None],
        msg="$percentile over an empty array input should return [null]",
    ),
    PercentileTest(
        "form_field_array",
        spec=percentile_spec("$v", [0.5]),
        document={"v": [10, 20, 30]},
        expected=[20.0],
        msg="$percentile should read an array from a field reference",
    ),
    PercentileTest(
        "form_dotted_path",
        spec=percentile_spec("$a.b", [0.5]),
        document={"a": [{"b": 1}, {"b": 2}, {"b": 3}]},
        expected=[2.0],
        msg="$percentile should resolve a dotted path over an array of objects",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(PERCENTILE_INPUT_FORMS_TESTS))
def test_percentile_input_form(collection, test_case: PercentileTest):
    """Test $percentile input forms."""
    expr = {"$percentile": test_case.spec}
    if test_case.document is not None:
        result = execute_expression_with_insert(collection, expr, test_case.document)
    else:
        result = execute_expression(collection, expr)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
