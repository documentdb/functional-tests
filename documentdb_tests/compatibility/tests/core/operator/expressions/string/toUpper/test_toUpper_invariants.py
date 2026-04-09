from __future__ import annotations

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

from .utils.toUpper_common import (
    ToUpperTest,
)

# Property [Idempotency]: applying $toUpper to an already-uppercased result produces the same
# result.
TOUPPER_IDEMPOTENCY_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "idempotency_lowercase",
        value="hello",
        expected="HELLO",
        msg="$toUpper applied twice should equal single application on lowercase",
    ),
    ToUpperTest(
        "idempotency_uppercase",
        value="HELLO",
        expected="HELLO",
        msg="$toUpper applied twice should equal single application on uppercase",
    ),
    ToUpperTest(
        "idempotency_mixed",
        value="HeLLo",
        expected="HELLO",
        msg="$toUpper applied twice should equal single application on mixed case",
    ),
    ToUpperTest(
        "idempotency_nonascii",
        value="café",
        expected="CAFé",
        msg="$toUpper applied twice should equal single application on non-ASCII",
    ),
    ToUpperTest(
        "idempotency_empty",
        value="",
        expected="",
        msg="$toUpper applied twice should equal single application on empty string",
    ),
    ToUpperTest(
        "idempotency_digits",
        value="123",
        expected="123",
        msg="$toUpper applied twice should equal single application on digits",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOUPPER_IDEMPOTENCY_TESTS))
def test_toupper_idempotency(collection, test_case: ToUpperTest):
    """Test $toUpper idempotency."""
    once = {"$toUpper": test_case.value}
    twice = {"$toUpper": once}
    result = execute_project(collection, {"once": once, "twice": twice})
    assertSuccess(
        result, [{"once": test_case.expected, "twice": test_case.expected}], msg=test_case.msg
    )


# Property [Return Type]: the result is always a string when the expression succeeds.
TOUPPER_RETURN_TYPE_TESTS: list[ToUpperTest] = [
    ToUpperTest(
        "return_type_lowercase",
        value="hello",
        msg="$toUpper should return type string for lowercase input",
    ),
    ToUpperTest(
        "return_type_uppercase",
        value="HELLO",
        msg="$toUpper should return type string for uppercase input",
    ),
    ToUpperTest(
        "return_type_empty", value="", msg="$toUpper should return type string for empty input"
    ),
    ToUpperTest(
        "return_type_coerced_int",
        value=42,
        msg="$toUpper should return type string for coerced int",
    ),
    ToUpperTest(
        "return_type_coerced_decimal",
        value=Decimal128("3.14"),
        msg="$toUpper should return type string for coerced Decimal128",
    ),
    ToUpperTest(
        "return_type_unicode",
        value="café",
        msg="$toUpper should return type string for Unicode input",
    ),
    ToUpperTest(
        "return_type_expression",
        value={"$concat": ["a", "b"]},
        msg="$toUpper should return type string for expression input",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(TOUPPER_RETURN_TYPE_TESTS))
def test_toupper_return_type(collection, test_case: ToUpperTest):
    """Test $toUpper result is always type string."""
    result = execute_expression(collection, {"$type": {"$toUpper": test_case.value}})
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)
