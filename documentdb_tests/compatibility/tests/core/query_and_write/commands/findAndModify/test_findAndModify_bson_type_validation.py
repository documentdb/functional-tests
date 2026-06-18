"""
BSON type validation tests for findAndModify command parameters.

Verifies that findAndModify correctly rejects invalid BSON types for all
parameters and accepts valid types.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_NAMESPACE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command

BSON_PARAMS = [
    BsonTypeTestCase(
        id="findAndModify",
        msg="findAndModify collection name should reject non-string types",
        keyword="findAndModify",
        valid_types=[BsonType.STRING],
        default_error_code=INVALID_NAMESPACE_ERROR,
    ),
    BsonTypeTestCase(
        id="query",
        msg="findAndModify query should reject non-document types",
        keyword="query",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="sort",
        msg="findAndModify sort should reject non-document types",
        keyword="sort",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="update",
        msg="findAndModify update should reject non-document/array types",
        keyword="update",
        valid_types=[BsonType.OBJECT, BsonType.ARRAY],
        valid_inputs={
            BsonType.OBJECT: {"$set": {"x": 1}},
            BsonType.ARRAY: [{"$set": {"x": 1}}],
        },
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="fields",
        msg="findAndModify fields should reject non-document types",
        keyword="fields",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        valid_inputs={BsonType.OBJECT: {"x": 1}, BsonType.NULL: None},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="remove",
        msg="findAndModify remove should reject non-numeric/non-bool types",
        keyword="remove",
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
        id="new",
        msg="findAndModify new should reject non-numeric/non-bool types",
        keyword="new",
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
        id="upsert",
        msg="findAndModify upsert should reject non-numeric/non-bool types",
        keyword="upsert",
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
        id="bypassDocumentValidation",
        msg="findAndModify bypassDocumentValidation should reject non-numeric/non-bool types",
        keyword="bypassDocumentValidation",
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
        id="maxTimeMS",
        msg="findAndModify maxTimeMS should reject non-numeric types",
        keyword="maxTimeMS",
        valid_types=[
            BsonType.INT,
            BsonType.LONG,
            BsonType.DOUBLE,
            BsonType.DECIMAL,
            BsonType.NULL,
        ],
        valid_inputs={
            BsonType.INT: 100,
            BsonType.LONG: 100,
            BsonType.DOUBLE: 100.0,
            BsonType.DECIMAL: 100,
            BsonType.NULL: None,
        },
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="collation",
        msg="findAndModify collation should reject non-document types",
        keyword="collation",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        valid_inputs={BsonType.OBJECT: {"locale": "en"}, BsonType.NULL: None},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="writeConcern",
        msg="findAndModify writeConcern should reject non-document types",
        keyword="writeConcern",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        valid_inputs={BsonType.OBJECT: {"w": 1}, BsonType.NULL: None},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="let",
        msg="findAndModify let should reject non-document types",
        keyword="let",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        valid_inputs={BsonType.OBJECT: {"a": 1}, BsonType.NULL: None},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="arrayFilters",
        msg="findAndModify arrayFilters should reject non-array types",
        keyword="arrayFilters",
        valid_types=[BsonType.ARRAY, BsonType.NULL],
        valid_inputs={BsonType.ARRAY: [], BsonType.NULL: None},
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="hint",
        msg="findAndModify hint should reject non-document/non-string types",
        keyword="hint",
        valid_types=[BsonType.OBJECT, BsonType.STRING],
        valid_inputs={
            BsonType.OBJECT: {"_id": 1},
            BsonType.STRING: "_id_",
        },
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="comment",
        msg="findAndModify comment should accept all BSON types",
        keyword="comment",
        valid_types=list(BsonType),
    ),
]

REJECTION_TESTS = generate_bson_rejection_test_cases(BSON_PARAMS)
ACCEPTANCE_TESTS = generate_bson_acceptance_test_cases(BSON_PARAMS)


def _build_command(collection_name, spec, sample_value):
    """Build a findAndModify command with sample_value placed at spec.keyword."""
    cmd = {
        "findAndModify": collection_name,
        "query": {"_id": 1},
        "update": {"$set": {"x": 1}},
        spec.keyword: sample_value,
    }
    if spec.id == "remove" and sample_value:
        cmd.pop("update", None)
    return cmd


def _build_expected(spec, sample_value):
    """Build expected partial result based on which parameter is being tested."""
    # These keywords replace query or collection name, so the doc may not be found
    if spec.keyword in ("query", "findAndModify"):
        return {"ok": 1.0}
    # remove with truthy value deletes the matched doc
    if spec.id == "remove" and sample_value:
        return {"ok": 1.0, "lastErrorObject": {"n": 1}, "value": {"_id": 1, "x": 10}}
    # All other keywords: query is {_id:1} which matches, update runs
    return {"ok": 1.0, "lastErrorObject": {"n": 1, "updatedExisting": True}}


@pytest.mark.parametrize("bson_type,sample_value,spec", REJECTION_TESTS)
def test_findAndModify_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Verifies findAndModify rejects invalid BSON types for each parameter."""
    collection.insert_one({"_id": 1, "x": 10})
    result = execute_command(collection, _build_command(collection.name, spec, sample_value))
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


@pytest.mark.parametrize("bson_type,sample_value,spec", ACCEPTANCE_TESTS)
def test_findAndModify_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Verifies findAndModify accepts valid BSON types for each parameter."""
    collection.insert_one({"_id": 1, "x": 10})
    result = execute_command(collection, _build_command(collection.name, spec, sample_value))
    assertSuccessPartial(
        result,
        _build_expected(spec, sample_value),
        msg=f"findAndModify should accept {bson_type.value} for {spec.keyword}",
    )
