"""Tests for $facet composing with other stages at different pipeline positions.

Per FOLDER_STRUCTURE.md, interactions between $facet and adjacent stages live
in the parent stages/ directory. Covers stages before $facet (which shape the
shared input), stages after $facet (which consume facet output arrays),
consecutive $facet stages, $facet as a middle stage, and preservation of
index-sorted input order into sub-pipelines.
"""

from __future__ import annotations

from typing import Any

import pytest
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [
    {"_id": 1, "cat": "A", "v": 30, "tags": ["x", "y"]},
    {"_id": 2, "cat": "A", "v": 10, "tags": ["y"]},
    {"_id": 3, "cat": "B", "v": 20, "tags": ["z"]},
]

# Property [Position Interactions]: $facet composes correctly with adjacent
# stages, preserves pre-sorted and pre-filtered input, and allows later stages
# to consume its output arrays.
FACET_POSITION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="first_stage_processes_all_documents",
        docs=DOCS,
        pipeline=[{"$facet": {"n": [{"$count": "n"}]}}],
        expected=[{"n": [{"n": 3}]}],
        msg="$facet as first stage should process all documents",
    ),
    StageTestCase(
        id="match_before_facet_filters_subpipelines",
        docs=DOCS,
        pipeline=[{"$match": {"cat": "A"}}, {"$facet": {"n": [{"$count": "n"}]}}],
        expected=[{"n": [{"n": 2}]}],
        msg="$match before $facet should filter input to all sub-pipelines",
    ),
    StageTestCase(
        id="sort_before_facet_preserves_order",
        docs=DOCS,
        pipeline=[
            {"$sort": {"v": 1}},
            {"$facet": {"docs": [{"$project": {"_id": 1}}]}},
        ],
        expected=[{"docs": [{"_id": 2}, {"_id": 3}, {"_id": 1}]}],
        msg="$sort before $facet should preserve document order into sub-pipelines",
    ),
    StageTestCase(
        id="limit_before_facet_reduces_input",
        docs=DOCS,
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$limit": 2},
            {"$facet": {"n": [{"$count": "n"}]}},
        ],
        expected=[{"n": [{"n": 2}]}],
        msg="$limit before $facet should reduce the input set",
    ),
    StageTestCase(
        id="skip_before_facet_removes_documents",
        docs=DOCS,
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$skip": 2},
            {"$facet": {"docs": [{"$project": {"_id": 1}}]}},
        ],
        expected=[{"docs": [{"_id": 3}]}],
        msg="$skip before $facet should remove skipped documents",
    ),
    StageTestCase(
        id="unwind_before_facet_expands_documents",
        docs=DOCS,
        pipeline=[
            {"$unwind": "$tags"},
            {"$facet": {"n": [{"$count": "n"}]}},
        ],
        expected=[{"n": [{"n": 4}]}],
        msg="$unwind before $facet should expand input documents",
    ),
    StageTestCase(
        id="group_before_facet_passes_grouped_documents",
        docs=DOCS,
        pipeline=[
            {"$group": {"_id": "$cat", "total": {"$sum": "$v"}}},
            {"$facet": {"grouped": [{"$sort": {"_id": 1}}]}},
        ],
        expected=[{"grouped": [{"_id": "A", "total": 40}, {"_id": "B", "total": 20}]}],
        msg="$group before $facet should pass grouped documents to sub-pipelines",
    ),
    StageTestCase(
        id="addfields_before_facet_visible_in_subpipelines",
        docs=DOCS,
        pipeline=[
            {"$addFields": {"doubled": {"$multiply": ["$v", 2]}}},
            {"$facet": {"docs": [{"$match": {"_id": 1}}, {"$project": {"_id": 1, "doubled": 1}}]}},
        ],
        expected=[{"docs": [{"_id": 1, "doubled": 60}]}],
        msg="Fields added before $facet should be visible in sub-pipelines",
    ),
    StageTestCase(
        id="project_before_facet_reduces_fields",
        docs=DOCS,
        pipeline=[
            {"$project": {"_id": 1, "cat": 1}},
            {"$facet": {"docs": [{"$match": {"_id": 1}}]}},
        ],
        expected=[{"docs": [{"_id": 1, "cat": "A"}]}],
        msg="$project before $facet should reduce fields seen by sub-pipelines",
    ),
    StageTestCase(
        id="replaceroot_before_facet_visible_in_subpipelines",
        docs=DOCS,
        pipeline=[
            {"$match": {"_id": 1}},
            {"$replaceRoot": {"newRoot": {"only": "$cat"}}},
            {"$facet": {"docs": [{"$project": {"_id": 0, "only": 1}}]}},
        ],
        expected=[{"docs": [{"only": "A"}]}],
        msg="$replaceRoot before $facet should be visible to sub-pipelines",
    ),
    StageTestCase(
        id="project_after_facet_references_output_arrays",
        docs=DOCS,
        pipeline=[
            {"$facet": {"a": [{"$match": {"cat": "A"}}], "b": [{"$match": {"cat": "B"}}]}},
            {"$project": {"a": 1}},
        ],
        expected=[
            {
                "a": [
                    {"_id": 1, "cat": "A", "v": 30, "tags": ["x", "y"]},
                    {"_id": 2, "cat": "A", "v": 10, "tags": ["y"]},
                ]
            }
        ],
        msg="$project after $facet should reference facet output arrays",
    ),
    StageTestCase(
        id="unwind_after_facet_deconstructs_output_array",
        docs=DOCS,
        pipeline=[
            {"$facet": {"a": [{"$match": {"cat": "A"}}, {"$sort": {"_id": 1}}]}},
            {"$unwind": "$a"},
            {"$project": {"_id": "$a._id"}},
        ],
        expected=[{"_id": 1}, {"_id": 2}],
        msg="$unwind after $facet should deconstruct the facet output array",
    ),
    StageTestCase(
        id="addfields_after_facet_derives_from_output",
        docs=DOCS,
        pipeline=[
            {"$facet": {"a": [{"$match": {"cat": "A"}}]}},
            {"$addFields": {"count": {"$size": "$a"}}},
            {"$project": {"count": 1}},
        ],
        expected=[{"count": 2}],
        msg="$addFields after $facet should derive fields from output arrays",
    ),
    StageTestCase(
        id="consecutive_facet_stages",
        docs=DOCS,
        pipeline=[
            {"$facet": {"a": [{"$match": {"cat": "A"}}]}},
            {"$facet": {"outer": [{"$project": {"n": {"$size": "$a"}}}]}},
        ],
        expected=[{"outer": [{"n": 2}]}],
        msg="A second $facet should receive the first $facet's single output document",
    ),
    StageTestCase(
        id="facet_as_middle_stage",
        docs=DOCS,
        pipeline=[
            {"$match": {"cat": "A"}},
            {"$facet": {"a": [{"$sort": {"_id": 1}}]}},
            {"$project": {"first_id": {"$arrayElemAt": ["$a._id", 0]}}},
        ],
        expected=[{"first_id": 1}],
        msg="$facet as a middle stage should compose with surrounding stages",
    ),
    StageTestCase(
        id="indexed_sort_before_facet_preserves_order",
        docs=DOCS,
        indexes=[IndexModel([("v", 1)])],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$facet": {"docs": [{"$project": {"_id": 1}}]}},
        ],
        expected=[{"docs": [{"_id": 2}, {"_id": 3}, {"_id": 1}]}],
        msg="Index-sorted order should be preserved into $facet sub-pipelines",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(FACET_POSITION_TESTS))
def test_stages_position_facet(collection, test_case: StageTestCase):
    """Test $facet composing with stages at different pipeline positions."""
    coll = populate_collection(collection, test_case)
    command: dict[str, Any] = {
        "aggregate": coll.name,
        "pipeline": test_case.pipeline,
        "cursor": {},
    }
    command.update(test_case.extra_command_fields)
    result = execute_command(coll, command)
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=test_case.ignore_doc_order,
        ignore_order_in=test_case.ignore_order_in,
    )
