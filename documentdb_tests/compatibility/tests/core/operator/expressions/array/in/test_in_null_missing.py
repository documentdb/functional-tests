"""
Null and missing field handling tests for $in expression.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Success: null/missing handling (runs both literal and insert)
NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_value_in_array",
        doc={"val": None, "arr": [1, None, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find null value in array containing null",
    ),
    ExpressionTestCase(
        "null_value_not_in_array",
        doc={"val": None, "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="$in should not find null in array without null",
    ),
]

# Success: missing value handling (literal only, MISSING is a field ref)
LITERAL_ONLY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_value",
        doc={"val": MISSING, "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="$in should not find missing value in array",
    ),
    ExpressionTestCase(
        "missing_value_null_in_array",
        doc={"val": MISSING, "arr": [1, None, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="$in should not find missing value even with null in array",
    ),
]

# Aggregate and test
TEST_SUBSET_FOR_LITERAL = [
    NULL_TESTS[0],  # null_value_in_array
    NULL_TESTS[1],  # null_value_not_in_array
] + LITERAL_ONLY_TESTS


@pytest.mark.parametrize("test", pytest_params(NULL_TESTS))
def test_in_insert(collection, test):
    """Test $in null with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
