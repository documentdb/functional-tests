# handle returning ints or longs
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

BITOR_RETURN_TYPE_TESTS: list[BitOrTest] = [
    BitOrTest(
        "return_type_int32",
        args=[3, 5],
        expected=7,
        msg="$bitOr of Int32 values should return Int32",
    ),
    BitOrTest(
        "return_type_all_int64",
        args=[Int64(23), Int64(24), Int64(12), Int64(14)],
        expected=Int64(31),
        msg="$bitOr of all Int64 values should return Int64",
    ),
    BitOrTest(
        "return_type_mixed_int32_int64",
        args=[43, 13, 2498, Int64(55)],
        expected=Int64(2559),
        msg="$bitOr of mixed Int32 and Int64 values should return Int64",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(BITOR_RETURN_TYPE_TESTS))
def test_bitOr_return_type(collection, test_case: BitOrTest):
    """Test $bitOr return type."""
    result = execute_expression(collection, {"$bitOr": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
