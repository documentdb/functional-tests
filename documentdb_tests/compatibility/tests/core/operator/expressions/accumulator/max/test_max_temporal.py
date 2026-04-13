from __future__ import annotations

from datetime import datetime

import pytest
from bson import Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DATE_EPOCH, INT32_MAX

# Property [Datetime Comparison]: datetime values are compared
# chronologically with millisecond precision.
MAX_DATETIME_COMPARISON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "datetime_earlier_vs_later",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DATE_EPOCH, "b": datetime(2024, 6, 15, 12, 0, 0)},
        expected=datetime(2024, 6, 15, 12, 0, 0),
        msg="$max should pick the chronologically later datetime",
    ),
    ExpressionTestCase(
        "datetime_later_vs_earlier",
        expression={"$max": ["$a", "$b"]},
        doc={"a": datetime(2024, 6, 15, 12, 0, 0), "b": DATE_EPOCH},
        expected=datetime(2024, 6, 15, 12, 0, 0),
        msg="$max should pick the later datetime regardless of argument order",
    ),
    ExpressionTestCase(
        "datetime_pre_epoch_vs_epoch",
        expression={"$max": ["$a", "$b"]},
        doc={"a": datetime(1969, 12, 31), "b": DATE_EPOCH},
        expected=DATE_EPOCH,
        msg="$max should pick epoch over pre-epoch datetime",
    ),
    ExpressionTestCase(
        "datetime_pre_epoch_vs_far_future",
        expression={"$max": ["$a", "$b"]},
        doc={"a": datetime(1969, 12, 31), "b": datetime(9999, 12, 31, 23, 59, 59)},
        expected=datetime(9999, 12, 31, 23, 59, 59),
        msg="$max should pick far future over pre-epoch datetime",
    ),
    ExpressionTestCase(
        "datetime_epoch_vs_far_future",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DATE_EPOCH, "b": datetime(9999, 12, 31, 23, 59, 59)},
        expected=datetime(9999, 12, 31, 23, 59, 59),
        msg="$max should pick far future over epoch datetime",
    ),
    ExpressionTestCase(
        "datetime_millis_precision",
        expression={"$max": ["$a", "$b"]},
        doc={
            "a": datetime(2024, 6, 15, 12, 30, 45, 123_000),
            "b": datetime(2024, 6, 15, 12, 30, 45, 124_000),
        },
        expected=datetime(2024, 6, 15, 12, 30, 45, 124_000),
        msg="$max should distinguish datetimes differing by one millisecond",
    ),
    ExpressionTestCase(
        "datetime_millis_precision_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={
            "a": datetime(2024, 6, 15, 12, 30, 45, 124_000),
            "b": datetime(2024, 6, 15, 12, 30, 45, 123_000),
        },
        expected=datetime(2024, 6, 15, 12, 30, 45, 124_000),
        msg="$max should pick the later millisecond-precision datetime regardless of order",
    ),
]

# Property [Timestamp Comparison]: timestamps are compared by time first,
# then by increment.
MAX_TIMESTAMP_COMPARISON_TESTS: list[ExpressionTestCase] = [
    # Different time values, same increment: higher time wins.
    ExpressionTestCase(
        "timestamp_higher_time_wins",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Timestamp(1, 1), "b": Timestamp(2, 1)},
        expected=Timestamp(2, 1),
        msg="$max should pick the timestamp with the higher time value",
    ),
    ExpressionTestCase(
        "timestamp_higher_time_wins_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Timestamp(2, 1), "b": Timestamp(1, 1)},
        expected=Timestamp(2, 1),
        msg="$max should pick the timestamp with the higher time value regardless of order",
    ),
    # Same time, different increments: higher increment wins.
    ExpressionTestCase(
        "timestamp_higher_increment_wins",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Timestamp(5, 1), "b": Timestamp(5, 2)},
        expected=Timestamp(5, 2),
        msg="$max should pick the timestamp with the higher increment when times are equal",
    ),
    ExpressionTestCase(
        "timestamp_higher_increment_wins_reversed",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Timestamp(5, 2), "b": Timestamp(5, 1)},
        expected=Timestamp(5, 2),
        msg="$max should pick the timestamp with the higher increment regardless of order",
    ),
    # Boundary: max signed 32-bit time.
    ExpressionTestCase(
        "timestamp_max_signed_time",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Timestamp(INT32_MAX, 1), "b": Timestamp(1, 1)},
        expected=Timestamp(INT32_MAX, 1),
        msg="$max should handle max signed 32-bit time value correctly",
    ),
    # Boundary: max unsigned 32-bit time (4_294_967_295).
    ExpressionTestCase(
        "timestamp_max_unsigned_time",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Timestamp(4_294_967_295, 1), "b": Timestamp(INT32_MAX, 1)},
        expected=Timestamp(4_294_967_295, 1),
        msg="$max should handle max unsigned 32-bit time value correctly",
    ),
    # Boundary: max unsigned 32-bit increment (4_294_967_295).
    ExpressionTestCase(
        "timestamp_max_unsigned_increment",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Timestamp(1, 4_294_967_295), "b": Timestamp(1, 1)},
        expected=Timestamp(1, 4_294_967_295),
        msg="$max should handle max unsigned 32-bit increment value correctly",
    ),
    # Time takes priority over increment.
    ExpressionTestCase(
        "timestamp_time_priority_over_increment",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Timestamp(1, 4_294_967_295), "b": Timestamp(2, 1)},
        expected=Timestamp(2, 1),
        msg="$max should compare time before increment",
    ),
]

MAX_TEMPORAL_TESTS = MAX_DATETIME_COMPARISON_TESTS + MAX_TIMESTAMP_COMPARISON_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MAX_TEMPORAL_TESTS))
def test_max_temporal_cases(collection, test_case: ExpressionTestCase):
    """Test $max temporal comparison cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
