"""Tests for aggregate command unrecognized top-level fields."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNRECOGNIZED_COMMAND_FIELD_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Unrecognized Top-Level Fields]: unknown fields at the command
# level are rejected.
AGGREGATE_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_field_single",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "fakeField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject unknown top-level field",
    ),
    CommandTestCase(
        "unrecognized_field_case_sensitive",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "Cursor": {},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject wrong-case top-level field name",
    ),
    CommandTestCase(
        "unrecognized_field_pipeline_case",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "Pipeline": [],
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="aggregate should reject Pipeline as unknown field (case-sensitive)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_UNRECOGNIZED_FIELD_TESTS))
def test_aggregate_unrecognized_fields(database_client, collection, test):
    """Test aggregate unrecognized top-level field rejection."""
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
