from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.set.utils.set_common import (
    STAGE_NAMES,
    replace_stage_name,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Same-Stage Field References]: field references within a single
# $set stage resolve against the original input document, not against fields
# being set in the same stage.
SET_SAME_STAGE_REF_TESTS: list[StageTestCase] = [
    StageTestCase(
        "same_stage_ref_swap",
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$set": {"a": "$b", "b": "$a"}}],
        expected=[{"_id": 1, "a": 20, "b": 10}],
        msg=(
            "$set should swap field values because both references"
            " resolve against the original document"
        ),
    ),
    StageTestCase(
        "same_stage_ref_forward_existing",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"a": 99, "b": "$a"}}],
        expected=[{"_id": 1, "a": 99, "b": 1}],
        msg=(
            "$set should resolve a forward reference to a field being"
            " overwritten against the original value"
        ),
    ),
    StageTestCase(
        "same_stage_ref_forward_new_field",
        docs=[{"_id": 1, "x": 5}],
        pipeline=[{"$set": {"a": 100, "b": "$a"}}],
        expected=[{"_id": 1, "x": 5, "a": 100}],
        msg=(
            "$set should omit a field when it references a field being"
            " added in the same stage that did not exist on the original document"
        ),
    ),
]

# Property [Dot Notation]: dot-separated field paths in $set traverse or create
# nested document structure, and descend into arrays to apply to each element.
SET_DOT_NOTATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "dot_creates_nested",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a.b.c": 1}}],
        expected=[{"_id": 1, "a": {"b": {"c": 1}}}],
        msg="$set should create nested structure when intermediate path does not exist",
    ),
    StageTestCase(
        "dot_adds_to_existing_embedded",
        docs=[{"_id": 1, "a": {"x": 10}}],
        pipeline=[{"$set": {"a.y": 20}}],
        expected=[{"_id": 1, "a": {"x": 10, "y": 20}}],
        msg="$set should add a field to an existing embedded document preserving siblings",
    ),
    StageTestCase(
        "dot_overwrites_existing_nested",
        docs=[{"_id": 1, "a": {"x": 10, "y": 20}}],
        pipeline=[{"$set": {"a.x": 99}}],
        expected=[{"_id": 1, "a": {"x": 99, "y": 20}}],
        msg="$set should overwrite an existing nested field via dot notation",
    ),
    StageTestCase(
        "dot_traverses_array",
        docs=[{"_id": 1, "arr": [{"x": 1}, {"x": 2}]}],
        pipeline=[{"$set": {"arr.y": 99}}],
        expected=[{"_id": 1, "arr": [{"x": 1, "y": 99}, {"x": 2, "y": 99}]}],
        msg="$set should add the field to each object element when dot notation traverses an array",
    ),
    StageTestCase(
        "dot_array_scalar_replaced",
        docs=[{"_id": 1, "arr": [{"x": 1}, 42, "hello"]}],
        pipeline=[{"$set": {"arr.y": 99}}],
        expected=[{"_id": 1, "arr": [{"x": 1, "y": 99}, {"y": 99}, {"y": 99}]}],
        msg="$set should replace scalar array elements with an object containing the new field",
    ),
    StageTestCase(
        "dot_nested_array_traversal",
        docs=[{"_id": 1, "a": [[{"x": 1}], [{"x": 2}]]}],
        pipeline=[{"$set": {"a.x": 99}}],
        expected=[{"_id": 1, "a": [[{"x": 99}], [{"x": 99}]]}],
        msg="$set should traverse into nested arrays recursively via dot notation",
    ),
    StageTestCase(
        "dot_through_scalar_parent",
        docs=[{"_id": 1, "x": 42}],
        pipeline=[{"$set": {"x.y": 10}}],
        expected=[{"_id": 1, "x": {"y": 10}}],
        msg=(
            "$set should replace a scalar parent with an object"
            " when dot notation traverses through it"
        ),
    ),
    StageTestCase(
        "dot_null_in_array",
        docs=[{"_id": 1, "arr": [{"x": 1}, None, {"x": 3}]}],
        pipeline=[{"$set": {"arr.y": 99}}],
        expected=[{"_id": 1, "arr": [{"x": 1, "y": 99}, {"y": 99}, {"x": 3, "y": 99}]}],
        msg="$set should convert a null element in an array to an object containing the new field",
    ),
    StageTestCase(
        "dot_numeric_path_as_field_name",
        docs=[{"_id": 1, "arr": [10, 20, 30]}],
        pipeline=[{"$set": {"arr.0": "val"}}],
        expected=[{"_id": 1, "arr": [{"0": "val"}, {"0": "val"}, {"0": "val"}]}],
        msg="$set should treat numeric path components as field names, not array indices",
    ),
    StageTestCase(
        "dot_deeply_nested",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"a.b.c.d": "deep"}}],
        expected=[{"_id": 1, "a": {"b": {"c": {"d": "deep"}}}}],
        msg="$set should handle deeply nested dot notation without error",
    ),
    StageTestCase(
        "dot_id_sub_document",
        docs=[{"_id": {"a": 1}, "x": 5}],
        pipeline=[{"$set": {"_id.sub": "hello"}}],
        expected=[{"_id": {"a": 1, "sub": "hello"}, "x": 5}],
        msg="$set should add a field to an _id sub-document via dot notation",
    ),
    StageTestCase(
        "dot_sibling_paths_same_depth",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$set": {"a.b": 2, "a.c": 3}}],
        expected=[{"_id": 1, "a": {"x": 1, "b": 2, "c": 3}}],
        msg="$set should accept sibling dot paths at the same depth and set both fields",
    ),
]

# Property [Embedded Object Values]: when a field is set to a non-empty object
# without $-prefixed keys, $set merges it recursively with the existing value
# rather than replacing it. An empty object or $literal-wrapped object replaces
# the existing value entirely.
SET_EMBEDDED_OBJECT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "embedded_merge_preserves_siblings",
        docs=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        pipeline=[{"$set": {"a": {"z": 3}}}],
        expected=[{"_id": 1, "a": {"x": 1, "y": 2, "z": 3}}],
        msg=(
            "$set should merge a non-empty embedded object with an"
            " existing nested document, preserving unmentioned fields"
        ),
    ),
    StageTestCase(
        "embedded_empty_replaces",
        docs=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        pipeline=[{"$set": {"a": {}}}],
        expected=[{"_id": 1, "a": {}}],
        msg="$set should replace the existing value entirely when set to an empty object",
    ),
    StageTestCase(
        "embedded_asymmetric_merge_and_replace",
        docs=[{"_id": 1, "a": {"x": 1, "y": 2}, "b": {"x": 1, "y": 2}}],
        pipeline=[{"$set": {"a": {"z": 3}, "b": {}}}],
        expected=[{"_id": 1, "a": {"x": 1, "y": 2, "z": 3}, "b": {}}],
        msg=(
            "$set should merge a non-empty object but replace with an"
            " empty object in the same specification"
        ),
    ),
    StageTestCase(
        "embedded_literal_replaces",
        docs=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        pipeline=[{"$set": {"a": {"$literal": {"z": 3}}}}],
        expected=[{"_id": 1, "a": {"z": 3}}],
        msg=(
            "$set should replace the existing value entirely when"
            " the object is wrapped in $literal"
        ),
    ),
    StageTestCase(
        "embedded_on_scalar_replaces",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$set": {"a": {"z": 3}}}],
        expected=[{"_id": 1, "a": {"z": 3}}],
        msg="$set should replace a scalar field with an embedded object",
    ),
    StageTestCase(
        "embedded_on_array_traverses",
        docs=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}],
        pipeline=[{"$set": {"a": {"y": 99}}}],
        expected=[{"_id": 1, "a": [{"x": 1, "y": 99}, {"x": 2, "y": 99}]}],
        msg="$set should traverse an array and merge the embedded object into each element",
    ),
]

SET_PATH_TESTS = SET_SAME_STAGE_REF_TESTS + SET_DOT_NOTATION_TESTS + SET_EMBEDDED_OBJECT_TESTS


@pytest.mark.parametrize("stage_name", STAGE_NAMES)
@pytest.mark.parametrize("test_case", pytest_params(SET_PATH_TESTS))
def test_set_paths(collection, stage_name: str, test_case: StageTestCase):
    """Test $set / $addFields path traversal and embedded object cases."""
    populate_collection(collection, test_case)
    pipeline = replace_stage_name(test_case.pipeline, stage_name)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=f"{stage_name!r}: {test_case.msg!r}",
    )
