from __future__ import annotations

from dataclasses import dataclass

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.test_case import BaseTestCase, pytest_params
from documentdb_tests.compatibility.tests.core.operator.expressions.string.concat.utils.concat_common import (
    ConcatTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)

# Property [Length Additivity]: len(result) == sum(len(arg) for arg in args), for both codepoints
# and bytes.
CONCAT_LENGTH_TESTS: list[ConcatTest] = [
    ConcatTest(
        "length_varying",
        args=["a", "bb", "ccc"],
        msg="$concat length should be additive for varying-length strings",
    ),
    ConcatTest(
        "length_two_words",
        args=["hello", "world"],
        msg="$concat length should be additive for two words",
    ),
    ConcatTest(
        "length_multibyte",
        args=["café", "naïve"],
        msg="$concat length should be additive for multibyte strings",
    ),
    ConcatTest(
        "length_emoji", args=["🎉", "🚀"], msg="$concat length should be additive for emoji"
    ),
    ConcatTest("length_cjk", args=["日本", "語"], msg="$concat length should be additive for CJK"),
    ConcatTest(
        "length_mixed_byte_widths",
        args=["a", "é", "🎉"],
        msg="$concat length should be additive for mixed byte widths",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONCAT_LENGTH_TESTS))
def test_concat_length_additivity(collection, test_case: ConcatTest):
    """Test $concat length additivity."""
    expected_cp = sum(len(a) for a in test_case.args)
    expected_bytes = sum(len(a.encode("utf-8")) for a in test_case.args)
    concat = {"$concat": test_case.args}
    result = execute_project(
        collection,
        {
            "lenCodepoints": {"$strLenCP": concat},
            "sumCodepoints": {"$add": [{"$strLenCP": a} for a in test_case.args]},
            "lenBytes": {"$strLenBytes": concat},
            "sumBytes": {"$add": [{"$strLenBytes": a} for a in test_case.args]},
        },
    )
    assertSuccess(
        result,
        [
            {
                "lenCodepoints": expected_cp,
                "sumCodepoints": expected_cp,
                "lenBytes": expected_bytes,
                "sumBytes": expected_bytes,
            }
        ],
        msg=test_case.msg,
    )


# Property [Associativity]: grouping does not affect the result.
# concat(concat(a, b), c) == concat(a, concat(b, c)) == concat(a, b, c)
@dataclass(frozen=True)
class ConcatAssocTest(BaseTestCase):
    a: str = None  # type: ignore[assignment]
    b: str = None  # type: ignore[assignment]
    c: str = None  # type: ignore[assignment]


CONCAT_ASSOC_TESTS: list[ConcatAssocTest] = [
    ConcatAssocTest(
        "words", a="hello", b=" ", c="world", msg="$concat should be associative for words"
    ),
    ConcatAssocTest(
        "single_chars", a="a", b="b", c="c", msg="$concat should be associative for single chars"
    ),
    ConcatAssocTest(
        "empties_around",
        a="",
        b="x",
        c="",
        msg="$concat should be associative with empty strings around",
    ),
    ConcatAssocTest(
        "empty_middle",
        a="foo",
        b="",
        c="bar",
        msg="$concat should be associative with empty middle",
    ),
    ConcatAssocTest(
        "all_empty", a="", b="", c="", msg="$concat should be associative for all empty strings"
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONCAT_ASSOC_TESTS))
def test_concat_associativity(collection, test_case: ConcatAssocTest):
    """Test $concat associativity."""
    expected = test_case.a + test_case.b + test_case.c
    a, b, c = test_case.a, test_case.b, test_case.c
    result = execute_project(
        collection,
        {
            "flat": {"$concat": [a, b, c]},
            "left": {"$concat": [{"$concat": [a, b]}, c]},
            "right": {"$concat": [a, {"$concat": [b, c]}]},
        },
    )
    assertSuccess(
        result, [{"flat": expected, "left": expected, "right": expected}], msg=test_case.msg
    )


# Property [Return Type]: when no argument is null or missing, the result is always type "string".
CONCAT_RETURN_TYPE_TESTS: list[ConcatTest] = [
    ConcatTest(
        "return_type_single",
        args=["hello"],
        msg="$concat of single string should return type string",
    ),
    ConcatTest(
        "return_type_two",
        args=["hello", "world"],
        msg="$concat of two strings should return type string",
    ),
    ConcatTest(
        "return_type_many",
        args=["a", "b", "c"],
        msg="$concat of many strings should return type string",
    ),
    ConcatTest(
        "return_type_empty_string",
        args=[""],
        msg="$concat of empty string should return type string",
    ),
    ConcatTest(
        "return_type_unicode",
        args=["🎉", "日本語"],
        msg="$concat of unicode strings should return type string",
    ),
    ConcatTest(
        "return_type_expression",
        args=[{"$toUpper": "hello"}],
        msg="$concat of expression should return type string",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONCAT_RETURN_TYPE_TESTS))
def test_concat_return_type(collection, test_case: ConcatTest):
    """Test $concat result is always type string."""
    result = execute_expression(collection, {"$type": {"$concat": test_case.args}})
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)
