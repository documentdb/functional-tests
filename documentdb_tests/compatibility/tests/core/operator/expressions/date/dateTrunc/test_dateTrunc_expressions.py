"""$dateTrunc literal and field-reference inputs, array-path rejection, and return type."""

from datetime import datetime, timezone

import pytest

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
from documentdb_tests.framework.error_codes import INVALID_DATE_VALUE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Literal Input]: $dateTrunc evaluates inline literal arguments.
DATETRUNC_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_basic",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                "unit": "hour",
            }
        },
        expected=datetime(2021, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate an inline literal date",
    ),
    ExpressionTestCase(
        "literal_null",
        expression={"$dateTrunc": {"date": None, "unit": "day"}},
        expected=None,
        msg="$dateTrunc should return null for an inline null date literal",
    ),
]

# Property [Field Reference]: $dateTrunc resolves the date from field references, including a
# nested path, an ObjectId, and a Timestamp.
DATETRUNC_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref",
        doc={"d": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$d", "unit": "day"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should resolve the date from a field reference",
    ),
    ExpressionTestCase(
        "nested_field",
        doc={"doc": {"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)}},
        expression={"$dateTrunc": {"date": "$doc.date", "unit": "day"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should resolve the date from a nested field path",
    ),
    ExpressionTestCase(
        "objectid_field_ref",
        doc={"oid": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$oid", "unit": "day"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should resolve an ObjectId from a field reference",
    ),
    ExpressionTestCase(
        "timestamp_field_ref",
        doc={"ts": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$dateTrunc": {"date": "$ts", "unit": "day"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should resolve a Timestamp from a field reference",
    ),
]

# Property [Missing Optional Field Reference]: a missing field reference for an optional parameter
# yields null.
DATETRUNC_MISSING_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_timezone_field_ref",
        doc={"d": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$d", "unit": "day", "timezone": "$tz"}},
        expected=None,
        msg="$dateTrunc should return null for a missing timezone field reference",
    ),
    ExpressionTestCase(
        "missing_binSize_field_ref",
        doc={"d": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$d", "unit": "hour", "binSize": "$bs"}},
        expected=None,
        msg="$dateTrunc should return null for a missing binSize field reference",
    ),
    ExpressionTestCase(
        "missing_startOfWeek_field_ref",
        doc={"d": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$d", "unit": "week", "startOfWeek": "$sow"}},
        expected=None,
        msg="$dateTrunc should return null for a missing startOfWeek field reference",
    ),
]

# Property [Array Path Rejection]: a field path resolving to an array is rejected as an invalid
# date value.
DATETRUNC_ARRAY_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2021, 6, 15, tzinfo=timezone.utc)},
                {"b": datetime(2021, 7, 1, tzinfo=timezone.utc)},
            ]
        },
        expression={"$dateTrunc": {"date": "$a.b", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a composite array field path",
    ),
    ExpressionTestCase(
        "single_element_array_path",
        doc={"a": [{"b": datetime(2021, 6, 15, 12, 30, 0, tzinfo=timezone.utc)}]},
        expression={"$dateTrunc": {"date": "$a.b", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a single-element array field path",
    ),
]

# Property [Return Type]: $dateTrunc returns the date type regardless of the input date type.
DATETRUNC_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_date",
        expression={
            "$type": {
                "$dateTrunc": {
                    "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                    "unit": "day",
                }
            }
        },
        expected="date",
        msg="$dateTrunc should return the date type for a Date input",
    ),
    ExpressionTestCase(
        "return_type_from_timestamp",
        doc={"ts": ts_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$type": {"$dateTrunc": {"date": "$ts", "unit": "day"}}},
        expected="date",
        msg="$dateTrunc should return the date type for a Timestamp input",
    ),
    ExpressionTestCase(
        "return_type_from_objectid",
        doc={"oid": oid_from_args(2021, 3, 20, 11, 30, 5)},
        expression={"$type": {"$dateTrunc": {"date": "$oid", "unit": "day"}}},
        expected="date",
        msg="$dateTrunc should return the date type for an ObjectId input",
    ),
]

DATETRUNC_EXPRESSION_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_LITERAL_TESTS
    + DATETRUNC_FIELD_REF_TESTS
    + DATETRUNC_MISSING_REF_TESTS
    + DATETRUNC_ARRAY_PATH_TESTS
    + DATETRUNC_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_EXPRESSION_TESTS))
def test_dateTrunc_expressions(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc literal and field-reference handling."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
