from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import MISSING


@dataclass(frozen=True)
class StdDevSampTest(BaseTestCase):
    values: Any = None


STDDEVSAMP_NULL_MISSING_TESTS: list[StdDevSampTest] = [
    StdDevSampTest(
        "null_scalar",
        values=None,
        expected=None,
        msg="Should return None for a null scalar",
    ),
    StdDevSampTest(
        "missing_scalar",
        values=MISSING,
        expected=None,
        msg="Should return None for a missing scalar",
    ),
    StdDevSampTest(
        "null_single_array",
        values=[None],
        expected=None,
        msg="Should return None for an array with single null",
    ),
    StdDevSampTest(
        "null_first_array",
        values=[None, 2, 3],
        expected=0.7071067811865476,
        msg="Should calculate stdDevSamp and ignore leading null",
    ),
    StdDevSampTest(
        "null_middle_array",
        values=[1, None, 3],
        expected=01.4142135623730951,
        msg="Should calculate stdDevSamp and ignore middle null",
    ),
    StdDevSampTest(
        "null_end_array",
        values=[1, 2, None],
        expected=0.7071067811865476,
        msg="Should calculate stdDevSamp and ignore ending null",
    ),
    StdDevSampTest(
        "all_null",
        values=[None, None],
        expected=None,
        msg="Should return None when all values are null",
    ),
    StdDevSampTest(
        "null_leaves_one_numeric",
        values=[None, 5],
        expected=None,
        msg="Should return None when only one numeric value with rest None",
    ),
    StdDevSampTest(
        "missing_first_array",
        values=[MISSING, 2, 3],
        expected=0.7071067811865476,
        msg="Should calculate stdDevSamp and ignore leading missing",
    ),
    StdDevSampTest(
        "missing_middle_array",
        values=[1, MISSING, 3],
        expected=1.4142135623730951,
        msg="Should calculate stdDevSamp and ignore middle missing",
    ),
    StdDevSampTest(
        "missing_end_array",
        values=[1, 2, MISSING],
        expected=0.7071067811865476,
        msg="Should calculate stdDevSamp and ignore ending missing",
    ),
    StdDevSampTest(
        "missing_leaves_one_numeric",
        values=[MISSING, 5],
        expected=None,
        msg="Should return None when only one numeric value with rest missing",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_NULL_MISSING_TESTS))
def test_stdDevSamp_null_missing_from_list(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression null & missing properties from a literal argument list."""

    result = execute_expression(collection, {"$stdDevSamp": test_case.values})

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_NULL_MISSING_TESTS))
def test_stdDevSamp_null_missing_from_field(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression null & missing properties from an inserted array field."""
    result = execute_expression_with_insert(
        collection, {"$stdDevSamp": "$values"}, {"values": test_case.values}
    )

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
