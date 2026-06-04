import pytest
from bson import ObjectId

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

# Property [ObjectId Equality]: ObjectIds are equal only when all 12 bytes
# match.
OBJECTID_EQUALITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "exact_match_equal",
        expression={
            "$eq": [ObjectId("507f1f77bcf86cd799439011"), ObjectId("507f1f77bcf86cd799439011")]
        },
        expected=True,
        msg="ObjectId equality should hold for identical 12-byte values",
    ),
    ExpressionTestCase(
        "last_byte_differs_not_equal",
        expression={
            "$eq": [ObjectId("507f1f77bcf86cd799439011"), ObjectId("507f1f77bcf86cd799439012")]
        },
        expected=False,
        msg="ObjectId equality should distinguish values differing in the last byte",
    ),
]

# Property [ObjectId Byte Ordering]: ObjectIds order by lexicographic byte
# comparison.
OBJECTID_BYTE_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leading_byte_dominates",
        expression={
            "$lt": [ObjectId("000000000000000000000001"), ObjectId("ffffffffffffffffffff0001")]
        },
        expected=True,
        msg="ObjectId ordering should let leading bytes dominate trailing bytes",
    ),
    ExpressionTestCase(
        "trailing_byte_tiebreak",
        expression={
            "$lt": [ObjectId("0000000000000000000000aa"), ObjectId("0000000000000000000000bb")]
        },
        expected=True,
        msg="ObjectId ordering should compare trailing bytes when leading bytes are equal",
    ),
    ExpressionTestCase(
        "min_oid_lt_max_oid",
        expression={"$lt": [ObjectId("0" * 24), ObjectId("f" * 24)]},
        expected=True,
        msg="ObjectId ordering should place the all-zeros minimum before the all-0xff maximum",
    ),
]

# Property [ObjectId Timestamp Component]: the leading 4-byte timestamp
# component orders ObjectIds chronologically.
OBJECTID_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "earlier_timestamp_first",
        expression={
            "$lt": [
                ObjectId("5e0be100" + "0" * 16),
                ObjectId("65920080" + "0" * 16),
            ]
        },
        expected=True,
        msg="ObjectId ordering should place an earlier timestamp prefix before a later one",
    ),
]

OBJECTID_COMPARISON_TESTS = (
    OBJECTID_EQUALITY_TESTS + OBJECTID_BYTE_ORDERING_TESTS + OBJECTID_TIMESTAMP_TESTS
)


@pytest.mark.parametrize("test", pytest_params(OBJECTID_COMPARISON_TESTS))
def test_objectid_comparison(collection, test):
    """Test ObjectId BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [ObjectId Round-Trip Fidelity]: ObjectId values survive insert and
# retrieval unchanged.
OBJECTID_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "min_oid",
        value=ObjectId("0" * 24),
        expected=ObjectId("0" * 24),
        msg="All-zeros ObjectId should survive round-trip",
    ),
    RoundTripTestCase(
        "max_oid",
        value=ObjectId("f" * 24),
        expected=ObjectId("f" * 24),
        msg="All-0xff ObjectId should survive round-trip",
    ),
    RoundTripTestCase(
        "typical_oid",
        value=ObjectId("507f1f77bcf86cd799439011"),
        expected=ObjectId("507f1f77bcf86cd799439011"),
        msg="Typical ObjectId should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OBJECTID_ROUND_TRIP_TESTS))
def test_objectid_round_trip(collection, test):
    """Test ObjectId values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
