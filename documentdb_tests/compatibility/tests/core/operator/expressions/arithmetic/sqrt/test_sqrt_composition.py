"""
arithmetic $sqrt tests.

Self-nested $sqrt expressions and field-path lookup tests for $sqrt
(simple/nested/deep/nonexistent paths).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import NON_NUMERIC_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

SQRT_NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_sqrt_2",
        expression={"$sqrt": {"$sqrt": 16}},
        expected=2.0,
        msg="sqrt(sqrt(16)) = 2.0 (double self-nesting)",
    ),
    ExpressionTestCase(
        "nested_sqrt_2_large",
        expression={"$sqrt": {"$sqrt": 65536}},
        expected=16.0,
        msg="sqrt(sqrt(65536)) = 16.0 (self-nesting, large input)",
    ),
    ExpressionTestCase(
        "nested_sqrt_3",
        expression={"$sqrt": {"$sqrt": {"$sqrt": 256}}},
        expected=2.0,
        msg="sqrt(sqrt(sqrt(256))) = 2.0 (triple self-nesting)",
    ),
]


SQRT_FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field",
        expression={"$sqrt": "$a.b"},
        doc={"a": {"b": 16}},
        expected=4.0,
        msg="sqrt(16) = 4.0 resolved via 1-level field path $a.b",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$sqrt": "$a.nonexistent"},
        doc={"a": {"missing": 1}},
        expected=None,
        msg="nonexistent field path returns null",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$sqrt": "$a.b.c.d"},
        doc={"a": {"b": {"c": {"d": 25}}}},
        expected=5.0,
        msg="sqrt(25) = 5.0 resolved via deep field path $a.b.c.d",
    ),
    ExpressionTestCase(
        "array_index_field_path",
        expression={"$sqrt": "$a.0"},
        doc={"a": [4, 9]},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg=(
            "$sqrt should reject a numeric path component over an array, "
            "which resolves non-numeric"
        ),
    ),
]


@pytest.mark.parametrize("test", pytest_params(SQRT_NESTED_TESTS))
def test_sqrt_nested_expression(collection, test):
    """Test $sqrt self-nesting (double and triple nested)"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(SQRT_FIELD_LOOKUP_TESTS))
def test_sqrt_field_lookup(collection, test):
    """Test $sqrt with simple, nested, deep, and nonexistent field paths"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
