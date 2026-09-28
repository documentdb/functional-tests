"""
Error tests for $reduce expression.

Consolidates all $reduce error cases: non-array input (one case per non-deprecated
BSON type), type mismatches between initialValue and elements, non-object argument,
unknown fields, and missing required fields.
Note: $reduce propagates null — null input returns null (tested in core_behavior).
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
    CONCAT_TYPE_ERROR,
    REDUCE_INPUT_NOT_ARRAY_ERROR,
    REDUCE_MISSING_IN_ERROR,
    REDUCE_MISSING_INIT_ERROR,
    REDUCE_MISSING_INPUT_ERROR,
    REDUCE_NON_OBJECT_ARG_ERROR,
    REDUCE_UNKNOWN_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Array Input]: $reduce rejects a non-array input for every non-deprecated BSON type.
NOT_ARRAY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": "hello"},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject string input",
    ),
    ExpressionTestCase(
        "int_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": 42},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject int input",
    ),
    ExpressionTestCase(
        "double_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": 3.14},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject double input",
    ),
    ExpressionTestCase(
        "decimal128_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": Decimal128("1")},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject decimal128 input",
    ),
    ExpressionTestCase(
        "int64_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": Int64(1)},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject int64 input",
    ),
    ExpressionTestCase(
        "bool_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": True},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject bool input",
    ),
    ExpressionTestCase(
        "object_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": {"a": 1}},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject object input",
    ),
    ExpressionTestCase(
        "objectid_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": ObjectId()},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject objectid input",
    ),
    ExpressionTestCase(
        "datetime_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject datetime input",
    ),
    ExpressionTestCase(
        "binary_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": Binary(b"x", 0)},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject binary input",
    ),
    ExpressionTestCase(
        "regex_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": Regex("x")},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject regex input",
    ),
    ExpressionTestCase(
        "javascript_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": Code("x")},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject JavaScript code input",
    ),
    ExpressionTestCase(
        "timestamp_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": Timestamp(0, 0)},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject timestamp input",
    ),
    ExpressionTestCase(
        "minkey_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": MinKey()},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject minkey input",
    ),
    ExpressionTestCase(
        "maxkey_input",
        expression={
            "$reduce": {"input": "$arr", "initialValue": 0, "in": {"$add": ["$$value", "$$this"]}}
        },
        doc={"arr": MaxKey()},
        error_code=REDUCE_INPUT_NOT_ARRAY_ERROR,
        msg="$reduce should reject maxkey input",
    ),
]

# Property [Type Mismatch]: an accumulator/element type mismatch propagates the error.
TYPE_MISMATCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_init_int_add",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": "hello",
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$reduce should reject a string accumulator passed to $add",
    ),
    ExpressionTestCase(
        "int_init_string_concat",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 0,
                "in": {"$concat": ["$$value", "$$this"]},
            }
        },
        doc={"arr": ["a"]},
        error_code=CONCAT_TYPE_ERROR,
        msg="$reduce should reject an int accumulator passed to $concat",
    ),
    ExpressionTestCase(
        "mid_iteration_type_mismatch",
        expression={
            "$reduce": {
                "input": "$arr",
                "initialValue": 0,
                "in": {"$add": ["$$value", "$$this"]},
            }
        },
        doc={"arr": [1, 2, "three", 4]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$reduce should reject a type mismatch mid-iteration",
    ),
]

# Property [Non-Object Argument]: a non-object $reduce argument is rejected.
NON_OBJECT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_arg",
        expression={"$reduce": 0},
        error_code=REDUCE_NON_OBJECT_ARG_ERROR,
        msg="$reduce should reject an int argument",
    ),
    ExpressionTestCase(
        "string_arg",
        expression={"$reduce": "hello"},
        error_code=REDUCE_NON_OBJECT_ARG_ERROR,
        msg="$reduce should reject a string argument",
    ),
    ExpressionTestCase(
        "array_arg",
        expression={"$reduce": [1, 2, 3]},
        error_code=REDUCE_NON_OBJECT_ARG_ERROR,
        msg="$reduce should reject an array argument",
    ),
    ExpressionTestCase(
        "null_arg",
        expression={"$reduce": None},
        error_code=REDUCE_NON_OBJECT_ARG_ERROR,
        msg="$reduce should reject a null argument",
    ),
    ExpressionTestCase(
        "bool_arg",
        expression={"$reduce": True},
        error_code=REDUCE_NON_OBJECT_ARG_ERROR,
        msg="$reduce should reject a bool argument",
    ),
]

# Property [Unknown Field]: an unrecognized field in the $reduce argument is rejected.
UNKNOWN_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "extra_unknown",
        expression={"$reduce": {"input": [1], "initialValue": 0, "in": "$$value", "extra": 1}},
        error_code=REDUCE_UNKNOWN_FIELD_ERROR,
        msg="$reduce should reject an unknown field",
    ),
]

# Property [Missing Required Field]: omitting exactly one required field is rejected.
MISSING_REQUIRED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_input",
        expression={"$reduce": {"initialValue": 0, "in": "$$value"}},
        error_code=REDUCE_MISSING_INPUT_ERROR,
        msg="$reduce should reject a missing input field",
    ),
    ExpressionTestCase(
        "missing_initialValue",
        expression={"$reduce": {"input": [1], "in": "$$value"}},
        error_code=REDUCE_MISSING_INIT_ERROR,
        msg="$reduce should reject a missing initialValue field",
    ),
    ExpressionTestCase(
        "missing_in",
        expression={"$reduce": {"input": [1], "initialValue": 0}},
        error_code=REDUCE_MISSING_IN_ERROR,
        msg="$reduce should reject a missing in field",
    ),
]

INPUT_ERROR_TESTS = NOT_ARRAY_ERROR_TESTS + TYPE_MISMATCH_TESTS
STRUCTURE_ERROR_TESTS = NON_OBJECT_ARG_TESTS + UNKNOWN_FIELD_TESTS + MISSING_REQUIRED_TESTS


@pytest.mark.parametrize("test", pytest_params(INPUT_ERROR_TESTS))
def test_reduce_error_insert(collection, test):
    """Test $reduce input errors with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(STRUCTURE_ERROR_TESTS))
def test_reduce_structure_error(collection, test):
    """Test $reduce argument structure validation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
