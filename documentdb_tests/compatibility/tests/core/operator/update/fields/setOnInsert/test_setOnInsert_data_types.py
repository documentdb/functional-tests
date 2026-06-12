"""
Tests for $setOnInsert update operator - data types.

Verifies $setOnInsert preserves exact BSON types, Decimal128 precision, and
distinguishes booleans from integers.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    FLOAT_NAN,
)

SETONINSERT_TYPE_DISTINCTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="preserves_positive_infinity",
        query={"_id": 1},
        update={"$setOnInsert": {"field": float("inf")}},
        upsert=True,
        expected=[{"_id": 1, "field": float("inf")}],
        msg="Should preserve positive infinity",
    ),
    UpdateTestCase(
        id="preserves_negative_infinity",
        query={"_id": 1},
        update={"$setOnInsert": {"field": float("-inf")}},
        upsert=True,
        expected=[{"_id": 1, "field": float("-inf")}],
        msg="Should preserve negative infinity",
    ),
    UpdateTestCase(
        id="preserves_decimal128_precision",
        query={"_id": 1},
        update={"$setOnInsert": {"field": Decimal128("1.234567890123456789012345678901234")}},
        upsert=True,
        expected=[{"_id": 1, "field": Decimal128("1.234567890123456789012345678901234")}],
        msg="Should preserve Decimal128 high precision",
    ),
    UpdateTestCase(
        id="preserves_decimal128_neg_zero",
        query={"_id": 1},
        update={"$setOnInsert": {"field": DECIMAL128_NEGATIVE_ZERO}},
        upsert=True,
        expected=[{"_id": 1, "field": DECIMAL128_NEGATIVE_ZERO}],
        msg="Should preserve Decimal128 -0",
    ),
    UpdateTestCase(
        id="null_vs_missing",
        query={"_id": 1},
        update={"$setOnInsert": {"field": None}},
        upsert=True,
        expected=[{"_id": 1, "field": None}],
        msg="Should store null value (field present, not missing)",
    ),
    UpdateTestCase(
        id="empty_string_vs_null",
        query={"_id": 1},
        update={"$setOnInsert": {"field": ""}},
        upsert=True,
        expected=[{"_id": 1, "field": ""}],
        msg="Empty string should be stored as string type, not null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_TYPE_DISTINCTION_TESTS))
def test_setOnInsert_type_distinction(collection, test):
    """Test $setOnInsert preserves exact BSON types."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)


SETONINSERT_NAN_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="preserves_double_nan",
        query={"_id": 1},
        update={"$setOnInsert": {"field": FLOAT_NAN}},
        upsert=True,
        expected=[{"_id": 1, "field": FLOAT_NAN}],
        msg="Should preserve double NaN",
    ),
    UpdateTestCase(
        id="preserves_decimal128_nan",
        query={"_id": 1},
        update={"$setOnInsert": {"field": DECIMAL128_NAN}},
        upsert=True,
        expected=[{"_id": 1, "field": DECIMAL128_NAN}],
        msg="Should preserve Decimal128 NaN",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_NAN_TESTS))
def test_setOnInsert_nan_types(collection, test):
    """Test $setOnInsert preserves NaN values."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccessNaN(result, test.expected, msg=test.msg)


SETONINSERT_BOOL_VS_INT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="false_stored_as_bool",
        query={"_id": 1},
        update={"$setOnInsert": {"field": False}},
        upsert=True,
        expected=[{"_id": 1, "field": False}],
        msg="false should be stored as bool, not int(0)",
    ),
    UpdateTestCase(
        id="true_stored_as_bool",
        query={"_id": 1},
        update={"$setOnInsert": {"field": True}},
        upsert=True,
        expected=[{"_id": 1, "field": True}],
        msg="true should be stored as bool, not int(1)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_BOOL_VS_INT_TESTS))
def test_setOnInsert_bool_vs_int(collection, test):
    """Test $setOnInsert stores booleans distinct from integers."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"_id": 1}},
    )
    assertSuccess(result, test.expected, msg=test.msg)
