"""
Error tests for $size expression.

$size errors on non-array input (including null and missing) and wrong arity.
Unlike most operators, $size does NOT propagate null — it errors.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    SIZE_NOT_ARRAY_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Array Rejection]: $size rejects any non-array input, including null.
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_input",
        expression={"$size": "$arr"},
        doc={"arr": "hello"},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject string input",
    ),
    ExpressionTestCase(
        "int_input",
        expression={"$size": "$arr"},
        doc={"arr": 42},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject int input",
    ),
    ExpressionTestCase(
        "double_input",
        expression={"$size": "$arr"},
        doc={"arr": 3.14},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject double input",
    ),
    ExpressionTestCase(
        "bool_true_input",
        expression={"$size": "$arr"},
        doc={"arr": True},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject boolean true input",
    ),
    ExpressionTestCase(
        "bool_false_input",
        expression={"$size": "$arr"},
        doc={"arr": False},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject boolean false input",
    ),
    ExpressionTestCase(
        "null_input",
        expression={"$size": "$arr"},
        doc={"arr": None},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject null input without null propagation",
    ),
    ExpressionTestCase(
        "object_input",
        expression={"$size": "$arr"},
        doc={"arr": {"a": 1}},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject object input",
    ),
    ExpressionTestCase(
        "decimal128_input",
        expression={"$size": "$arr"},
        doc={"arr": Decimal128("1")},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject decimal128 input",
    ),
    ExpressionTestCase(
        "int64_input",
        expression={"$size": "$arr"},
        doc={"arr": Int64(1)},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject int64 input",
    ),
    ExpressionTestCase(
        "objectid_input",
        expression={"$size": "$arr"},
        doc={"arr": ObjectId()},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject objectid input",
    ),
    ExpressionTestCase(
        "datetime_input",
        expression={"$size": "$arr"},
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject datetime input",
    ),
    ExpressionTestCase(
        "binary_input",
        expression={"$size": "$arr"},
        doc={"arr": Binary(b"x", 0)},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject binary input",
    ),
    ExpressionTestCase(
        "regex_input",
        expression={"$size": "$arr"},
        doc={"arr": Regex("x")},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject regex input",
    ),
    ExpressionTestCase(
        "javascript_input",
        expression={"$size": "$arr"},
        doc={"arr": Code("x")},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject JavaScript code input",
    ),
    ExpressionTestCase(
        "timestamp_input",
        expression={"$size": "$arr"},
        doc={"arr": Timestamp(0, 0)},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject timestamp input",
    ),
    ExpressionTestCase(
        "minkey_input",
        expression={"$size": "$arr"},
        doc={"arr": MinKey()},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject minkey input",
    ),
    ExpressionTestCase(
        "maxkey_input",
        expression={"$size": "$arr"},
        doc={"arr": MaxKey()},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject maxkey input",
    ),
]

# Property [Non-Array Field Rejection]: $size errors on a non-array or missing field path.
FIELD_EXPR_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_single_element_array_wrapped",
        expression={"$size": ["$a"]},
        doc={"a": 1},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg=(
            "$size should reject a non-array field ref even when wrapped in a "
            "single-element argument array (array-unwrap syntax)"
        ),
    ),
    ExpressionTestCase(
        "missing_field",
        expression={"$size": "$nonexistent"},
        doc={"other": 1},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject a missing field",
    ),
    ExpressionTestCase(
        "nested_missing_field",
        expression={"$size": "$a.b"},
        doc={"a": {}},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject a missing nested field",
    ),
]

# Property [Literal Input]: $size rejects a non-array literal argument.
LITERAL_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_string",
        expression={"$size": "hello"},
        error_code=SIZE_NOT_ARRAY_ERROR,
        msg="$size should reject a non-array literal",
    ),
]

# Property [Arity]: $size requires exactly one argument.
ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        expression={"$size": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$size should reject zero arguments",
    ),
    ExpressionTestCase(
        "two_args",
        expression={"$size": [1, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$size should reject two arguments",
    ),
]

INSERT_ERROR_TESTS = NOT_ARRAY_ERROR_TESTS + FIELD_EXPR_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(INSERT_ERROR_TESTS))
def test_size_insert(collection, test):
    """Test $size error cases with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(LITERAL_ERROR_TESTS + ARITY_ERROR_TESTS))
def test_size_literal(collection, test):
    """Test $size error cases with literal values, including wrong arity."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
