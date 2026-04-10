from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.strLenCP_common import (
    StrLenCPTest,
)

# Property [Return Type]: the result is always an integer when the expression succeeds.
STRLENCP_RETURN_TYPE_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "return_type_ascii", value="hello", msg="$strLenCP of ASCII string should return int"
    ),
    StrLenCPTest("return_type_empty", value="", msg="$strLenCP of empty string should return int"),
    StrLenCPTest(
        "return_type_multibyte", value="café", msg="$strLenCP of multibyte string should return int"
    ),
    StrLenCPTest("return_type_emoji", value="🎉", msg="$strLenCP of emoji should return int"),
    StrLenCPTest(
        "return_type_expression",
        value={"$concat": ["a", "b"]},
        msg="$strLenCP of expression result should return int",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRLENCP_RETURN_TYPE_TESTS))
def test_strlencp_return_type(collection, test_case: StrLenCPTest):
    """Test $strLenCP result is always type int."""
    result = execute_expression(collection, {"$type": {"$strLenCP": test_case.value}})
    assertSuccess(result, [{"result": "int"}], msg=test_case.msg)


# Property [Byte Count Invariant]: the code point count is always <= the byte count.
STRLENCP_INVARIANT_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "invariant_ascii", value="hello", msg="$strLenCP should be <= $strLenBytes for ASCII"
    ),
    StrLenCPTest(
        "invariant_2byte", value="café", msg="$strLenCP should be <= $strLenBytes for 2-byte chars"
    ),
    StrLenCPTest(
        "invariant_3byte", value="寿司", msg="$strLenCP should be <= $strLenBytes for 3-byte chars"
    ),
    StrLenCPTest(
        "invariant_4byte", value="😀🎉", msg="$strLenCP should be <= $strLenBytes for 4-byte chars"
    ),
    StrLenCPTest(
        "invariant_mixed",
        value="aé€😀",
        msg="$strLenCP should be <= $strLenBytes for mixed byte widths",
    ),
    StrLenCPTest(
        "invariant_empty", value="", msg="$strLenCP should be <= $strLenBytes for empty string"
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRLENCP_INVARIANT_TESTS))
def test_strlencp_invariant(collection, test_case: StrLenCPTest):
    """Test $strLenCP is always <= $strLenBytes."""
    s = test_case.value
    result = execute_project(
        collection,
        {"cpLteBytes": {"$lte": [{"$strLenCP": s}, {"$strLenBytes": s}]}},
    )
    assertSuccess(result, [{"cpLteBytes": True}], msg=test_case.msg)


# Property [Length Additivity]: code point length of a concatenation equals the sum of its parts.
STRLENCP_ADDITIVITY_TESTS: list[StrLenCPTest] = [
    StrLenCPTest(
        "additivity_ascii",
        value=["hello", "world"],
        msg="$strLenCP of concat should equal sum of parts for ASCII",
    ),
    StrLenCPTest(
        "additivity_2byte",
        value=["café", "naïve"],
        msg="$strLenCP of concat should equal sum of parts for 2-byte chars",
    ),
    StrLenCPTest(
        "additivity_mixed",
        value=["寿司", "🎉"],
        msg="$strLenCP of concat should equal sum of parts for mixed byte widths",
    ),
    StrLenCPTest(
        "additivity_empty_left",
        value=["", "hello"],
        msg="$strLenCP of concat should equal sum of parts with empty left",
    ),
    StrLenCPTest(
        "additivity_empty_right",
        value=["hello", ""],
        msg="$strLenCP of concat should equal sum of parts with empty right",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRLENCP_ADDITIVITY_TESTS))
def test_strlencp_additivity(collection, test_case: StrLenCPTest):
    """Test $strLenCP of concatenation equals sum of parts."""
    parts = test_case.value
    expected_cp = sum(len(p) for p in parts)
    result = execute_project(
        collection,
        {
            "lenConcat": {"$strLenCP": {"$concat": parts}},
            "sumParts": {"$add": [{"$strLenCP": p} for p in parts]},
        },
    )
    assertSuccess(result, [{"lenConcat": expected_cp, "sumParts": expected_cp}], msg=test_case.msg)
