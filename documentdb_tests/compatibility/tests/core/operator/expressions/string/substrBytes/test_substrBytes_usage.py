from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_project_with_insert,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_TRAILING_ZERO,
    MISSING,
)

from .utils.substrBytes_common import (
    OPERATORS,
    SubstrBytesTest,
    _expr,
)

# Property [Expression Arguments]: all three parameters accept expressions that resolve to valid
# types.
SUBSTRBYTES_EXPRESSION_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "expr_string",
        string={"$concat": ["hel", "lo"]},
        byte_index=0,
        byte_count=5,
        expected="hello",
        msg="$substrBytes should accept an expression for the string parameter",
    ),
    SubstrBytesTest(
        "expr_start",
        string="hello",
        byte_index={"$add": [1, 1]},
        byte_count=3,
        expected="llo",
        msg="$substrBytes should accept an expression for the start parameter",
    ),
    SubstrBytesTest(
        "expr_length",
        string="hello",
        byte_index=0,
        byte_count={"$strLenBytes": "hel"},
        expected="hel",
        msg="$substrBytes should accept an expression for the length parameter",
    ),
    SubstrBytesTest(
        "nested_substrBytes",
        string={"$substrBytes": ["hello world", 0, 5]},
        byte_index=1,
        byte_count=3,
        expected="ell",
        msg="$substrBytes should compose with itself (substring of a substring)",
    ),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_EXPRESSION_TESTS))
def test_substrbytes_usage(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes cases."""
    result = execute_expression(collection, _expr(test_case, op))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


# Property [Document Field References]: $substrBytes works with field references from inserted
# documents.
@pytest.mark.parametrize("op", OPERATORS)
def test_substrbytes_document_fields(collection, op):
    """Test $substrBytes reads values from document fields."""
    result = execute_project_with_insert(
        collection,
        {"s": "hello world", "i": 6, "n": 5},
        {"result": {op: ["$s", "$i", "$n"]}},
    )
    assertSuccess(
        result, [{"result": "world"}], msg="$substrBytes should read values from document fields"
    )


# Property [Return Type]: the result is always type "string" when the expression succeeds,
# including when the string parameter is null, missing, or coerced from a non-string type.
SUBSTRBYTES_RETURN_TYPE_TESTS: list[SubstrBytesTest] = [
    SubstrBytesTest(
        "return_type_normal",
        string="hello",
        byte_index=0,
        byte_count=5,
        msg="$substrBytes should return type string for normal input",
    ),
    SubstrBytesTest(
        "return_type_null",
        string=None,
        byte_index=0,
        byte_count=5,
        msg="$substrBytes should return type string for null input",
    ),
    SubstrBytesTest(
        "return_type_missing",
        string=MISSING,
        byte_index=0,
        byte_count=5,
        msg="$substrBytes should return type string for missing input",
    ),
    SubstrBytesTest(
        "return_type_coerced_int",
        string=42,
        byte_index=0,
        byte_count=2,
        msg="$substrBytes should return type string for coerced int",
    ),
    SubstrBytesTest(
        "return_type_coerced_double",
        string=3.14,
        byte_index=0,
        byte_count=4,
        msg="$substrBytes should return type string for coerced double",
    ),
    SubstrBytesTest(
        "return_type_coerced_decimal",
        string=DECIMAL128_TRAILING_ZERO,
        byte_index=0,
        byte_count=3,
        msg="$substrBytes should return type string for coerced Decimal128",
    ),
    SubstrBytesTest(
        "return_type_empty",
        string="",
        byte_index=0,
        byte_count=0,
        msg="$substrBytes should return type string for empty input",
    ),
]


@pytest.mark.parametrize("op", OPERATORS)
@pytest.mark.parametrize("test_case", pytest_params(SUBSTRBYTES_RETURN_TYPE_TESTS))
def test_substrbytes_return_type(collection, op, test_case: SubstrBytesTest):
    """Test $substrBytes result is always type string."""
    result = execute_expression(
        collection,
        {"$type": {op: [test_case.string, test_case.byte_index, test_case.byte_count]}},
    )
    assertSuccess(result, [{"result": "string"}], msg=test_case.msg)
