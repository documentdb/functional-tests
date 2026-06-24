"""Tests for applyOps rejected and unsupported parameters.

Validates that applyOps rejects prepare, partialTxn, count,
alwaysUpsert, and preCondition parameters.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.replication.utils.replication_test_case import (  # noqa: E501
    ReplicationTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    APPLYOPS_ALWAYS_UPSERT_NOT_SUPPORTED_ERROR,
    APPLYOPS_PRECONDITION_NOT_SUPPORTED_ERROR,
    BAD_VALUE_ERROR,
    PARTIAL_TRANSACTION_NOT_ALLOWED_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.requires(replication=True), pytest.mark.no_parallel]


# Property [Rejected Parameters]: prepare, partialTxn, and count fields are
# explicitly rejected by the applyOps command.
APPLYOPS_REJECTED_PARAM_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "rejected_prepare_true",
        command=lambda ctx: {"applyOps": [], "prepare": True},
        error_code=BAD_VALUE_ERROR,
        msg="applyOps should reject prepare: true",
    ),
    ReplicationTestCase(
        "rejected_prepare_false",
        command=lambda ctx: {"applyOps": [], "prepare": False},
        error_code=BAD_VALUE_ERROR,
        msg="applyOps should reject prepare: false",
    ),
    ReplicationTestCase(
        "rejected_partial_txn_true",
        command=lambda ctx: {"applyOps": [], "partialTxn": True},
        error_code=PARTIAL_TRANSACTION_NOT_ALLOWED_ERROR,
        msg="applyOps should reject partialTxn: true",
    ),
    ReplicationTestCase(
        "rejected_partial_txn_false",
        command=lambda ctx: {"applyOps": [], "partialTxn": False},
        error_code=PARTIAL_TRANSACTION_NOT_ALLOWED_ERROR,
        msg="applyOps should reject partialTxn: false",
    ),
    ReplicationTestCase(
        "rejected_count_true",
        command=lambda ctx: {"applyOps": [], "count": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="applyOps should reject count: true",
    ),
    ReplicationTestCase(
        "rejected_count_false",
        command=lambda ctx: {"applyOps": [], "count": False},
        error_code=TYPE_MISMATCH_ERROR,
        msg="applyOps should reject count: false",
    ),
]

# Property [alwaysUpsert Rejection]: alwaysUpsert is no longer supported.
# Boolean true triggers a specific error; non-bool types trigger TYPE_MISMATCH_ERROR.
APPLYOPS_ALWAYSUPSERT_ERROR_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "alwaysupsert_bool_true",
        command=lambda ctx: {"applyOps": [], "alwaysUpsert": True},
        error_code=APPLYOPS_ALWAYS_UPSERT_NOT_SUPPORTED_ERROR,
        msg="applyOps should reject alwaysUpsert: true (no longer supported)",
    ),
] + [
    ReplicationTestCase(
        f"alwaysupsert_{tid}",
        command=lambda ctx, v=val: {"applyOps": [], "alwaysUpsert": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"applyOps should reject alwaysUpsert: {tid} (wrong type)",
    )
    for tid, val in [
        ("int32_one", 1),
        ("int32_zero", 0),
        ("int64_one", Int64(1)),
        ("int64_zero", Int64(0)),
        ("double_one", 1.0),
        ("double_zero", 0.0),
        ("decimal128_one", Decimal128("1")),
        ("decimal128_zero", Decimal128("0")),
        ("string", "true"),
        ("array", []),
        ("object", {}),
    ]
]

# Property [preCondition Rejection]: applyOps rejects the preCondition option.
APPLYOPS_PRECONDITION_ERROR_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "precondition_rejected",
        docs=[{"_id": 0, "setup": True}],
        command=lambda ctx: {
            "applyOps": [{"op": "i", "ns": ctx.namespace, "o": {"_id": 1}}],
            "preCondition": [],
        },
        error_code=APPLYOPS_PRECONDITION_NOT_SUPPORTED_ERROR,
        msg="applyOps should reject preCondition (no longer supported)",
    ),
    ReplicationTestCase(
        "precondition_with_entries_rejected",
        docs=[{"_id": 1, "x": 10}],
        command=lambda ctx: {
            "applyOps": [
                {
                    "op": "u",
                    "ns": ctx.namespace,
                    "o": {"_id": 1, "x": 20},
                    "o2": {"_id": 1},
                }
            ],
            "preCondition": [
                {"ns": ctx.namespace, "q": {"_id": 1}, "res": {"x": 10}},
            ],
        },
        error_code=APPLYOPS_PRECONDITION_NOT_SUPPORTED_ERROR,
        msg="applyOps should reject preCondition with entries (no longer supported)",
    ),
]

APPLYOPS_ALL_REJECTED_TESTS: list[ReplicationTestCase] = (
    APPLYOPS_REJECTED_PARAM_TESTS
    + APPLYOPS_ALWAYSUPSERT_ERROR_TESTS
    + APPLYOPS_PRECONDITION_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(APPLYOPS_ALL_REJECTED_TESTS))
def test_applyOps_rejected_params(database_client, collection, test):
    """Test applyOps rejects unsupported parameters."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertFailureCode(result, test.error_code, msg=test.msg)
