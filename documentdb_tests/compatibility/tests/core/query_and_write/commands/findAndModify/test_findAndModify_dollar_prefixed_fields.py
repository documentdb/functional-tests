"""Tests for findAndModify with nested dollar-prefixed field names."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

DOLLAR_PREFIXED_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "set_nested_dollar_field_succeeds",
        docs=[{"_id": 1, "a": {"$x": 1}}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"a.$x": 99}},
            "new": True,
        },
        expected={"value": {"_id": Eq(1), "a": Eq({"$x": 99})}},
        msg="$set on nested dollar-prefixed field should succeed",
    ),
    CommandTestCase(
        "inc_nested_dollar_field_succeeds",
        docs=[{"_id": 1, "a": {"$count": 5}}],
        command={
            "query": {"_id": 1},
            "update": {"$inc": {"a.$count": 1}},
            "new": True,
        },
        expected={"value": {"_id": Eq(1), "a": Eq({"$count": 6})}},
        msg="$inc on nested dollar-prefixed field should succeed",
    ),
    CommandTestCase(
        "mul_nested_dollar_field_succeeds",
        docs=[{"_id": 1, "a": {"$val": 5}}],
        command={
            "query": {"_id": 1},
            "update": {"$mul": {"a.$val": 2}},
            "new": True,
        },
        expected={"value": {"_id": Eq(1), "a": Eq({"$val": 10})}},
        msg="$mul on nested dollar-prefixed field should succeed",
    ),
    CommandTestCase(
        "max_nested_dollar_field_succeeds",
        docs=[{"_id": 1, "a": {"$val": 5}}],
        command={
            "query": {"_id": 1},
            "update": {"$max": {"a.$val": 10}},
            "new": True,
        },
        expected={"value": {"_id": Eq(1), "a": Eq({"$val": 10})}},
        msg="$max on nested dollar-prefixed field should succeed",
    ),
]

ALL_TESTS = DOLLAR_PREFIXED_SUCCESS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_findAndModify_dollar_prefixed_fields(database_client, collection, test):
    """Test findAndModify with dollar-prefixed and dotted field names."""
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
