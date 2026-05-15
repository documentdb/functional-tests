"""Tests for the create command write concern acceptance behavior."""

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
)

# Property [WriteConcern Document Acceptance]: the writeConcern option accepts
# a document or null; empty document succeeds; w accepts numbers, "majority",
# and tagged objects.
CREATE_WC_DOCUMENT_AND_W_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="wc_null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": None,
        },
        expected={"ok": 1.0},
        msg="null writeConcern should be treated as omitted",
    ),
    CommandTestCase(
        id="wc_empty_document",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {},
        },
        expected={"ok": 1.0},
        msg="Empty writeConcern document should succeed",
    ),
    CommandTestCase(
        id="wc_w_zero",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 0},
        },
        expected={"ok": 1.0},
        msg="w:0 should succeed",
    ),
    CommandTestCase(
        id="wc_w_one",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1},
        },
        expected={"ok": 1.0},
        msg="w:1 should succeed",
    ),
    CommandTestCase(
        id="wc_w_majority",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": "majority"},
        },
        expected={"ok": 1.0},
        msg="w:'majority' should succeed",
    ),
    CommandTestCase(
        id="wc_w_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1.0},
        },
        expected={"ok": 1.0},
        msg="w as double should succeed",
    ),
    CommandTestCase(
        id="wc_w_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": Int64(1)},
        },
        expected={"ok": 1.0},
        msg="w as Int64 should succeed",
    ),
    CommandTestCase(
        id="wc_w_decimal128",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": Decimal128("1")},
        },
        expected={"ok": 1.0},
        msg="w as Decimal128 should succeed",
    ),
    CommandTestCase(
        id="wc_w_tagged_object",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": {"dc1": 1}},
        },
        expected={"ok": 1.0},
        msg="w as tagged object with numeric values should succeed",
    ),
]

# Property [WriteConcern j Acceptance]: j accepts bool, numeric types
# (truthiness), and null.
CREATE_WC_J_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="wc_j_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "j": True},
        },
        expected={"ok": 1.0},
        msg="j:true should succeed",
    ),
    CommandTestCase(
        id="wc_j_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "j": False},
        },
        expected={"ok": 1.0},
        msg="j:false should succeed",
    ),
    CommandTestCase(
        id="wc_j_int32",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "j": 42},
        },
        expected={"ok": 1.0},
        msg="j as int32 (numeric truthiness) should succeed",
    ),
    CommandTestCase(
        id="wc_j_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "j": Int64(1)},
        },
        expected={"ok": 1.0},
        msg="j as Int64 (numeric truthiness) should succeed",
    ),
    CommandTestCase(
        id="wc_j_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "j": 3.14},
        },
        expected={"ok": 1.0},
        msg="j as double (numeric truthiness) should succeed",
    ),
    CommandTestCase(
        id="wc_j_decimal128",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "j": Decimal128("1")},
        },
        expected={"ok": 1.0},
        msg="j as Decimal128 (numeric truthiness) should succeed",
    ),
    CommandTestCase(
        id="wc_j_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "j": None},
        },
        expected={"ok": 1.0},
        msg="j:null should succeed",
    ),
]

# Property [WriteConcern fsync Acceptance]: fsync accepts bool, numeric types
# (truthiness), and null.
CREATE_WC_FSYNC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="wc_fsync_true",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "fsync": True},
        },
        expected={"ok": 1.0},
        msg="fsync:true should succeed",
    ),
    CommandTestCase(
        id="wc_fsync_false",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "fsync": False},
        },
        expected={"ok": 1.0},
        msg="fsync:false should succeed",
    ),
    CommandTestCase(
        id="wc_fsync_int32",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "fsync": 42},
        },
        expected={"ok": 1.0},
        msg="fsync as int32 (numeric truthiness) should succeed",
    ),
    CommandTestCase(
        id="wc_fsync_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "fsync": Int64(1)},
        },
        expected={"ok": 1.0},
        msg="fsync as Int64 (numeric truthiness) should succeed",
    ),
    CommandTestCase(
        id="wc_fsync_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "fsync": 3.14},
        },
        expected={"ok": 1.0},
        msg="fsync as double (numeric truthiness) should succeed",
    ),
    CommandTestCase(
        id="wc_fsync_decimal128",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "fsync": Decimal128("1")},
        },
        expected={"ok": 1.0},
        msg="fsync as Decimal128 (numeric truthiness) should succeed",
    ),
    CommandTestCase(
        id="wc_fsync_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "fsync": None},
        },
        expected={"ok": 1.0},
        msg="fsync:null should succeed",
    ),
]

# Property [WriteConcern wtimeout Acceptance]: wtimeout accepts all BSON types.
CREATE_WC_WTIMEOUT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="wc_wtimeout_int",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": 5000},
        },
        expected={"ok": 1.0},
        msg="wtimeout as int should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": Int64(5000)},
        },
        expected={"ok": 1.0},
        msg="wtimeout as Int64 should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_double",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": 5000.0},
        },
        expected={"ok": 1.0},
        msg="wtimeout as double should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_decimal128",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": Decimal128("5000")},
        },
        expected={"ok": 1.0},
        msg="wtimeout as Decimal128 should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_code",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": Code("function(){}")},
        },
        expected={"ok": 1.0},
        msg="wtimeout as Code should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_code_with_scope",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": Code("function(){}", {"x": 1})},
        },
        expected={"ok": 1.0},
        msg="wtimeout as Code with scope should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_string",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": "hello"},
        },
        expected={"ok": 1.0},
        msg="wtimeout as string should succeed (all BSON types accepted)",
    ),
    CommandTestCase(
        id="wc_wtimeout_bool",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": True},
        },
        expected={"ok": 1.0},
        msg="wtimeout as bool should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_array",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": [1, 2]},
        },
        expected={"ok": 1.0},
        msg="wtimeout as array should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_object",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": {"a": 1}},
        },
        expected={"ok": 1.0},
        msg="wtimeout as object should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_null",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": None},
        },
        expected={"ok": 1.0},
        msg="wtimeout as null should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_objectid",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": ObjectId()},
        },
        expected={"ok": 1.0},
        msg="wtimeout as ObjectId should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_binary",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": Binary(b"x")},
        },
        expected={"ok": 1.0},
        msg="wtimeout as Binary should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_datetime",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {
                "w": 1,
                "wtimeout": datetime(2024, 1, 1, tzinfo=timezone.utc),
            },
        },
        expected={"ok": 1.0},
        msg="wtimeout as datetime should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_regex",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": Regex("x")},
        },
        expected={"ok": 1.0},
        msg="wtimeout as Regex should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_timestamp",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": Timestamp(1, 1)},
        },
        expected={"ok": 1.0},
        msg="wtimeout as Timestamp should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_minkey",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": MinKey()},
        },
        expected={"ok": 1.0},
        msg="wtimeout as MinKey should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_maxkey",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": MaxKey()},
        },
        expected={"ok": 1.0},
        msg="wtimeout as MaxKey should succeed",
    ),
    CommandTestCase(
        id="wc_wtimeout_at_int32_max",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wtimeout": INT32_MAX},
        },
        expected={"ok": 1.0},
        msg="wtimeout at INT32_MAX boundary should succeed",
    ),
]

# Property [WriteConcern provenance and Legacy Fields]: provenance accepts
# valid enum strings; getLastError, wElectionId, and wOpTime accept any type.
CREATE_WC_PROVENANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="wc_provenance_client_supplied",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "provenance": "clientSupplied"},
        },
        expected={"ok": 1.0},
        msg="provenance 'clientSupplied' should succeed",
    ),
    CommandTestCase(
        id="wc_provenance_custom_default",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "provenance": "customDefault"},
        },
        expected={"ok": 1.0},
        msg="provenance 'customDefault' should succeed",
    ),
    CommandTestCase(
        id="wc_provenance_implicit_default",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "provenance": "implicitDefault"},
        },
        expected={"ok": 1.0},
        msg="provenance 'implicitDefault' should succeed",
    ),
    CommandTestCase(
        id="wc_provenance_get_last_error_defaults",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "provenance": "getLastErrorDefaults"},
        },
        expected={"ok": 1.0},
        msg="provenance 'getLastErrorDefaults' should succeed",
    ),
    CommandTestCase(
        id="wc_get_last_error_any_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "getLastError": "anything"},
        },
        expected={"ok": 1.0},
        msg="getLastError accepts any type (ignored)",
    ),
    CommandTestCase(
        id="wc_w_election_id_any_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wElectionId": ObjectId()},
        },
        expected={"ok": 1.0},
        msg="wElectionId accepts any type (ignored)",
    ),
    CommandTestCase(
        id="wc_w_op_time_any_type",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "writeConcern": {"w": 1, "wOpTime": Timestamp(1, 1)},
        },
        expected={"ok": 1.0},
        msg="wOpTime accepts any type (ignored)",
    ),
]

CREATE_WRITE_CONCERN_SUCCESS_TESTS: list[CommandTestCase] = (
    CREATE_WC_DOCUMENT_AND_W_TESTS
    + CREATE_WC_J_TESTS
    + CREATE_WC_FSYNC_TESTS
    + CREATE_WC_WTIMEOUT_TESTS
    + CREATE_WC_PROVENANCE_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_WRITE_CONCERN_SUCCESS_TESTS))
def test_create_write_concern_acceptance(database_client, collection, test):
    """Test create command write concern acceptance behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
