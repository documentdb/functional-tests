"""Tests for $querySettings stage argument and field validation."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Empty Result]: with no query settings configured, the stage
# returns zero documents whether showDebugQueryShape is omitted or set.
QUERYSETTINGS_EMPTY_RESULT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_omitted_empty_doc",
        pipeline=[{"$querySettings": {}}],
        expected=[],
        msg=(
            "$querySettings should return zero documents for an empty"
            " argument when no settings are configured"
        ),
    ),
    StageTestCase(
        "empty_with_debug_true",
        pipeline=[{"$querySettings": {"showDebugQueryShape": True}}],
        expected=[],
        msg=(
            "$querySettings should return zero documents with"
            " showDebugQueryShape true when no settings are configured"
        ),
    ),
    StageTestCase(
        "empty_with_debug_false",
        pipeline=[{"$querySettings": {"showDebugQueryShape": False}}],
        expected=[],
        msg=(
            "$querySettings should return zero documents with"
            " showDebugQueryShape false when no settings are configured"
        ),
    ),
]

# Property [Stage Document Validation Errors]: an extra top-level key in
# the pipeline stage specification object alongside $querySettings is
# rejected with PIPELINE_STAGE_EXTRA_FIELD_ERROR.
QUERYSETTINGS_STAGE_DOC_VALIDATION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "stage_doc_extra_key",
        pipeline=[{"$querySettings": {}, "extra": 1}],
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="$querySettings should reject an extra key in the stage specification object",
    ),
]

# Property [Unknown Field Errors]: a field name in the stage argument
# document other than `showDebugQueryShape` is rejected with
# UNRECOGNIZED_COMMAND_FIELD_ERROR.
QUERYSETTINGS_UNKNOWN_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"unknown_field_{tid}",
        pipeline=[{"$querySettings": {name: 1}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg=f"$querySettings should reject {tid} as an unknown field name",
    )
    for tid, name in [
        ("plain", "foo"),
        ("case_titled", "ShowDebugQueryShape"),
        ("dollar_prefixed", "$x"),
        ("expression_literal", "$literal"),
        # U+0430 (Cyrillic small letter a) replaces the Latin 'a' in
        # 'showDebugQueryShape' to verify exact byte comparison.
        ("unicode_homoglyph", "showDebugQuerySh\u0430pe"),
        # U+200B (zero-width space) appended to the known field name to
        # verify invisible characters are part of the field name.
        ("zero_width_suffix", "showDebugQueryShape\u200b"),
        ("dot_notation", "a.b"),
        ("empty_string", ""),
        ("leading_space", " showDebugQueryShape"),
        ("trailing_space", "showDebugQueryShape "),
    ]
]

QUERYSETTINGS_VALIDATION_TESTS = (
    QUERYSETTINGS_EMPTY_RESULT_TESTS
    + QUERYSETTINGS_STAGE_DOC_VALIDATION_ERROR_TESTS
    + QUERYSETTINGS_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(QUERYSETTINGS_VALIDATION_TESTS))
def test_querySettings_validation(collection: Collection, test_case: StageTestCase):
    """Test $querySettings empty-result, stage-document, and unknown-field validation."""
    result = execute_admin_command(
        collection,
        {"aggregate": 1, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
