"""Tests for dataSize command argument validation.

Covers BSON type rejection and acceptance for namespace, keyPattern,
and estimate. Min/max type validation lives in test_dataSize_min_max.py
alongside their behavioral tests.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccessPartial,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import MISSING_FIELD_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

BSON_TYPE_PARAMS = [
    BsonTypeTestCase(
        id="dataSize_namespace",
        msg="dataSize namespace should reject non-string types",
        keyword="dataSize",
        valid_types=[BsonType.STRING],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
    ),
    BsonTypeTestCase(
        id="keyPattern_type",
        msg="keyPattern should reject non-document types",
        keyword="keyPattern",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="estimate_type",
        msg="estimate should reject non-numeric/non-boolean/non-null types",
        keyword="estimate",
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

REJECTION_CASES = generate_bson_rejection_test_cases(BSON_TYPE_PARAMS)
ACCEPTANCE_CASES = generate_bson_acceptance_test_cases(BSON_TYPE_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_CASES)
def test_dataSize_rejects_invalid_type(collection, bson_type, sample_value, spec):
    """Test dataSize rejects invalid BSON types for each parameter."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    if spec.keyword == "dataSize":
        cmd = {"dataSize": sample_value}
    else:
        cmd = {"dataSize": ns, spec.keyword: sample_value}
    result = execute_command(collection, cmd)
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_CASES)
def test_dataSize_accepts_valid_type(collection, bson_type, sample_value, spec):
    """Test dataSize accepts valid BSON types for each parameter.

    Namespace acceptance uses the real namespace since the generic sample
    string is not a valid db.collection namespace.
    """
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    if spec.keyword == "dataSize":
        cmd = {"dataSize": ns}
    else:
        cmd = {"dataSize": ns, spec.keyword: sample_value}
    result = execute_command(collection, cmd)
    assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)
