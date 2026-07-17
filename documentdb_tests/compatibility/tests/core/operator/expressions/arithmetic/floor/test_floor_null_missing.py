"""Tests for $floor returning null on null and missing-field inputs."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing]: floor returns null when the input is null or a missing field.
FLOOR_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_value",
        doc={"value": None},
        expression={"$floor": ["$value"]},
        expected=None,
        msg="$floor should return null for a null input",
    ),
    ExpressionTestCase(
        "missing_field",
        doc={},
        expression={"$floor": ["$value"]},
        expected=None,
        msg="$floor should return null for a missing field input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FLOOR_NULL_MISSING_TESTS))
def test_floor_null_missing(collection, test):
    """Test $floor null and missing propagation."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
