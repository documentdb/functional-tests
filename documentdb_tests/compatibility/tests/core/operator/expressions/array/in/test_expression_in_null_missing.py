"""
Null and missing field handling tests for $in expression.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# ---------------------------------------------------------------------------
# Success: null/missing handling (runs both literal and insert)
# ---------------------------------------------------------------------------
NULL_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="null_value_in_array",
        value=None,
        array=[1, None, 3],
        expected=True,
        msg="Should find null value in array containing null",
    ),
    ArrayTestClass(
        id="null_value_not_in_array",
        value=None,
        array=[1, 2, 3],
        expected=False,
        msg="Should not find null in array without null",
    ),
]

# ---------------------------------------------------------------------------
# Success: missing value handling (literal only, MISSING is a field ref)
# ---------------------------------------------------------------------------
LITERAL_ONLY_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="missing_value",
        value=MISSING,
        array=[1, 2, 3],
        expected=False,
        msg="Should not find missing value in array",
    ),
    ArrayTestClass(
        id="missing_value_null_in_array",
        value=MISSING,
        array=[1, None, 3],
        expected=False,
        msg="Should not find missing value even with null in array",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
TEST_SUBSET_FOR_LITERAL = [
    NULL_TESTS[0],  # null_value_in_array
    NULL_TESTS[1],  # null_value_not_in_array
] + LITERAL_ONLY_TESTS


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_in_literal(collection, test):
    """Test $in null/missing with literal values."""
    result = execute_expression(collection, {"$in": [test.value, test.array]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(NULL_TESTS))
def test_in_insert(collection, test):
    """Test $in null with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$in": ["$val", "$arr"]}, {"val": test.value, "arr": test.array}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
