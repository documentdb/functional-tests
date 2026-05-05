"""Tests for $unwind stage — includeArrayIndex behavior and field name acceptance."""

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

# Property [includeArrayIndex Behavior]: when includeArrayIndex is specified,
# each output document includes a field with the given name containing the
# element's zero-based Int64 index, sequential per input document; non-array
# scalars and preserved documents (null, missing, empty array) receive a null
# index; null elements within an array receive a sequential index; and the
# index field is appended at the end of the document field order.
UNWIND_INCLUDE_ARRAY_INDEX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_zero_based_int64",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": 10, "idx": INT64_ZERO},
            {"_id": 1, "a": 20, "idx": Int64(1)},
            {"_id": 1, "a": 30, "idx": Int64(2)},
        ],
        msg="$unwind includeArrayIndex should produce zero-based Int64 indices",
    ),
    StageTestCase(
        "index_resets_per_document",
        docs=[{"_id": 1, "a": [10, 20]}, {"_id": 2, "a": [30]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": 10, "idx": INT64_ZERO},
            {"_id": 1, "a": 20, "idx": Int64(1)},
            {"_id": 2, "a": 30, "idx": INT64_ZERO},
        ],
        msg="$unwind includeArrayIndex should reset to 0 for each input document",
    ),
    StageTestCase(
        "index_scalar_is_null",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[{"_id": 1, "a": 42, "idx": None}],
        msg="$unwind includeArrayIndex should be null for non-array scalar values",
    ),
    StageTestCase(
        "index_preserved_null",
        docs=[{"_id": 1, "a": None}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "a": None, "idx": None}],
        msg="$unwind includeArrayIndex should be null for preserved null document",
    ),
    StageTestCase(
        "index_preserved_missing",
        docs=[{"_id": 1, "x": 10}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "x": 10, "idx": None}],
        msg="$unwind includeArrayIndex should be null for preserved missing document",
    ),
    StageTestCase(
        "index_preserved_empty_array",
        docs=[{"_id": 1, "a": []}],
        pipeline=[
            {
                "$unwind": {
                    "path": "$a",
                    "includeArrayIndex": "idx",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ],
        expected=[{"_id": 1, "idx": None}],
        msg="$unwind includeArrayIndex should be null for preserved empty array document",
    ),
    StageTestCase(
        "index_null_element_gets_sequential_index",
        docs=[{"_id": 1, "a": [10, None, 30]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "idx"}}],
        expected=[
            {"_id": 1, "a": 10, "idx": INT64_ZERO},
            {"_id": 1, "a": None, "idx": Int64(1)},
            {"_id": 1, "a": 30, "idx": Int64(2)},
        ],
        msg="$unwind includeArrayIndex should assign sequential index to null elements",
    ),
]

# Property [includeArrayIndex Field Name Collisions]: when includeArrayIndex
# names an existing field (_id, the unwound path, or a dotted path component),
# the index value overwrites the existing field; a dotted index name replaces
# a scalar parent with a nested document containing the index.
UNWIND_INDEX_FIELD_NAME_COLLISION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_collision_overwrites_id",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "_id"}}],
        expected=[
            {"_id": INT64_ZERO, "a": 10},
            {"_id": Int64(1), "a": 20},
        ],
        msg="$unwind includeArrayIndex should overwrite _id with the Int64 index",
    ),
    StageTestCase(
        "index_collision_overwrites_unwound_path",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a"}}],
        expected=[
            {"_id": 1, "a": INT64_ZERO},
            {"_id": 1, "a": Int64(1)},
        ],
        msg="$unwind includeArrayIndex should overwrite the unwound value with the index",
    ),
    StageTestCase(
        "index_collision_dotted_overwrites_nested_field",
        docs=[{"_id": 1, "a": [10, 20], "x": {"y": "old", "z": 99}}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "x.y"}}],
        expected=[
            {"_id": 1, "a": 10, "x": {"y": INT64_ZERO, "z": 99}},
            {"_id": 1, "a": 20, "x": {"y": Int64(1), "z": 99}},
        ],
        msg=(
            "$unwind includeArrayIndex dotted name should overwrite the"
            " nested field while preserving siblings"
        ),
    ),
    StageTestCase(
        "index_collision_dotted_replaces_scalar_parent",
        docs=[{"_id": 1, "a": [10, 20], "x": "scalar"}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "x.y"}}],
        expected=[
            {"_id": 1, "a": 10, "x": {"y": INT64_ZERO}},
            {"_id": 1, "a": 20, "x": {"y": Int64(1)}},
        ],
        msg=(
            "$unwind includeArrayIndex dotted name should replace a scalar"
            " parent with a nested document containing the index"
        ),
    ),
    StageTestCase(
        "index_collision_simple_name_overwrites_dotted_path_parent",
        docs=[{"_id": 1, "a": {"b": [10, 20]}}],
        pipeline=[{"$unwind": {"path": "$a.b", "includeArrayIndex": "a"}}],
        expected=[
            {"_id": 1, "a": INT64_ZERO},
            {"_id": 1, "a": Int64(1)},
        ],
        msg=(
            "$unwind includeArrayIndex simple name matching the parent of"
            " the dotted unwound path should overwrite the entire nested document"
        ),
    ),
]

# Property [includeArrayIndex Field Name Acceptance]: includeArrayIndex
# accepts arbitrary non-empty, non-dollar-prefixed field names regardless of
# character content, encoding, or length.
UNWIND_INDEX_FIELD_NAME_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_name_unicode_cjk",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "\u5b57\u6bb5"}}],
        expected=[
            {"_id": 1, "a": 10, "\u5b57\u6bb5": INT64_ZERO},
            {"_id": 1, "a": 20, "\u5b57\u6bb5": Int64(1)},
        ],
        msg="includeArrayIndex should accept CJK Unicode field name",
    ),
    StageTestCase(
        "index_name_emoji",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "\U0001f389"}}],
        expected=[
            {"_id": 1, "a": 10, "\U0001f389": INT64_ZERO},
            {"_id": 1, "a": 20, "\U0001f389": Int64(1)},
        ],
        msg="includeArrayIndex should accept emoji field name",
    ),
    StageTestCase(
        "index_name_space",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a b"}}],
        expected=[
            {"_id": 1, "a": 10, "a b": INT64_ZERO},
            {"_id": 1, "a": 20, "a b": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with spaces",
    ),
    StageTestCase(
        "index_name_tab",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\tb"}}],
        expected=[
            {"_id": 1, "a": 10, "a\tb": INT64_ZERO},
            {"_id": 1, "a": 20, "a\tb": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with tab",
    ),
    StageTestCase(
        "index_name_newline",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\nb"}}],
        expected=[
            {"_id": 1, "a": 10, "a\nb": INT64_ZERO},
            {"_id": 1, "a": 20, "a\nb": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with newline",
    ),
    StageTestCase(
        "index_name_nbsp",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\u00a0b"}}],
        expected=[
            {"_id": 1, "a": 10, "a\u00a0b": INT64_ZERO},
            {"_id": 1, "a": 20, "a\u00a0b": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with NBSP",
    ),
    StageTestCase(
        "index_name_zero_width_joiner",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\u200db"}}],
        expected=[
            {"_id": 1, "a": 10, "a\u200db": INT64_ZERO},
            {"_id": 1, "a": 20, "a\u200db": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with zero-width joiner",
    ),
    StageTestCase(
        "index_name_zero_width_space",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\u200bb"}}],
        expected=[
            {"_id": 1, "a": 10, "a\u200bb": INT64_ZERO},
            {"_id": 1, "a": 20, "a\u200bb": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with zero-width space",
    ),
    StageTestCase(
        "index_name_control_char",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a\x01b"}}],
        expected=[
            {"_id": 1, "a": 10, "a\x01b": INT64_ZERO},
            {"_id": 1, "a": 20, "a\x01b": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with control character",
    ),
    StageTestCase(
        "index_name_dunder_proto",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "__proto__"}}],
        expected=[
            {"_id": 1, "a": 10, "__proto__": INT64_ZERO},
            {"_id": 1, "a": 20, "__proto__": Int64(1)},
        ],
        msg="includeArrayIndex should accept __proto__ as field name",
    ),
    StageTestCase(
        "index_name_constructor",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "constructor"}}],
        expected=[
            {"_id": 1, "a": 10, "constructor": INT64_ZERO},
            {"_id": 1, "a": 20, "constructor": Int64(1)},
        ],
        msg="includeArrayIndex should accept constructor as field name",
    ),
    StageTestCase(
        "index_name_numeric_string",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "123"}}],
        expected=[
            {"_id": 1, "a": 10, "123": INT64_ZERO},
            {"_id": 1, "a": 20, "123": Int64(1)},
        ],
        msg="includeArrayIndex should accept numeric-looking string as field name",
    ),
    StageTestCase(
        "index_name_non_leading_dollar",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a$b"}}],
        expected=[
            {"_id": 1, "a": 10, "a$b": INT64_ZERO},
            {"_id": 1, "a": 20, "a$b": Int64(1)},
        ],
        msg="includeArrayIndex should accept non-leading dollar sign in field name",
    ),
    StageTestCase(
        "index_name_very_long",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "x" * 10_000}}],
        expected=[
            {"_id": 1, "a": 10, "x" * 10_000: INT64_ZERO},
            {"_id": 1, "a": 20, "x" * 10_000: Int64(1)},
        ],
        msg="includeArrayIndex should accept very long field names (10,000+ characters)",
    ),
    StageTestCase(
        "index_name_special_punctuation",
        docs=[{"_id": 1, "a": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "a!@#%&"}}],
        expected=[
            {"_id": 1, "a": 10, "a!@#%&": INT64_ZERO},
            {"_id": 1, "a": 20, "a!@#%&": Int64(1)},
        ],
        msg="includeArrayIndex should accept field name with special punctuation",
    ),
]

UNWIND_INDEX_ALL_TESTS = (
    UNWIND_INCLUDE_ARRAY_INDEX_TESTS
    + UNWIND_INDEX_FIELD_NAME_COLLISION_TESTS
    + UNWIND_INDEX_FIELD_NAME_ACCEPTANCE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_INDEX_ALL_TESTS))
def test_unwind_include_array_index(collection, test_case: StageTestCase):
    """Test $unwind includeArrayIndex behavior and field name acceptance."""
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
