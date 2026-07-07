"""Tests for bulkWrite BSON type validation of command, operation, and namespace fields.

Verifies that each bulkWrite input field accepts its valid BSON types and rejects
all other types with the correct error code, using the shared BSON type harness.
"""

from typing import Any

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
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
    DOUBLE_ZERO,
    INT32_ZERO,
    INT64_ZERO,
)

COMMAND_FIELD_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="command_bulkWrite",
        keyword="bulkWrite",
        msg="bulkWrite dispatches on the first field being named 'bulkWrite'; its value is "
        "ignored, so the command field accepts any BSON type",
        valid_types=list(BsonType),
    ),
    BsonTypeTestCase(
        id="command_ordered",
        keyword="ordered",
        msg="bulkWrite ordered accepts only bool and null",
        valid_types=[BsonType.BOOL, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="command_bypassDocumentValidation",
        keyword="bypassDocumentValidation",
        msg="bulkWrite bypassDocumentValidation accepts bool, null, and numeric types",
        valid_types=[
            BsonType.BOOL,
            BsonType.NULL,
            BsonType.DOUBLE,
            BsonType.INT,
            BsonType.LONG,
            BsonType.DECIMAL,
        ],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="command_comment",
        keyword="comment",
        msg="bulkWrite comment accepts any BSON type",
        valid_types=list(BsonType),
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="command_let",
        keyword="let",
        msg="bulkWrite let accepts only a document or null",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="command_errorsOnly",
        keyword="errorsOnly",
        msg="bulkWrite errorsOnly accepts only bool and null",
        valid_types=[BsonType.BOOL, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="command_cursor",
        keyword="cursor",
        msg="bulkWrite cursor accepts only a document or null",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.OBJECT: {"batchSize": 1}},
    ),
    BsonTypeTestCase(
        id="command_writeConcern",
        keyword="writeConcern",
        msg="bulkWrite writeConcern accepts only a document or null",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.OBJECT: {"w": 1}},
    ),
]

NAMESPACE_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="command_nsInfo",
        msg="bulkWrite nsInfo accepts only an array",
        valid_types=[BsonType.ARRAY],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
    ),
    BsonTypeTestCase(
        id="nsInfo_ns",
        msg="bulkWrite nsInfo.ns accepts only a string",
        valid_types=[BsonType.STRING],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
    ),
]

INSERT_OP_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="op_insert_index",
        msg="bulkWrite insert namespace index accepts only numeric types",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
        valid_inputs={
            BsonType.DOUBLE: DOUBLE_ZERO,
            BsonType.INT: INT32_ZERO,
            BsonType.LONG: INT64_ZERO,
            BsonType.DECIMAL: DECIMAL128_ZERO,
        },
    ),
    BsonTypeTestCase(
        id="op_document",
        msg="bulkWrite insert document accepts only a document",
        valid_types=[BsonType.OBJECT],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
    ),
]

UPDATE_OP_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="op_update_index",
        msg="bulkWrite update namespace index accepts only numeric types",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
        valid_inputs={
            BsonType.DOUBLE: DOUBLE_ZERO,
            BsonType.INT: INT32_ZERO,
            BsonType.LONG: INT64_ZERO,
            BsonType.DECIMAL: DECIMAL128_ZERO,
        },
    ),
    BsonTypeTestCase(
        id="op_filter",
        msg="bulkWrite update filter accepts only a document",
        valid_types=[BsonType.OBJECT],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
    ),
    BsonTypeTestCase(
        id="op_updateMods",
        msg="bulkWrite updateMods accepts a document or an aggregation pipeline array",
        valid_types=[BsonType.OBJECT, BsonType.ARRAY],
        default_error_code=FAILED_TO_PARSE_ERROR,
        valid_inputs={BsonType.ARRAY: [{"$set": {"x": 1}}]},
    ),
    BsonTypeTestCase(
        id="op_arrayFilters",
        msg="bulkWrite arrayFilters accepts only an array or null",
        valid_types=[BsonType.ARRAY, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.ARRAY: []},
    ),
    BsonTypeTestCase(
        id="op_multi",
        msg="bulkWrite multi accepts only bool and null",
        valid_types=[BsonType.BOOL, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="op_hint",
        msg="bulkWrite hint accepts only a string or a document",
        valid_types=[BsonType.STRING, BsonType.OBJECT],
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="op_constants",
        msg="bulkWrite constants accepts only a document or null",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="op_collation",
        msg="bulkWrite collation accepts only a document or null",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.OBJECT: {"locale": "en"}},
    ),
    BsonTypeTestCase(
        id="op_upsert",
        msg="bulkWrite upsert accepts only bool and null",
        valid_types=[BsonType.BOOL, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
]

DELETE_OP_PARAMS: list[BsonTypeTestCase] = [
    BsonTypeTestCase(
        id="op_delete_index",
        msg="bulkWrite delete namespace index accepts only numeric types",
        valid_types=[BsonType.DOUBLE, BsonType.INT, BsonType.LONG, BsonType.DECIMAL],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
        valid_inputs={
            BsonType.DOUBLE: DOUBLE_ZERO,
            BsonType.INT: INT32_ZERO,
            BsonType.LONG: INT64_ZERO,
            BsonType.DECIMAL: DECIMAL128_ZERO,
        },
    ),
    BsonTypeTestCase(
        id="op_delete_filter",
        msg="bulkWrite delete filter accepts only a document",
        valid_types=[BsonType.OBJECT],
        default_error_code=TYPE_MISMATCH_ERROR,
        error_code_overrides={BsonType.NULL: MISSING_FIELD_ERROR},
    ),
    BsonTypeTestCase(
        id="op_delete_multi",
        msg="bulkWrite delete multi accepts only bool and null",
        valid_types=[BsonType.BOOL, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
    ),
    BsonTypeTestCase(
        id="op_delete_hint",
        msg="bulkWrite delete hint accepts only a string or a document",
        valid_types=[BsonType.STRING, BsonType.OBJECT],
        default_error_code=FAILED_TO_PARSE_ERROR,
    ),
    BsonTypeTestCase(
        id="op_delete_collation",
        msg="bulkWrite delete collation accepts only a document or null",
        valid_types=[BsonType.OBJECT, BsonType.NULL],
        default_error_code=TYPE_MISMATCH_ERROR,
        valid_inputs={BsonType.OBJECT: {"locale": "en"}},
    ),
]

BULKWRITE_TYPE_PARAMS: list[BsonTypeTestCase] = (
    COMMAND_FIELD_PARAMS + NAMESPACE_PARAMS + INSERT_OP_PARAMS + UPDATE_OP_PARAMS + DELETE_OP_PARAMS
)


def _inject_command_nsInfo(
    command: dict[str, Any], bson_type: BsonType, sample_value: Any, namespace: str
) -> None:
    """Replace the whole ``nsInfo`` array (valid ARRAY uses the live namespace)."""
    command["nsInfo"] = [{"ns": namespace}] if bson_type == BsonType.ARRAY else sample_value


def _inject_nsInfo_ns(
    command: dict[str, Any], bson_type: BsonType, sample_value: Any, namespace: str
) -> None:
    """Set ``nsInfo[0].ns`` (valid STRING uses the live namespace)."""
    ns_val = namespace if bson_type == BsonType.STRING else sample_value
    command["nsInfo"] = [{"ns": ns_val}]


def _inject_op_field(command: dict[str, Any], spec_id: str, sample_value: Any) -> None:
    """Build the op under test with ``sample_value`` and set it as ``ops[0]``.

    Field order matters: the op discriminator (insert/update/delete) must be first, so
    ``sample_value`` leads the ``*_index`` specs.
    """
    ops_by_spec: dict[str, dict[str, Any]] = {
        "op_insert_index": {"insert": sample_value, "document": {"_id": 1}},
        "op_document": {"insert": 0, "document": sample_value},
        "op_update_index": {"update": sample_value, "filter": {}, "updateMods": {"$set": {"x": 1}}},
        "op_filter": {"update": 0, "filter": sample_value, "updateMods": {"$set": {"x": 1}}},
        "op_updateMods": {"update": 0, "filter": {}, "updateMods": sample_value},
        "op_arrayFilters": {
            "update": 0,
            "filter": {},
            "updateMods": {"$set": {"x": 1}},
            "arrayFilters": sample_value,
        },
        "op_multi": {
            "update": 0,
            "filter": {},
            "updateMods": {"$set": {"x": 1}},
            "multi": sample_value,
        },
        "op_hint": {
            "update": 0,
            "filter": {},
            "updateMods": {"$set": {"x": 1}},
            "hint": sample_value,
        },
        "op_constants": {
            "update": 0,
            "filter": {},
            "updateMods": [{"$set": {"x": 1}}],
            "constants": sample_value,
        },
        "op_collation": {
            "update": 0,
            "filter": {},
            "updateMods": {"$set": {"x": 1}},
            "collation": sample_value,
        },
        "op_upsert": {
            "update": 0,
            "filter": {},
            "updateMods": {"$set": {"x": 1}},
            "upsert": sample_value,
        },
        "op_delete_index": {"delete": sample_value, "filter": {}},
        "op_delete_filter": {"delete": 0, "filter": sample_value},
        "op_delete_multi": {"delete": 0, "filter": {}, "multi": sample_value},
        "op_delete_hint": {"delete": 0, "filter": {}, "hint": sample_value},
        "op_delete_collation": {"delete": 0, "filter": {}, "collation": sample_value},
    }
    command["ops"] = [ops_by_spec[spec_id]]


def _inject_top_level(command: dict[str, Any], spec: BsonTypeTestCase, sample_value: Any) -> None:
    """Set a top-level command field directly on the command document."""
    if spec.keyword is None:
        raise ValueError(f"top-level spec {spec.id!r} must define a keyword")
    command[spec.keyword] = sample_value


def _build_command(
    spec: BsonTypeTestCase, bson_type: BsonType, sample_value: Any, namespace: str
) -> dict[str, Any]:
    """Build a bulkWrite command injecting ``sample_value`` into the field named by ``spec``."""
    command: dict[str, Any] = {
        "bulkWrite": 1,
        "ops": [{"insert": 0, "document": {"_id": 1}}],
        "nsInfo": [{"ns": namespace}],
    }

    if spec.id == "command_nsInfo":
        _inject_command_nsInfo(command, bson_type, sample_value, namespace)
    elif spec.id == "nsInfo_ns":
        _inject_nsInfo_ns(command, bson_type, sample_value, namespace)
    elif spec.id.startswith("op_"):
        _inject_op_field(command, spec.id, sample_value)
    else:
        _inject_top_level(command, spec, sample_value)

    return command


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_rejection_test_cases(BULKWRITE_TYPE_PARAMS)
)
def test_bulkWrite_bson_type_rejected(collection, bson_type, sample_value, spec):
    """Test bulkWrite rejects invalid BSON types for each input field with the correct code."""
    namespace = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection, _build_command(spec, bson_type, sample_value, namespace)
    )
    assertFailureCode(
        result, spec.expected_code(bson_type), msg=f"{spec.msg}: rejects {bson_type.value}"
    )


@pytest.mark.parametrize(
    "bson_type,sample_value,spec", generate_bson_acceptance_test_cases(BULKWRITE_TYPE_PARAMS)
)
def test_bulkWrite_bson_type_accepted(collection, bson_type, sample_value, spec):
    """Test bulkWrite accepts valid BSON types for each input field."""
    namespace = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection, _build_command(spec, bson_type, sample_value, namespace)
    )
    assertSuccessPartial(
        result, {"ok": 1.0, "nErrors": 0}, msg=f"{spec.msg}: accepts {bson_type.value}"
    )
