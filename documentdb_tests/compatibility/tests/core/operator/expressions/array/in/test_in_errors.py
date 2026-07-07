"""
Error tests for $in expression.

Tests non-array second argument and wrong arity errors.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
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

# Error: second argument not an array (runs both literal and insert)
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_as_array",
        doc={"val": 1, "arr": "hello"},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject string as array arg",
    ),
    ExpressionTestCase(
        id="int_as_array",
        doc={"val": 1, "arr": 42},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject int as array arg",
    ),
    ExpressionTestCase(
        id="double_as_array",
        doc={"val": 1, "arr": 3.14},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject double as array arg",
    ),
    ExpressionTestCase(
        id="bool_true_as_array",
        doc={"val": 1, "arr": True},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject bool true as array arg",
    ),
    ExpressionTestCase(
        id="bool_false_as_array",
        doc={"val": 1, "arr": False},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject bool false as array arg",
    ),
    ExpressionTestCase(
        id="object_as_array",
        doc={"val": 1, "arr": {"a": 1}},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject object as array arg",
    ),
    ExpressionTestCase(
        id="decimal128_as_array",
        doc={"val": 1, "arr": Decimal128("1")},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject decimal128 as array arg",
    ),
    ExpressionTestCase(
        id="int64_as_array",
        doc={"val": 1, "arr": Int64(1)},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject int64 as array arg",
    ),
    ExpressionTestCase(
        id="binary_as_array",
        doc={"val": 1, "arr": Binary(b"x", 0)},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject binary as array arg",
    ),
    ExpressionTestCase(
        id="datetime_as_array",
        doc={"val": 1, "arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject datetime as array arg",
    ),
    ExpressionTestCase(
        id="objectid_as_array",
        doc={"val": 1, "arr": ObjectId()},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject objectid as array arg",
    ),
    ExpressionTestCase(
        id="regex_as_array",
        doc={"val": 1, "arr": Regex("x")},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject regex as array arg",
    ),
    ExpressionTestCase(
        id="maxkey_as_array",
        doc={"val": 1, "arr": MaxKey()},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject maxkey as array arg",
    ),
    ExpressionTestCase(
        id="minkey_as_array",
        doc={"val": 1, "arr": MinKey()},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject minkey as array arg",
    ),
    ExpressionTestCase(
        id="timestamp_as_array",
        doc={"val": 1, "arr": Timestamp(0, 0)},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject timestamp as array arg",
    ),
    ExpressionTestCase(
        id="null_as_array",
        doc={"val": 1, "arr": None},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject null as array arg",
    ),
]

# Error: missing as array (literal only, MISSING is a field ref)
LITERAL_ONLY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_as_array",
        doc={"val": 1, "arr": MISSING},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="Should reject missing as array arg",
    ),
]

# Aggregate and test
TEST_SUBSET_FOR_LITERAL = [
    NOT_ARRAY_ERROR_TESTS[0],  # string_as_array
    NOT_ARRAY_ERROR_TESTS[-1],  # null_as_array
] + LITERAL_ONLY_TESTS


@pytest.mark.parametrize("test", pytest_params(NOT_ARRAY_ERROR_TESTS))
def test_in_insert(collection, test):
    """Test $in error cases with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Error: wrong arity
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
