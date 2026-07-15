from dataclasses import dataclass
from typing import Any

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ModTest(BaseTestCase):
    """Test case for $mod operator."""

    dividend: Any = None
    divisor: Any = None


MOD_TYPE_MATRIX_TESTS: list[ModTest] = [
    ModTest(
        "same_type_int32",
        dividend=10,
        divisor=3,
        expected=1,
        msg="Should compute modulo of int32 values",
    ),
    ModTest(
        "same_type_int64",
        dividend=Int64(10),
        divisor=Int64(3),
        expected=Int64(1),
        msg="Should compute modulo of int64 values",
    ),
    ModTest(
        "same_type_double",
        dividend=10.5,
        divisor=3.0,
        expected=1.5,
        msg="Should compute modulo of double values",
    ),
    ModTest(
        "same_type_decimal",
        dividend=Decimal128("10.5"),
        divisor=Decimal128("3"),
        expected=Decimal128("1.5"),
        msg="Should compute modulo of decimal128 values",
    ),
    ModTest(
        "int32_int64",
        dividend=10,
        divisor=Int64(3),
        expected=Int64(1),
        msg="Should compute modulo of int32 by int64",
    ),
    ModTest(
        "int32_double",
        dividend=10,
        divisor=3.0,
        expected=1.0,
        msg="Should compute modulo of int32 by double",
    ),
    ModTest(
        "int32_decimal",
        dividend=10,
        divisor=Decimal128("3"),
        expected=Decimal128("1"),
        msg="Should compute modulo of int32 by decimal128",
    ),
    ModTest(
        "int64_double",
        dividend=Int64(10),
        divisor=3.0,
        expected=1.0,
        msg="Should compute modulo of int64 by double",
    ),
    ModTest(
        "int64_decimal",
        dividend=Int64(10),
        divisor=Decimal128("3"),
        expected=Decimal128("1"),
        msg="Should compute modulo of int64 by decimal128",
    ),
    ModTest(
        "double_decimal",
        dividend=10.5,
        divisor=Decimal128("3"),
        expected=Decimal128("1.5000000000000"),
        msg="Should compute modulo of double by decimal128",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_TYPE_MATRIX_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.dividend, test.divisor]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_TYPE_MATRIX_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents"""
    result = execute_expression_with_insert(
        collection,
        {"$mod": ["$dividend", "$divisor"]},
        {"dividend": test.dividend, "divisor": test.divisor},
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
