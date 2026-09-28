"""$toString ObjectId conversion tests: hex string output and case normalization."""

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
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [ObjectId Conversion]: ObjectId values convert to 24-character lowercase
# hexadecimal strings; mixed-case input to the ObjectId constructor is normalized.
TOSTRING_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "objectid_normal",
        msg="ObjectId converts to its 24-character lowercase hex string",
        expression={"$toString": ObjectId("507f1f77bcf86cd799439011")},
        expected="507f1f77bcf86cd799439011",
    ),
    ExpressionTestCase(
        "objectid_all_zeros",
        msg="All-zero ObjectId converts to 24 zero hex characters",
        expression={"$toString": ObjectId("000000000000000000000000")},
        expected="000000000000000000000000",
    ),
    ExpressionTestCase(
        "objectid_all_fs",
        msg="All-f ObjectId converts to 24 'f' hex characters",
        expression={"$toString": ObjectId("ffffffffffffffffffffffff")},
        expected="ffffffffffffffffffffffff",
    ),
    ExpressionTestCase(
        "objectid_mixed_case_normalized",
        msg="Mixed-case hex in the ObjectId constructor is normalized to lowercase",
        expression={"$toString": ObjectId("507F1F77BCF86CD799439011")},
        expected="507f1f77bcf86cd799439011",
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TOSTRING_OBJECTID_TESTS, "$toString", "string")),
)
def test_toString_objectid(collection, test: ExpressionTestCase):
    """$toString converts ObjectId values to 24-character lowercase hex strings."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
