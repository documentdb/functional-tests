"""Tests for $unwind stage — core unwinding behavior."""

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

# Property [Core Unwinding]: each element of the array at the path produces a
# separate output document with the array field replaced by that element,
# retaining all other fields, in original array order, without deduplication.
UNWIND_CORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "core_basic_array",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": 2},
            {"_id": 1, "a": 3},
        ],
        msg="$unwind should produce one document per array element",
    ),
    StageTestCase(
        "core_retains_other_fields",
        docs=[{"_id": 1, "a": [10, 20], "x": "keep", "y": 99}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 10, "x": "keep", "y": 99},
            {"_id": 1, "a": 20, "x": "keep", "y": 99},
        ],
        msg="$unwind should retain all other fields from the input document",
    ),
    StageTestCase(
        "core_preserves_array_order",
        docs=[{"_id": 1, "a": ["c", "a", "b"]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": "c"},
            {"_id": 1, "a": "a"},
            {"_id": 1, "a": "b"},
        ],
        msg="$unwind should emit elements in their original array order",
    ),
    StageTestCase(
        "core_duplicates_not_deduplicated",
        docs=[{"_id": 1, "a": [5, 5, 5]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 5},
            {"_id": 1, "a": 5},
            {"_id": 1, "a": 5},
        ],
        msg="$unwind should produce one document per duplicate value without deduplication",
    ),
    StageTestCase(
        "core_mixed_type_array",
        docs=[{"_id": 1, "a": [1, "two", True, None, 3.5]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": "two"},
            {"_id": 1, "a": True},
            {"_id": 1, "a": None},
            {"_id": 1, "a": 3.5},
        ],
        msg="$unwind should preserve each element's type in a mixed-type array",
    ),
    StageTestCase(
        "core_shorthand_form",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$unwind": "$a"}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": 2},
            {"_id": 1, "a": 3},
        ],
        msg="$unwind shorthand string form should behave identically to document form",
    ),
]

UNWIND_CORE_ALL_TESTS = UNWIND_CORE_TESTS + [
    StageTestCase(
        "non_existent_collection",
        docs=None,
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[],
        msg="$unwind on non-existent collection should return empty result",
    ),
    StageTestCase(
        "empty_collection",
        docs=[],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[],
        msg="$unwind on empty collection should return empty result",
    ),
    StageTestCase(
        "non_existent_collection_with_options",
        docs=None,
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[],
        msg="$unwind with all options on non-existent collection should return empty result",
    ),
    StageTestCase(
        "other_arrays_not_unwound",
        docs=[{"_id": 1, "a": [1, 2], "b": ["x", "y"], "c": [[3]]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 1, "b": ["x", "y"], "c": [[3]]},
            {"_id": 1, "a": 2, "b": ["x", "y"], "c": [[3]]},
        ],
        msg="$unwind should not unwind other array fields in the document",
    ),
    # Property [Field Ordering]: document field order from the input is preserved
    # in output documents.
    StageTestCase(
        "field_ordering_preserved",
        docs=[{"_id": 1, "z": 99, "a": [10, 20], "m": "mid", "b": "end"}],
        pipeline=[
            {"$unwind": {"path": "$a"}},
            {"$limit": 1},
        ],
        expected=[{"_id": 1, "z": 99, "a": 10, "m": "mid", "b": "end"}],
        msg="$unwind should preserve input document field order in output",
    ),
    # Property [Large Arrays]: arrays with many elements produce the correct
    # number of output documents with sequential indices and no off-by-one errors.
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_CORE_ALL_TESTS))
def test_unwind_core(collection, test_case: StageTestCase):
    """Test $unwind core unwinding and shorthand equivalence."""
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


@pytest.mark.aggregate
def test_unwind_large_array_10k(collection):
    """Test $unwind produces correct output for a 10,000-element array."""
    collection.database.create_collection(collection.name)
    collection.insert_one({"_id": 1, "a": list(range(10_000))})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
            "cursor": {"batchSize": 10_000},
        },
    )
    expected = [{"_id": 1, "a": i, "idx": Int64(i)} for i in range(10_000)]
    assertResult(
        result,
        expected=expected,
        msg="$unwind should produce 10,000 output documents from a 10,000-element array",
    )
