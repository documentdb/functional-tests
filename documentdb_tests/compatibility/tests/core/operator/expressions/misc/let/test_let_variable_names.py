"""
Variable name validation tests for $let.

Covers valid and invalid variable naming patterns including starting characters,
special characters, system variable name collisions, and edge cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Invalid variable names — starting character
# ---------------------------------------------------------------------------
INVALID_START_CHAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "start_digit",
        expression={"$let": {"vars": {"1abc": 1}, "in": "$$1abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with digit",
    ),
    ExpressionTestCase(
        "start_dot",
        expression={"$let": {"vars": {".abc": 1}, "in": "$$.abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with dot",
    ),
    ExpressionTestCase(
        "start_backtick",
        expression={"$let": {"vars": {"`abc": 1}, "in": "$$`abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with backtick",
    ),
    ExpressionTestCase(
        "start_bang",
        expression={"$let": {"vars": {"!abc": 1}, "in": "$$!abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with !",
    ),
    ExpressionTestCase(
        "start_at",
        expression={"$let": {"vars": {"@abc": 1}, "in": "$$@abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with @",
    ),
    ExpressionTestCase(
        "start_hash",
        expression={"$let": {"vars": {"#abc": 1}, "in": "$$#abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with #",
    ),
    ExpressionTestCase(
        "start_dollar",
        expression={"$let": {"vars": {"$abc": 1}, "in": "$$$abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with $",
    ),
    ExpressionTestCase(
        "start_percent",
        expression={"$let": {"vars": {"%abc": 1}, "in": "$$%abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with %",
    ),
    ExpressionTestCase(
        "start_caret",
        expression={"$let": {"vars": {"^abc": 1}, "in": "$$^abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with ^",
    ),
    ExpressionTestCase(
        "start_ampersand",
        expression={"$let": {"vars": {"&abc": 1}, "in": "$$&abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with &",
    ),
    ExpressionTestCase(
        "start_star",
        expression={"$let": {"vars": {"*abc": 1}, "in": "$$*abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with *",
    ),
    ExpressionTestCase(
        "start_paren",
        expression={"$let": {"vars": {"(abc": 1}, "in": "$$(abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with (",
    ),
    ExpressionTestCase(
        "start_rparen",
        expression={"$let": {"vars": {")abc": 1}, "in": "$$)abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with )",
    ),
    ExpressionTestCase(
        "start_slash",
        expression={"$let": {"vars": {"/abc": 1}, "in": "$$/abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with /",
    ),
    ExpressionTestCase(
        "start_underscore",
        expression={"$let": {"vars": {"_abc": 1}, "in": "$$_abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with underscore",
    ),
    ExpressionTestCase(
        "start_uppercase",
        expression={"$let": {"vars": {"Abc": 1}, "in": "$$Abc"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name starting with uppercase",
    ),
    ExpressionTestCase(
        "system_ROOT",
        expression={"$let": {"vars": {"ROOT": 1}, "in": "$$ROOT"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject system variable name ROOT",
    ),
    ExpressionTestCase(
        "system_DESCEND",
        expression={"$let": {"vars": {"DESCEND": 1}, "in": "$$DESCEND"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject system variable name DESCEND",
    ),
    ExpressionTestCase(
        "system_PRUNE",
        expression={"$let": {"vars": {"PRUNE": 1}, "in": "$$PRUNE"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject system variable name PRUNE",
    ),
    ExpressionTestCase(
        "system_KEEP",
        expression={"$let": {"vars": {"KEEP": 1}, "in": "$$KEEP"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject system variable name KEEP",
    ),
    ExpressionTestCase(
        "system_REMOVE",
        expression={"$let": {"vars": {"REMOVE": 1}, "in": "$$REMOVE"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject system variable name REMOVE",
    ),
    ExpressionTestCase(
        "system_NOW",
        expression={"$let": {"vars": {"NOW": 1}, "in": "$$NOW"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject system variable name NOW",
    ),
    ExpressionTestCase(
        "system_CLUSTER_TIME",
        expression={"$let": {"vars": {"CLUSTER_TIME": 1}, "in": "$$CLUSTER_TIME"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject system variable name CLUSTER_TIME",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_START_CHAR_TESTS))
def test_let_invalid_variable_name_start(collection, test):
    """Test $let rejects variable names starting with invalid characters."""
    result = execute_expression(collection, test.expression)
    assertFailureCode(result, test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Invalid variable names — containing invalid characters
# ---------------------------------------------------------------------------
INVALID_CHAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "contains_dot",
        expression={"$let": {"vars": {"a.b": 1}, "in": "$$a.b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing dot",
    ),
    ExpressionTestCase(
        "contains_hyphen",
        expression={"$let": {"vars": {"a-b": 1}, "in": "$$a-b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing hyphen",
    ),
    ExpressionTestCase(
        "contains_star",
        expression={"$let": {"vars": {"a*b": 1}, "in": "$$a*b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing *",
    ),
    ExpressionTestCase(
        "contains_question",
        expression={"$let": {"vars": {"a?b": 1}, "in": "$$a?b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing ?",
    ),
    ExpressionTestCase(
        "contains_backtick",
        expression={"$let": {"vars": {"a`b": 1}, "in": "$$a`b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing backtick",
    ),
    ExpressionTestCase(
        "contains_bang",
        expression={"$let": {"vars": {"a!b": 1}, "in": "$$a!b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing !",
    ),
    ExpressionTestCase(
        "contains_at",
        expression={"$let": {"vars": {"a@b": 1}, "in": "$$a@b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing @",
    ),
    ExpressionTestCase(
        "contains_hash",
        expression={"$let": {"vars": {"a#b": 1}, "in": "$$a#b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing #",
    ),
    ExpressionTestCase(
        "contains_dollar",
        expression={"$let": {"vars": {"a$b": 1}, "in": "$$a$b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing $",
    ),
    ExpressionTestCase(
        "contains_percent",
        expression={"$let": {"vars": {"a%b": 1}, "in": "$$a%b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing %",
    ),
    ExpressionTestCase(
        "contains_caret",
        expression={"$let": {"vars": {"a^b": 1}, "in": "$$a^b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing ^",
    ),
    ExpressionTestCase(
        "contains_ampersand",
        expression={"$let": {"vars": {"a&b": 1}, "in": "$$a&b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing &",
    ),
    ExpressionTestCase(
        "contains_paren",
        expression={"$let": {"vars": {"a(b": 1}, "in": "$$a(b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing (",
    ),
    ExpressionTestCase(
        "contains_rparen",
        expression={"$let": {"vars": {"a)b": 1}, "in": "$$a)b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing )",
    ),
    ExpressionTestCase(
        "contains_slash",
        expression={"$let": {"vars": {"a/b": 1}, "in": "$$a/b"}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should reject name containing /",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_CHAR_TESTS))
def test_let_invalid_variable_name_chars(collection, test):
    """Test $let rejects variable names containing invalid characters."""
    result = execute_expression(collection, test.expression)
    assertFailureCode(result, test.error_code, msg=test.msg)
