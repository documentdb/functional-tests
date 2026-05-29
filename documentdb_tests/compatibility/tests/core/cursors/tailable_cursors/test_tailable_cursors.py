"""Tests for tailable cursor creation and error conditions on capped collections."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Ne
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    SiblingCollection,
    TargetCollection,
    TimeseriesCollection,
)
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Tailable Cursor Creation]: a tailable cursor on a capped collection
# remains open after exhausting available results.
TAILABLE_CREATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "creation_nonempty_cursor_open",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {"find": ctx.collection, "tailable": True, "batchSize": 100},
        expected={
            "cursor": {
                "id": Ne(INT64_ZERO),
                "firstBatch": Eq([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}]),
            },
        },
        msg="Tailable cursor on non-empty capped collection should stay open",
    ),
    CommandTestCase(
        "creation_nontailable_cursor_closed",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {"find": ctx.collection, "tailable": False, "batchSize": 100},
        expected={
            "cursor": {
                "id": Eq(INT64_ZERO),
                "firstBatch": Eq([{"_id": 1, "x": 1}, {"_id": 2, "x": 2}]),
            },
        },
        msg="Non-tailable cursor on non-empty capped collection should close",
    ),
    CommandTestCase(
        "creation_empty_dead_cursor",
        target_collection=CappedCollection(),
        docs=[],
        command=lambda ctx: {"find": ctx.collection, "tailable": True, "batchSize": 100},
        expected={"cursor": {"id": Eq(INT64_ZERO), "firstBatch": Eq([])}},
        msg="Tailable cursor on empty capped collection should produce a dead cursor",
    ),
    CommandTestCase(
        "creation_nomatch_filter_cursor_open",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "batchSize": 100,
            "filter": {"x": 999},
        },
        expected={"cursor": {"id": Ne(INT64_ZERO), "firstBatch": Eq([])}},
        msg="Tailable cursor with no-match filter on non-empty capped should stay open",
    ),
    CommandTestCase(
        "creation_false_same_as_omitted",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"find": ctx.collection, "tailable": False, "batchSize": 100},
        expected={
            "cursor": {
                "id": Eq(INT64_ZERO),
                "firstBatch": Eq([{"_id": 1, "x": 1}]),
            },
        },
        msg="tailable: false should behave identically to omitting the field",
    ),
]

# Property [Non-Capped and Special Collections]: tailable cursors require a capped
# collection.
TAILABLE_NONCAPPED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "noncapped_error",
        target_collection=TargetCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"find": ctx.collection, "tailable": True},
        error_code=BAD_VALUE_ERROR,
        msg="Tailable cursor on non-capped collection should produce an error",
    ),
    CommandTestCase(
        "view_error",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        siblings=[SiblingCollection(suffix="_view", view_on_source=True)],
        command=lambda ctx: {"find": f"{ctx.collection}_view", "tailable": True},
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="Tailable cursor on a view should produce a view error",
    ),
    CommandTestCase(
        "timeseries_error",
        target_collection=TimeseriesCollection(),
        command=lambda ctx: {"find": ctx.collection, "tailable": True},
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="Tailable cursor on a timeseries collection should produce an error",
    ),
    CommandTestCase(
        "nonexistent_dead_cursor",
        docs=None,
        command=lambda ctx: {"find": ctx.collection, "tailable": True},
        expected={"cursor": {"id": Eq(INT64_ZERO), "firstBatch": Eq([])}},
        msg="Tailable cursor on non-existent collection should produce dead cursor",
    ),
]

# Property [Sort Restrictions - Allowed]: tailable cursors only accept forward natural
# sort order.
TAILABLE_SORT_ALLOWED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_natural_forward",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "sort": {"$natural": 1},
        },
        expected={
            "cursor": {"id": Ne(INT64_ZERO), "firstBatch": Eq([{"_id": 1}])},
        },
        msg="sort: {$natural: 1} should be allowed with tailable",
    ),
    CommandTestCase(
        "sort_empty",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "sort": {},
        },
        expected={
            "cursor": {"id": Ne(INT64_ZERO), "firstBatch": Eq([{"_id": 1}])},
        },
        msg="sort: {} should be allowed with tailable",
    ),
]

# Property [Sort Restrictions - Rejected]: non-natural sorts are rejected with tailable.
TAILABLE_SORT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_natural_reverse_error",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "sort": {"$natural": -1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="sort: {$natural: -1} with tailable should produce an error",
    ),
    CommandTestCase(
        "sort_field_error",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "sort": {"x": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Non-$natural sort with tailable should produce an error",
    ),
    CommandTestCase(
        "sort_compound_natural_error",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "sort": {"$natural": 1, "x": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="Compound sort with $natural and tailable should produce an error",
    ),
]

# Property [Incompatible Options]: certain find options are incompatible with tailable.
TAILABLE_INCOMPATIBLE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "singlebatch_conflict",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "singleBatch": True,
        },
        error_code=BAD_VALUE_ERROR,
        msg="singleBatch: true with tailable: true should produce an error",
    ),
    CommandTestCase(
        "negative_limit",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "limit": -1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Negative limit with tailable should produce an error",
    ),
    CommandTestCase(
        "negative_skip",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "skip": -1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Negative skip with tailable should produce an error",
    ),
]

# Property [Compatible Find Options]: standard find options are accepted alongside
# tailable.
TAILABLE_COMPATIBLE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "compatible_mixed_options",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "filter": {"x": {"$gte": 1}},
            "projection": {"x": 1},
            "skip": 0,
            "limit": 10,
            "batchSize": 5,
            "allowDiskUse": True,
        },
        expected={"cursor": {"id": Ne(INT64_ZERO)}},
        msg="Compatible find options should be accepted with tailable cursors",
    ),
    CommandTestCase(
        "compatible_hint_index",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "hint": {"_id": 1},
        },
        expected={"cursor": {"id": Ne(INT64_ZERO)}},
        msg="hint: {_id: 1} should be accepted with tailable cursors",
    ),
    CommandTestCase(
        "compatible_hint_natural_reverse",
        target_collection=CappedCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "find": ctx.collection,
            "tailable": True,
            "hint": {"$natural": -1},
        },
        expected={"cursor": {"id": Ne(INT64_ZERO)}},
        msg="hint: {$natural: -1} should be accepted with tailable cursors (unlike sort)",
    ),
]

ALL_TESTS = (
    TAILABLE_CREATION_TESTS
    + TAILABLE_NONCAPPED_TESTS
    + TAILABLE_SORT_ALLOWED_TESTS
    + TAILABLE_SORT_ERROR_TESTS
    + TAILABLE_INCOMPATIBLE_TESTS
    + TAILABLE_COMPATIBLE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_tailable_cursors(database_client, collection, test: CommandTestCase):
    """Test tailable cursor creation and error conditions."""
    resolved = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(resolved)
    result = execute_command(resolved, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
