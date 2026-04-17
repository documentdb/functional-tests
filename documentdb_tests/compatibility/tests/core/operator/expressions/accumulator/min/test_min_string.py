from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [String Comparison]: string comparison follows BSON byte-by-byte
# ordering with no Unicode normalization or case folding.
MIN_STRING_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_decomposed_vs_precomposed",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "caf\u00e9", "b": "cafe\u0301"},
        expected="cafe\u0301",
        msg="$min should distinguish decomposed and precomposed Unicode forms",
    ),
    ExpressionTestCase(
        "string_digit_lexicographic",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "9", "b": "10"},
        expected="10",
        msg="$min should compare digit strings lexicographically, not numerically",
    ),
    ExpressionTestCase(
        "string_null_byte",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "a\x00c", "b": "a\x00b"},
        expected="a\x00b",
        msg="$min should accept and compare strings containing null bytes",
    ),
    ExpressionTestCase(
        "string_no_case_folding",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "a", "b": "A"},
        expected="A",
        msg="$min should compare without case folding, returning uppercase as lower byte value",
    ),
    ExpressionTestCase(
        "string_no_ligature_expansion",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "\ufb01", "b": "fi"},
        expected="fi",
        msg="$min should not expand ligatures, treating fi ligature as distinct from 'fi'",
    ),
    ExpressionTestCase(
        "string_no_zwj_stripping",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "a\u200db", "b": "ab"},
        expected="ab",
        msg="$min should not strip zero-width characters during comparison",
    ),
    ExpressionTestCase(
        "string_literal_dollar_prefix",
        expression={"$min": [{"$literal": "$notAField"}, "$a"]},
        doc={"a": "abc"},
        expected="$notAField",
        msg="$min should compare $literal dollar-prefixed string by byte value",
    ),
    # 4-byte UTF-8 (supplementary plane) characters.
    ExpressionTestCase(
        "string_4byte_utf8",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "\U0001f389", "b": "\U0001f388"},
        expected="\U0001f388",
        msg="$min should compare 4-byte UTF-8 characters by byte value",
    ),
    ExpressionTestCase(
        "string_prefix",
        expression={"$min": ["$a", "$b"]},
        doc={"a": "abc", "b": "abcd"},
        expected="abc",
        msg="$min should pick the shorter string when it shares a prefix with the longer",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MIN_STRING_COMPARISON_TESTS))
def test_min_string_cases(collection, test_case: ExpressionTestCase):
    """Test $min string comparison cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
