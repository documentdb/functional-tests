"""Tests for $dateToString format handling, specifiers, padding, and the default format."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    DATETOSTRING_INVALID_FORMAT_ERROR,
    DATETOSTRING_INVALID_FORMAT_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Format Validation]: a literal format is emitted verbatim, and an unsupported specifier
# or a non-string format is rejected.
DATETOSTRING_FORMAT_VALIDATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "format_empty",
        doc={"format": ""},
        expression={
            "$dateToString": {
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "format": "$format",
            }
        },
        expected="",
        msg="$dateToString should return an empty string for an empty format",
    ),
    ExpressionTestCase(
        "format_no_spec",
        doc={"format": "hello"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "format": "$format",
            }
        },
        expected="hello",
        msg="$dateToString should emit a format with no specifiers verbatim",
    ),
    ExpressionTestCase(
        "format_percent",
        doc={"format": "100%%"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "format": "$format",
            }
        },
        expected="100%",
        msg="$dateToString should emit a literal percent for %%",
    ),
    ExpressionTestCase(
        "format_invalid_spec",
        doc={"format": "%x"},
        expression={
            "$dateToString": {
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "format": "$format",
            }
        },
        error_code=DATETOSTRING_INVALID_FORMAT_ERROR,
        msg="$dateToString should reject an unsupported format specifier",
    ),
    ExpressionTestCase(
        "format_number",
        doc={"format": 123},
        expression={
            "$dateToString": {
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "format": "$format",
            }
        },
        error_code=DATETOSTRING_INVALID_FORMAT_TYPE_ERROR,
        msg="$dateToString should reject a numeric format",
    ),
    ExpressionTestCase(
        "format_boolean",
        doc={"format": True},
        expression={
            "$dateToString": {
                "date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "format": "$format",
            }
        },
        error_code=DATETOSTRING_INVALID_FORMAT_TYPE_ERROR,
        msg="$dateToString should reject a boolean format",
    ),
]

# Property [Format Specifiers]: each supported conversion specifier formats its component correctly.
DATETOSTRING_FORMAT_SPECIFIER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"spec_{name}",
        doc={"date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date", "format": fmt}},
        expected=expected,
        msg=f"$dateToString should format the {name} specifier",
    )
    for name, fmt, expected in [
        ("Y", "%Y", "2024"),
        ("m", "%m", "06"),
        ("d", "%d", "15"),
        ("H", "%H", "10"),
        ("M", "%M", "30"),
        ("S", "%S", "45"),
        ("L", "%L", "123"),
        ("j", "%j", "167"),
        ("u", "%u", "6"),
        ("w", "%w", "7"),
        ("pct", "%%", "%"),
        ("G", "%G", "2024"),
        ("V", "%V", "24"),
        ("U", "%U", "23"),
        ("b", "%b", "Jun"),
        ("B", "%B", "June"),
    ]
]

# Property [Zero Padding]: single-digit components are zero-padded to their fixed width.
DATETOSTRING_PADDING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"pad_{name}",
        doc={"date": date},
        expression={"$dateToString": {"date": "$date", "format": fmt}},
        expected=expected,
        msg=f"$dateToString should zero-pad the {name} specifier",
    )
    for name, date, fmt, expected in [
        ("d", datetime(2024, 1, 5, 0, 0, 0, tzinfo=timezone.utc), "%d", "05"),
        ("m", datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc), "%m", "03"),
        ("H", datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc), "%H", "08"),
        ("M", datetime(2024, 1, 1, 0, 5, 0, tzinfo=timezone.utc), "%M", "05"),
        ("S", datetime(2024, 1, 1, 0, 0, 3, tzinfo=timezone.utc), "%S", "03"),
        ("L", datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc), "%L", "001"),
        ("j", datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc), "%j", "001"),
    ]
]

# Property [Timezone Specifiers]: the %z and %Z specifiers emit the offset of the given timezone.
DATETOSTRING_TZ_SPECIFIER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "spec_z",
        doc={"date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date", "format": "%z", "timezone": "UTC"}},
        expected="+0000",
        msg="$dateToString should format the %z specifier as a numeric offset",
    ),
    ExpressionTestCase(
        "spec_Z",
        doc={"date": datetime(2024, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date", "format": "%Z", "timezone": "UTC"}},
        expected="0",
        msg="$dateToString should format the %Z specifier as an offset in minutes",
    ),
]

# Property [Default Format]: with no format, the ISO representation reflects the applied timezone.
DATETOSTRING_DEFAULT_FORMAT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "default_utc",
        doc={"date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date"}},
        expected="2024-01-01T12:00:00.000Z",
        msg="$dateToString should use the ISO default format with a trailing Z for UTC",
    ),
    ExpressionTestCase(
        "default_utc_tz",
        doc={"date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "timezone": "UTC",
            }
        },
        expected="2024-01-01T12:00:00.000Z",
        msg="$dateToString should keep the trailing Z when the timezone is UTC",
    ),
    ExpressionTestCase(
        "default_non_utc",
        doc={"date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateToString": {
                "date": "$date",
                "timezone": "America/New_York",
            }
        },
        expected="2024-01-01T07:00:00.000",
        msg="$dateToString should drop the trailing Z for a non-UTC timezone",
    ),
]

DATETOSTRING_FORMAT_TESTS: list[ExpressionTestCase] = (
    DATETOSTRING_FORMAT_VALIDATION_TESTS
    + DATETOSTRING_FORMAT_SPECIFIER_TESTS
    + DATETOSTRING_PADDING_TESTS
    + DATETOSTRING_TZ_SPECIFIER_TESTS
    + DATETOSTRING_DEFAULT_FORMAT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_FORMAT_TESTS))
def test_dateToString_format(collection, test_case: ExpressionTestCase):
    """Test $dateToString format handling and specifiers."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
