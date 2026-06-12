"""Tests for aggregate command pipeline element and stage validation."""

from __future__ import annotations

from functools import reduce
from typing import Any, List, cast

import pytest
from bson.son import SON

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    MAX_NESTED_SUB_PIPELINE_ERROR,
    PIPELINE_LENGTH_LIMIT_ERROR,
    PIPELINE_STAGE_EXTRA_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNKNOWN_PIPELINE_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Pipeline Element Validation]: invalid pipeline elements and
# structural errors in stage documents are rejected.
AGGREGATE_PIPELINE_ELEMENT_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "validate_non_object_string",
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": ["hello"], "cursor": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject non-object element in pipeline array",
    ),
    CommandTestCase(
        "validate_non_object_int",
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [42], "cursor": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject integer element in pipeline array",
    ),
    CommandTestCase(
        "validate_non_object_null",
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [None], "cursor": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject null element in pipeline array",
    ),
    CommandTestCase(
        "validate_non_object_array",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [[{"$match": {}}]],
            "cursor": {},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject array element in pipeline array",
    ),
    CommandTestCase(
        "validate_non_object_bool",
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [True], "cursor": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="aggregate should reject boolean element in pipeline array",
    ),
    CommandTestCase(
        "validate_empty_stage",
        command=lambda ctx: {"aggregate": ctx.collection, "pipeline": [{}], "cursor": {}},
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="aggregate should reject empty document as a pipeline stage",
    ),
    CommandTestCase(
        "validate_multi_key_stage",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [SON([("$match", {}), ("$sort", {"x": 1})])],
            "cursor": {},
        },
        error_code=PIPELINE_STAGE_EXTRA_FIELD_ERROR,
        msg="aggregate should reject stage document with multiple keys",
    ),
    CommandTestCase(
        "validate_unrecognized_stage",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$fakeStage": {}}],
            "cursor": {},
        },
        error_code=UNKNOWN_PIPELINE_STAGE_ERROR,
        msg="aggregate should reject unrecognized stage name",
    ),
]

# Property [Pipeline Length Limits]: pipelines and sub-pipelines exceeding
# 1000 stages or nesting depth exceeding 20 are rejected.
AGGREGATE_PIPELINE_LENGTH_LIMIT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "validate_exceed_1000_stages",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$addFields": {"x": 1}}] * 1001,
            "cursor": {},
        },
        error_code=PIPELINE_LENGTH_LIMIT_ERROR,
        msg="aggregate should reject pipeline exceeding 1000 stages",
    ),
    CommandTestCase(
        "validate_exceed_nesting_depth",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": reduce(  # type: ignore[dict-item]
                lambda p, i: [{"$lookup": {"from": ctx.collection, "pipeline": p, "as": f"j{i}"}}],
                range(21),
                cast(List[Any], [{"$addFields": {"x": 1}}]),
            ),
            "cursor": {},
        },
        error_code=MAX_NESTED_SUB_PIPELINE_ERROR,
        msg="aggregate should reject sub-pipeline nesting depth exceeding 20 via $lookup",
    ),
    CommandTestCase(
        "validate_exceed_nesting_depth_unionwith",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": reduce(  # type: ignore[dict-item]
                lambda p, _: [{"$unionWith": {"coll": ctx.collection, "pipeline": p}}],
                range(21),
                cast(List[Any], [{"$addFields": {"x": 1}}]),
            ),
            "cursor": {},
        },
        error_code=MAX_NESTED_SUB_PIPELINE_ERROR,
        msg="aggregate should reject sub-pipeline nesting depth exceeding 20 via $unionWith",
    ),
    CommandTestCase(
        "validate_exceed_1000_stages_facet",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$facet": {"branch": [{"$addFields": {"x": 1}}] * 1001}}],
            "cursor": {},
        },
        error_code=PIPELINE_LENGTH_LIMIT_ERROR,
        msg="aggregate should reject $facet sub-pipeline exceeding 1000 stages",
    ),
    CommandTestCase(
        "validate_exceed_1000_stages_lookup",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": ctx.collection,
                        "pipeline": [{"$addFields": {"x": 1}}] * 1001,
                        "as": "j",
                    }
                }
            ],
            "cursor": {},
        },
        error_code=PIPELINE_LENGTH_LIMIT_ERROR,
        msg="aggregate should reject $lookup sub-pipeline exceeding 1000 stages",
    ),
    CommandTestCase(
        "validate_exceed_1000_stages_unionwith",
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$unionWith": {
                        "coll": ctx.collection,
                        "pipeline": [{"$addFields": {"x": 1}}] * 1001,
                    }
                }
            ],
            "cursor": {},
        },
        error_code=PIPELINE_LENGTH_LIMIT_ERROR,
        msg="aggregate should reject $unionWith sub-pipeline exceeding 1000 stages",
    ),
]

AGGREGATE_PIPELINE_VALIDATION_TESTS = (
    AGGREGATE_PIPELINE_ELEMENT_VALIDATION_TESTS + AGGREGATE_PIPELINE_LENGTH_LIMIT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_PIPELINE_VALIDATION_TESTS))
def test_aggregate_pipeline_validation(database_client, collection, test):
    """Test aggregate pipeline element and stage validation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
