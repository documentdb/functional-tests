"""
Null and missing field handling tests for $indexOfArray expression.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.array.indexOfArray.utils.indexOfArray_common import (  # noqa: E501
    IndexOfArrayTest,
    build_args,
    build_insert_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# ---------------------------------------------------------------------------
# Success: null/missing array → null (runs both literal and insert)
# ---------------------------------------------------------------------------
NULL_ARRAY_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="null_array",
        array=None,
        search=1,
        expected=None,
        msg="Should return null for null array",
    ),
    IndexOfArrayTest(
        id="null_array_with_start",
        array=None,
        search=1,
        start=0,
        expected=None,
        msg="Should return null for null array with start",
    ),
]

# ---------------------------------------------------------------------------
# Success: null/missing as search value (runs both literal and insert)
# ---------------------------------------------------------------------------
NULL_SEARCH_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="null_value_in_array",
        array=[1, None, 3],
        search=None,
        expected=1,
        msg="Should find null in array",
    ),
    IndexOfArrayTest(
        id="null_value_not_in_array",
        array=[1, 2, 3],
        search=None,
        expected=-1,
        msg="Should return -1 for null not in array",
    ),
]

# ---------------------------------------------------------------------------
# Literal only: MISSING field refs
# ---------------------------------------------------------------------------
LITERAL_ONLY_TESTS: list[IndexOfArrayTest] = [
    IndexOfArrayTest(
        id="missing_array",
        array=MISSING,
        search=1,
        expected=None,
        msg="Should return null for missing array",
    ),
    IndexOfArrayTest(
        id="missing_value",
        array=[1, 2, 3],
        search=MISSING,
        expected=-1,
        msg="Should return -1 for missing search value",
    ),
    IndexOfArrayTest(
        id="missing_value_null_in_array",
        array=[1, None, 3],
        search=MISSING,
        expected=-1,
        msg="Should return -1 for missing search even with null in array",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_TESTS = NULL_ARRAY_TESTS + NULL_SEARCH_TESTS

TEST_SUBSET_FOR_LITERAL = [
    NULL_ARRAY_TESTS[0],  # null_array
    NULL_SEARCH_TESTS[0],  # null_value_in_array
] + LITERAL_ONLY_TESTS


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_indexOfArray_literal(collection, test):
    """Test $indexOfArray null/missing with literal values."""
    result = execute_expression(collection, {"$indexOfArray": build_args(test)})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_indexOfArray_insert(collection, test):
    """Test $indexOfArray null with values from inserted documents."""
    args, doc = build_insert_args(test)
    result = execute_expression_with_insert(collection, {"$indexOfArray": args}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
