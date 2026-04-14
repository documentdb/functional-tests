from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

from .utils.replaceOne_common import (
    ReplaceOneTest,
    _expr,
)

# Property [Core Replacement]: only the first occurrence of find is replaced;
# subsequent occurrences are left unchanged. If no match exists, the input is
# returned unchanged. The result is not re-scanned for additional matches.
REPLACEONE_CORE_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "core_first_occurrence_only",
        input="cat bat cat",
        find="cat",
        replacement="dog",
        expected="dog bat cat",
        msg="$replaceOne should first occurrence only",
    ),
    ReplaceOneTest(
        "core_repeated_single_char",
        input="aaa",
        find="a",
        replacement="X",
        expected="Xaa",
        msg="$replaceOne should repeated single char",
    ),
    ReplaceOneTest(
        "core_no_match",
        input="hello world",
        find="xyz",
        replacement="abc",
        expected="hello world",
        msg="$replaceOne should no match",
    ),
    # Replacement contains the find pattern. No re-scanning should occur.
    ReplaceOneTest(
        "core_no_rescan",
        input="ab",
        find="a",
        replacement="aa",
        expected="aab",
        msg="$replaceOne should no rescan",
    ),
    ReplaceOneTest(
        "core_no_rescan_multiple",
        input="xyx",
        find="x",
        replacement="xx",
        expected="xxyx",
        msg="$replaceOne should no rescan multiple",
    ),
    # Overlapping pattern: "aa" in "aaaa" replaces only first match at position 0.
    ReplaceOneTest(
        "core_overlapping_pattern",
        input="aaaa",
        find="aa",
        replacement="X",
        expected="Xaa",
        msg="$replaceOne should overlapping pattern",
    ),
]

# Property [Empty String Behavior]: empty find inserts replacement at the
# beginning of input only, and empty replacement deletes the first occurrence.
REPLACEONE_EMPTY_STRING_TESTS: list[ReplaceOneTest] = [
    # Empty find on non-empty input prepends replacement.
    ReplaceOneTest(
        "empty_find_prepends",
        input="hello",
        find="",
        replacement="X",
        expected="Xhello",
        msg="$replaceOne empty string: find prepends",
    ),
    # Empty find on empty input produces the replacement.
    ReplaceOneTest(
        "empty_find_empty_input",
        input="",
        find="",
        replacement="X",
        expected="X",
        msg="$replaceOne empty string: find empty input",
    ),
    # Empty input with non-empty find produces empty string.
    ReplaceOneTest(
        "empty_input_no_match",
        input="",
        find="abc",
        replacement="X",
        expected="",
        msg="$replaceOne empty string: input no match",
    ),
    # Empty replacement deletes the first occurrence.
    ReplaceOneTest(
        "empty_replacement_deletes",
        input="hello world",
        find="hello ",
        replacement="",
        expected="world",
        msg="$replaceOne empty string: replacement deletes",
    ),
    ReplaceOneTest(
        "empty_replacement_single_char",
        input="aaa",
        find="a",
        replacement="",
        expected="aa",
        msg="$replaceOne empty string: replacement single char",
    ),
]

# Property [Case Sensitivity]: matching is case-sensitive for ASCII and
# non-ASCII scripts, with no case folding, ligature expansion, or
# locale-specific folding.
REPLACEONE_CASE_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "case_lower_find_no_match",
        input="Hello",
        find="hello",
        replacement="X",
        expected="Hello",
        msg="$replaceOne case sensitivity: lower find no match",
    ),
    ReplaceOneTest(
        "case_upper_find_no_match",
        input="hello",
        find="Hello",
        replacement="X",
        expected="hello",
        msg="$replaceOne case sensitivity: upper find no match",
    ),
    ReplaceOneTest(
        "case_exact_match_first_only",
        input="hello Hello hello",
        find="Hello",
        replacement="X",
        expected="hello X hello",
        msg="$replaceOne case sensitivity: exact match first only",
    ),
    # Greek: uppercase Σ (U+03A3) does not match lowercase σ (U+03C3).
    ReplaceOneTest(
        "case_greek_upper_sigma_no_match",
        input="\u03a3\u03b1",
        find="\u03c3\u03b1",
        replacement="X",
        expected="\u03a3\u03b1",
        msg="$replaceOne case sensitivity: greek upper sigma no match",
    ),
    # Cyrillic: uppercase Б (U+0411) does not match lowercase б (U+0431).
    ReplaceOneTest(
        "case_cyrillic_upper_no_match",
        input="\u0411\u043e\u0433",
        find="\u0431\u043e\u0433",
        replacement="X",
        expected="\u0411\u043e\u0433",
        msg="$replaceOne case sensitivity: cyrillic upper no match",
    ),
    # Latin extended: uppercase Ž (U+017D) does not match lowercase ž (U+017E).
    ReplaceOneTest(
        "case_latin_extended_no_match",
        input="\u017divot",
        find="\u017eivot",
        replacement="X",
        expected="\u017divot",
        msg="$replaceOne case sensitivity: latin extended no match",
    ),
    # Deseret: uppercase 𐐀 (U+10400) does not match lowercase 𐐨 (U+10428).
    ReplaceOneTest(
        "case_deseret_no_match",
        input="\U00010400",
        find="\U00010428",
        replacement="X",
        expected="\U00010400",
        msg="$replaceOne case sensitivity: deseret no match",
    ),
    # No case folding: German sharp s (ß) does not match "SS" or "ss".
    ReplaceOneTest(
        "case_sharp_s_no_match_upper_ss",
        input="Stra\u00dfe",
        find="SS",
        replacement="X",
        expected="Stra\u00dfe",
        msg="$replaceOne case sensitivity: sharp s no match upper ss",
    ),
    ReplaceOneTest(
        "case_sharp_s_no_match_lower_ss",
        input="Stra\u00dfe",
        find="ss",
        replacement="X",
        expected="Stra\u00dfe",
        msg="$replaceOne case sensitivity: sharp s no match lower ss",
    ),
    # No ligature expansion: fi ligature (U+FB01) does not match "fi".
    ReplaceOneTest(
        "case_fi_ligature_no_match",
        input="\ufb01sh",
        find="fi",
        replacement="X",
        expected="\ufb01sh",
        msg="$replaceOne case sensitivity: fi ligature no match",
    ),
    # No locale-specific folding: Turkish dotless i (U+0131) does not match "i" or "I".
    ReplaceOneTest(
        "case_turkish_dotless_i_no_match_lower",
        input="\u0131stanbul",
        find="i",
        replacement="X",
        expected="\u0131stanbul",
        msg="$replaceOne case sensitivity: turkish dotless i no match lower",
    ),
    ReplaceOneTest(
        "case_turkish_dotless_i_no_match_upper",
        input="\u0131stanbul",
        find="I",
        replacement="X",
        expected="\u0131stanbul",
        msg="$replaceOne case sensitivity: turkish dotless i no match upper",
    ),
]


# Property [Identity]: when find equals replacement, the result equals the
# input. An empty find with an empty replacement also leaves input unchanged.
REPLACEONE_IDENTITY_TESTS: list[ReplaceOneTest] = [
    ReplaceOneTest(
        "identity_find_equals_replacement",
        input="hello world",
        find="world",
        replacement="world",
        expected="hello world",
        msg="$replaceOne identity: find equals replacement",
    ),
    ReplaceOneTest(
        "identity_single_char",
        input="aaa",
        find="a",
        replacement="a",
        expected="aaa",
        msg="$replaceOne identity: single char",
    ),
    ReplaceOneTest(
        "identity_full_match",
        input="hello",
        find="hello",
        replacement="hello",
        expected="hello",
        msg="$replaceOne identity: full match",
    ),
    ReplaceOneTest(
        "identity_empty_find_empty_replacement",
        input="hello",
        find="",
        replacement="",
        expected="hello",
        msg="$replaceOne identity: empty find empty replacement",
    ),
    ReplaceOneTest(
        "identity_all_empty",
        input="",
        find="",
        replacement="",
        expected="",
        msg="$replaceOne identity: all empty",
    ),
]


# Property [Edge Cases]: $replaceOne behaves correctly at boundary conditions.
REPLACEONE_EDGE_TESTS: list[ReplaceOneTest] = [
    # Find at the start of input.
    ReplaceOneTest(
        "edge_find_at_start",
        input="hello world",
        find="hello",
        replacement="X",
        expected="X world",
        msg="$replaceOne edge: find at start",
    ),
    # Find at the middle of input.
    ReplaceOneTest(
        "edge_find_at_middle",
        input="hello big world",
        find="big",
        replacement="X",
        expected="hello X world",
        msg="$replaceOne edge: find at middle",
    ),
    # Find at the end of input.
    ReplaceOneTest(
        "edge_find_at_end",
        input="hello world",
        find="world",
        replacement="X",
        expected="hello X",
        msg="$replaceOne edge: find at end",
    ),
    # Find is a prefix of input.
    ReplaceOneTest(
        "edge_find_prefix",
        input="hello",
        find="hel",
        replacement="X",
        expected="Xlo",
        msg="$replaceOne edge: find prefix",
    ),
    # Find is a suffix of input.
    ReplaceOneTest(
        "edge_find_suffix",
        input="hello",
        find="llo",
        replacement="X",
        expected="heX",
        msg="$replaceOne edge: find suffix",
    ),
    # Find equals the entire input.
    ReplaceOneTest(
        "edge_find_equals_input",
        input="hello",
        find="hello",
        replacement="X",
        expected="X",
        msg="$replaceOne edge: find equals input",
    ),
    # Find longer than input produces no match.
    ReplaceOneTest(
        "edge_find_longer_than_input",
        input="hi",
        find="hello",
        replacement="X",
        expected="hi",
        msg="$replaceOne edge: find longer than input",
    ),
    # Replacement longer than the entire input.
    ReplaceOneTest(
        "edge_replacement_longer_than_input",
        input="hi",
        find="hi",
        replacement="hello world",
        expected="hello world",
        msg="$replaceOne edge: replacement longer than input",
    ),
    # Replacement is the entire input string.
    ReplaceOneTest(
        "edge_replacement_is_input",
        input="hello",
        find="h",
        replacement="hello",
        expected="helloello",
        msg="$replaceOne edge: replacement is input",
    ),
]

REPLACEONE_CORE_ALL_TESTS = (
    REPLACEONE_CORE_TESTS
    + REPLACEONE_EMPTY_STRING_TESTS
    + REPLACEONE_CASE_TESTS
    + REPLACEONE_IDENTITY_TESTS
    + REPLACEONE_EDGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(REPLACEONE_CORE_ALL_TESTS))
def test_replaceone_core_cases(collection, test_case: ReplaceOneTest):
    """Test $replaceOne core replacement cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
