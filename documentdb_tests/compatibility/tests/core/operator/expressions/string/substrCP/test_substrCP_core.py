from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT32_MAX

from .utils.substrCP_common import SubstrCPTest, _expr

# Property [Core Substring]: extraction uses zero-based code point indexing with count specifying
# the number of code points to extract.
SUBSTRCP_CORE_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "core_basic_ascii",
        string="abcde",
        index=1,
        count=2,
        expected="bc",
        msg="$substrCP should extract from zero-based code point index",
    ),
    SubstrCPTest(
        "core_digit_string",
        string="12345",
        index=0,
        count=3,
        expected="123",
        msg="$substrCP should treat digit characters as a string, not a number",
    ),
    SubstrCPTest(
        "core_expression_params",
        string="hello",
        index={"$add": [0, 1]},
        count={"$subtract": [3, 1]},
        expected="el",
        msg="$substrCP should accept expressions for index and count",
    ),
    SubstrCPTest(
        "core_expression_string",
        string={"$concat": ["hel", "lo"]},
        index=1,
        count=3,
        expected="ell",
        msg="$substrCP should accept expression for string parameter",
    ),
    SubstrCPTest(
        "core_dollar_literal",
        string={"$literal": "$hello"},
        index=0,
        count=6,
        expected="$hello",
        msg="$substrCP should handle dollar-prefixed string via $literal",
    ),
]

# Property [Boundary Clamping]: when index or count exceeds the string length, the result is
# clamped without error.
SUBSTRCP_BOUNDARY_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "boundary_count_exceeds",
        string="hello",
        index=3,
        count=10,
        expected="lo",
        msg="$substrCP should clamp when index + count exceeds string length",
    ),
    SubstrCPTest(
        "boundary_index_at_length",
        string="hello",
        index=5,
        count=1,
        expected="",
        msg="$substrCP should return empty string when index equals string length",
    ),
    SubstrCPTest(
        "boundary_int32_max_index",
        string="hello",
        index=INT32_MAX,
        count=1,
        expected="",
        msg="$substrCP should return empty string for INT32_MAX index on short string",
    ),
    SubstrCPTest(
        "boundary_int32_max_count",
        string="hello",
        index=0,
        count=INT32_MAX,
        expected="hello",
        msg="$substrCP should clamp INT32_MAX count to remaining characters",
    ),
    SubstrCPTest(
        "boundary_both_int32_max",
        string="hello",
        index=INT32_MAX,
        count=INT32_MAX,
        expected="",
        msg="$substrCP should handle both index and count at INT32_MAX without overflow",
    ),
    SubstrCPTest(
        "boundary_count_zero",
        string="hello",
        index=2,
        count=0,
        expected="",
        msg="$substrCP should return empty string when count is 0",
    ),
    SubstrCPTest(
        "boundary_empty_string",
        string="",
        index=0,
        count=0,
        expected="",
        msg="$substrCP should return empty string for empty input with index 0 count 0",
    ),
    SubstrCPTest(
        "boundary_empty_string_count_1",
        string="",
        index=0,
        count=1,
        expected="",
        msg="$substrCP should return empty string for empty input with count > 0",
    ),
]


SUBSTRCP_CORE_ALL_TESTS = SUBSTRCP_CORE_TESTS + SUBSTRCP_BOUNDARY_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_CORE_ALL_TESTS))
def test_substrcp_core(collection, test_case: SubstrCPTest):
    """Test $substrCP core substring and boundary cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
