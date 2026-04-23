"""
Tests for $expr field resolution, null handling, and missing field behavior.

Covers null vs missing distinction, null comparison ordering,
nested field paths, and composite array paths.
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
        id="null_eq_null",
        doc=[{"_id": 1, "a": None}],
        filter={"$expr": {"$eq": ["$a", None]}},
        expected=[{"_id": 1, "a": None}],
        msg="$expr {$eq: ['$a', null]} where a is null",
    ),
    QueryTestCase(
        id="missing_eq_null",
        doc=[{"_id": 1, "b": 1}],
        filter={"$expr": {"$eq": ["$a", None]}},
        expected=[],
        msg="$expr {$eq: ['$a', null]} where a is missing — missing != null in $expr",
    ),
    QueryTestCase(
        id="missing_field_gt",
        doc=[{"_id": 1, "b": 1}],
        filter={"$expr": {"$gt": ["$missing_field", 0]}},
        expected=[],
        msg="$expr {$gt: ['$missing', 0]} — missing resolves to null, null < 0",
    ),
    QueryTestCase(
        id="null_lt_number",
        doc=[{"_id": 1, "a": None}],
        filter={"$expr": {"$lt": ["$a", 0]}},
        expected=[{"_id": 1, "a": None}],
        msg="$expr {$lt: ['$a', 0]} where a is null — null < numbers in BSON",
    ),
    QueryTestCase(
        id="nested_dotted_field",
        doc=[{"_id": 1, "a": {"b": 10}}, {"_id": 2, "a": {"b": 1}}],
        filter={"$expr": {"$gt": ["$a.b", 5]}},
        expected=[{"_id": 1, "a": {"b": 10}}],
        msg="$expr with nested field path '$a.b'",
    ),
    QueryTestCase(
        id="deep_dotted_field",
        doc=[{"_id": 1, "a": {"b": {"c": 1}}}, {"_id": 2, "a": {"b": {"c": 0}}}],
        filter={"$expr": {"$eq": ["$a.b.c", 1]}},
        expected=[{"_id": 1, "a": {"b": {"c": 1}}}],
        msg="$expr with deep nested field path '$a.b.c'",
    ),
    QueryTestCase(
        id="nonexistent_dotted_field",
        doc=[{"_id": 1, "a": {"b": 1}}],
        filter={"$expr": {"$eq": ["$a.b.c", None]}},
        expected=[],
        msg="$expr with nonexistent nested field — missing != null in $expr",
    ),
    QueryTestCase(
        id="composite_array_path",
        doc=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        filter={"$expr": {"$eq": [{"$size": "$a.b"}, 2]}},
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg="$expr with composite array path '$a.b' on array of objects",
    ),
    QueryTestCase(
        id="dotted_field_explicit_null",
        doc=[{"_id": 1, "a": {"b": None}}, {"_id": 2, "a": {"b": 5}}, {"_id": 3, "a": {}}],
        filter={"$expr": {"$eq": ["$a.b", None]}},
        expected=[{"_id": 1, "a": {"b": None}}],
        msg="$expr with $eq comparing nested dotted field to null — only matches explicit null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_expr_field_resolution(collection, test):
    """Test $expr field resolution, null handling, and missing field behavior."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
