"""Tests for bulkWrite error and rejection cases."""

import uuid

import pytest
from bson.binary import Binary

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
    IndexModel,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    BSON_OBJECT_TOO_LARGE_ERROR,
    COLLECTION_UUID_MISMATCH_ERROR,
    COMMAND_NOT_FOUND_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    DOCUMENT_VALIDATION_FAILURE_ERROR,
    DUPLICATE_KEY_ERROR,
    FAILED_TO_PARSE_ERROR,
    IMMUTABLE_FIELD_ERROR,
    INVALID_BSON_ID_ERROR,
    INVALID_LENGTH_ERROR,
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
    UPDATE_C_FIELD_REQUIRES_PIPELINE_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len
from documentdb_tests.framework.target_collection import CustomCollection, ViewCollection

BULKWRITE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "ops_empty_array",
        command={"bulkWrite": 1, "ops": []},
        error_code=INVALID_LENGTH_ERROR,
        msg="bulkWrite with an empty ops array should fail with InvalidLength",
    ),
    CommandTestCase(
        "ops_field_missing",
        command={"bulkWrite": 1},
        error_code=MISSING_FIELD_ERROR,
        msg="bulkWrite without an ops field should fail with MissingField",
    ),
    CommandTestCase(
        "ops_insert_missing_document",
        command={"bulkWrite": 1, "ops": [{"insert": 0}]},
        error_code=MISSING_FIELD_ERROR,
        msg="bulkWrite insert op missing document should fail with MissingField",
    ),
    CommandTestCase(
        "ops_update_missing_filter",
        command={"bulkWrite": 1, "ops": [{"update": 0, "updateMods": {"$set": {"x": 1}}}]},
        error_code=MISSING_FIELD_ERROR,
        msg="bulkWrite update op missing filter should fail with MissingField",
    ),
    CommandTestCase(
        "ops_delete_missing_filter",
        command={"bulkWrite": 1, "ops": [{"delete": 0}]},
        error_code=MISSING_FIELD_ERROR,
        msg="bulkWrite delete op missing filter should fail with MissingField",
    ),
    CommandTestCase(
        "ops_invalid_namespace_index",
        command={"bulkWrite": 1, "ops": [{"insert": 5, "document": {"_id": 1}}]},
        error_code=BAD_VALUE_ERROR,
        msg="bulkWrite op referencing a non-existent nsInfo index should fail with BadValue",
    ),
    CommandTestCase(
        "ops_negative_namespace_index",
        command={"bulkWrite": 1, "ops": [{"insert": -1, "document": {"_id": 1}}]},
        error_code=BAD_VALUE_ERROR,
        msg="bulkWrite op with a negative namespace index should fail with BadValue",
    ),
    CommandTestCase(
        "nsInfo_empty_array",
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}], "nsInfo": []},
        error_code=BAD_VALUE_ERROR,
        msg="bulkWrite with an empty nsInfo array should fail with BadValue",
    ),
    CommandTestCase(
        "nsInfo_invalid_ns_format",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "nsInfo": [{"ns": "no_dot"}],
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="bulkWrite with an invalid namespace format should fail with InvalidNamespace",
    ),
    CommandTestCase(
        "unrecognized_top_level_field",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "unknownField": True,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="bulkWrite with an unrecognized top-level field should fail",
    ),
    CommandTestCase(
        "unrecognized_op_discriminator",
        command={
            "bulkWrite": 1,
            "ops": [{"replace": 0, "document": {"_id": 1}}],
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="bulkWrite op with an unrecognized discriminator should fail at parse time",
    ),
]

BULKWRITE_OPERATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "invalid_filter_expression",
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"$badOp": 1}, "updateMods": {"$set": {"x": 1}}}],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nModified": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(BAD_VALUE_ERROR),
        },
        msg="bulkWrite with an invalid query operator should report nErrors:1",
    ),
    CommandTestCase(
        "invalid_update_expression",
        docs=[{"_id": 1, "x": 1}],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"_id": 1}, "updateMods": {"$badOp": {"x": 1}}}],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nModified": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(FAILED_TO_PARSE_ERROR),
        },
        msg="bulkWrite with an invalid update operator should report nErrors:1",
    ),
    CommandTestCase(
        "duplicate_id_insert",
        docs=[{"_id": 1}],
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}]},
        expected={"ok": Eq(1.0), "nErrors": Eq(1), "nInserted": Eq(0)},
        msg="bulkWrite duplicate _id insert should report nErrors:1",
    ),
    CommandTestCase(
        "ordered_true_stops_at_dupkey",
        docs=[{"_id": 1}],
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
                {"insert": 0, "document": {"_id": 3}},
            ],
            "ordered": True,
        },
        expected={"ok": Eq(1.0), "nErrors": Eq(1), "nInserted": Eq(0)},
        msg="bulkWrite ordered:true should stop at the duplicate key",
    ),
    CommandTestCase(
        "ordered_false_continues_after_dupkey",
        docs=[{"_id": 1}],
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
                {"insert": 0, "document": {"_id": 3}},
            ],
            "ordered": False,
        },
        expected={"ok": Eq(1.0), "nErrors": Eq(1), "nInserted": Eq(2)},
        msg="bulkWrite ordered:false should continue after the duplicate key",
    ),
    CommandTestCase(
        "insert_unique_index_violation",
        indexes=[IndexModel([("x", 1)], unique=True)],
        docs=[{"_id": 1, "x": 1}],
        command={"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 2, "x": 1}}]},
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nInserted": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(DUPLICATE_KEY_ERROR),
        },
        msg="bulkWrite insert violating a unique index should report nErrors:1",
    ),
    CommandTestCase(
        "update_causes_unique_index_violation",
        indexes=[IndexModel([("x", 1)], unique=True)],
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"_id": 2}, "updateMods": {"$set": {"x": 1}}}],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nModified": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(DUPLICATE_KEY_ERROR),
        },
        msg="bulkWrite update causing a unique index violation should report nErrors:1",
    ),
    CommandTestCase(
        "update_immutable_field",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"_id": 2}}}],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nModified": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(IMMUTABLE_FIELD_ERROR),
        },
        msg="bulkWrite update of the immutable _id field should report nErrors:1",
    ),
    CommandTestCase(
        "update_on_view",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": 1}],
        command={
            "bulkWrite": 1,
            "ops": [{"update": 0, "filter": {}, "updateMods": {"$set": {"x": 2}}}],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nModified": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR),
        },
        msg="bulkWrite update on a view should report nErrors:1",
    ),
    CommandTestCase(
        "delete_on_view",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": 1}],
        command={
            "bulkWrite": 1,
            "ops": [{"delete": 0, "filter": {}}],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nDeleted": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR),
        },
        msg="bulkWrite delete on a view should report nErrors:1",
    ),
    CommandTestCase(
        "schema_validation_rejects_insert",
        target_collection=CustomCollection(
            options={"validator": {"$jsonSchema": {"required": ["name"]}}}
        ),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "bypassDocumentValidation": False,
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nInserted": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(DOCUMENT_VALIDATION_FAILURE_ERROR),
        },
        msg="bulkWrite bypassDocumentValidation:false should reject a validator-violating insert",
    ),
    CommandTestCase(
        "arrayFilters_invalid_filter",
        docs=[{"_id": 1, "items": [{"x": 1}]}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": {"$set": {"items.$[elem].x": 99}},
                    "arrayFilters": [{"elem.x": {"$badOp": 1}}],
                }
            ],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nModified": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(BAD_VALUE_ERROR),
        },
        msg="bulkWrite arrayFilters with an invalid operator should report nErrors:1",
    ),
    CommandTestCase(
        "update_hint_nonexistent_index",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"x": 10},
                    "updateMods": {"$set": {"x": 20}},
                    "hint": "nonexistent_index",
                }
            ],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nModified": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(BAD_VALUE_ERROR),
        },
        msg="bulkWrite update with a hint on a non-existent index should report nErrors:1",
    ),
    CommandTestCase(
        "delete_hint_nonexistent_index",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [{"delete": 0, "filter": {"x": 10}, "hint": "nonexistent_index"}],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nDeleted": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(BAD_VALUE_ERROR),
        },
        msg="bulkWrite delete with a hint on a non-existent index should report nErrors:1",
    ),
    CommandTestCase(
        "constants_on_non_pipeline_update",
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": {"$set": {"x": 20}},
                    "constants": {"val": 1},
                }
            ],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nModified": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(UPDATE_C_FIELD_REQUIRES_PIPELINE_ERROR),
        },
        msg="bulkWrite constants on a non-pipeline update should report nErrors:1",
    ),
    CommandTestCase(
        "errorsOnly_true_with_error",
        docs=[{"_id": 1}],
        command={
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
            ],
            "errorsOnly": True,
            "ordered": False,
        },
        expected={"ok": Eq(1.0), "nErrors": Eq(1)},
        msg="bulkWrite errorsOnly:true with a failing operation should report nErrors:1",
    ),
    CommandTestCase(
        "array_id_surfaces_as_op_level_error",
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": [1, 2]}}],
        },
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nInserted": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(INVALID_BSON_ID_ERROR),
        },
        msg="bulkWrite should surface an array _id as an op-level error (code 53), not reject it",
    ),
    CommandTestCase(
        "collection_uuid_mismatch",
        docs=[{"_id": 0}],
        command=lambda ctx: {
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "nsInfo": [{"ns": ctx.namespace, "collectionUUID": Binary(uuid.uuid4().bytes, 4)}],
        },
        # Unlike renameCollection (top-level), bulkWrite surfaces this mismatch op-level.
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nInserted": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(COLLECTION_UUID_MISMATCH_ERROR),
        },
        msg="bulkWrite should surface a collectionUUID mismatch as an op-level error (code 361)",
    ),
]

BULKWRITE_ERROR_TESTS = BULKWRITE_REJECTION_TESTS + BULKWRITE_OPERATION_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(BULKWRITE_ERROR_TESTS))
def test_bulkWrite_errors(database_client, collection, test):
    """Test bulkWrite error and rejection cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = test.build_command(ctx)
    if "nsInfo" not in command:
        command = {**command, "nsInfo": [{"ns": ctx.namespace}]}
    result = execute_admin_command(collection, command)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


def test_bulkWrite_failure_in_one_ns_does_not_block_another(collection):
    """Test an unordered bulkWrite failure in one namespace does not block writes to another."""
    sibling = collection.database[f"{collection.name}_b"]
    sibling.drop()
    collection.insert_one({"_id": 1, "x": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_b = f"{collection.database.name}.{sibling.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "x": 2}},  # dup key on ns 0
                {"insert": 1, "document": {"_id": 1, "y": 1}},  # succeeds on ns 1
            ],
            "nsInfo": [{"ns": ns}, {"ns": ns_b}],
            "ordered": False,
        },
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0), "nInserted": Eq(1), "nErrors": Eq(1)},
        raw_res=True,
    )
    sibling.drop()


def test_bulkWrite_command_name_must_be_first_field(collection):
    """Test bulkWrite is rejected with CommandNotFound when bulkWrite is not the first field."""
    ns = f"{collection.database.name}.{collection.name}"
    # nsInfo is intentionally placed before bulkWrite so it is read as the command name.
    result = execute_admin_command(
        collection,
        {
            "nsInfo": [{"ns": ns}],
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
        },
    )
    assertResult(result, error_code=COMMAND_NOT_FOUND_ERROR, raw_res=True)


def test_bulkWrite_oversized_document(collection):
    """Test an op inserting a document over the 16MB BSON limit reports an op-level error."""
    large_doc = {"_id": 1, "data": "x" * (16 * 1024 * 1024)}
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection,
        {"bulkWrite": 1, "ops": [{"insert": 0, "document": large_doc}], "nsInfo": [{"ns": ns}]},
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nInserted": Eq(0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(BSON_OBJECT_TOO_LARGE_ERROR),
        },
        raw_res=True,
        msg="bulkWrite oversized document should report an op-level BSONObjectTooLarge error",
    )


def test_bulkWrite_oversized_document_in_batch(collection):
    """Test an oversized doc fails op-level while a sibling op in the unordered batch succeeds."""
    large_doc = {"_id": 1, "data": "x" * (16 * 1024 * 1024)}
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": large_doc},
                {"insert": 0, "document": {"_id": 2, "x": 1}},
            ],
            "nsInfo": [{"ns": ns}],
            "ordered": False,
        },
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nInserted": Eq(1),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(BSON_OBJECT_TOO_LARGE_ERROR),
        },
        raw_res=True,
        msg="bulkWrite oversized doc should fail op-level while the sibling op succeeds",
    )


def test_bulkWrite_duplicate_key_per_op_cursor_detail(collection):
    """Test a dup-key op reports per-op detail (idx/code/keyPattern/keyValue) in firstBatch."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection,
        {"bulkWrite": 1, "ops": [{"insert": 0, "document": {"_id": 1}}], "nsInfo": [{"ns": ns}]},
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "nErrors": Eq(1),
            "nInserted": Eq(0),
            "cursor.firstBatch.0.ok": Eq(0.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.0.code": Eq(DUPLICATE_KEY_ERROR),
            "cursor.firstBatch.0.keyPattern": Eq({"_id": 1}),
            "cursor.firstBatch.0.keyValue": Eq({"_id": 1}),
        },
        raw_res=True,
        msg="bulkWrite dup-key op should report per-op detail (idx/code/keyPattern/keyValue) "
        "in firstBatch",
    )


def test_bulkWrite_ordered_partial_success_cursor_shape(collection):
    """Test ordered:true partial-succeeds, errors at idx 1, and omits the never-run 3rd op."""
    collection.insert_one({"_id": 1})  # pre-existing → second op is a dup
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 2}},  # good
                {"insert": 0, "document": {"_id": 1}},  # dup → error at idx 1
                {"insert": 0, "document": {"_id": 3}},  # never runs (ordered:true)
            ],
            "nsInfo": [{"ns": ns}],
            "ordered": True,
        },
    )
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "nInserted": Eq(1),
            "nErrors": Eq(1),
            "cursor.firstBatch": Len(2),  # 3rd op absent — never executed
            "cursor.firstBatch.0.ok": Eq(1.0),
            "cursor.firstBatch.0.idx": Eq(0),
            "cursor.firstBatch.1.ok": Eq(0.0),
            "cursor.firstBatch.1.idx": Eq(1),
            "cursor.firstBatch.1.code": Eq(DUPLICATE_KEY_ERROR),
        },
        raw_res=True,
        msg="bulkWrite ordered:true should partial-succeed, error at idx 1, and omit the 3rd op",
    )


_MAX_WRITE_BATCH_SIZE = 100_000


def test_bulkWrite_exceeds_max_write_batch_size(collection):
    """Test exceeding maxWriteBatchSize (100,000 ops) is rejected with InvalidLength."""
    ns = f"{collection.database.name}.{collection.name}"
    ops = [{"insert": 0, "document": {}} for _ in range(_MAX_WRITE_BATCH_SIZE + 1)]
    result = execute_admin_command(
        collection,
        {"bulkWrite": 1, "ops": ops, "nsInfo": [{"ns": ns}]},
    )
    assertResult(
        result,
        error_code=INVALID_LENGTH_ERROR,
        raw_res=True,
        msg="bulkWrite exceeding maxWriteBatchSize should fail with InvalidLength",
    )
