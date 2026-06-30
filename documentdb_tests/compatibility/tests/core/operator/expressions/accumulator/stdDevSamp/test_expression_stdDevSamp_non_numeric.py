from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
from bson import ObjectId, Regex

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class StdDevSampTest(BaseTestCase):
    values: Any = None


STDDEVSAMP_NON_NUMERIC_TESTS: list[StdDevSampTest] = [
    # sole non-numerics are treated as scalar => None output
    StdDevSampTest(
        "sole_string",
        values="string",
        expected=None,
        msg="Should return None for any scalar string",
    ),
    StdDevSampTest(
        "sole_numeric_string",
        values="30",
        expected=None,
        msg="Should return None for any scalar numeric string",
    ),
    StdDevSampTest(
        "scalar_boolean",
        values=True,
        expected=None,
        msg="Should return None for a boolean scalar",
    ),
    # non-numeric only arrays return None
    StdDevSampTest(
        "array_numeric_string",
        values=["30"],
        expected=None,
        msg="Should return None for one element array with string",
    ),
    StdDevSampTest(
        "array_all_non_numerics",
        values=["3", True, Regex("a"), datetime(2026, 6, 1), ObjectId("000000000000000000000000")],
        expected=None,
        msg="Should return None for arrays with only non-numerics",
    ),
    # non-numerics are ignored among numerics
    StdDevSampTest(
        "numeric_string_with_one_int",
        values=[60, "30"],
        expected=None,
        msg="Should return None due to N>1, all strings are ignored",
    ),
    StdDevSampTest(
        "numeric_string_with_two_int",
        values=[60, "30", 50],
        expected=pytest.approx(7.0710678118654755),
        msg="Should return stdDevSamp of all numerical values, strings are ignored",
    ),
    StdDevSampTest(
        "non_numerics_with_two_int",
        values=[60, "3", 50, True, datetime(2026, 6, 1), ObjectId("000000000000000000000000")],
        expected=pytest.approx(7.0710678118654755),
        msg="Should return stdDevSamp of numerical values, non-numericals are ignored",
    ),
    StdDevSampTest(
        "bool_ignored_with_numerics",
        values=[True, 5, 10, False],
        expected=pytest.approx(3.5355339059327378),
        msg="Should ignore boolean values and compute over remaining numerics",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_NON_NUMERIC_TESTS))
def test_stdDevSamp_non_numeric_from_list(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression non numeric properties from a literal argument list."""

    result = execute_expression(collection, {"$stdDevSamp": test_case.values})

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


@pytest.mark.parametrize("test_case", pytest_params(STDDEVSAMP_NON_NUMERIC_TESTS))
def test_stdDevSamp_non_numeric_from_field(collection, test_case: StdDevSampTest):
    """Test $stdDevSamp expression non numeric properties from an inserted array field."""
    result = execute_expression_with_insert(
        collection, {"$stdDevSamp": "$values"}, {"values": test_case.values}
    )

    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
