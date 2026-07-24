"""
Error tests for $objectToArray expression.

Tests non-object input (all BSON types), wrong arity, and non-object input
resolved via field-path/expression (e.g. composite array paths).
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
    EXPRESSION_TYPE_MISMATCH_ERROR,
    OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_NAN,
)

# Property [Literal-path parity]: representative non-object rejections also
# run through the literal-value path (not just via inserted documents).
# Defined here directly (not by positional index into NOT_OBJECT_ERROR_TESTS
# below) so the mapping is name-stable, and appended to the insert list below
# so they also get insert coverage.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_input",
        doc={"obj": "hello"},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject string input",
    ),
    ExpressionTestCase(
        id="int_input",
        doc={"obj": 42},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject int input",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        doc={"obj": Timestamp(0, 0)},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject timestamp input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_objectToArray_not_object_literal(collection, test):
    """Test $objectToArray error cases with literal values."""
    result = execute_expression(collection, {"$objectToArray": test.doc["obj"]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Non-object rejection]: every non-object BSON type (scalar, array,
# and edge values like empty string/array, false, NaN) is rejected with
# OBJECT_TO_ARRAY_NOT_OBJECT_ERROR (40390) — no type is silently coerced.
NOT_OBJECT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="double_input",
        doc={"obj": 3.14},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject double input",
    ),
    ExpressionTestCase(
        id="bool_input",
        doc={"obj": True},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject bool input",
    ),
    ExpressionTestCase(
        id="array_input",
        doc={"obj": [1, 2, 3]},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject array input",
    ),
    ExpressionTestCase(
        id="decimal128_input",
        doc={"obj": Decimal128("1")},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject decimal128 input",
    ),
    ExpressionTestCase(
        id="int64_input",
        doc={"obj": Int64(1)},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject int64 input",
    ),
    ExpressionTestCase(
        id="objectid_input",
        doc={"obj": ObjectId()},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject objectid input",
    ),
    ExpressionTestCase(
        id="datetime_input",
        doc={"obj": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject datetime input",
    ),
    ExpressionTestCase(
        id="binary_input",
        doc={"obj": Binary(b"x", 0)},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject binary input",
    ),
    ExpressionTestCase(
        id="regex_input",
        doc={"obj": Regex("x")},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject regex input",
    ),
    ExpressionTestCase(
        id="maxkey_input",
        doc={"obj": MaxKey()},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject maxkey input",
    ),
    ExpressionTestCase(
        id="minkey_input",
        doc={"obj": MinKey()},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject minkey input",
    ),
    ExpressionTestCase(
        id="nan_input",
        doc={"obj": FLOAT_NAN},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject NaN input",
    ),
    ExpressionTestCase(
        id="bool_false_input",
        doc={"obj": False},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject bool false input",
    ),
    ExpressionTestCase(
        id="empty_array_input",
        doc={"obj": []},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject empty array input",
    ),
    ExpressionTestCase(
        id="empty_string_input",
        doc={"obj": ""},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject empty string input",
    ),
    ExpressionTestCase(
        id="decimal128_nan_input",
        doc={"obj": DECIMAL128_NAN},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject Decimal128 NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_infinity_input",
        doc={"obj": DECIMAL128_INFINITY},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject Decimal128 Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_infinity_input",
        doc={"obj": DECIMAL128_NEGATIVE_INFINITY},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject Decimal128 -Infinity input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NOT_OBJECT_ERROR_TESTS + TEST_SUBSET_FOR_LITERAL))
def test_objectToArray_not_object_insert(collection, test):
    """Test $objectToArray error cases with values from inserted documents."""
    result = execute_expression_with_insert(collection, {"$objectToArray": "$obj"}, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def test_objectToArray_two_args_error(collection):
    """Test $objectToArray errors with two arguments."""
    result = execute_expression(collection, {"$objectToArray": [{"a": 1}, {"b": 2}]})
    assert_expression_result(result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR)


def test_objectToArray_zero_args_error(collection):
    """Test $objectToArray errors with zero arguments.

    A literal empty argument array is treated as zero arguments (16020), which
    is distinct from an empty array *value* resolved via a field path (40390,
    OBJECT_TO_ARRAY_NOT_OBJECT_ERROR — see empty_array_input above).
    """
    result = execute_expression(collection, {"$objectToArray": []})
    assert_expression_result(result, error_code=EXPRESSION_TYPE_MISMATCH_ERROR)


def test_objectToArray_composite_array_path_error(collection):
    """Test $objectToArray error case from field-path/expression resolution."""
    result = execute_expression_with_insert(
        collection,
        {"$objectToArray": "$a.b"},
        {"a": [{"b": {"x": 1}}, {"b": {"y": 2}}]},
    )
    assert_expression_result(
        result,
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Composite array path should resolve to non-object",
    )
