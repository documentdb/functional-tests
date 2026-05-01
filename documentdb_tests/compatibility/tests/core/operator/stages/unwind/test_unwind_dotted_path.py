"""Tests for $unwind stage — dotted path traversal."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

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


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_DOTTED_PATH_TESTS))
def test_unwind_dotted_path(collection, test_case: StageTestCase):
    """Test $unwind dotted path traversal."""
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
