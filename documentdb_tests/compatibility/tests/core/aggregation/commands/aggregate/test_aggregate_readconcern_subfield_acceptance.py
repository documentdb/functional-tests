"""Tests for aggregate command readConcern sub-field acceptance."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [readConcern Sub-field Acceptance]: provenance accepts its
# documented string values and null.
AGGREGATE_READCONCERN_SUBFIELD_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_subfield_provenance_client_supplied",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": "clientSupplied"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept provenance 'clientSupplied'",
    ),
    CommandTestCase(
        "rc_subfield_provenance_implicit_default",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": "implicitDefault"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept provenance 'implicitDefault'",
    ),
    CommandTestCase(
        "rc_subfield_provenance_custom_default",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": "customDefault"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept provenance 'customDefault'",
    ),
    CommandTestCase(
        "rc_subfield_provenance_get_last_error_defaults",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": "getLastErrorDefaults"},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept provenance 'getLastErrorDefaults'",
    ),
    CommandTestCase(
        "rc_subfield_provenance_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"provenance": None},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept null provenance",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_READCONCERN_SUBFIELD_ACCEPTANCE_TESTS))
def test_aggregate_readconcern_subfield_acceptance(database_client, collection, test):
    """Test aggregate readConcern sub-field acceptance."""
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
