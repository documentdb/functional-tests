"""Tests for $unwind stage — multi-document, nested arrays, and multi-stage chaining."""

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

# Property [Nested Arrays]: $unwind peels exactly one level of array nesting
# per invocation - inner arrays are preserved as elements, and successive
# $unwind stages on the same field flatten additional nesting levels.
UNWIND_NESTED_ARRAYS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nested_array_of_arrays",
        docs=[{"_id": 1, "a": [[1, 2], [3]]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 1, "a": [3]},
        ],
        msg="$unwind should produce one document per inner array",
    ),
    StageTestCase(
        "nested_deeply_nested",
        docs=[{"_id": 1, "a": [[[1]], [[2, 3]]]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": [[1]]},
            {"_id": 1, "a": [[2, 3]]},
        ],
        msg="$unwind should peel only one level, preserving deeper nesting",
    ),
    StageTestCase(
        "nested_mixed_scalars_and_arrays",
        docs=[{"_id": 1, "a": [1, [2, 3], 4]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": [2, 3]},
            {"_id": 1, "a": 4},
        ],
        msg="$unwind should preserve inner arrays alongside scalar elements",
    ),
    StageTestCase(
        "nested_successive_unwind_flattens",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[{"$unwind": {"path": "$a"}}, {"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 10},
            {"_id": 1, "a": 20},
            {"_id": 1, "a": 30},
        ],
        msg="Successive $unwind stages on the same field should flatten additional nesting",
    ),
]

# Property [Multi-Stage Unwind]: chaining multiple $unwind stages composes
# correctly with independent state tracking, cross-product semantics, and
# preserve interactions.
UNWIND_MULTI_STAGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "multi_stage_index_resets_per_subarray",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[
            {"$unwind": {"path": "$a", "includeArrayIndex": "i1"}},
            {"$unwind": {"path": "$a", "includeArrayIndex": "i2"}},
        ],
        expected=[
            {"_id": 1, "a": 10, "i1": INT64_ZERO, "i2": INT64_ZERO},
            {"_id": 1, "a": 20, "i1": INT64_ZERO, "i2": Int64(1)},
            {"_id": 1, "a": 30, "i1": Int64(1), "i2": INT64_ZERO},
        ],
        msg=(
            "Second $unwind includeArrayIndex should reset to 0 for each"
            " sub-array produced by the first $unwind"
        ),
    ),
    StageTestCase(
        "multi_stage_cross_product_different_fields",
        docs=[{"_id": 1, "a": [1, 2], "b": ["x", "y"]}],
        pipeline=[{"$unwind": {"path": "$a"}}, {"$unwind": {"path": "$b"}}],
        expected=[
            {"_id": 1, "a": 1, "b": "x"},
            {"_id": 1, "a": 1, "b": "y"},
            {"_id": 1, "a": 2, "b": "x"},
            {"_id": 1, "a": 2, "b": "y"},
        ],
        msg=(
            "Two $unwind stages on different array fields should produce"
            " a cross product of elements"
        ),
    ),
    StageTestCase(
        "multi_stage_preserve_first_filter_second",
        docs=[
            {"_id": 1, "a": [1, 2], "b": ["x"]},
            {"_id": 2, "a": [3], "b": None},
            {"_id": 3, "a": [4]},
            {"_id": 4, "a": None, "b": ["z"]},
        ],
        pipeline=[
            {"$unwind": {"path": "$a", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$b", "preserveNullAndEmptyArrays": False}},
        ],
        expected=[
            {"_id": 1, "a": 1, "b": "x"},
            {"_id": 1, "a": 2, "b": "x"},
            {"_id": 4, "a": None, "b": "z"},
        ],
        msg=(
            "preserveNullAndEmptyArrays on first $unwind followed by false"
            " on second should filter documents where second path is null or missing"
        ),
    ),
]

UNWIND_COMPLEX_TESTS = (
    UNWIND_MIXED_SHAPE_TESTS + UNWIND_NESTED_ARRAYS_TESTS + UNWIND_MULTI_STAGE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_COMPLEX_TESTS))
def test_unwind_complex(collection, test_case: StageTestCase):
    """Test $unwind multi-document, nested arrays, and multi-stage chaining."""
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
