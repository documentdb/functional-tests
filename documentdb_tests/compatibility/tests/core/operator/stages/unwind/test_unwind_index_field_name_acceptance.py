"""Tests for $unwind stage — includeArrayIndex field name acceptance."""

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


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_INDEX_FIELD_NAME_ACCEPTANCE_TESTS))
def test_unwind_index_field_name_acceptance(collection, test_case: StageTestCase):
    """Test $unwind includeArrayIndex field name acceptance."""
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
