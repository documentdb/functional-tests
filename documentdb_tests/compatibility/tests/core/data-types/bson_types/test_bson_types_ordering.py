from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
    DOUBLE_ZERO,
    INT64_ZERO,
)

# Property [Adjacent Type Order]: each BSON type sorts immediately before the
# next type in the canonical order MinKey < Null < Number < String < Object <
# Array < BinData < ObjectId < Bool < Date < Timestamp < Regex < JavaScript <
# MaxKey.
ADJACENT_TYPE_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "minkey_lt_null",
        expression={"$lt": [MinKey(), None]},
        expected=True,
        msg="BSON ordering should place MinKey before null",
    ),
    ExpressionTestCase(
        "null_lt_int",
        expression={"$lt": [None, 0]},
        expected=True,
        msg="BSON ordering should place null before int32",
    ),
    ExpressionTestCase(
        "null_lt_long",
        expression={"$lt": [None, INT64_ZERO]},
        expected=True,
        msg="BSON ordering should place null before Int64",
    ),
    ExpressionTestCase(
        "null_lt_double",
        expression={"$lt": [None, DOUBLE_ZERO]},
        expected=True,
        msg="BSON ordering should place null before double",
    ),
    ExpressionTestCase(
        "null_lt_decimal128",
        expression={"$lt": [None, DECIMAL128_ZERO]},
        expected=True,
        msg="BSON ordering should place null before Decimal128",
    ),
    ExpressionTestCase(
        "int_lt_string",
        expression={"$lt": [0, ""]},
        expected=True,
        msg="BSON ordering should place int32 before string",
    ),
    ExpressionTestCase(
        "long_lt_string",
        expression={"$lt": [INT64_ZERO, ""]},
        expected=True,
        msg="BSON ordering should place Int64 before string",
    ),
    ExpressionTestCase(
        "double_lt_string",
        expression={"$lt": [DOUBLE_ZERO, ""]},
        expected=True,
        msg="BSON ordering should place double before string",
    ),
    ExpressionTestCase(
        "decimal128_lt_string",
        expression={"$lt": [DECIMAL128_ZERO, ""]},
        expected=True,
        msg="BSON ordering should place Decimal128 before string",
    ),
    ExpressionTestCase(
        "string_lt_object",
        expression={"$lt": ["", {}]},
        expected=True,
        msg="BSON ordering should place string before object",
    ),
    ExpressionTestCase(
        "object_lt_array",
        expression={"$lt": [{}, []]},
        expected=True,
        msg="BSON ordering should place object before array",
    ),
    ExpressionTestCase(
        "array_lt_bindata",
        expression={"$lt": [[], Binary(b"", 0)]},
        expected=True,
        msg="BSON ordering should place array before BinData",
    ),
    ExpressionTestCase(
        "bindata_lt_objectid",
        expression={"$lt": [Binary(b"", 0), ObjectId("000000000000000000000000")]},
        expected=True,
        msg="BSON ordering should place BinData before ObjectId",
    ),
    ExpressionTestCase(
        "objectid_lt_bool",
        expression={"$lt": [ObjectId("000000000000000000000000"), False]},
        expected=True,
        msg="BSON ordering should place ObjectId before bool",
    ),
    ExpressionTestCase(
        "bool_lt_date",
        expression={"$lt": [False, datetime(1970, 1, 1, tzinfo=timezone.utc)]},
        expected=True,
        msg="BSON ordering should place bool before date",
    ),
    ExpressionTestCase(
        "date_lt_timestamp",
        expression={"$lt": [datetime(1970, 1, 1, tzinfo=timezone.utc), Timestamp(0, 0)]},
        expected=True,
        msg="BSON ordering should place date before Timestamp",
    ),
    ExpressionTestCase(
        "timestamp_lt_regex",
        expression={"$lt": [Timestamp(0, 0), Regex("a")]},
        expected=True,
        msg="BSON ordering should place Timestamp before regex",
    ),
    ExpressionTestCase(
        "regex_lt_javascript",
        expression={"$lt": [Regex("a"), Code("f")]},
        expected=True,
        msg="BSON ordering should place regex before JavaScript code",
    ),
    ExpressionTestCase(
        "javascript_lt_maxkey",
        expression={"$lt": [Code("f"), MaxKey()]},
        expected=True,
        msg="BSON ordering should place JavaScript code before MaxKey",
    ),
]

# Property [Non-Adjacent Type Order]: cross-type ordering is transitive, so a
# type sorts before every type that appears later in the canonical order, not
# only its immediate successor.
NON_ADJACENT_TYPE_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_lt_object",
        expression={"$lt": [None, {}]},
        expected=True,
        msg="BSON ordering should place null before object across intervening types",
    ),
    ExpressionTestCase(
        "int_lt_bindata",
        expression={"$lt": [0, Binary(b"", 0)]},
        expected=True,
        msg="BSON ordering should place number before BinData across intervening types",
    ),
    ExpressionTestCase(
        "string_lt_timestamp",
        expression={"$lt": ["", Timestamp(0, 0)]},
        expected=True,
        msg="BSON ordering should place string before Timestamp across intervening types",
    ),
    ExpressionTestCase(
        "minkey_lt_maxkey",
        expression={"$lt": [MinKey(), MaxKey()]},
        expected=True,
        msg="BSON ordering should place MinKey before MaxKey at the extremes",
    ),
]

TYPE_ORDERING_TESTS = ADJACENT_TYPE_ORDERING_TESTS + NON_ADJACENT_TYPE_ORDERING_TESTS


@pytest.mark.parametrize("test", pytest_params(TYPE_ORDERING_TESTS))
def test_bson_types_ordering(collection, test):
    """Test cross-type BSON comparison order."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
