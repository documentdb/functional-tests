"""Tests for listCollections command field value acceptance."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNRECOGNIZED_COMMAND_FIELD_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len

# Property [Command Field Value Acceptance]: the listCollections field
# value is completely ignored - any BSON type and any value is accepted.
COMMAND_FIELD_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_int_zero",
        command={"listCollections": 0},
        msg="listCollections=0 should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_int_negative",
        command={"listCollections": -1},
        msg="listCollections=-1 should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_int_positive",
        command={"listCollections": 42},
        msg="listCollections=42 should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_string",
        command={"listCollections": "hello"},
        msg="listCollections='hello' should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_bool_true",
        command={"listCollections": True},
        msg="listCollections=True should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_bool_false",
        command={"listCollections": False},
        msg="listCollections=False should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_null",
        command={"listCollections": None},
        msg="listCollections=None should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_empty_list",
        command={"listCollections": []},
        msg="listCollections=[] should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_empty_dict",
        command={"listCollections": {}},
        msg="listCollections={} should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_float",
        command={"listCollections": 3.14},
        msg="listCollections=3.14 should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_decimal128",
        command={"listCollections": Decimal128("99")},
        msg="listCollections=Decimal128 should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_int64",
        command={"listCollections": Int64(123)},
        msg="listCollections=Int64 should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_objectid",
        command=lambda _: {"listCollections": ObjectId()},
        msg="listCollections=ObjectId should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_datetime",
        command={"listCollections": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="listCollections=datetime should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_timestamp",
        command={"listCollections": Timestamp(1, 1)},
        msg="listCollections=Timestamp should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_binary",
        command={"listCollections": Binary(b"hello")},
        msg="listCollections=Binary should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_regex",
        command={"listCollections": Regex(".*")},
        msg="listCollections=Regex should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_code",
        command={"listCollections": Code("function(){}")},
        msg="listCollections=Code should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_code_with_scope",
        command={"listCollections": Code("function(){}", {"x": 1})},
        msg="listCollections=CodeWithScope should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_minkey",
        command={"listCollections": MinKey()},
        msg="listCollections=MinKey should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="value_maxkey",
        command={"listCollections": MaxKey()},
        msg="listCollections=MaxKey should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
]

# Property [Unknown Field Errors]: unknown fields in the command
# document or within the cursor sub-document produce
# UNRECOGNIZED_COMMAND_FIELD_ERROR.
UNKNOWN_FIELD_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="unknown_top_level_field",
        command={"listCollections": 1, "unknownField": 1},
        msg="Unknown top-level field should produce UNRECOGNIZED_COMMAND_FIELD_ERROR",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
    CommandTestCase(
        id="unknown_cursor_sub_field",
        command={"listCollections": 1, "cursor": {"batchSize": 10, "unknownSub": 1}},
        msg="Unknown cursor sub-field should produce UNRECOGNIZED_COMMAND_FIELD_ERROR",
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
    ),
]

COMMAND_ACCEPTANCE_TESTS: list[CommandTestCase] = (
    COMMAND_FIELD_VALUE_TESTS + UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMMAND_ACCEPTANCE_TESTS))
def test_listCollections_command_acceptance(database_client, collection, test):
    """Test listCollections command field value acceptance."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
