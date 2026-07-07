"""writeConcern BSON type validation: the writeConcern field accepts only a
document or null, and the w/j/wtimeout sub-fields accept their supported BSON
types; all other types are rejected.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

WRITE_CONCERN_PARAMS = [
    BsonTypeTestCase(
        id="write_concern_field",
        msg="writeConcern should reject non-document types",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.OBJECT: {"w": 1}},
    ),
]

SUB_FIELD_PARAMS = [
    BsonTypeTestCase(
        id="w",
        msg="w should accept numbers, 'majority', and tagged objects",
        valid_types=[
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
            BsonType.STRING,
            BsonType.OBJECT,
        ],
        skip_rejection_types=[BsonType.NULL],
        default_error_code=FAILED_TO_PARSE_ERROR,
        valid_inputs={
            BsonType.INT: 1,
            BsonType.LONG: Int64(1),
            BsonType.DOUBLE: 1.0,
            BsonType.DECIMAL: Decimal128("1"),
            BsonType.STRING: "majority",
            BsonType.OBJECT: {"dc1": 1},
        },
    ),
    BsonTypeTestCase(
        id="j",
        msg="j should accept boolean, numeric types, and null",
        valid_types=[
            BsonType.BOOL,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="wtimeout",
        msg="wtimeout should accept all BSON types",
        valid_types=list(BsonType),
        default_error_code=FAILED_TO_PARSE_ERROR,
        valid_inputs={BsonType.LONG: Int64(5_000)},
    ),
]


def _build_command(collection_name, spec, sample_value):
    """Build an update command placing the sample value per the spec."""
    if spec.id == "write_concern_field":
        write_concern = sample_value
    elif spec.id == "w":
        write_concern = {"w": sample_value}
    else:
        write_concern = {"w": 1, spec.id: sample_value}
    return {
        "update": collection_name,
        "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
        "writeConcern": write_concern,
    }


_ALL_PARAMS = WRITE_CONCERN_PARAMS + SUB_FIELD_PARAMS


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_acceptance_test_cases(_ALL_PARAMS)
)
def test_write_concern_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test the writeConcern field and sub-fields accept their supported BSON types."""
    result = execute_command(collection, _build_command(collection.name, spec, sample_value))
    assertSuccessPartial(result, {"ok": 1.0}, msg=f"{spec.id} should accept {bson_type.value}")


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_rejection_test_cases(_ALL_PARAMS)
)
def test_write_concern_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test the writeConcern field and sub-fields reject unsupported BSON types."""
    result = execute_command(collection, _build_command(collection.name, spec, sample_value))
    assertResult(
        result,
        error_code=spec.expected_code(bson_type),
        msg=f"{spec.id} should reject {bson_type.value}",
    )
