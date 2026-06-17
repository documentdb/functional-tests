"""Tests for dbStats command argument handling.

The value of the ``dbStats`` field is ignored by the server: any value
selects the current database, so every BSON type should be accepted,
including numeric edge cases such as 0, -1, and Infinity.

Also covers the ``scale`` parameter (valid/invalid values and types,
truncation, duplicate keys, and the scaling applied to size fields) and the
``freeStorage`` parameter (acceptance, free-storage field presence and the
totalFreeStorageSize relationship, and omission when unset or 0).
"""

import pytest
from bson import SON, Decimal128, Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, NotExists
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, BsonType

pytestmark = pytest.mark.admin


# dbStats ignores the command field value — all BSON types should succeed.
DBSTATS_VALUE_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="dbStats_value",
        msg="dbStats should accept all BSON types for the command field value",
        keyword="dbStats",
        valid_types=list(BsonType),
    ),
]

VALUE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(DBSTATS_VALUE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", VALUE_ACCEPTANCE_CASES)
def test_dbStats_accepts_any_value_type(collection, bson_type, sample_value, spec):
    """Test dbStats accepts all BSON types for the command field value."""
    result = execute_command(collection, {"dbStats": sample_value})
    assertSuccessPartial(
        result,
        {"ok": 1.0, "db": collection.database.name},
        msg=f"dbStats should accept {bson_type.value} for the command field value",
    )


# Specific numeric edge-case values for the command field.
EDGE_CASE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        id="value_zero",
        command={"dbStats": 0},
        checks={"ok": Eq(1.0)},
        msg="dbStats:0 should succeed",
    ),
    DiagnosticTestCase(
        id="value_negative_one",
        command={"dbStats": -1},
        checks={"ok": Eq(1.0)},
        msg="dbStats:-1 should succeed",
    ),
    DiagnosticTestCase(
        id="value_infinity",
        command={"dbStats": FLOAT_INFINITY},
        checks={"ok": Eq(1.0)},
        msg="dbStats:Infinity should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_dbStats_accepts_value_edge_cases(collection, test):
    """Test dbStats succeeds for specific numeric edge-case command values."""
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)


# Type-level acceptance and rejection for the scale parameter.
# Valid numeric types: double, int, long, decimal, null.
# The default decimal sample (0.5) is overridden to 1024 since 0.5 would fail
# with BadValue rather than TypeMismatch.
SCALE_TYPE_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="scale",
        msg="scale should reject non-numeric types with TypeMismatch",
        keyword="scale",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.DECIMAL: Decimal128("1024")},
    ),
]

SCALE_REJECTION_CASES = generate_bson_rejection_test_cases(SCALE_TYPE_PARAMS)
SCALE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SCALE_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", SCALE_ACCEPTANCE_CASES)
def test_dbStats_scale_accepts_valid_type(collection, bson_type, sample_value, spec):
    """Test dbStats accepts valid BSON types for the scale parameter."""
    result = execute_command(collection, {"dbStats": 1, "scale": sample_value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", SCALE_REJECTION_CASES)
def test_dbStats_scale_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test dbStats rejects non-numeric BSON types for the scale parameter with TypeMismatch."""
    result = execute_command(collection, {"dbStats": 1, "scale": sample_value})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


# Truncation and default behaviour edge cases not covered by type-level tests.
SCALE_EDGE_CASES: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "double_truncates",
        command={"dbStats": 1, "scale": 2.5},
        checks={"ok": Eq(1.0), "scaleFactor": Eq(Int64(2))},
        msg="Double scale should truncate toward zero",
    ),
    DiagnosticTestCase(
        "double_1023_999_truncates",
        command={"dbStats": 1, "scale": 1023.999},
        checks={"ok": Eq(1.0), "scaleFactor": Eq(Int64(1023))},
        msg="Double scale 1023.999 should truncate to 1023",
    ),
    DiagnosticTestCase(
        "default_no_scale",
        command={"dbStats": 1},
        checks={"ok": Eq(1.0), "scaleFactor": Eq(Int64(1))},
        msg="Omitting scale should default scaleFactor to 1",
    ),
    DiagnosticTestCase(
        "duplicate_keys_last_valid",
        command=SON([("dbStats", 1), ("scale", 1), ("scale", 1024)]),
        checks={"ok": Eq(1.0), "scaleFactor": Eq(Int64(1024))},
        msg="Last duplicate scale value should win",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SCALE_EDGE_CASES))
def test_dbStats_scale_edge_cases(collection, test):
    """Test dbStats scale truncation and default behaviour."""
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, raw_res=True, msg=test.msg)


# Invalid scale values (BadValue). Non-positive or truncate-to-zero values of
# otherwise-valid numeric types are rejected with code 2. Type-level rejections
# (TypeMismatch) are covered by SCALE_REJECTION_CASES above.
INVALID_SCALE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "zero",
        command={"dbStats": 1, "scale": 0},
        error_code=BAD_VALUE_ERROR,
        msg="scale=0 should error with BadValue",
    ),
    DiagnosticTestCase(
        "negative_int",
        command={"dbStats": 1, "scale": -1},
        error_code=BAD_VALUE_ERROR,
        msg="Negative int scale should error with BadValue",
    ),
    DiagnosticTestCase(
        "fractional_lt_1",
        command={"dbStats": 1, "scale": 0.5},
        error_code=BAD_VALUE_ERROR,
        msg="Fractional scale < 1 should error with BadValue",
    ),
    DiagnosticTestCase(
        "duplicate_keys_last_invalid",
        command=SON([("dbStats", 1), ("scale", 1024), ("scale", -1)]),
        error_code=BAD_VALUE_ERROR,
        msg="Invalid last duplicate scale value should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_SCALE_TESTS))
def test_dbStats_invalid_scale_errors(collection, test):
    """Test dbStats rejects invalid (non-positive/truncate-to-zero) scale values with BadValue."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_dbStats_scale_divides_storage_size(collection):
    """Test the scale factor divides storageSize in the response."""
    collection.insert_many([{"_id": i, "a": i} for i in range(20)])
    scale = 1024
    unscaled = execute_command(collection, {"dbStats": 1})
    scaled = execute_command(collection, {"dbStats": 1, "scale": scale})
    assertSuccessPartial(
        scaled,
        expected={"storageSize": unscaled.get("storageSize") / scale},
        msg="storageSize should be divided by the scale factor",
    )


def test_dbStats_scale_divides_index_size(collection):
    """Test the scale factor divides indexSize in the response."""
    collection.insert_many([{"_id": i, "a": i} for i in range(20)])
    collection.create_index("a")
    scale = 1024
    unscaled = execute_command(collection, {"dbStats": 1})
    scaled = execute_command(collection, {"dbStats": 1, "scale": scale})
    assertSuccessPartial(
        scaled,
        expected={"indexSize": unscaled.get("indexSize") / scale},
        msg="indexSize should be divided by the scale factor",
    )


def test_dbStats_scale_does_not_affect_avg_obj_size(collection):
    """Test avgObjSize is not affected by the scale factor."""
    collection.insert_many([{"_id": i, "a": i} for i in range(20)])
    unscaled = execute_command(collection, {"dbStats": 1})
    scaled = execute_command(collection, {"dbStats": 1, "scale": 1024})
    assertSuccessPartial(
        scaled,
        expected={"avgObjSize": unscaled.get("avgObjSize")},
        msg="avgObjSize should be unaffected by scale",
    )


def test_dbStats_free_storage_one_includes_expected_fields(collection):
    """Test dbStats with freeStorage:1 includes the three free-storage fields."""
    collection.insert_one({"_id": 1})
    collection.create_index("a")
    result = execute_command(collection, {"dbStats": 1, "freeStorage": 1})
    assertProperties(
        result,
        {
            "freeStorageSize": Exists(),
            "indexFreeStorageSize": Exists(),
            "totalFreeStorageSize": Exists(),
        },
        raw_res=True,
        msg="freeStorage:1 should include free-storage fields",
    )


def test_dbStats_total_free_storage_size_relationship(collection):
    """Test totalFreeStorageSize equals freeStorageSize plus indexFreeStorageSize."""
    collection.insert_many([{"_id": i, "a": i} for i in range(20)])
    collection.create_index("a")
    result = execute_command(collection, {"dbStats": 1, "freeStorage": 1})
    assertSuccess(
        result.get("totalFreeStorageSize"),
        result.get("freeStorageSize") + result.get("indexFreeStorageSize"),
        raw_res=True,
        msg="totalFreeStorageSize should equal freeStorageSize + indexFreeStorageSize",
    )


OMITS_FREE_STORAGE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "no_free_storage_param",
        command={"dbStats": 1},
        checks={
            "freeStorageSize": NotExists(),
            "indexFreeStorageSize": NotExists(),
            "totalFreeStorageSize": NotExists(),
        },
        msg="Omitting freeStorage should omit free-storage fields",
    ),
    DiagnosticTestCase(
        "free_storage_zero",
        command={"dbStats": 1, "freeStorage": 0},
        checks={
            "freeStorageSize": NotExists(),
            "indexFreeStorageSize": NotExists(),
            "totalFreeStorageSize": NotExists(),
        },
        msg="freeStorage:0 should omit free-storage fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OMITS_FREE_STORAGE_TESTS))
def test_dbStats_omits_free_storage_fields(collection, test):
    """Test dbStats omits free-storage fields when freeStorage is not set or 0."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, raw_res=True, msg=test.msg)
