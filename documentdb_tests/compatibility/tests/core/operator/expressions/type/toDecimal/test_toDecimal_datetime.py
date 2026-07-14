"""$toDecimal datetime conversion tests and unsupported BSON type errors."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DATE_YEAR_1,
    DATE_YEAR_9999,
    DECIMAL128_ZERO,
)

# Property [Datetime]: $toDecimal converts datetime to milliseconds since Unix epoch as Decimal128.
TODECIMAL_DATETIME_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "datetime_epoch",
        msg="Epoch datetime converts to Decimal128('0')",
        expression={"$toDecimal": DATE_EPOCH},
        expected=DECIMAL128_ZERO,
    ),
    ExpressionTestCase(
        "datetime_1ms_after_epoch",
        msg="1 ms after epoch converts to Decimal128('1')",
        expression={"$toDecimal": datetime(1970, 1, 1, 0, 0, 0, 1_000, tzinfo=timezone.utc)},
        expected=Decimal128("1"),
    ),
    ExpressionTestCase(
        "datetime_one_day",
        msg="One day after epoch converts to Decimal128('86400000')",
        expression={"$toDecimal": datetime(1970, 1, 2, 0, 0, 0, tzinfo=timezone.utc)},
        expected=Decimal128("86400000"),
    ),
    ExpressionTestCase(
        "datetime_before_epoch",
        msg="1 ms before epoch converts to Decimal128('-1')",
        expression={"$toDecimal": DATE_BEFORE_EPOCH},
        expected=Decimal128("-1"),
    ),
    ExpressionTestCase(
        "datetime_pre_epoch",
        msg="Pre-epoch date (1960-01-01) converts to negative ms value",
        expression={"$toDecimal": datetime(1960, 1, 1, tzinfo=timezone.utc)},
        expected=Decimal128("-315619200000"),
    ),
    ExpressionTestCase(
        "datetime_with_millis",
        msg="Datetime with sub-second precision preserves milliseconds",
        expression={"$toDecimal": datetime(2018, 3, 27, 5, 4, 47, 890_000, tzinfo=timezone.utc)},
        expected=Decimal128("1522127087890"),
    ),
    ExpressionTestCase(
        "datetime_2024",
        msg="A modern date converts to its ms-since-epoch value",
        expression={"$toDecimal": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expected=Decimal128("1704067200000"),
    ),
    ExpressionTestCase(
        "datetime_millisecond_precision",
        msg="Datetime preserves millisecond precision",
        expression={"$toDecimal": datetime(1970, 1, 1, 0, 0, 0, 500_000, tzinfo=timezone.utc)},
        expected=Decimal128("500"),
    ),
    ExpressionTestCase(
        "datetime_far_past",
        msg="Far-past datetime (year 1) converts to its ms-since-epoch value",
        expression={"$toDecimal": DATE_YEAR_1},
        expected=Decimal128("-62135596800000"),
    ),
    ExpressionTestCase(
        "datetime_far_future",
        msg="Far-future datetime (year 9999) converts to its ms-since-epoch value",
        expression={"$toDecimal": DATE_YEAR_9999},
        expected=Decimal128("253402300799999"),
    ),
]

# Property [Unsupported Types]: $toDecimal fails with a conversion error for BSON types it
# cannot convert (object, binary, ObjectId, regex, timestamp, code, MinKey, MaxKey, array).
TODECIMAL_UNSUPPORTED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "type_object",
        msg="Object BSON type is a conversion failure",
        expression={"$toDecimal": {"$literal": {"a": 1}}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_binary",
        msg="Binary BSON type is a conversion failure",
        expression={"$toDecimal": Binary(b"data")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_binary_uuid",
        msg="Binary UUID subtype 4 is a conversion failure",
        expression={"$toDecimal": Binary(b"\x00" * 16, 4)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_objectid",
        msg="ObjectId BSON type is a conversion failure",
        expression={"$toDecimal": ObjectId("507f1f77bcf86cd799439011")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_regex",
        msg="Regex BSON type is a conversion failure",
        expression={"$toDecimal": Regex("abc")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_timestamp",
        msg="Timestamp BSON type is a conversion failure",
        expression={"$toDecimal": Timestamp(1, 1)},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_code",
        msg="Code BSON type is a conversion failure",
        expression={"$toDecimal": Code("function() {}")},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_minkey",
        msg="MinKey BSON type is a conversion failure",
        expression={"$toDecimal": MinKey()},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_maxkey",
        msg="MaxKey BSON type is a conversion failure",
        expression={"$toDecimal": MaxKey()},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_array",
        msg="Array value (from $literal) is a conversion failure",
        expression={"$toDecimal": {"$literal": [1, 2]}},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
    ExpressionTestCase(
        "type_nested_array",
        msg="Nested literal array after single-element unwrap is a conversion failure",
        expression={"$toDecimal": [["hello"]]},
        error_code=CONVERSION_FAILURE_ERROR,
    ),
]

TODECIMAL_DATETIME_TESTS = TODECIMAL_DATETIME_TESTS + TODECIMAL_UNSUPPORTED_TYPE_TESTS


@pytest.mark.parametrize("test", pytest_params(TODECIMAL_DATETIME_TESTS))
def test_toDecimal_datetime(collection, test: ExpressionTestCase):
    """$toDecimal converts datetime to ms-since-epoch Decimal128; rejects unsupported types."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
