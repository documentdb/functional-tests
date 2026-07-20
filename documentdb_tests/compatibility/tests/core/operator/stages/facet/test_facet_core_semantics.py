"""Aggregation $facet stage tests - core pipeline stage semantics.

Covers TEST_COVERAGE.md §15 (Pipeline Stage Coverage) core semantics for the
$facet stage: single/multiple sub-pipelines, sole-stage behavior, empty and
non-existent collections, empty sub-pipeline results, shared input snapshot,
single-output-document guarantee, always-array output fields, and case-sensitive
output field names.
"""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len

DOCS = [
    {"_id": 1, "category": "A", "price": 10},
    {"_id": 2, "category": "B", "price": 20},
    {"_id": 3, "category": "A", "price": 30},
]

# Property [Core Semantics]: $facet emits one output document, preserves
# sub-pipeline input independence, and produces one array per declared output
# field on empty, non-existent, and populated collections.
FACET_CORE_SEMANTICS_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="single_subpipeline",
        docs=DOCS,
        pipeline=[{"$facet": {"categoryA": [{"$match": {"category": "A"}}]}}],
        expected=[
            {
                "categoryA": [
                    {"_id": 1, "category": "A", "price": 10},
                    {"_id": 3, "category": "A", "price": 30},
                ]
            }
        ],
        msg="Single sub-pipeline should yield one document with one array field",
    ),
    StageTestCase(
        id="sole_stage",
        docs=DOCS,
        pipeline=[{"$facet": {"all": []}}],
        expected=[{"all": DOCS}],
        msg="$facet as the only stage should pass all docs through an empty sub-pipeline",
    ),
    StageTestCase(
        id="empty_collection",
        docs=[],
        pipeline=[
            {
                "$facet": {
                    "a": [{"$match": {"category": "A"}}],
                    "b": [{"$match": {"category": "B"}}],
                }
            }
        ],
        expected=[{"a": [], "b": []}],
        msg="Empty collection should yield one document with empty arrays per sub-pipeline",
    ),
    StageTestCase(
        id="nonexistent_collection",
        docs=None,
        pipeline=[
            {
                "$facet": {
                    "a": [{"$match": {"category": "A"}}],
                    "b": [{"$match": {"category": "B"}}],
                }
            }
        ],
        expected=[{"a": [], "b": []}],
        msg="Non-existent collection should yield one document with empty arrays per sub-pipeline",
    ),
    StageTestCase(
        id="no_matching_documents",
        docs=DOCS,
        pipeline=[{"$facet": {"none": [{"$match": {"category": "Z"}}]}}],
        expected=[{"none": []}],
        msg="A non-matching sub-pipeline should return an empty array field",
    ),
    StageTestCase(
        id="output_field_always_array",
        docs=DOCS,
        pipeline=[{"$facet": {"total": [{"$count": "n"}]}}],
        expected={"total": [Len(1), Eq([{"n": 3}])]},
        msg="Output field should be a one-element array, not a bare document",
    ),
    StageTestCase(
        id="output_field_names_case_sensitive",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "cat": [{"$match": {"category": "A"}}],
                    "Cat": [{"$match": {"category": "B"}}],
                }
            }
        ],
        expected=[
            {
                "cat": [
                    {"_id": 1, "category": "A", "price": 10},
                    {"_id": 3, "category": "A", "price": 30},
                ],
                "Cat": [{"_id": 2, "category": "B", "price": 20}],
            }
        ],
        msg="Output field names 'cat' and 'Cat' should be distinct (case-sensitive)",
    ),
    StageTestCase(
        id="skip_beyond_count_empty",
        docs=DOCS,
        pipeline=[{"$facet": {"a": [{"$skip": 100}]}}],
        expected=[{"a": []}],
        msg="$facet should yield an empty array when $skip exceeds the document count",
    ),
    StageTestCase(
        id="allowDiskUse_true_operates_normally",
        docs=DOCS,
        pipeline=[{"$facet": {"n": [{"$count": "n"}]}}],
        expected=[{"n": [{"n": 3}]}],
        extra_command_fields={"allowDiskUse": True},
        msg="$facet should operate normally when allowDiskUse:true is set",
    ),
    StageTestCase(
        id="allowDiskUse_false_operates_normally",
        docs=DOCS,
        pipeline=[{"$facet": {"n": [{"$count": "n"}]}}],
        expected=[{"n": [{"n": 3}]}],
        extra_command_fields={"allowDiskUse": False},
        msg="$facet should operate normally when allowDiskUse:false is set",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(FACET_CORE_SEMANTICS_TESTS))
def test_facet_core_semantics(collection, test_case: StageTestCase):
    """Test core semantic behaviours of the $facet stage."""
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
