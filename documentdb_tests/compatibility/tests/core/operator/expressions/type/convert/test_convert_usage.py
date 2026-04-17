from __future__ import annotations

import struct

import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.operator.expressions.type.convert.utils.convert_common import (  # noqa: E501
    ConvertTest,
    _expr,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Arguments]: each parameter of $convert accepts
# expressions that resolve to valid values at runtime.
CONVERT_EXPRESSION_ARGS_TESTS: list[ConvertTest] = [
    ConvertTest(
        "expr_args_input",
        input={"$add": [10, 32]},
        to="string",
        expected="42",
        msg="$convert should accept expression for input parameter",
    ),
    ConvertTest(
        "expr_args_to",
        input=42,
        to={"$concat": ["in", "t"]},
        expected=42,
        msg="$convert should accept expression for to parameter",
    ),
    ConvertTest(
        "expr_args_to_type",
        input=42,
        to={"type": {"$concat": ["stri", "ng"]}},
        expected="42",
        msg="$convert should accept expression for to.type parameter",
    ),
    ConvertTest(
        "expr_args_subtype",
        input=42,
        to={"type": "binData", "subtype": {"$add": [2, 3]}},
        expected=Binary(struct.pack("<i", 42), 5),
        msg="$convert should accept expression for to.subtype parameter",
    ),
    ConvertTest(
        "expr_args_byte_order",
        input=42,
        to="binData",
        byte_order={"$concat": ["bi", "g"]},
        expected=struct.pack(">i", 42),
        msg="$convert should accept expression for byteOrder parameter",
    ),
    ConvertTest(
        "expr_args_format",
        input="hello",
        to="binData",
        format={"$concat": ["ut", "f8"]},
        expected=b"hello",
        msg="$convert should accept expression for format parameter",
    ),
    ConvertTest(
        "expr_args_on_error",
        input="abc",
        to="int",
        on_error={"$add": [40, 2]},
        expected=42,
        msg="$convert should accept expression for onError parameter",
    ),
    ConvertTest(
        "expr_args_on_null",
        input=None,
        to="int",
        on_null={"$add": [40, 2]},
        expected=42,
        msg="$convert should accept expression for onNull parameter",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONVERT_EXPRESSION_ARGS_TESTS))
def test_convert_expression_args(collection, test_case: ConvertTest):
    """Test $convert expression arguments."""
    result = execute_expression(collection, _expr(test_case))
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


def test_convert_document_fields(collection):
    """Test $convert reads values from document fields."""
    result = execute_expression_with_insert(
        collection,
        {"$convert": {"input": "$val", "to": "$target"}},
        {"val": "42", "target": "int"},
    )
    assert_expression_result(
        result, expected=42, msg="$convert should read input and to from document fields"
    )
