"""Tests for fsyncUnlock command behavior."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from bson import Int64
from pymongo import MongoClient

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import (
    API_STRICT_ERROR,
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_admin_command,
    execute_command,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType, NotExists
from documentdb_tests.framework.test_constants import (
    BSON_TYPE_SAMPLES,
    DOUBLE_ZERO,
    INT64_ZERO,
)

# fsyncUnlock decrements a server-global lock count, so these tests must never
# run in parallel with anything that takes or releases the fsync lock.
pytestmark = pytest.mark.no_parallel


def _drain_locks(collection) -> None:
    """Release any outstanding fsync locks so the count returns to 0.

    fsyncUnlock decrements a server-global lock count and reports the remaining
    count, so this loops until that count reaches 0 (or the not-locked error
    confirms it is already 0).
    """
    # The loop is bounded by the lock count, and the configured pytest timeout.
    while True:
        result = execute_admin_command(collection, {"fsyncUnlock": 1})
        if isinstance(result, Exception):
            # Verify the error is the not-locked error, meaning the count is
            # already 0.
            if getattr(result, "code", None) == ILLEGAL_OPERATION_ERROR:
                return
            raise result
        if result.get("lockCount", 0) == 0:
            return


@pytest.fixture(autouse=True)
def _unlocked_baseline(collection):
    """Drain the server-global fsync lock before and after every test.

    The lock is global state the collection fixture does not manage, so draining
    before gives each test a known unlocked baseline. Additionally, draining
    after releases whatever the test took, even if the test fails.
    """
    _drain_locks(collection)
    yield
    _drain_locks(collection)


# Sentinel marking an FsyncUnlockCase field that the caller must set. Every
# field inherited from CommandTestCase has a default, so the dataclass cannot
# make these positionally required; instead they default to this sentinel and
# __post_init__ rejects it, forcing each case to state its lock-state
# preconditions explicitly rather than inheriting a hidden default.
_REQUIRED = object()


@dataclass(frozen=True)
class FsyncUnlockCase(CommandTestCase):
    """A command-test case carrying fsyncUnlock's lock-state preconditions.

    fsyncUnlock's success path depends on the current lock count, which is not
    derivable from the command itself, so each case declares how many fsync
    locks to take and how many unlocks to issue before the command under test
    runs. Both are required: no default lock state is assumed.
    """

    locks_taken: int = _REQUIRED  # type: ignore[assignment]
    unlocks_before: int = _REQUIRED  # type: ignore[assignment]

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.locks_taken is _REQUIRED or self.unlocks_before is _REQUIRED:
            raise ValueError(
                f"FsyncUnlockCase '{self.id}' must set locks_taken and unlocks_before explicitly"
            )


# Property [Response Shape and Return Types]: lockCount is a BSON Int64 holding
# the remaining lock count (not a hardcoded 0) and seeAlso is absent (it belongs
# only to the fsync lock response).
FSYNCUNLOCK_RESPONSE_SHAPE_TESTS: list[FsyncUnlockCase] = [
    FsyncUnlockCase(
        "response_shape",
        # Lock twice so the unlock leaves a nonzero remaining count; this proves
        # lockCount reflects the locks remaining rather than a hardcoded 0.
        locks_taken=2,
        unlocks_before=0,
        command={"fsyncUnlock": 1},
        expected={
            "info": Eq("fsyncUnlock completed"),
            "lockCount": [IsType("long"), Eq(Int64(1))],
            "ok": [IsType("double"), Eq(1.0)],
            "seeAlso": NotExists(),
        },
        msg="fsyncUnlock should return info, an Int64 lockCount of the remaining "
        "locks, a double ok of 1.0, and no seeAlso field",
    ),
]

# Property [Command-Key Value Handling]: the command-key value is ignored across
# every BSON type, so each still succeeds and decrements normally.
FSYNCUNLOCK_COMMAND_KEY_TESTS: list[FsyncUnlockCase] = [
    FsyncUnlockCase(
        f"command_key_{bson_type.value}",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": val},
        expected={"lockCount": Eq(INT64_ZERO), "ok": Eq(1.0)},
        msg="fsyncUnlock should ignore its command-key value and decrement the "
        "lock count by exactly 1 on the locked path",
    )
    for bson_type, val in BSON_TYPE_SAMPLES.items()
]

# Property [Comment Field Handling]: a comment of any BSON type is accepted
# untyped, succeeds, and is never echoed in the reply.
FSYNCUNLOCK_COMMENT_TESTS: list[FsyncUnlockCase] = [
    FsyncUnlockCase(
        f"comment_{bson_type.value}",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "comment": val},
        expected={"lockCount": Eq(INT64_ZERO), "ok": Eq(1.0), "comment": NotExists()},
        msg="fsyncUnlock should accept any comment value, decrement the lock "
        "count by exactly 1, and never echo the comment in the reply",
    )
    for bson_type, val in BSON_TYPE_SAMPLES.items()
]

# Property [Generic Command Options Accepted]: generic command-envelope options
# fall through to the normal path, leaving the success+decrement outcome
# unchanged.
FSYNCUNLOCK_GENERIC_OPTION_TESTS: list[FsyncUnlockCase] = [
    FsyncUnlockCase(
        "generic_read_concern_local",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "readConcern": {"level": "local"}},
        expected={"lockCount": Eq(INT64_ZERO), "ok": Eq(1.0)},
        msg="fsyncUnlock should accept the generic command option and decrement "
        "the lock count by exactly 1 on the locked path",
    ),
    FsyncUnlockCase(
        "generic_read_preference_primary",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "$readPreference": {"mode": "primary"}},
        expected={"lockCount": Eq(INT64_ZERO), "ok": Eq(1.0)},
        msg="fsyncUnlock should accept the generic command option and decrement "
        "the lock count by exactly 1 on the locked path",
    ),
    FsyncUnlockCase(
        "generic_read_preference_secondary_preferred",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "$readPreference": {"mode": "secondaryPreferred"}},
        expected={"lockCount": Eq(INT64_ZERO), "ok": Eq(1.0)},
        msg="fsyncUnlock should accept the generic command option and decrement "
        "the lock count by exactly 1 on the locked path",
    ),
    FsyncUnlockCase(
        "generic_max_time_ms_zero",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "maxTimeMS": 0},
        expected={"lockCount": Eq(INT64_ZERO), "ok": Eq(1.0)},
        msg="fsyncUnlock should accept the generic command option and decrement "
        "the lock count by exactly 1 on the locked path",
    ),
    FsyncUnlockCase(
        "generic_max_time_ms_zero_float",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "maxTimeMS": DOUBLE_ZERO},
        expected={"lockCount": Eq(INT64_ZERO), "ok": Eq(1.0)},
        msg="fsyncUnlock should accept the generic command option and decrement "
        "the lock count by exactly 1 on the locked path",
    ),
    FsyncUnlockCase(
        "generic_unknown_extra_field",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "someUnknownField": 1},
        expected={"lockCount": Eq(INT64_ZERO), "ok": Eq(1.0)},
        msg="fsyncUnlock should accept the generic command option and decrement "
        "the lock count by exactly 1 on the locked path",
    ),
]

# Property [Error: Instance Not Locked]: unlocking at lock count 0 errors with
# IllegalOperation rather than no-opping, whether never raised or driven back to
# 0 by over-unlocking.
FSYNCUNLOCK_NOT_LOCKED_TESTS: list[FsyncUnlockCase] = [
    FsyncUnlockCase(
        "not_locked_never_raised",
        locks_taken=0,
        unlocks_before=0,
        command={"fsyncUnlock": 1},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="fsyncUnlock should error as not-locked when the lock count is "
        "already 0 instead of silently no-opping",
    ),
    FsyncUnlockCase(
        "over_unlock_below_zero",
        locks_taken=1,
        unlocks_before=1,
        command={"fsyncUnlock": 1},
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="fsyncUnlock should error as not-locked when the lock count is "
        "already 0 instead of silently no-opping",
    ),
]

# Property [Error: writeConcern Not Supported]: a writeConcern envelope errors
# with InvalidOptions even with a lock held; the command does not support
# writeConcern.
FSYNCUNLOCK_WRITE_CONCERN_TESTS: list[FsyncUnlockCase] = [
    FsyncUnlockCase(
        "write_concern_w1",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "writeConcern": {"w": 1}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="fsyncUnlock should reject a writeConcern envelope while a lock is held",
    ),
]

# Property [Error: readConcern Non-Local Levels]: a non-local readConcern level
# errors with InvalidOptions even with a lock held; only the local level is
# supported.
FSYNCUNLOCK_READ_CONCERN_TESTS: list[FsyncUnlockCase] = [
    FsyncUnlockCase(
        f"read_concern_{level}",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "readConcern": {"level": level}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="fsyncUnlock should reject a non-local readConcern level while a lock is held",
    )
    for level in ("majority", "linearizable", "available", "snapshot")
]

# Property [Error: Stable API Rejection]: under apiVersion 1 + apiStrict the
# command errors with APIStrictError even with a lock held; it is not in API
# Version 1.
FSYNCUNLOCK_API_STRICT_TESTS: list[FsyncUnlockCase] = [
    FsyncUnlockCase(
        "api_strict",
        locks_taken=1,
        unlocks_before=0,
        command={"fsyncUnlock": 1, "apiVersion": "1", "apiStrict": True},
        error_code=API_STRICT_ERROR,
        msg="fsyncUnlock should be rejected under apiStrict true while a lock is held",
    ),
]

FSYNCUNLOCK_TESTS = (
    FSYNCUNLOCK_RESPONSE_SHAPE_TESTS
    + FSYNCUNLOCK_COMMAND_KEY_TESTS
    + FSYNCUNLOCK_COMMENT_TESTS
    + FSYNCUNLOCK_GENERIC_OPTION_TESTS
    + FSYNCUNLOCK_NOT_LOCKED_TESTS
    + FSYNCUNLOCK_WRITE_CONCERN_TESTS
    + FSYNCUNLOCK_READ_CONCERN_TESTS
    + FSYNCUNLOCK_API_STRICT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(FSYNCUNLOCK_TESTS))
def test_fsyncUnlock_cases(collection, test):
    """Test fsyncUnlock cases against its response contract on the admin database."""
    for _ in range(test.locks_taken):
        execute_admin_command(collection, {"fsync": 1, "lock": True})
    for _ in range(test.unlocks_before):
        execute_admin_command(collection, {"fsyncUnlock": 1})
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Error: Non-Admin Database]: a non-admin database errors with
# Unauthorized even with a lock held - the admin-scope dispatch check, not an
# auth-privilege failure.
def test_fsyncUnlock_rejects_non_admin_database(collection):
    """Test fsyncUnlock rejects a non-admin database while a lock is held."""
    execute_admin_command(collection, {"fsync": 1, "lock": True})
    result = execute_command(collection, {"fsyncUnlock": 1})
    assertFailureCode(
        result,
        UNAUTHORIZED_ERROR,
        msg="fsyncUnlock should reject a non-admin database while a lock is held",
    )


# Property [Cross-Connection Lock Sharing]: the lock count is server-global, so
# an unlock on one connection releases a lock taken on another.
def test_fsyncUnlock_releases_lock_taken_on_another_connection(collection, pytestconfig):
    """Test fsyncUnlock releases a lock that was taken on a different connection."""
    other_client: MongoClient = MongoClient(pytestconfig.connection_string)
    try:
        # Take the lock on a separate connection and pool.
        other_client.admin.command({"fsync": 1, "lock": True})
        # Release it from the primary connection; if the count were
        # per-connection this unlock would instead error as not-locked.
        result = execute_admin_command(collection, {"fsyncUnlock": 1})
        assertSuccessPartial(
            result,
            {"lockCount": INT64_ZERO, "ok": 1.0},
            msg="fsyncUnlock should release a lock taken on another connection "
            "and report the shared count at 0",
        )
    finally:
        other_client.close()


# Property [Explicit Session Accepted]: an explicit client session is accepted
# and behaves identically to a sessionless invocation.
def test_fsyncUnlock_accepts_explicit_session(collection):
    """Test fsyncUnlock runs under an explicit client session and behaves identically."""
    execute_admin_command(collection, {"fsync": 1, "lock": True})
    session = collection.database.client.start_session()
    try:
        result = execute_admin_command(collection, {"fsyncUnlock": 1}, session=session)
        assertSuccessPartial(
            result,
            {"lockCount": INT64_ZERO, "ok": 1.0},
            msg="fsyncUnlock should run under an explicit session and decrement the "
            "lock count by exactly 1",
        )
    finally:
        session.end_session()


# Property [Error: Non-Admin Database Consumes No Lock]: a non-admin rejection
# does not consume a held lock, so a following admin fsyncUnlock still decrements
# the count to 0.
def test_fsyncUnlock_non_admin_consumes_no_lock(collection):
    """Test fsyncUnlock non-admin rejection does not consume a held lock."""
    execute_admin_command(collection, {"fsync": 1, "lock": True})
    execute_command(collection, {"fsyncUnlock": 1})
    result = execute_admin_command(collection, {"fsyncUnlock": 1})
    assertSuccessPartial(
        result,
        {"lockCount": INT64_ZERO, "ok": 1.0},
        msg="fsyncUnlock non-admin rejection should not consume a held lock, so a "
        "following real unlock still decrements the count to 0",
    )


# Property [Error: Multi-Document Transaction]: inside a multi-document
# transaction fsyncUnlock errors with OperationNotSupportedInTransaction.
@pytest.mark.replica_set
def test_fsyncUnlock_rejects_multi_document_transaction(collection):
    """Test fsyncUnlock errors when issued inside a multi-document transaction."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        try:
            result = execute_admin_command(collection, {"fsyncUnlock": 1}, session=session)
        finally:
            session.abort_transaction()
    assertFailureCode(
        result,
        OPERATION_NOT_SUPPORTED_IN_TRANSACTION_ERROR,
        msg="fsyncUnlock should error as not supported when issued inside a "
        "multi-document transaction",
    )
