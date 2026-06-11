"""
Insert BSON type preservation tests.

Tests that insert correctly stores and preserves all BSON types,
numeric boundaries, Decimal128 precision, and binary subtypes.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, Regex, Timestamp

from documentdb_tests.framework.assertions import (
    assertProperties,
    assertSuccess,
    assertSuccessNaN,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import IsType
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    DATE_LEAP_FEB29,
    DATE_Y2K,
    DATE_YEAR_1,
    DATE_YEAR_1900,
    DATE_YEAR_9999,
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
    OID_EPOCH,
    OID_MAX_SIGNED32,
    OID_MAX_UNSIGNED32,
    OID_MIN_SIGNED32,
    TS_EPOCH,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)


@dataclass(frozen=True)
class BsonTypeTest(BaseTestCase):
    value: Any = None


# Property [BSON Type Roundtrip]: insert preserves every non-deprecated BSON type on retrieval.
BSON_TYPE_TESTS: list[BsonTypeTest] = [
    BsonTypeTest("double", value=3.14, expected=3.14, msg="insert should preserve double."),
    BsonTypeTest("string", value="hello", expected="hello", msg="insert should preserve string."),
    BsonTypeTest(
        "object", value={"k": "v"}, expected={"k": "v"}, msg="insert should preserve object."
    ),
    BsonTypeTest("array", value=[1, 2, 3], expected=[1, 2, 3], msg="insert should preserve array."),
    BsonTypeTest(
        "binData",
        value=Binary(b"\x01\x02\x03"),
        expected=b"\x01\x02\x03",
        msg="insert should preserve binary.",
    ),
    BsonTypeTest(
        "objectId", value=OID_EPOCH, expected=OID_EPOCH, msg="insert should preserve ObjectId."
    ),
    BsonTypeTest("bool_true", value=True, expected=True, msg="insert should preserve true."),
    BsonTypeTest("bool_false", value=False, expected=False, msg="insert should preserve false."),
    BsonTypeTest("date", value=DATE_EPOCH, expected=DATE_EPOCH, msg="insert should preserve date."),
    BsonTypeTest("null", value=None, expected=None, msg="insert should preserve null."),
    BsonTypeTest(
        "regex",
        value=Regex("^abc", "i"),
        expected=Regex("^abc", "i"),
        msg="insert should preserve regex.",
    ),
    BsonTypeTest(
        "javascript",
        value=Code("function(){}"),
        expected=Code("function(){}"),
        msg="insert should preserve javascript.",
    ),
    BsonTypeTest("int32", value=42, expected=42, msg="insert should preserve int32."),
    BsonTypeTest("int64", value=INT64_MAX, expected=INT64_MAX, msg="insert should preserve int64."),
    BsonTypeTest(
        "decimal128",
        value=Decimal128("123.456"),
        expected=Decimal128("123.456"),
        msg="insert should preserve decimal128.",
    ),
    BsonTypeTest(
        "timestamp", value=TS_EPOCH, expected=TS_EPOCH, msg="insert should preserve timestamp."
    ),
    BsonTypeTest("minKey", value=MinKey(), expected=MinKey(), msg="insert should preserve MinKey."),
    BsonTypeTest("maxKey", value=MaxKey(), expected=MaxKey(), msg="insert should preserve MaxKey."),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(BSON_TYPE_TESTS))
def test_insert_bson_type(collection, test):
    """Test that insert preserves each BSON type."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": test.value}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "value": test.expected}], msg=test.msg)


# Property [Int64 Boundaries]: insert preserves Int64 boundary values without type promotion.
INT64_BOUNDARY_TESTS: list[BsonTypeTest] = [
    BsonTypeTest(
        "int64_min", value=INT64_MIN, expected=INT64_MIN, msg="insert should preserve INT64_MIN."
    ),
    BsonTypeTest(
        "int64_max", value=INT64_MAX, expected=INT64_MAX, msg="insert should preserve INT64_MAX."
    ),
    BsonTypeTest(
        "int64_zero",
        value=INT64_ZERO,
        expected=INT64_ZERO,
        msg="insert should preserve INT64_ZERO.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(INT64_BOUNDARY_TESTS))
def test_insert_int64_boundary(collection, test):
    """Test that insert preserves Int64 boundary values."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": test.value}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "value": test.expected}], msg=test.msg)


# Property [Double Special Values]: insert preserves Infinity, -Infinity, -0.0, subnormals.
DOUBLE_SPECIAL_TESTS: list[BsonTypeTest] = [
    BsonTypeTest(
        "infinity",
        value=FLOAT_INFINITY,
        expected=FLOAT_INFINITY,
        msg="insert should preserve Infinity.",
    ),
    BsonTypeTest(
        "neg_infinity",
        value=FLOAT_NEGATIVE_INFINITY,
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="insert should preserve -Infinity.",
    ),
    BsonTypeTest(
        "neg_zero",
        value=DOUBLE_NEGATIVE_ZERO,
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="insert should preserve -0.0.",
    ),
    BsonTypeTest(
        "min_subnormal",
        value=DOUBLE_MIN_SUBNORMAL,
        expected=DOUBLE_MIN_SUBNORMAL,
        msg="insert should preserve min subnormal.",
    ),
    BsonTypeTest(
        "near_max",
        value=DOUBLE_NEAR_MAX,
        expected=DOUBLE_NEAR_MAX,
        msg="insert should preserve near max double.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(DOUBLE_SPECIAL_TESTS))
def test_insert_double_special(collection, test):
    """Test that insert preserves special double values."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": test.value}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "value": test.expected}], msg=test.msg)


@pytest.mark.insert
def test_insert_double_nan(collection):
    """Test that insert preserves NaN."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": FLOAT_NAN}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccessNaN(result, [{"_id": 1, "value": float("nan")}], msg="insert should preserve NaN.")


# Property [Date Boundaries]: insert preserves date values across the full range.
DATE_BOUNDARY_TESTS: list[BsonTypeTest] = [
    BsonTypeTest(
        "epoch", value=DATE_EPOCH, expected=DATE_EPOCH, msg="insert should preserve epoch date."
    ),
    BsonTypeTest(
        "before_epoch",
        value=DATE_BEFORE_EPOCH,
        expected=DATE_BEFORE_EPOCH,
        msg="insert should preserve pre-epoch date.",
    ),
    BsonTypeTest("y2k", value=DATE_Y2K, expected=DATE_Y2K, msg="insert should preserve Y2K date."),
    BsonTypeTest(
        "year_1", value=DATE_YEAR_1, expected=DATE_YEAR_1, msg="insert should preserve year 1 date."
    ),
    BsonTypeTest(
        "year_9999",
        value=DATE_YEAR_9999,
        expected=DATE_YEAR_9999,
        msg="insert should preserve year 9999 date.",
    ),
    BsonTypeTest(
        "year_1900",
        value=DATE_YEAR_1900,
        expected=DATE_YEAR_1900,
        msg="insert should preserve year 1900 date.",
    ),
    BsonTypeTest(
        "leap_feb29",
        value=DATE_LEAP_FEB29,
        expected=DATE_LEAP_FEB29,
        msg="insert should preserve leap day date.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(DATE_BOUNDARY_TESTS))
def test_insert_date_boundary(collection, test):
    """Test that insert preserves date boundary values."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": test.value}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "value": test.expected}], msg=test.msg)


# Property [Timestamp Boundaries]: insert preserves Timestamp boundary values.
TIMESTAMP_BOUNDARY_TESTS: list[BsonTypeTest] = [
    BsonTypeTest(
        "ts_epoch", value=TS_EPOCH, expected=TS_EPOCH, msg="insert should preserve epoch timestamp."
    ),
    BsonTypeTest(
        "ts_max_signed32",
        value=TS_MAX_SIGNED32,
        expected=TS_MAX_SIGNED32,
        msg="insert should preserve max signed32 timestamp.",
    ),
    BsonTypeTest(
        "ts_max_unsigned32",
        value=TS_MAX_UNSIGNED32,
        expected=TS_MAX_UNSIGNED32,
        msg="insert should preserve max unsigned32 timestamp.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(TIMESTAMP_BOUNDARY_TESTS))
def test_insert_timestamp_boundary(collection, test):
    """Test that insert preserves timestamp boundary values."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": test.value}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "value": test.expected}], msg=test.msg)


# Property [ObjectId Boundaries]: insert preserves ObjectId boundary values used as _id.
OID_BOUNDARY_TESTS: list[BsonTypeTest] = [
    BsonTypeTest(
        "oid_epoch", value=OID_EPOCH, expected=OID_EPOCH, msg="insert should preserve epoch OID."
    ),
    BsonTypeTest(
        "oid_max_signed32",
        value=OID_MAX_SIGNED32,
        expected=OID_MAX_SIGNED32,
        msg="insert should preserve max signed32 OID.",
    ),
    BsonTypeTest(
        "oid_min_signed32",
        value=OID_MIN_SIGNED32,
        expected=OID_MIN_SIGNED32,
        msg="insert should preserve min signed32 OID.",
    ),
    BsonTypeTest(
        "oid_max_unsigned32",
        value=OID_MAX_UNSIGNED32,
        expected=OID_MAX_UNSIGNED32,
        msg="insert should preserve max unsigned32 OID.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(OID_BOUNDARY_TESTS))
def test_insert_objectid_boundary(collection, test):
    """Test that insert preserves ObjectId boundary values as _id."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": test.value, "x": 1}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.value}})
    assertSuccess(result, [{"_id": test.expected, "x": 1}], msg=test.msg)


# Property [Decimal128 Precision]: insert preserves Decimal128 precision,
# exponent, and special values.
DECIMAL128_PRECISION_TESTS: list[BsonTypeTest] = [
    BsonTypeTest(
        "max",
        value=DECIMAL128_MAX,
        expected=DECIMAL128_MAX,
        msg="insert should preserve Decimal128 max.",
    ),
    BsonTypeTest(
        "min",
        value=DECIMAL128_MIN,
        expected=DECIMAL128_MIN,
        msg="insert should preserve Decimal128 min.",
    ),
    BsonTypeTest(
        "zero",
        value=DECIMAL128_ZERO,
        expected=DECIMAL128_ZERO,
        msg="insert should preserve Decimal128 zero.",
    ),
    BsonTypeTest(
        "neg_zero",
        value=DECIMAL128_NEGATIVE_ZERO,
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="insert should preserve Decimal128 -0.",
    ),
    BsonTypeTest(
        "infinity",
        value=DECIMAL128_INFINITY,
        expected=DECIMAL128_INFINITY,
        msg="insert should preserve Decimal128 Infinity.",
    ),
    BsonTypeTest(
        "neg_infinity",
        value=DECIMAL128_NEGATIVE_INFINITY,
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="insert should preserve Decimal128 -Infinity.",
    ),
    BsonTypeTest(
        "large_exp",
        value=DECIMAL128_LARGE_EXPONENT,
        expected=DECIMAL128_LARGE_EXPONENT,
        msg="insert should preserve large exponent.",
    ),
    BsonTypeTest(
        "small_exp",
        value=DECIMAL128_SMALL_EXPONENT,
        expected=DECIMAL128_SMALL_EXPONENT,
        msg="insert should preserve small exponent.",
    ),
    BsonTypeTest(
        "trailing_zero",
        value=DECIMAL128_TRAILING_ZERO,
        expected=DECIMAL128_TRAILING_ZERO,
        msg="insert should preserve trailing zero.",
    ),
    BsonTypeTest(
        "many_trailing_zeros",
        value=DECIMAL128_MANY_TRAILING_ZEROS,
        expected=DECIMAL128_MANY_TRAILING_ZEROS,
        msg="insert should preserve many trailing zeros.",
    ),
    BsonTypeTest(
        "neg_zero_exp",
        value=Decimal128("-0E+3"),
        expected=Decimal128("-0E+3"),
        msg="insert should preserve -0E+3 exponent.",
    ),
    BsonTypeTest(
        "smallest_positive",
        value=Decimal128("1E-6176"),
        expected=Decimal128("1E-6176"),
        msg="insert should preserve smallest positive.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(DECIMAL128_PRECISION_TESTS))
def test_insert_decimal128_precision(collection, test):
    """Test that insert preserves Decimal128 precision and representation."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": test.value}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "value": test.expected}], msg=test.msg)


@pytest.mark.insert
def test_insert_decimal128_nan(collection):
    """Test that insert preserves Decimal128 NaN."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": Decimal128("NaN")}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccessNaN(
        result,
        [{"_id": 1, "value": Decimal128("NaN")}],
        msg="insert should preserve Decimal128 NaN.",
    )


# Property [Binary Subtypes]: insert preserves binary data with all subtype values.
BINARY_SUBTYPE_TESTS: list[BsonTypeTest] = [
    BsonTypeTest(
        "subtype_0_generic",
        value=Binary(b"\x01\x02", 0),
        expected=b"\x01\x02",
        msg="insert should preserve generic binary.",
    ),
    BsonTypeTest(
        "subtype_1_function",
        value=Binary(b"\x01\x02", 1),
        expected=Binary(b"\x01\x02", 1),
        msg="insert should preserve function binary.",
    ),
    BsonTypeTest(
        "subtype_2_old_binary",
        value=Binary(b"\x01\x02", 2),
        expected=Binary(b"\x01\x02", 2),
        msg="insert should preserve old binary.",
    ),
    BsonTypeTest(
        "subtype_3_old_uuid",
        value=Binary(b"\x01" * 16, 3),
        expected=Binary(b"\x01" * 16, 3),
        msg="insert should preserve old UUID binary.",
    ),
    BsonTypeTest(
        "subtype_4_uuid",
        value=Binary(b"\x01" * 16, 4),
        expected=Binary(b"\x01" * 16, 4),
        msg="insert should preserve UUID binary.",
    ),
    BsonTypeTest(
        "subtype_5_md5",
        value=Binary(b"\x01" * 16, 5),
        expected=Binary(b"\x01" * 16, 5),
        msg="insert should preserve MD5 binary.",
    ),
    BsonTypeTest(
        "subtype_6_encrypted",
        value=Binary(b"\x01\x02", 6),
        expected=Binary(b"\x01\x02", 6),
        msg="insert should preserve encrypted binary.",
    ),
    BsonTypeTest(
        "subtype_128_user",
        value=Binary(b"\x01\x02", 128),
        expected=Binary(b"\x01\x02", 128),
        msg="insert should preserve user-defined subtype.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(BINARY_SUBTYPE_TESTS))
def test_insert_binary_subtype(collection, test):
    """Test that insert preserves binary data with various subtypes."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": test.value}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "value": test.expected}], msg=test.msg)


# Property [BSON Type Distinction]: insert preserves the exact BSON type,
# not a numerically equivalent type.
BSON_DISTINCTION_TESTS: list[BsonTypeTest] = [
    BsonTypeTest(
        "int32_not_long", value=1, expected=1, msg="insert should retrieve int32 as int32."
    ),
    BsonTypeTest(
        "int64_not_double",
        value=Int64(1),
        expected=Int64(1),
        msg="insert should retrieve int64 as int64.",
    ),
    BsonTypeTest(
        "double_not_int", value=1.0, expected=1.0, msg="insert should retrieve double as double."
    ),
    BsonTypeTest(
        "decimal128_not_double",
        value=Decimal128("1"),
        expected=Decimal128("1"),
        msg="insert should retrieve decimal128 as decimal128.",
    ),
    BsonTypeTest(
        "false_not_zero",
        value=False,
        expected=False,
        msg="insert should store false distinctly from 0.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(BSON_DISTINCTION_TESTS))
def test_insert_bson_type_distinction(collection, test):
    """Test that insert preserves exact BSON type identity."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": test.value}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "value": test.expected}], msg=test.msg)


@pytest.mark.insert
def test_insert_null_field_exists(collection):
    """Test that null field value is stored as explicit null."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "value": None}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result, [{"_id": 1, "value": None}], msg="insert should store null field explicitly."
    )


@pytest.mark.insert
def test_insert_missing_field_not_null(collection):
    """Test that missing field is not stored as null."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1}], msg="insert should not materialize missing fields as null.")


@pytest.mark.insert
def test_insert_timestamp_zero_gets_autofilled(collection):
    """Test that Timestamp(0,0) is auto-filled with current time on insert."""
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "ts": Timestamp(0, 0)}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result, {"ts": IsType("timestamp")}, msg="insert should auto-fill Timestamp(0,0)."
    )
