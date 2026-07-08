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

# Error: non-numeric start
NON_NUMERIC_START_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_start",
        doc={"start": "hello", "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject string start",
    ),
    ExpressionTestCase(
        id="bool_start",
        doc={"start": True, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject bool start",
    ),
    ExpressionTestCase(
        id="null_start",
        doc={"start": None, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject null start",
    ),
    ExpressionTestCase(
        id="object_start",
        doc={"start": {"a": 1}, "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject object start",
    ),
    ExpressionTestCase(
        id="array_start",
        doc={"start": [1], "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject array start",
    ),
    ExpressionTestCase(
        id="objectid_start",
        doc={"start": ObjectId(), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject objectid start",
    ),
    ExpressionTestCase(
        id="datetime_start",
        doc={"start": datetime(2024, 1, 1, tzinfo=timezone.utc), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject datetime start",
    ),
    ExpressionTestCase(
        id="binary_start",
        doc={"start": Binary(b"x", 0), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject binary start",
    ),
    ExpressionTestCase(
        id="regex_start",
        doc={"start": Regex("x"), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject regex start",
    ),
    ExpressionTestCase(
        id="maxkey_start",
        doc={"start": MaxKey(), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject maxkey start",
    ),
    ExpressionTestCase(
        id="minkey_start",
        doc={"start": MinKey(), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject minkey start",
    ),
    ExpressionTestCase(
        id="timestamp_start",
        doc={"start": Timestamp(0, 0), "end": 5},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Should reject timestamp start",
    ),
]

# Error: non-numeric end
NON_NUMERIC_END_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_end",
        doc={"start": 0, "end": "hello"},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject string end",
    ),
    ExpressionTestCase(
        id="bool_end",
        doc={"start": 0, "end": True},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject bool end",
    ),
    ExpressionTestCase(
        id="null_end",
        doc={"start": 0, "end": None},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject null end",
    ),
    ExpressionTestCase(
        id="object_end",
        doc={"start": 0, "end": {"a": 1}},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject object end",
    ),
    ExpressionTestCase(
        id="array_end",
        doc={"start": 0, "end": [1]},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject array end",
    ),
    ExpressionTestCase(
        id="objectid_end",
        doc={"start": 0, "end": ObjectId()},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject objectid end",
    ),
    ExpressionTestCase(
        id="datetime_end",
        doc={"start": 0, "end": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject datetime end",
    ),
    ExpressionTestCase(
        id="binary_end",
        doc={"start": 0, "end": Binary(b"x", 0)},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject binary end",
    ),
    ExpressionTestCase(
        id="regex_end",
        doc={"start": 0, "end": Regex("x")},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject regex end",
    ),
    ExpressionTestCase(
        id="maxkey_end",
        doc={"start": 0, "end": MaxKey()},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject maxkey end",
    ),
    ExpressionTestCase(
        id="minkey_end",
        doc={"start": 0, "end": MinKey()},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject minkey end",
    ),
    ExpressionTestCase(
        id="timestamp_end",
        doc={"start": 0, "end": Timestamp(0, 0)},
        expression={"$range": ["$start", "$end"]},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Should reject timestamp end",
    ),
]

# Error: non-numeric step
NON_NUMERIC_STEP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="string_step",
        doc={"start": 0, "end": 5, "step": "bad"},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject string step",
    ),
    ExpressionTestCase(
        id="bool_step",
        doc={"start": 0, "end": 5, "step": True},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject bool step",
    ),
    ExpressionTestCase(
        id="object_step",
        doc={"start": 0, "end": 5, "step": {"a": 1}},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject object step",
    ),
    ExpressionTestCase(
        id="array_step",
        doc={"start": 0, "end": 5, "step": [1]},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject array step",
    ),
    ExpressionTestCase(
        id="objectid_step",
        doc={"start": 0, "end": 5, "step": ObjectId()},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject objectid step",
    ),
    ExpressionTestCase(
        id="datetime_step",
        doc={"start": 0, "end": 5, "step": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject datetime step",
    ),
    ExpressionTestCase(
        id="binary_step",
        doc={"start": 0, "end": 5, "step": Binary(b"x", 0)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject binary step",
    ),
    ExpressionTestCase(
        id="regex_step",
        doc={"start": 0, "end": 5, "step": Regex("x")},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject regex step",
    ),
    ExpressionTestCase(
        id="maxkey_step",
        doc={"start": 0, "end": 5, "step": MaxKey()},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject maxkey step",
    ),
    ExpressionTestCase(
        id="minkey_step",
        doc={"start": 0, "end": 5, "step": MinKey()},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject minkey step",
    ),
    ExpressionTestCase(
        id="timestamp_step",
        doc={"start": 0, "end": 5, "step": Timestamp(0, 0)},
        expression={"$range": ["$start", "$end", "$step"]},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Should reject timestamp step",
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
