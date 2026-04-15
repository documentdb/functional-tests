from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

from .utils.toLower_common import (
    ToLowerTest,
)

# Property [Idempotency]: applying $toLower to an already-lowercased result produces the same
# result.
TOLOWER_IDEMPOTENCY_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "idempotency_upper",
        value="HELLO WORLD",
        expected="hello world",
        msg="$toLower applied twice should equal single application on uppercase",
    ),
    ToLowerTest(
        "idempotency_lowercase",
        value="hello world",
        expected="hello world",
        msg="$toLower applied twice should equal single application on lowercase",
    ),
    ToLowerTest(
        "idempotency_mixed",
        value="HeLLo WoRLd",
        expected="hello world",
        msg="$toLower applied twice should equal single application on mixed case",
    ),
    ToLowerTest(
        "idempotency_nonascii",
        value="RÉSUMÉ",
        expected="rÉsumÉ",
        msg="$toLower applied twice should equal single application on non-ASCII",
    ),
    ToLowerTest(
        "idempotency_empty",
        value="",
        expected="",
        msg="$toLower applied twice should equal single application on empty string",
    ),
    ToLowerTest(
        "idempotency_digits",
        value="12345",
        expected="12345",
        msg="$toLower applied twice should equal single application on digits",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOLOWER_IDEMPOTENCY_TESTS))
def test_tolower_idempotency(collection, test_case: ToLowerTest):
    """Test $toLower idempotency."""
    once = {"$toLower": test_case.value}
    twice = {"$toLower": once}
    result = execute_project(collection, {"once": once, "twice": twice})
    assertSuccess(
        result, [{"once": test_case.expected, "twice": test_case.expected}], msg=test_case.msg
    )


# Property [Return Type]: the result is always a string when the expression succeeds.
TOLOWER_RETURN_TYPE_TESTS: list[ToLowerTest] = [
    ToLowerTest(
        "return_type_string",
        value="HELLO",
        msg="$toLower should return type string for string input",
    ),
    ToLowerTest(
        "return_type_int32", value=42, msg="$toLower should return type string for coerced int32"
    ),
    ToLowerTest(
        "return_type_double",
        value=3.14,
        msg="$toLower should return type string for coerced double",
    ),
    ToLowerTest(
        "return_type_decimal128",
        value=DECIMAL128_ONE_AND_HALF,
        msg="$toLower should return type string for coerced Decimal128",
    ),
    ToLowerTest(
        "return_type_expression",
        value={"$concat": ["A", "B"]},
        msg="$toLower should return type string for expression input",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOLOWER_RETURN_TYPE_TESTS))
def test_tolower_return_type(collection, test_case: ToLowerTest):
    """Test $toLower result is always type string."""
    result = execute_expression(collection, {"$type": {"$toLower": test_case.value}})
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)
