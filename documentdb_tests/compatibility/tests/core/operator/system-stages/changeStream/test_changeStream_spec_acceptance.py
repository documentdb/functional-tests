"""Tests for $changeStream spec and option acceptance for valid specs."""

from __future__ import annotations

import pytest
from utils.changeStream_common import change_stream_command

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

# Property [Empty Spec Acceptance]: an empty spec document opens a change stream
# because every option field is optional.
CHANGESTREAM_EMPTY_SPEC_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_spec",
        pipeline=[{"$changeStream": {}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should open with an empty spec document",
    ),
]

# Property [Boolean Option Acceptance]: showExpandedEvents accepts both boolean
# values, and allChangesForCluster accepts false on a collection-scoped stream.
# allChangesForCluster true is not accepted here because it requires a
# cluster-scoped stream on the admin database; that accept path is covered by
# the namespace-scope tests.
CHANGESTREAM_BOOLEAN_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "all_changes_for_cluster_false",
        pipeline=[{"$changeStream": {"allChangesForCluster": False}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept allChangesForCluster false",
    ),
    StageTestCase(
        "show_expanded_events_true",
        pipeline=[{"$changeStream": {"showExpandedEvents": True}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept showExpandedEvents true",
    ),
    StageTestCase(
        "show_expanded_events_false",
        pipeline=[{"$changeStream": {"showExpandedEvents": False}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept showExpandedEvents false",
    ),
]

# Property [fullDocument Enum Acceptance]: fullDocument accepts each of its
# documented enum strings.
CHANGESTREAM_FULL_DOCUMENT_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"full_document_{value}",
        pipeline=[{"$changeStream": {"fullDocument": value}}],
        expected={"ok": Eq(1.0)},
        msg=f"$changeStream should accept fullDocument '{value}'",
    )
    for value in ["default", "required", "updateLookup", "whenAvailable"]
]

# Property [fullDocumentBeforeChange Enum Acceptance]: fullDocumentBeforeChange
# accepts each of its documented enum strings.
CHANGESTREAM_FULL_DOCUMENT_BEFORE_CHANGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"full_document_before_change_{value}",
        pipeline=[{"$changeStream": {"fullDocumentBeforeChange": value}}],
        expected={"ok": Eq(1.0)},
        msg=f"$changeStream should accept fullDocumentBeforeChange '{value}'",
    )
    for value in ["off", "whenAvailable", "required"]
]

# Property [Option Combination]: independent option fields combine in one spec
# without a parse-time conflict, and the two enum options are parsed
# independently of each other.
CHANGESTREAM_OPTION_COMBINATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "combo_all_options",
        pipeline=[
            {
                "$changeStream": {
                    "allChangesForCluster": False,
                    "showExpandedEvents": True,
                    "fullDocument": "updateLookup",
                    "fullDocumentBeforeChange": "whenAvailable",
                }
            }
        ],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept all independent options combined in one spec",
    ),
] + [
    StageTestCase(
        f"combo_{full_document}_{before_change}",
        pipeline=[
            {
                "$changeStream": {
                    "fullDocument": full_document,
                    "fullDocumentBeforeChange": before_change,
                }
            }
        ],
        expected={"ok": Eq(1.0)},
        msg=(
            f"$changeStream should accept fullDocument '{full_document}' with "
            f"fullDocumentBeforeChange '{before_change}'"
        ),
    )
    for full_document, before_change in [
        ("default", "off"),
        ("required", "required"),
        ("whenAvailable", "whenAvailable"),
    ]
]

# Property [Null Option Acceptance]: an explicit null value for any of the five
# non-boolean-typed options (fullDocument, fullDocumentBeforeChange,
# resumeAfter, startAfter, startAtOperationTime) is accepted and opens a stream
# as if the field were unset, and a null resume option does not trigger
# resume-option mutual exclusivity. This group exercises only the null value;
# rejection of other BSON types per option is covered in
# test_changeStream_validation_errors.py.
CHANGESTREAM_NULL_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_full_document",
        pipeline=[{"$changeStream": {"fullDocument": None}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept a null fullDocument",
    ),
    StageTestCase(
        "null_full_document_before_change",
        pipeline=[{"$changeStream": {"fullDocumentBeforeChange": None}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept a null fullDocumentBeforeChange",
    ),
    StageTestCase(
        "null_resume_after",
        pipeline=[{"$changeStream": {"resumeAfter": None}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept a null resumeAfter",
    ),
    StageTestCase(
        "null_start_after",
        pipeline=[{"$changeStream": {"startAfter": None}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept a null startAfter",
    ),
    StageTestCase(
        "null_start_at_operation_time",
        pipeline=[{"$changeStream": {"startAtOperationTime": None}}],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should accept a null startAtOperationTime",
    ),
    StageTestCase(
        "null_all_resume_options",
        pipeline=[
            {
                "$changeStream": {
                    "resumeAfter": None,
                    "startAfter": None,
                    "startAtOperationTime": None,
                }
            }
        ],
        expected={"ok": Eq(1.0)},
        msg="$changeStream should not treat null resume options as a mutual exclusivity conflict",
    ),
]

CHANGESTREAM_SUCCESS_TESTS = (
    CHANGESTREAM_EMPTY_SPEC_TESTS
    + CHANGESTREAM_BOOLEAN_OPTION_TESTS
    + CHANGESTREAM_FULL_DOCUMENT_TESTS
    + CHANGESTREAM_FULL_DOCUMENT_BEFORE_CHANGE_TESTS
    + CHANGESTREAM_OPTION_COMBINATION_TESTS
    + CHANGESTREAM_NULL_OPTION_TESTS
)


@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(CHANGESTREAM_SUCCESS_TESTS))
def test_changeStream_cases(collection, test_case: StageTestCase):
    """Test $changeStream spec document and option acceptance."""
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg, raw_res=True)


# Property [Null Resume-Option Non-Conflict]: a resume option set to an explicit
# null does not count as a second resume point, so pairing it with another
# present resume token opens successfully rather than tripping resume-option
# mutual exclusivity. This holds for every (present token, null option) pairing.
@pytest.mark.requires(change_streams=True)
@pytest.mark.aggregate
@pytest.mark.parametrize(
    "present_field,null_field",
    [
        ("resumeAfter", "startAtOperationTime"),
        ("startAfter", "startAtOperationTime"),
        ("resumeAfter", "startAfter"),
        ("startAfter", "resumeAfter"),
    ],
)
def test_changeStream_null_resume_option_non_conflict(collection, present_field, null_field):
    """Test $changeStream treats a null resume option as absent, not a second resume point."""
    opened = execute_command(
        collection, change_stream_command(collection, pipeline=[{"$changeStream": {}}])
    )
    token = opened["cursor"]["postBatchResumeToken"]

    spec = {present_field: token, null_field: None}
    result = execute_command(
        collection, change_stream_command(collection, pipeline=[{"$changeStream": spec}])
    )
    assertResult(
        result,
        expected={"ok": Eq(1.0)},
        msg=f"$changeStream should accept {present_field!r} token with null {null_field!r}",
        raw_res=True,
    )
