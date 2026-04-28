"""
Tests for $expr edge cases and unusual expression forms.

Covers empty object/array as $expr argument, $or mixing regular query
and $expr, field path through array of objects, $not, and $$REMOVE behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

ALL_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="expr_empty_object",
        doc=[{"_id": 1}],
        filter={"$expr": {}},
        expected=[{"_id": 1}],
        msg="$expr with empty object {} — truthy, matches all",
    ),
    QueryTestCase(
        id="expr_empty_array",
        doc=[{"_id": 1}],
        filter={"$expr": []},
        expected=[{"_id": 1}],
        msg="$expr with empty array [] — truthy, matches all",
    ),
    QueryTestCase(
        id="or_regular_and_expr",
        doc=[
            {"_id": 1, "a": 1, "b": 5, "c": 3},
            {"_id": 2, "a": 2, "b": 1, "c": 5},
            {"_id": 3, "a": 3, "b": 1, "c": 1},
        ],
        filter={"$or": [{"a": 1}, {"$expr": {"$gt": ["$b", "$c"]}}]},
        expected=[{"_id": 1, "a": 1, "b": 5, "c": 3}],
        msg="$or mixing regular query and $expr",
    ),
    QueryTestCase(
        id="field_path_through_array",
        doc=[{"_id": 1, "items": [{"price": 50}, {"price": 150}]}],
        filter={"$expr": {"$in": [150, "$items.price"]}},
        expected=[{"_id": 1, "items": [{"price": 50}, {"price": 150}]}],
        msg="$expr with field path through array of objects",
    ),
    QueryTestCase(
        id="field_path_through_scalar_array",
        doc=[{"_id": 1, "a": [4, 5]}, {"_id": 2, "a": [1, 2, 3]}, {"_id": 3, "a": [1, 1]}],
        filter={"$expr": {"$gt": ["$a", [1, 2]]}},
        expected=[{"_id": 1, "a": [4, 5]}, {"_id": 2, "a": [1, 2, 3]}],
        msg="$expr compares scalar arrays element-by-element using BSON ordering",
    ),
    QueryTestCase(
        id="cond_with_remove",
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": -1}],
        filter={"$expr": {"$cond": [{"$gt": ["$a", 0]}, "$a", "$$REMOVE"]}},
        expected=[{"_id": 1, "a": 5}],
        msg="$expr with $$REMOVE in $cond false branch — falsy",
    ),
    QueryTestCase(
        id="not_inverts_expr",
        doc=[{"_id": 1, "a": 5}, {"_id": 2, "a": -1}],
        filter={"$expr": {"$not": {"$gt": ["$a", 0]}}},
        expected=[{"_id": 2, "a": -1}],
        msg="$expr with $not inverts comparison result",
    ),
    QueryTestCase(
        id="bare_remove_falsy",
        doc=[{"_id": 1}],
        filter={"$expr": "$$REMOVE"},
        expected=[],
        msg="$expr with bare $$REMOVE — falsy, no documents match",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_expr_complex(collection, test):
    """Test $expr edge cases and unusual expressions."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
