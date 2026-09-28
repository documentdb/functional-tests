"""Tests for compact command parameter behavior."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing Behavior]: null values for optional parameters
# are accepted and treated identically to omitting the field. These omit force,
# so they are gated on the precondition that compact succeeds without it.
COMPACT_NULL_AND_MISSING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dry_run_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": None},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="null dryRun should be treated as omitted (defaults to false)",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
    CommandTestCase(
        "force_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": None},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="null force should be treated as omitted",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
    CommandTestCase(
        "free_space_target_mb_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "freeSpaceTargetMB": None},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="null freeSpaceTargetMB should be treated as omitted",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
    CommandTestCase(
        "comment_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "comment": None},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="null comment should be accepted",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
    CommandTestCase(
        "all_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "dryRun": None,
            "force": None,
            "freeSpaceTargetMB": None,
            "comment": None,
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="All-null optional parameters should be treated as all omitted",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
    CommandTestCase(
        "write_concern_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "writeConcern": None},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="null writeConcern should be treated as omitted",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
]

# Property [Response Format]: the response structure differs based on
# whether dryRun is enabled. These omit force, so they are gated on the
# precondition that compact succeeds without it.
COMPACT_RESPONSE_FORMAT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "without_dry_run",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Should return bytesFreed and ok when dryRun is omitted",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
    CommandTestCase(
        "dry_run_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": False},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="Should return bytesFreed and ok when dryRun is false",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
    CommandTestCase(
        "dry_run_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "dryRun": True},
        expected={"estimatedBytesFreed": 0, "ok": 1.0},
        msg="Should return estimatedBytesFreed when dryRun is true",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
]

# Property [force Behavior]: force=true is accepted with no observable
# difference from force=false or omitted.
COMPACT_FORCE_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "force_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": True},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="force=true should be accepted with same response as omitted",
    ),
    CommandTestCase(
        "force_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "force": False},
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="force=false should be accepted with same response as omitted",
        marks=(pytest.mark.requires(unforced_compact=True),),
    ),
]

# Property [Parameter Interactions]: all optional parameters can be
# combined simultaneously without conflict.
COMPACT_PARAMETER_INTERACTIONS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "all_params_dry_run_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "dryRun": False,
            "force": True,
            "freeSpaceTargetMB": 1,
            "comment": "combined",
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="All params with dryRun=false should succeed with bytesFreed",
    ),
    CommandTestCase(
        "dry_run_true_force_true_threshold",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "dryRun": True,
            "force": True,
            "freeSpaceTargetMB": 1,
        },
        expected={"estimatedBytesFreed": 0, "ok": 1.0},
        msg="dryRun=true + force=true + freeSpaceTargetMB should succeed together",
    ),
    CommandTestCase(
        "force_and_threshold_without_dry_run",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "force": True,
            "freeSpaceTargetMB": 5,
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="force + freeSpaceTargetMB without dryRun should succeed",
    ),
    CommandTestCase(
        "comment_with_other_params",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "dryRun": True,
            "force": True,
            "freeSpaceTargetMB": 1,
            "comment": {"reason": "test"},
        },
        expected={"estimatedBytesFreed": 0, "ok": 1.0},
        msg="comment should not interact with other parameters",
    ),
]

COMPACT_PARAMETER_TESTS: list[CommandTestCase] = (
    COMPACT_NULL_AND_MISSING_TESTS
    + COMPACT_RESPONSE_FORMAT_TESTS
    + COMPACT_FORCE_BEHAVIOR_TESTS
    + COMPACT_PARAMETER_INTERACTIONS_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_PARAMETER_TESTS))
def test_compact_parameters(database_client, collection, test):
    """Test compact command parameter behavior."""
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
