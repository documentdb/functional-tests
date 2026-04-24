"""Tests for $match core matching behavior."""

from __future__ import annotations

import pytest
from bson.son import SON

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing Field Matching]: {field: null} matches both
# documents where the field is null-valued and documents where the field is
# missing entirely.
MATCH_NULL_MISSING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_matches_null_valued",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "a": "x"}],
        pipeline=[{"$match": {"a": None}}],
        expected=[{"_id": 1, "a": None}],
        msg="$match with {field: null} should match documents where the field is null",
    ),
    StageTestCase(
        "null_matches_missing_field",
        docs=[{"_id": 1, "a": "x"}, {"_id": 2}],
        pipeline=[{"$match": {"a": None}}],
        expected=[{"_id": 2}],
        msg="$match with {field: null} should match documents where the field is missing",
    ),
    StageTestCase(
        "null_matches_both_null_and_missing",
        docs=[
            {"_id": 1, "a": None},
            {"_id": 2, "a": "x"},
            {"_id": 3},
            {"_id": 4, "a": 0},
        ],
        pipeline=[{"$match": {"a": None}}],
        expected=[{"_id": 1, "a": None}, {"_id": 3}],
        msg="$match with {field: null} should match both null-valued and missing-field documents",
    ),
    StageTestCase(
        "null_excludes_falsy_values",
        docs=[
            {"_id": 1, "a": None},
            {"_id": 2, "a": 0},
            {"_id": 3, "a": False},
            {"_id": 4, "a": ""},
        ],
        pipeline=[{"$match": {"a": None}}],
        expected=[{"_id": 1, "a": None}],
        msg="$match with {field: null} should not match falsy non-null values",
    ),
]

# Property [Core Matching Behavior]: simple equality filtering, insertion
# order preservation, $comment transparency, and contradictory conditions
# returning empty results all work correctly.
MATCH_CORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "core_equality_single_match",
        docs=[
            {"_id": 1, "a": 10, "b": "x"},
            {"_id": 2, "a": 20, "b": "y"},
            {"_id": 3, "a": 10, "b": "z"},
        ],
        pipeline=[{"$match": {"a": 10}}],
        expected=[
            {"_id": 1, "a": 10, "b": "x"},
            {"_id": 3, "a": 10, "b": "z"},
        ],
        msg="$match should filter documents to those where the field equals the value",
    ),
    StageTestCase(
        "core_nonexistent_collection",
        docs=None,
        pipeline=[{"$match": {"a": 1}}],
        expected=[],
        msg="$match on a non-existent collection should return empty result",
    ),
    StageTestCase(
        "core_empty_collection",
        docs=[],
        pipeline=[{"$match": {"a": 1}}],
        expected=[],
        msg="$match on empty collection should return empty result",
    ),
]

# Property [Predicate Semantics]: $match correctly handles non-obvious
# predicate edge cases that could differ between compatible engines.
MATCH_PREDICATE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "predicate_comment_ignored",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 20},
            {"_id": 3, "a": 10},
        ],
        pipeline=[{"$match": {"a": 10, "$comment": "this is a comment"}}],
        expected=[{"_id": 1, "a": 10}, {"_id": 3, "a": 10}],
        msg="$match should ignore $comment in the predicate and filter normally",
    ),
    StageTestCase(
        "predicate_contradictory_empty",
        docs=[
            {"_id": 1, "a": 3},
            {"_id": 2, "a": 7},
            {"_id": 3, "a": 15},
        ],
        pipeline=[{"$match": {"a": {"$gt": 10, "$lt": 5}}}],
        expected=[],
        msg="$match with contradictory conditions should return empty result without error",
    ),
    StageTestCase(
        "predicate_dollar_string_literal",
        docs=[
            {"_id": 1, "a": "$notAFieldRef"},
            {"_id": 2, "a": "hello"},
        ],
        pipeline=[{"$match": {"a": "$notAFieldRef"}}],
        expected=[{"_id": 1, "a": "$notAFieldRef"}],
        msg="$match should treat $-prefixed strings as literal values, not field references",
    ),
    StageTestCase(
        "predicate_duplicate_field_last_wins_equality",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 20},
        ],
        pipeline=[{"$match": SON([("a", 10), ("a", 20)])}],
        expected=[{"_id": 2, "a": 20}],
        msg="$match with duplicate field names should use last-value-wins semantics",
    ),
    StageTestCase(
        "predicate_duplicate_field_last_wins_operator",
        docs=[
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 20},
        ],
        pipeline=[{"$match": SON([("a", {"$gt": 15}), ("a", {"$lt": 15})])}],
        expected=[{"_id": 1, "a": 10}],
        msg="$match with duplicate operator predicates should use last-value-wins, not AND",
    ),
    StageTestCase(
        "predicate_dot_notation",
        docs=[
            {"_id": 1, "a": {"b": 10}},
            {"_id": 2, "a": {"b": 20}},
        ],
        pipeline=[{"$match": {"a.b": 10}}],
        expected=[{"_id": 1, "a": {"b": 10}}],
        msg="$match should support dot notation to match nested fields",
    ),
    StageTestCase(
        "predicate_dot_notation_array_index",
        docs=[
            {"_id": 1, "a": [{"b": 10}, {"b": 20}]},
            {"_id": 2, "a": [{"b": 30}, {"b": 40}]},
            {"_id": 3, "a": {"0": {"b": 99}}},
        ],
        pipeline=[{"$match": {"a.0.b": 10}}],
        expected=[{"_id": 1, "a": [{"b": 10}, {"b": 20}]}],
        msg="$match with numeric dot path should resolve as array index",
    ),
    StageTestCase(
        "predicate_dot_notation_object_key",
        docs=[
            {"_id": 1, "a": [{"b": 10}, {"b": 20}]},
            {"_id": 2, "a": [{"b": 30}, {"b": 40}]},
            {"_id": 3, "a": {"0": {"b": 99}}},
        ],
        pipeline=[{"$match": {"a.0.b": 99}}],
        expected=[{"_id": 3, "a": {"0": {"b": 99}}}],
        msg="$match with numeric dot path should also match object keys",
    ),
    StageTestCase(
        "predicate_dot_notation_array_index_and_object_key",
        docs=[
            {"_id": 1, "a": [{"b": 10}, {"b": 20}]},
            {"_id": 2, "a": [{"b": 10}, {"b": 40}]},
            {"_id": 3, "a": {"0": {"b": 10}}},
        ],
        pipeline=[{"$match": {"a.0.b": 10}}],
        expected=[
            {"_id": 1, "a": [{"b": 10}, {"b": 20}]},
            {"_id": 2, "a": [{"b": 10}, {"b": 40}]},
            {"_id": 3, "a": {"0": {"b": 10}}},
        ],
        msg="$match with numeric dot path should match both array index and object key",
    ),
]

# Property [Empty Predicate]: {$match: {}} returns all documents, and an
# empty collection always returns an empty result.
MATCH_EMPTY_PREDICATE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_predicate_returns_all",
        docs=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        pipeline=[{"$match": {}}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}],
        msg="$match with empty predicate should return all documents",
    ),
    StageTestCase(
        "nonexistent_collection_empty_predicate",
        docs=None,
        pipeline=[{"$match": {}}],
        expected=[],
        msg="$match on a non-existent collection with empty predicate should return empty result",
    ),
    StageTestCase(
        "empty_collection_empty_predicate",
        docs=[],
        pipeline=[{"$match": {}}],
        expected=[],
        msg="$match on empty collection with empty predicate should return empty result",
    ),
]

# Property [Large Predicate]: $match handles predicates with many conditions
# without error.
MATCH_LARGE_PREDICATE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "large_many_field_conditions",
        docs=[
            {"_id": 1, **{f"f{i}": i for i in range(500)}},
            {"_id": 2, "f0": 0},
        ],
        pipeline=[{"$match": {f"f{i}": i for i in range(500)}}],
        expected=[{"_id": 1, **{f"f{i}": i for i in range(500)}}],
        msg="$match should handle a predicate with 500 field conditions",
    ),
    StageTestCase(
        "large_many_or_branches",
        docs=[
            {"_id": 1, "a": 0},
            {"_id": 2, "a": 499},
            {"_id": 3, "a": 999},
        ],
        pipeline=[{"$match": {"$or": [{"a": i} for i in range(500)]}}],
        expected=[{"_id": 1, "a": 0}, {"_id": 2, "a": 499}],
        msg="$match should handle an $or predicate with 500 branches",
    ),
]

MATCH_CORE_TESTS_ALL = (
    MATCH_NULL_MISSING_TESTS
    + MATCH_CORE_TESTS
    + MATCH_PREDICATE_TESTS
    + MATCH_EMPTY_PREDICATE_TESTS
    + MATCH_LARGE_PREDICATE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MATCH_CORE_TESTS_ALL))
def test_match_core_cases(collection, test_case: StageTestCase):
    """Test $match core matching behavior."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
