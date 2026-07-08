"""Tests for $lookup correlated subquery — concise correlated syntax (additional cases).

Extends test_lookup_concise_correlated_subquery.py with additional concise
syntax cases: empty pipeline equivalence, no-match behavior, and array
localField matching. Basic equality+pipeline and let+equality combinations
are covered in the pre-existing file.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

LOOKUP_CONCISE_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "concise_empty_pipeline_same_as_simple_equality",
        docs=[{"_id": 1, "x": "val"}],
        foreign_docs=[
            {"_id": 10, "y": "val"},
            {"_id": 11, "y": "other"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "x",
                    "foreignField": "y",
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "x": "val",
                "joined": [{"_id": 10, "y": "val"}],
            }
        ],
        msg=(
            "$lookup concise syntax with empty pipeline should be"
            " equivalent to simple equality lookup"
        ),
    ),
    LookupTestCase(
        "concise_equality_no_match_pipeline_not_executed",
        docs=[{"_id": 1, "x": "no_match"}],
        foreign_docs=[
            {"_id": 10, "y": "val1"},
            {"_id": 11, "y": "val2"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "x",
                    "foreignField": "y",
                    "let": {"v": "$x"},
                    "pipeline": [{"$addFields": {"src": "$$v"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "x": "no_match",
                "joined": [],
            }
        ],
        msg=(
            "$lookup concise syntax with no equality matches should"
            " result in empty array (pipeline never runs on empty set)"
        ),
    ),
    LookupTestCase(
        "concise_localField_array_matches_scalar",
        docs=[{"_id": 1, "refs": [10, 20]}],
        foreign_docs=[
            {"_id": 10, "val": "a"},
            {"_id": 20, "val": "b"},
            {"_id": 30, "val": "c"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "refs",
                    "foreignField": "_id",
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "refs": [10, 20],
                "joined": [
                    {"_id": 10, "val": "a"},
                    {"_id": 20, "val": "b"},
                ],
            }
        ],
        msg=(
            "$lookup concise syntax with array localField should match"
            " each element against scalar foreignField"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CONCISE_TESTS))
def test_lookup_correlated_concise(collection, test_case: LookupTestCase):
    """Test $lookup concise correlated subquery syntax (localField/foreignField + pipeline)."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
