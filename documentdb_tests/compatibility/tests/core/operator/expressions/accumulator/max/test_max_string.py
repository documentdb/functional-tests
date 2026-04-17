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
MAX_STRING_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_decomposed_vs_precomposed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "caf\u00e9", "b": "cafe\u0301"},
        expected="caf\u00e9",
        msg="$max should distinguish decomposed and precomposed Unicode forms",
    ),
    ExpressionTestCase(
        "string_digit_lexicographic",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "9", "b": "10"},
        expected="9",
        msg="$max should compare digit strings lexicographically, not numerically",
    ),
    ExpressionTestCase(
        "string_null_byte",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "a\x00c", "b": "a\x00b"},
        expected="a\x00c",
        msg="$max should accept and compare strings containing null bytes",
    ),
    ExpressionTestCase(
        "string_no_case_folding",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "a", "b": "A"},
        expected="a",
        msg="$max should compare without case folding, returning lowercase as higher byte value",
    ),
    ExpressionTestCase(
        "string_no_ligature_expansion",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "\ufb01", "b": "fi"},
        expected="\ufb01",
        msg="$max should not expand ligatures, treating fi ligature as distinct from 'fi'",
    ),
    ExpressionTestCase(
        "string_no_zwj_stripping",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "a\u200db", "b": "ab"},
        expected="a\u200db",
        msg="$max should not strip zero-width characters during comparison",
    ),
    ExpressionTestCase(
        "string_literal_dollar_prefix",
        expression={"$max": [{"$literal": "$notAField"}, "$a"]},
        doc={"a": "abc"},
        expected="abc",
        msg="$max should compare $literal dollar-prefixed string by byte value",
    ),
    # 4-byte UTF-8 (supplementary plane) characters.
    ExpressionTestCase(
        "string_4byte_utf8",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "\U0001f389", "b": "\U0001f388"},
        expected="\U0001f389",
        msg="$max should compare 4-byte UTF-8 characters by byte value",
    ),
    ExpressionTestCase(
        "string_prefix",
        expression={"$max": ["$a", "$b"]},
        doc={"a": "abc", "b": "abcd"},
        expected="abcd",
        msg="$max should pick the longer string when it shares a prefix with the shorter",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MAX_STRING_COMPARISON_TESTS))
def test_max_string_cases(collection, test_case: ExpressionTestCase):
    """Test $max string comparison cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
