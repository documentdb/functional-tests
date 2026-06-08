import pytest
from bson import Regex

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

# Property [Regex Ordering]: regex values compare by pattern first, then by
# flags, and flag order is normalized so the same flags in any order are equal.
REGEX_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pattern_first",
        expression={"$lt": [Regex("abc", ""), Regex("abd", "")]},
        expected=True,
        msg="Regex ordering should compare pattern before flags",
    ),
    ExpressionTestCase(
        "flags_after_pattern",
        expression={"$lt": [Regex("abc", ""), Regex("abc", "i")]},
        expected=True,
        msg="Regex ordering should compare flags when patterns are equal",
    ),
    ExpressionTestCase(
        "flag_order_normalized",
        expression={"$eq": [Regex("abc", "im"), Regex("abc", "mi")]},
        expected=True,
        msg="Regex equality should normalize flag order",
    ),
    ExpressionTestCase(
        "different_flags_distinct",
        expression={"$eq": [Regex("abc", "i"), Regex("abc", "m")]},
        expected=False,
        msg="Regex equality should distinguish the same pattern with different flags",
    ),
    ExpressionTestCase(
        "same_pattern_and_flags_equal",
        expression={"$eq": [Regex("^test$", "i"), Regex("^test$", "i")]},
        expected=True,
        msg="Regex equality should hold for identical pattern and flags",
    ),
]


@pytest.mark.parametrize("test", pytest_params(REGEX_COMPARISON_TESTS))
def test_regex_comparison(collection, test):
    """Test Regex BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Regex Round-Trip Fidelity]: Regex values survive insert and
# retrieval unchanged, preserving pattern and flags.
REGEX_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "simple_pattern",
        value=Regex("^hello$", ""),
        expected=Regex("^hello$", ""),
        msg="Simple regex pattern should survive round-trip",
    ),
    RoundTripTestCase(
        "pattern_with_flags",
        value=Regex("test", "ims"),
        expected=Regex("test", "ims"),
        msg="Regex with flags should survive round-trip",
    ),
    RoundTripTestCase(
        "empty_pattern",
        value=Regex("", ""),
        expected=Regex("", ""),
        msg="Empty regex pattern should survive round-trip",
    ),
]


@pytest.mark.parametrize("test", pytest_params(REGEX_ROUND_TRIP_TESTS))
def test_regex_round_trip(collection, test):
    """Test Regex values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
