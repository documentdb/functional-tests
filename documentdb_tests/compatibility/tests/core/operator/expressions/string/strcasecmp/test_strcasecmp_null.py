from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import MISSING
from documentdb_tests.compatibility.tests.core.operator.expressions.string.strcasecmp.utils.strcasecmp_common import (
    StrcasecmpTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

# Property [Null and Missing]: null and missing values participate in comparison
# rather than short-circuiting, and are treated as equal to each other and to
# empty string.
STRCASECMP_NULL_TESTS: list[StrcasecmpTest] = [
    StrcasecmpTest(
        "null_first_vs_string",
        string1=None,
        string2="hello",
        expected=-1,
        msg="$strcasecmp should rank null before a non-empty string",
    ),
    StrcasecmpTest(
        "null_string_vs_second",
        string1="hello",
        string2=None,
        expected=1,
        msg="$strcasecmp should rank a non-empty string after null",
    ),
    StrcasecmpTest(
        "null_both",
        string1=None,
        string2=None,
        expected=0,
        msg="$strcasecmp should return 0 when both arguments are null",
    ),
    StrcasecmpTest(
        "missing_first_vs_string",
        string1=MISSING,
        string2="hello",
        expected=-1,
        msg="$strcasecmp should rank missing before a non-empty string",
    ),
    StrcasecmpTest(
        "missing_string_vs_second",
        string1="hello",
        string2=MISSING,
        expected=1,
        msg="$strcasecmp should rank a non-empty string after missing",
    ),
    StrcasecmpTest(
        "missing_both",
        string1=MISSING,
        string2=MISSING,
        expected=0,
        msg="$strcasecmp should return 0 when both arguments are missing",
    ),
    # Null and missing compare as equal.
    StrcasecmpTest(
        "null_vs_missing",
        string1=None,
        string2=MISSING,
        expected=0,
        msg="$strcasecmp should treat null and missing as equal",
    ),
    StrcasecmpTest(
        "missing_vs_null",
        string1=MISSING,
        string2=None,
        expected=0,
        msg="$strcasecmp should treat missing and null as equal",
    ),
    # Null is equal to empty string.
    StrcasecmpTest(
        "null_vs_empty_string",
        string1=None,
        string2="",
        expected=0,
        msg="$strcasecmp should treat null as equal to empty string",
    ),
    StrcasecmpTest(
        "null_empty_string_vs_null",
        string1="",
        string2=None,
        expected=0,
        msg="$strcasecmp should treat empty string as equal to null",
    ),
    # Missing is also equal to empty string.
    StrcasecmpTest(
        "missing_vs_empty_string",
        string1=MISSING,
        string2="",
        expected=0,
        msg="$strcasecmp should treat missing as equal to empty string",
    ),
    StrcasecmpTest(
        "missing_empty_string_vs_missing",
        string1="",
        string2=MISSING,
        expected=0,
        msg="$strcasecmp should treat empty string as equal to missing",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(STRCASECMP_NULL_TESTS))
def test_strcasecmp_null_cases(collection, test_case: StrcasecmpTest):
    """Test $strcasecmp null and missing cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
