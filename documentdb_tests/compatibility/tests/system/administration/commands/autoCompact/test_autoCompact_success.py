"""Tests for the autoCompact command: successful requests and accepted inputs."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.system.administration.commands.autoCompact.utils.autoCompact_common import (  # noqa: E501
    ensure_autocompact_idle,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import OBJECT_IS_BUSY_ERROR
from documentdb_tests.framework.executor import execute_admin_with_retry_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType, NotExists

# Property [Response Format]: a successful autoCompact returns a bare ok
# response with no command-specific result fields.
AUTOCOMPACT_RESPONSE_FORMAT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "response_enable",
        command=lambda ctx: {"autoCompact": True},
        expected={
            "ok": [Eq(1.0), IsType("double")],
            "autoCompact": NotExists(),
        },
        msg="autoCompact enable should return ok:1.0 as a double with no command-specific fields",
    ),
    CommandTestCase(
        "response_disable",
        command=lambda ctx: {"autoCompact": False},
        expected={
            "ok": [Eq(1.0), IsType("double")],
            "autoCompact": NotExists(),
        },
        msg="autoCompact disable should return ok:1.0 as a double with no command-specific fields",
    ),
    CommandTestCase(
        "response_enable_with_options",
        command=lambda ctx: {
            "autoCompact": True,
            "freeSpaceTargetMB": 1,
            "runOnce": False,
        },
        expected={
            "ok": [Eq(1.0), IsType("double")],
            "autoCompact": NotExists(),
            "freeSpaceTargetMB": NotExists(),
            "runOnce": NotExists(),
        },
        msg="autoCompact enable with options should not echo freeSpaceTargetMB or runOnce",
    ),
]

# Property [Null Optional Fields]: a null freeSpaceTargetMB or runOnce is
# accepted and treated identically to omitting the field.
AUTOCOMPACT_NULL_OPTIONAL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_fstmb",
        command=lambda ctx: {"autoCompact": True, "freeSpaceTargetMB": None},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should treat a null freeSpaceTargetMB as omitted",
    ),
    CommandTestCase(
        "null_runonce",
        command=lambda ctx: {"autoCompact": True, "runOnce": None},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should treat a null runOnce as omitted",
    ),
]

# Property [Value Behavior]: runOnce:true is accepted alongside a disable
# (autoCompact:false) rather than rejected as contradictory.
AUTOCOMPACT_VALUE_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "value_disable_with_runonce",
        command=lambda ctx: {"autoCompact": False, "runOnce": True},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept runOnce:true alongside a disable and return ok:1.0",
    ),
]

# Property [runOnce Accepted Values]: both runOnce:true and runOnce:false are
# accepted on the enable path.
AUTOCOMPACT_RUNONCE_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "runonce_true",
        command=lambda ctx: {"autoCompact": True, "runOnce": True},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept runOnce:true and return ok:1.0",
    ),
    CommandTestCase(
        "runonce_false",
        command=lambda ctx: {"autoCompact": True, "runOnce": False},
        expected={"ok": Eq(1.0)},
        msg="autoCompact should accept runOnce:false and return ok:1.0",
    ),
]

AUTOCOMPACT_SUCCESS_TESTS: list[CommandTestCase] = (
    AUTOCOMPACT_RESPONSE_FORMAT_TESTS
    + AUTOCOMPACT_NULL_OPTIONAL_TESTS
    + AUTOCOMPACT_VALUE_BEHAVIOR_TESTS
    + AUTOCOMPACT_RUNONCE_ACCEPTED_TESTS
)


@pytest.mark.no_parallel
@pytest.mark.parametrize("test", pytest_params(AUTOCOMPACT_SUCCESS_TESTS))
def test_autoCompact_success(database_client, collection, test):
    """Test autoCompact successful requests and accepted inputs."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    # Ensure autoCompact is idle first: a leftover config from a prior test
    # would otherwise conflict.
    ensure_autocompact_idle(collection)
    # Tolerate the transient busy state while a prior compaction winds down.
    result = execute_admin_with_retry_command(
        collection, test.build_command(ctx), retry_code=OBJECT_IS_BUSY_ERROR
    )
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
