"""$dateTrunc optional-argument acceptance: required plus optional fields and binSize types."""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Argument Handling]: $dateTrunc accepts the required date and unit plus the optional
# binSize, timezone, and startOfWeek parameters.
DATETRUNC_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arg_required_only",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour"}},
        expected=datetime(2021, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate with the required fields only",
    ),
    ExpressionTestCase(
        "arg_with_binSize",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "binSize": 2}},
        expected=datetime(2021, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a binSize",
    ),
    ExpressionTestCase(
        "arg_with_timezone",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "UTC"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a timezone",
    ),
    ExpressionTestCase(
        "arg_with_startOfWeek",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "monday"}},
        expected=datetime(2021, 3, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a startOfWeek",
    ),
    ExpressionTestCase(
        "arg_all_fields",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={
            "$dateTrunc": {
                "date": "$date",
                "unit": "week",
                "binSize": 1,
                "timezone": "UTC",
                "startOfWeek": "monday",
            }
        },
        expected=datetime(2021, 3, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept all fields together",
    ),
]

# Property [BinSize Numeric Types]: integral int64, decimal128, and double binSize values are
# accepted.
DATETRUNC_BINSIZE_ACCEPT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binSize_int64",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "binSize": Int64(2)}},
        expected=datetime(2021, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an int64 binSize",
    ),
    ExpressionTestCase(
        "binSize_decimal128",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "binSize": Decimal128("2")}},
        expected=datetime(2021, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a decimal128 binSize",
    ),
    ExpressionTestCase(
        "binSize_double_integral",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "binSize": 2.0}},
        expected=datetime(2021, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an integral double binSize",
    ),
]

DATETRUNC_ARGUMENT_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_ARG_TESTS + DATETRUNC_BINSIZE_ACCEPT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_ARGUMENT_TESTS))
def test_dateTrunc_arguments(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc accepts its optional arguments and numeric binSize types."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
