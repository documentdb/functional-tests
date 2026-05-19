"""Tests for aggregate command view-specific option behavior."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import OPTION_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Collation View Acceptance]: compatible collation values are
# accepted when aggregating on views.
AGGREGATE_COLLATION_VIEW_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_collation_matching",
        target_collection=ViewCollection(
            options={"pipeline": [], "collation": {"locale": "en", "strength": 2}},
            suffix="_collated_view",
        ),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept matching explicit collation on a view with explicit collation",
    ),
    CommandTestCase(
        "view_collation_null",
        target_collection=ViewCollection(
            options={"pipeline": [], "collation": {"locale": "en", "strength": 2}},
            suffix="_collated_view",
        ),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": None,
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept null collation on a view with explicit collation",
    ),
    CommandTestCase(
        "view_collation_empty_doc",
        target_collection=ViewCollection(
            options={"pipeline": [], "collation": {"locale": "en", "strength": 2}},
            suffix="_collated_view",
        ),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {},
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept empty document collation on a view with explicit collation",
    ),
    CommandTestCase(
        "view_collation_omitted",
        target_collection=ViewCollection(
            options={"pipeline": [], "collation": {"locale": "en", "strength": 2}},
            suffix="_collated_view",
        ),
        docs=[],
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [], "cursor": {}},
        expected={"ok": Eq(1.0)},
        msg="aggregate should accept omitted collation on a view with explicit collation",
    ),
]

# Property [Collation View Rejection]: incompatible explicit collation on
# views is rejected.
AGGREGATE_COLLATION_VIEW_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_collation_different_locale",
        target_collection=ViewCollection(
            options={"pipeline": [], "collation": {"locale": "en", "strength": 2}},
            suffix="_collated_view",
        ),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "fr", "strength": 1},
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="aggregate should reject a different explicit collation on a collated view",
    ),
    CommandTestCase(
        "view_collation_different_strength",
        target_collection=ViewCollection(
            options={"pipeline": [], "collation": {"locale": "en", "strength": 2}},
            suffix="_collated_view",
        ),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="aggregate should reject collation with different strength on a collated view",
    ),
    CommandTestCase(
        "view_inherited_collation_any_explicit",
        target_collection=ViewCollection(options={"pipeline": []}, suffix="_inherited_view"),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="aggregate should reject any explicit collation on a view without own collation",
    ),
    CommandTestCase(
        "view_inherited_collation_different",
        target_collection=ViewCollection(options={"pipeline": []}, suffix="_inherited_view"),
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "collation": {"locale": "fr"},
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="aggregate should reject different collation on a view that inherits collation",
    ),
]

# Property [Hint View]: aggregate hint validates against source collection
# indexes when run on a view.
AGGREGATE_HINT_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "hint_view_valid_index",
        target_collection=ViewCollection(
            options={"pipeline": []},
            suffix="_hint_view",
        ),
        docs=[{"_id": 1, "x": 10}],
        indexes=[IndexModel([("x", 1)])],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "hint": "x_1",
        },
        expected={"ok": Eq(1.0)},
        msg="aggregate should validate hint against source collection indexes on a view",
    ),
]

AGGREGATE_VIEW_OPTIONS_TESTS = (
    AGGREGATE_COLLATION_VIEW_ACCEPTANCE_TESTS
    + AGGREGATE_COLLATION_VIEW_REJECTION_TESTS
    + AGGREGATE_HINT_VIEW_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_VIEW_OPTIONS_TESTS))
def test_aggregate_view_options(database_client, collection, test):
    """Test aggregate view-specific option behavior."""
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
