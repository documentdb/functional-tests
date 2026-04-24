"""Tests for $count aggregation stage — field name validation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Valid Field Names]: any non-empty string that does not start with
# $, does not contain a dot or null byte, and is not "_id" is accepted.
COUNT_VALID_FIELD_NAME_TESTS: list[StageTestCase] = [
    StageTestCase(
        "valid_space",
        docs=[{"_id": 1}],
        pipeline=[{"$count": " "}],
        expected=[{" ": 1}],
        msg="$count should accept a space character as field name",
    ),
    StageTestCase(
        "valid_tab",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "\t"}],
        expected=[{"\t": 1}],
        msg="$count should accept a tab character as field name",
    ),
    StageTestCase(
        "valid_nbsp",
        docs=[{"_id": 1}],
        # U+00A0 non-breaking space.
        pipeline=[{"$count": "\u00a0"}],
        expected=[{"\u00a0": 1}],
        msg="$count should accept NBSP as field name",
    ),
    StageTestCase(
        "valid_unicode_accented",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "caf\u00e9"}],
        expected=[{"caf\u00e9": 1}],
        msg="$count should accept accented Unicode characters",
    ),
    StageTestCase(
        "valid_unicode_emoji",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "\U0001f600"}],
        expected=[{"\U0001f600": 1}],
        msg="$count should accept emoji as field name",
    ),
    StageTestCase(
        "valid_unicode_cjk",
        docs=[{"_id": 1}],
        # U+4E16 (CJK character).
        pipeline=[{"$count": "\u4e16"}],
        expected=[{"\u4e16": 1}],
        msg="$count should accept CJK characters as field name",
    ),
    StageTestCase(
        "valid_zwsp",
        docs=[{"_id": 1}],
        # U+200B zero-width space.
        pipeline=[{"$count": "\u200b"}],
        expected=[{"\u200b": 1}],
        msg="$count should accept zero-width space as field name",
    ),
    StageTestCase(
        "valid_zwj_emoji_sequence",
        docs=[{"_id": 1}],
        # Family emoji ZWJ sequence.
        pipeline=[{"$count": "\U0001f468\u200d\U0001f469\u200d\U0001f467"}],
        expected=[{"\U0001f468\u200d\U0001f469\u200d\U0001f467": 1}],
        msg="$count should accept ZWJ emoji sequence as field name",
    ),
    StageTestCase(
        "valid_control_char_x01",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "\x01"}],
        expected=[{"\x01": 1}],
        msg="$count should accept control character 0x01 as field name",
    ),
    StageTestCase(
        "valid_control_char_x1f",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "\x1f"}],
        expected=[{"\x1f": 1}],
        msg="$count should accept control character 0x1F as field name",
    ),
    StageTestCase(
        "valid_del_x7f",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "\x7f"}],
        expected=[{"\x7f": 1}],
        msg="$count should accept DEL character 0x7F as field name",
    ),
    StageTestCase(
        "valid_backslash",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "\\"}],
        expected=[{"\\": 1}],
        msg="$count should accept backslash as field name",
    ),
    StageTestCase(
        "valid_braces",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "{}"}],
        expected=[{"{}": 1}],
        msg="$count should accept braces as field name",
    ),
    StageTestCase(
        "valid_brackets",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "[]"}],
        expected=[{"[]": 1}],
        msg="$count should accept brackets as field name",
    ),
    StageTestCase(
        "valid_double_quote",
        docs=[{"_id": 1}],
        pipeline=[{"$count": '"'}],
        expected=[{'"': 1}],
        msg="$count should accept double quote as field name",
    ),
    StageTestCase(
        "valid_numeric_string",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "123"}],
        expected=[{"123": 1}],
        msg="$count should accept numeric-looking string as field name",
    ),
    StageTestCase(
        "valid_negative_numeric_string",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "-1"}],
        expected=[{"-1": 1}],
        msg="$count should accept negative numeric-looking string as field name",
    ),
    StageTestCase(
        "valid_dollar_in_middle",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "a$b"}],
        expected=[{"a$b": 1}],
        msg="$count should accept $ in non-initial position",
    ),
    StageTestCase(
        "valid_dollar_at_end",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "a$"}],
        expected=[{"a$": 1}],
        msg="$count should accept $ at end of field name",
    ),
    StageTestCase(
        "valid_proto",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "__proto__"}],
        expected=[{"__proto__": 1}],
        msg="$count should accept __proto__ as field name",
    ),
    StageTestCase(
        "valid_constructor",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "constructor"}],
        expected=[{"constructor": 1}],
        msg="$count should accept 'constructor' as field name",
    ),
    StageTestCase(
        "valid_long_name",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "a" * 10_000}],
        expected=[{"a" * 10_000: 1}],
        msg="$count should accept very long field names",
    ),
]

# Property [Case-Sensitive _id Check]: only the exact string "_id" is
# rejected; case variations and similar strings are accepted.
COUNT_ID_CASE_SENSITIVITY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "string_id_case_variation_upper",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "_ID"}],
        expected=[{"_ID": 1}],
        msg="$count should accept '_ID' since check is case-sensitive",
    ),
    StageTestCase(
        "string_id_case_variation_mixed",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "_Id"}],
        expected=[{"_Id": 1}],
        msg="$count should accept '_Id' since check is case-sensitive",
    ),
    StageTestCase(
        "string_id_prefix",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "__id"}],
        expected=[{"__id": 1}],
        msg="$count should accept '__id' since it is not exactly '_id'",
    ),
    StageTestCase(
        "string_id_no_underscore",
        docs=[{"_id": 1}],
        pipeline=[{"$count": "id"}],
        expected=[{"id": 1}],
        msg="$count should accept 'id' since it is not exactly '_id'",
    ),
]

COUNT_FIELD_NAME_TESTS = COUNT_VALID_FIELD_NAME_TESTS + COUNT_ID_CASE_SENSITIVITY_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(COUNT_FIELD_NAME_TESTS))
def test_count_field_names(collection, test_case: StageTestCase):
    """Test $count field name validation."""
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
