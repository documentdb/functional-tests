"""
Tests for return type preservation across conditional expressions ($switch, $cond, $ifNull).

Verifies that $switch, $cond, and $ifNull preserve the BSON type of their result expressions.
"""

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
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
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

BSON_VALUES = [
    ("bool", True),
    ("int", 42),
    ("long", Int64(42)),
    ("double", 3.14),
    ("string", "hello"),
    ("null", None),
    ("array", [1, 2, 3]),
    ("object", {"$literal": {"a": 1}}),
    ("date", datetime(2026, 1, 1, tzinfo=timezone.utc)),
    ("decimal", Decimal128("3.14")),
    ("objectId", ObjectId()),
    ("binData", Binary(b"\x00")),
    ("regex", Regex("^abc")),
    ("timestamp", Timestamp(1, 1)),
    ("minKey", MinKey()),
    ("maxKey", MaxKey()),
]

ALL_TESTS = (
    [
        ExpressionTestCase(
            f"switch_then_{name}",
            expression={"$switch": {"branches": [{"case": True, "then": value}]}},
            expected=name,
            msg=f"$switch then should return {name}",
        )
        for name, value in BSON_VALUES
    ]
    + [
        ExpressionTestCase(
            f"switch_default_{name}",
            expression={
                "$switch": {"branches": [{"case": False, "then": "unused"}], "default": value}
            },
            expected=name,
            msg=f"$switch default should return {name}",
        )
        for name, value in BSON_VALUES
    ]
    + [
        ExpressionTestCase(
            f"cond_then_{name}",
            expression={"$cond": {"if": True, "then": value, "else": "unused"}},
            expected=name,
            msg=f"$cond then should return {name}",
        )
        for name, value in BSON_VALUES
    ]
    + [
        ExpressionTestCase(
            f"cond_else_{name}",
            expression={"$cond": {"if": False, "then": "unused", "else": value}},
            expected=name,
            msg=f"$cond else should return {name}",
        )
        for name, value in BSON_VALUES
    ]
    + [
        ExpressionTestCase(
            f"ifNull_non_null_{name}",
            expression={"$ifNull": [value, "fallback"]},
            expected=name,
            msg=f"$ifNull non-null should return {name}",
        )
        for name, value in BSON_VALUES
        if name != "null"
    ]
    + [
        ExpressionTestCase(
            f"ifNull_fallback_{name}",
            expression={"$ifNull": [None, value]},
            expected=name,
            msg=f"$ifNull fallback should return {name}",
        )
        for name, value in BSON_VALUES
    ]
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_conditional_return_type(collection, test):
    """Test conditional expressions preserve return types."""
    result = execute_expression(collection, {"$type": test.expression})
    assert_expression_result(result, expected=test.expected, msg=test.msg)
