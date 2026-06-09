"""Tests for $changeStream event read errors when a required pre/post image is missing."""

from __future__ import annotations

import pytest
from utils.changeStream_common import change_stream_command, get_more_command

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import NO_MATCHING_DOCUMENT_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Required Image Event-Read Error]: a required-image mode on a
# collection without pre/post images enabled fails when reading the update event.
CHANGESTREAM_EVENT_READ_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "full_document_required_no_images",
        pipeline=[{"$changeStream": {"fullDocument": "required"}}],
        error_code=NO_MATCHING_DOCUMENT_ERROR,
        msg="$changeStream fullDocument required should open but fail reading an update"
        " event without pre/post images enabled",
    ),
    StageTestCase(
        "full_document_before_change_required_no_images",
        pipeline=[{"$changeStream": {"fullDocumentBeforeChange": "required"}}],
        error_code=NO_MATCHING_DOCUMENT_ERROR,
        msg="$changeStream fullDocumentBeforeChange required should open but fail reading"
        " an update event without pre/post images enabled",
    ),
]


@pytest.mark.replica_set
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_EVENT_READ_ERROR_TESTS))
def test_changeStream_required_image_event_read_error(collection, test_case):
    """Test $changeStream defers required-image enforcement to event-read time."""
    collection.insert_one({"_id": 1, "a": 1})
    # The open must succeed: enforcement of the required image is deferred to the
    # getMore that reads the update event, not raised at parse/open time.
    opened = collection.database.command(
        change_stream_command(collection, pipeline=test_case.pipeline)
    )
    collection.update_one({"_id": 1}, {"$set": {"a": 2}})
    result = execute_command(collection, get_more_command(collection, opened["cursor"]["id"]))
    assertResult(result, error_code=test_case.error_code, msg=test_case.msg, raw_res=True)
