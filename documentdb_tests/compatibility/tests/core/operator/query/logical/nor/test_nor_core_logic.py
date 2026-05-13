"""
Tests for $nor query operator core logic.

Covers basic NOR semantics: documents must fail ALL conditions to be returned,
implicit equality, multiple fields in single expression, and equivalence patterns.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

FOUR_DOCS = [
    {"_id": 1, "a": 1, "b": 1},
    {"_id": 2, "a": 1, "b": 2},
    {"_id": 3, "a": 2, "b": 1},
    {"_id": 4, "a": 2, "b": 2},
]

BASIC_NOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="fails_all_conditions",
        filter={"$nor": [{"a": 1}, {"b": 1}]},
        doc=FOUR_DOCS,
        expected=[{"_id": 4, "a": 2, "b": 2}],
        msg="$nor should return only docs that fail ALL conditions",
    ),
    QueryTestCase(
        id="single_condition_negation",
        filter={"$nor": [{"a": 1}]},
        doc=FOUR_DOCS,
        expected=[{"_id": 3, "a": 2, "b": 1}, {"_id": 4, "a": 2, "b": 2}],
        msg="$nor with single condition should negate it",
    ),
    QueryTestCase(
        id="all_docs_match_at_least_one",
        filter={"$nor": [{"a": 1}, {"a": 2}]},
        doc=FOUR_DOCS,
        expected=[],
        msg="$nor should return empty when all docs match at least one condition",
    ),
    QueryTestCase(
        id="no_docs_match_any",
        filter={"$nor": [{"a": 99}, {"b": 99}]},
        doc=FOUR_DOCS,
        expected=FOUR_DOCS,
        msg="$nor should return all docs when none match any condition",
    ),
    QueryTestCase(
        id="three_expressions",
        filter={"$nor": [{"a": 1}, {"b": 1}, {"a": 2, "b": 2}]},
        doc=FOUR_DOCS,
        expected=[],
        msg="$nor with three expressions — docs must fail ALL THREE",
    ),
    QueryTestCase(
        id="duplicate_expressions",
        filter={"$nor": [{"a": 1}, {"a": 1}]},
        doc=FOUR_DOCS,
        expected=[{"_id": 3, "a": 2, "b": 1}, {"_id": 4, "a": 2, "b": 2}],
        msg="$nor with duplicate expressions should behave same as single",
    ),
]

IMPLICIT_EQUALITY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="multiple_equalities_same_field",
        filter={"$nor": [{"a": 1}, {"a": 2}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        expected=[{"_id": 3, "a": 3}],
        msg="$nor with multiple equalities on same field excludes all matching values",
    ),
    QueryTestCase(
        id="equalities_different_fields",
        filter={"$nor": [{"a": 1}, {"b": 2}]},
        doc=[
            {"_id": 1, "a": 1, "b": 1},
            {"_id": 2, "a": 2, "b": 2},
            {"_id": 3, "a": 2, "b": 1},
        ],
        expected=[{"_id": 3, "a": 2, "b": 1}],
        msg="$nor with equalities on different fields returns docs failing both",
    ),
    QueryTestCase(
        id="includes_missing_field_docs",
        filter={"$nor": [{"a": 1}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "b": 1}],
        expected=[{"_id": 2, "a": 2}, {"_id": 3, "b": 1}],
        msg="$nor includes docs where referenced field does not exist",
    ),
]

MULTIPLE_FIELDS_IN_EXPRESSION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="implicit_and_in_expression",
        filter={"$nor": [{"a": 1, "b": 2}]},
        doc=FOUR_DOCS,
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

EQUIVALENCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nor_single_equivalent_to_ne",
        filter={"$nor": [{"a": 1}]},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 2, "a": 2}],
        msg="$nor with single equality is equivalent to $ne",
    ),
    QueryTestCase(
        id="ne_equivalent_to_nor_single",
        filter={"a": {"$ne": 1}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 2, "a": 2}],
        msg="$ne should produce same results as $nor with single equality",
    ),
]

ALL_TESTS = (
    BASIC_NOR_TESTS
    + IMPLICIT_EQUALITY_TESTS
    + MULTIPLE_FIELDS_IN_EXPRESSION_TESTS
    + EQUIVALENCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_core_logic(collection, test):
    """Test $nor query operator core NOR logic."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
