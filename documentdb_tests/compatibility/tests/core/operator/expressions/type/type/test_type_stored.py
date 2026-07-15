"""$type stored document field reference tests.

Tests that $type correctly identifies the BSON type of values stored in
document fields, including arrays accessed via field references and documents
with dollar-prefixed keys.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_ONE_AND_HALF

# Property [Stored Field References]: $type returns the correct BSON type name
# for values read from stored document fields.
TYPE_STORED_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "stored_int",
        expression={"$type": "$val"},
        doc={"val": 42},
        expected="int",
        msg="$type should return 'int' for a stored int32 field",
    ),
    ExpressionTestCase(
        "stored_long",
        expression={"$type": "$val"},
        doc={"val": Int64(42)},
        expected="long",
        msg="$type should return 'long' for a stored int64 field",
    ),
    ExpressionTestCase(
        "stored_double",
        expression={"$type": "$val"},
        doc={"val": DOUBLE_ONE_AND_HALF},
        expected="double",
        msg="$type should return 'double' for a stored double field",
    ),
    ExpressionTestCase(
        "stored_decimal",
        expression={"$type": "$val"},
        doc={"val": Decimal128("1")},
        expected="decimal",
        msg="$type should return 'decimal' for a stored Decimal128 field",
    ),
    ExpressionTestCase(
        "stored_string",
        expression={"$type": "$val"},
        doc={"val": "hello"},
        expected="string",
        msg="$type should return 'string' for a stored string field",
    ),
    ExpressionTestCase(
        "stored_null",
        expression={"$type": "$val"},
        doc={"val": None},
        expected="null",
        msg="$type should return 'null' for a stored null field",
    ),
    ExpressionTestCase(
        "stored_object",
        expression={"$type": "$val"},
        doc={"val": {"a": 1}},
        expected="object",
        msg="$type should return 'object' for a stored object field",
    ),
    ExpressionTestCase(
        "stored_bindata",
        expression={"$type": "$val"},
        doc={"val": Binary(b"hello")},
        expected="binData",
        msg="$type should return 'binData' for a stored Binary field",
    ),
    ExpressionTestCase(
        "stored_objectid",
        expression={"$type": "$val"},
        doc={"val": ObjectId("507f1f77bcf86cd799439011")},
        expected="objectId",
        msg="$type should return 'objectId' for a stored ObjectId field",
    ),
    ExpressionTestCase(
        "stored_bool",
        expression={"$type": "$val"},
        doc={"val": True},
        expected="bool",
        msg="$type should return 'bool' for a stored bool field",
    ),
    ExpressionTestCase(
        "stored_date",
        expression={"$type": "$val"},
        doc={"val": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expected="date",
        msg="$type should return 'date' for a stored date field",
    ),
    ExpressionTestCase(
        "stored_regex",
        expression={"$type": "$val"},
        doc={"val": Regex("abc", "i")},
        expected="regex",
        msg="$type should return 'regex' for a stored Regex field",
    ),
    ExpressionTestCase(
        "stored_javascript",
        expression={"$type": "$val"},
        doc={"val": Code("function(){}")},
        expected="javascript",
        msg="$type should return 'javascript' for a stored Code field",
    ),
    ExpressionTestCase(
        "stored_timestamp",
        expression={"$type": "$val"},
        doc={"val": Timestamp(1, 1)},
        expected="timestamp",
        msg="$type should return 'timestamp' for a stored Timestamp field",
    ),
    ExpressionTestCase(
        "stored_minkey",
        expression={"$type": "$val"},
        doc={"val": MinKey()},
        expected="minKey",
        msg="$type should return 'minKey' for a stored MinKey field",
    ),
    ExpressionTestCase(
        "stored_maxkey",
        expression={"$type": "$val"},
        doc={"val": MaxKey()},
        expected="maxKey",
        msg="$type should return 'maxKey' for a stored MaxKey field",
    ),
]

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

TYPE_STORED_TESTS = (
    TYPE_STORED_FIELD_TESTS + TYPE_ARRAY_FIELD_REF_TESTS + TYPE_STORED_OPERATOR_KEY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(TYPE_STORED_TESTS))
def test_type_stored(collection, test: ExpressionTestCase):
    """$type returns the correct type name for values stored in document fields."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
