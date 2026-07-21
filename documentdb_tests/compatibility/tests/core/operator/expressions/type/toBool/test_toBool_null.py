"""$toBool null and missing input tests."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.type.utils.convert_variants import (  # noqa: E501
    with_convert_variants,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Null and Missing]: $toBool returns null for null and missing inputs.
TOBOOL_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null",
        msg="Should return null for null input",
        expression={"$toBool": None},
        expected=None,
    ),
    ExpressionTestCase(
        "missing",
        msg="Should return null for missing field",
        expression={"$toBool": MISSING},
        expected=None,
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TOBOOL_NULL_MISSING_TESTS, "$toBool", "bool")),
)
def test_toBool_null(collection, test: ExpressionTestCase):
    """$toBool returns null for null and missing inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
