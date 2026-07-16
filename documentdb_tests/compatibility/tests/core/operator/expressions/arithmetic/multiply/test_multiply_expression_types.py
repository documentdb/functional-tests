"""
Tests for $multiply expression type smoke tests.

Covers array-expression input, object-expression input, composite array field
paths, and array-index field paths per TEST_COVERAGE §3 (per-operator
expression-type checklist).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

EXPRESSION_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_expression_single_operand",
        expression={"$multiply": [["$x", "$y"]]},
        doc={"x": 10, "y": 3},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array literal containing field-path expressions resolves to a "
        "non-numeric array operand",
    ),
    ExpressionTestCase(
        "object_expression_single_operand",
        expression={"$multiply": [{"a": "$x"}]},
        doc={"x": 10},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Object literal containing a field-path expression resolves to a "
        "non-numeric object operand",
    ),
    ExpressionTestCase(
        "composite_array_field_path",
        expression={"$multiply": ["$a.b", 1]},
        doc={"a": [{"b": 2}, {"b": 3}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Composite array field path resolves to [2,3], a non-numeric array operand",
    ),
    ExpressionTestCase(
        "array_index_field_path",
        expression={"$multiply": ["$a.0.b", 3]},
        doc={"a": [{"b": 7}, {"b": 2}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$a.0.b does not do positional array indexing in this context; "
        "it resolves to a non-numeric array operand",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXPRESSION_TYPE_TESTS))
def test_multiply_expression_types(collection, test):
    """Test $multiply with composite array field path and array-index path inputs."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
