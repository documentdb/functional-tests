import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [No Cross-Type Coercion]: BSON equality does not implicitly coerce
# values across types.
NO_COERCION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_ne_string",
        expression={"$eq": [1, "1"]},
        expected=False,
        msg="BSON equality should not coerce a number to a string",
    ),
    ExpressionTestCase(
        "int_ne_bool",
        expression={"$eq": [0, False]},
        expected=False,
        msg="BSON equality should not coerce a number to a bool",
    ),
    ExpressionTestCase(
        "one_ne_true",
        expression={"$eq": [1, True]},
        expected=False,
        msg="BSON equality should not coerce a number to a bool",
    ),
    ExpressionTestCase(
        "null_ne_bool",
        expression={"$eq": [None, False]},
        expected=False,
        msg="BSON equality should not coerce null to a bool",
    ),
    ExpressionTestCase(
        "empty_string_ne_null",
        expression={"$eq": ["", None]},
        expected=False,
        msg="BSON equality should not coerce an empty string to null",
    ),
    ExpressionTestCase(
        "zero_ne_null",
        expression={"$eq": [0, None]},
        expected=False,
        msg="BSON equality should not coerce zero to null",
    ),
    ExpressionTestCase(
        "empty_string_ne_false",
        expression={"$eq": ["", False]},
        expected=False,
        msg="BSON equality should not coerce an empty string to false",
    ),
    ExpressionTestCase(
        "empty_array_ne_false",
        expression={"$eq": [[], False]},
        expected=False,
        msg="BSON equality should not coerce an empty array to false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NO_COERCION_TESTS))
def test_bson_types_no_coercion(collection, test):
    """Test BSON equality does not implicitly coerce across types."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
