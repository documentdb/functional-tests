"""$toString Binary conversion tests: base64 encoding, UUID format, and subtype handling."""

import pytest
from bson import Binary

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

# Property [Binary Conversion]: non-UUID Binary values are base64 encoded; subtype 4 with
# exactly 16 bytes converts to UUID string format; subtype 2 (old binary) includes the
# inner 4-byte length prefix in the base64 encoding.
TOSTRING_BINARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binary_empty_sub0",
        msg="Empty Binary (subtype 0) converts to empty string",
        expression={"$toString": Binary(b"", 0)},
        expected="",
    ),
    ExpressionTestCase(
        "binary_sub0",
        msg="Subtype 0 Binary is base64 encoded",
        expression={"$toString": Binary(b"hello", 0)},
        expected="aGVsbG8=",
    ),
    ExpressionTestCase(
        "binary_sub1",
        msg="Subtype 1 Binary is base64 encoded",
        expression={"$toString": Binary(b"hello", 1)},
        expected="aGVsbG8=",
    ),
    ExpressionTestCase(
        "binary_sub2_old_binary",
        msg="Subtype 2 (old binary) includes the inner 4-byte length prefix in base64",
        expression={"$toString": Binary(b"hello", 2)},
        expected="BQAAAGhlbGxv",
    ),
    ExpressionTestCase(
        "binary_sub3",
        msg="Subtype 3 Binary is base64 encoded",
        expression={"$toString": Binary(b"hello", 3)},
        expected="aGVsbG8=",
    ),
    ExpressionTestCase(
        "binary_sub5",
        msg="Subtype 5 Binary is base64 encoded",
        expression={"$toString": Binary(b"hello", 5)},
        expected="aGVsbG8=",
    ),
    ExpressionTestCase(
        "binary_sub6",
        msg="Subtype 6 (encrypted) Binary is base64 encoded",
        expression={"$toString": Binary(b"hello", 6)},
        expected="aGVsbG8=",
    ),
    ExpressionTestCase(
        "binary_sub8",
        msg="Subtype 8 (sensitive) Binary is base64 encoded",
        expression={"$toString": Binary(b"hello", 8)},
        expected="aGVsbG8=",
    ),
    ExpressionTestCase(
        "binary_sub9",
        msg="Subtype 9 (vector) Binary is base64 encoded",
        expression={"$toString": Binary(b"hello", 9)},
        expected="aGVsbG8=",
    ),
    ExpressionTestCase(
        "binary_sub128",
        msg="Subtype 128 Binary is base64 encoded",
        expression={"$toString": Binary(b"hello", 128)},
        expected="aGVsbG8=",
    ),
    ExpressionTestCase(
        "binary_sub4_uuid",
        msg="Subtype 4 Binary with exactly 16 bytes converts to UUID format",
        expression={
            "$toString": Binary(
                b"\x12\x34\x56\x78\x12\x34\x12\x34\x12\x34\x12\x34\x56\x78\x90\x12",
                4,
            )
        },
        expected="12345678-1234-1234-1234-123456789012",
    ),
    ExpressionTestCase(
        "binary_sub4_15bytes",
        msg="Subtype 4 with 15 bytes (not 16) falls back to base64",
        expression={
            "$toString": Binary(
                b"\x12\x34\x56\x78\x12\x34\x12\x34\x12\x34\x12\x34\x56\x78\x90",
                4,
            )
        },
        expected="EjRWeBI0EjQSNBI0VniQ",
    ),
    ExpressionTestCase(
        "binary_sub4_17bytes",
        msg="Subtype 4 with 17 bytes (not 16) falls back to base64",
        expression={
            "$toString": Binary(
                b"\x12\x34\x56\x78\x12\x34\x12\x34\x12\x34\x12\x34\x56\x78\x90\x12\x99",
                4,
            )
        },
        expected="EjRWeBI0EjQSNBI0VniQEpk=",
    ),
    ExpressionTestCase(
        "binary_sub4_8bytes",
        msg="Subtype 4 with 8 bytes (half of 16) falls back to base64",
        expression={"$toString": Binary(b"\x12\x34\x56\x78\x12\x34\x56\x78", 4)},
        expected="EjRWeBI0Vng=",
    ),
    ExpressionTestCase(
        "binary_sub4_32bytes",
        msg="Subtype 4 with 32 bytes (double of 16) falls back to base64",
        expression={"$toString": Binary(b"\x12\x34\x56\x78" * 8, 4)},
        expected="EjRWeBI0VngSNFZ4EjRWeBI0VngSNFZ4EjRWeBI0Vng=",
    ),
    ExpressionTestCase(
        "binary_16bytes_sub0",
        msg="16-byte subtype 0 Binary uses base64, not UUID format",
        expression={
            "$toString": Binary(
                b"\x12\x34\x56\x78\x12\x34\x12\x34\x12\x34\x12\x34\x56\x78\x90\x12",
                0,
            )
        },
        expected="EjRWeBI0EjQSNBI0VniQEg==",
    ),
    ExpressionTestCase(
        "binary_16bytes_sub3",
        msg="16-byte subtype 3 Binary uses base64, not UUID format",
        expression={
            "$toString": Binary(
                b"\x12\x34\x56\x78\x12\x34\x12\x34\x12\x34\x12\x34\x56\x78\x90\x12",
                3,
            )
        },
        expected="EjRWeBI0EjQSNBI0VniQEg==",
    ),
    ExpressionTestCase(
        "binary_16bytes_sub5",
        msg="16-byte subtype 5 Binary uses base64, not UUID format",
        expression={
            "$toString": Binary(
                b"\x12\x34\x56\x78\x12\x34\x12\x34\x12\x34\x12\x34\x56\x78\x90\x12",
                5,
            )
        },
        expected="EjRWeBI0EjQSNBI0VniQEg==",
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(with_convert_variants(TOSTRING_BINARY_TESTS, "$toString", "string")),
)
def test_toString_binary(collection, test: ExpressionTestCase):
    """$toString converts Binary to base64 or UUID strings depending on subtype and length."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
