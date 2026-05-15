"""Tests for $lookup uncorrelated subquery and $documents in sub-pipeline."""

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

# Property [Uncorrelated Subquery]: when pipeline is specified without
# localField/foreignField and without let, the sub-pipeline runs
# independently of each input document and its result is placed in the as
# output array for every input document.
LOOKUP_UNCORRELATED_SUBQUERY_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "pipeline_runs_independently_of_input_documents",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "b"},
        ],
        foreign_docs=[
            {"_id": 10, "val": 1},
            {"_id": 11, "val": 2},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [{"$match": {"val": 1}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "x": "a",
                "joined": [{"_id": 10, "val": 1}],
            },
            {
                "_id": 2,
                "x": "b",
                "joined": [{"_id": 10, "val": 1}],
            },
        ],
        msg=(
            "$lookup with pipeline and no let should run the"
            " sub-pipeline independently and produce the same result"
            " for every input document"
        ),
    ),
    LookupTestCase(
        "empty_pipeline_returns_all_foreign_documents",
        docs=[{"_id": 1}],
        foreign_docs=[
            {"_id": 10, "val": "a"},
            {"_id": 11, "val": "b"},
            {"_id": 12, "val": "c"},
        ],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "pipeline": [],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [
                    {"_id": 10, "val": "a"},
                    {"_id": 11, "val": "b"},
                    {"_id": 12, "val": "c"},
                ],
            },
        ],
        msg=(
            "$lookup with an empty pipeline should return all"
            " documents from the foreign collection"
        ),
    ),
]

# Property [$documents in Sub-Pipeline]: $documents as the first
# sub-pipeline stage provides inline documents without requiring from.
LOOKUP_DOCUMENTS_IN_SUB_PIPELINE_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "documents_without_from",
        docs=[{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "pipeline": [
                        {"$documents": [{"x": 1}, {"x": 2}]},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "val": "a",
                "joined": [{"x": 1}, {"x": 2}],
            },
            {
                "_id": 2,
                "val": "b",
                "joined": [{"x": 1}, {"x": 2}],
            },
        ],
        msg=(
            "$lookup with $documents as the first pipeline stage"
            " should work without from being specified"
        ),
    ),
    LookupTestCase(
        "documents_with_local_and_foreign_field",
        docs=[{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "localField": "val",
                    "foreignField": "fval",
                    "pipeline": [
                        {
                            "$documents": [
                                {"fval": "a", "n": 10},
                                {"fval": "b", "n": 20},
                                {"fval": "c", "n": 30},
                            ]
                        },
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "val": "a",
                "joined": [{"fval": "a", "n": 10}],
            },
            {
                "_id": 2,
                "val": "b",
                "joined": [{"fval": "b", "n": 20}],
            },
        ],
        msg=(
            "$lookup with $documents combined with localField/foreignField"
            " should work as a concise correlated subquery against inline"
            " documents"
        ),
    ),
    LookupTestCase(
        "documents_with_let_variables",
        docs=[{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "let": {"local_val": "$val"},
                    "pipeline": [
                        {"$documents": [{"x": 1}, {"x": 2}]},
                        {"$addFields": {"from_outer": "$$local_val"}},
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "val": "a",
                "joined": [
                    {"x": 1, "from_outer": "a"},
                    {"x": 2, "from_outer": "a"},
                ],
            },
            {
                "_id": 2,
                "val": "b",
                "joined": [
                    {"x": 1, "from_outer": "b"},
                    {"x": 2, "from_outer": "b"},
                ],
            },
        ],
        msg="$lookup let variables should be accessible in a $documents-based sub-pipeline",
    ),
    LookupTestCase(
        "empty_documents_returns_empty_array",
        docs=[{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}],
        foreign_docs=None,
        pipeline=[
            {
                "$lookup": {
                    "pipeline": [{"$documents": []}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {"_id": 1, "val": "a", "joined": []},
            {"_id": 2, "val": "b", "joined": []},
        ],
        msg=(
            "$lookup with empty $documents should return an empty"
            " joined array for every input document"
        ),
    ),
]

LOOKUP_UNCORRELATED_SUBQUERY_ALL_TESTS: list[LookupTestCase] = (
    LOOKUP_UNCORRELATED_SUBQUERY_TESTS + LOOKUP_DOCUMENTS_IN_SUB_PIPELINE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_UNCORRELATED_SUBQUERY_ALL_TESTS))
def test_lookup_uncorrelated_subquery(collection, test_case: LookupTestCase):
    """Test $lookup uncorrelated subquery."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
