"""Tests for $dateToParts argument handling and null propagation."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    DATETOPARTS_MISSING_DATE_ERROR,
    DATETOPARTS_NON_OBJECT_ERROR,
    DATETOPARTS_UNKNOWN_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Argument Handling]: the argument is an object holding a required date and
# optional timezone and iso8601, and any other shape is rejected.
DATETOPARTS_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_only",
        doc={"date": datetime(2017, 1, 1, 1, 29, 9, 123000, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2017,
            "month": 1,
            "day": 1,
            "hour": 1,
            "minute": 29,
            "second": 9,
            "millisecond": 123,
        },
        msg="$dateToParts should extract parts from a date alone",
    ),
    ExpressionTestCase(
        "with_tz",
        doc={"date": datetime(2017, 1, 1, 1, 29, 9, 123000, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "timezone": "America/New_York",
            }
        },
        expected={
            "year": 2016,
            "month": 12,
            "day": 31,
            "hour": 20,
            "minute": 29,
            "second": 9,
            "millisecond": 123,
        },
        msg="$dateToParts should apply the timezone when extracting parts",
    ),
    ExpressionTestCase(
        "iso_true",
        doc={"date": datetime(2017, 1, 1, 1, 29, 9, 123000, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "iso8601": True,
            }
        },
        expected={
            "isoWeekYear": 2016,
            "isoWeek": 52,
            "isoDayOfWeek": 7,
            "hour": 1,
            "minute": 29,
            "second": 9,
            "millisecond": 123,
        },
        msg="$dateToParts should return ISO week-date parts when iso8601 is true",
    ),
    ExpressionTestCase(
        "all_fields",
        doc={"date": datetime(2017, 1, 1, 1, 29, 9, 123000, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "timezone": "UTC",
                "iso8601": True,
            }
        },
        expected={
            "isoWeekYear": 2016,
            "isoWeek": 52,
            "isoDayOfWeek": 7,
            "hour": 1,
            "minute": 29,
            "second": 9,
            "millisecond": 123,
        },
        msg="$dateToParts should accept date, timezone, and iso8601 together",
    ),
    ExpressionTestCase(
        "missing_date",
        expression={"$dateToParts": {"timezone": "UTC"}},
        error_code=DATETOPARTS_MISSING_DATE_ERROR,
        msg="$dateToParts should reject an argument that omits the date field",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$dateToParts": {}},
        error_code=DATETOPARTS_MISSING_DATE_ERROR,
        msg="$dateToParts should reject an empty object argument",
    ),
    ExpressionTestCase(
        "unknown_field",
        expression={"$dateToParts": {"date": datetime(2017, 1, 1, tzinfo=timezone.utc), "foo": 1}},
        error_code=DATETOPARTS_UNKNOWN_FIELD_ERROR,
        msg="$dateToParts should reject an unknown field in the argument",
    ),
    ExpressionTestCase(
        "non_object_str",
        expression={"$dateToParts": "string"},
        error_code=DATETOPARTS_NON_OBJECT_ERROR,
        msg="$dateToParts should reject a string argument",
    ),
    ExpressionTestCase(
        "non_object_arr",
        expression={"$dateToParts": [1, 2]},
        error_code=DATETOPARTS_NON_OBJECT_ERROR,
        msg="$dateToParts should reject an array argument",
    ),
    ExpressionTestCase(
        "non_object_num",
        expression={"$dateToParts": 123},
        error_code=DATETOPARTS_NON_OBJECT_ERROR,
        msg="$dateToParts should reject a numeric argument",
    ),
]

# Property [Null Propagation]: a null date, a missing date reference, or a null iso8601 yields null.
DATETOPARTS_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_date",
        doc={"date": None},
        expression={"$dateToParts": {"date": "$date"}},
        expected=None,
        msg="$dateToParts should return null for a null date",
    ),
    ExpressionTestCase(
        "missing_date_ref",
        expression={"$dateToParts": {"date": MISSING}},
        expected=None,
        msg="$dateToParts should return null when the date references a missing field",
    ),
    ExpressionTestCase(
        "iso8601_null",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToParts": {
                "date": "$date",
                "iso8601": None,
            }
        },
        expected=None,
        msg="$dateToParts should return null for a null iso8601",
    ),
]

DATETOPARTS_ARGUMENTS_TESTS: list[ExpressionTestCase] = (
    DATETOPARTS_ARG_TESTS + DATETOPARTS_NULL_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_ARGUMENTS_TESTS))
def test_dateToParts_arguments(collection, test_case: ExpressionTestCase):
    """Test $dateToParts argument handling and null propagation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
