import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import STRING_SIZE_LIMIT_BYTES

from ..utils.round_trip_test_case import RoundTripTestCase

# Property [String Equality]: string equality is byte-exact with no Unicode
# normalization.
STRING_EQUALITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_equal",
        expression={"$eq": ["abc", "abc"]},
        expected=True,
        msg="String equality should hold for identical strings",
    ),
    ExpressionTestCase(
        "str_empty_equal",
        expression={"$eq": ["", ""]},
        expected=True,
        msg="String equality should hold for two empty strings",
    ),
    ExpressionTestCase(
        "str_case_sensitive",
        expression={"$eq": ["abc", "ABC"]},
        expected=False,
        msg="String equality should be case-sensitive",
    ),
    ExpressionTestCase(
        "str_different",
        expression={"$eq": ["abc", "abd"]},
        expected=False,
        msg="String equality should distinguish different strings",
    ),
    ExpressionTestCase(
        "str_different_length",
        expression={"$eq": ["abc", "abcd"]},
        expected=False,
        msg="String equality should distinguish strings of different length",
    ),
    ExpressionTestCase(
        "str_null_byte_significant",
        expression={"$eq": ["abc\0", "abc"]},
        expected=False,
        msg="String equality should treat a trailing null byte as significant",
    ),
    ExpressionTestCase(
        # U+00E9 precomposed vs "e" + U+0301 combining acute accent.
        "str_no_unicode_normalization",
        expression={"$eq": ["caf\u00e9", "cafe\u0301"]},
        expected=False,
        msg="String equality should not apply Unicode normalization",
    ),
    ExpressionTestCase(
        "str_emoji_equal",
        expression={"$eq": ["\U0001f600", "\U0001f600"]},
        expected=True,
        msg="String equality should hold for identical emoji",
    ),
    ExpressionTestCase(
        "str_cjk_equal",
        expression={"$eq": ["\u4e16\u754c", "\u4e16\u754c"]},
        expected=True,
        msg="String equality should hold for identical CJK strings",
    ),
    ExpressionTestCase(
        "str_cjk_different",
        expression={"$eq": ["\u4e16\u754c", "\u4e16\u754d"]},
        expected=False,
        msg="String equality should distinguish different CJK strings",
    ),
]

# Property [String Ordering]: strings order by lexicographic byte comparison.
STRING_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "str_lt_lexicographic",
        expression={"$lt": ["abc", "abd"]},
        expected=True,
        msg="String ordering should compare strings byte by byte",
    ),
    ExpressionTestCase(
        "str_prefix_shorter_first",
        expression={"$lt": ["a", "aa"]},
        expected=True,
        msg="String ordering should place a prefix before the longer string",
    ),
    ExpressionTestCase(
        "str_empty_before_nonempty",
        expression={"$lt": ["", "a"]},
        expected=True,
        msg="String ordering should place the empty string before a non-empty string",
    ),
    ExpressionTestCase(
        "str_uppercase_before_lowercase",
        # 'A' is U+0041, 'a' is U+0061, so byte ordering puts uppercase first.
        expression={"$lt": ["A", "a"]},
        expected=True,
        msg="String ordering should place uppercase before lowercase by byte value",
    ),
    ExpressionTestCase(
        "str_null_byte_after_prefix",
        # 'a' is a prefix of 'a\0', so the prefix sorts first.
        expression={"$lt": ["a", "a\0"]},
        expected=True,
        msg="String ordering should treat a trailing null byte as extending the string",
    ),
]

STRING_COMPARISON_TESTS = STRING_EQUALITY_TESTS + STRING_ORDERING_TESTS


@pytest.mark.parametrize("test", pytest_params(STRING_COMPARISON_TESTS))
def test_string_comparison(collection, test):
    """Test string BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [String Round-Trip Fidelity]: string values survive insert and
# retrieval unchanged.
STRING_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "empty_string",
        value="",
        expected="",
        msg="Empty string should survive round-trip",
    ),
    RoundTripTestCase(
        "null_byte",
        value="abc\x00def",
        expected="abc\x00def",
        msg="String with embedded null byte should survive round-trip",
    ),
    RoundTripTestCase(
        "emoji",
        value="\U0001f600",
        expected="\U0001f600",
        msg="Emoji string should survive round-trip",
    ),
    RoundTripTestCase(
        "cjk",
        value="\u4e16\u754c",
        expected="\u4e16\u754c",
        msg="CJK string should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STRING_ROUND_TRIP_TESTS))
def test_string_round_trip(collection, test):
    """Test string values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)


def test_string_max_length(collection):
    """Test max-length string passes through the engine unchanged."""
    max_str = "a" * (STRING_SIZE_LIMIT_BYTES - 1)
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{"v": max_str}]},
                {"$project": {"_id": 0, "v": 1}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"v": max_str}], msg="Max-length string should pass through unchanged")
