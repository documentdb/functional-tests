"""Tests for $unwind stage — dotted path traversal and options."""

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

# Property [Dotted Path Traversal]: a dotted path traverses into nested
# documents to reach the array leaf and unwinds it normally, but does not
# traverse into array elements; numeric path components are treated as field
# names, not array indices; and when an intermediate component is a scalar,
# null, or missing, the path is treated as missing.
UNWIND_DOTTED_PATH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dotted_basic_nested_doc",
        docs=[{"_id": 1, "a": {"b": [1, 2, 3]}}],
        pipeline=[{"$unwind": {"path": "$a.b"}}],
        expected=[
            {"_id": 1, "a": {"b": 1}},
            {"_id": 1, "a": {"b": 2}},
            {"_id": 1, "a": {"b": 3}},
        ],
        msg="$unwind with dotted path should traverse nested doc and unwind the leaf array",
    ),
    StageTestCase(
        "dotted_deep_nested_doc",
        docs=[{"_id": 1, "a": {"b": {"c": [10, 20]}}}],
        pipeline=[{"$unwind": {"path": "$a.b.c"}}],
        expected=[
            {"_id": 1, "a": {"b": {"c": 10}}},
            {"_id": 1, "a": {"b": {"c": 20}}},
        ],
        msg="$unwind with deep dotted path should traverse multiple levels",
    ),
    StageTestCase(
        "dotted_preserves_sibling_fields",
        docs=[{"_id": 1, "a": {"b": [1, 2], "x": 99}}],
        pipeline=[{"$unwind": {"path": "$a.b"}}],
        expected=[
            {"_id": 1, "a": {"b": 1, "x": 99}},
            {"_id": 1, "a": {"b": 2, "x": 99}},
        ],
        msg="$unwind with dotted path should preserve sibling fields in nested doc",
    ),
    StageTestCase(
        "dotted_intermediate_array_no_preserve",
        docs=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        pipeline=[{"$unwind": {"path": "$a.b"}}],
        expected=[],
        msg=(
            "$unwind with dotted path should not traverse into array elements"
            " and should drop the document when preserve is false"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_array_preserve_true",
        docs=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg=(
            "$unwind with dotted path should preserve original value when"
            " intermediate is an array and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_numeric_component_as_field_name",
        docs=[{"_id": 1, "a": {"0": [10, 20]}}],
        pipeline=[{"$unwind": {"path": "$a.0"}}],
        expected=[
            {"_id": 1, "a": {"0": 10}},
            {"_id": 1, "a": {"0": 20}},
        ],
        msg="$unwind should treat numeric path components as field names, not array indices",
    ),
    StageTestCase(
        "dotted_numeric_component_array_parent_no_preserve",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[{"$unwind": {"path": "$a.0"}}],
        expected=[],
        msg=(
            "$unwind with numeric path component should not index into array"
            " and should drop when preserve is false"
        ),
    ),
    StageTestCase(
        "dotted_numeric_component_array_parent_preserve_true",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[{"$unwind": {"path": "$a.0", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": [[10, 20], [30]]}],
        msg=(
            "$unwind with numeric path component should preserve original"
            " value when parent is array and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_empty_array_leaf_preserve_true",
        docs=[{"_id": 1, "a": {"b": []}}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": {}}],
        msg=(
            "$unwind with dotted path and preserve=true should remove the"
            " leaf field from the nested object when the leaf is an empty array"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_scalar_no_preserve",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a.b"}}],
        expected=[],
        msg="$unwind with dotted path should treat path as missing when intermediate is a scalar",
    ),
    StageTestCase(
        "dotted_intermediate_scalar_preserve_true",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": 42}],
        msg=(
            "$unwind with dotted path should preserve document when"
            " intermediate is a scalar and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_null_no_preserve",
        docs=[{"_id": 1, "a": None}],
        pipeline=[{"$unwind": {"path": "$a.b"}}],
        expected=[],
        msg="$unwind with dotted path should treat path as missing when intermediate is null",
    ),
    StageTestCase(
        "dotted_intermediate_null_preserve_true",
        docs=[{"_id": 1, "a": None}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": None}],
        msg=(
            "$unwind with dotted path should preserve document when"
            " intermediate is null and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_missing_no_preserve",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a.b"}}],
        expected=[],
        msg=(
            "$unwind with dotted path should treat path as missing when"
            " intermediate field is missing"
        ),
    ),
    StageTestCase(
        "dotted_intermediate_missing_preserve_true",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "x": 10}],
        msg=(
            "$unwind with dotted path should preserve document when"
            " intermediate field is missing and preserve=true"
        ),
    ),
    StageTestCase(
        "dotted_null_leaf_preserve_true",
        docs=[{"_id": 1, "a": {"b": None}}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": {"b": None}}],
        msg=(
            "$unwind with dotted path and preserve=true should keep null"
            " leaf value in the nested object"
        ),
    ),
    StageTestCase(
        "dotted_missing_leaf_preserve_true",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$unwind": {"path": "$a.b", "preserveNullAndEmptyArrays": True}}],
        expected=[{"_id": 1, "a": {"x": 1}}],
        msg=(
            "$unwind with dotted path and preserve=true should preserve"
            " document when leaf field is missing from nested object"
        ),
    ),
    StageTestCase(
        "dotted_path_depth_200_succeeds",
        docs=[],
        pipeline=[{"$unwind": {"path": "$" + ".".join(["a"] * 200)}}],
        expected=[],
        msg="$unwind should accept a path with exactly 200 components",
    ),
]

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

UNWIND_DOTTED_PATH_ALL_TESTS = (
    UNWIND_DOTTED_PATH_TESTS
    + UNWIND_DOTTED_PATH_INDEX_TESTS
    + UNWIND_DOTTED_PATH_PRESERVE_INDEX_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_DOTTED_PATH_ALL_TESTS))
def test_unwind_dotted_path(collection, test_case: StageTestCase):
    """Test $unwind dotted path traversal and options."""
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
