"""Tests for dataSize command argument validation."""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticPropertyTest,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import MISSING_FIELD_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

DATASIZE_NAMESPACE_PARAMS = [
    BsonTypeTestCase(
        id="dataSize_namespace",
        msg="dataSize namespace should reject non-string types",
        keyword="dataSize",
        valid_types=[BsonType.STRING],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
    ),
]

REJECTION_CASES = generate_bson_rejection_test_cases(DATASIZE_NAMESPACE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_dataSize_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test dataSize rejects non-string BSON types for namespace."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dataSize": sample_value})
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


VALID_TESTS: list[DiagnosticPropertyTest] = [
    DiagnosticPropertyTest(
        "valid_namespace",
        checks={"ok": Eq(1.0)},
        msg="Valid namespace should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_TESTS))
def test_dataSize_argument_property(collection, test):
    """Test dataSize with valid arguments returns expected properties."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertProperties(result, test.checks, msg=test.msg, raw_res=True)
