"""Tests for $unwind stage — dotted path with includeArrayIndex and preserveNullAndEmptyArrays."""

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

# Property [Dotted Path with includeArrayIndex]: when $unwind uses a dotted
# path, includeArrayIndex places the index field at the top level of the
# output document (not inside the nested structure), and indices are
# zero-based per input document.
UNWIND_DOTTED_PATH_INDEX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dotted_index_basic",
        docs=[{"_id": 1, "a": {"b": [10, 20, 30]}}],
        pipeline=[{"$unwind": {"path": "$a.b", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": {"b": 10}, "idx": INT64_ZERO},
            {"_id": 1, "a": {"b": 20}, "idx": Int64(1)},
            {"_id": 1, "a": {"b": 30}, "idx": Int64(2)},
        ],
        msg=(
            "$unwind with dotted path and includeArrayIndex should place"
            " the index at the top level"
        ),
    ),
    StageTestCase(
        "dotted_index_deep_path",
        docs=[{"_id": 1, "a": {"b": {"c": [10, 20]}}}],
        pipeline=[{"$unwind": {"path": "$a.b.c", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": {"b": {"c": 10}}, "idx": INT64_ZERO},
            {"_id": 1, "a": {"b": {"c": 20}}, "idx": Int64(1)},
        ],
        msg=(
            "$unwind with deep dotted path and includeArrayIndex should"
            " place the index at the top level"
        ),
    ),
    StageTestCase(
        "dotted_index_scalar_leaf",
        docs=[{"_id": 1, "a": {"b": 42}}],
        pipeline=[{"$unwind": {"path": "$a.b", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": {"b": 42}, "idx": None},
        ],
        msg=("$unwind with dotted path to scalar should pass through" " with null index"),
    ),
    StageTestCase(
        "dotted_index_preserves_siblings",
        docs=[{"_id": 1, "a": {"b": [1, 2], "x": 99}}],
        pipeline=[{"$unwind": {"path": "$a.b", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": {"b": 1, "x": 99}, "idx": INT64_ZERO},
            {"_id": 1, "a": {"b": 2, "x": 99}, "idx": Int64(1)},
        ],
        msg=(
            "$unwind with dotted path and includeArrayIndex should preserve"
            " sibling fields in the nested document"
        ),
    ),
    StageTestCase(
        "dotted_index_name_inside_nested_doc",
        docs=[{"_id": 1, "a": {"b": [10, 20]}}],
        pipeline=[{"$unwind": {"path": "$a.b", "includeArrayIndex": "a.idx"}}],
        expected=[
            {"_id": 1, "a": {"b": 10, "idx": INT64_ZERO}},
            {"_id": 1, "a": {"b": 20, "idx": Int64(1)}},
        ],
        msg=(
            "$unwind with dotted includeArrayIndex name should create the"
            " index inside the nested document"
        ),
    ),
]

# Property [Dotted Path with preserveNullAndEmptyArrays and includeArrayIndex]:
# when all three options are combined, preserved documents (null leaf, missing
# leaf, empty array leaf, intermediate null/missing/array) receive a null
# index at the top level.
UNWIND_DOTTED_PATH_PRESERVE_INDEX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dotted_preserve_index_null_leaf",
        docs=[{"_id": 1, "a": {"b": None}}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a.b",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "a": {"b": None}, "idx": None}],
        msg=(
            "$unwind with dotted path, preserve=true, and includeArrayIndex"
            " should emit null leaf with null index"
        ),
    ),
    StageTestCase(
        "dotted_preserve_index_missing_leaf",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a.b",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "a": {"x": 1}, "idx": None}],
        msg=(
            "$unwind with dotted path, preserve=true, and includeArrayIndex"
            " should emit missing leaf with null index"
        ),
    ),
    StageTestCase(
        "dotted_preserve_index_empty_array_leaf",
        docs=[{"_id": 1, "a": {"b": []}}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a.b",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "a": {}, "idx": None}],
        msg=(
            "$unwind with dotted path, preserve=true, and includeArrayIndex"
            " should emit empty array leaf with field removed and null index"
        ),
    ),
    StageTestCase(
        "dotted_preserve_index_intermediate_null",
        docs=[{"_id": 1, "a": None}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a.b",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "a": None, "idx": None}],
        msg=(
            "$unwind with dotted path, preserve=true, and includeArrayIndex"
            " should preserve document when intermediate is null with null index"
        ),
    ),
    StageTestCase(
        "dotted_preserve_index_intermediate_missing",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a.b",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "x": 10, "idx": None}],
        msg=(
            "$unwind with dotted path, preserve=true, and includeArrayIndex"
            " should preserve document when intermediate is missing with null index"
        ),
    ),
    StageTestCase(
        "dotted_preserve_index_intermediate_array",
        docs=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a.b",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}], "idx": None}],
        msg=(
            "$unwind with dotted path, preserve=true, and includeArrayIndex"
            " should preserve document when intermediate is array with null index"
        ),
    ),
]

UNWIND_DOTTED_PATH_OPTIONS_ALL_TESTS = (
    UNWIND_DOTTED_PATH_INDEX_TESTS + UNWIND_DOTTED_PATH_PRESERVE_INDEX_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_DOTTED_PATH_OPTIONS_ALL_TESTS))
def test_unwind_dotted_path_options(collection, test_case: StageTestCase):
    """Test $unwind dotted path with includeArrayIndex and preserveNullAndEmptyArrays."""
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
