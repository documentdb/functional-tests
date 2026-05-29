"""Tests for valid TTL index creation via createIndexes.

Validates allowed key patterns, special index types, and valid
expireAfterSeconds boundary values.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_ZERO,
)

pytestmark = pytest.mark.index

TTL_CREATE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="descending_field",
        indexes=({"key": {"dateField": -1}, "name": "ttl_desc", "expireAfterSeconds": 3600},),
        msg="Should allow TTL on single descending field",
    ),
    IndexTestCase(
        id="hashed_field",
        indexes=({"key": {"dateField": "hashed"}, "name": "ttl_hash", "expireAfterSeconds": 3600},),
        msg="Should allow TTL on hashed index",
    ),
    IndexTestCase(
        id="text_field",
        indexes=({"key": {"dateField": "text"}, "name": "ttl_text", "expireAfterSeconds": 3600},),
        msg="Should allow TTL on text index",
    ),
    IndexTestCase(
        id="2dsphere_field",
        indexes=(
            {"key": {"dateField": "2dsphere"}, "name": "ttl_2ds", "expireAfterSeconds": 3600},
        ),
        msg="Should allow TTL on 2dsphere index",
    ),
    IndexTestCase(
        id="2d_field",
        indexes=({"key": {"dateField": "2d"}, "name": "ttl_2d", "expireAfterSeconds": 3600},),
        msg="Should allow TTL on 2d index",
    ),
    IndexTestCase(
        id="value_zero",
        indexes=({"key": {"d": 1}, "name": "ttl_0", "expireAfterSeconds": INT32_ZERO},),
        msg="Should accept expireAfterSeconds 0",
    ),
    IndexTestCase(
        id="value_just_below_max",
        indexes=(
            {"key": {"d": 1}, "name": "ttl_below_max", "expireAfterSeconds": INT32_MAX_MINUS_1},
        ),
        msg="Should accept expireAfterSeconds just below INT32_MAX",
    ),
    IndexTestCase(
        id="value_int32_max",
        indexes=({"key": {"d": 1}, "name": "ttl_max", "expireAfterSeconds": INT32_MAX},),
        msg="Should accept expireAfterSeconds at INT32_MAX",
    ),
    IndexTestCase(
        id="value_int32_max_as_int64",
        indexes=({"key": {"d": 1}, "name": "ttl_i64", "expireAfterSeconds": Int64(INT32_MAX)},),
        msg="Should accept INT32_MAX as Int64",
    ),
    IndexTestCase(
        id="value_int32_max_as_double",
        indexes=({"key": {"d": 1}, "name": "ttl_dbl", "expireAfterSeconds": float(INT32_MAX)},),
        msg="Should accept INT32_MAX as double",
    ),
    IndexTestCase(
        id="value_int32_max_as_decimal128",
        indexes=(
            {
                "key": {"d": 1},
                "name": "ttl_dec",
                "expireAfterSeconds": Decimal128(str(INT32_MAX)),
            },
        ),
        msg="Should accept INT32_MAX as Decimal128",
    ),
    IndexTestCase(
        id="value_negative_zero_double",
        indexes=(
            {"key": {"d": 1}, "name": "ttl_nz_d", "expireAfterSeconds": DOUBLE_NEGATIVE_ZERO},
        ),
        msg="Should accept negative zero double (stored as 0)",
    ),
    IndexTestCase(
        id="value_negative_zero_decimal128",
        indexes=(
            {
                "key": {"d": 1},
                "name": "ttl_nz_dec",
                "expireAfterSeconds": DECIMAL128_NEGATIVE_ZERO,
            },
        ),
        msg="Should accept negative zero Decimal128 (stored as 0)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TTL_CREATE_TESTS))
def test_ttl_create_success(collection, test):
    """Test that createIndexes succeeds for valid TTL index specs."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(
        result, {"ok": 1.0, "numIndexesBefore": 1, "numIndexesAfter": 2}, msg=test.msg
    )
