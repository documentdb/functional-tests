from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

from ...utils.expression_test_case import (
    ExpressionTestCase,
)
from .utils.replaceAll_common import (
    ReplaceAllTest,
    _expr,
)

# Property [Core Replacement]: all occurrences of find are replaced. Matching is left-to-right
# greedy with no re-scanning.
REPLACEALL_CORE_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "core_all_occurrences",
        input="cat bat cat",
        find="cat",
        replacement="dog",
        expected="dog bat dog",
        msg="$replaceAll should all occurrences",
    ),
    ReplaceAllTest(
        "core_repeated_single_char",
        input="aaa",
        find="a",
        replacement="X",
        expected="XXX",
        msg="$replaceAll should repeated single char",
    ),
    ReplaceAllTest(
        "core_no_match",
        input="hello world",
        find="xyz",
        replacement="abc",
        expected="hello world",
        msg="$replaceAll should no match",
    ),
    # Overlapping pattern: "aa" in "aaa" matches first two, leaving third.
    ReplaceAllTest(
        "core_overlapping_greedy",
        input="aaa",
        find="aa",
        replacement="X",
        expected="Xa",
        msg="$replaceAll should overlapping greedy",
    ),
    ReplaceAllTest(
        "core_overlapping_even",
        input="aaaa",
        find="aa",
        replacement="X",
        expected="XX",
        msg="$replaceAll should overlapping even",
    ),
    # Replacement contains find pattern. No re-scanning should occur.
    ReplaceAllTest(
        "core_no_rescan",
        input="ab",
        find="a",
        replacement="aa",
        expected="aab",
        msg="$replaceAll should no rescan",
    ),
    ReplaceAllTest(
        "core_no_rescan_multiple",
        input="xyx",
        find="x",
        replacement="xx",
        expected="xxyxx",
        msg="$replaceAll should no rescan multiple",
    ),
]


# Property [Case Sensitivity]: matching is case-sensitive.
REPLACEALL_CASE_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "case_lower_find_no_match",
        input="Hello",
        find="hello",
        replacement="X",
        expected="Hello",
        msg="$replaceAll case sensitivity: lower find no match",
    ),
    ReplaceAllTest(
        "case_upper_find_no_match",
        input="hello",
        find="Hello",
        replacement="X",
        expected="hello",
        msg="$replaceAll case sensitivity: upper find no match",
    ),
    ReplaceAllTest(
        "case_exact_match_all",
        input="Hello hello Hello",
        find="Hello",
        replacement="X",
        expected="X hello X",
        msg="$replaceAll case sensitivity: exact match all",
    ),
    ReplaceAllTest(
        "case_all_upper_no_match",
        input="ABC",
        find="abc",
        replacement="X",
        expected="ABC",
        msg="$replaceAll case sensitivity: all upper no match",
    ),
    # Latin extended: é (U+00E9) vs É (U+00C9).
    ReplaceAllTest(
        "case_latin_extended",
        input="\u00c9",
        find="\u00e9",
        replacement="X",
        expected="\u00c9",
        msg="$replaceAll case sensitivity: latin extended",
    ),
    # Greek: σ (U+03C3) vs Σ (U+03A3).
    ReplaceAllTest(
        "case_greek",
        input="\u03a3",
        find="\u03c3",
        replacement="X",
        expected="\u03a3",
        msg="$replaceAll case sensitivity: greek",
    ),
    # Cyrillic: д (U+0434) vs Д (U+0414).
    ReplaceAllTest(
        "case_cyrillic",
        input="\u0414",
        find="\u0434",
        replacement="X",
        expected="\u0414",
        msg="$replaceAll case sensitivity: cyrillic",
    ),
    # Deseret: 𐐨 (U+10428) vs 𐐀 (U+10400).
    ReplaceAllTest(
        "case_deseret",
        input="\U00010400",
        find="\U00010428",
        replacement="X",
        expected="\U00010400",
        msg="$replaceAll case sensitivity: deseret",
    ),
    # No case folding: ß (U+00DF) does not match SS or ss.
    ReplaceAllTest(
        "case_no_fold_eszett_upper",
        input="SS",
        find="\u00df",
        replacement="X",
        expected="SS",
        msg="$replaceAll case sensitivity: no fold eszett upper",
    ),
    ReplaceAllTest(
        "case_no_fold_eszett_lower",
        input="ss",
        find="\u00df",
        replacement="X",
        expected="ss",
        msg="$replaceAll case sensitivity: no fold eszett lower",
    ),
    # No case folding: ﬁ (U+FB01) does not match fi.
    ReplaceAllTest(
        "case_no_fold_fi_ligature",
        input="fi",
        find="\ufb01",
        replacement="X",
        expected="fi",
        msg="$replaceAll case sensitivity: no fold fi ligature",
    ),
    # No case folding: ı (U+0131) does not match i or I.
    ReplaceAllTest(
        "case_no_fold_dotless_i_lower",
        input="i",
        find="\u0131",
        replacement="X",
        expected="i",
        msg="$replaceAll case sensitivity: no fold dotless i lower",
    ),
    ReplaceAllTest(
        "case_no_fold_dotless_i_upper",
        input="I",
        find="\u0131",
        replacement="X",
        expected="I",
        msg="$replaceAll case sensitivity: no fold dotless i upper",
    ),
]


# Property [Identity]: find equals replacement leaves input unchanged.
REPLACEALL_IDENTITY_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "identity_find_equals_replacement",
        input="hello world",
        find="world",
        replacement="world",
        expected="hello world",
        msg="$replaceAll identity: find equals replacement",
    ),
    ReplaceAllTest(
        "identity_single_char",
        input="aaa",
        find="a",
        replacement="a",
        expected="aaa",
        msg="$replaceAll identity: single char",
    ),
    ReplaceAllTest(
        "identity_full_match",
        input="hello",
        find="hello",
        replacement="hello",
        expected="hello",
        msg="$replaceAll identity: full match",
    ),
    ReplaceAllTest(
        "identity_empty_find_empty_replacement",
        input="hello",
        find="",
        replacement="",
        expected="hello",
        msg="$replaceAll identity: empty find empty replacement",
    ),
]


# Property [Expression Arguments]: all three parameters accept arbitrary expressions.
REPLACEALL_EXPR_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "expr_input_expression",
        input={"$toUpper": "hello world"},
        find="WORLD",
        replacement="X",
        expected="HELLO X",
        msg="$replaceAll should accept input expression",
    ),
    ReplaceAllTest(
        "expr_find_expression",
        input="HELLO WORLD",
        find={"$toUpper": "world"},
        replacement="X",
        expected="HELLO X",
        msg="$replaceAll should accept find expression",
    ),
    ReplaceAllTest(
        "expr_replacement_expression",
        input="hello world",
        find="world",
        replacement={"$toUpper": "earth"},
        expected="hello EARTH",
        msg="$replaceAll should accept replacement expression",
    ),
    ReplaceAllTest(
        "expr_all_expressions",
        input={"$concat": ["hel", "lo"]},
        find={"$toLower": "LO"},
        replacement={"$toUpper": "p"},
        expected="helP",
        msg="$replaceAll should accept all expressions",
    ),
    # Expression resolving to null follows null-propagation.
    ReplaceAllTest(
        "expr_null_input",
        input={"$literal": None},
        find="a",
        replacement="b",
        expected=None,
        msg="$replaceAll should accept null input",
    ),
]


# Property [Empty String Behavior]: empty strings in any parameter position produce well-defined
# results including insertion between characters, deletion, and identity. Empty find inserts
# replacement at every code point boundary, not byte boundary.
REPLACEALL_EMPTY_STRING_TESTS: list[ReplaceAllTest] = [
    ReplaceAllTest(
        "empty_input_no_match",
        input="",
        find="abc",
        replacement="X",
        expected="",
        msg="$replaceAll empty string: input no match",
    ),
    ReplaceAllTest(
        "empty_find_inserts_everywhere",
        input="abc",
        find="",
        replacement="X",
        expected="XaXbXcX",
        msg="$replaceAll empty string: find inserts everywhere",
    ),
    ReplaceAllTest(
        "empty_find_empty_input",
        input="",
        find="",
        replacement="X",
        expected="X",
        msg="$replaceAll empty string: find empty input",
    ),
    ReplaceAllTest(
        "empty_all_three",
        input="",
        find="",
        replacement="",
        expected="",
        msg="$replaceAll empty string: all three",
    ),
    ReplaceAllTest(
        "empty_replacement_deletes",
        input="hello world",
        find="o",
        replacement="",
        expected="hell wrld",
        msg="$replaceAll empty string: replacement deletes",
    ),
    # Empty find with multi-byte characters: replacement should be inserted at code point
    # boundaries, not byte boundaries.
    # 2-byte character: é (U+00E9).
    ReplaceAllTest(
        "empty_find_multibyte_2byte",
        input="\u00e9",
        find="",
        replacement="X",
        expected="X\u00e9X",
        msg="$replaceAll empty string: find multibyte 2byte",
        marks=(
            pytest.mark.engine_xfail(
                engine="mongodb",
                reason="MongoDB returns invalid UTF-8 for empty-find multibyte (#95)",
                raises=AssertionError,
            ),
        ),
    ),
    # 3-byte character: 世 (U+4E16).
    ReplaceAllTest(
        "empty_find_multibyte_3byte",
        input="\u4e16",
        find="",
        replacement="X",
        expected="X\u4e16X",
        msg="$replaceAll empty string: find multibyte 3byte",
        marks=(
            pytest.mark.engine_xfail(
                engine="mongodb",
                reason="MongoDB returns invalid UTF-8 for empty-find multibyte (#95)",
                raises=AssertionError,
            ),
        ),
    ),
    # 4-byte character: 😀 (U+1F600).
    ReplaceAllTest(
        "empty_find_multibyte_4byte",
        input="\U0001f600",
        find="",
        replacement="X",
        expected="X\U0001f600X",
        msg="$replaceAll empty string: find multibyte 4byte",
        marks=(
            pytest.mark.engine_xfail(
                engine="mongodb",
                reason="MongoDB returns invalid UTF-8 for empty-find multibyte (#95)",
                raises=AssertionError,
            ),
        ),
    ),
]


# Property [Edge Cases]: position boundaries, backslashes, and large inputs are handled correctly.
REPLACEALL_EDGE_TESTS: list[ReplaceAllTest] = [
    # Find longer than input.
    ReplaceAllTest(
        "edge_find_longer_than_input",
        input="hi",
        find="hello",
        replacement="X",
        expected="hi",
        msg="$replaceAll edge: find longer than input",
    ),
    # Find at start.
    ReplaceAllTest(
        "edge_find_at_start",
        input="abcdef",
        find="abc",
        replacement="X",
        expected="Xdef",
        msg="$replaceAll edge: find at start",
    ),
    # Find at end.
    ReplaceAllTest(
        "edge_find_at_end",
        input="abcdef",
        find="def",
        replacement="X",
        expected="abcX",
        msg="$replaceAll edge: find at end",
    ),
    # Find at start and end.
    ReplaceAllTest(
        "edge_find_at_start_and_end",
        input="abcabc",
        find="abc",
        replacement="X",
        expected="XX",
        msg="$replaceAll edge: find at start and end",
    ),
    # Backslash in all arguments.
    ReplaceAllTest(
        "edge_backslash_find",
        input="a\\b\\c",
        find="\\",
        replacement="X",
        expected="aXbXc",
        msg="$replaceAll edge: backslash find",
    ),
    ReplaceAllTest(
        "edge_backslash_replacement",
        input="hello",
        find="h",
        replacement="\\",
        expected="\\ello",
        msg="$replaceAll edge: backslash replacement",
    ),
    ReplaceAllTest(
        "edge_backslash_in_input_and_find",
        input="a\\b",
        find="a\\b",
        replacement="X",
        expected="X",
        msg="$replaceAll edge: backslash in input and find",
    ),
]


REPLACEALL_CORE_ALL_TESTS = (
    REPLACEALL_CORE_TESTS
    + REPLACEALL_CASE_TESTS
    + REPLACEALL_IDENTITY_TESTS
    + REPLACEALL_EXPR_TESTS
    + REPLACEALL_EMPTY_STRING_TESTS
    + REPLACEALL_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REPLACEALL_CORE_ALL_TESTS))
def test_replaceall_core_cases(collection, test_case: ReplaceAllTest):
    """Test $replaceAll core cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


# Property [Document Field References]: $replaceAll works with field references from inserted
# documents.
REPLACEALL_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    # Object expression: all args from simple field paths.
    ExpressionTestCase(
        "field_object",
        expression={"$replaceAll": {"input": "$i", "find": "$f", "replacement": "$r"}},
        doc={"i": "cat bat cat", "f": "cat", "r": "dog"},
        expected="dog bat dog",
        msg="$replaceAll should accept args from document field paths",
    ),
    # Composite array: all args from $arrayElemAt on a projected array-of-objects field.
    ExpressionTestCase(
        "field_composite_array",
        expression={
            "$replaceAll": {
                "input": {"$arrayElemAt": ["$a.b", 0]},
                "find": {"$arrayElemAt": ["$a.b", 1]},
                "replacement": {"$arrayElemAt": ["$a.b", 2]},
            }
        },
        doc={"a": [{"b": "cat bat cat"}, {"b": "cat"}, {"b": "dog"}]},
        expected="dog bat dog",
        msg="$replaceAll should accept args from composite array field paths",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(REPLACEALL_FIELD_REF_TESTS))
def test_replaceall_field_refs(collection, test_case: ExpressionTestCase):
    """Test $replaceAll with document field references."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
