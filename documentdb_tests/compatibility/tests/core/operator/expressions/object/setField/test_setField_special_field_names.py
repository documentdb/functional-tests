"""
Tests for $setField special field names: dotted, dollar-prefixed, empty string,
_id, unicode, numeric-looking, null characters.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import NULL_CHAR_IN_FIELD_NAME_ERROR
from documentdb_tests.framework.parametrize import pytest_params

SPECIAL_NAME_TESTS: list[ExpressionTestCase] = [
    # Dotted
    ExpressionTestCase(
        "single_dot",
        expression={"$setField": {"field": "price.usd", "input": {}, "value": 9.99}},
        expected={"price.usd": 9.99},
        msg="Single-dot field name should succeed as literal key",
    ),
    ExpressionTestCase(
        "multi_dot",
        expression={"$setField": {"field": "a.b.c.d", "input": {}, "value": 1}},
        expected={"a.b.c.d": 1},
        msg="Multi-dot field name should succeed as literal key",
    ),
    ExpressionTestCase(
        "leading_dot",
        expression={"$setField": {"field": ".xy", "input": {}, "value": 1}},
        expected={".xy": 1},
        msg="Leading-dot field name should succeed as literal key",
    ),
    ExpressionTestCase(
        "trailing_dot",
        expression={"$setField": {"field": "xy.", "input": {}, "value": 1}},
        expected={"xy.": 1},
        msg="Trailing-dot field name should succeed as literal key",
    ),
    ExpressionTestCase(
        "only_dots",
        expression={"$setField": {"field": "...", "input": {}, "value": 1}},
        expected={"...": 1},
        msg="Only-dots field name should succeed as literal key",
    ),
    ExpressionTestCase(
        "double_dot",
        expression={"$setField": {"field": "..zz", "input": {}, "value": 1}},
        expected={"..zz": 1},
        msg="Double-leading-dot field name should succeed as literal key",
    ),
    # Dollar-prefixed (using $const/$literal)
    ExpressionTestCase(
        "dollar_mid",
        expression={"$setField": {"field": "a$b", "input": {}, "value": 1}},
        expected={"a$b": 1},
        msg="Dollar-in-middle field name should succeed as literal key",
    ),
    ExpressionTestCase(
        "dollar_prefix_const",
        expression={"$setField": {"field": {"$const": "$a"}, "input": {}, "value": 1}},
        expected={"$a": 1},
        msg="Dollar-prefixed field via $const should succeed as literal key",
    ),
    ExpressionTestCase(
        "dollar_dot_const",
        expression={"$setField": {"field": {"$const": "$x.$y"}, "input": {}, "value": 1}},
        expected={"$x.$y": 1},
        msg="Dollar+dot field via $const should succeed as literal key",
    ),
    ExpressionTestCase(
        "dollar_dot_prefix_const",
        expression={"$setField": {"field": {"$const": ".$xz"}, "input": {}, "value": 1}},
        expected={".$xz": 1},
        msg="Dot+dollar field via $const should succeed as literal key",
    ),
    ExpressionTestCase(
        "double_dollar_const",
        expression={"$setField": {"field": {"$const": "$$var"}, "input": {}, "value": 1}},
        expected={"$$var": 1},
        msg="Double-dollar field via $const should succeed as literal key",
    ),
    ExpressionTestCase(
        "triple_dollar_literal",
        expression={"$setField": {"field": {"$literal": "$$$"}, "input": {}, "value": 1}},
        expected={"$$$": 1},
        msg="Triple-dollar field via $literal should succeed as literal key",
    ),
    ExpressionTestCase(
        "a_dollar_b_dot",
        expression={"$setField": {"field": "a.$b", "input": {}, "value": 1}},
        expected={"a.$b": 1},
        msg="a.$b field name should succeed as literal key",
    ),
    ExpressionTestCase(
        "dollar_x_double_dot_y",
        expression={"$setField": {"field": {"$const": "$x..$y"}, "input": {}, "value": 1}},
        expected={"$x..$y": 1},
        msg="$x..$y field via $const should succeed as literal key",
    ),
    # Misc
    ExpressionTestCase(
        "empty_string",
        expression={"$setField": {"field": "", "input": {}, "value": 1}},
        expected={"": 1},
        msg="Empty string field name should succeed",
    ),
    ExpressionTestCase(
        "space",
        expression={"$setField": {"field": "a b", "input": {}, "value": 1}},
        expected={"a b": 1},
        msg="Space in field name should succeed",
    ),
    ExpressionTestCase(
        "unicode",
        expression={"$setField": {"field": "\u540d\u524d", "input": {}, "value": 1}},
        expected={"\u540d\u524d": 1},
        msg="Unicode field name should succeed",
    ),
    ExpressionTestCase(
        "numeric_string",
        expression={"$setField": {"field": "0", "input": {}, "value": 1}},
        expected={"0": 1},
        msg="Numeric string field name should succeed",
    ),
    ExpressionTestCase(
        "_id_field",
        expression={"$setField": {"field": "_id", "input": {"_id": 1, "a": 2}, "value": 99}},
        expected={"_id": 99, "a": 2},
        msg="Updating _id field should succeed",
    ),
    # Null character validation
    ExpressionTestCase(
        "null_char_direct",
        expression={"$setField": {"field": "a\x00b", "input": {}, "value": 1}},
        error_code=NULL_CHAR_IN_FIELD_NAME_ERROR,
        msg="Null char in field name should error with invalid field name",
    ),
    ExpressionTestCase(
        "null_char_const",
        expression={"$setField": {"field": {"$const": "a\x00b"}, "input": {}, "value": 1}},
        error_code=NULL_CHAR_IN_FIELD_NAME_ERROR,
        msg="Null char in $const field should error with invalid field name",
    ),
    ExpressionTestCase(
        "null_char_literal",
        expression={"$setField": {"field": {"$literal": "a\x00b"}, "input": {}, "value": 1}},
        error_code=NULL_CHAR_IN_FIELD_NAME_ERROR,
        msg="Null char in $literal field should error with invalid field name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPECIAL_NAME_TESTS))
def test_setField_special_names(collection, test):
    """Test $setField with special field names."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result,
        expected=test.expected if test.error_code is None else None,
        error_code=test.error_code,
        msg=test.msg,
    )
