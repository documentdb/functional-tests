"""
Tests for $mod expression type smoke tests.

Covers expression-operator input, array/object-expression input, composite
array field paths, array-index field paths, and self-nested $mod.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    MODULO_NON_NUMERIC_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

EXPRESSION_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "expression_operator_dividend",
        expression={"$mod": [{"$add": [7, 3]}, 3]},
        doc={},
        expected=1,
        msg="$add(7,3)=10 mod 3 = 1",
    ),
    ExpressionTestCase(
        "array_expression_single_arg",
        expression={"$mod": [["$x", "$y"]]},
        doc={"x": 10, "y": 3},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$mod requires exactly two arguments; a single array-expression argument is arity 1",
    ),
    ExpressionTestCase(
        "object_expression_dividend",
        expression={"$mod": [{"a": "$x"}, 3]},
        doc={"x": 10},
        error_code=MODULO_NON_NUMERIC_ERROR,
        msg="Object expression dividend is rejected as non-numeric",
    ),
    ExpressionTestCase(
        "composite_array_field_path",
        expression={"$mod": ["$a.b", 3]},
        doc={"a": [{"b": 1}, {"b": 2}]},
        error_code=MODULO_NON_NUMERIC_ERROR,
        msg="Composite array field path resolves to [1,2], a non-numeric array dividend",
    ),
    ExpressionTestCase(
        "array_index_field_path",
        expression={"$mod": ["$a.0.b", 3]},
        doc={"a": [{"b": 7}, {"b": 2}]},
        error_code=MODULO_NON_NUMERIC_ERROR,
        msg="$a.0.b does not do positional array indexing in this context; "
        "it resolves to a non-numeric array dividend",
    ),
    ExpressionTestCase(
        "self_nested_mod",
        expression={"$mod": [{"$mod": ["$v", 10]}, 3]},
        doc={"v": 25},
        expected=2,
        msg="Self-nested $mod: (25 mod 10)=5, 5 mod 3 = 2",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXPRESSION_TYPE_TESTS))
def test_mod_expression_types(collection, test):
    """Test $mod with expression-operator, array/object, and composite field path inputs."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
