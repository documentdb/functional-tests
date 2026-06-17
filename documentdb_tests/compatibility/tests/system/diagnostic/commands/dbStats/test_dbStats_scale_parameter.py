"""Tests for the dbStats ``scale`` parameter.

Covers valid scale values and their reported scaleFactor (including type
coverage and non-integer truncation), invalid scale values, invalid scale
types, duplicate scale keys, and the scaling applied to size fields.
"""

import pytest
from bson import SON, Decimal128, Int64

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
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
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin


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

REJECTION_CASES = generate_bson_rejection_test_cases(SCALE_TYPE_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(SCALE_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_dbStats_scale_accepts_valid_type(collection, bson_type, sample_value, spec):
    """Test dbStats accepts valid BSON types for the scale parameter."""
    result = execute_command(collection, {"dbStats": 1, "scale": sample_value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
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
# (TypeMismatch) are covered by REJECTION_CASES above.
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
        "approaching_1_from_below",
        command={"dbStats": 1, "scale": 0.9999999},
        error_code=BAD_VALUE_ERROR,
        msg="Scale truncating to 0 should error with BadValue",
    ),
    DiagnosticTestCase(
        "negative_double",
        command={"dbStats": 1, "scale": -1.5},
        error_code=BAD_VALUE_ERROR,
        msg="Negative double scale should error with BadValue",
    ),
    DiagnosticTestCase(
        "negative_int64",
        command={"dbStats": 1, "scale": Int64(-5)},
        error_code=BAD_VALUE_ERROR,
        msg="Negative int64 scale should error with BadValue",
    ),
    DiagnosticTestCase(
        "negative_decimal",
        command={"dbStats": 1, "scale": Decimal128("-5")},
        error_code=BAD_VALUE_ERROR,
        msg="Negative decimal scale should error with BadValue",
    ),
    DiagnosticTestCase(
        "decimal_lt_1",
        command={"dbStats": 1, "scale": Decimal128("0.5")},
        error_code=BAD_VALUE_ERROR,
        msg="Decimal scale < 1 should error with BadValue",
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
    """Test dbStats rejects invalid scale values and types with the expected error."""
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
