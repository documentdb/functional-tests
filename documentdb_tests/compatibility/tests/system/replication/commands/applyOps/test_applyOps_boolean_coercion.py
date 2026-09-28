"""Tests for applyOps boolean coercion of allowAtomic and alwaysUpsert.

Validates that allowAtomic accepts all BSON types (including null,
negative zero, NaN, Infinity) and that alwaysUpsert: false/null are
accepted (equivalent to default behavior).
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
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.requires(replication=True), pytest.mark.no_parallel]


# Property [allowAtomic Accepts All Types]: allowAtomic accepts any value
# without type rejection. All types are silently coerced or ignored.
ALLOWATOMIC_COERCION_SUCCESS_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        f"allowatomic_{tid}",
        command=lambda ctx, v=val: {"applyOps": [], "allowAtomic": v},
        expected={"ok": 1.0},
        msg=f"applyOps should accept allowAtomic: {tid}",
    )
    for tid, val in [
        ("bool_true", True),
        ("bool_false", False),
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
        ("null", None),
        ("neg_zero", -0.0),
        ("nan", float("nan")),
        ("infinity", float("inf")),
    ]
]

# Property [alwaysUpsert Accepted Values]: alwaysUpsert: false and null are
# accepted (equivalent to default behavior).
ALWAYSUPSERT_ACCEPTED_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "alwaysupsert_bool_false",
        command=lambda ctx: {"applyOps": [], "alwaysUpsert": False},
        expected={"ok": 1.0},
        msg="applyOps should accept alwaysUpsert: false (equivalent to default)",
    ),
    ReplicationTestCase(
        "alwaysupsert_null",
        command=lambda ctx: {"applyOps": [], "alwaysUpsert": None},
        expected={"ok": 1.0},
        msg="applyOps should accept alwaysUpsert: null (treated as omitted)",
    ),
]

APPLYOPS_COERCION_SUCCESS_TESTS: list[ReplicationTestCase] = (
    ALLOWATOMIC_COERCION_SUCCESS_TESTS + ALWAYSUPSERT_ACCEPTED_TESTS
)


@pytest.mark.parametrize("test", pytest_params(APPLYOPS_COERCION_SUCCESS_TESTS))
def test_applyOps_boolean_coercion(collection, test):
    """Test applyOps boolean coercion success cases."""
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertSuccessPartial(result, test.expected, msg=test.msg)
