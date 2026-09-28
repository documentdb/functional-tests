"""Aggregation $facet stage tests - collation wiring.

Per TEST_COVERAGE.md §19 (Foundational Spec Behaviors), collation semantics are
tested comprehensively under tests/core/collation/. These tests only verify
that $facet correctly wires the command-level collation into its sub-pipelines
(e.g. a case-insensitive $match and $sortByCount respect the collation).
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

CI = {"locale": "en", "strength": 2}  # case-insensitive collation
DOCS = [{"_id": 1, "cat": "a"}, {"_id": 2, "cat": "A"}, {"_id": 3, "cat": "b"}]

FACET_COLLATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="applies_to_subpipeline_match",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "ci": [{"$match": {"cat": "a"}}, {"$sort": {"_id": 1}}],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[{"ci": [{"_id": 1, "cat": "a"}, {"_id": 2, "cat": "A"}], "total": [{"n": 3}]}],
        extra_command_fields={"collation": CI},
        msg="Case-insensitive collation should apply to a $match in a sub-pipeline",
    ),
    StageTestCase(
        id="applies_to_subpipeline_sortByCount",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "byCat": [
                        {"$sortByCount": "$cat"},
                        {"$project": {"_id": 0, "count": 1}},
                        {"$sort": {"count": -1}},
                    ],
                    "total": [{"$count": "n"}],
                }
            }
        ],
        expected=[{"byCat": [{"count": 2}, {"count": 1}], "total": [{"n": 3}]}],
        extra_command_fields={"collation": CI},
        msg="Case-insensitive collation should merge 'a'/'A' in $sortByCount grouping",
    ),
]


@pytest.mark.aggregate
@pytest.mark.collation
@pytest.mark.parametrize("test_case", pytest_params(FACET_COLLATION_TESTS))
def test_facet_collation(collection, test_case: StageTestCase):
    """A command-level collation applies inside $facet sub-pipelines."""
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
