"""$dateDiff date-like operand types: ObjectId, Timestamp, and mixed sources."""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    oid_from_args,
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT64_ZERO,
)

# Property [ObjectId Source]: an ObjectId date operand uses its embedded timestamp for either
# position and for the timezone option.
DATEDIFF_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_day",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0), "e": oid_from_args(2024, 1, 6, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day"}},
        expected=Int64(5),
        msg="$dateDiff should count days between two ObjectId dates",
    ),
    ExpressionTestCase(
        "oid_hour",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(2024, 1, 1, 5, 0, 0, tzinfo=timezone.utc),
                "unit": "hour",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should count hours from an ObjectId startDate",
    ),
    ExpressionTestCase(
        "oid_month",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0), "e": oid_from_args(2024, 6, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(5),
        msg="$dateDiff should count months between two ObjectId dates",
    ),
    ExpressionTestCase(
        "oid_year",
        doc={
            "s": oid_from_args(2024, 1, 1, 0, 0, 0),
            "e": oid_from_args(2024, 12, 31, 23, 59, 59),
        },
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "year"}},
        expected=INT64_ZERO,
        msg="$dateDiff should count zero years within the same ObjectId year",
    ),
    ExpressionTestCase(
        "oid_with_tz",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0), "e": oid_from_args(2024, 1, 6, 0, 0, 0)},
        expression={
            "$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day", "timezone": "UTC"}
        },
        expected=Int64(5),
        msg="$dateDiff should count days between ObjectId dates with a timezone",
    ),
    ExpressionTestCase(
        "oid_negative",
        doc={"s": oid_from_args(2024, 6, 1, 0, 0, 0), "e": oid_from_args(2024, 1, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(-5),
        msg="$dateDiff should return a negative month difference between ObjectId dates",
    ),
    ExpressionTestCase(
        "oid_endDate",
        doc={"e": oid_from_args(2024, 1, 6, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": "$e",
                "unit": "day",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should accept an ObjectId endDate",
    ),
    ExpressionTestCase(
        "oid_epoch",
        doc={"s": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(1970, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should accept an epoch ObjectId startDate",
    ),
    ExpressionTestCase(
        "oid_far_future",
        doc={"s": oid_from_args(2035, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(2035, 6, 1, tzinfo=timezone.utc),
                "unit": "month",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should accept a far-future ObjectId startDate",
    ),
]

# Property [Timestamp Source]: a Timestamp date operand uses its seconds for either position
# and for the timezone option.
DATEDIFF_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_day",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0), "e": ts_from_args(2024, 1, 6, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day"}},
        expected=Int64(5),
        msg="$dateDiff should count days between two Timestamp dates",
    ),
    ExpressionTestCase(
        "ts_hour",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(2024, 1, 1, 5, 0, 0, tzinfo=timezone.utc),
                "unit": "hour",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should count hours from a Timestamp startDate",
    ),
    ExpressionTestCase(
        "ts_month",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0), "e": ts_from_args(2024, 6, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(5),
        msg="$dateDiff should count months between two Timestamp dates",
    ),
    ExpressionTestCase(
        "ts_year",
        doc={
            "s": ts_from_args(2024, 1, 1, 0, 0, 0),
            "e": ts_from_args(2024, 12, 31, 23, 59, 59),
        },
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "year"}},
        expected=INT64_ZERO,
        msg="$dateDiff should count zero years within the same Timestamp year",
    ),
    ExpressionTestCase(
        "ts_with_tz",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0), "e": ts_from_args(2024, 1, 6, 0, 0, 0)},
        expression={
            "$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day", "timezone": "UTC"}
        },
        expected=Int64(5),
        msg="$dateDiff should count days between Timestamp dates with a timezone",
    ),
    ExpressionTestCase(
        "ts_negative",
        doc={"s": ts_from_args(2024, 6, 1, 0, 0, 0), "e": ts_from_args(2024, 1, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(-5),
        msg="$dateDiff should return a negative month difference between Timestamp dates",
    ),
    ExpressionTestCase(
        "ts_epoch",
        doc={"s": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(1970, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should accept an epoch Timestamp startDate",
    ),
    ExpressionTestCase(
        "ts_far_future",
        doc={"s": ts_from_args(2100, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(2100, 6, 1, tzinfo=timezone.utc),
                "unit": "month",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should accept a far-future Timestamp startDate",
    ),
]

# Property [Mixed Source]: ObjectId and Timestamp date operands can be combined.
DATEDIFF_MIXED_SOURCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_ts_mixed",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0), "e": ts_from_args(2024, 1, 6, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day"}},
        expected=Int64(5),
        msg="$dateDiff should count days from an ObjectId startDate to a Timestamp endDate",
    ),
    ExpressionTestCase(
        "ts_oid_mixed",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0), "e": oid_from_args(2024, 6, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(5),
        msg="$dateDiff should count months from a Timestamp startDate to an ObjectId endDate",
    ),
]

DATEDIFF_INPUT_TYPE_TESTS: list[ExpressionTestCase] = (
    DATEDIFF_OBJECTID_TESTS + DATEDIFF_TIMESTAMP_TESTS + DATEDIFF_MIXED_SOURCE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_INPUT_TYPE_TESTS))
def test_dateDiff_input_types(collection, test_case: ExpressionTestCase):
    """Test $dateDiff accepts ObjectId, Timestamp, and mixed date-like operands."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
