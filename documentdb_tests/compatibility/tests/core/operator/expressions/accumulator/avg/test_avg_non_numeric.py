from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.avg.utils.avg_common import (  # noqa: E501
    AvgTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Numeric Ignoring]: non-numeric values in a list are silently
# ignored and excluded from both sum and count.
AVG_NON_NUMERIC_TESTS: list[AvgTest] = [
    AvgTest(
        "nonnumeric_string",
        args=[10, "str", 20],
        expected=15.0,
        msg="$avg should ignore string and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_bool_true",
        args=[10, True, 20],
        expected=15.0,
        msg="$avg should ignore boolean true, not coerce it to 1",
    ),
    AvgTest(
        "nonnumeric_bool_false",
        args=[10, False, 20],
        expected=15.0,
        msg="$avg should ignore boolean false, not coerce it to 0",
    ),
    AvgTest(
        "nonnumeric_object",
        args=[10, {"a": 1}, 20],
        expected=15.0,
        msg="$avg should ignore embedded object and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_objectid",
        args=[10, ObjectId("000000000000000000000001"), 20],
        expected=15.0,
        msg="$avg should ignore ObjectId and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_datetime",
        args=[10, datetime(2020, 1, 1, tzinfo=timezone.utc), 20],
        expected=15.0,
        msg="$avg should ignore datetime and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_datetime_epoch",
        args=[10, datetime(1970, 1, 1, tzinfo=timezone.utc), 20],
        expected=15.0,
        msg="$avg should ignore epoch datetime, not coerce it to 0",
    ),
    AvgTest(
        "nonnumeric_timestamp",
        args=[10, Timestamp(1, 1), 20],
        expected=15.0,
        msg="$avg should ignore Timestamp and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_timestamp_zero",
        args=[10, Timestamp(0, 0), 20],
        expected=15.0,
        msg="$avg should ignore Timestamp(0, 0), not coerce it to 0",
    ),
    AvgTest(
        "nonnumeric_binary",
        args=[10, Binary(b"abc"), 20],
        expected=15.0,
        msg="$avg should ignore Binary and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_regex",
        args=[10, Regex("abc"), 20],
        expected=15.0,
        msg="$avg should ignore Regex and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_minkey",
        args=[10, MinKey(), 20],
        expected=15.0,
        msg="$avg should ignore MinKey and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_maxkey",
        args=[10, MaxKey(), 20],
        expected=15.0,
        msg="$avg should ignore MaxKey and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_code",
        args=[10, Code("function(){}"), 20],
        expected=15.0,
        msg="$avg should ignore JavaScript code and average only numeric values",
    ),
    AvgTest(
        "nonnumeric_code_with_scope",
        args=[10, Code("function(){}", {"x": 1}), 20],
        expected=15.0,
        msg="$avg should ignore JavaScript code with scope and average only numeric values",
    ),
]

# Property [All Non-Numeric Returns Null]: if all values in a list are
# non-numeric the result is null.
AVG_ALL_NON_NUMERIC_TESTS: list[AvgTest] = [
    AvgTest(
        "all_nonnumeric_string",
        args=["hello"],
        expected=None,
        msg="$avg should return null when all operands are strings",
    ),
    AvgTest(
        "all_nonnumeric_bool",
        args=[True, False],
        expected=None,
        msg="$avg should return null when all operands are booleans",
    ),
    AvgTest(
        "all_nonnumeric_object",
        args=[{"a": 1}],
        expected=None,
        msg="$avg should return null when all operands are objects",
    ),
    AvgTest(
        "all_nonnumeric_objectid",
        args=[ObjectId("000000000000000000000001")],
        expected=None,
        msg="$avg should return null when all operands are ObjectIds",
    ),
    AvgTest(
        "all_nonnumeric_datetime",
        args=[datetime(2020, 1, 1, tzinfo=timezone.utc)],
        expected=None,
        msg="$avg should return null when all operands are datetimes",
    ),
    AvgTest(
        "all_nonnumeric_timestamp",
        args=[Timestamp(1, 1)],
        expected=None,
        msg="$avg should return null when all operands are Timestamps",
    ),
    AvgTest(
        "all_nonnumeric_binary",
        args=[Binary(b"abc")],
        expected=None,
        msg="$avg should return null when all operands are Binary",
    ),
    AvgTest(
        "all_nonnumeric_regex",
        args=[Regex("abc")],
        expected=None,
        msg="$avg should return null when all operands are Regex",
    ),
    AvgTest(
        "all_nonnumeric_minkey",
        args=[MinKey()],
        expected=None,
        msg="$avg should return null when all operands are MinKey",
    ),
    AvgTest(
        "all_nonnumeric_maxkey",
        args=[MaxKey()],
        expected=None,
        msg="$avg should return null when all operands are MaxKey",
    ),
    AvgTest(
        "all_nonnumeric_code",
        args=[Code("function(){}")],
        expected=None,
        msg="$avg should return null when all operands are JavaScript code",
    ),
    AvgTest(
        "all_nonnumeric_code_with_scope",
        args=[Code("function(){}", {"x": 1})],
        expected=None,
        msg="$avg should return null when all operands are JavaScript code with scope",
    ),
]

# Property [Non-Numeric Scalar Returns Null]: a single non-numeric scalar
# operand produces null.
AVG_NON_NUMERIC_SCALAR_TESTS: list[AvgTest] = [
    AvgTest(
        "nonnumeric_scalar_string",
        args="hello",
        expected=None,
        msg="$avg should return null for a string scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_bool",
        args=True,
        expected=None,
        msg="$avg should return null for a boolean scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_empty_object",
        args={},
        expected=None,
        msg="$avg should return null for an empty object literal",
    ),
    AvgTest(
        "nonnumeric_scalar_objectid",
        args=ObjectId("000000000000000000000001"),
        expected=None,
        msg="$avg should return null for an ObjectId scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_datetime",
        args=datetime(2020, 1, 1, tzinfo=timezone.utc),
        expected=None,
        msg="$avg should return null for a datetime scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_timestamp",
        args=Timestamp(1, 1),
        expected=None,
        msg="$avg should return null for a Timestamp scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_binary",
        args=Binary(b"abc"),
        expected=None,
        msg="$avg should return null for a Binary scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_regex",
        args=Regex("abc"),
        expected=None,
        msg="$avg should return null for a Regex scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_minkey",
        args=MinKey(),
        expected=None,
        msg="$avg should return null for a MinKey scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_maxkey",
        args=MaxKey(),
        expected=None,
        msg="$avg should return null for a MaxKey scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_code",
        args=Code("function(){}"),
        expected=None,
        msg="$avg should return null for a JavaScript code scalar operand",
    ),
    AvgTest(
        "nonnumeric_scalar_code_with_scope",
        args=Code("function(){}", {"x": 1}),
        expected=None,
        msg="$avg should return null for a JavaScript code with scope scalar operand",
    ),
]

AVG_NON_NUMERIC_ALL_TESTS = (
    AVG_NON_NUMERIC_TESTS + AVG_ALL_NON_NUMERIC_TESTS + AVG_NON_NUMERIC_SCALAR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(AVG_NON_NUMERIC_ALL_TESTS))
def test_avg_non_numeric(collection, test_case: AvgTest):
    """Test $avg cases."""
    result = execute_expression(collection, {"$avg": test_case.args})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
