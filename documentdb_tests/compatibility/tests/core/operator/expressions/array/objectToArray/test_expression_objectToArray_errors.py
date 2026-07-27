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
# below) so the mapping is name-stable, and appended to ALL_ERROR_TESTS below
# so they also get insert coverage.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_input",
        expression={"$objectToArray": "hello"},
        doc={"obj": "hello"},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject string input",
    ),
    ExpressionTestCase(
        id="int_input",
        expression={"$objectToArray": 42},
        doc={"obj": 42},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject int input",
    ),
    ExpressionTestCase(
        id="timestamp_input",
        expression={"$objectToArray": Timestamp(0, 0)},
        doc={"obj": Timestamp(0, 0)},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject timestamp input",
    ),
]


# Property [Arity/structure errors]: a wrong number of top-level arguments
# (two, or zero via a literal empty array) is rejected with
# EXPRESSION_TYPE_MISMATCH_ERROR — distinct from an empty array *value*
# resolved via a field path, which is OBJECT_TO_ARRAY_NOT_OBJECT_ERROR (see
# empty_array_input above). These have no doc, so they only run through the
# literal path below (no insert-path counterpart makes sense for them).
ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="two_args",
        expression={"$objectToArray": [{"a": 1}, {"b": 2}]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject two arguments",
    ),
    ExpressionTestCase(
        id="zero_args",
        expression={"$objectToArray": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="A literal empty argument array is treated as zero arguments",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL + ARITY_ERROR_TESTS))
def test_objectToArray_not_object_literal(collection, test):
    """Test $objectToArray error cases with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [Non-object rejection]: every non-object BSON type (scalar, array,
# and edge values like empty string/array, false, NaN) is rejected with
# OBJECT_TO_ARRAY_NOT_OBJECT_ERROR — no type is silently coerced.
NOT_OBJECT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="double_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": 3.14},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject double input",
    ),
    ExpressionTestCase(
        id="bool_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": True},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject bool input",
    ),
    ExpressionTestCase(
        id="array_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": [1, 2, 3]},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject array input",
    ),
    ExpressionTestCase(
        id="decimal128_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": Decimal128("1")},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject decimal128 input",
    ),
    ExpressionTestCase(
        id="int64_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": Int64(1)},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject int64 input",
    ),
    ExpressionTestCase(
        id="objectid_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": ObjectId()},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject objectid input",
    ),
    ExpressionTestCase(
        id="datetime_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject datetime input",
    ),
    ExpressionTestCase(
        id="binary_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": Binary(b"x", 0)},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject binary input",
    ),
    ExpressionTestCase(
        id="regex_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": Regex("x")},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject regex input",
    ),
    ExpressionTestCase(
        id="maxkey_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": MaxKey()},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject maxkey input",
    ),
    ExpressionTestCase(
        id="minkey_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": MinKey()},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject minkey input",
    ),
    ExpressionTestCase(
        id="nan_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": FLOAT_NAN},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject NaN input",
    ),
    ExpressionTestCase(
        id="bool_false_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": False},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject bool false input",
    ),
    ExpressionTestCase(
        id="empty_array_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": []},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject empty array input",
    ),
    ExpressionTestCase(
        id="empty_string_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": ""},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject empty string input",
    ),
    ExpressionTestCase(
        id="decimal128_nan_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": DECIMAL128_NAN},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject Decimal128 NaN input",
    ),
    ExpressionTestCase(
        id="decimal128_infinity_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": DECIMAL128_INFINITY},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject Decimal128 Infinity input",
    ),
    ExpressionTestCase(
        id="decimal128_neg_infinity_input",
        expression={"$objectToArray": "$obj"},
        doc={"obj": DECIMAL128_NEGATIVE_INFINITY},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Should reject Decimal128 -Infinity input",
    ),
]

# Property [Composite-path error]: a composite array path (field-path
# resolution through an array of objects) is rejected as non-object, just
# like a plain non-object value.
COMPOSITE_PATH_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="composite_array_path",
        expression={"$objectToArray": "$a.b"},
        doc={"a": [{"b": {"x": 1}}, {"b": {"y": 2}}]},
        error_code=OBJECT_TO_ARRAY_NOT_OBJECT_ERROR,
        msg="Composite array path should resolve to non-object",
    ),
]

ALL_ERROR_TESTS = NOT_OBJECT_ERROR_TESTS + TEST_SUBSET_FOR_LITERAL + COMPOSITE_PATH_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_objectToArray_not_object_insert(collection, test):
    """Test $objectToArray error cases with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
