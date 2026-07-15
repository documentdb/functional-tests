from dataclasses import dataclass
from typing import Any

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import (
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)


@dataclass(frozen=True)
class ModTest(BaseTestCase):
    """Test case for $mod operator."""

    dividend: Any = None
    divisor: Any = None


MOD_INTEGER_BOUNDARY_TESTS: list[ModTest] = [
    ModTest(
        "int32_max",
        dividend=INT32_MAX,
        divisor=10,
        expected=7,
        msg="Should handle INT32_MAX as dividend",
    ),
    ModTest(
        "int32_max_minus_1",
        dividend=INT32_MAX_MINUS_1,
        divisor=10,
        expected=6,
        msg="Should handle INT32_MAX-1 as dividend",
    ),
    ModTest(
        "int32_min",
        dividend=INT32_MIN,
        divisor=10,
        expected=-8,
        msg="Should handle INT32_MIN as dividend",
    ),
    ModTest(
        "int32_min_plus_1",
        dividend=INT32_MIN_PLUS_1,
        divisor=10,
        expected=-7,
        msg="Should handle INT32_MIN+1 as dividend",
    ),
    ModTest(
        "int64_max",
        dividend=INT64_MAX,
        divisor=Int64(10),
        expected=Int64(7),
        msg="Should handle INT64_MAX as dividend",
    ),
    ModTest(
        "int64_max_minus_1",
        dividend=INT64_MAX_MINUS_1,
        divisor=Int64(10),
        expected=Int64(6),
        msg="Should handle INT64_MAX-1 as dividend",
    ),
    ModTest(
        "int64_min",
        dividend=INT64_MIN,
        divisor=Int64(10),
        expected=Int64(-8),
        msg="Should handle INT64_MIN as dividend",
    ),
    ModTest(
        "int64_min_plus_1",
        dividend=INT64_MIN_PLUS_1,
        divisor=Int64(10),
        expected=Int64(-7),
        msg="Should handle INT64_MIN+1 as dividend",
    ),
    ModTest(
        "int32_min_mod_negative_one",
        dividend=INT32_MIN,
        divisor=-1,
        expected=0,
        msg="Should handle INT32_MIN mod -1 without overflow",
    ),
    ModTest(
        "int32_min_plus_1_mod_negative_one",
        dividend=INT32_MIN_PLUS_1,
        divisor=-1,
        expected=0,
        msg="Should handle INT32_MIN+1 mod -1",
    ),
    ModTest(
        "int64_min_mod_negative_one",
        dividend=INT64_MIN,
        divisor=Int64(-1),
        expected=Int64(0),
        msg="Should handle INT64_MIN mod -1 without overflow",
    ),
    ModTest(
        "int64_min_plus_1_mod_negative_one",
        dividend=INT64_MIN_PLUS_1,
        divisor=Int64(-1),
        expected=Int64(0),
        msg="Should handle INT64_MIN+1 mod -1",
    ),
    ModTest(
        "million_mod_seven",
        dividend=1000000,
        divisor=7,
        expected=1,
        msg="Should handle large dividend",
    ),
    ModTest(
        "int64_max_modulo",
        dividend=INT64_MAX,
        divisor=1000000,
        expected=Int64(775807),
        msg="Should handle INT64_MAX mod large divisor",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_INTEGER_BOUNDARY_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.dividend, test.divisor]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_INTEGER_BOUNDARY_TESTS))
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
