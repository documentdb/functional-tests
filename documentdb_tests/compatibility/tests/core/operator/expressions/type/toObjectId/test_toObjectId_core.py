"""$toObjectId core conversion tests: valid hex strings, ObjectId identity, expression inputs."""

import pytest
from bson import ObjectId

from documentdb_tests.compatibility.tests.core.operator.expressions.type.utils.convert_variants import (  # noqa: E501
    with_convert_variants,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Conversions]: a 24-character hex string is converted to the corresponding
# ObjectId, hex parsing is case-insensitive, output is normalized to lowercase, and ObjectId
# input is returned unchanged.
TOOBJECTID_HEX_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "lowercase_hex",
        msg="Lowercase hex string converts to the corresponding ObjectId",
        expression={"$toObjectId": "507f1f77bcf86cd799439011"},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "uppercase_hex",
        msg="Uppercase hex string converts to the same ObjectId as its lowercase equivalent",
        expression={"$toObjectId": "507F1F77BCF86CD799439011"},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "mixed_case_hex",
        msg="Mixed-case hex string converts to the same ObjectId as its lowercase equivalent",
        expression={"$toObjectId": "507f1F77bcF86cD799439011"},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "all_zeros",
        msg="All-zero hex string converts to the epoch ObjectId",
        expression={"$toObjectId": "000000000000000000000000"},
        expected=ObjectId("000000000000000000000000"),
    ),
    ExpressionTestCase(
        "all_f",
        msg="All-f hex string converts to the max ObjectId",
        expression={"$toObjectId": "ffffffffffffffffffffffff"},
        expected=ObjectId("ffffffffffffffffffffffff"),
    ),
]

# Property [ObjectId Identity]: ObjectId input is returned unchanged.
TOOBJECTID_IDENTITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_identity",
        msg="ObjectId input passes through unchanged",
        expression={"$toObjectId": ObjectId("507f1f77bcf86cd799439011")},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "objectid_identity_zeros",
        msg="All-zero ObjectId passes through unchanged",
        expression={"$toObjectId": ObjectId("000000000000000000000000")},
        expected=ObjectId("000000000000000000000000"),
    ),
]

# Property [Expression Input]: $toObjectId evaluates a nested expression before converting.
TOOBJECTID_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "concat_expression",
        msg="$toObjectId converts a string produced by a $concat expression",
        expression={"$toObjectId": {"$concat": ["507f1f77bcf8", "6cd799439011"]}},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "toobjectid_of_toobjectid",
        msg="$toObjectId of a $toObjectId expression returns the same ObjectId",
        expression={"$toObjectId": {"$toObjectId": "507f1f77bcf86cd799439011"}},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
]

# Property [Field Reference]: $toObjectId resolves field paths from inserted documents.
TOOBJECTID_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_field",
        msg="Valid hex string field converts to ObjectId",
        expression={"$toObjectId": "$v"},
        doc={"v": "507f1f77bcf86cd799439011"},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "objectid_field",
        msg="ObjectId field passes through unchanged",
        expression={"$toObjectId": "$v"},
        doc={"v": ObjectId("507f1f77bcf86cd799439011")},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "missing_field",
        msg="Missing top-level field returns null",
        expression={"$toObjectId": "$v"},
        doc={},
        expected=None,
    ),
    ExpressionTestCase(
        "nested_field",
        msg="Nested field path resolves to ObjectId",
        expression={"$toObjectId": "$doc.v"},
        doc={"doc": {"v": "507f1f77bcf86cd799439011"}},
        expected=ObjectId("507f1f77bcf86cd799439011"),
    ),
    ExpressionTestCase(
        "missing_nested_field",
        msg="Missing nested field returns null",
        expression={"$toObjectId": "$doc.missing"},
        doc={"doc": {"x": 1}},
        expected=None,
    ),
]


TOOBJECTID_CORE_TESTS = with_convert_variants(
    TOOBJECTID_HEX_STRING_TESTS
    + TOOBJECTID_IDENTITY_TESTS
    + TOOBJECTID_EXPRESSION_INPUT_TESTS
    + TOOBJECTID_FIELD_REF_TESTS,
    "$toObjectId",
    "objectId",
)


@pytest.mark.parametrize("test", pytest_params(TOOBJECTID_CORE_TESTS))
def test_toObjectId_core(collection, test: ExpressionTestCase):
    """$toObjectId converts hex strings, passes ObjectId through, and resolves field paths."""
    if test.doc is not None:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    else:
        result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
