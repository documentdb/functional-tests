"""Tests for $add date arithmetic including numeric offsets, rounding boundaries, operand
position, and sign handling.
"""

from datetime import datetime, timedelta, timezone

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Date Arithmetic]: $add accepts exactly one date operand and one or more numeric
# operands (in milliseconds). The date may appear in any position.
ADD_DATE_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_int32",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 86400000},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 2, tzinfo=timezone.utc),
        msg="$add should add int32 milliseconds to a date",
    ),
    ExpressionTestCase(
        "date_int64",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": Int64(86400000)},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 2, tzinfo=timezone.utc),
        msg="$add should add int64 milliseconds to a date",
    ),
    ExpressionTestCase(
        "date_decimal",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": Decimal128("1.5")},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 2000, tzinfo=timezone.utc),
        msg="$add should round a decimal128 fractional millisecond value when adding to a date",
    ),
    ExpressionTestCase(
        "date_double_round_up",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 2.5},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 3000, tzinfo=timezone.utc),
        msg="$add should round up a double fractional millisecond value (.5) when adding to a date",
    ),
    ExpressionTestCase(
        "date_double_truncates",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 4.4},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 4000, tzinfo=timezone.utc),
        msg="$add should truncate a double fractional millisecond value (<.5) when adding to a date",  # noqa: E501
    ),
]

# Property [Date Rounding Boundaries]: $add rounds fractional millisecond offsets using
# round-half-away-from-zero. Values with |frac| < 0.5 truncate toward zero; values with
# |frac| >= 0.5 round away from zero.
ADD_DATE_ROUNDING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_double_0_1",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 0.1},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, tzinfo=timezone.utc),
        msg="$add should truncate 0.1ms and leave the date unchanged",
    ),
    ExpressionTestCase(
        "date_double_0_49",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 0.49},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, tzinfo=timezone.utc),
        msg="$add should truncate 0.49ms and leave the date unchanged",
    ),
    ExpressionTestCase(
        "date_double_0_51",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 0.51},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
        msg="$add should round up 0.51ms to 1ms when adding to a date",
    ),
    ExpressionTestCase(
        "date_double_0_6",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 0.6},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
        msg="$add should round up 0.6ms to 1ms when adding to a date",
    ),
    ExpressionTestCase(
        "date_double_neg_0_5",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": -0.5},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, tzinfo=timezone.utc) - timedelta(milliseconds=1),
        msg="$add should round -0.5ms away from zero to -1ms when adding to a date",
    ),
    ExpressionTestCase(
        "date_double_neg_0_51",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": -0.51},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, tzinfo=timezone.utc) - timedelta(milliseconds=1),
        msg="$add should round -0.51ms away from zero to -1ms when adding to a date",
    ),
]

# Property [Date Operand Position]: the date operand may appear in any position among the
# operands; only one date is permitted.
ADD_DATE_POSITION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "number_then_date",
        doc={"a": 86400000, "b": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 2, tzinfo=timezone.utc),
        msg="$add should add a date when the numeric operand appears before the date",
    ),
    ExpressionTestCase(
        "date_in_middle",
        doc={"a": 1, "b": datetime(2026, 1, 1, tzinfo=timezone.utc), "c": 1000},
        expression={"$add": ["$a", "$b", "$c"]},
        expected=datetime(2026, 1, 1, 0, 0, 1, 1000, tzinfo=timezone.utc),
        msg="$add should add a date when it appears in the middle of the operand list",
    ),
]

# Property [Date Sign Handling]: adding zero or a negative number of milliseconds to a date
# returns the date unchanged or subtracted.
ADD_DATE_SIGN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_negative",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": -86400000},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2025, 12, 31, tzinfo=timezone.utc),
        msg="$add should subtract milliseconds from a date when adding a negative number",
    ),
    ExpressionTestCase(
        "date_zero",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 0},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, tzinfo=timezone.utc),
        msg="$add should return the same date when adding zero milliseconds",
    ),
    ExpressionTestCase(
        "date_negative_zero",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": -0.0},
        expression={"$add": ["$a", "$b"]},
        expected=datetime(2026, 1, 1, tzinfo=timezone.utc),
        msg="$add should return the same date when adding negative zero",
    ),
]

ADD_DATE_ALL_TESTS = (
    ADD_DATE_NUMERIC_TESTS + ADD_DATE_POSITION_TESTS + ADD_DATE_SIGN_TESTS + ADD_DATE_ROUNDING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ADD_DATE_ALL_TESTS))
def test_add_date(collection, test_case: ExpressionTestCase):
    """Test $add date arithmetic: numeric types, operand position, and sign handling."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
