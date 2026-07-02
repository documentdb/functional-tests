"""Tests for findAndModify with $expr in query and let variables."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

EXPR_LET_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "expr_comparison_selects_correct_doc",
        docs=[
            {"_id": 1, "a": 5, "b": 3},
            {"_id": 2, "a": 1, "b": 10},
        ],
        command={
            "query": {"$expr": {"$gt": ["$a", "$b"]}},
            "update": {"$set": {"matched": True}},
            "sort": {"_id": 1},
        },
        expected={"value": {"_id": Eq(1), "a": Eq(5), "b": Eq(3)}},
        msg="findAndModify query using $expr with $gt should select correct document",
    ),
    CommandTestCase(
        "expr_with_let_variable",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 20},
        ],
        command={
            "query": {"$expr": {"$eq": ["$a", "$$target"]}},
            "update": {"$set": {"found": True}},
            "let": {"target": 20},
        },
        expected={"value": {"_id": Eq(2), "a": Eq(20)}},
        msg="$expr referencing a let variable should select correct document",
    ),
    CommandTestCase(
        "let_variable_in_pipeline_update",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": [{"$set": {"y": "$$bonus"}}],
            "let": {"bonus": 100},
            "new": True,
        },
        expected={"value": {"_id": Eq(1), "x": Eq(10), "y": Eq(100)}},
        msg="findAndModify with let variable used in update pipeline should apply variable value",
    ),
    CommandTestCase(
        "expr_with_sort_composes_correctly",
        docs=[
            {"_id": 1, "a": 5, "b": 3},
            {"_id": 2, "a": 8, "b": 2},
            {"_id": 3, "a": 1, "b": 10},
        ],
        command={
            "query": {"$expr": {"$gt": ["$a", "$b"]}},
            "update": {"$set": {"matched": True}},
            "sort": {"_id": -1},
        },
        # Both _id:1 (a=5>b=3) and _id:2 (a=8>b=2) match; sort desc picks _id:2
        expected={"value": {"_id": Eq(2), "a": Eq(8), "b": Eq(2)}},
        msg="$expr filtering combined with descending sort picks highest _id among matches",
    ),
    CommandTestCase(
        "let_in_replacement_update",
        docs=[{"_id": 1, "a": 5}, {"_id": 2, "a": 10}],
        command={
            "query": {"$expr": {"$eq": ["$a", "$$val"]}},
            "update": {"a": 99, "replaced": True},
            "let": {"val": 10},
            "new": True,
        },
        expected={"value": {"_id": Eq(2), "a": Eq(99), "replaced": Eq(True)}},
        msg="let variable in $expr query with replacement update should select and replace",
    ),
    CommandTestCase(
        "expr_literal_true_matches_all",
        docs=[
            {"_id": 1, "a": 5, "b": 3},
            {"_id": 2, "a": 1, "b": 10},
            {"_id": 3, "a": -1, "b": 0},
        ],
        command={
            "query": {"$expr": True},
            "update": {"$set": {"touched": True}},
            "sort": {"_id": 1},
        },
        expected={"value": {"_id": Eq(1), "a": Eq(5), "b": Eq(3)}},
        msg="$expr with literal true should match all and return first by sort",
    ),
]

ALL_TESTS = EXPR_LET_SUCCESS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_findAndModify_expr_let(database_client, collection, test):
    """Test findAndModify $expr in query and let variables."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = {"findAndModify": collection.name, **test.build_command(ctx)}
    result = execute_command(collection, command)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
