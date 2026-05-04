from __future__ import annotations

import struct
from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    ConvertTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_NEGATIVE_ZERO, DOUBLE_NEGATIVE_ZERO

# Property [Subtype Valid Range]: to.subtype accepts valid subtype values and
# numeric types for the subtype field.
CONVERT_SUBTYPE_VALID_TESTS: list[ConvertTest] = [
    ConvertTest(
        "subtype_zero",
        input=42,
        to={"type": "binData", "subtype": 0},
        expected=struct.pack("<i", 42),
        msg="$convert should accept subtype 0",
    ),
    ConvertTest(
        "subtype_five",
        input=42,
        to={"type": "binData", "subtype": 5},
        expected=Binary(struct.pack("<i", 42), 5),
        msg="$convert should accept subtype 5",
    ),
    ConvertTest(
        "subtype_nine",
        input=42,
        to={"type": "binData", "subtype": 9},
        expected=Binary(struct.pack("<i", 42), 9),
        msg="$convert should accept subtype 9",
    ),
    ConvertTest(
        "subtype_128",
        input=42,
        to={"type": "binData", "subtype": 128},
        expected=Binary(struct.pack("<i", 42), 128),
        msg="$convert should accept subtype 128 (user-defined)",
    ),
    ConvertTest(
        "subtype_255",
        input=42,
        to={"type": "binData", "subtype": 255},
        expected=Binary(struct.pack("<i", 42), 255),
        msg="$convert should accept subtype 255 (user-defined)",
    ),
    ConvertTest(
        "subtype_int64",
        input=42,
        to={"type": "binData", "subtype": Int64(5)},
        expected=Binary(struct.pack("<i", 42), 5),
        msg="$convert should accept Int64 value for subtype",
    ),
    ConvertTest(
        "subtype_double",
        input=42,
        to={"type": "binData", "subtype": 5.0},
        expected=Binary(struct.pack("<i", 42), 5),
        msg="$convert should accept whole-number double for subtype",
    ),
    ConvertTest(
        "subtype_decimal128",
        input=42,
        to={"type": "binData", "subtype": Decimal128("5")},
        expected=Binary(struct.pack("<i", 42), 5),
        msg="$convert should accept Decimal128 value for subtype",
    ),
    ConvertTest(
        "subtype_neg_zero_double",
        input=42,
        to={"type": "binData", "subtype": DOUBLE_NEGATIVE_ZERO},
        expected=struct.pack("<i", 42),
        msg="$convert should accept double -0.0 as subtype 0",
    ),
    ConvertTest(
        "subtype_neg_zero_decimal",
        input=42,
        to={"type": "binData", "subtype": DECIMAL128_NEGATIVE_ZERO},
        expected=struct.pack("<i", 42),
        msg="$convert should accept Decimal128('-0') as subtype 0",
    ),
]

# Property [Subtype Default]: to.subtype defaults to 0 when omitted or when the
# field reference is missing.
CONVERT_SUBTYPE_DEFAULT_TESTS: list[ConvertTest] = [
    ConvertTest(
        "subtype_default_object_form_no_subtype",
        input=42,
        to={"type": "binData"},
        expected=struct.pack("<i", 42),
        msg="$convert should default to subtype 0 when to is object form without subtype",
    ),
]

# Property [Subtype Ignored for Non-BinData]: to.subtype is silently ignored
# when to.type is not binData.
CONVERT_SUBTYPE_IGNORED_TESTS: list[ConvertTest] = [
    ConvertTest(
        "subtype_ignored_for_int",
        input="42",
        to={"type": "int", "subtype": 5},
        expected=42,
        msg="$convert should ignore subtype when target type is int",
    ),
    ConvertTest(
        "subtype_ignored_for_long",
        input=42,
        to={"type": "long", "subtype": 5},
        expected=Int64(42),
        msg="$convert should ignore subtype when target type is long",
    ),
    ConvertTest(
        "subtype_ignored_for_double",
        input=42,
        to={"type": "double", "subtype": 5},
        expected=42.0,
        msg="$convert should ignore subtype when target type is double",
    ),
    ConvertTest(
        "subtype_ignored_for_decimal",
        input=42,
        to={"type": "decimal", "subtype": 5},
        expected=Decimal128("42"),
        msg="$convert should ignore subtype when target type is decimal",
    ),
    ConvertTest(
        "subtype_ignored_for_string",
        input=42,
        to={"type": "string", "subtype": 5},
        expected="42",
        msg="$convert should ignore subtype when target type is string",
    ),
    ConvertTest(
        "subtype_ignored_for_bool",
        input=42,
        to={"type": "bool", "subtype": 5},
        expected=True,
        msg="$convert should ignore subtype when target type is bool",
    ),
    ConvertTest(
        "subtype_ignored_for_date",
        input="2024-06-15T12:30:45Z",
        to={"type": "date", "subtype": 5},
        expected=datetime(2024, 6, 15, 12, 30, 45, tzinfo=timezone.utc),
        msg="$convert should ignore subtype when target type is date",
    ),
    ConvertTest(
        "subtype_ignored_for_objectId",
        input="507f1f77bcf86cd799439011",
        to={"type": "objectId", "subtype": 5},
        expected=ObjectId("507f1f77bcf86cd799439011"),
        msg="$convert should ignore subtype when target type is objectId",
    ),
]

CONVERT_SUBTYPE_SUCCESS_TESTS = (
    CONVERT_SUBTYPE_VALID_TESTS + CONVERT_SUBTYPE_DEFAULT_TESTS + CONVERT_SUBTYPE_IGNORED_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_SUBTYPE_SUCCESS_TESTS))
def test_convert_subtype(collection, test_case: ConvertTest):
    """Test $convert subtype behavior."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
