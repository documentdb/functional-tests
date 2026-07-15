"""$toBool boolean passthrough, string truthiness, always-truthy type, and string error tests."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import STRING_SIZE_LIMIT_ERROR
from documentdb_tests.framework.lazy_payload import lazy
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

# Property [Boolean Passthrough]: boolean inputs are returned unchanged.
TOBOOL_PASSTHROUGH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "passthrough_true",
        msg="true input passes through unchanged",
        expression={"$toBool": True},
        expected=True,
    ),
    ExpressionTestCase(
        "passthrough_false",
        msg="false input passes through unchanged",
        expression={"$toBool": False},
        expected=False,
    ),
]

# Property [String Truthiness]: all strings produce true regardless of content, including the
# empty string, the string "false", and the string "0".
TOBOOL_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_nonempty",
        msg="Non-empty string converts to true",
        expression={"$toBool": "hello"},
        expected=True,
    ),
    ExpressionTestCase(
        "string_empty",
        msg="Empty string converts to true",
        expression={"$toBool": ""},
        expected=True,
    ),
    ExpressionTestCase(
        "string_false",
        msg="The string 'false' converts to true",
        expression={"$toBool": "false"},
        expected=True,
    ),
    ExpressionTestCase(
        "string_zero",
        msg="The string '0' converts to true",
        expression={"$toBool": "0"},
        expected=True,
    ),
]

# Property [String Size Limit]: strings at or above the 16 MB byte limit are rejected.
TOBOOL_STRING_SIZE_LIMIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "size_at_limit_single_byte",
        msg="Single-byte string at the 16 MB byte limit is rejected",
        expression=lazy(lambda: {"$toBool": "a" * STRING_SIZE_LIMIT_BYTES}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
    ExpressionTestCase(
        "size_at_limit_four_byte",
        msg="Four-byte character string reaching 16 MB bytes is rejected",
        expression=lazy(lambda: {"$toBool": "\U0001f600" * (STRING_SIZE_LIMIT_BYTES // 4)}),
        error_code=STRING_SIZE_LIMIT_ERROR,
    ),
]

# Property [Always-Truthy Types]: non-numeric, non-string, non-boolean, non-null types always
# produce true regardless of their value, including empty arrays and empty objects.
TOBOOL_TRUTHY_TYPES_TESTS: list[ExpressionTestCase] = [
    # array (must use $literal to avoid arity interpretation)
    ExpressionTestCase(
        "truthy_array_empty",
        msg="Empty array is truthy",
        expression={"$toBool": {"$literal": []}},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_array_nonempty",
        msg="Non-empty array is truthy",
        expression={"$toBool": {"$literal": [1, 2]}},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_array_containing_null",
        msg="Array containing null is truthy",
        expression={"$toBool": {"$literal": [None]}},
        expected=True,
    ),
    # Binary
    ExpressionTestCase(
        "truthy_binary_empty",
        msg="Empty Binary is truthy",
        expression={"$toBool": Binary(b"")},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_binary_nonempty",
        msg="Non-empty Binary is truthy",
        expression={"$toBool": Binary(b"\x01\x02")},
        expected=True,
    ),
    # ObjectId
    ExpressionTestCase(
        "truthy_objectid",
        msg="ObjectId is truthy",
        expression={"$toBool": ObjectId("000000000000000000000000")},
        expected=True,
    ),
    # datetime
    ExpressionTestCase(
        "truthy_datetime_epoch",
        msg="Epoch datetime is truthy",
        expression={"$toBool": datetime(1970, 1, 1, tzinfo=timezone.utc)},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_datetime_pre_epoch",
        msg="Pre-epoch datetime is truthy",
        expression={"$toBool": datetime(1969, 12, 31, tzinfo=timezone.utc)},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_timestamp_zero",
        msg="Timestamp (0, 0) is truthy",
        expression={"$toBool": Timestamp(0, 0)},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_timestamp_nonzero",
        msg="Timestamp (1, 1) is truthy",
        expression={"$toBool": Timestamp(1, 1)},
        expected=True,
    ),
    # object (must use $literal to avoid expression interpretation)
    ExpressionTestCase(
        "truthy_object_empty",
        msg="Empty object is truthy",
        expression={"$toBool": {"$literal": {}}},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_object_nonempty",
        msg="Non-empty object is truthy",
        expression={"$toBool": {"$literal": {"a": 1}}},
        expected=True,
    ),
    # Regex
    ExpressionTestCase(
        "truthy_regex",
        msg="Regex is truthy",
        expression={"$toBool": Regex("abc")},
        expected=True,
    ),
    # Code
    ExpressionTestCase(
        "truthy_code",
        msg="Code is truthy",
        expression={"$toBool": Code("x")},
        expected=True,
    ),
    # MinKey / MaxKey
    ExpressionTestCase(
        "truthy_minkey",
        msg="MinKey is truthy",
        expression={"$toBool": MinKey()},
        expected=True,
    ),
    ExpressionTestCase(
        "truthy_maxkey",
        msg="MaxKey is truthy",
        expression={"$toBool": MaxKey()},
        expected=True,
    ),
]

TOBOOL_STRING_AND_TYPES_TESTS = (
    TOBOOL_PASSTHROUGH_TESTS
    + TOBOOL_STRING_TESTS
    + TOBOOL_STRING_SIZE_LIMIT_TESTS
    + TOBOOL_TRUTHY_TYPES_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TOBOOL_STRING_AND_TYPES_TESTS))
def test_toBool_string_and_types(collection, test: ExpressionTestCase):
    """$toBool boolean passthrough, string truthiness, always-truthy types, and string errors."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
