from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.strLenBytes_common import (
    StrLenBytesTest,
)

# Property [Return Type]: the result is always an integer when the expression succeeds.
STRLENBYTES_RETURN_TYPE_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "return_type_ascii", value="hello", msg="$strLenBytes of ASCII string should return int"
    ),
    StrLenBytesTest(
        "return_type_empty", value="", msg="$strLenBytes of empty string should return int"
    ),
    StrLenBytesTest(
        "return_type_multibyte",
        value="café",
        msg="$strLenBytes of multibyte string should return int",
    ),
    StrLenBytesTest("return_type_emoji", value="🎉", msg="$strLenBytes of emoji should return int"),
    StrLenBytesTest(
        "return_type_expression",
        value={"$concat": ["a", "b"]},
        msg="$strLenBytes of expression result should return int",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRLENBYTES_RETURN_TYPE_TESTS))
def test_strlenbytes_return_type(collection, test_case: StrLenBytesTest):
    """Test $strLenBytes result is always type int."""
    result = execute_expression(collection, {"$type": {"$strLenBytes": test_case.value}})
    assertSuccess(result, [{"result": "int"}], msg=test_case.msg)


# Property [Byte Count Invariant]: the byte count is always >= the code point count.
STRLENBYTES_INVARIANT_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "invariant_ascii", value="hello", msg="$strLenBytes should be >= $strLenCP for ASCII"
    ),
    StrLenBytesTest(
        "invariant_2byte", value="café", msg="$strLenBytes should be >= $strLenCP for 2-byte chars"
    ),
    StrLenBytesTest(
        "invariant_3byte", value="寿司", msg="$strLenBytes should be >= $strLenCP for 3-byte chars"
    ),
    StrLenBytesTest(
        "invariant_4byte", value="😀🎉", msg="$strLenBytes should be >= $strLenCP for 4-byte chars"
    ),
    StrLenBytesTest(
        "invariant_mixed",
        value="aé€😀",
        msg="$strLenBytes should be >= $strLenCP for mixed byte widths",
    ),
    StrLenBytesTest(
        "invariant_empty", value="", msg="$strLenBytes should be >= $strLenCP for empty string"
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRLENBYTES_INVARIANT_TESTS))
def test_strlenbytes_invariant(collection, test_case: StrLenBytesTest):
    """Test $strLenBytes is always >= $strLenCP."""
    s = test_case.value
    result = execute_project(
        collection,
        {"bytesGeCp": {"$gte": [{"$strLenBytes": s}, {"$strLenCP": s}]}},
    )
    assertSuccess(result, [{"bytesGeCp": True}], msg=test_case.msg)


# Property [Length Additivity]: byte length of a concatenation equals the sum of its parts.
STRLENBYTES_ADDITIVITY_TESTS: list[StrLenBytesTest] = [
    StrLenBytesTest(
        "additivity_ascii",
        value=["hello", "world"],
        msg="$strLenBytes of concat should equal sum of parts for ASCII",
    ),
    StrLenBytesTest(
        "additivity_2byte",
        value=["café", "naïve"],
        msg="$strLenBytes of concat should equal sum of parts for 2-byte chars",
    ),
    StrLenBytesTest(
        "additivity_mixed",
        value=["寿司", "🎉"],
        msg="$strLenBytes of concat should equal sum of parts for mixed byte widths",
    ),
    StrLenBytesTest(
        "additivity_empty_left",
        value=["", "hello"],
        msg="$strLenBytes of concat should equal sum of parts with empty left",
    ),
    StrLenBytesTest(
        "additivity_empty_right",
        value=["hello", ""],
        msg="$strLenBytes of concat should equal sum of parts with empty right",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRLENBYTES_ADDITIVITY_TESTS))
def test_strlenbytes_additivity(collection, test_case: StrLenBytesTest):
    """Test $strLenBytes of concatenation equals sum of parts."""
    expected_bytes = sum(len(p.encode("utf-8")) for p in test_case.value)
    parts = test_case.value
    result = execute_project(
        collection,
        {
            "lenConcat": {"$strLenBytes": {"$concat": parts}},
            "sumParts": {"$add": [{"$strLenBytes": p} for p in parts]},
        },
    )
    assertSuccess(
        result, [{"lenConcat": expected_bytes, "sumParts": expected_bytes}], msg=test_case.msg
    )
