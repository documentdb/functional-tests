"""Tests for applyOps operation entry validation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.replication.utils.replication_test_case import (  # noqa: E501
    ReplicationTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    ILLEGAL_OPERATION_ERROR,
    MISSING_FIELD_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
    NO_SUCH_KEY_ERROR,
    TYPE_MISMATCH_ERROR,
    UNKNOWN_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.requires(change_streams=True), pytest.mark.no_parallel]


# Property [Missing Required Fields]: applyOps rejects entries that omit
# required fields (op, ns, o).
APPLYOPS_MISSING_FIELD_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "missing_op",
        command=lambda ctx: {
            "applyOps": [{"ns": ctx.namespace, "o": {"_id": 1}}],
        },
        error_code=NO_SUCH_KEY_ERROR,
        msg="applyOps should reject entry without op field",
    ),
    ReplicationTestCase(
        "missing_ns",
        command=lambda ctx: {"applyOps": [{"op": "i", "o": {"_id": 1}}]},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="applyOps should reject entry without ns field",
    ),
    ReplicationTestCase(
        "missing_o",
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace}],
        },
        error_code=MISSING_FIELD_ERROR,
        msg="applyOps should reject entry without o field",
    ),
    ReplicationTestCase(
        "insert_empty_document_missing_id",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {}}],
        },
        error_code=NO_SUCH_KEY_ERROR,
        msg="applyOps should reject insert of document without _id",
    ),
]


# Property [Invalid Op Type]: applyOps rejects entries with invalid op values.
APPLYOPS_INVALID_OP_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "op_invalid_char",
        command=lambda ctx: {
            "applyOps": [{"op": "x", "ns": ctx.namespace, "o": {"_id": 1}}],
        },
        error_code=BAD_VALUE_ERROR,
        msg="applyOps should reject invalid op type",
    ),
    ReplicationTestCase(
        "op_empty_string",
        command=lambda ctx: {
            "applyOps": [{"op": "", "ns": ctx.namespace, "o": {"_id": 1}}],
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="applyOps should reject empty string op type",
    ),
    ReplicationTestCase(
        "op_non_string",
        command=lambda ctx: {
            "applyOps": [{"op": 123, "ns": ctx.namespace, "o": {"_id": 1}}],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="applyOps should reject non-string op type",
    ),
    ReplicationTestCase(
        "op_null",
        command=lambda ctx: {
            "applyOps": [{"op": None, "ns": ctx.namespace, "o": {"_id": 1}}],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="applyOps should reject null op type",
    ),
]


# Property [Invalid Namespace]: applyOps rejects entries with invalid ns values.
APPLYOPS_INVALID_NS_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "ns_empty_string",
        command=lambda ctx: {"applyOps": [{"op": "i", "ns": "", "o": {"_id": 1}}]},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="applyOps should reject empty string namespace",
    ),
    ReplicationTestCase(
        "ns_non_string",
        command=lambda ctx: {"applyOps": [{"op": "i", "ns": 123, "o": {"_id": 1}}]},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="applyOps should reject non-string namespace",
    ),
    ReplicationTestCase(
        "ns_null",
        command=lambda ctx: {"applyOps": [{"op": "i", "ns": None, "o": {"_id": 1}}]},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="applyOps should reject null namespace",
    ),
]


# Property [Invalid Array Entries]: applyOps rejects non-object entries in
# the operations array.
APPLYOPS_INVALID_ENTRY_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "entry_non_object_int",
        command=lambda ctx: {"applyOps": [1, 2, 3]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="applyOps should reject integer entries",
    ),
    ReplicationTestCase(
        "entry_non_object_string",
        command=lambda ctx: {"applyOps": ["insert"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="applyOps should reject string entries",
    ),
    ReplicationTestCase(
        "entry_null",
        command=lambda ctx: {"applyOps": [None]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="applyOps should reject null entry",
    ),
    ReplicationTestCase(
        "entry_empty_object",
        command=lambda ctx: {"applyOps": [{}]},
        error_code=NO_SUCH_KEY_ERROR,
        msg="applyOps should reject empty object entry",
    ),
]


# Property [Nonexistent Collection]: applyOps rejects insert/update operations
# targeting a namespace that does not exist.
APPLYOPS_NONEXISTENT_NS_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "insert_nonexistent_collection",
        docs=[],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "i",
                    "ns": f"{ctx.database}.{ctx.collection}_nonexistent",
                    "o": {"_id": 1, "x": 1},
                }
            ],
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="applyOps should reject insert into non-existent collection",
    ),
]

# Property [o2 Field Validation]: o2 (update query document) must contain
# _id and must match an existing document.
APPLYOPS_O2_FIELD_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "update_o2_unmatched_id",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "u",
                    "ns": ctx.namespace,
                    "o": {"_id": 999, "x": 2},
                    "o2": {"_id": 999},
                }
            ],
        },
        error_code=UNKNOWN_ERROR,
        msg="applyOps should reject update when o2._id does not match any document",
    ),
    ReplicationTestCase(
        "update_o2_missing_id",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "u",
                    "ns": ctx.namespace,
                    "o": {"_id": 1, "x": 99},
                    "o2": {},
                }
            ],
        },
        error_code=NO_SUCH_KEY_ERROR,
        msg="applyOps should reject update when o2 is missing _id",
    ),
]

APPLYOPS_ENTRY_VALIDATION_TESTS: list[ReplicationTestCase] = (
    APPLYOPS_MISSING_FIELD_TESTS
    + APPLYOPS_INVALID_OP_TESTS
    + APPLYOPS_INVALID_NS_TESTS
    + APPLYOPS_INVALID_ENTRY_TESTS
    + APPLYOPS_NONEXISTENT_NS_TESTS
    + APPLYOPS_O2_FIELD_TESTS
)


@pytest.mark.parametrize("test", pytest_params(APPLYOPS_ENTRY_VALIDATION_TESTS))
def test_applyOps_entry_validation(database_client, collection, test):
    """Test applyOps operation entry validation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    if test.use_admin:
        result = execute_admin_command(collection, test.build_command(ctx))
    else:
        result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
