"""Tests for $unwind stage — unicode encoding and normalization."""

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

# Property [Unicode No Normalization]: precomposed and decomposed Unicode forms
# are treated as distinct field names with no normalization, for both the path
# and includeArrayIndex field names; special characters are accepted in field
# names referenced by the path.
UNWIND_UNICODE_ENCODING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unicode_precomposed_path_distinct_from_decomposed",
        docs=[{"_id": 1, "\u00e9": [1, 2], "e\u0301": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$\u00e9"}}],
        expected=[
            {"_id": 1, "\u00e9": 1, "e\u0301": [10, 20]},
            {"_id": 1, "\u00e9": 2, "e\u0301": [10, 20]},
        ],
        msg=(
            "$unwind on precomposed path should only unwind that field"
            " and leave the decomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_decomposed_path_distinct_from_precomposed",
        docs=[{"_id": 1, "\u00e9": [1, 2], "e\u0301": [10, 20]}],
        pipeline=[{"$unwind": {"path": "$e\u0301"}}],
        expected=[
            {"_id": 1, "\u00e9": [1, 2], "e\u0301": 10},
            {"_id": 1, "\u00e9": [1, 2], "e\u0301": 20},
        ],
        msg=(
            "$unwind on decomposed path should only unwind that field"
            " and leave the precomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_precomposed_index_distinct_from_decomposed",
        docs=[{"_id": 1, "a": [10, 20], "\u00e9": "pre", "e\u0301": "dec"}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "\u00e9"}}],
        expected=[
            {"_id": 1, "a": 10, "\u00e9": INT64_ZERO, "e\u0301": "dec"},
            {"_id": 1, "a": 20, "\u00e9": Int64(1), "e\u0301": "dec"},
        ],
        msg=(
            "includeArrayIndex with precomposed name should overwrite only"
            " the precomposed field and leave the decomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_decomposed_index_distinct_from_precomposed",
        docs=[{"_id": 1, "a": [10, 20], "\u00e9": "pre", "e\u0301": "dec"}],
        pipeline=[{"$unwind": {"path": "$a", "includeArrayIndex": "e\u0301"}}],
        expected=[
            {"_id": 1, "a": 10, "\u00e9": "pre", "e\u0301": INT64_ZERO},
            {"_id": 1, "a": 20, "\u00e9": "pre", "e\u0301": Int64(1)},
        ],
        msg=(
            "includeArrayIndex with decomposed name should overwrite only"
            " the decomposed field and leave the precomposed form intact"
        ),
    ),
    StageTestCase(
        "unicode_space_in_path",
        docs=[{"_id": 1, "a b": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$a b"}}],
        expected=[{"_id": 1, "a b": 1}, {"_id": 1, "a b": 2}],
        msg="$unwind should accept space in path field name",
    ),
    StageTestCase(
        "unicode_tab_in_path",
        docs=[{"_id": 1, "a\tb": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$a\tb"}}],
        expected=[{"_id": 1, "a\tb": 1}, {"_id": 1, "a\tb": 2}],
        msg="$unwind should accept tab in path field name",
    ),
    StageTestCase(
        "unicode_nbsp_in_path",
        docs=[{"_id": 1, "a\u00a0b": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$a\u00a0b"}}],
        expected=[{"_id": 1, "a\u00a0b": 1}, {"_id": 1, "a\u00a0b": 2}],
        msg="$unwind should accept NBSP in path field name",
    ),
    StageTestCase(
        "unicode_control_char_in_path",
        docs=[{"_id": 1, "a\x01b": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$a\x01b"}}],
        expected=[{"_id": 1, "a\x01b": 1}, {"_id": 1, "a\x01b": 2}],
        msg="$unwind should accept control character in path field name",
    ),
    StageTestCase(
        "unicode_emoji_in_path",
        docs=[{"_id": 1, "\U0001f389": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$\U0001f389"}}],
        expected=[{"_id": 1, "\U0001f389": 1}, {"_id": 1, "\U0001f389": 2}],
        msg="$unwind should accept emoji in path field name",
    ),
    StageTestCase(
        "unicode_zwj_sequence_in_path",
        docs=[{"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": [1, 2]}],
        pipeline=[{"$unwind": {"path": "$\U0001f468\u200d\U0001f469\u200d\U0001f467"}}],
        expected=[
            {"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": 1},
            {"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": 2},
        ],
        msg="$unwind should accept ZWJ sequence in path field name",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_UNICODE_ENCODING_TESTS))
def test_unwind_unicode(collection, test_case: StageTestCase):
    """Test $unwind unicode encoding and normalization."""
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
