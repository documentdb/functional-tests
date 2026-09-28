"""Tests for dbStats command argument handling.

The value of the ``dbStats`` field is ignored by the server: any value
selects the current database, so every BSON type should be accepted,
including numeric edge cases such as 0, -1, and Infinity.

Also covers the ``scale`` parameter (type-level acceptance and rejection,
value truncation, and duplicate-key behavior) and the ``freeStorage``
parameter (type-level acceptance and rejection, free-storage field
presence, and omission when unset or 0). Value-level errors (BadValue)
are in test_dbStats_errors.py.
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
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, NotExists
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, BsonType

pytestmark = pytest.mark.admin


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


SCALE_TYPE_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="scale",
        msg="scale should reject non-numeric types with TypeMismatch",
        keyword="scale",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.DECIMAL: Decimal128("1024"), BsonType.LONG: Int64(1024)},
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


FREE_STORAGE_TYPE_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="freeStorage",
        msg="freeStorage should reject non-numeric, non-bool types with TypeMismatch",
        keyword="freeStorage",
        valid_types=[
            BsonType.BOOL,
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

FREE_STORAGE_REJECTION_CASES = generate_bson_rejection_test_cases(FREE_STORAGE_TYPE_PARAMS)
FREE_STORAGE_ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(FREE_STORAGE_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", FREE_STORAGE_ACCEPTANCE_CASES)
def test_dbStats_free_storage_accepts_valid_type(collection, bson_type, sample_value, spec):
    """Test dbStats accepts valid BSON types for the freeStorage parameter."""
    result = execute_command(collection, {"dbStats": 1, "freeStorage": sample_value})
    assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", FREE_STORAGE_REJECTION_CASES)
def test_dbStats_free_storage_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test dbStats rejects non-numeric, non-bool BSON types for freeStorage with TypeMismatch."""
    result = execute_command(collection, {"dbStats": 1, "freeStorage": sample_value})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


FREE_STORAGE_FIELD_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "free_storage_one_includes_fields",
        setup=[
            {"insert": "c1", "documents": [{"_id": 1}]},
            {"createIndexes": "c1", "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
        ],
        command={"dbStats": 1, "freeStorage": 1},
        checks={
            "freeStorageSize": Exists(),
            "indexFreeStorageSize": Exists(),
            "totalFreeStorageSize": Exists(),
        },
        msg="freeStorage:1 should include free-storage fields",
    ),
    DiagnosticTestCase(
        "no_free_storage_param",
        setup=[{"insert": "c1", "documents": [{"_id": 1}]}],
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
        setup=[{"insert": "c1", "documents": [{"_id": 1}]}],
        command={"dbStats": 1, "freeStorage": 0},
        checks={
            "freeStorageSize": NotExists(),
            "indexFreeStorageSize": NotExists(),
            "totalFreeStorageSize": NotExists(),
        },
        msg="freeStorage:0 should omit free-storage fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FREE_STORAGE_FIELD_TESTS))
def test_dbStats_free_storage_fields(collection, test):
    """Test dbStats free-storage field presence based on the freeStorage option."""
    for setup_command in test.setup:
        setup_result = execute_command(collection, setup_command)
        if isinstance(setup_result, Exception):
            raise setup_result
    result = execute_command(collection, test.command)
    assertProperties(result, test.checks, raw_res=True, msg=test.msg)
