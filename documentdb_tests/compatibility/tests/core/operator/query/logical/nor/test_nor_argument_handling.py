"""
Tests for $nor query operator argument handling.

Covers valid array argument variations: single expression, multiple expressions,
many expressions, empty object in array, and multiple fields in a single expression.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 1}]

VALID_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="single_expression",
        filter={"$nor": [{"a": 1}]},
        doc=DOCS,
        expected=[{"_id": 2, "a": 2, "b": 1}],
        msg="$nor with single expression should exclude matching docs",
    ),
    QueryTestCase(
        id="two_expressions",
        filter={"$nor": [{"a": 1}, {"b": 1}]},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 1}, {"_id": 3, "a": 2, "b": 2}],
        expected=[{"_id": 3, "a": 2, "b": 2}],
        msg="$nor with two expressions should return docs failing both",
    ),
    QueryTestCase(
        id="many_expressions",
        filter={"$nor": [{"a": 1}, {"b": 1}, {"a": 3}, {"b": 3}, {"a": 4}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2, "b": 2}],
        expected=[{"_id": 2, "a": 2, "b": 2}],
        msg="$nor with many expressions should return docs failing all",
    ),
    QueryTestCase(
        id="all_docs_match_at_least_one",
        filter={"$nor": [{"a": 1}, {"a": 2}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 1, "b": 2},
            {"_id": 3, "a": 2, "b": 1},
            {"_id": 4, "a": 2, "b": 2},
        ],
        expected=[],
        msg="$nor should return empty when all docs match at least one condition",
    ),
    QueryTestCase(
        id="no_docs_match_any",
        filter={"$nor": [{"a": 99}, {"b": 99}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 1, "b": 2},
            {"_id": 3, "a": 2, "b": 1},
            {"_id": 4, "a": 2, "b": 2},
        ],
        expected=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 1, "b": 2},
            {"_id": 3, "a": 2, "b": 1},
            {"_id": 4, "a": 2, "b": 2},
        ],
        msg="$nor should return all docs when none match any condition",
    ),
    QueryTestCase(
        id="duplicate_expressions",
        filter={"$nor": [{"a": 1}, {"a": 1}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 1, "b": 2},
            {"_id": 3, "a": 2, "b": 1},
            {"_id": 4, "a": 2, "b": 2},
        ],
        expected=[{"_id": 3, "a": 2, "b": 1}, {"_id": 4, "a": 2, "b": 2}],
        msg="$nor with duplicate expressions should behave same as single",
    ),
    QueryTestCase(
        id="empty_object_in_array",
        filter={"$nor": [{}]},
        doc=DOCS,
        expected=[],
        msg="$nor with empty object matches all docs so returns empty",
    ),
]

MULTIPLE_FIELDS_IN_EXPRESSION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="implicit_and_in_expression",
        filter={"$nor": [{"a": 1, "b": 2}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 1, "b": 2},
            {"_id": 3, "a": 2, "b": 1},
            {"_id": 4, "a": 2, "b": 2},
        ],
        expected=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 3, "a": 2, "b": 1},
            {"_id": 4, "a": 2, "b": 2},
        ],
        msg="$nor with multiple fields in one expression is implicit AND within",
    ),
    QueryTestCase(
        id="overlapping_field_conditions",
        filter={"$nor": [{"a": {"$gt": 5}}, {"a": {"$lt": 2}}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 3}, {"_id": 3, "a": 7}],
        expected=[{"_id": 2, "a": 3}],
        msg="$nor with overlapping conditions returns docs in the gap",
    ),
    QueryTestCase(
        id="conflicting_operators_same_field",
        filter={"$nor": [{"val": {"$gt": 10}}, {"val": {"$lt": 5}}, {"val": {"$eq": 7}}]},
        doc=[
            {"_id": 1, "val": 3},
            {"_id": 2, "val": 7},
            {"_id": 3, "val": 8},
            {"_id": 4, "val": 12},
        ],
        expected=[{"_id": 3, "val": 8}],
        msg="$nor with conflicting operators on same field returns docs failing all",
    ),
]

CLAUSE_BEHAVIOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="clause_ordering_invariance",
        filter={"$nor": [{"b": 1}, {"a": 1}]},
        doc=[{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 2, "b": 1}, {"_id": 3, "a": 2, "b": 2}],
        expected=[{"_id": 3, "a": 2, "b": 2}],
        msg="$nor with clauses in different order should produce identical results",
    ),
    QueryTestCase(
        id="combined_with_top_level_filter",
        filter={"x": 1, "$nor": [{"a": 1}, {"b": 2}]},
        doc=[
            {"_id": 1, "x": 1, "a": 1, "b": 1},
            {"_id": 2, "x": 1, "a": 2, "b": 1},
            {"_id": 3, "x": 2, "a": 2, "b": 1},
        ],
        expected=[{"_id": 2, "x": 1, "a": 2, "b": 1}],
        msg="$nor combined with top-level field filter applies implicit AND",
    ),
]

ALL_TESTS = VALID_ARRAY_TESTS + MULTIPLE_FIELDS_IN_EXPRESSION_TESTS + CLAUSE_BEHAVIOR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_argument_handling(collection, test):
    """Test $nor query operator argument validation."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
