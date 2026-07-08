"""Tests for $lookup concise correlated subquery — localField + foreignField + pipeline."""

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

# Property [Concise Correlated Subquery]: when localField, foreignField,
# and pipeline are all specified, the equality match is applied first and
# the pipeline runs on the matched subset.
LOOKUP_CONCISE_CORRELATED_SUBQUERY_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "equality_match_then_pipeline_filters",
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "b"},
            {"_id": 3, "lf": "c"},
        ],
        foreign_docs=[
            {"_id": 10, "ff": "a", "val": 1},
            {"_id": 11, "ff": "a", "val": 2},
            {"_id": 12, "ff": "b", "val": 3},
            {"_id": 13, "ff": "b", "val": 4},
            {"_id": 14, "ff": "c", "val": 5},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "pipeline": [{"$match": {"val": {"$gte": 2}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [{"_id": 11, "ff": "a", "val": 2}],
            },
            {
                "_id": 2,
                "lf": "b",
                "joined": [
                    {"_id": 12, "ff": "b", "val": 3},
                    {"_id": 13, "ff": "b", "val": 4},
                ],
            },
            {
                "_id": 3,
                "lf": "c",
                "joined": [{"_id": 14, "ff": "c", "val": 5}],
            },
        ],
        msg=(
            "$lookup with localField, foreignField, and pipeline should"
            " apply equality match first then run the pipeline on the"
            " matched subset"
        ),
    ),
    LookupTestCase(
        "let_combined_with_equality_and_pipeline",
        docs=[
            {"_id": 1, "lf": "a", "extra": "x"},
            {"_id": 2, "lf": "b", "extra": "y"},
        ],
        foreign_docs=[
            {"_id": 10, "ff": "a", "val": 1},
            {"_id": 11, "ff": "a", "val": 2},
            {"_id": 12, "ff": "b", "val": 3},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "lf",
                    "foreignField": "ff",
                    "let": {"local_extra": "$extra"},
                    "pipeline": [{"$addFields": {"from_local": "$$local_extra"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "extra": "x",
                "joined": [
                    {"_id": 10, "ff": "a", "val": 1, "from_local": "x"},
                    {"_id": 11, "ff": "a", "val": 2, "from_local": "x"},
                ],
            },
            {
                "_id": 2,
                "lf": "b",
                "extra": "y",
                "joined": [
                    {"_id": 12, "ff": "b", "val": 3, "from_local": "y"},
                ],
            },
        ],
        msg=(
            "$lookup should allow let combined with localField,"
            " foreignField, and pipeline for additional filtering"
        ),
    ),
    LookupTestCase(
        "null_local_and_foreign_field_with_pipeline_degrades_to_uncorrelated",
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "b"},
        ],
        foreign_docs=[
            {"_id": 10, "ff": "a"},
            {"_id": 11, "ff": "b"},
            {"_id": 12, "ff": "c"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": None,
                    "foreignField": None,
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [
                    {"_id": 10, "ff": "a"},
                    {"_id": 11, "ff": "b"},
                    {"_id": 12, "ff": "c"},
                ],
            },
            {
                "_id": 2,
                "lf": "b",
                "joined": [
                    {"_id": 10, "ff": "a"},
                    {"_id": 11, "ff": "b"},
                    {"_id": 12, "ff": "c"},
                ],
            },
        ],
        msg=(
            "$lookup with null localField and foreignField plus pipeline"
            " should degrade to an uncorrelated subquery returning all"
            " foreign documents"
        ),
    ),
    LookupTestCase(
        "empty_string_local_and_foreign_field_with_pipeline_degrades_to_uncorrelated",
        docs=[
            {"_id": 1, "lf": "a"},
            {"_id": 2, "lf": "b"},
        ],
        foreign_docs=[
            {"_id": 10, "ff": "a"},
            {"_id": 11, "ff": "b"},
            {"_id": 12, "ff": "c"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "localField": "",
                    "foreignField": "",
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "lf": "a",
                "joined": [
                    {"_id": 10, "ff": "a"},
                    {"_id": 11, "ff": "b"},
                    {"_id": 12, "ff": "c"},
                ],
            },
            {
                "_id": 2,
                "lf": "b",
                "joined": [
                    {"_id": 10, "ff": "a"},
                    {"_id": 11, "ff": "b"},
                    {"_id": 12, "ff": "c"},
                ],
            },
        ],
        msg=(
            "$lookup with empty string localField and foreignField plus"
            " pipeline should degrade to an uncorrelated subquery"
            " returning all foreign documents"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CONCISE_CORRELATED_SUBQUERY_TESTS))
def test_lookup_concise_correlated_subquery(collection, test_case: LookupTestCase):
    """Test $lookup concise correlated subquery."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
