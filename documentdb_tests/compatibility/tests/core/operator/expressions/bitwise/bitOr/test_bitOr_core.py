# handles all int types and inf/nan
from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.bitwise.bitOr.utils.bitOr_common import (  # noqa: E501
    BitOrTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

BITOR_CORE_TESTS: list[BitOrTest] = [
    BitOrTest(
        "core_single_int32",
        args=42,
        expected=42,
        msg="$bitOr of a single int32 should return that value as an integer",
    ),
    BitOrTest(
        "core_single_int64",
        args=Int64(42),
        expected=Int64(42),
        msg="$bitOr of a single int64 should return that value as an integer",
    ),
    BitOrTest(
        "core_two_equal",
        args=[42, 42],
        expected=42,
        msg="$bitOr of two equal int32 values should return that value",
    ),
    BitOrTest(
        "core_two_distinct",
        args=[3, 5],
        expected=7,
        msg="$bitOr of two distinct int32 values should return the correct bitwise OR result",
    ),
    BitOrTest(
        "core_empty_array",
        args=[],
        expected=0,
        msg="$bitOr of an empty array should return 0",
    ),
    BitOrTest(
        "core_int32_and_int64",
        args=[3, Int64(5)],
        expected=Int64(7),
        msg="$bitOr of Int32 and Int64 returns an Int64",
    ),
    BitOrTest(
        "core_negative",
        args=[-1, -6],
        expected=-1,
        msg="$bitOr of negative numbers",
    ),
    BitOrTest(
        "core_six_ints",
        args=[1, 2, 3, 4, 5, 6],
        expected=7,
        msg="$bitOr of [1,2,3,4,5,6] should return 7",
    ),
    BitOrTest(
        "core_four_ints",
        args=[111, 222, 333, 444],
        expected=511,
        msg="$bitOr of [111,222,333,444] should return 511",
    ),
    BitOrTest(
        "core_six_larger_ints",
        args=[349, 1234, 44, 129308, 33, 2309],
        expected=130559,
        msg="$bitOr of [349,1234,44,129308,33,2309] should return 130559",
    ),
    BitOrTest(
        "core_five_ints",
        args=[2342, 23, 104, 253, 1035],
        expected=3583,
        msg="$bitOr of [2342,23,104,253,1035] should return 3583",
    ),
    BitOrTest(
        "core_range_1_to_100",
        args=list(range(1, 101)),
        expected=127,
        msg="$bitOr of integers 1 through 100 should return 127",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(BITOR_CORE_TESTS))
def test_bitOr_core(collection, test_case: BitOrTest):
    """Test $bitOr cases."""
    result = execute_expression(collection, {"$bitOr": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
