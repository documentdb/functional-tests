"""Tests for $rankFusion spec field type-strictness errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [input Type Strictness]: a non-object input value produces a
# TypeMismatch error (null is handled separately as missing).
RANKFUSION_INPUT_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"input_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": val}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$rankFusion should reject a {tid} input",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 5),
        ("int64", Int64(5)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", [{"$sort": {"a": -1}}]),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [input.pipelines Type Strictness]: a non-object input.pipelines value
# produces a TypeMismatch error (null is handled separately as missing).
RANKFUSION_PIPELINES_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"pipelines_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": val}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$rankFusion should reject a {tid} input.pipelines",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 5),
        ("int64", Int64(5)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", [{"p1": [{"$sort": {"a": -1}}]}]),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Pipeline Value Type Strictness]: a pipeline map value that is not an
# array produces a TypeMismatch error (here null is a type mismatch, not
# missing).
RANKFUSION_PIPELINE_VALUE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"pipeline_value_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": val}}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$rankFusion should reject a {tid} pipeline value that is not an array",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 5),
        ("int64", Int64(5)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("null", None),
        ("object", {"$sort": {"a": -1}}),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Pipeline Element Type Strictness]: a pipeline array element that is
# not an object produces a TypeMismatch error.
RANKFUSION_PIPELINE_ELEMENT_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"pipeline_element_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": [val]}}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$rankFusion should reject a {tid} pipeline array element",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 5),
        ("int64", Int64(5)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("null", None),
        ("array", [{"$sort": {"a": -1}}]),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [combination Type Strictness]: a non-object combination value
# produces a TypeMismatch error (null is handled separately as accepted).
RANKFUSION_COMBINATION_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"combination_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": val,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$rankFusion should reject a {tid} combination",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 5),
        ("int64", Int64(5)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", [{"weights": {}}]),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [combination.weights Type Strictness]: a non-object
# combination.weights value produces a TypeMismatch error (null is handled
# separately as missing-required).
RANKFUSION_WEIGHTS_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"weights_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": val},
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$rankFusion should reject a {tid} combination.weights",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 5),
        ("int64", Int64(5)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", [{"p1": 1}]),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [scoreDetails Type Strictness]: a non-boolean scoreDetails value
# produces a TypeMismatch error with no numeric or string coercion (null is
# handled separately as accepted).
RANKFUSION_SCORE_DETAILS_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"score_details_type_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "scoreDetails": val,
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$rankFusion should reject a {tid} scoreDetails without coercion",
    )
    for tid, val in [
        ("string_true", "true"),
        ("string_empty", ""),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("double_nan", FLOAT_NAN),
        ("double_inf", FLOAT_INFINITY),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("array", [True]),
        ("object", {"x": 1}),
        ("objectid", ObjectId("000000000000000000000001")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

RANKFUSION_TYPE_ERROR_TESTS = (
    RANKFUSION_INPUT_TYPE_ERROR_TESTS
    + RANKFUSION_PIPELINES_TYPE_ERROR_TESTS
    + RANKFUSION_PIPELINE_VALUE_TYPE_ERROR_TESTS
    + RANKFUSION_PIPELINE_ELEMENT_TYPE_ERROR_TESTS
    + RANKFUSION_COMBINATION_TYPE_ERROR_TESTS
    + RANKFUSION_WEIGHTS_TYPE_ERROR_TESTS
    + RANKFUSION_SCORE_DETAILS_TYPE_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_TYPE_ERROR_TESTS))
def test_rankFusion_type_errors(collection, test_case: StageTestCase):
    """Test $rankFusion spec field type-strictness errors."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
