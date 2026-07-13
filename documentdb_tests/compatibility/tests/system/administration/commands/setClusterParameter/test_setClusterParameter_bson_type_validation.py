"""Tests for setClusterParameter BSON type validation.

The setClusterParameter command value field accepts only object (document) type.
Parameter value fields each accept specific BSON types.
"""

import pytest
from bson import Int64
from bson.decimal128 import Decimal128

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]

# NULL is skipped from the rejection matrices below: its behavior is field-dependent and does not
# cleanly map to success or failure, so it is covered by dedicated tests in the other files.
BSON_TYPE_SPECS = [
    BsonTypeTestCase(
        id="setClusterParameter_value",
        msg="setClusterParameter value should only accept object type",
        keyword="setClusterParameter",
        valid_types=[BsonType.OBJECT],
        skip_rejection_types=[BsonType.NULL],
        valid_inputs={
            BsonType.OBJECT: {
                "changeStreamOptions": {"preAndPostImages": {"expireAfterSeconds": 7200}}
            },
        },
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="bool_param_pauseMigrations",
        msg="pauseMigrationsDuringMultiUpdates.enabled accepts only bool",
        keyword="pauseMigrationsDuringMultiUpdates",
        valid_types=[BsonType.BOOL],
        skip_rejection_types=[BsonType.NULL],
        valid_inputs={BsonType.BOOL: {"enabled": False}},
        requires={"field": "enabled"},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="numeric_param_changeStreams",
        msg="changeStreams.expireAfterSeconds accepts only numeric types",
        keyword="changeStreams",
        valid_types=[BsonType.INT, BsonType.LONG, BsonType.DOUBLE, BsonType.DECIMAL],
        skip_rejection_types=[BsonType.NULL],
        valid_inputs={
            BsonType.INT: {"expireAfterSeconds": 3600},
            BsonType.LONG: {"expireAfterSeconds": Int64(3600)},
            BsonType.DOUBLE: {"expireAfterSeconds": 3600.0},
            BsonType.DECIMAL: {"expireAfterSeconds": Decimal128("3600")},
        },
        requires={"field": "expireAfterSeconds"},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="document_param_changeStreamOptions",
        msg="changeStreamOptions.preAndPostImages accepts only object type",
        keyword="changeStreamOptions",
        valid_types=[BsonType.OBJECT],
        skip_rejection_types=[BsonType.NULL],
        valid_inputs={BsonType.OBJECT: {"preAndPostImages": {"expireAfterSeconds": 7200}}},
        requires={"field": "preAndPostImages"},
        default_error_code=BAD_VALUE_ERROR,
    ),
]

ALL_REJECTIONS = generate_bson_rejection_test_cases(BSON_TYPE_SPECS)
ALL_ACCEPTANCES = generate_bson_acceptance_test_cases(BSON_TYPE_SPECS)

_DEFAULTS = {
    "changeStreamOptions": {"preAndPostImages": {"expireAfterSeconds": "off"}},
    "changeStreams": {"expireAfterSeconds": Int64(3600)},
    "pauseMigrationsDuringMultiUpdates": {"enabled": False},
}


def _build_command(spec, sample_value, *, is_rejection):
    """Build the setClusterParameter command for a given spec and sample value."""
    if spec.keyword == "setClusterParameter":
        return {"setClusterParameter": sample_value}
    if is_rejection:
        field = spec.requires["field"]
        return {"setClusterParameter": {spec.keyword: {field: sample_value}}}
    return {"setClusterParameter": {spec.keyword: sample_value}}


def _restore_default(collection, spec):
    """Restore a parameter to its default value after an acceptance test."""
    if spec.keyword == "setClusterParameter":
        execute_admin_command(
            collection,
            {
                "setClusterParameter": {
                    "changeStreamOptions": {"preAndPostImages": {"expireAfterSeconds": "off"}}
                }
            },
        )
    else:
        if spec.keyword in _DEFAULTS:
            execute_admin_command(
                collection, {"setClusterParameter": {spec.keyword: _DEFAULTS[spec.keyword]}}
            )


@pytest.mark.parametrize("bson_type,sample_value,spec", ALL_REJECTIONS)
def test_setClusterParameter_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test setClusterParameter rejects invalid BSON types."""
    command = _build_command(spec, sample_value, is_rejection=True)
    result = execute_admin_command(collection, command)
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ALL_ACCEPTANCES)
def test_setClusterParameter_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test setClusterParameter accepts valid BSON types."""
    command = _build_command(spec, sample_value, is_rejection=False)
    try:
        result = execute_admin_command(collection, command)
        assertSuccessPartial(result, {"ok": 1.0}, msg=spec.msg)
    finally:
        _restore_default(collection, spec)
