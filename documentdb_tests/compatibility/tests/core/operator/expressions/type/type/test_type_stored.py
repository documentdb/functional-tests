"""$type stored document field reference tests.

Tests that $type correctly identifies the BSON type of values stored in
document fields, including arrays accessed via field references and documents
with dollar-prefixed keys.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Array Field References]: $type returns "array" for any array
# accessed via a field reference, regardless of contents, length, or dotted
# path traversal.
TYPE_ARRAY_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_basic",
        expression={"$type": "$val"},
        doc={"val": [1, 2, 3]},
        expected="array",
        msg="$type should return 'array' for a stored array",
    ),
    ExpressionTestCase(
        "array_with_null",
        expression={"$type": "$val"},
        doc={"val": [None, 1]},
        expected="array",
        msg="$type should return 'array' for a stored array containing null",
    ),
    ExpressionTestCase(
        "array_empty",
        expression={"$type": "$val"},
        doc={"val": []},
        expected="array",
        msg="$type should return 'array' for a stored empty array",
    ),
    ExpressionTestCase(
        "array_single_element",
        expression={"$type": "$val"},
        doc={"val": [42]},
        expected="array",
        msg="$type should return 'array' for a stored single-element array",
    ),
    ExpressionTestCase(
        "array_dotted_index",
        expression={"$type": "$nested.0"},
        doc={"nested": [{"y": 1}, {"y": 2}]},
        expected="array",
        msg="$type should return 'array' for a dotted index into an array",
    ),
    ExpressionTestCase(
        "array_dotted_field",
        expression={"$type": "$nested.y"},
        doc={"nested": [{"y": 1}, {"y": 2}]},
        expected="array",
        msg="$type should return 'array' for a dotted field across array elements",
    ),
    ExpressionTestCase(
        "array_dotted_deep",
        expression={"$type": "$nested.0.y"},
        doc={"nested": [{"y": 1}, {"y": 2}]},
        expected="array",
        msg="$type should return 'array' for a deep dotted path into an array",
    ),
    ExpressionTestCase(
        "array_wrapped_field_path",
        expression={"$type": ["$val"]},
        doc={"val": 42},
        expected="int",
        msg="$type should resolve the field path in ['$val'] to the stored field's type",
    ),
]

# Property [Stored Operator-Like Keys]: documents with $-prefixed keys stored
# in the database are treated as plain objects, not evaluated as expressions.
TYPE_STORED_OPERATOR_KEY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "stored_operator_like_add",
        expression={"$type": "$val"},
        doc={"val": {"$add": [1, 2]}},
        expected="object",
        msg="$type should return 'object' for a stored document with $add key",
    ),
    ExpressionTestCase(
        "stored_operator_like_type",
        expression={"$type": "$val"},
        doc={"val": {"$type": "hello"}},
        expected="object",
        msg="$type should return 'object' for a stored document with $type key",
    ),
    ExpressionTestCase(
        "stored_operator_like_literal",
        expression={"$type": "$val"},
        doc={"val": {"$literal": 1}},
        expected="object",
        msg="$type should return 'object' for a stored document with $literal key",
    ),
]

TYPE_STORED_TESTS = TYPE_ARRAY_FIELD_REF_TESTS + TYPE_STORED_OPERATOR_KEY_TESTS


@pytest.mark.parametrize("test", pytest_params(TYPE_STORED_TESTS))
def test_type_stored(collection, test: ExpressionTestCase):
    """$type returns the correct type name for values stored in document fields."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
