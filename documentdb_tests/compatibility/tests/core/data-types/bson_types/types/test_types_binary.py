import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

from ..utils.round_trip_test_case import RoundTripTestCase

# Property [Binary Ordering]: Binary values order first by data length, then by
# data bytes, then by subtype, with subtypes ordered 0 < 1 < 3 < 4 < 5 < 128
# < 2.
BINARY_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_equality",
        expression={"$eq": [Binary(b"", 0), Binary(b"", 0)]},
        expected=True,
        msg="Binary equality should hold for two empty binaries of the same subtype",
    ),
    ExpressionTestCase(
        "empty_lt_nonempty",
        expression={"$lt": [Binary(b"", 0), Binary(b"\x00", 0)]},
        expected=True,
        msg="Binary ordering should place empty binary before any non-empty binary",
    ),
    ExpressionTestCase(
        "length_before_bytes",
        expression={"$lt": [Binary(b"\xff", 0), Binary(b"\x00\x00", 0)]},
        expected=True,
        msg="Binary ordering should compare data length before data bytes",
    ),
    ExpressionTestCase(
        "bytes_when_same_length",
        expression={"$lt": [Binary(b"\x00", 0), Binary(b"\xff", 0)]},
        expected=True,
        msg="Binary ordering should compare data bytes when length is equal",
    ),
    ExpressionTestCase(
        "subtype_0_before_1",
        expression={"$lt": [Binary(b"\x01" * 16, 0), Binary(b"\x01" * 16, 1)]},
        expected=True,
        msg="Binary ordering should place subtype 0 before subtype 1",
    ),
    ExpressionTestCase(
        "subtype_1_before_3",
        expression={"$lt": [Binary(b"\x01" * 16, 1), Binary(b"\x01" * 16, 3)]},
        expected=True,
        msg="Binary ordering should place subtype 1 before subtype 3",
    ),
    ExpressionTestCase(
        "subtype_3_before_4",
        expression={"$lt": [Binary(b"\x01" * 16, 3), Binary(b"\x01" * 16, 4)]},
        expected=True,
        msg="Binary ordering should place subtype 3 before subtype 4",
    ),
    ExpressionTestCase(
        "subtype_4_before_5",
        expression={"$lt": [Binary(b"\x01" * 16, 4), Binary(b"\x01" * 16, 5)]},
        expected=True,
        msg="Binary ordering should place subtype 4 before subtype 5",
    ),
    ExpressionTestCase(
        "subtype_5_before_128",
        expression={"$lt": [Binary(b"\x01" * 16, 5), Binary(b"\x01" * 16, 128)]},
        expected=True,
        msg="Binary ordering should place subtype 5 before subtype 128",
    ),
    ExpressionTestCase(
        "subtype_128_before_2",
        expression={"$lt": [Binary(b"\x01" * 16, 128), Binary(b"\x01" * 16, 2)]},
        expected=True,
        msg="Binary ordering should place subtype 128 before subtype 2",
    ),
    ExpressionTestCase(
        "same_data_different_subtype_not_equal",
        expression={"$eq": [Binary(b"hello", 0), Binary(b"hello", 5)]},
        expected=False,
        msg="Binary equality should distinguish identical data with different subtypes",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BINARY_ORDERING_TESTS))
def test_binary_comparison(collection, test):
    """Test Binary BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Binary Round-Trip Fidelity]: Binary values survive insert and
# retrieval unchanged, preserving both data bytes and subtype.
BINARY_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "empty_subtype_0",
        value=Binary(b"", 0),
        expected=b"",
        msg="Empty binary with subtype 0 should survive round-trip",
    ),
    RoundTripTestCase(
        "subtype_0_data",
        value=Binary(b"\x00\x01\x02\xff", 0),
        expected=b"\x00\x01\x02\xff",
        msg="Binary subtype 0 with data should survive round-trip",
    ),
    RoundTripTestCase(
        "subtype_4_uuid",
        value=Binary(b"\x01" * 16, 4),
        expected=Binary(b"\x01" * 16, 4),
        msg="Binary subtype 4 (UUID) should survive round-trip",
    ),
    RoundTripTestCase(
        "subtype_128_user_defined",
        value=Binary(b"custom", 128),
        expected=Binary(b"custom", 128),
        msg="Binary subtype 128 (user-defined) should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BINARY_ROUND_TRIP_TESTS))
def test_binary_round_trip(collection, test):
    """Test Binary values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
