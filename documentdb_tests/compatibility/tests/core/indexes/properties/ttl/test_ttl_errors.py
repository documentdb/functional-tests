"""Tests for invalid TTL index creation via createIndexes.

Validates that createIndexes rejects disallowed key patterns, invalid
expireAfterSeconds values, and conflicting index options.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CANNOT_CREATE_INDEX_ERROR,
    INDEX_OPTIONS_CONFLICT_ERROR,
    INVALID_INDEX_SPEC_OPTION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

CREATE_INDEX_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="key_compound",
        indexes=(
            {
                "key": {"dateField": 1, "other": 1},
                "name": "ttl_compound",
                "expireAfterSeconds": 3600,
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject TTL on compound index",
    ),
    IndexTestCase(
        id="key_id_field",
        indexes=({"key": {"_id": 1}, "name": "ttl_id", "expireAfterSeconds": 3600},),
        error_code=INVALID_INDEX_SPEC_OPTION_ERROR,
        msg="Should reject TTL on _id field",
    ),
    IndexTestCase(
        id="key_wildcard",
        indexes=({"key": {"$**": 1}, "name": "ttl_wild", "expireAfterSeconds": 3600},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject TTL on wildcard index",
    ),
    IndexTestCase(
        id="value_negative_int",
        indexes=({"key": {"d": 1}, "name": "ttl_neg", "expireAfterSeconds": -1},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject negative int expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_negative_int64",
        indexes=({"key": {"d": 1}, "name": "ttl_neg_l", "expireAfterSeconds": Int64(-1)},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject negative Int64 expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_negative_double",
        indexes=({"key": {"d": 1}, "name": "ttl_neg_d", "expireAfterSeconds": -1.0},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject negative double expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_negative_decimal128",
        indexes=({"key": {"d": 1}, "name": "ttl_neg_dec", "expireAfterSeconds": Decimal128("-1")},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject negative Decimal128 expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_int32_min",
        indexes=({"key": {"d": 1}, "name": "ttl_i32min", "expireAfterSeconds": -2147483648},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject INT32_MIN expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_nan_double",
        indexes=({"key": {"d": 1}, "name": "ttl_nan", "expireAfterSeconds": float("nan")},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject NaN expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_nan_decimal128",
        indexes=(
            {"key": {"d": 1}, "name": "ttl_nan_dec", "expireAfterSeconds": Decimal128("NaN")},
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject Decimal128 NaN expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_infinity",
        indexes=({"key": {"d": 1}, "name": "ttl_inf", "expireAfterSeconds": float("inf")},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject Infinity expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_negative_infinity",
        indexes=({"key": {"d": 1}, "name": "ttl_ninf", "expireAfterSeconds": float("-inf")},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject -Infinity expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_decimal128_infinity",
        indexes=(
            {"key": {"d": 1}, "name": "ttl_dec_inf", "expireAfterSeconds": Decimal128("Infinity")},
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject Decimal128 Infinity expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_decimal128_negative_infinity",
        indexes=(
            {
                "key": {"d": 1},
                "name": "ttl_dec_ninf",
                "expireAfterSeconds": Decimal128("-Infinity"),
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject Decimal128 -Infinity expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_above_int32_max",
        indexes=({"key": {"d": 1}, "name": "ttl_over", "expireAfterSeconds": 2147483648},),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject value above INT32_MAX",
    ),
    IndexTestCase(
        id="value_int64_above_int32_max",
        indexes=(
            {"key": {"d": 1}, "name": "ttl_i64_over", "expireAfterSeconds": Int64(2147483648)},
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject Int64 above INT32_MAX",
    ),
    IndexTestCase(
        id="value_int64_max",
        indexes=(
            {
                "key": {"d": 1},
                "name": "ttl_i64max",
                "expireAfterSeconds": Int64(9223372036854775807),
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject INT64_MAX expireAfterSeconds",
    ),
    IndexTestCase(
        id="value_very_large_decimal128",
        indexes=(
            {
                "key": {"d": 1},
                "name": "ttl_huge",
                "expireAfterSeconds": Decimal128("10002147483648"),
            },
        ),
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="Should reject very large Decimal128 expireAfterSeconds",
    ),
    IndexTestCase(
        id="conflict_non_ttl_exists",
        setup_indexes=[{"key": {"dateField": 1}, "name": "dateField_1"}],
        indexes=({"key": {"dateField": 1}, "name": "dateField_1_ttl", "expireAfterSeconds": 3600},),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="TTL on key with existing non-TTL index should fail",
    ),
    IndexTestCase(
        id="conflict_different_expire",
        setup_indexes=[{"key": {"dateField": 1}, "name": "ttl_3600", "expireAfterSeconds": 3600}],
        indexes=({"key": {"dateField": 1}, "name": "ttl_7200", "expireAfterSeconds": 7200},),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Different expireAfterSeconds on same key should fail",
    ),
    IndexTestCase(
        id="conflict_decimal128_on_non_ttl",
        setup_indexes=[{"key": {"dateField": 1}, "name": "dateField_1"}],
        indexes=(
            {"key": {"dateField": 1}, "name": "ttl_dec", "expireAfterSeconds": Decimal128("3600")},
        ),
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="TTL Decimal128 on key with existing non-TTL should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CREATE_INDEX_ERROR_TESTS))
def test_ttl_create_index_error(collection, test):
    """Test that createIndexes rejects invalid TTL index specs."""
    if test.setup_indexes:
        execute_command(
            collection, {"createIndexes": collection.name, "indexes": test.setup_indexes}
        )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)
