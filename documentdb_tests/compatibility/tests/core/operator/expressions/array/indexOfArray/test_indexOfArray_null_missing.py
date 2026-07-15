"""
Null and missing field handling tests for $indexOfArray expression.
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
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Array]: $indexOfArray returns null when array is null or missing.
NULL_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_array",
        doc={"arr": None, "search": 1},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=None,
        msg="$indexOfArray should return null for null array",
    ),
    ExpressionTestCase(
        "null_array_with_start",
        doc={"arr": None, "search": 1, "start": 0},
        expression={"$indexOfArray": ["$arr", "$search", "$start"]},
        expected=None,
        msg="$indexOfArray should return null for null array with start",
    ),
]

# Property [Null Search]: $indexOfArray handles null and missing search values.
NULL_SEARCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_value_in_array",
        doc={"arr": [1, None, 3], "search": None},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=1,
        msg="$indexOfArray should find null in array",
    ),
    ExpressionTestCase(
        "null_value_not_in_array",
        doc={"arr": [1, 2, 3], "search": None},
        expression={"$indexOfArray": ["$arr", "$search"]},
        expected=-1,
        msg="$indexOfArray should return -1 for null not in array",
    ),
]

# Property [Literal Evaluation]: null/missing handling with inline literal values.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_array",
        expression={"$indexOfArray": [None, 1]},
        expected=None,
        msg="$indexOfArray should return null for null array",
    ),
    ExpressionTestCase(
        "null_value_in_array",
        expression={"$indexOfArray": [[1, None, 3], None]},
        expected=1,
        msg="$indexOfArray should find null in array",
    ),
    ExpressionTestCase(
        "missing_array",
        expression={"$indexOfArray": [MISSING, 1]},
        expected=None,
        msg="$indexOfArray should return null for missing array",
    ),
    ExpressionTestCase(
        "missing_value",
        expression={"$indexOfArray": [[1, 2, 3], MISSING]},
        expected=-1,
        msg="$indexOfArray should return -1 for missing search value",
    ),
    ExpressionTestCase(
        "missing_value_null_in_array",
        expression={"$indexOfArray": [[1, None, 3], MISSING]},
        expected=-1,
        msg="$indexOfArray should return -1 for missing search even with null in array",
    ),
]

# Aggregate and test
ALL_TESTS = NULL_ARRAY_TESTS + NULL_SEARCH_TESTS


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_indexOfArray_literal(collection, test):
    """Test $indexOfArray null/missing with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_indexOfArray_insert(collection, test):
    """Test $indexOfArray null with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
