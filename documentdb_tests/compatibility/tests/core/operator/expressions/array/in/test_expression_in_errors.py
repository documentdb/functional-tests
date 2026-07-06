"""
Error tests for $in expression.

Tests non-array second argument and wrong arity errors.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.arrays_in_common import (  # noqa: E501
    InTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_IN_NOT_ARRAY_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# ---------------------------------------------------------------------------
# Error: second argument not an array (runs both literal and insert)
# ---------------------------------------------------------------------------
NOT_ARRAY_ERROR_TESTS: list[InTest] = [
    InTest(
        id="string_as_array",
        value=1,
        array="hello",
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject string as array arg",
    ),
    InTest(
        id="int_as_array",
        value=1,
        array=42,
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject int as array arg",
    ),
    InTest(
        id="double_as_array",
        value=1,
        array=3.14,
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject double as array arg",
    ),
    InTest(
        id="bool_true_as_array",
        value=1,
        array=True,
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject bool true as array arg",
    ),
    InTest(
        id="bool_false_as_array",
        value=1,
        array=False,
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject bool false as array arg",
    ),
    InTest(
        id="object_as_array",
        value=1,
        array={"a": 1},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject object as array arg",
    ),
    InTest(
        id="decimal128_as_array",
        value=1,
        array=Decimal128("1"),
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject decimal128 as array arg",
    ),
    InTest(
        id="int64_as_array",
        value=1,
        array=Int64(1),
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject int64 as array arg",
    ),
    InTest(
        id="binary_as_array",
        value=1,
        array=Binary(b"x", 0),
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject binary as array arg",
    ),
    InTest(
        id="datetime_as_array",
        value=1,
        array=datetime(2024, 1, 1),
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject datetime as array arg",
    ),
    InTest(
        id="objectid_as_array",
        value=1,
        array=ObjectId(),
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject objectid as array arg",
    ),
    InTest(
        id="regex_as_array",
        value=1,
        array=Regex("x"),
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject regex as array arg",
    ),
    InTest(
        id="maxkey_as_array",
        value=1,
        array=MaxKey(),
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject maxkey as array arg",
    ),
    InTest(
        id="minkey_as_array",
        value=1,
        array=MinKey(),
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject minkey as array arg",
    ),
    InTest(
        id="timestamp_as_array",
        value=1,
        array=Timestamp(0, 0),
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject timestamp as array arg",
    ),
    InTest(
        id="null_as_array",
        value=1,
        array=None,
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject null as array arg",
    ),
]

# ---------------------------------------------------------------------------
# Error: missing as array (literal only, MISSING is a field ref)
# ---------------------------------------------------------------------------
LITERAL_ONLY_TESTS: list[InTest] = [
    InTest(
        id="missing_as_array",
        value=1,
        array=MISSING,
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject missing as array arg",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
TEST_SUBSET_FOR_LITERAL = [
    NOT_ARRAY_ERROR_TESTS[0],  # string_as_array
    NOT_ARRAY_ERROR_TESTS[-1],  # null_as_array
] + LITERAL_ONLY_TESTS


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_in_literal(collection, test):
    """Test $in error cases with literal values."""
    result = execute_expression(collection, {"$in": [test.value, test.array]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(NOT_ARRAY_ERROR_TESTS))
def test_in_insert(collection, test):
    """Test $in error cases with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$in": ["$val", "$arr"]}, {"val": test.value, "arr": test.array}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# ---------------------------------------------------------------------------
# Error: wrong arity
# ---------------------------------------------------------------------------
ARITY_ERROR_TESTS = [
    pytest.param({"$in": []}, id="zero_args"),
    pytest.param({"$in": [[1, 2, 3]]}, id="one_arg"),
    pytest.param({"$in": [1, [1, 2], 3]}, id="three_args"),
]


@pytest.mark.parametrize("expr", ARITY_ERROR_TESTS)
def test_in_arity_error(collection, expr):
    """Test $in errors with wrong number of arguments."""
    result = execute_expression(collection, expr)
    assert_expression_result(result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR)
