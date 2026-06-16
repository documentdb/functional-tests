"""Tests for the create command clustered index acceptance behavior."""

from uuid import uuid4

import pytest
from bson import Binary, Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_ZERO,
    STRING_SIZE_LIMIT_BYTES,
)

# Property [Clustered Index Key Value Types]: key:{_id:N} accepts int32,
# Int64, double, and Decimal128 values that compare equal to 1.
CREATE_CLUSTERED_KEY_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="basic_clustered",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
        },
        expected={"ok": 1.0},
        msg="Basic clustered index creation should succeed",
    ),
    CommandTestCase(
        id="key_value_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": Int64(1)}, "unique": True},
        },
        expected={"ok": 1.0},
        msg="key value as Int64(1) should succeed",
    ),
    CommandTestCase(
        id="key_value_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1.0}, "unique": True},
        },
        expected={"ok": 1.0},
        msg="key value as double 1.0 should succeed",
    ),
    CommandTestCase(
        id="key_value_decimal128_1",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": Decimal128("1")}, "unique": True},
        },
        expected={"ok": 1.0},
        msg="key value as Decimal128('1') should succeed",
    ),
    CommandTestCase(
        id="key_value_decimal128_1_0",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": DECIMAL128_TRAILING_ZERO}, "unique": True},
        },
        expected={"ok": 1.0},
        msg="key value as Decimal128('1.0') should succeed",
    ),
    CommandTestCase(
        id="key_value_decimal128_1_00",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": Decimal128("1.00")}, "unique": True},
        },
        expected={"ok": 1.0},
        msg="key value as Decimal128('1.00') should succeed",
    ),
]

# Property [Clustered Index Unique Truthiness]: unique accepts bool and numeric
# truthy values including NaN and Infinity.
CREATE_CLUSTERED_UNIQUE_TRUTHY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="unique_int_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": 42},
        },
        expected={"ok": 1.0},
        msg="unique as truthy int should succeed",
    ),
    CommandTestCase(
        id="unique_int64_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": Int64(1)},
        },
        expected={"ok": 1.0},
        msg="unique as truthy Int64 should succeed",
    ),
    CommandTestCase(
        id="unique_double_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": 3.14},
        },
        expected={"ok": 1.0},
        msg="unique as truthy double should succeed",
    ),
    CommandTestCase(
        id="unique_decimal128_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": Decimal128("1")},
        },
        expected={"ok": 1.0},
        msg="unique as truthy Decimal128 should succeed",
    ),
    CommandTestCase(
        id="unique_nan_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": FLOAT_NAN},
        },
        expected={"ok": 1.0},
        msg="unique as NaN (truthy) should succeed",
    ),
    CommandTestCase(
        id="unique_negative_nan_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": FLOAT_NEGATIVE_NAN},
        },
        expected={"ok": 1.0},
        msg="unique as -NaN (truthy) should succeed",
    ),
    CommandTestCase(
        id="unique_decimal128_nan_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": DECIMAL128_NAN},
        },
        expected={"ok": 1.0},
        msg="unique as Decimal128 NaN (truthy) should succeed",
    ),
    CommandTestCase(
        id="unique_decimal128_negative_nan_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": DECIMAL128_NEGATIVE_NAN},
        },
        expected={"ok": 1.0},
        msg="unique as Decimal128 -NaN (truthy) should succeed",
    ),
    CommandTestCase(
        id="unique_infinity_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": FLOAT_INFINITY},
        },
        expected={"ok": 1.0},
        msg="unique as Infinity (truthy) should succeed",
    ),
    CommandTestCase(
        id="unique_negative_infinity_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": FLOAT_NEGATIVE_INFINITY},
        },
        expected={"ok": 1.0},
        msg="unique as -Infinity (truthy) should succeed",
    ),
    CommandTestCase(
        id="unique_decimal128_infinity_truthy",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": DECIMAL128_INFINITY},
        },
        expected={"ok": 1.0},
        msg="unique as Decimal128 Infinity (truthy) should succeed",
    ),
]

# Property [Clustered Index Name Acceptance]: the name sub-field accepts any
# string including empty, null bytes, dots, dollar prefix, unicode, and long.
CREATE_CLUSTERED_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="name_custom_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "name": "my_index",
            },
        },
        expected={"ok": 1.0},
        msg="Custom name string should succeed",
    ),
    CommandTestCase(
        id="name_empty_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "name": "",
            },
        },
        expected={"ok": 1.0},
        msg="Empty name string should succeed",
    ),
    CommandTestCase(
        id="name_null_bytes",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "name": "a\x00b",
            },
        },
        expected={"ok": 1.0},
        msg="Name with null bytes should succeed",
    ),
    CommandTestCase(
        id="name_dots",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "name": "a.b.c",
            },
        },
        expected={"ok": 1.0},
        msg="Name with dots should succeed",
    ),
    CommandTestCase(
        id="name_dollar_prefix",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "name": "$idx",
            },
        },
        expected={"ok": 1.0},
        msg="Name with dollar prefix should succeed",
    ),
    CommandTestCase(
        id="name_unicode",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "name": "\u6d4b\u8bd5\u7d22\u5f15",
            },
        },
        expected={"ok": 1.0},
        msg="Unicode name should succeed",
    ),
    CommandTestCase(
        id="name_at_max_bson_size",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "name": "x" * STRING_SIZE_LIMIT_BYTES,
            },
        },
        expected={"ok": 1.0},
        msg="Name of MAX_BSON_SIZE chars should succeed (no server-side name length limit)",
    ),
]

# Property [Clustered Index Version Coercion]: v accepts values that coerce
# to 2 via double truncation or Decimal128 banker's rounding.
CREATE_CLUSTERED_VERSION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="v_equals_2",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True, "v": 2},
        },
        expected={"ok": 1.0},
        msg="v=2 should succeed",
    ),
    CommandTestCase(
        id="v_double_truncates_to_2",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True, "v": 2.999},
        },
        expected={"ok": 1.0},
        msg="v=2.999 truncates toward zero to 2, which is valid",
    ),
    CommandTestCase(
        id="v_decimal128_1_5_rounds_to_2",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "v": DECIMAL128_ONE_AND_HALF,
            },
        },
        expected={"ok": 1.0},
        msg="Decimal128('1.5') banker's rounds to 2, which is valid",
    ),
    CommandTestCase(
        id="v_decimal128_2_5_rounds_to_2",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {
                "key": {"_id": 1},
                "unique": True,
                "v": DECIMAL128_TWO_AND_HALF,
            },
        },
        expected={"ok": 1.0},
        msg="Decimal128('2.5') banker's rounds to 2, which is valid",
    ),
]

# Property [Clustered Index Falsy Bypass]: falsy values (false, 0, -0.0,
# Int64(0), Decimal128('0'), Decimal128('-0')) bypass clustered creation.
CREATE_CLUSTERED_FALSY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="clustered_index_false_creates_regular",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": False,
        },
        expected={"ok": 1.0},
        msg="clusteredIndex:false creates a regular collection",
    ),
    CommandTestCase(
        id="clustered_index_zero_creates_regular",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": 0,
        },
        expected={"ok": 1.0},
        msg="clusteredIndex:0 creates a regular collection",
    ),
    CommandTestCase(
        id="clustered_index_zero_double_creates_regular",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": DOUBLE_ZERO,
        },
        expected={"ok": 1.0},
        msg="clusteredIndex:0.0 creates a regular collection",
    ),
    CommandTestCase(
        id="clustered_index_neg_zero_creates_regular",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": DOUBLE_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="clusteredIndex:-0.0 creates a regular collection",
    ),
    CommandTestCase(
        id="clustered_index_int64_zero_creates_regular",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": INT64_ZERO,
        },
        expected={"ok": 1.0},
        msg="clusteredIndex:Int64(0) creates a regular collection",
    ),
    CommandTestCase(
        id="clustered_index_decimal128_zero_creates_regular",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": DECIMAL128_ZERO,
        },
        expected={"ok": 1.0},
        msg="clusteredIndex:Decimal128('0') creates a regular collection",
    ),
    CommandTestCase(
        id="clustered_index_decimal128_neg_zero_creates_regular",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": DECIMAL128_NEGATIVE_ZERO,
        },
        expected={"ok": 1.0},
        msg="clusteredIndex:Decimal128('-0') creates a regular collection",
    ),
]

# Property [Clustered Index Compatibility]: clusteredIndex is compatible with
# validator, collation, storageEngine, indexOptionDefaults, expireAfterSeconds,
# and encryptedFields.
CREATE_CLUSTERED_COMPATIBILITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="compatible_with_validator",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "validator": {"x": {"$exists": True}},
        },
        expected={"ok": 1.0},
        msg="Clustered with validator should succeed",
    ),
    CommandTestCase(
        id="compatible_with_collation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="Clustered with collation should succeed",
    ),
    CommandTestCase(
        id="compatible_with_storage_engine",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "storageEngine": {"wiredTiger": {"configString": ""}},
        },
        expected={"ok": 1.0},
        msg="Clustered with storageEngine should succeed",
    ),
    CommandTestCase(
        id="compatible_with_index_option_defaults",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "indexOptionDefaults": {"storageEngine": {"wiredTiger": {"configString": ""}}},
        },
        expected={"ok": 1.0},
        msg="Clustered with indexOptionDefaults should succeed",
    ),
    CommandTestCase(
        id="compatible_with_expire_after_seconds",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "expireAfterSeconds": 7200,
        },
        expected={"ok": 1.0},
        msg="Clustered with expireAfterSeconds should succeed",
    ),
    CommandTestCase(
        id="compatible_with_encrypted_fields",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
            "encryptedFields": {
                "fields": [{"path": "ssn", "bsonType": "string", "keyId": Binary(uuid4().bytes, 4)}]
            },
        },
        expected={"ok": Eq(1.0)},
        msg="Clustered with encryptedFields should succeed",
        marks=(pytest.mark.replica_set,),
    ),
]

CREATE_CLUSTERED_SUCCESS_TESTS: list[CommandTestCase] = (
    CREATE_CLUSTERED_KEY_VALUE_TESTS
    + CREATE_CLUSTERED_UNIQUE_TRUTHY_TESTS
    + CREATE_CLUSTERED_NAME_TESTS
    + CREATE_CLUSTERED_VERSION_TESTS
    + CREATE_CLUSTERED_FALSY_TESTS
    + CREATE_CLUSTERED_COMPATIBILITY_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_CLUSTERED_SUCCESS_TESTS))
def test_create_clustered_index_acceptance(database_client, collection, test):
    """Test create command clustered index acceptance behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
