"""Tests for malformed $rankFusion spec structure errors."""

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
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_DOT_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    MISSING_FIELD_ERROR,
    PIPELINE_LENGTH_LIMIT_ERROR,
    RANK_FUSION_EMPTY_PIPELINE_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

# Property [Null and Missing Errors]: a missing or null input, a null
# input.pipelines, or a null combination.weights value each produce a
# missing-required-field error because null is treated as field-absent.
RANKFUSION_NULL_MISSING_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "error_input_null",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": None}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$rankFusion should treat a null input as missing and require it",
    ),
    StageTestCase(
        "error_input_omitted",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$rankFusion should require the input field when it is omitted",
    ),
    StageTestCase(
        "error_pipelines_null",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": None}}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$rankFusion should treat a null input.pipelines as missing and require it",
    ),
    StageTestCase(
        "error_weights_null",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": None},
                }
            }
        ],
        error_code=MISSING_FIELD_ERROR,
        msg="$rankFusion should treat a null combination.weights map as missing-required",
    ),
]

# Property [Structure and Arity Errors]: a present-but-incomplete spec object
# (an input, input.pipelines, or combination object missing its required nested
# field) or an empty pipeline array is rejected, as is a spec whose input
# sub-pipeline exceeds the 1000-stage pipeline-length limit.
RANKFUSION_STRUCTURE_ARITY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "error_input_empty_no_pipelines",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {}}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$rankFusion should require input.pipelines when input is an empty object",
    ),
    StageTestCase(
        "error_pipelines_empty_map",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {}}}}],
        error_code=BAD_VALUE_ERROR,
        msg="$rankFusion should require at least one pipeline when the pipelines map is empty",
    ),
    StageTestCase(
        "error_combination_empty_no_weights",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {},
                }
            }
        ],
        error_code=MISSING_FIELD_ERROR,
        msg="$rankFusion should require combination.weights when combination is present",
    ),
    StageTestCase(
        "error_pipeline_array_empty",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {"p1": []}}}}],
        error_code=RANK_FUSION_EMPTY_PIPELINE_ERROR,
        msg="$rankFusion should reject an empty input pipeline array",
    ),
    StageTestCase(
        "error_sub_pipeline_over_limit",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}] + [{"$skip": 0}] * 1000}}
                }
            }
        ],
        error_code=PIPELINE_LENGTH_LIMIT_ERROR,
        msg="$rankFusion should reject a sub-pipeline exceeding 1000 stages before desugaring",
    ),
]

# Property [Pipeline Name Errors]: a pipeline name that is an empty string, that
# starts with a $, or that contains an ASCII dot is rejected, each producing its
# own error code.
RANKFUSION_PIPELINE_NAME_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"pipeline_name_error_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines": {name: [{"$sort": {"a": -1}}]}}}}],
        error_code=code,
        msg=f"$rankFusion should reject a {tid} pipeline name",
    )
    for tid, name, code in [
        ("empty", "", FIELD_PATH_EMPTY_COMPONENT_ERROR),
        ("dollar_prefixed", "$foo", FIELD_PATH_DOLLAR_PREFIX_ERROR),
        ("dollar_only", "$", FIELD_PATH_DOLLAR_PREFIX_ERROR),
        ("dot_leading", ".ab", FIELD_PATH_DOT_ERROR),
        ("dot_mid", "a.b", FIELD_PATH_DOT_ERROR),
        ("dot_trailing", "ab.", FIELD_PATH_DOT_ERROR),
    ]
]

# Property [Non-Object Spec]: a $rankFusion value that is not an object
# produces a parse error because the stage must take a nested object.
RANKFUSION_NON_OBJECT_SPEC_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"non_object_spec_{tid}",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": val}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"$rankFusion should reject a {tid} spec that is not a nested object",
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
        # Unlike the input/combination fields where null is treated as missing
        # or accepted, a null stage value is rejected as a non-object spec.
        ("null", None),
    ]
]

# Property [Unknown Field]: a field name that does not exactly match a
# recognized spec field (whether an entirely unknown field at any spec level
# or a case- or whitespace-variant of a known field, since matching is
# case-sensitive and not trimmed) produces an unrecognized-field error.
RANKFUSION_UNKNOWN_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "unknown_top_level",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "bogus": 1,
                }
            }
        ],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$rankFusion should reject an unknown top-level spec field",
    ),
    StageTestCase(
        "unknown_inside_input",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}, "bogus": 1},
                }
            }
        ],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$rankFusion should reject an unknown field inside input",
    ),
    StageTestCase(
        "unknown_inside_combination",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"weights": {}, "method": 1},
                }
            }
        ],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$rankFusion should reject an unknown field inside combination",
    ),
    StageTestCase(
        "case_variant_input",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"Input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$rankFusion should reject a case-variant spelling of the input field",
    ),
    StageTestCase(
        "case_variant_pipelines",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"Pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$rankFusion should reject a case-variant spelling of the pipelines field",
    ),
    StageTestCase(
        "case_variant_weights",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[
            {
                "$rankFusion": {
                    "input": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}},
                    "combination": {"Weights": {}},
                }
            }
        ],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$rankFusion should reject a case-variant spelling of the weights field",
    ),
    StageTestCase(
        "whitespace_input",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input ": {"pipelines": {"p1": [{"$sort": {"a": -1}}]}}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$rankFusion should reject a trailing-space variant of the input field",
    ),
    StageTestCase(
        "whitespace_pipelines",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$rankFusion": {"input": {"pipelines ": {"p1": [{"$sort": {"a": -1}}]}}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$rankFusion should reject a trailing-space variant of the pipelines field",
    ),
]

RANKFUSION_SPEC_ERROR_TESTS = (
    RANKFUSION_NULL_MISSING_ERROR_TESTS
    + RANKFUSION_STRUCTURE_ARITY_ERROR_TESTS
    + RANKFUSION_PIPELINE_NAME_ERROR_TESTS
    + RANKFUSION_NON_OBJECT_SPEC_ERROR_TESTS
    + RANKFUSION_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(RANKFUSION_SPEC_ERROR_TESTS))
def test_rankFusion_spec_errors(collection, test_case: StageTestCase):
    """Test malformed $rankFusion spec structure errors."""
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
