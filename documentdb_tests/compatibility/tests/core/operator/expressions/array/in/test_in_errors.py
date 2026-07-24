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

# Property [Not Array]: $in rejects non-array second argument across all BSON types.
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_as_array",
        doc={"val": 1, "arr": "hello"},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject string as array arg",
    ),
    ExpressionTestCase(
        "int_as_array",
        doc={"val": 1, "arr": 42},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject int as array arg",
    ),
    ExpressionTestCase(
        "double_as_array",
        doc={"val": 1, "arr": 3.14},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject double as array arg",
    ),
    ExpressionTestCase(
        "bool_true_as_array",
        doc={"val": 1, "arr": True},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject bool true as array arg",
    ),
    ExpressionTestCase(
        "bool_false_as_array",
        doc={"val": 1, "arr": False},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject bool false as array arg",
    ),
    ExpressionTestCase(
        "object_as_array",
        doc={"val": 1, "arr": {"a": 1}},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject object as array arg",
    ),
    ExpressionTestCase(
        "decimal128_as_array",
        doc={"val": 1, "arr": Decimal128("1")},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject decimal128 as array arg",
    ),
    ExpressionTestCase(
        "int64_as_array",
        doc={"val": 1, "arr": Int64(1)},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject int64 as array arg",
    ),
    ExpressionTestCase(
        "binary_as_array",
        doc={"val": 1, "arr": Binary(b"x", 0)},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject binary as array arg",
    ),
    ExpressionTestCase(
        "datetime_as_array",
        doc={"val": 1, "arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject datetime as array arg",
    ),
    ExpressionTestCase(
        "objectid_as_array",
        doc={"val": 1, "arr": ObjectId()},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject objectid as array arg",
    ),
    ExpressionTestCase(
        "regex_as_array",
        doc={"val": 1, "arr": Regex("x")},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject regex as array arg",
    ),
    ExpressionTestCase(
        "maxkey_as_array",
        doc={"val": 1, "arr": MaxKey()},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject maxkey as array arg",
    ),
    ExpressionTestCase(
        "minkey_as_array",
        doc={"val": 1, "arr": MinKey()},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject minkey as array arg",
    ),
    ExpressionTestCase(
        "timestamp_as_array",
        doc={"val": 1, "arr": Timestamp(0, 0)},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject timestamp as array arg",
    ),
    ExpressionTestCase(
        "null_as_array",
        doc={"val": 1, "arr": None},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject null as array arg",
    ),
]

# Property [Missing Field]: $in rejects a missing field as the second argument.
LITERAL_ONLY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_as_array",
        doc={"val": 1, "arr": MISSING},
        expression={"$in": ["$val", "$arr"]},
        error_code=EXPRESSION_IN_NOT_ARRAY_ERROR,
        msg="$in should reject missing as array arg",
    ),
]

# Property [Arity]: $in requires exactly two arguments.
ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        expression={"$in": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$in should reject zero arguments",
    ),
    ExpressionTestCase(
        "one_arg",
        expression={"$in": [[1, 2, 3]]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$in should reject one argument",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$in": [1, [1, 2], 3]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$in should reject three arguments",
    ),
]

ALL_ERROR_TESTS = NOT_ARRAY_ERROR_TESTS + LITERAL_ONLY_TESTS + ARITY_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_in_error(collection, test):
    """Test $in error cases."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
