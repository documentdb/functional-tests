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
from documentdb_tests.framework.test_constants import (
    MISSING,
)


@dataclass(frozen=True)
class ModTest(BaseTestCase):
    """Test case for $mod operator."""

    dividend: Any = None
    divisor: Any = None


MOD_NULL_MISSING_TESTS: list[ModTest] = [
    ModTest(
        "null_divisor",
        dividend=10,
        divisor=None,
        expected=None,
        msg="Should return null when divisor is null",
    ),
    ModTest(
        "null_dividend",
        dividend=None,
        divisor=3,
        expected=None,
        msg="Should return null when dividend is null",
    ),
    ModTest(
        "missing_dividend",
        dividend=MISSING,
        divisor=3,
        expected=None,
        msg="Should return null when dividend is missing",
    ),
    ModTest(
        "missing_divisor",
        dividend=10,
        divisor=MISSING,
        expected=None,
        msg="Should return null when divisor is missing",
    ),
    ModTest(
        "both_null",
        dividend=None,
        divisor=None,
        expected=None,
        msg="Should return null when both are null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_NULL_MISSING_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.dividend, test.divisor]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_NULL_MISSING_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents.

    A MISSING dividend/divisor is represented by omitting that key from the
    inserted document entirely, rather than inserting a MISSING sentinel value.
    """
    doc = {}
    if test.dividend != MISSING:
        doc["dividend"] = test.dividend
    if test.divisor != MISSING:
        doc["divisor"] = test.divisor
    result = execute_expression_with_insert(collection, {"$mod": ["$dividend", "$divisor"]}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
