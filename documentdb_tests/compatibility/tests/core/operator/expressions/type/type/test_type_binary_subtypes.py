"""$type binary subtype tests.

Tests that $type returns 'binData' for all Binary subtypes regardless of
subtype number or payload content.
"""

from __future__ import annotations

import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Binary Subtypes]: all Binary subtypes return "binData" regardless
# of subtype or payload.
TYPE_BINARY_SUBTYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binary_subtype_0_generic",
        expression={"$type": Binary(b"test", 0)},
        expected="binData",
        msg="$type should return 'binData' for Binary subtype 0 (generic)",
    ),
    ExpressionTestCase(
        "binary_subtype_1_function",
        expression={"$type": Binary(b"test", 1)},
        expected="binData",
        msg="$type should return 'binData' for Binary subtype 1 (function)",
    ),
    ExpressionTestCase(
        "binary_subtype_2_old_binary",
        expression={"$type": Binary(b"test", 2)},
        expected="binData",
        msg="$type should return 'binData' for Binary subtype 2 (old binary)",
    ),
    ExpressionTestCase(
        "binary_subtype_3_old_uuid",
        expression={"$type": Binary(b"\x00" * 16, 3)},
        expected="binData",
        msg="$type should return 'binData' for Binary subtype 3 (old UUID)",
    ),
    ExpressionTestCase(
        "binary_subtype_4_uuid",
        expression={"$type": Binary(b"\x00" * 16, 4)},
        expected="binData",
        msg="$type should return 'binData' for Binary subtype 4 (UUID)",
    ),
    ExpressionTestCase(
        "binary_subtype_5_md5",
        expression={"$type": Binary(b"\x00" * 16, 5)},
        expected="binData",
        msg="$type should return 'binData' for Binary subtype 5 (MD5)",
    ),
    ExpressionTestCase(
        "binary_subtype_6_encrypted",
        expression={"$type": Binary(b"\x00" * 32, 6)},
        expected="binData",
        msg="$type should return 'binData' for Binary subtype 6 (encrypted)",
    ),
    ExpressionTestCase(
        "binary_subtype_128_user_defined",
        expression={"$type": Binary(b"test", 128)},
        expected="binData",
        msg="$type should return 'binData' for Binary subtype 128 (user-defined)",
    ),
    ExpressionTestCase(
        "binary_empty",
        expression={"$type": Binary(b"")},
        expected="binData",
        msg="$type should return 'binData' for empty binary data",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TYPE_BINARY_SUBTYPE_TESTS))
def test_type_binary_subtypes(collection, test: ExpressionTestCase):
    """$type returns 'binData' for all Binary subtypes."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
