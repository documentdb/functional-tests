"""
Core behavior tests for the $$ROOT aggregation system variable.

Covers what $$ROOT resolves to: the entire document currently being processed,
byte-for-byte, including BSON type/numeric-precision fidelity, structural
boundaries (many fields, deep nesting), field ordering, the empty-document
case, and its reported BSON type.
"""

from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DOUBLE_PRECISION_LOSS, INT64_MAX

# Property [Document Echo]: $$ROOT returns the entire current document byte-for-byte,
# preserving every BSON type, nested structure, and type distinction (false vs 0,
# '' vs null, int vs long vs double vs decimal).
ROOT_ECHOES_DOC_TESTS: list[ExpressionTestCase] = [
    # `expected` is intentionally omitted for every case here: $$ROOT simply
    # echoes back the whole inserted document, so the executor below falls
    # back to `test.doc` as the expected result.
    ExpressionTestCase(
        id="all_bson_types",
        expression="$$ROOT",
        doc={
            "_id": 1,
            "double": 1.5,
            "string": "text",
            "object": {"nested": 1},
            "array": [1, "two", {"three": 3}],
            "binData": b"\x01\x02\x03",
            "objectId": ObjectId("507f1f77bcf86cd799439011"),
            "bool": True,
            "date": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "null": None,
            "regex": Regex("^abc", "i"),
            "javascript": Code("function() { return 1; }"),
            "int": 42,
            "timestamp": Timestamp(1700000000, 1),
            "long": INT64_MAX,
            "decimal128": Decimal128("1.25"),
            "minKey": MinKey(),
            "maxKey": MaxKey(),
        },
        msg="$$ROOT should return the whole document with every BSON type intact",
    ),
    ExpressionTestCase(
        id="deeply_nested_document",
        expression="$$ROOT",
        doc={"_id": 1, "a": {"b": {"c": {"d": {"e": [{"f": {"g": 1}}]}}}}},
        msg="$$ROOT should return a deeply nested document unchanged",
    ),
    ExpressionTestCase(
        id="array_fields",
        expression="$$ROOT",
        doc={"_id": 1, "arr": [1, 2, 3], "empty": [], "nestedArr": [[1, 2], [3]]},
        msg="$$ROOT should return array-valued fields intact",
    ),
    ExpressionTestCase(
        id="many_fields",
        expression="$$ROOT",
        doc={"_id": 1, **{f"f{i}": i for i in range(200)}},
        msg="$$ROOT should return a document with many fields intact",
    ),
    ExpressionTestCase(
        id="bson_type_distinction",
        expression="$$ROOT",
        doc={
            "_id": 1,
            "boolFalse": False,
            "intZero": 0,
            "boolTrue": True,
            "intOne": 1,
            "emptyString": "",
            "nullValue": None,
        },
        msg="$$ROOT should preserve false vs 0, true vs 1 and '' vs null distinctions",
    ),
    ExpressionTestCase(
        id="numeric_type_distinction",
        expression="$$ROOT",
        doc={
            "_id": 1,
            "int": 1,
            "long": Int64(DOUBLE_PRECISION_LOSS),
            "double": 1.0,
            "decimal": Decimal128("1"),
        },
        msg="$$ROOT should preserve the original numeric type of each field",
    ),
    ExpressionTestCase(
        id="numeric_negative_zero_and_exponent",
        expression="$$ROOT",
        doc={
            "_id": 1,
            "doubleNegativeZero": -0.0,
            "decimalNegativeExponent": Decimal128("-0E+3"),
        },
        msg="$$ROOT should preserve double negative zero sign and Decimal128 exponent",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ROOT_ECHOES_DOC_TESTS))
def test_root_echoes_doc(collection, test):
    """$$ROOT resolves to the exact document that was inserted."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.doc, msg=test.msg)


# Property [Empty Document]: $$ROOT is an empty object when the input document has
# no fields.
ROOT_EMPTY_DOCUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="empty_document",
        expression="$$ROOT",
        doc=None,
        expected={},
        msg="$$ROOT should return an empty object when the input document has no fields",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ROOT_EMPTY_DOCUMENT_TESTS))
def test_root_empty_document(collection, test):
    """$$ROOT over a field-less input document.

    ``doc=None`` selects execute_expression, which evaluates the expression over
    a ``$documents: [{}]`` stage rather than inserting a document, since an
    inserted document would always be given an ``_id``.
    """
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Reported Type]: $$ROOT always reports BSON type "object".
ROOT_REPORTED_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="reported_bson_type",
        expression={"$type": "$$ROOT"},
        doc={"_id": 1, "a": 1},
        expected="object",
        msg="$$ROOT should be typed as object",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ROOT_REPORTED_TYPE_TESTS))
def test_root_reported_type(collection, test):
    """$$ROOT always reports BSON type "object"."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


def test_root_preserves_field_order(collection):
    """$$ROOT re-emits the root document with its original field ordering."""
    doc = {"_id": 1, "z": 1, "a": 2, "m": 3}
    result = execute_expression_with_insert(collection, "$$ROOT", doc)
    assertSuccess(
        result,
        [["_id", "z", "a", "m"]],
        msg="$$ROOT should preserve document field order",
        transform=lambda batch: [list(d["result"].keys()) for d in batch],
    )
