from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.split_common import (
    SplitTest,
    _expr,
)

# Property [Core Splitting]: splitting produces an array of substrings between
# delimiter occurrences, with the delimiter excluded from results.
SPLIT_CORE_TESTS: list[SplitTest] = [
    SplitTest(
        "core_basic",
        string="a-b-c",
        delimiter="-",
        expected=["a", "b", "c"],
        msg="$split should split on single-char delimiter",
    ),
    SplitTest(
        "core_space_delim",
        string="hello world foo",
        delimiter=" ",
        expected=["hello", "world", "foo"],
        msg="$split should split on space delimiter",
    ),
    # Delimiter not found returns single-element array with original string.
    SplitTest(
        "core_no_match",
        string="hello",
        delimiter="xyz",
        expected=["hello"],
        msg="$split should return single-element array when delimiter not found",
    ),
    # Delimiter at start produces leading empty string.
    SplitTest(
        "core_delim_at_start",
        string="-hello-world",
        delimiter="-",
        expected=["", "hello", "world"],
        msg="$split should produce leading empty string when delimiter is at start",
    ),
    # Delimiter at end produces trailing empty string.
    SplitTest(
        "core_delim_at_end",
        string="hello-world-",
        delimiter="-",
        expected=["hello", "world", ""],
        msg="$split should produce trailing empty string when delimiter is at end",
    ),
    # Consecutive delimiters produce empty strings between them.
    SplitTest(
        "core_consecutive_delim",
        string="a--b",
        delimiter="-",
        expected=["a", "", "b"],
        msg="$split should produce empty string between consecutive delimiters",
    ),
    SplitTest(
        "core_triple_consecutive_delim",
        string="a---b",
        delimiter="-",
        expected=["a", "", "", "b"],
        msg="$split should produce multiple empty strings for triple consecutive delimiters",
    ),
    # Multi-character delimiter.
    SplitTest(
        "core_multi_char_delim",
        string="helloXYworld",
        delimiter="XY",
        expected=["hello", "world"],
        msg="$split should match multi-character delimiter as a unit",
    ),
    # Delimiter equals the input.
    SplitTest(
        "core_delim_equals_string",
        string="hello",
        delimiter="hello",
        expected=["", ""],
        msg="$split should produce two empty strings when delimiter equals input",
    ),
    # Greedy left-to-right: "aaa" split by "aa" matches at position 0, leaving "a".
    SplitTest(
        "core_greedy_overlap",
        string="aaa",
        delimiter="aa",
        expected=["", "a"],
        msg="$split should match greedily left-to-right for overlapping delimiter",
    ),
]

# Property [Expression Arguments]: both argument positions accept expressions
# that resolve to strings, not just literals.
SPLIT_EXPR_TESTS: list[SplitTest] = [
    SplitTest(
        "expr_string_from_concat",
        string={"$concat": ["a-", "b"]},
        delimiter="-",
        expected=["a", "b"],
        msg="$split should accept expression resolving to string as first argument",
    ),
    SplitTest(
        "expr_delimiter_from_concat",
        string="hello-world",
        delimiter={"$concat": ["-", ""]},
        expected=["hello", "world"],
        msg="$split should accept expression resolving to string as delimiter",
    ),
    # $literal suppresses field-path interpretation of $-prefixed strings.
    SplitTest(
        "expr_literal_dollar_prefix",
        string={"$literal": "$hello"},
        delimiter="h",
        expected=["$", "ello"],
        msg="$split should treat $literal dollar-prefixed string as text, not field path",
    ),
]

SPLIT_CORE_ALL_TESTS = SPLIT_CORE_TESTS + SPLIT_EXPR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SPLIT_CORE_ALL_TESTS))
def test_split_core_cases(collection, test_case: SplitTest):
    """Test $split core splitting and expression argument cases."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Document Field References]: $split works with values read from
# document fields.
def test_split_document_fields(collection):
    """Test $split reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "a,b,c", "d": ","},
        {"result": {"$split": ["$s", "$d"]}},
    )
    assertSuccess(
        result,
        [{"result": ["a", "b", "c"]}],
        msg="$split should read string and delimiter from document fields",
    )
