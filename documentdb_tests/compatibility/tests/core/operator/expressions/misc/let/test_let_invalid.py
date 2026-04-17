"""
Error and invalid usage tests for $let.

Covers argument validation, vars field type validation, undefined variable
references, invalid variable references, and field path errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    EXPRESSION_NOT_OBJECT_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    FAILED_TO_PARSE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
    LET_MISSING_IN_ERROR,
    LET_MISSING_VARS_ERROR,
    LET_NON_OBJECT_ARGUMENT_ERROR,
    LET_UNDEFINED_VARIABLE_ERROR,
    LET_UNKNOWN_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Raw argument errors
# ---------------------------------------------------------------------------
RAW_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_vars",
        expression={"$let": {"in": 1}},
        error_code=LET_MISSING_VARS_ERROR,
        msg="Missing vars should fail",
    ),
    ExpressionTestCase(
        "missing_in",
        expression={"$let": {"vars": {"x": 1}}},
        error_code=LET_MISSING_IN_ERROR,
        msg="Missing in should fail",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$let": {}},
        error_code=LET_MISSING_VARS_ERROR,
        msg="Empty object should fail",
    ),
    ExpressionTestCase(
        "non_object_string",
        expression={"$let": "not_an_object"},
        error_code=LET_NON_OBJECT_ARGUMENT_ERROR,
        msg="String argument should fail",
    ),
    ExpressionTestCase(
        "non_object_array",
        expression={"$let": [1, 2]},
        error_code=LET_NON_OBJECT_ARGUMENT_ERROR,
        msg="Array argument should fail",
    ),
    ExpressionTestCase(
        "non_object_number",
        expression={"$let": 42},
        error_code=LET_NON_OBJECT_ARGUMENT_ERROR,
        msg="Number argument should fail",
    ),
    ExpressionTestCase(
        "non_object_null",
        expression={"$let": None},
        error_code=LET_NON_OBJECT_ARGUMENT_ERROR,
        msg="Null argument should fail",
    ),
    ExpressionTestCase(
        "extra_unknown_field",
        expression={"$let": {"vars": {"x": 1}, "in": "$$x", "extra": 1}},
        error_code=LET_UNKNOWN_FIELD_ERROR,
        msg="Unknown field should fail",
    ),
    ExpressionTestCase(
        "vars_string",
        expression={"$let": {"vars": "not_object", "in": 1}},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="String vars should fail",
    ),
    ExpressionTestCase(
        "vars_array",
        expression={"$let": {"vars": [1, 2], "in": 1}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Array vars should fail",
    ),
    ExpressionTestCase(
        "vars_number",
        expression={"$let": {"vars": 42, "in": 1}},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Number vars should fail",
    ),
    ExpressionTestCase(
        "vars_null",
        expression={"$let": {"vars": None, "in": 1}},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Null vars should fail",
    ),
    ExpressionTestCase(
        "vars_bool",
        expression={"$let": {"vars": True, "in": 1}},
        error_code=EXPRESSION_NOT_OBJECT_ERROR,
        msg="Bool vars should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RAW_ERROR_TESTS))
def test_let_raw_errors(collection, test):
    """Test $let with invalid raw arguments."""
    result = execute_expression(collection, test.expression)
    assertFailureCode(result, test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Expression errors (valid structure but invalid vars/in content)
# ---------------------------------------------------------------------------
EXPRESSION_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "undefined_variable",
        expression={"$let": {"vars": {"x": 1}, "in": "$$undefinedVar"}},
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="Undefined variable should fail",
    ),
    ExpressionTestCase(
        "typo_variable",
        expression={"$let": {"vars": {"myvar": 1}, "in": "$$myVar"}},
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="Typo variable should fail",
    ),
    ExpressionTestCase(
        "vars_same_block_ref",
        expression={"$let": {"vars": {"a": 1, "b": "$$a"}, "in": "$$b"}},
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="Same-block ref with no outer scope should fail",
    ),
    ExpressionTestCase(
        "wrong_type_in_operator",
        expression={"$let": {"vars": {"x": {"a": 1}}, "in": {"$add": ["$$x", 1]}}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Object in $add should fail with type error",
    ),
    ExpressionTestCase(
        "empty_variable_ref",
        expression={"$let": {"vars": {"x": 1}, "in": "$$"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Empty variable ref should fail",
    ),
    ExpressionTestCase(
        "empty_field_path",
        expression={"$let": {"vars": {"x": 1}, "in": "$"}},
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="Empty field path should fail",
    ),
    ExpressionTestCase(
        "multiple_operators",
        expression={"$let": {"vars": {"x": 1}, "in": {"$add": [1, 2], "$subtract": [3, 1]}}},
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="Multiple operators should fail",
    ),
    ExpressionTestCase(
        "trailing_dot",
        expression={"$let": {"vars": {"x": {"a": 1}}, "in": "$$x."}},
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="Trailing dot should fail",
    ),
    ExpressionTestCase(
        "consecutive_dots",
        expression={"$let": {"vars": {"x": {"a": 1}}, "in": "$$x..a"}},
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="Consecutive dots should fail",
    ),
    ExpressionTestCase(
        "dollar_field_path",
        expression={"$let": {"vars": {"x": {"$a": 1}}, "in": "$$x.$a"}},
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="Dollar-prefixed field in path should fail",
    ),
    ExpressionTestCase(
        "double_dollar_path",
        expression={"$let": {"vars": {"x": {"a": 1}}, "in": "$$x.$$a"}},
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="Double-dollar in path should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EXPRESSION_ERROR_TESTS))
def test_let_expression_errors(collection, test):
    """Test $let with invalid expressions in vars or in."""
    result = execute_expression(collection, test.expression)
    assertFailureCode(result, test.error_code, msg=test.msg)
