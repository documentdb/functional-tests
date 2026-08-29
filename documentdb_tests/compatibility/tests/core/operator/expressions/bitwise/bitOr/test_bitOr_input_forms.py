# handle nested lists or literal evals to arrays
from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.bitwise.bitOr.utils.bitOr_common import (  # noqa: E501
    BitOrTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

FIELD_PATH_TESTS = [
    ExpressionTestCase(
        "simple_field_refs",
        expression={"$bitOr": ["$x", "$y", "$a", "$b"]},
        doc={"x": 23, "y": 1093, "a": 130942, "b": 90},
        expected=130943,
        msg="$bitOr of simple field references should return the correct OR",
    ),
    ExpressionTestCase(
        "nested_field_paths",
        expression={"$bitOr": ["$x.y", "$a.b"]},
        doc={"x": {"y": 1093}, "a": {"b": 19304}},
        expected=20333,
        msg="$bitOr of nested field paths should return the correct OR",
    ),
    ExpressionTestCase(
        "array_index_path",
        expression={"$bitOr": ["$a", "$b.0"]},
        doc={"a": 10, "b": [1, 2, 3, 4, 5]},
        expected=11,
        msg="$bitOr with $b.0 should resolve to the first array element",
    ),
    ExpressionTestCase(
        "field_is_array",
        expression={"$bitOr": "$a"},
        doc={"a": [2043, 21, 940282, 1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bitOr of an array leads to a mismatch",
    ),
]

NESTED_EXPR_TESTS: list[BitOrTest] = [
    BitOrTest(
        "nested_bitor_args",
        args=[{"$bitOr": [1, 2]}, {"$bitOr": [3, 4]}],
        expected=7,
        msg="$bitOr whose operands are themselves $bitOr expressions should return 7",
    ),
    BitOrTest(
        "nested_bitor_mixed",
        args=[10, {"$bitOr": [4, 6, 8, 22]}],
        expected=30,
        msg="$bitOr of a literal and a nested $bitOr should return 30",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(FIELD_PATH_TESTS))
def test_bitOr_field_paths(collection, test_case: ExpressionTestCase):
    """Test $bitOr with field path inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


@pytest.mark.parametrize("test_case", pytest_params(NESTED_EXPR_TESTS))
def test_bitOr_nested_expressions(collection, test_case: BitOrTest):
    """Test $bitOr with nested $bitOr expressions."""
    result = execute_expression(collection, {"$bitOr": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
