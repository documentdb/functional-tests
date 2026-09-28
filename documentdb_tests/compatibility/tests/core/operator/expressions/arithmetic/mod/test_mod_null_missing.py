"""
Null and missing operand tests for $mod expression.

Covers null/missing short-circuiting to a null result in each operand
position, independent of the other operand's value.
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
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    MISSING,
)

MOD_NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": None},
        expected=None,
        msg="Should return null when divisor is null",
    ),
    ExpressionTestCase(
        "null_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": None, "divisor": 3},
        expected=None,
        msg="Should return null when dividend is null",
    ),
    ExpressionTestCase(
        "missing_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": MISSING, "divisor": 3},
        expected=None,
        msg="Should return null when dividend is missing",
    ),
    ExpressionTestCase(
        "missing_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": MISSING},
        expected=None,
        msg="Should return null when divisor is missing",
    ),
    ExpressionTestCase(
        "both_null",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": None, "divisor": None},
        expected=None,
        msg="Should return null when both are null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_NULL_MISSING_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.doc["dividend"], test.doc["divisor"]]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_NULL_MISSING_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents.

    A MISSING dividend/divisor is represented by omitting that key from the
    inserted document entirely, rather than inserting a MISSING sentinel value.
    """
    doc = {}
    if test.doc["dividend"] != MISSING:
        doc["dividend"] = test.doc["dividend"]
    if test.doc["divisor"] != MISSING:
        doc["divisor"] = test.doc["divisor"]
    result = execute_expression_with_insert(collection, test.expression, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
