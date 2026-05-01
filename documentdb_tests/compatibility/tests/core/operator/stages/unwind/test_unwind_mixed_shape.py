"""Tests for $unwind stage — mixed-shape multi-document behavior."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Mixed-Shape Multi-Document]: when a collection contains documents
# with varying shapes for the unwind path (arrays, scalars, null, missing,
# empty arrays), $unwind processes each document independently — arrays are
# unwound, scalars pass through, and null/missing/empty are dropped or
# preserved per the preserveNullAndEmptyArrays setting.
UNWIND_MIXED_SHAPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "mixed_default_drops_null_missing_empty",
        docs=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": None},
            {"_id": 3},
            {"_id": 4, "a": []},
            {"_id": 5, "a": "scalar"},
            {"_id": 6, "a": [3]},
        ],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": 2},
            {"_id": 5, "a": "scalar"},
            {"_id": 6, "a": 3},
        ],
        msg=(
            "$unwind should unwind arrays, pass through scalars, and drop"
            " null/missing/empty across mixed-shape documents"
        ),
    ),
    StageTestCase(
        "mixed_preserve_true_keeps_all",
        docs=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 2, "a": None},
            {"_id": 3},
            {"_id": 4, "a": []},
            {"_id": 5, "a": "scalar"},
            {"_id": 6, "a": [3]},
        ],
        pipeline=[{"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": 2},
            {"_id": 2, "a": None},
            {"_id": 3},
            {"_id": 4},
            {"_id": 5, "a": "scalar"},
            {"_id": 6, "a": 3},
        ],
        msg=(
            "$unwind with preserve=true should unwind arrays, pass through"
            " scalars, and preserve null/missing/empty documents"
        ),
    ),
    StageTestCase(
        "mixed_with_index_default",
        docs=[
            {"_id": 1, "a": [10, 20]},
            {"_id": 2, "a": None},
            {"_id": 3},
            {"_id": 4, "a": []},
            {"_id": 5, "a": "scalar"},
            {"_id": 6, "a": [30]},
        ],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": 10, "idx": INT64_ZERO},
            {"_id": 1, "a": 20, "idx": Int64(1)},
            {"_id": 5, "a": "scalar", "idx": None},
            {"_id": 6, "a": 30, "idx": INT64_ZERO},
        ],
        msg=(
            "$unwind with includeArrayIndex should assign sequential indices"
            " to array elements, null index to scalars, and drop null/missing/empty"
        ),
    ),
    StageTestCase(
        "mixed_with_index_preserve_true",
        docs=[
            {"_id": 1, "a": [10, 20]},
            {"_id": 2, "a": None},
            {"_id": 3},
            {"_id": 4, "a": []},
            {"_id": 5, "a": "scalar"},
        ],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[
            {"_id": 1, "a": 10, "idx": INT64_ZERO},
            {"_id": 1, "a": 20, "idx": Int64(1)},
            {"_id": 2, "a": None, "idx": None},
            {"_id": 3, "idx": None},
            {"_id": 4, "idx": None},
            {"_id": 5, "a": "scalar", "idx": None},
        ],
        msg=(
            "$unwind with preserve=true and includeArrayIndex should assign"
            " sequential indices to arrays, null index to preserved and scalar documents"
        ),
    ),
    StageTestCase(
        "mixed_single_element_arrays",
        docs=[
            {"_id": 1, "a": [42]},
            {"_id": 2, "a": [99]},
            {"_id": 3, "a": "not_array"},
        ],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": 42, "idx": INT64_ZERO},
            {"_id": 2, "a": 99, "idx": INT64_ZERO},
            {"_id": 3, "a": "not_array", "idx": None},
        ],
        msg=(
            "$unwind should produce one document per single-element array"
            " with index 0, and null index for scalars"
        ),
    ),
    StageTestCase(
        "mixed_all_dropped_produces_empty",
        docs=[
            {"_id": 1, "a": None},
            {"_id": 2},
            {"_id": 3, "a": []},
        ],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[],
        msg=(
            "$unwind should produce empty result when all documents have"
            " null, missing, or empty array values"
        ),
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_MIXED_SHAPE_TESTS))
def test_unwind_mixed_shape(collection, test_case: StageTestCase):
    """Test $unwind mixed-shape multi-document behavior."""
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
    )
