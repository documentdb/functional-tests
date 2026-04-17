from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Numeric Handling]: $sum skips non-numeric values (strings,
# booleans, dates, etc.) and sums only the numeric elements.
SUM_NONNUMERIC_SOLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nonnumeric_string_sole",
        expression={"$sum": "$a"},
        doc={"a": "hello"},
        expected=0,
        msg="$sum should return 0 when sole operand is a string",
    ),
    ExpressionTestCase(
        "nonnumeric_numeric_looking_string_sole",
        expression={"$sum": "$a"},
        doc={"a": "42"},
        expected=0,
        msg="$sum should not coerce numeric-looking string '42' to a number",
    ),
    ExpressionTestCase(
        "nonnumeric_bool_true_sole",
        expression={"$sum": "$a"},
        doc={"a": True},
        expected=0,
        msg="$sum should return 0 when sole operand is boolean true",
    ),
    ExpressionTestCase(
        "nonnumeric_bool_false_sole",
        expression={"$sum": "$a"},
        doc={"a": False},
        expected=0,
        msg="$sum should return 0 when sole operand is boolean false",
    ),
    ExpressionTestCase(
        "nonnumeric_object_sole",
        expression={"$sum": "$a"},
        doc={"a": {"x": 1}},
        expected=0,
        msg="$sum should return 0 when sole operand is an object",
    ),
    ExpressionTestCase(
        "nonnumeric_objectid_sole",
        expression={"$sum": "$a"},
        doc={"a": ObjectId("000000000000000000000001")},
        expected=0,
        msg="$sum should return 0 when sole operand is an ObjectId",
    ),
    ExpressionTestCase(
        "nonnumeric_datetime_sole",
        expression={"$sum": "$a"},
        doc={"a": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        expected=0,
        msg="$sum should return 0 when sole operand is a datetime",
    ),
    ExpressionTestCase(
        "nonnumeric_timestamp_sole",
        expression={"$sum": "$a"},
        doc={"a": Timestamp(1_234_567_890, 1)},
        expected=0,
        msg="$sum should return 0 when sole operand is a Timestamp",
    ),
    ExpressionTestCase(
        "nonnumeric_binary_sole",
        expression={"$sum": "$a"},
        doc={"a": Binary(b"\x01\x02")},
        expected=0,
        msg="$sum should return 0 when sole operand is a Binary",
    ),
    ExpressionTestCase(
        "nonnumeric_regex_sole",
        expression={"$sum": "$a"},
        doc={"a": Regex("abc")},
        expected=0,
        msg="$sum should return 0 when sole operand is a Regex",
    ),
    ExpressionTestCase(
        "nonnumeric_minkey_sole",
        expression={"$sum": "$a"},
        doc={"a": MinKey()},
        expected=0,
        msg="$sum should return 0 when sole operand is MinKey",
    ),
    ExpressionTestCase(
        "nonnumeric_maxkey_sole",
        expression={"$sum": "$a"},
        doc={"a": MaxKey()},
        expected=0,
        msg="$sum should return 0 when sole operand is MaxKey",
    ),
    ExpressionTestCase(
        "nonnumeric_array_sole",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": [1, 2], "b": [3, 4]},
        expected=0,
        msg="$sum should return 0 when all list elements are arrays (non-numeric)",
    ),
    ExpressionTestCase(
        "nonnumeric_code_sole",
        expression={"$sum": "$a"},
        doc={"a": Code("function(){}")},
        expected=0,
        msg="$sum should return 0 when sole operand is JavaScript Code",
    ),
    ExpressionTestCase(
        "nonnumeric_code_with_scope_sole",
        expression={"$sum": "$a"},
        doc={"a": Code("function(){}", {"x": 1})},
        expected=0,
        msg="$sum should return 0 when sole operand is Code with scope",
    ),
]

# Property [Non-Numeric - Exclusion]: non-numeric values among numeric operands are ignored.
SUM_NONNUMERIC_EXCLUSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nonnumeric_bool_true_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": True, "b": 1},
        expected=1,
        msg="$sum should ignore boolean true and not coerce it to 1",
    ),
    ExpressionTestCase(
        "nonnumeric_bool_false_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": False, "b": 3},
        expected=3,
        msg="$sum should ignore boolean false and not coerce it to 0",
    ),
    ExpressionTestCase(
        "nonnumeric_string_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": "hello", "b": 5},
        expected=5,
        msg="$sum should ignore string and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_object_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": {"x": 1}, "b": 4},
        expected=4,
        msg="$sum should ignore object and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_objectid_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": ObjectId("000000000000000000000001"), "b": 6},
        expected=6,
        msg="$sum should ignore ObjectId and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_datetime_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": datetime(2023, 1, 1, tzinfo=timezone.utc), "b": 10},
        expected=10,
        msg="$sum should ignore datetime and not coerce it to milliseconds",
    ),
    ExpressionTestCase(
        "nonnumeric_timestamp_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Timestamp(1_234_567_890, 1), "b": 7},
        expected=7,
        msg="$sum should ignore Timestamp and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_binary_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Binary(b"\x01\x02"), "b": 9},
        expected=9,
        msg="$sum should ignore Binary and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_regex_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Regex("abc"), "b": 2},
        expected=2,
        msg="$sum should ignore Regex and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_code_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Code("function(){}"), "b": 8},
        expected=8,
        msg="$sum should ignore Code and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_code_with_scope_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Code("function(){}", {"x": 1}), "b": 11},
        expected=11,
        msg="$sum should ignore Code with scope and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_minkey_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": MinKey(), "b": 12},
        expected=12,
        msg="$sum should ignore MinKey and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_maxkey_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": MaxKey(), "b": 13},
        expected=13,
        msg="$sum should ignore MaxKey and sum remaining numeric values",
    ),
    ExpressionTestCase(
        "nonnumeric_array_with_num",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": [1, 2, 3], "b": 10},
        expected=10,
        msg="$sum should treat array as non-numeric in list-of-expressions form",
    ),
]

# Property [Non-Numeric - Reverse Order]: non-numeric values are ignored regardless of
# operand position.
SUM_NONNUMERIC_REVERSE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nonnumeric_num_with_bool_true",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 1, "b": True},
        expected=1,
        msg="$sum should ignore trailing boolean true",
    ),
    ExpressionTestCase(
        "nonnumeric_num_with_string",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 5, "b": "hello"},
        expected=5,
        msg="$sum should ignore trailing string",
    ),
    ExpressionTestCase(
        "nonnumeric_num_with_object",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 4, "b": {"x": 1}},
        expected=4,
        msg="$sum should ignore trailing object",
    ),
    ExpressionTestCase(
        "nonnumeric_num_with_datetime",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 10, "b": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        expected=10,
        msg="$sum should ignore trailing datetime",
    ),
]

SUM_NONNUMERIC_TESTS = (
    SUM_NONNUMERIC_SOLE_TESTS + SUM_NONNUMERIC_EXCLUSION_TESTS + SUM_NONNUMERIC_REVERSE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_NONNUMERIC_TESTS))
def test_sum_non_numeric(collection, test_case: ExpressionTestCase):
    """Test $sum non-numeric handling."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
