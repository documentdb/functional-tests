"""Tests for find command projection functionality."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
    PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
    PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Projection]: find inclusion/exclusion projections control which fields
# are returned, and invalid projections produce correct errors.
FIND_PROJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "inclusion",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        command=lambda ctx: {"find": ctx.collection, "projection": {"a": 1, "b": 1}},
        expected=[{"_id": 1, "a": 10, "b": 20}],
        msg="find should include only projected fields plus _id.",
    ),
    CommandTestCase(
        "inclusion_exclude_id",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        command=lambda ctx: {"find": ctx.collection, "projection": {"a": 1, "_id": 0}},
        expected=[{"a": 10}],
        msg="find should exclude _id when _id: 0 with inclusion.",
    ),
    CommandTestCase(
        "exclusion",
        docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        command=lambda ctx: {"find": ctx.collection, "projection": {"c": 0}},
        expected=[{"_id": 1, "a": 10, "b": 20}],
        msg="find should exclude specified fields in exclusion projection.",
    ),
    CommandTestCase(
        "mixed_inclusion_exclusion_error",
        docs=[],
        command=lambda ctx: {"find": ctx.collection, "projection": {"a": 1, "b": 0}},
        error_code=PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
        msg="find should reject mixed inclusion/exclusion projection.",
    ),
    CommandTestCase(
        "nested_field_inclusion",
        docs=[{"_id": 1, "obj": {"x": 10, "y": 20, "z": 30}}],
        command=lambda ctx: {"find": ctx.collection, "projection": {"obj.x": 1}},
        expected=[{"_id": 1, "obj": {"x": 10}}],
        msg="find should project nested field via dot notation.",
    ),
    CommandTestCase(
        "nested_field_exclusion",
        docs=[{"_id": 1, "obj": {"x": 10, "y": 20}}],
        command=lambda ctx: {"find": ctx.collection, "projection": {"obj.y": 0}},
        expected=[{"_id": 1, "obj": {"x": 10}}],
        msg="find should exclude nested field via dot notation.",
    ),
    CommandTestCase(
        "path_collision_parent_then_child",
        docs=[],
        command=lambda ctx: {"find": ctx.collection, "projection": {"a": 1, "a.b": 1}},
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="find should reject path collision (parent then child).",
    ),
    CommandTestCase(
        "path_collision_child_then_parent",
        docs=[],
        command=lambda ctx: {"find": ctx.collection, "projection": {"a.b": 1, "a": 1}},
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="find should reject path collision (child then parent).",
    ),
    CommandTestCase(
        "slice_positive",
        docs=[{"_id": 1, "arr": [10, 20, 30, 40, 50]}],
        command=lambda ctx: {"find": ctx.collection, "projection": {"arr": {"$slice": 2}}},
        expected=[{"_id": 1, "arr": [10, 20]}],
        msg="find should return first N elements with $slice positive.",
    ),
    CommandTestCase(
        "slice_negative",
        docs=[{"_id": 1, "arr": [10, 20, 30, 40, 50]}],
        command=lambda ctx: {"find": ctx.collection, "projection": {"arr": {"$slice": -2}}},
        expected=[{"_id": 1, "arr": [40, 50]}],
        msg="find should return last N elements with $slice negative.",
    ),
    CommandTestCase(
        "slice_skip_limit",
        docs=[{"_id": 1, "arr": [10, 20, 30, 40, 50]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"arr": {"$slice": [1, 2]}},
        },
        expected=[{"_id": 1, "arr": [20, 30]}],
        msg="find should apply [skip, limit] $slice form.",
    ),
    CommandTestCase(
        "elemmatch",
        docs=[{"_id": 1, "arr": [{"x": 1}, {"x": 2}, {"x": 3}]}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"arr": {"$elemMatch": {"x": {"$gte": 2}}}},
        },
        expected=[{"_id": 1, "arr": [{"x": 2}]}],
        msg="find should return first matching array element with $elemMatch.",
    ),
    CommandTestCase(
        "literal",
        docs=[{"_id": 1, "a": 10}],
        command=lambda ctx: {
            "find": ctx.collection,
            "projection": {"_id": 1, "val": {"$literal": 1}},
        },
        expected=[{"_id": 1, "val": 1}],
        msg="find should set field to literal value with $literal.",
    ),
    CommandTestCase(
        "filter_on_excluded_field",
        docs=[{"_id": 1, "a": 10, "b": 20}, {"_id": 2, "a": 30, "b": 40}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"b": 20},
            "projection": {"a": 1},
        },
        expected=[{"_id": 1, "a": 10}],
        msg="find should filter on fields not in projection.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_PROJECTION_TESTS))
def test_find_projection(database_client, collection, test):
    """Test find command projection behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
