"""Tests for startSession maxTimeMS type acceptance."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [maxTimeMS Type Acceptance]: maxTimeMS accepts numeric types in range [0, INT32_MAX].
STARTSESSION_MAXTIMEMS_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"maxtimems_accept_{tid}",
        command=lambda ctx, v=val: {"startSession": 1, "maxTimeMS": v},
        expected={"ok": Eq(1.0)},
        msg=f"startSession should accept {tid} as maxTimeMS value",
    )
    for tid, val in [
        ("int32_positive", 1000),
        ("int32_zero", 0),
        ("int64", Int64(1000)),
        ("int64_zero", Int64(0)),
        ("double_whole", 1000.0),
        ("decimal128", Decimal128("1000")),
        ("decimal128_zero", Decimal128("0")),
        ("null", None),
        ("int32_max", 2_147_483_647),
        ("int32_max_as_int64", Int64(2_147_483_647)),
        ("int32_max_as_double", 2_147_483_647.0),
        ("int32_max_as_decimal128", Decimal128("2147483647")),
    ]
]


@pytest.mark.parametrize("test", pytest_params(STARTSESSION_MAXTIMEMS_ACCEPTANCE_TESTS))
def test_startSession_maxtimems_acceptance(database_client, collection, test):
    """Test startSession maxTimeMS type acceptance."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=True,
    )
