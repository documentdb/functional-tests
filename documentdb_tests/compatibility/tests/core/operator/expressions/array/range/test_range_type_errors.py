"""
Type error tests for $range expression.

Tests non-numeric types for start, end, and step positions.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    RANGE_END_NOT_NUMERIC_ERROR,
    RANGE_START_NOT_INT32_ERROR,
    RANGE_STEP_NOT_NUMERIC_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Numeric Start]: $range rejects non-numeric types for start.
NON_NUMERIC_START_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_start",
        doc={"start": "hello", "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject string start",
    ),
    ExpressionTestCase(
        "bool_start",
        doc={"start": True, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject bool start",
    ),
    ExpressionTestCase(
        "null_start",
        doc={"start": None, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject null start",
    ),
    ExpressionTestCase(
        "object_start",
        doc={"start": {"a": 1}, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject object start",
    ),
    ExpressionTestCase(
        "array_start",
        doc={"start": [1], "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject array start",
    ),
    ExpressionTestCase(
        "objectid_start",
        doc={"start": ObjectId(), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject objectid start",
    ),
    ExpressionTestCase(
        "datetime_start",
        doc={"start": datetime(2024, 1, 1, tzinfo=timezone.utc), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject datetime start",
    ),
    ExpressionTestCase(
        "binary_start",
        doc={"start": Binary(b"x", 0), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject binary start",
    ),
    ExpressionTestCase(
        "regex_start",
        doc={"start": Regex("x"), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject regex start",
    ),
    ExpressionTestCase(
        "maxkey_start",
        doc={"start": MaxKey(), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject maxkey start",
    ),
    ExpressionTestCase(
        "minkey_start",
        doc={"start": MinKey(), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject minkey start",
    ),
    ExpressionTestCase(
        "timestamp_start",
        doc={"start": Timestamp(0, 0), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range should reject timestamp start",
    ),
]

# Property [Non-Numeric End]: $range rejects non-numeric types for end.
NON_NUMERIC_END_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_end",
        doc={"start": 0, "end": "hello"},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject string end",
    ),
    ExpressionTestCase(
        "bool_end",
        doc={"start": 0, "end": True},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject bool end",
    ),
    ExpressionTestCase(
        "null_end",
        doc={"start": 0, "end": None},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject null end",
    ),
    ExpressionTestCase(
        "object_end",
        doc={"start": 0, "end": {"a": 1}},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject object end",
    ),
    ExpressionTestCase(
        "array_end",
        doc={"start": 0, "end": [1]},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject array end",
    ),
    ExpressionTestCase(
        "objectid_end",
        doc={"start": 0, "end": ObjectId()},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject objectid end",
    ),
    ExpressionTestCase(
        "datetime_end",
        doc={"start": 0, "end": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject datetime end",
    ),
    ExpressionTestCase(
        "binary_end",
        doc={"start": 0, "end": Binary(b"x", 0)},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject binary end",
    ),
    ExpressionTestCase(
        "regex_end",
        doc={"start": 0, "end": Regex("x")},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject regex end",
    ),
    ExpressionTestCase(
        "maxkey_end",
        doc={"start": 0, "end": MaxKey()},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject maxkey end",
    ),
    ExpressionTestCase(
        "minkey_end",
        doc={"start": 0, "end": MinKey()},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject minkey end",
    ),
    ExpressionTestCase(
        "timestamp_end",
        doc={"start": 0, "end": Timestamp(0, 0)},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range should reject timestamp end",
    ),
]

# Property [Non-Numeric Step]: $range rejects non-numeric types for step.
NON_NUMERIC_STEP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_step",
        doc={"start": 0, "end": 5, "step": "bad"},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject string step",
    ),
    ExpressionTestCase(
        "bool_step",
        doc={"start": 0, "end": 5, "step": True},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject bool step",
    ),
    ExpressionTestCase(
        "object_step",
        doc={"start": 0, "end": 5, "step": {"a": 1}},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject object step",
    ),
    ExpressionTestCase(
        "array_step",
        doc={"start": 0, "end": 5, "step": [1]},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject array step",
    ),
    ExpressionTestCase(
        "objectid_step",
        doc={"start": 0, "end": 5, "step": ObjectId()},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject objectid step",
    ),
    ExpressionTestCase(
        "datetime_step",
        doc={"start": 0, "end": 5, "step": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject datetime step",
    ),
    ExpressionTestCase(
        "binary_step",
        doc={"start": 0, "end": 5, "step": Binary(b"x", 0)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject binary step",
    ),
    ExpressionTestCase(
        "regex_step",
        doc={"start": 0, "end": 5, "step": Regex("x")},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject regex step",
    ),
    ExpressionTestCase(
        "maxkey_step",
        doc={"start": 0, "end": 5, "step": MaxKey()},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject maxkey step",
    ),
    ExpressionTestCase(
        "minkey_step",
        doc={"start": 0, "end": 5, "step": MinKey()},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject minkey step",
    ),
    ExpressionTestCase(
        "timestamp_step",
        doc={"start": 0, "end": 5, "step": Timestamp(0, 0)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range should reject timestamp step",
    ),
]

ALL_TESTS = NON_NUMERIC_START_TESTS + NON_NUMERIC_END_TESTS + NON_NUMERIC_STEP_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_range_type_error(collection, test):
    """Test $range error with non-numeric types for start, end, step."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
