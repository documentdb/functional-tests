"""Tests for $unset stage field name acceptance and matching."""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field Name Acceptance]: $unset accepts arbitrary valid field
# names regardless of character content or length.
UNSET_FIELD_NAME_ACCEPTANCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "field_name_accented",
        docs=[{"_id": 1, "\u00e9\u00e8\u00ea": 10, "a": 20}],
        pipeline=[{"$unset": "\u00e9\u00e8\u00ea"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept accented unicode field names",
    ),
    StageTestCase(
        "field_name_emoji",
        docs=[{"_id": 1, "\U0001f600\U0001f680": 10, "a": 20}],
        pipeline=[{"$unset": "\U0001f600\U0001f680"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept emoji field names",
    ),
    StageTestCase(
        "field_name_cjk",
        docs=[{"_id": 1, "\u4e16\u754c": 10, "a": 20}],
        pipeline=[{"$unset": "\u4e16\u754c"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept CJK character field names",
    ),
    StageTestCase(
        "field_name_space",
        docs=[{"_id": 1, "hello world": 10, "a": 20}],
        pipeline=[{"$unset": "hello world"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept field names containing spaces",
    ),
    StageTestCase(
        "field_name_tab",
        docs=[{"_id": 1, "a\tb": 10, "c": 20}],
        pipeline=[{"$unset": "a\tb"}],
        expected=[{"_id": 1, "c": 20}],
        msg="$unset should accept field names containing tabs",
    ),
    StageTestCase(
        "field_name_whitespace_only",
        docs=[{"_id": 1, " ": 10, "a": 20}],
        pipeline=[{"$unset": " "}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept whitespace-only field names",
    ),
    StageTestCase(
        "field_name_special_chars",
        docs=[{"_id": 1, "!@#%^&*()=+\\{}[]|~": 10, "a": 20}],
        pipeline=[{"$unset": "!@#%^&*()=+\\{}[]|~"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept special characters in field names",
    ),
    StageTestCase(
        "field_name_long",
        docs=[{"_id": 1, "x" * 10_000: 10, "a": 20}],
        pipeline=[{"$unset": "x" * 10_000}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept long field names up to 10,000 characters",
    ),
    StageTestCase(
        "field_name_numeric_only",
        docs=[{"_id": 1, "0": 10, "123": 20, "a": 30}],
        pipeline=[{"$unset": ["0", "123"]}],
        expected=[{"_id": 1, "a": 30}],
        msg="$unset should accept numeric-only field names",
    ),
    StageTestCase(
        "field_name_non_leading_dollar",
        docs=[{"_id": 1, "a$b": 10, "c": 20}],
        pipeline=[{"$unset": "a$b"}],
        expected=[{"_id": 1, "c": 20}],
        msg="$unset should accept non-leading $ characters in field names",
    ),
    StageTestCase(
        "field_name_bom",
        docs=[{"_id": 1, "\ufeff": 10, "a": 20}],
        pipeline=[{"$unset": "\ufeff"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept BOM character in field names",
    ),
    StageTestCase(
        "field_name_zwsp",
        docs=[{"_id": 1, "\u200b": 10, "a": 20}],
        pipeline=[{"$unset": "\u200b"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept zero-width space in field names",
    ),
    StageTestCase(
        "field_name_zwj",
        docs=[{"_id": 1, "\u200d": 10, "a": 20}],
        pipeline=[{"$unset": "\u200d"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept zero-width joiner in field names",
    ),
    StageTestCase(
        "field_name_directional_marks",
        docs=[{"_id": 1, "\u200e\u200f": 10, "a": 20}],
        pipeline=[{"$unset": "\u200e\u200f"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept directional marks in field names",
    ),
    StageTestCase(
        "field_name_zwj_emoji_sequence",
        docs=[{"_id": 1, "\U0001f468\u200d\U0001f469\u200d\U0001f467": 10, "a": 20}],
        pipeline=[{"$unset": "\U0001f468\u200d\U0001f469\u200d\U0001f467"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept ZWJ emoji sequences in field names",
    ),
    StageTestCase(
        "field_name_proto",
        docs=[{"_id": 1, "__proto__": 10, "a": 20}],
        pipeline=[{"$unset": "__proto__"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept __proto__ as a field name",
    ),
    StageTestCase(
        "field_name_constructor",
        docs=[{"_id": 1, "constructor": 10, "a": 20}],
        pipeline=[{"$unset": "constructor"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should accept constructor as a field name",
    ),
]

# Property [Unicode and Case Sensitivity]: field name matching is
# case-sensitive and no Unicode normalization is performed, so precomposed and
# decomposed forms of the same character are treated as distinct field names.
UNSET_UNICODE_CASE_SENSITIVITY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "case_sensitive_removes_exact",
        docs=[{"_id": 1, "A": 10, "a": 20}],
        pipeline=[{"$unset": "A"}],
        expected=[{"_id": 1, "a": 20}],
        msg="$unset should remove only the exact-case field name",
    ),
    StageTestCase(
        "no_normalization_removes_precomposed_only",
        docs=[{"_id": 1, "\u00e9": 10, "e\u0301": 20}],
        pipeline=[{"$unset": "\u00e9"}],
        expected=[{"_id": 1, "e\u0301": 20}],
        msg="$unset should remove only the precomposed form, leaving the decomposed form intact",
    ),
    StageTestCase(
        "no_normalization_removes_decomposed_only",
        docs=[{"_id": 1, "\u00e9": 10, "e\u0301": 20}],
        pipeline=[{"$unset": "e\u0301"}],
        expected=[{"_id": 1, "\u00e9": 10}],
        msg="$unset should remove only the decomposed form, leaving the precomposed form intact",
    ),
]

UNSET_FIELD_NAME_TESTS = UNSET_FIELD_NAME_ACCEPTANCE_TESTS + UNSET_UNICODE_CASE_SENSITIVITY_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNSET_FIELD_NAME_TESTS))
def test_unset_field_names(collection: Any, test_case: StageTestCase) -> None:
    """Test $unset stage field name acceptance and matching."""
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
