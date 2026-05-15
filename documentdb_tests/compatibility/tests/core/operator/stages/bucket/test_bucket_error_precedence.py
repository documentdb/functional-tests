"""Tests for $bucket aggregation stage — error precedence ordering."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
    BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
    BUCKET_OUTPUT_NOT_OBJECT_ERROR,
    BUCKET_UNRECOGNIZED_OPTION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Error Precedence]: when multiple validation rules are violated
# simultaneously, errors are produced in a fixed priority order:
# arg type > boundaries type > groupBy type > unrecognized option > missing
# required > boundaries length > boundaries sort > boundaries mixed types >
# output type > default range.
BUCKET_ERROR_PRECEDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "precedence_boundaries_type_over_missing_groupBy",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"boundaries": "bad"}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="boundaries type error should fire before missing groupBy",
    ),
    StageTestCase(
        "precedence_groupBy_type_over_bad_boundaries",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": 42, "boundaries": "bad"}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="groupBy type error should fire before boundaries type error",
    ),
    StageTestCase(
        "precedence_groupBy_type_over_unsorted_boundaries",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": 42, "boundaries": [10, 5]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="groupBy type error should fire before boundaries sort error",
    ),
    StageTestCase(
        "precedence_groupBy_type_over_bad_output",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": 42,
                    "boundaries": [0, 10],
                    "output": "bad",
                }
            }
        ],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="groupBy type error should fire before output type error",
    ),
    StageTestCase(
        "precedence_groupBy_type_over_bad_default",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": 42,
                    "boundaries": [0, 10],
                    "default": 5,
                }
            }
        ],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="groupBy type error should fire before default range error",
    ),
    StageTestCase(
        "precedence_unrecognized_over_missing_groupBy",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"boundaries": [0, 10], "extra": 1}}],
        error_code=BUCKET_UNRECOGNIZED_OPTION_ERROR,
        msg="unrecognized option error should fire before missing required",
    ),
    StageTestCase(
        "precedence_boundaries_type_over_groupBy_type",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": "bad",
                    "extra": 1,
                }
            }
        ],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="boundaries type error should fire before unrecognized option",
    ),
    StageTestCase(
        "precedence_output_type_over_default_range",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": 5,
                    "output": "bad",
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="output type error should fire before default range error",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_ERROR_PRECEDENCE_TESTS))
def test_bucket_error_precedence(collection, test_case: StageTestCase):
    """Test $bucket error precedence ordering."""
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
