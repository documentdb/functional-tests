"""Tests for $changeStream mutual exclusivity of resume options."""

from __future__ import annotations

import pytest
from utils.changeStream_common import OPERATION_TIME, RESUME_TOKEN, change_stream_command

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    MULTIPLE_RESUME_OPTIONS_ERROR,
    RESUME_AFTER_START_AFTER_CONFLICT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Resume-Option Mutual Exclusivity]: specifying any pair of resume
# options in a single spec is rejected at open; the conflict is a parse-time
# check, so the same token may fill both token options.
CHANGESTREAM_RESUME_MUTUAL_EXCLUSIVITY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "resume_after_and_start_after",
        pipeline=[{"$changeStream": {"resumeAfter": RESUME_TOKEN, "startAfter": RESUME_TOKEN}}],
        error_code=RESUME_AFTER_START_AFTER_CONFLICT_ERROR,
        msg="$changeStream should reject both resumeAfter and startAfter together",
    ),
    StageTestCase(
        "resume_after_and_operation_time",
        pipeline=[
            {"$changeStream": {"resumeAfter": RESUME_TOKEN, "startAtOperationTime": OPERATION_TIME}}
        ],
        error_code=MULTIPLE_RESUME_OPTIONS_ERROR,
        msg="$changeStream should reject both resumeAfter and startAtOperationTime together",
    ),
    StageTestCase(
        "start_after_and_operation_time",
        pipeline=[
            {"$changeStream": {"startAfter": RESUME_TOKEN, "startAtOperationTime": OPERATION_TIME}}
        ],
        error_code=MULTIPLE_RESUME_OPTIONS_ERROR,
        msg="$changeStream should reject both startAfter and startAtOperationTime together",
    ),
]


@pytest.mark.replica_set
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_RESUME_MUTUAL_EXCLUSIVITY_TESTS))
def test_changeStream_resume_option_mutual_exclusivity(collection, test_case):
    """Test $changeStream rejects specifying more than one resume option."""
    opened = execute_command(
        collection, change_stream_command(collection, pipeline=[{"$changeStream": {}}])
    )
    token = opened["cursor"]["postBatchResumeToken"]
    operation_time = opened["operationTime"]
    substitutions = {id(RESUME_TOKEN): token, id(OPERATION_TIME): operation_time}
    spec = {
        key: substitutions.get(id(value), value)
        for key, value in test_case.pipeline[0]["$changeStream"].items()
    }
    result = execute_command(
        collection, change_stream_command(collection, pipeline=[{"$changeStream": spec}])
    )
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg)
