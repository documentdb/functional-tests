"""Null and missing input handling for the $percentile expression operator.

A null or missing ``input`` yields one null per requested percentile.
Captured against MongoDB 8.3.4.
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

# Property [Null/Missing Input]: null or missing input produces [null], one per p.
PERCENTILE_NULL_TESTS: list[PercentileTest] = [
    PercentileTest(
        "null_input",
        spec=percentile_spec({"$literal": None}, [0.5]),
        expected=[None],
        msg="$percentile over a null input should return [null]",
    ),
    PercentileTest(
        "null_input_multiple_p",
        spec=percentile_spec({"$literal": None}, [0.25, 0.75]),
        expected=[None, None],
        msg="$percentile over a null input should return one null per requested p",
    ),
    PercentileTest(
        "missing_input_field",
        spec=percentile_spec("$v", [0.5]),
        document={"x": 1},
        expected=[None],
        msg="$percentile over a missing input field should return [null]",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(PERCENTILE_NULL_TESTS))
def test_percentile_null(collection, test_case: PercentileTest):
    """Test $percentile null and missing input handling."""
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
