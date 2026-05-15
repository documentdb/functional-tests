"""Tests for TTL index runtime behavior.

Validates multiple TTL indexes on the same collection and
expireAfterSeconds storage consistency across numeric types.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


def test_multiple_ttl_indexes_different_fields(collection):
    """Test creating two TTL indexes on different fields succeeds."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"dateField1": 1}, "name": "ttl_1", "expireAfterSeconds": 3600}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"dateField2": 1}, "name": "ttl_2", "expireAfterSeconds": 7200}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0, "numIndexesBefore": 2, "numIndexesAfter": 3})


def test_multiple_ttl_indexes_listed(collection):
    """Test listIndexes shows both TTL indexes with correct expireAfterSeconds."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"dateField1": 1}, "name": "ttl_1", "expireAfterSeconds": 3600},
                {"key": {"dateField2": 1}, "name": "ttl_2", "expireAfterSeconds": 7200},
            ],
        },
    )
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        [
            {"name": "ttl_1", "expireAfterSeconds": 3600},
            {"name": "ttl_2", "expireAfterSeconds": 7200},
        ],
        transform=lambda docs: [
            {"name": d["name"], "expireAfterSeconds": d["expireAfterSeconds"]}
            for d in docs
            if "expireAfterSeconds" in d
        ],
    )


STORAGE_CASES: list[IndexTestCase] = [
    IndexTestCase(
        id="stored_as_int32",
        indexes=({"key": {"dateField": 1}, "name": "ttl_i32", "expireAfterSeconds": 3600},),
        expected=[{"name": "ttl_i32", "expireAfterSeconds": 3600}],
        msg="int32 expireAfterSeconds should store correctly",
    ),
    IndexTestCase(
        id="stored_as_int64",
        indexes=({"key": {"dateField": 1}, "name": "ttl_i64", "expireAfterSeconds": Int64(3600)},),
        expected=[{"name": "ttl_i64", "expireAfterSeconds": 3600}],
        msg="Int64 expireAfterSeconds should store same value",
    ),
    IndexTestCase(
        id="stored_as_double",
        indexes=({"key": {"dateField": 1}, "name": "ttl_dbl", "expireAfterSeconds": 3600.0},),
        expected=[{"name": "ttl_dbl", "expireAfterSeconds": 3600}],
        msg="double expireAfterSeconds should store same value",
    ),
    IndexTestCase(
        id="stored_as_decimal128",
        indexes=(
            {"key": {"dateField": 1}, "name": "ttl_dec", "expireAfterSeconds": Decimal128("3600")},
        ),
        expected=[{"name": "ttl_dec", "expireAfterSeconds": 3600}],
        msg="Decimal128 expireAfterSeconds should store same value",
    ),
    IndexTestCase(
        id="stored_fractional_double_truncated",
        indexes=({"key": {"dateField": 1}, "name": "ttl_frac_d", "expireAfterSeconds": 3600.5},),
        expected=[{"name": "ttl_frac_d", "expireAfterSeconds": 3600}],
        msg="Fractional double expireAfterSeconds should be truncated to integer",
    ),
    IndexTestCase(
        id="stored_fractional_decimal128_truncated",
        indexes=(
            {
                "key": {"dateField": 1},
                "name": "ttl_frac_dec",
                "expireAfterSeconds": Decimal128("3600.5"),
            },
        ),
        expected=[{"name": "ttl_frac_dec", "expireAfterSeconds": 3600}],
        msg="Fractional Decimal128 expireAfterSeconds should be truncated to integer",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STORAGE_CASES))
def test_expire_after_seconds_storage(collection, test):
    """Test expireAfterSeconds stored consistently across numeric types."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        test.expected,
        msg=test.msg,
        transform=lambda docs: [
            {"name": d["name"], "expireAfterSeconds": d["expireAfterSeconds"]}
            for d in docs
            if "expireAfterSeconds" in d
        ],
    )
