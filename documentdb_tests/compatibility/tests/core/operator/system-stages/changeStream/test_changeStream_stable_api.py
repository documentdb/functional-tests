"""Tests for $changeStream behavior under Stable API v1 (apiStrict)."""

from __future__ import annotations

import pytest
from utils.changeStream_common import OPERATION_TIME, change_stream_command

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import API_STRICT_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Stable API V1 Acceptance]: under apiStrict true (Stable API V1), a
# spec that omits showExpandedEvents opens the stream; specifying
# showExpandedEvents under apiStrict true is rejected because the parameter is
# not part of API Version 1, regardless of its boolean value.
CHANGESTREAM_STABLE_API_V1_TESTS: list[StageTestCase] = [
    StageTestCase(
        "stable_api_empty_spec",
        pipeline=[{"$changeStream": {}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open with an empty spec under apiStrict true",
    ),
    StageTestCase(
        "stable_api_full_document",
        pipeline=[{"$changeStream": {"fullDocument": "updateLookup"}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open with fullDocument under apiStrict true",
    ),
    StageTestCase(
        "stable_api_full_document_before_change",
        pipeline=[{"$changeStream": {"fullDocumentBeforeChange": "whenAvailable"}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open with fullDocumentBeforeChange under apiStrict true",
    ),
    StageTestCase(
        "stable_api_start_at_operation_time",
        pipeline=[{"$changeStream": {"startAtOperationTime": OPERATION_TIME}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open with startAtOperationTime under apiStrict true",
    ),
    StageTestCase(
        "stable_api_show_expanded_events_true",
        pipeline=[{"$changeStream": {"showExpandedEvents": True}}],
        error_code=API_STRICT_ERROR,
        msg="$changeStream should reject showExpandedEvents true under apiStrict true",
    ),
    StageTestCase(
        "stable_api_show_expanded_events_false",
        pipeline=[{"$changeStream": {"showExpandedEvents": False}}],
        error_code=API_STRICT_ERROR,
        msg="$changeStream should reject showExpandedEvents false under apiStrict true",
    ),
]


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_STABLE_API_V1_TESTS))
def test_changeStream_stable_api_v1(collection, test_case):
    """Test $changeStream Stable API V1 (apiStrict true) acceptance and rejection."""
    stage = dict(test_case.pipeline[0]["$changeStream"])
    if stage.get("startAtOperationTime") is OPERATION_TIME:
        base = execute_command(
            collection, change_stream_command(collection, pipeline=[{"$changeStream": {}}])
        )
        stage["startAtOperationTime"] = base["operationTime"]
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$changeStream": stage}],
            "cursor": {},
            "apiVersion": "1",
            "apiStrict": True,
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        raw_res=True,
    )
