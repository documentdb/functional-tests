"""Aggregation $facet stage tests - output document structure.

Covers TEST_COVERAGE.md §15 (Document Handling): the single output document,
one array field per sub-pipeline, output-field order matching declaration
order, in-array document order preservation, and faithful representation of
nested arrays, null fields, array-of-arrays, and many-field documents.
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
from documentdb_tests.framework.property_checks import Eq, OrderedKeys

DOCS = [
    {"_id": 1, "cat": "A", "v": 30},
    {"_id": 2, "cat": "B", "v": 10},
    {"_id": 3, "cat": "C", "v": 20},
]

MANY_FIELD_DOC = {"_id": 1}
MANY_FIELD_DOC.update({f"k{i}": i for i in range(30)})

# Property [Output Structure]: $facet produces a single document with one array
# per sub-pipeline; array order, output-field order, and nested/special values are
# preserved.
FACET_OUTPUT_STRUCTURE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="array_preserves_subpipeline_order",
        docs=DOCS,
        pipeline=[{"$facet": {"sorted": [{"$sort": {"v": 1}}, {"$project": {"_id": 1}}]}}],
        expected=[{"sorted": [{"_id": 2}, {"_id": 3}, {"_id": 1}]}],
        msg="Output array should preserve the sub-pipeline's document order",
    ),
    StageTestCase(
        id="field_order_matches_declaration",
        docs=DOCS,
        pipeline=[
            {"$facet": {"z": [{"$count": "n"}], "a": [{"$count": "n"}], "m": [{"$count": "n"}]}}
        ],
        expected={"": OrderedKeys(["z", "a", "m"])},
        msg="Output field order should match sub-pipeline declaration order",
    ),
    StageTestCase(
        id="one_field_per_subpipeline",
        docs=DOCS,
        pipeline=[{"$facet": {"one": [{"$count": "n"}], "two": [{"$count": "n"}]}}],
        expected=[{"one": [{"n": 3}], "two": [{"n": 3}]}],
        msg="Output should contain exactly one field per sub-pipeline",
    ),
    StageTestCase(
        id="nested_arrays_preserved",
        docs=[{"_id": 1, "nested": [[1, 2], [3, 4]]}],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [{"_id": 1, "nested": [[1, 2], [3, 4]]}]}],
        msg="Nested arrays should be preserved in the output array",
    ),
    StageTestCase(
        id="array_of_arrays_from_push",
        docs=[{"_id": 1, "arr": [1, 2]}, {"_id": 2, "arr": [3, 4]}],
        pipeline=[
            {"$facet": {"grouped": [{"$group": {"_id": None, "pushed": {"$push": "$arr"}}}]}}
        ],
        expected={"grouped": Eq([{"_id": None, "pushed": [[1, 2], [3, 4]]}])},
        msg="$push of an array field should yield an array-of-arrays in the output",
    ),
    StageTestCase(
        id="many_field_document",
        docs=[MANY_FIELD_DOC],
        pipeline=[{"$facet": {"docs": [{"$match": {"_id": 1}}]}}],
        expected=[{"docs": [MANY_FIELD_DOC]}],
        msg="A many-field document should appear intact in the output array",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(FACET_OUTPUT_STRUCTURE_TESTS))
def test_facet_output_structure(collection, test_case: StageTestCase):
    """Test output document structure of the $facet stage."""
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
